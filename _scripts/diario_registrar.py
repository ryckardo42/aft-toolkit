# -*- coding: utf-8 -*-
"""
diario_registrar.py — grava um dia trabalhado no DIÁRIO DE ATIVIDADES da OS.

O diário mora na tabela '## Registro de atividades' do memory.md de cada OS:
cada linha classificada começa com uma ou mais LETRAS entre colchetes, que
correspondem às atividades da tela 2.1 do RI (SFIT-WEB):

  [A] Preparação/planejamento da fiscalização
  [B] Início da fiscalização
  [C] Inspeção do ambiente de trabalho / auditoria de documentos no
      estabelecimento / entrevista de empregados no estabelecimento
  [D] Auditoria e análise de documentos fora do estabelecimento
  [E] Elaboração e/ou emissão de documentos / lançamento de dados em sistemas
  [F] Fim da fiscalização

A data da linha é a data DA ATIVIDADE (que pode ser passada: "inspecionei em
11/08"), não a do registro. Deduplicação por (data, letra): registrar de novo
uma letra que o dia já tem é ignorado em silêncio — cumulativo, nunca duplica.

Uso (skills e Claude):
    python diario_registrar.py "<pasta da OS ou memory.md>" --tipos BC
        [--data dd/mm/aaaa] [--detalhe "via /aft-inspecao-fisica"]
        [--acao "texto livre da ação"]

    --tipos    letras A-F, juntas ("CE") — obrigatório no modo normal
    --data     data da atividade (padrão: hoje)
    --detalhe  coluna Detalhes da tabela (padrão: vazio)
    --acao     texto da coluna Ação; sem ele, o texto padrão das letras

Modo GANCHO (hook PostToolUse do Claude Code — ver instalar_hook_diario.py):
    python diario_registrar.py --hook
Lê o JSON do evento no stdin; se a tool editada for um memory.md dentro de
'OS ATIVAS', anota o dia num sidecar .diario-auto.jsonl na pasta da OS (1 linha
por dia, deduplicado). NUNCA toca o memory.md nesse modo — o Claude pode estar
no meio de uma sequência de edições e uma escrita externa invalidaria o estado
do arquivo para ele. O painel e o /aft-diario fundem o sidecar como "dia
trabalhado sem classificação" quando o dia não tem linha classificada.

Saída (modo normal): JSON {ok, os, data, tipos_novos, tipos_ja_registrados,
msg}. Modo gancho: silencioso, sempre exit 0 (um gancho nunca pode travar a
conversa).
"""
from __future__ import annotations

try:  # ticket automatico de erro (ver _scripts/erro_ticket.py e a skill /aft-erro)
    import sys as _sys
    from pathlib import Path as _Path
    _aqui = _Path(__file__).resolve()
    for _p in (_aqui.parent, *(_a / "_scripts" for _a in _aqui.parents)):
        if (_p / "erro_ticket.py").is_file():
            _sys.path.insert(0, str(_p))
            from erro_ticket import ativar as _ativar_ticket
            _ativar_ticket(__file__)
            break
except Exception:
    pass

import datetime
import json
import re
import subprocess
import sys
from pathlib import Path

# Console do Windows é cp1252: nunca deixar um acento derrubar o script.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

SIDECAR = ".diario-auto.jsonl"

# Rótulos curtos para a coluna Ação (o texto OFICIAL da tela do RI fica no
# diario_mensal.py, que monta a lista pronta para transcrição).
TIPOS = {
    "A": "Preparação/planejamento da fiscalização",
    "B": "Início da fiscalização",
    "C": "Inspeção/auditoria/entrevista no estabelecimento",
    "D": "Análise de documentos fora do estabelecimento",
    "E": "Elaboração de documentos / lançamento em sistemas",
    "F": "Fim da fiscalização",
}

RE_DATA_BR = re.compile(r"^(\d{2})/(\d{2})/(\d{4})$")
RE_LETRAS = re.compile(r"\[([A-F])\]")
RE_PREFIXO = re.compile(r"^((?:\[[A-F]\])+)\s*")


