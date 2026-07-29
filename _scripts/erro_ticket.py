#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
erro_ticket.py — quando alguma coisa do toolkit quebra, escreve um TICKET DE
CORREÇÃO: um arquivo .md pronto para o AFT encaminhar ao mantenedor, com tudo
que ele precisa para reproduzir e corrigir o defeito — e SEM nenhum dado de
empresa ou de trabalhador.

Duas portas de entrada:

1. AUTOMÁTICA (o caso comum). Todo script do toolkit chama `ativar()` logo no
   começo. Se o script morrer com uma exceção não tratada, em vez de um
   traceback cru na tela o AFT recebe:

       ==========================================================
         O AFT Toolkit encontrou um erro e preparou um TICKET.
         Arquivo: ...\\AFT\\tickets\\ticket-2026-07-29-1432.md
       ==========================================================

   O traceback original continua sendo impresso depois (o Claude precisa dele
   para diagnosticar na hora).

2. MANUAL, pela skill /aft-erro — para o que NÃO é exceção: a skill devolveu
   texto errado, o painel não abre, o .docx saiu torto. Aí quem descreve o
   problema é o AFT (ou o Claude, por ele).

O que entra no ticket: versão do toolkit (commit), sistema operacional, Python,
programas externos (zip, unzip, LibreOffice, Word), bibliotecas Python,
serviços do painel e o traceback. O que NÃO entra, nunca: nome de empresa,
CNPJ/CPF, nome de trabalhador, conteúdo de documento de fiscalização. Todo
texto passa por `_redigir()` antes de ser gravado.

Uso (linha de comando):
    python erro_ticket.py --mensagem "o painel abre em branco"
    python erro_ticket.py --mensagem "..." --skill /aft-painel --erro "<saída bruta>"
    python erro_ticket.py --listar
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import platform
import re
import shutil
import socket
import subprocess
import sys
import traceback
from pathlib import Path

SKILLS_DIR = Path(__file__).resolve().parent.parent
AQUI = Path(__file__).resolve().parent
PORTA_PAINEL = 8347

# Bibliotecas que o toolkit usa (mesma lista do /aft-doctor): nome no pip -> módulo.
LIBS = {
    "pillow": "PIL",
    "pikepdf": "pikepdf",
    "pypdf": "pypdf",
    "python-docx": "docx",
    "pdfplumber": "pdfplumber",
    "pillow-heif": "pillow_heif",
}


# ── Privacidade: nada de fiscalização sai daqui ─────────────────────────────

def _caminhos_sensiveis() -> list[tuple[str, str]]:
    """Pares (trecho literal, marcador) a esconder — do mais específico ao mais
    genérico, para o mais longo casar primeiro."""
    pares: list[tuple[str, str]] = []
    try:
        sys.path.insert(0, str(AQUI))
        from pasta_aft import pasta_aft as _pasta_aft
        pares.append((str(_pasta_aft()), "<PASTA AFT>"))
    except Exception:
        pass
    try:
        pares.append((str(Path.home()), "<HOME>"))
    except Exception:
        pass
    pares.sort(key=lambda p: len(p[0]), reverse=True)
    return pares


