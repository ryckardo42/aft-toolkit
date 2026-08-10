#!/usr/bin/env python3
"""
instalar_rotina_pendencias.py — instala/remove/consulta o AVISO SEMANAL de
pendências (notificar_pendencias.py) como agendamento do PRÓPRIO sistema
operacional: toda SEGUNDA-FEIRA no horário configurado (padrão 08:00), o SO
chama o Python diretamente — zero tokens, zero Claude Code.

Uso:
    python instalar_rotina_pendencias.py instalar <python_path> <pasta_os_ativas> [--hora HH:MM]
    python instalar_rotina_pendencias.py remover
    python instalar_rotina_pendencias.py status

Imprime um JSON no stdout: {"ok": bool, "sistema": "...", "detalhe": "...",
"acao": "..."}. Nunca lança exceção não tratada.
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

import json
import subprocess
import sys
from pathlib import Path

NOME_TAREFA = "Painel AFT - Pendencias da semana"
LABEL_LAUNCHD = "br.aft.pendencias"


def script_notificador() -> Path:
    return Path(__file__).resolve().parent / "notificar_pendencias.py"


def resultado(ok: bool, sistema: str, detalhe: str, acao: str) -> int:
    print(json.dumps({"ok": ok, "sistema": sistema, "detalhe": detalhe, "acao": acao},
                     ensure_ascii=False, indent=2))
    return 0 if ok else 1


# ── macOS (launchd) ──────────────────────────────────────────────────────────

def plist_path() -> Path:
    return Path.home() / "Library" / "LaunchAgents" / f"{LABEL_LAUNCHD}.plist"


def instalar_macos(python_path: str, pasta_os: str, hora: int, minuto: int) -> int:
    plist = plist_path()
    plist.parent.mkdir(parents=True, exist_ok=True)
    log = str(Path.home() / "Library" / "Logs" / "aft-pendencias.log")
    conteudo = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>{LABEL_LAUNCHD}</string>
  <key>ProgramArguments</key>
  <array>
    <string>{python_path}</string>
    <string>{script_notificador()}</string>
    <string>{pasta_os}</string>
  </array>
  <key>StartCalendarInterval</key>
  <dict>
    <key>Weekday</key><integer>1</integer>
    <key>Hour</key><integer>{hora}</integer>
    <key>Minute</key><integer>{minuto}</integer>
  </dict>
  <key>StandardOutPath</key><string>{log}</string>
  <key>StandardErrorPath</key><string>{log}</string>
</dict>
</plist>
"""
    plist.write_text(conteudo, encoding="utf-8")
    subprocess.run(["launchctl", "unload", str(plist)], capture_output=True)
    r = subprocess.run(["launchctl", "load", str(plist)], capture_output=True, text=True)
    if r.returncode != 0:
        return resultado(False, "macOS",
                         f"launchctl load falhou: {r.stderr.strip() or r.stdout.strip()}",
                         "instalar")
    return resultado(True, "macOS",
                     f"Aviso semanal instalado em {plist} — toda segunda às "
                     f"{hora:02d}:{minuto:02d}. Log em {log}.", "instalar")


def remover_macos() -> int:
    plist = plist_path()
    subprocess.run(["launchctl", "unload", str(plist)], capture_output=True)
    if plist.exists():
        plist.unlink()
    return resultado(True, "macOS", "Aviso semanal removido.", "remover")


def status_macos() -> int:
    plist = plist_path()
    if not plist.exists():
        return resultado(True, "macOS", "Aviso semanal não instalado.", "status")
    r = subprocess.run(["launchctl", "list"], capture_output=True, text=True)
    ativo = LABEL_LAUNCHD in r.stdout
    return resultado(True, "macOS",
                     f"Aviso semanal instalado em {plist} — "
                     f"{'ativo' if ativo else 'inativo (rode launchctl load)'}.",
                     "status")


# ── Windows (Agendador de Tarefas) ──────────────────────────────────────────

def instalar_windows(python_path: str, pasta_os: str, hora: int, minuto: int) -> int:
    comando = f'"{python_path}" "{script_notificador()}" "{pasta_os}"'
    r = subprocess.run(
        ["schtasks", "/Create", "/SC", "WEEKLY", "/D", "MON",
         "/ST", f"{hora:02d}:{minuto:02d}",
         "/TN", NOME_TAREFA, "/TR", comando, "/F"],
        capture_output=True, text=True)
    if r.returncode != 0:
        return resultado(False, "Windows",
                         f"schtasks falhou: {r.stderr.strip() or r.stdout.strip()}",
                         "instalar")
    return resultado(True, "Windows",
                     f'Tarefa "{NOME_TAREFA}" criada — toda segunda às '
                     f"{hora:02d}:{minuto:02d}.", "instalar")


def remover_windows() -> int:
    r = subprocess.run(["schtasks", "/Delete", "/TN", NOME_TAREFA, "/F"],
                       capture_output=True, text=True)
    if r.returncode != 0 and "ERROR" in (r.stderr or "").upper():
        return resultado(True, "Windows", "Tarefa já não existia.", "remover")
    return resultado(True, "Windows", "Tarefa removida.", "remover")


def status_windows() -> int:
    r = subprocess.run(["schtasks", "/Query", "/TN", NOME_TAREFA], capture_output=True, text=True)
    if r.returncode != 0:
        return resultado(True, "Windows", "Aviso semanal não instalado.", "status")
    return resultado(True, "Windows", f'Tarefa "{NOME_TAREFA}" instalada.', "status")


# ── Main ──────────────────────────────────────────────────────────────────

def main() -> int:
    if len(sys.argv) < 2:
        print("Uso: instalar_rotina_pendencias.py <instalar|remover|status> ...", file=sys.stderr)
        return 2
    acao = sys.argv[1]
    sistema = "macOS" if sys.platform == "darwin" else ("Windows" if sys.platform.startswith("win") else "outro")

    if sistema == "outro":
        return resultado(False, sys.platform,
                         "Sistema não suportado pelo aviso automático (só macOS e Windows).", acao)

    if acao == "instalar":
        if len(sys.argv) < 4:
            print("Uso: instalar_rotina_pendencias.py instalar <python_path> <pasta_os_ativas> [--hora HH:MM]",
                  file=sys.stderr)
            return 2
        python_path, pasta_os = sys.argv[2], sys.argv[3]
        hora, minuto = 8, 0
        if "--hora" in sys.argv:
            i = sys.argv.index("--hora")
            if i + 1 < len(sys.argv):
                try:
                    hora, minuto = (int(x) for x in sys.argv[i + 1].split(":"))
                except ValueError:
                    pass
        if not script_notificador().exists():
            return resultado(False, sistema,
                             f"notificar_pendencias.py não encontrado em {script_notificador()}", acao)
        if sistema == "macOS":
            return instalar_macos(python_path, pasta_os, hora, minuto)
        return instalar_windows(python_path, pasta_os, hora, minuto)

    if acao == "remover":
        return remover_macos() if sistema == "macOS" else remover_windows()

    if acao == "status":
        return status_macos() if sistema == "macOS" else status_windows()

    print(f"Ação desconhecida: {acao}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