def parse_data_br(s: str) -> datetime.date | None:
    m = RE_DATA_BR.match(s.strip())
    if not m:
        return None
    try:
        return datetime.date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
    except ValueError:
        return None


def limites_secao(linhas: list[str]) -> tuple[int, int]:
    """(inicio, fim) do corpo de '## Registro de atividades' (fim exclusivo)."""
    ini = -1
    for i, l in enumerate(linhas):
        if l.strip().startswith("## ") and \
                l.strip()[3:].strip().startswith("Registro de atividades"):
            ini = i + 1
            break
    if ini < 0:
        return -1, -1
    fim = len(linhas)
    for i in range(ini, len(linhas)):
        if linhas[i].strip().startswith("## "):
            fim = i
            break
    return ini, fim


def letras_do_dia(linhas: list[str], ini: int, fim: int, data_br: str) -> set[str]:
    """Letras [A-F] já registradas na tabela para a data dada."""
    letras: set[str] = set()
    for i in range(ini, fim):
        s = linhas[i].strip()
        if not s.startswith("|"):
            continue
        celulas = [c.strip() for c in s.strip("|").split("|")]
        if len(celulas) >= 2 and celulas[0] == data_br:
            m = RE_PREFIXO.match(celulas[1])
            if m:
                letras.update(RE_LETRAS.findall(m.group(1)))
    return letras


def registrar_em_texto(texto: str, data_br: str, tipos: str,
                       acao: str = "", detalhe: str = "",
                       origem: str = "") -> tuple[str, dict]:
    """Acrescenta a linha classificada na tabela, deduplicando por (data,
    letra). Devolve (novo_texto, resumo). Cria a seção se não existir (fichas
    antigas / schema v2)."""
    pedidas = [t for t in dict.fromkeys(tipos.upper()) if t in TIPOS]
    if not pedidas:
        raise ValueError(f"tipos inválidos: {tipos!r} (use letras A-F)")
    if not parse_data_br(data_br):
        raise ValueError(f"data inválida: {data_br!r} (use dd/mm/aaaa)")

    linhas = texto.splitlines(keepends=True)
    ini, fim = limites_secao(linhas)
    if ini < 0:  # ficha sem a seção: cria no fim, com o cabeçalho da tabela
        if linhas and not linhas[-1].endswith("\n"):
            linhas[-1] += "\n"
        linhas += ["\n", "## Registro de atividades\n",
                   "| Data | Ação | Detalhes |\n",
                   "|------|------|----------|\n"]
        ini, fim = limites_secao(linhas)

    existentes = letras_do_dia(linhas, ini, fim, data_br)
    novas = [t for t in pedidas if t not in existentes]
    resumo = {"data": data_br, "tipos_novos": "".join(novas),
              "tipos_ja_registrados": "".join(t for t in pedidas if t in existentes)}
    if not novas:
        return texto, resumo

    rotulo = " ".join(f"[{t}]" for t in novas).replace("] [", "][")
    corpo = " ".join(acao.split()) or " + ".join(TIPOS[t] for t in novas)
    det = " ".join((detalhe or "").split())
    if origem and origem not in det:
        det = f"{det} ({origem})".strip() if det else origem
    corpo = corpo.replace("|", "/")
    det = det.replace("|", "/")
    nova = f"| {data_br} | {rotulo} {corpo} | {det} |\n"

    ultima_tab = -1
    for i in range(ini, fim):
        if linhas[i].strip().startswith("|"):
            ultima_tab = i
    if ultima_tab < 0:  # seção existe mas sem tabela: cria o cabeçalho
        linhas.insert(ini, "|------|------|----------|\n")
        linhas.insert(ini, "| Data | Ação | Detalhes |\n")
        ultima_tab = ini + 1
    linhas.insert(ultima_tab + 1, nova)
    return "".join(linhas), resumo


