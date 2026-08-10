#!/usr/bin/env python3
"""
servir_painel.py — modo INTERATIVO do painel AFT (servidor local).

Sobe um mini-servidor em http://127.0.0.1:8347 que serve o painel sempre
recém-gerado e aceita as AÇÕES MECÂNICAS dos cards (os controles só aparecem
no navegador quando o painel é aberto por este endereço, não pelo file://):

  - marcar/desmarcar uma notificação DET como respondida ([ ] ↔ [x]);
  - resolver uma pendência ([ ] → [x], com carimbo de data);
  - anotar uma constatação da auditoria (nova linha em Anotações da auditoria)
    ou marcá-la como tratada ([ ] → [x]);
  - registrar uma atividade (nova linha na tabela Registro de atividades);
  - mudar o status da OS (front-matter `status:`);
  - alternar embargo/interdição entre vigente/suspenso (front-matter
    `embargo_interdicao:`, preservando a descrição existente).

Cada escrita: backup do memory.md antes (via backup_arquivo.py, em .backups/),
edição cirúrgica da linha, e o painel é regenerado no próximo carregamento.
Ações que exigem julgamento (analisar resposta, gerar AI) NÃO passam por aqui —
o painel oferece botões que copiam o comando pronto para colar no Claude Code.

Só escuta em 127.0.0.1 (inacessível pela rede). Consumo: ~20 MB de RAM,
CPU zero enquanto ocioso. Sem dependências além da biblioteca padrão.

Uso:
    python servir_painel.py [PASTA_OS_ATIVAS] [--porta 8347] [--abrir]

  PASTA_OS_ATIVAS (opcional): padrão ~/Documents/AFT/OS ATIVAS
  --porta N       (opcional): porta local (padrão 8347)
  --abrir         (opcional): abre o navegador no painel ao iniciar

Se a porta já estiver em uso (servidor já rodando), apenas informa o endereço
e sai — pode chamar quantas vezes quiser.
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
import html
import json
import os
import re
import socket
import subprocess
import sys
import threading
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

AQUI = Path(__file__).resolve().parent
GERAR = AQUI / "gerar_painel.py"
BACKUP = AQUI / "backup_arquivo.py"
PORTA_PADRAO = 8347
MAX_BODY = 64_000

# Sync do DET via extensão Chrome "SisOS — Sync DET" (ver det_sync.py).
# CORS restrito ao site do DET: é de lá que a extensão dispara o fetch.
sys.path.insert(0, str(AQUI))
import det_sync  # noqa: E402

ORIGEM_DET = "https://auditor-det.sit.trabalho.gov.br"
CORS_DET = {
    "Access-Control-Allow-Origin": ORIGEM_DET,
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Allow-Private-Network": "true",
}

RE_FM = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
RE_CHECKBOX = re.compile(r"^(\s*-\s*\[)([ xX]?)(\]\s*)(.*)$")
STATUS_VALIDOS = {"em_andamento", "aguardando_resposta", "encerrada"}


def args_posicionais() -> list[str]:
    out, pular = [], False
    for i, a in enumerate(sys.argv[1:], 1):
        if pular:
            pular = False
            continue
        if a == "--porta":
            pular = True
        elif not a.startswith("--"):
            out.append(a)
    return out


def porta_escolhida() -> int:
    argv = sys.argv[1:]
    if "--porta" in argv:
        try:
            return int(argv[argv.index("--porta") + 1])
        except (IndexError, ValueError):
            pass
    return PORTA_PADRAO


def base_os() -> Path:
    pos = args_posicionais()
    if pos and pos[0].strip():
        return Path(pos[0])
    try:  # resolve a "Documentos" real (Windows: OneDrive/idioma)
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from pasta_aft import pasta_os_ativas
        return pasta_os_ativas()
    except Exception:
        return Path.home() / "Documents" / "AFT" / "OS ATIVAS"


# ── Edições cirúrgicas no memory.md ─────────────────────────────────────────

def limites_secao(linhas: list[str], titulos: tuple[str, ...]) -> tuple[int, int]:
    """(inicio, fim) das linhas do corpo da seção '## titulo' (fim exclusivo),
    ou (-1, -1) se não existir."""
    ini = -1
    for i, l in enumerate(linhas):
        if l.strip().startswith("## ") and l.strip()[3:].strip() in titulos:
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


def sem_comentario(s: str) -> str:
    return re.sub(r"<!--.*?-->", "", s).strip()


def acao_det(texto: str, codigo: str) -> tuple[str, str]:
    """Alterna [ ]/[x] na linha da notificação DET com o código dado."""
    linhas = texto.splitlines(keepends=True)
    ini, fim = limites_secao(linhas, ("Notificações DET", "Notificacoes DET"))
    if ini < 0:
        raise ValueError("seção 'Notificações DET' não encontrada")
    for i in range(ini, fim):
        m = RE_CHECKBOX.match(linhas[i].rstrip("\n"))
        if m and codigo in m.group(4):
            novo = " " if m.group(2).strip().lower() == "x" else "x"
            fim_l = "\n" if linhas[i].endswith("\n") else ""
            linhas[i] = m.group(1) + novo + m.group(3) + m.group(4) + fim_l
            estado = "respondida" if novo == "x" else "reaberta"
            return "".join(linhas), f"DET {codigo} marcada como {estado}"
    raise ValueError(f"notificação {codigo} não encontrada no memory.md")


def acao_pendencia(texto: str, alvo: str) -> tuple[str, str]:
    """Marca [x] a pendência em aberto cujo texto visível bate com `alvo`."""
    linhas = texto.splitlines(keepends=True)
    ini, fim = limites_secao(linhas, ("Pendências", "Pendencias"))
    if ini < 0:
        raise ValueError("seção 'Pendências' não encontrada")
    hoje = datetime.date.today().strftime("%d/%m/%Y")
    for i in range(ini, fim):
        m = RE_CHECKBOX.match(linhas[i].rstrip("\n"))
        if m and m.group(2).strip().lower() != "x" \
                and sem_comentario(m.group(4)) == alvo.strip():
            fim_l = "\n" if linhas[i].endswith("\n") else ""
            linhas[i] = (m.group(1) + "x" + m.group(3) + m.group(4)
                         + f" <!-- resolvida em {hoje} (painel) -->" + fim_l)
            return "".join(linhas), "pendência resolvida"
    raise ValueError("pendência não encontrada (ou já resolvida)")


RE_DETALHE_DET = re.compile(r"^\s+-\s+lavrada\s", re.IGNORECASE)
RE_ULT_ENTREGA = re.compile(r"última entrega\s+(\d{2})/(\d{2})/(\d{4})",
                            re.IGNORECASE)


def acao_det_visto(texto: str, codigo: str) -> tuple[str, str]:
    """Dispensa o alerta '⚠️ atualização pendente' de uma notificação DET:
    remove o alerta da sub-linha de detalhes e grava `<!-- visto: X -->`
    (X = última entrega, ou 'sem-entrega'). O det_sync respeita o marcador
    e só reexibe o alerta se a empresa fizer entrega NOVA."""
    linhas = texto.splitlines(keepends=True)
    ini, fim = limites_secao(linhas, ("Notificações DET", "Notificacoes DET"))
    if ini < 0:
        raise ValueError("seção 'Notificações DET' não encontrada")
    for i in range(ini, fim):
        m = RE_CHECKBOX.match(linhas[i].rstrip("\n"))
        if not (m and codigo in m.group(4)):
            continue
        if i + 1 >= fim or not RE_DETALHE_DET.match(linhas[i + 1]):
            raise ValueError(f"notificação {codigo} sem sub-linha de detalhes")
        det = linhas[i + 1].rstrip("\n")
        me = RE_ULT_ENTREGA.search(det)
        visto = f"{me.group(3)}-{me.group(2)}-{me.group(1)}" if me else "sem-entrega"
        det = det.replace(" · ⚠️ atualização pendente", "")
        det = re.sub(r"\s*<!--\s*visto:[^>]*-->", "", det)
        linhas[i + 1] = f"{det} <!-- visto: {visto} -->\n"
        return "".join(linhas), f"alerta da {codigo} dispensado (volta se houver entrega nova)"
    raise ValueError(f"notificação {codigo} não encontrada no memory.md")


def acao_anotacao_ok(texto: str, alvo: str) -> tuple[str, str]:
    """Marca [x] a anotação em aberto cujo texto visível bate com `alvo`."""
    linhas = texto.splitlines(keepends=True)
    ini, fim = limites_secao(linhas, ("Anotações da auditoria", "Anotacoes da auditoria"))
    if ini < 0:
        raise ValueError("seção 'Anotações da auditoria' não encontrada")
    hoje = datetime.date.today().strftime("%d/%m/%Y")
    for i in range(ini, fim):
        m = RE_CHECKBOX.match(linhas[i].rstrip("\n"))
        if m and m.group(2).strip().lower() != "x" \
                and sem_comentario(m.group(4)) == alvo.strip():
            fim_l = "\n" if linhas[i].endswith("\n") else ""
            linhas[i] = (m.group(1) + "x" + m.group(3) + m.group(4)
                         + f" <!-- tratada em {hoje} (painel) -->" + fim_l)
            return "".join(linhas), "anotação marcada como tratada"
    raise ValueError("anotação não encontrada (ou já tratada)")


def acao_anotacao_add(texto: str, descricao: str) -> tuple[str, str]:
    """Acrescenta '- [ ] dd/mm/aaaa — texto' em '## Anotações da auditoria'.
    Cria a seção (antes de 'Registro de atividades', ou no fim) se faltar."""
    descricao = " ".join(descricao.split())
    if not descricao:
        raise ValueError("anotação vazia")
    hoje = datetime.date.today().strftime("%d/%m/%Y")
    nova = f"- [ ] {hoje} — {descricao}\n"
    linhas = texto.splitlines(keepends=True)
    ini, fim = limites_secao(linhas, ("Anotações da auditoria", "Anotacoes da auditoria"))
    if ini < 0:
        # Seção ausente: cria antes de 'Registro de atividades', senão no fim.
        bloco = f"## Anotações da auditoria\n{nova}\n"
        reg_ini = -1
        for i, l in enumerate(linhas):
            if l.strip().startswith("## ") and l.strip()[3:].strip().startswith("Registro de atividades"):
                reg_ini = i
                break
        if reg_ini >= 0:
            linhas.insert(reg_ini, bloco)
        else:
            if linhas and not linhas[-1].endswith("\n"):
                linhas[-1] += "\n"
            linhas.append("\n" + bloco)
        return "".join(linhas), "anotação registrada"
    # Seção existe: remove placeholder '_(vazio)_' e insere após o cabeçalho.
    ins = ini
    for i in range(ini, fim):
        if linhas[i].strip() == "_(vazio)_":
            linhas.pop(i)
            fim -= 1
            break
    linhas.insert(ins, nova)
    return "".join(linhas), "anotação registrada"


def acao_atividade(texto: str, descricao: str) -> tuple[str, str]:
    """Acrescenta uma linha na tabela Registro de atividades (data de hoje)."""
    descricao = " ".join(descricao.split())
    if not descricao:
        raise ValueError("descrição vazia")
    if "|" in descricao:
        descricao = descricao.replace("|", "/")
    linhas = texto.splitlines(keepends=True)
    ini, fim = limites_secao(linhas, ("Registro de atividades",))
    if ini < 0:
        raise ValueError("seção 'Registro de atividades' não encontrada")
    ultima_tab = -1
    for i in range(ini, fim):
        if linhas[i].strip().startswith("|"):
            ultima_tab = i
    if ultima_tab < 0:
        raise ValueError("tabela do Registro de atividades não encontrada")
    hoje = datetime.date.today().strftime("%d/%m/%Y")
    nova = f"| {hoje} | {descricao} | painel |\n"
    linhas.insert(ultima_tab + 1, nova)
    return "".join(linhas), "atividade registrada"


def editar_fm(texto: str, chave: str, valor: str) -> str:
    """Troca (ou insere) `chave: valor` no front-matter."""
    m = RE_FM.match(texto)
    if not m:
        raise ValueError("memory.md sem front-matter")
    fm = m.group(1)
    if re.search(rf"^{chave}\s*:", fm, re.MULTILINE):
        fm_novo = re.sub(rf"^{chave}\s*:.*$", f"{chave}: {valor}", fm,
                         count=1, flags=re.MULTILINE)
    else:
        fm_novo = fm + f"\n{chave}: {valor}"
    return texto[:m.start(1)] + fm_novo + texto[m.end(1):]


def acao_status(texto: str, valor: str) -> tuple[str, str]:
    if valor not in STATUS_VALIDOS:
        raise ValueError(f"status inválido: {valor}")
    return editar_fm(texto, "status", valor), f"status → {valor}"


def acao_embargo(texto: str, estado: str) -> tuple[str, str]:
    """Alterna vigente/suspenso preservando a descrição já registrada."""
    if estado not in ("vigente", "suspenso"):
        raise ValueError(f"estado inválido: {estado}")
    m = RE_FM.match(texto)
    atual = ""
    if m:
        vm = re.search(r"^embargo_interdicao\s*:\s*(.*)$", m.group(1), re.MULTILINE)
        if vm:
            atual = vm.group(1).strip().strip('"').strip("'")
            if atual in ("null", "~"):
                atual = ""
    desc = re.sub(r"\s*[—–-]\s*(vigente|suspenso)\s*$", "", atual,
                  flags=re.IGNORECASE).strip()
    if desc.lower() in ("vigente", "suspenso"):
        desc = ""
    novo = f"{desc} — {estado}" if desc else estado
    return (editar_fm(texto, "embargo_interdicao", novo),
            f"embargo/interdição → {novo}")


ACOES = {
    "det": lambda t, p: acao_det(t, p.get("codigo", "")),
    "det_visto": lambda t, p: acao_det_visto(t, p.get("codigo", "")),
    "pendencia": lambda t, p: acao_pendencia(t, p.get("texto", "")),
    "anotacao_ok": lambda t, p: acao_anotacao_ok(t, p.get("texto", "")),
    "anotacao_add": lambda t, p: acao_anotacao_add(t, p.get("texto", "")),
    "atividade": lambda t, p: acao_atividade(t, p.get("texto", "")),
    "status": lambda t, p: acao_status(t, p.get("valor", "")),
    "embargo": lambda t, p: acao_embargo(t, p.get("estado", "")),
}


# ── Visualização de relatórios .md (rota /doc/) ──────────────────────────────
# Os relatórios das skills (analise-preliminar-*.md, autos-lavrados.md etc.)
# são a fonte de verdade em markdown; esta rota os converte em HTML legível
# on-the-fly, na mesma paleta do painel. Nada é gravado em disco.

def _md_inline(s: str) -> str:
    s = html.escape(s)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\[([^\]]+)\]\((https?://[^)\s]+)\)",
               r'<a href="\2" target="_blank" rel="noopener">\1</a>', s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"(?<!\*)\*([^*\s][^*]*)\*(?!\*)", r"<i>\1</i>", s)
    return s


def md_para_html(md: str) -> str:
    """Conversor mínimo (stdlib) do subconjunto de markdown usado nos
    relatórios do ecossistema: títulos, negrito/itálico/código, links,
    listas (inclusive aninhadas), citações, blocos de código, tabelas e
    réguas. O que não reconhece vira parágrafo."""
    m = RE_FM.match(md)
    if m:  # front-matter não interessa ao leitor
        md = md[m.end():]
    out: list[str] = []
    listas: list[tuple[int, str]] = []  # pilha (indentação, "ul"|"ol") abertas
    tabela: list[str] = []
    quote = False
    codigo: list[str] | None = None     # linhas do bloco ``` aberto

    def fecha_listas(indent: int = -1):
        while listas and listas[-1][0] > indent:
            out.append(f"</{listas.pop()[1]}>")

    def fecha_quote():
        nonlocal quote
        if quote:
            out.append("</blockquote>")
            quote = False

    def fecha_tabela():
        nonlocal tabela
        if not tabela:
            return
        linhas = [l for l in tabela if not re.match(r"^\s*\|?[\s:|-]+\|?\s*$", l)]
        for j, l in enumerate(linhas):
            cels = [c.strip() for c in l.strip().strip("|").split("|")]
            tag = "th" if j == 0 else "td"
            out.append("<tr>" + "".join(f"<{tag}>{_md_inline(c)}</{tag}>"
                                        for c in cels) + "</tr>")
        if linhas:
            out.insert(len(out) - len(linhas), "<table>")
            out.append("</table>")
        tabela = []

    for linha in md.splitlines():
        if codigo is not None:              # dentro de um bloco ``` ... ```
            if linha.strip().startswith("```"):
                out.append("<pre><code>" + html.escape("\n".join(codigo))
                           + "</code></pre>")
                codigo = None
            else:
                codigo.append(linha)
            continue
        s = linha.strip()
        if s.startswith("```"):
            fecha_listas()
            fecha_quote()
            fecha_tabela()
            codigo = []
            continue
        if s.startswith("|"):
            fecha_listas()
            fecha_quote()
            tabela.append(s)
            continue
        fecha_tabela()
        m_h = re.match(r"^(#{1,4})\s+(.*)$", s)
        m_ul = re.match(r"^[-*]\s+(.*)$", s)
        m_ol = re.match(r"^\d+[.)]\s+(.*)$", s)
        if m_h:
            fecha_listas()
            fecha_quote()
            n = len(m_h.group(1))
            out.append(f"<h{n}>{_md_inline(m_h.group(2))}</h{n}>")
        elif m_ul or m_ol:
            fecha_quote()
            tipo = "ul" if m_ul else "ol"
            ind = len(linha) - len(linha.lstrip())
            fecha_listas(ind)               # fecha níveis mais fundos que este
            if not listas or listas[-1][0] < ind:
                out.append(f"<{tipo}>")
                listas.append((ind, tipo))
            elif listas[-1][1] != tipo:     # mesmo nível, trocou ul<->ol
                out.append(f"</{listas.pop()[1]}>")
                out.append(f"<{tipo}>")
                listas.append((ind, tipo))
            item = (m_ul or m_ol).group(1)
            # Checkbox de tarefa ("- [ ] item" / "- [x] item"): vira caixinha
            # em vez dos colchetes crus. Os relatórios do toolkit são cheios
            # deles (checklists, ementas da OS, autos lavrados, pendências).
            m_cb = re.match(r"^\[([ xX])\]\s+(.*)$", item)
            if m_cb:
                feito = m_cb.group(1).lower() == "x"
                classe = "tarefa feita" if feito else "tarefa"
                marca = "&#9745;" if feito else "&#9744;"   # ☑ / ☐
                out.append(f'<li class="{classe}"><span class="cb">{marca}</span>'
                           f"{_md_inline(m_cb.group(2))}</li>")
            else:
                out.append(f"<li>{_md_inline(item)}</li>")
        elif s.startswith(">"):
            fecha_listas()
            if not quote:
                out.append("<blockquote>")
                quote = True
            corpo = s.lstrip(">").strip()
            if corpo:
                out.append(f"<p>{_md_inline(corpo)}</p>")
        elif s in ("---", "***", "___"):
            fecha_listas()
            fecha_quote()
            out.append("<hr>")
        elif s:
            fecha_listas()
            fecha_quote()
            out.append(f"<p>{_md_inline(s)}</p>")
        else:
            fecha_listas()
            fecha_quote()
    fecha_listas()
    fecha_quote()
    fecha_tabela()
    if codigo is not None:                  # ``` que ficou sem fechar
        out.append("<pre><code>" + html.escape("\n".join(codigo))
                   + "</code></pre>")
    return "\n".join(out)


DOC_CSS = """
:root{--cream:#F0EEE6;--paper:#FAF9F5;--coral:#CC785C;--coral-deep:#B0593E;
--t1:#141413;--t2:#5A574E;--t3:#8F8B7D;--bd:#DDD9CC;--bds:#E8E4D6;
--teal:#4F8A7C;--serif:'Source Serif 4',Georgia,'Times New Roman',serif;}
*{box-sizing:border-box}
body{margin:0;background:var(--cream);color:var(--t1);font:15.5px/1.6 var(--serif)}
main{width:min(96vw,max(80vw,860px));margin:0 auto;
padding:36px clamp(16px,4vw,48px) 80px;
background:var(--paper);min-height:100vh;border-left:1px solid var(--bds);
border-right:1px solid var(--bds)}
h1{font-size:25px;font-weight:600;margin:0 0 14px;line-height:1.3}
h1 em{color:var(--coral);font-style:italic}
h2{font-size:14px;letter-spacing:.08em;text-transform:uppercase;color:var(--t3);
border-bottom:1px solid var(--bds);padding-bottom:5px;margin:32px 0 12px}
h3{font-size:16.5px;font-weight:600;margin:24px 0 8px;color:var(--coral-deep)}
h4{font-size:14.5px;margin:18px 0 6px}
p{margin:8px 0}
ul,ol{margin:8px 0;padding-left:24px}
li{margin-bottom:6px}
li.tarefa{list-style:none;margin-left:-20px}
li.tarefa .cb{display:inline-block;width:20px;color:var(--coral);font-size:17px}
li.tarefa.feita{color:var(--t2)}
li.tarefa.feita .cb{color:var(--teal)}
code{background:var(--cream);border:1px solid var(--bds);border-radius:4px;
padding:1px 5px;font-size:13px}
pre{background:var(--cream);border:1px solid var(--bds);border-radius:6px;
padding:10px 12px;overflow-x:auto;font-size:13px;line-height:1.45}
pre code{background:none;border:none;padding:0}
blockquote{border-left:3px solid var(--coral);margin:10px 0;padding:2px 14px;
color:var(--t2)}
main a{color:var(--coral-deep)}
hr{border:none;border-top:1px solid var(--bds);margin:24px 0}
table{border-collapse:collapse;margin:12px 0;font-size:14px;width:100%}
th,td{border:1px solid var(--bds);padding:6px 10px;text-align:left;vertical-align:top}
th{background:var(--cream);font-weight:600}
.topo{font-size:12.5px;color:var(--t3);margin-bottom:22px}
.topo a{color:var(--coral-deep)}
@media print{main{border:none}.topo{display:none}}
@media (prefers-color-scheme: dark){
:root{--cream:#191917;--paper:#211F1C;--t1:#EDEAE0;--t2:#B5B0A1;--t3:#8F8B7D;
--bd:#3A372F;--bds:#2E2B25}}
"""


def pagina_doc(titulo: str, corpo: str, pasta: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(titulo)}</title>
<style>{DOC_CSS}</style>
</head>
<body>
<main>
<div class="topo"><a href="/">← painel</a> · {html.escape(pasta)} · {html.escape(titulo)}</div>
{corpo}
</main>
</body>
</html>
"""


# ── Cache da geração do painel ───────────────────────────────────────────────
# Gerar o painel varre todas as OS e lê a 1ª página dos PDFs de notificação:
# com uma dezena de auditorias isso passa de 10 segundos. Regerar a CADA
# carregamento fazia o painel parecer travado e chegava a derrubar a checagem
# do /aft-doctor por tempo esgotado. Agora só regeramos quando alguma coisa
# mudou de verdade.

_cache_lock = threading.Lock()
_cache_assinatura: tuple | None = None


def assinatura_os(base: Path) -> tuple:
    """Retrato barato do conteúdo das OS: quantidade de arquivos, a data de
    modificação mais recente entre as PASTAS (que muda quando entra ou sai
    arquivo, ex.: um PDF novo de notificação) e entre os memory.md, mais a
    versão do gerador. Só faz stat de diretório e de ficha — nunca abre um
    PDF —, então custa milissegundos."""
    n_arquivos = 0
    mais_novo = 0.0
    for raiz, _dirs, arquivos in os.walk(base):
        n_arquivos += len(arquivos)
        try:
            mais_novo = max(mais_novo, os.stat(raiz).st_mtime)
        except OSError:
            pass
        if "memory.md" in arquivos:
            try:
                mais_novo = max(mais_novo, os.stat(os.path.join(raiz, "memory.md")).st_mtime)
            except OSError:
                pass
    try:
        versao_gerador = GERAR.stat().st_mtime
    except OSError:
        versao_gerador = 0.0
    return (n_arquivos, round(mais_novo, 3), versao_gerador)


def garantir_painel(base: Path, painel: Path) -> None:
    """Regera o painel.html se (e só se) algo mudou desde a última geração.
    Serializado: dois carregamentos simultâneos não disparam duas varreduras."""
    global _cache_assinatura
    with _cache_lock:
        try:
            agora = assinatura_os(base)
        except Exception:
            agora = None
        if agora is not None and agora == _cache_assinatura and painel.exists():
            return
        try:
            subprocess.run([sys.executable, str(GERAR), str(base)],
                           capture_output=True, timeout=180)
            _cache_assinatura = agora
        except Exception:
            pass  # serve o painel anterior, se existir


# ── Servidor ─────────────────────────────────────────────────────────────────

class Handler(BaseHTTPRequestHandler):
    base: Path  # definido em servir()

    def log_message(self, fmt, *args):  # silencioso
        pass

    def _responde(self, code: int, corpo: bytes, ctype: str,
                  extra: dict | None = None):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(corpo)))
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(corpo)

    def _json(self, code: int, obj: dict, extra: dict | None = None):
        self._responde(code, json.dumps(obj, ensure_ascii=False).encode("utf-8"),
                       "application/json; charset=utf-8", extra)

    def _host_ok(self) -> bool:
        host = (self.headers.get("Host") or "").split(":")[0]
        return host in ("127.0.0.1", "localhost")

    def do_GET(self):
        if not self._host_ok():
            return self._json(403, {"ok": False, "erro": "host não permitido"})
        if self.path in ("/", "/index.html", "/painel.html"):
            painel = self.base.parent / "painel.html"
            garantir_painel(self.base, painel)
            if not painel.exists():
                return self._responde(404, "painel.html não encontrado — rode a skill /aft-painel"
                                      .encode("utf-8"), "text/plain; charset=utf-8")
            self._responde(200, painel.read_bytes(), "text/html; charset=utf-8")
        elif self.path == "/api/ping":
            # Responde na hora, sem varrer nada: é por aqui que o /aft-doctor
            # confere se o servidor está no ar — e QUAL pasta ele está
            # servindo, que é o que denuncia um servidor sobrevivente
            # apontando para a pasta de antes de uma mudança de lugar.
            self._json(200, {"ok": True, "painel_aft": True,
                             "os_ativas": str(self.base), "pid": os.getpid()})
        elif self.path == "/api/estado":
            # Carimbo da última mudança nas fichas: o maior mtime dos memory.md.
            # O painel aberto consulta isto a cada poucos segundos e recarrega
            # quando muda (ex.: logo após o sync da extensão DET gravar).
            try:
                mts = [m.stat().st_mtime for m in self.base.glob("*/memory.md")]
                self._json(200, {"ok": True,
                                 "estado": max(mts) if mts else 0,
                                 "fichas": len(mts)})
            except OSError as e:
                self._json(500, {"ok": False, "erro": str(e)})
        elif self.path.startswith("/doc/"):
            self._serve_doc()
        else:
            self._json(404, {"ok": False, "erro": "rota desconhecida"})

    def _serve_doc(self):
        """GET /doc/<pasta-da-OS>/<arquivo>.md — renderiza o relatório em HTML.
        <arquivo> pode ter 1 nível de subpasta (interdicao-embargo/autos.md,
        Acidentes/Relatorio-*.md). Mesma validação de caminho do /api/acao:
        só .md dentro de OS ATIVAS."""
        try:
            partes = self.path[len("/doc/"):].split("/")
            if len(partes) not in (2, 3):
                raise ValueError("use /doc/<pasta>/[subpasta/]<arquivo>.md")
            pasta = urllib.parse.unquote(partes[0]).strip()
            arquivo = "/".join(urllib.parse.unquote(p).strip() for p in partes[1:])
            segs = arquivo.split("/")
            if (not pasta or "/" in pasta or "\\" in pasta or pasta.startswith(".")
                    or "\\" in arquivo or len(segs) > 2
                    or any((not s) or s.startswith(".") for s in segs)
                    or not arquivo.endswith(".md")):
                raise ValueError("caminho inválido")
            alvo = (self.base / pasta / arquivo).resolve()
            if self.base.resolve() not in alvo.parents or not alvo.exists():
                raise ValueError(f"{arquivo} não encontrado em {pasta}")
            corpo = md_para_html(alvo.read_text(encoding="utf-8", errors="replace"))
            pag = pagina_doc(arquivo, corpo, pasta)
            self._responde(200, pag.encode("utf-8"), "text/html; charset=utf-8")
        except ValueError as e:
            self._responde(404, html.escape(str(e)).encode("utf-8"),
                           "text/plain; charset=utf-8")
        except Exception as e:
            self._responde(500, f"{type(e).__name__}: {e}".encode("utf-8"),
                           "text/plain; charset=utf-8")

    def do_OPTIONS(self):
        # Preflight do navegador para o POST /api/det-sync vindo do site do DET.
        if self.path == "/api/det-sync":
            self._responde(204, b"", "text/plain", CORS_DET)
        else:
            self._responde(204, b"", "text/plain")

    def do_POST(self):
        if not self._host_ok():
            return self._json(403, {"ok": False, "erro": "host não permitido"})
        if self.path == "/api/det-sync":
            return self._det_sync()
        if self.path != "/api/acao":
            return self._json(404, {"ok": False, "erro": "rota desconhecida"})
        try:
            n = min(int(self.headers.get("Content-Length") or 0), MAX_BODY)
            p = json.loads(self.rfile.read(n).decode("utf-8"))
            acao = p.get("acao")
            if acao not in ACOES:
                raise ValueError(f"ação desconhecida: {acao}")
            pasta = (p.get("pasta") or "").strip()
            if not pasta or "/" in pasta or "\\" in pasta or pasta.startswith("."):
                raise ValueError("pasta inválida")
            mem = (self.base / pasta / "memory.md").resolve()
            if self.base.resolve() not in mem.parents or not mem.exists():
                raise ValueError(f"memory.md não encontrado em {pasta}")
            texto = mem.read_text(encoding="utf-8")
            novo, msg = ACOES[acao](texto, p)
            if BACKUP.exists():
                subprocess.run([sys.executable, str(BACKUP), str(mem)],
                               capture_output=True, timeout=30)
            mem.write_text(novo, encoding="utf-8")
            self._json(200, {"ok": True, "msg": msg})
        except ValueError as e:
            self._json(400, {"ok": False, "erro": str(e)})
        except Exception as e:
            self._json(500, {"ok": False, "erro": f"{type(e).__name__}: {e}"})

    def _det_sync(self):
        """POST /api/det-sync — corpo {det_access_token}; chamado pela
        extensão Chrome. O token vive só nesta requisição (nunca em disco)."""
        try:
            n = min(int(self.headers.get("Content-Length") or 0), MAX_BODY)
            p = json.loads(self.rfile.read(n).decode("utf-8"))
            token = p.get("det_access_token")
            if not token or not isinstance(token, str) or token.count(".") != 2:
                return self._json(400, {"ok": False,
                                        "erro": "det_access_token ausente ou inválido"},
                                  CORS_DET)
            resultado = det_sync.sincronizar_todas(self.base, token)
            self._json(200, resultado, CORS_DET)
        except Exception as e:
            self._json(500, {"ok": False, "erro": f"{type(e).__name__}: {e}"},
                       CORS_DET)


def porta_ocupada(porta: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", porta)) == 0


def main() -> int:
    base = base_os()
    porta = porta_escolhida()
    url = f"http://127.0.0.1:{porta}"
    if not base.exists():
        print(f"ERRO: pasta de OS não existe: {base}", file=sys.stderr)
        return 1
    if porta_ocupada(porta):
        print(f"Painel interativo já está no ar: {url}")
        if "--abrir" in sys.argv[1:]:
            webbrowser.open(url)
        return 0
    Handler.base = base
    srv = ThreadingHTTPServer(("127.0.0.1", porta), Handler)
    print(f"Painel interativo no ar: {url}  (OS: {base})")
    print("Ctrl+C para encerrar. Consumo ocioso ~20 MB de RAM, CPU 0%.")
    if "--abrir" in sys.argv[1:]:
        webbrowser.open(url)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nencerrado.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