def _redigir(texto) -> str:
    """Remove de um texto qualquer tudo que possa identificar empresa,
    trabalhador ou o próprio AFT. Roda em TODO conteúdo antes de gravar."""
    if texto is None:
        return ""
    s = str(texto)

    # 1. Nome da empresa fiscalizada: o segmento logo depois de OS ATIVAS/ARQUIVADAS.
    s = re.sub(r"(OS\s+(?:ATIVAS|ARQUIVADAS))([\\/]+)([^\\/\r\n\"']+)",
               r"\1\2<EMPRESA>", s, flags=re.IGNORECASE)

    # 2. Inscrições (CNPJ/CPF), formatadas ou só dígitos.
    s = re.sub(r"\b\d{2}[.\s]?\d{3}[.\s]?\d{3}[/\s]?\d{4}[-\s]?\d{2}\b", "<INSCRICAO>", s)
    s = re.sub(r"\b\d{3}[.\s]?\d{3}[.\s]?\d{3}[-\s]?\d{2}\b", "<INSCRICAO>", s)
    s = re.sub(r"\b\d{11,14}\b", "<INSCRICAO>", s)

    # 3. E-mail.
    s = re.sub(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b", "<EMAIL>", s)

    # 4. Caminho da pasta de trabalho e da pasta pessoal (sem diferenciar
    #    maiúsculas: o Windows escreve o mesmo caminho de várias formas).
    for alvo, marca in _caminhos_sensiveis():
        if alvo:
            s = re.sub(re.escape(alvo), marca, s, flags=re.IGNORECASE)
            s = re.sub(re.escape(alvo.replace("\\", "/")), marca, s, flags=re.IGNORECASE)

    # 5. Nome da conta do usuário solto no texto.
    try:
        usuario = Path.home().name
        if usuario and len(usuario) > 2:
            s = re.sub(rf"\b{re.escape(usuario)}\b", "<USUARIO>", s, flags=re.IGNORECASE)
    except Exception:
        pass
    return s


# ── Coleta do ambiente ──────────────────────────────────────────────────────

def _rodar(cmd: list[str], timeout: int = 15) -> str:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout,
                           stdin=subprocess.DEVNULL, errors="replace")
        return ((r.stdout or "") + (r.stderr or "")).strip()
    except Exception:
        return ""


def versao_toolkit() -> dict:
    """Commit instalado, data, branch e se há alteração local não commitada."""
    info = {"commit": "?", "data": "?", "branch": "?", "sujo": "?"}
    if not (SKILLS_DIR / ".git").exists() or not shutil.which("git"):
        return info
    g = ["git", "-C", str(SKILLS_DIR)]
    info["commit"] = _rodar(g + ["rev-parse", "--short", "HEAD"]).splitlines()[:1] or ["?"]
    info["commit"] = info["commit"][0]
    info["data"] = (_rodar(g + ["log", "-1", "--format=%cd", "--date=short"])
                    .splitlines()[:1] or ["?"])[0]
    info["branch"] = (_rodar(g + ["rev-parse", "--abbrev-ref", "HEAD"])
                      .splitlines()[:1] or ["?"])[0]
    sujo = _rodar(g + ["status", "--porcelain"])
    info["sujo"] = f"{len(sujo.splitlines())} arquivo(s) alterado(s) localmente" if sujo else "nenhuma"
    return info


def _word_instalado() -> str:
    if not sys.platform.startswith("win"):
        return "n/a (não é Windows)"
    try:
        import winreg
        chave = r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\winword.exe"
        for raiz in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
            try:
                with winreg.OpenKey(raiz, chave) as k:
                    valor, _ = winreg.QueryValueEx(k, None)
                    if valor:
                        return f"sim ({Path(valor).name})"
            except OSError:
                continue
    except Exception:
        pass
    return "não encontrado"


def _porta_responde(porta: int) -> bool:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(2)
            return s.connect_ex(("127.0.0.1", porta)) == 0
    except Exception:
        return False


def _tarefa_existe(nome: str) -> bool:
    if sys.platform.startswith("win"):
        try:
            return subprocess.run(["schtasks", "/Query", "/TN", nome],
                                  capture_output=True).returncode == 0
        except OSError:
            return False
    if sys.platform == "darwin":
        return (Path.home() / "Library" / "LaunchAgents" / f"{nome}.plist").is_file()
    return False


