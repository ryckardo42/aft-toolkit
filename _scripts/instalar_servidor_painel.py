#!/usr/bin/env python3
"""
instalar_servidor_painel.py — instala/remove/consulta o SERVIDOR interativo
do painel (servir_painel.py, http://127.0.0.1:8347) como serviço em segundo
plano do próprio sistema operacional: sobe sozinho no login e se reinicia se
cair. É diferente da rotina diária (instalar_rotina_painel.py), que só
regenera o painel.html estático 1x por dia — este script mantém o servidor
ATIVO o tempo todo, necessário para os controles do painel e para o sync do
DET pela extensão Chrome ("SisOS — Sync DET").

  macOS:   LaunchAgent com RunAtLoad + KeepAlive (reinicia sozinho se cair).
  Windows: Tarefa Agendada com gatilho "ao fazer logon" + reinício automático
           (via PowerShell Register-ScheduledTask — schtasks.exe básico não
           expõe reinício automático). Usa pythonw.exe (sem janela de console)
           quando disponível ao lado do python.exe informado.

Uso:
    python instalar_servidor_painel.py instalar <python_path> <pasta_os_ativas> [--porta N]
    python instalar_servidor_painel.py remover
    python instalar_servidor_painel.py status

Imprime um JSON no stdout: {"ok": bool, "sistema": "...", "detalhe": "...",
"acao": "..."}. Nunca lança exceção não tratada.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

NOME_TAREFA = "Painel AFT - Servidor"
LABEL_LAUNCHD = "br.aft.painel-servidor"
PORTA_PADRAO = 8347


def script_servidor() -> Path:
    return Path(__file__).resolve().parent / "servir_painel.py"


def resultado(ok: bool, sistema: str, detalhe: str, acao: str) -> int:
    print(json.dumps({"ok": ok, "sistema": sistema, "detalhe": detalhe, "acao": acao},
                     ensure_ascii=False, indent=2))
    return 0 if ok else 1


# ── macOS (launchd) ──────────────────────────────────────────────────────────

def plist_path() -> Path:
    return Path.home() / "Library" / "LaunchAgents" / f"{LABEL_LAUNCHD}.plist"


def instalar_macos(python_path: str, pasta_os: str, porta: int) -> int:
    plist = plist_path()
    plist.parent.mkdir(parents=True, exist_ok=True)
    log = str(Path.home() / "Library" / "Logs" / "aft-painel-servidor.log")
    conteudo = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>{LABEL_LAUNCHD}</string>
  <key>ProgramArguments</key>
  <array>
    <string>{python_path}</string>
    <string>{script_servidor()}</string>
    <string>{pasta_os}</string>
    <string>--porta</string>
    <string>{porta}</string>
  </array>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
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
                     f"Servidor instalado como serviço em {plist} — sobe sozinho no login "
                     f"e se reinicia se cair. Endereço: http://127.0.0.1:{porta}. Log em {log}.",
                     "instalar")


def remover_macos() -> int:
    plist = plist_path()
    subprocess.run(["launchctl", "unload", str(plist)], capture_output=True)
    if plist.exists():
        plist.unlink()
    return resultado(True, "macOS", "Serviço do servidor removido.", "remover")


def status_macos() -> int:
    plist = plist_path()
    if not plist.exists():
        return resultado(True, "macOS", "Servidor não instalado como serviço.", "status")
    r = subprocess.run(["launchctl", "list"], capture_output=True, text=True)
    ativo = LABEL_LAUNCHD in r.stdout
    return resultado(True, "macOS",
                     f"Serviço instalado — {'ativo' if ativo else 'inativo (rode launchctl load)'}.",
                     "status")


# ── Windows (Agendador de Tarefas via PowerShell) ───────────────────────────

def pythonw_de(python_path: str) -> str:
    """Troca python.exe por pythonw.exe (mesma pasta) se existir — evita a
    janela de console preta. Sem pythonw.exe, usa o interpretador informado."""
    p = Path(python_path)
    candidato = p.with_name("pythonw.exe")
    return str(candidato) if candidato.exists() else python_path


def _ps_aspas(s: str) -> str:
    """Escapa para dentro de aspas simples do PowerShell (dobra aspas simples)."""
    return "'" + s.replace("'", "''") + "'"


def instalar_windows(python_path: str, pasta_os: str, porta: int) -> int:
    exe = pythonw_de(python_path)
    script_ps = f"""