def resolver_memory(caminho: str) -> Path:
    p = Path(caminho).expanduser()
    if p.is_dir():
        p = p / "memory.md"
    if p.name != "memory.md" or not p.exists():
        raise ValueError(f"memory.md não encontrado em: {caminho}")
    return p.resolve()


def fazer_backup(mem: Path) -> None:
    backup = Path(__file__).resolve().parent / "backup_arquivo.py"
    if backup.exists():
        try:
            subprocess.run([sys.executable, str(backup), str(mem)],
                           capture_output=True, timeout=30)
        except Exception:
            pass  # backup é rede de segurança, nunca bloqueia o registro


# ── Modo gancho (hook PostToolUse) ───────────────────────────────────────────

def modo_hook() -> int:
    """Lê o evento do stdin; se for edição de um memory.md de OS ATIVAS,
    anota o dia no sidecar da OS. Silencioso e à prova de falha: um gancho
    que quebra ou demora atrapalha TODA edição de arquivo do AFT."""
    try:
        evento = json.load(sys.stdin)
        arq = (evento.get("tool_input") or {}).get("file_path") or ""
        p = Path(arq)
        if p.name != "memory.md" or p.parent.parent.name != "OS ATIVAS":
            return 0
        pasta = p.parent
        if not pasta.exists():
            return 0
        hoje = datetime.date.today().isoformat()
        sidecar = pasta / SIDECAR
        if sidecar.exists():
            try:
                conteudo = sidecar.read_text(encoding="utf-8", errors="replace")
                if f'"{hoje}"' in conteudo:
                    return 0  # dia já anotado
            except OSError:
                return 0
        linha = json.dumps({"data": hoje,
                            "hora": datetime.datetime.now().strftime("%H:%M"),
                            "origem": "hook"}, ensure_ascii=False)
        with sidecar.open("a", encoding="utf-8") as f:
            f.write(linha + "\n")
    except Exception:
        pass
    return 0


# ── CLI ──────────────────────────────────────────────────────────────────────

def valor_flag(argv: list[str], flag: str) -> str:
    if flag in argv:
        i = argv.index(flag)
        if i + 1 < len(argv):
            return argv[i + 1]
    return ""


def main() -> int:
    argv = sys.argv[1:]
    if "--hook" in argv:
        return modo_hook()

    pos, pular = [], False
    for a in argv:
        if pular:
            pular = False
        elif a in ("--tipos", "--data", "--detalhe", "--acao"):
            pular = True
        elif not a.startswith("--"):
            pos.append(a)
    if not pos:
        print(json.dumps({"ok": False, "erro": "informe a pasta da OS (ou o memory.md)"},
                         ensure_ascii=False))
        return 1
    tipos = valor_flag(argv, "--tipos")
    if not tipos:
        print(json.dumps({"ok": False, "erro": "informe --tipos (letras A-F, ex.: --tipos CE)"},
                         ensure_ascii=False))
        return 1
    data_br = valor_flag(argv, "--data") or datetime.date.today().strftime("%d/%m/%Y")

    try:
        mem = resolver_memory(pos[0])
        texto = mem.read_text(encoding="utf-8")
        novo, resumo = registrar_em_texto(
            texto, data_br, tipos,
            acao=valor_flag(argv, "--acao"),
            detalhe=valor_flag(argv, "--detalhe"))
        if novo != texto:
            fazer_backup(mem)
            mem.write_text(novo, encoding="utf-8")
            msg = f"registrado: {resumo['tipos_novos']} em {data_br}"
            if resumo["tipos_ja_registrados"]:
                msg += f" (já havia: {resumo['tipos_ja_registrados']})"
        else:
            msg = f"nada a fazer: {resumo['tipos_ja_registrados']} já registrado(s) em {data_br}"
        print(json.dumps({"ok": True, "os": mem.parent.name, **resumo, "msg": msg},
                         ensure_ascii=False, indent=2))
        return 0
    except (ValueError, OSError) as e:
        print(json.dumps({"ok": False, "erro": str(e)}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    sys.exit(main())