def ambiente() -> list[tuple[str, str]]:
    """Lista (rótulo, valor) com o retrato da máquina. Só dado técnico."""
    from importlib.util import find_spec

    itens: list[tuple[str, str]] = []
    itens.append(("Sistema", platform.platform()))
    itens.append(("Python", f"{platform.python_version()} — {sys.executable}"))
    itens.append(("Encoding do console",
                  f"stdout={getattr(sys.stdout, 'encoding', '?')} · "
                  f"preferido={__import__('locale').getpreferredencoding(False)}"))
    itens.append(("Shell/terminal", os.environ.get("TERM_PROGRAM")
                  or os.environ.get("MSYSTEM") or os.environ.get("COMSPEC") or "?"))

    git = _rodar(["git", "--version"]) if shutil.which("git") else ""
    itens.append(("Git", git.splitlines()[0] if git else "NÃO ENCONTRADO"))

    for exe, para_que in (("zip", "compactar .docx"),
                          ("unzip", "descompactar .docx"),
                          ("soffice", "converter .docx em PDF"),
                          ("notebooklm", "consultar ementários")):
        onde = shutil.which(exe)
        itens.append((f"Programa `{exe}` ({para_que})", onde or "não instalado"))
    itens.append(("Microsoft Word", _word_instalado()))

    faltando = [nome for nome, mod in LIBS.items() if find_spec(mod) is None]
    itens.append(("Bibliotecas Python",
                  "todas instaladas" if not faltando else "FALTAM: " + ", ".join(faltando)))

    itens.append(("Servidor do painel (127.0.0.1:8347)",
                  "respondendo" if _porta_responde(PORTA_PAINEL) else "não responde"))
    if sys.platform.startswith("win"):
        itens.append(("Tarefa 'Painel AFT - Servidor'",
                      "instalada" if _tarefa_existe("Painel AFT - Servidor") else "não instalada"))
        itens.append(("Tarefa 'AFT Sessoes - Vigia'",
                      "instalada" if _tarefa_existe("AFT Sessoes - Vigia") else "não instalada"))

    # Pasta de trabalho: interessa a ORIGEM e o formato, nunca o caminho real.
    try:
        sys.path.insert(0, str(AQUI))
        from pasta_aft import diagnostico
        d = diagnostico()
        origem = {"ponteiro": "escolhida pelo AFT (ponteiro aft-pasta.txt)",
                  "env": "variável de ambiente PASTA_AFT",
                  "dados": "padrão (Documentos/AFT)"}.get(d.get("origem"), d.get("origem", "?"))
        extras = []
        if d.get("onedrive"):
            extras.append("dentro do OneDrive")
        if d.get("redirecionada"):
            extras.append("Documentos redirecionada")
        if d.get("fora_do_lugar"):
            extras.append("FORA da Documentos de verdade")
        itens.append(("Pasta de trabalho", origem + (f" · {', '.join(extras)}" if extras else "")))
        itens.append(("Auditorias em OS ATIVAS",
                      str(len(list(Path(d.get("os_ativas") or "").glob("*/memory.md"))))))
    except Exception as e:
        itens.append(("Pasta de trabalho", f"NÃO RESOLVIDA ({type(e).__name__}: {e})"))

    try:
        itens.append(("Skills instaladas", str(len(list(SKILLS_DIR.glob("*/SKILL.md"))))))
    except Exception:
        pass
    return itens


# ── Gravação do ticket ──────────────────────────────────────────────────────

def pasta_tickets() -> Path:
    """<pasta AFT>/tickets — e, se a pasta de trabalho não resolver (pode ser
    justamente o defeito), ~/.claude/aft-tickets."""
    try:
        sys.path.insert(0, str(AQUI))
        from pasta_aft import pasta_aft as _pasta_aft
        alvo = Path(_pasta_aft()) / "tickets"
        alvo.mkdir(parents=True, exist_ok=True)
        return alvo
    except Exception:
        alvo = Path.home() / ".claude" / "aft-tickets"
        alvo.mkdir(parents=True, exist_ok=True)
        return alvo


def _caminho_novo(pasta: Path) -> Path:
    agora = datetime.datetime.now()
    base = f"ticket-{agora:%Y-%m-%d-%H%M}"
    alvo = pasta / f"{base}.md"
    n = 2
    while alvo.exists():
        alvo = pasta / f"{base}-{n}.md"
        n += 1
    return alvo