$ErrorActionPreference = 'Stop'
$action = New-ScheduledTaskAction -Execute {_ps_aspas(exe)} `
  -Argument ('"{script_servidor()}" "{pasta_os}" --porta {porta}')
$trigger = New-ScheduledTaskTrigger -AtLogOn
$settings = New-ScheduledTaskSettingsSet -RestartCount 3 `
  -RestartInterval (New-TimeSpan -Minutes 1) `
  -ExecutionTimeLimit (New-TimeSpan -Zero) `
  -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
Register-ScheduledTask -TaskName {_ps_aspas(NOME_TAREFA)} -Action $action `
  -Trigger $trigger -Settings $settings -Force | Out-Null
Start-ScheduledTask -TaskName {_ps_aspas(NOME_TAREFA)}
"""
    r = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", script_ps],
                       capture_output=True, text=True)
    if r.returncode != 0:
        return resultado(False, "Windows",
                         f"Register-ScheduledTask falhou: {r.stderr.strip() or r.stdout.strip()}",
                         "instalar")
    return resultado(True, "Windows",
                     f'Tarefa "{NOME_TAREFA}" criada e iniciada — sobe sozinha no login e se '
                     f"reinicia se cair. Endereço: http://127.0.0.1:{porta}.", "instalar")


def remover_windows() -> int:
    subprocess.run(
        ["powershell", "-NoProfile", "-NonInteractive", "-Command",
         f"Stop-ScheduledTask -TaskName {_ps_aspas(NOME_TAREFA)} -ErrorAction SilentlyContinue; "
         f"Unregister-ScheduledTask -TaskName {_ps_aspas(NOME_TAREFA)} -Confirm:$false "
         f"-ErrorAction SilentlyContinue"],
        capture_output=True, text=True)
    return resultado(True, "Windows", "Tarefa removida (se existia).", "remover")


def status_windows() -> int:
    r = subprocess.run(["schtasks", "/Query", "/TN", NOME_TAREFA], capture_output=True, text=True)
    if r.returncode != 0:
        return resultado(True, "Windows", "Servidor não instalado como tarefa.", "status")
    return resultado(True, "Windows", f'Tarefa "{NOME_TAREFA}" instalada.', "status")


# ── Main ──────────────────────────────────────────────────────────────────

def main() -> int:
    if len(sys.argv) < 2:
        print("Uso: instalar_servidor_painel.py <instalar|remover|status> ...", file=sys.stderr)
        return 2
    acao = sys.argv[1]
    sistema = "macOS" if sys.platform == "darwin" else ("Windows" if sys.platform.startswith("win") else "outro")

    if sistema == "outro":
        return resultado(False, sys.platform,
                         "Sistema não suportado pelo serviço automático (só macOS e Windows). "
                         "Rode 'python servir_painel.py --abrir' manualmente quando precisar.", acao)

    if acao == "instalar":
        if len(sys.argv) < 4:
            print("Uso: instalar_servidor_painel.py instalar <python_path> <pasta_os_ativas> [--porta N]",
                  file=sys.stderr)
            return 2
        python_path, pasta_os = sys.argv[2], sys.argv[3]
        porta = PORTA_PADRAO
        if "--porta" in sys.argv:
            i = sys.argv.index("--porta")
            if i + 1 < len(sys.argv):
                try:
                    porta = int(sys.argv[i + 1])
                except ValueError:
                    pass
        if not script_servidor().exists():
            return resultado(False, sistema, f"servir_painel.py não encontrado em {script_servidor()}", acao)
        if sistema == "macOS":
            return instalar_macos(python_path, pasta_os, porta)
        return instalar_windows(python_path, pasta_os, porta)

    if acao == "remover":
        return remover_macos() if sistema == "macOS" else remover_windows()

    if acao == "status":
        return status_macos() if sistema == "macOS" else status_windows()

    print(f"Ação desconhecida: {acao}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