def registrar(titulo: str, *, mensagem: str = "", script: str = "",
              skill: str = "", erro: str = "", automatico: bool = False) -> Path:
    """Escreve o ticket e devolve o caminho. Nunca levanta exceção."""
    try:
        return _registrar(titulo, mensagem, script, skill, erro, automatico)
    except Exception:
        # Último recurso: um ticket mínimo, para o defeito nunca ficar mudo.
        try:
            alvo = Path.home() / ".claude" / "aft-tickets"
            alvo.mkdir(parents=True, exist_ok=True)
            p = _caminho_novo(alvo)
            p.write_text(f"# Ticket (mínimo)\n\n{_redigir(titulo)}\n\n"
                         f"```\n{_redigir(erro)}\n```\n", encoding="utf-8")
            return p
        except Exception:
            return Path("(não foi possível gravar o ticket)")


def _registrar(titulo, mensagem, script, skill, erro, automatico) -> Path:
    v = versao_toolkit()
    agora = datetime.datetime.now()
    alvo = _caminho_novo(pasta_tickets())

    linhas: list[str] = []
    linhas.append(f"# Ticket de correção — AFT Toolkit")
    linhas.append("")
    linhas.append(f"**{_redigir(titulo)}**")
    linhas.append("")
    linhas.append("| | |")
    linhas.append("|---|---|")
    linhas.append(f"| Ticket | `{alvo.stem}` |")
    linhas.append(f"| Quando | {agora:%d/%m/%Y às %H:%M} |")
    linhas.append(f"| Origem | {'automático (o script quebrou)' if automatico else 'relatado pelo AFT'} |")
    linhas.append(f"| Versão do toolkit | commit `{v['commit']}` de {v['data']} (branch `{v['branch']}`) |")
    linhas.append(f"| Alterações locais | {v['sujo']} |")
    if skill:
        linhas.append(f"| Skill | `{_redigir(skill)}` |")
    if script:
        linhas.append(f"| Script | `{_redigir(script)}` |")
    linhas.append("")

    linhas.append("## O que aconteceu")
    linhas.append("")
    linhas.append(_redigir(mensagem).strip() or
                  "_(o script foi interrompido por um erro; veja o traceback abaixo)_")
    linhas.append("")

    if erro:
        linhas.append("## Erro (bruto)")
        linhas.append("")
        linhas.append("```")
        linhas.append(_redigir(erro).strip())
        linhas.append("```")
        linhas.append("")

    linhas.append("## Ambiente desta máquina")
    linhas.append("")
    linhas.append("| Item | Situação |")
    linhas.append("|---|---|")
    for rotulo, valor in ambiente():
        linhas.append(f"| {rotulo} | {_redigir(valor)} |")
    linhas.append("")

    linhas.append("## Como enviar")
    linhas.append("")
    linhas.append("Encaminhe **este arquivo** ao mantenedor do AFT Toolkit "
                  "(anexo, ou copiado e colado inteiro). Ele já traz a versão "
                  "instalada, o erro e o retrato da máquina.")
    linhas.append("")
    linhas.append("> **Privacidade:** este ticket é gerado com os dados de "
                  "fiscalização já removidos — nome de empresa, CNPJ/CPF, "
                  "e-mail e o caminho das suas pastas aparecem como `<EMPRESA>`, "
                  "`<INSCRICAO>`, `<EMAIL>`, `<PASTA AFT>`. Ainda assim, dê uma "
                  "lida antes de enviar: quem decide o que sai da sua máquina é você.")
    linhas.append("")

    alvo.write_text("\n".join(linhas) + "\n", encoding="utf-8")
    return alvo


# ── Gancho automático ───────────────────────────────────────────────────────

def _avisar_console(caminho: Path) -> None:
    """Aviso curto e SEM acentos (o console do Windows é cp1252 e engasga)."""
    barra = "=" * 66
    try:
        msg = (f"\n{barra}\n"
               f"  O AFT TOOLKIT ENCONTROU UM ERRO E PREPAROU UM TICKET.\n"
               f"  Arquivo: {caminho}\n"
               f"  Envie este arquivo ao mantenedor do toolkit - ele tem a\n"
               f"  versao instalada, o erro e o retrato desta maquina.\n"
               f"  Dados de empresa e de trabalhador ja foram removidos.\n"
               f"{barra}\n")
        sys.stderr.write(msg.encode("ascii", "replace").decode("ascii"))
        sys.stderr.flush()
    except Exception:
        pass


def ativar(script: str | None = None) -> None:
    """Instala o gancho que transforma um crash em ticket. Idempotente e
    inofensivo: se este arquivo estiver apenas sendo IMPORTADO por outro
    script, não faz nada (quem manda é o script principal)."""
    try:
        alvo = Path(script or sys.argv[0]).resolve()
        if not sys.argv or Path(sys.argv[0]).resolve() != alvo:
            return  # módulo importado, não é o programa em execução
    except Exception:
        return
    if getattr(sys, "_aft_ticket_ativo", False):
        return
    sys._aft_ticket_ativo = True

    anterior = sys.excepthook

    def _hook(tipo, valor, tb):
        try:
            if not issubclass(tipo, (KeyboardInterrupt, SystemExit, BrokenPipeError)):
                texto = "".join(traceback.format_exception(tipo, valor, tb))
                caminho = registrar(
                    f"{tipo.__name__} em {alvo.name}",
                    mensagem=f"O script `{alvo.name}` foi interrompido por um erro "
                             f"não tratado ao ser executado.",
                    script=str(alvo), erro=texto, automatico=True)
                _avisar_console(caminho)
        except Exception:
            pass
        anterior(tipo, valor, tb)  # o traceback original continua aparecendo

    sys.excepthook = _hook


# ── Linha de comando ────────────────────────────────────────────────────────

def main() -> int:
    ap = argparse.ArgumentParser(
        description="Gera um ticket de correção do AFT Toolkit (sem dados de fiscalização).")
    ap.add_argument("--mensagem", "-m", default="",
                    help="o que o AFT estava fazendo e o que deu errado")
    ap.add_argument("--titulo", "-t", default="", help="resumo em uma linha")
    ap.add_argument("--skill", default="", help="skill envolvida (ex.: /aft-painel)")
    ap.add_argument("--script", default="", help="script envolvido, se houver")
    ap.add_argument("--erro", default="", help="mensagem de erro bruta / traceback")
    ap.add_argument("--erro-arquivo", default="",
                    help="arquivo com a mensagem de erro (evita acento quebrado na linha de comando)")
    ap.add_argument("--listar", action="store_true", help="lista os tickets já gerados")
    ap.add_argument("--json", action="store_true", help="saída em JSON")
    a = ap.parse_args()

    if a.listar:
        pasta = pasta_tickets()
        achados = sorted(pasta.glob("ticket-*.md"), reverse=True)
        if a.json:
            print(json.dumps({"pasta": str(pasta), "tickets": [str(p) for p in achados]},
                             ensure_ascii=False, indent=2))
        else:
            print(f"Tickets em {pasta}:")
            for p in achados or []:
                print(f"  {p.name}")
            if not achados:
                print("  (nenhum)")
        return 0

    erro = a.erro
    if a.erro_arquivo:
        try:
            erro = Path(a.erro_arquivo).read_text(encoding="utf-8", errors="replace")
        except OSError as e:
            erro = f"(não consegui ler {a.erro_arquivo}: {e})"

    if not (a.mensagem or a.titulo or erro):
        ap.error("informe pelo menos --mensagem (o que deu errado).")

    titulo = a.titulo or (a.mensagem.strip().splitlines() or ["Problema relatado pelo AFT"])[0][:120]
    caminho = registrar(titulo, mensagem=a.mensagem, script=a.script,
                        skill=a.skill, erro=erro, automatico=False)
    if a.json:
        print(json.dumps({"ok": True, "ticket": str(caminho)}, ensure_ascii=False, indent=2))
    else:
        print(f"OK: ticket gerado em {caminho}")
    return 0


if __name__ == "__main__":
    ativar(__file__)
    sys.exit(main())
