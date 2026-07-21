#!/usr/bin/env python3
"""
instalar_vigia_sessoes.py — instala/remove/consulta o VIGIA AUTOMÁTICO de
sessões (sessoes_os.py --vigia) como serviço em segundo plano do sistema:
sobe sozinho no login e se reinicia se cair. É ele que torna as sessões por
empresa 100% automáticas: sempre que o app do Claude fechar, o vigia aplica
as pendências (sessões novas de OS ATIVAS, grupo "OS ATIVAS", vínculos no
memory.md) — e as sessões aparecem na próxima abertura do app.

  macOS:   LaunchAgent com RunAtLoad + KeepAlive (reinicia sozinho se cair).
  Windows: Tarefa Agendada com gatilho "ao fazer logon" + reinício automático
           (via PowerShell Register-ScheduledTask). Usa pythonw.exe (sem
           janela de console) quando disponível ao lado do python.exe.

Uso:
    python instalar_vigia_sessoes.py instalar <python_path>
    python instalar_vigia_sessoes.py remover
    python instalar_vigia_sessoes.py status

Imprime um JSON no stdout: {"ok": bool, "sistema": "...", "detalhe": "...",
"acao": "..."}. Nunca lança exceção não tratada.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

NOME_TAREFA = "AFT Sessoes - Vigia"
LABEL_LAUNCHD = "br.aft.sessoes-vigia"


def script_vigia() -> Path:
    return Path(__file__).resolve().parent / "sessoes_os.py"


def resultado(ok: bool, sistema: str, detalhe: str, acao: str) -> int:
    print(json.dumps({"ok": ok, "sistema": sistema, "detalhe": detalhe, "acao": acao},
                     ensure_ascii=False, indent=2))
    return 0 if ok else 1


# ── macOS (launchd) ──────────────────────────────────────────────────────────

def plist_path() -> Path:
    return Path.home() / "Library" / "LaunchAgents" / f"{LABEL_LAUNCHD}.plist"


def instalar_macos(python_path: str) -> int:
    plist = plist_path()
    plist.parent.mkdir(parents=True, exist_ok=True)
    log = str(Path.home() / "Library" / "Logs" / "aft-sessoes-vigia.log")
    conteudo = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>{LABEL_LAUNCHD}</string>
  <key>ProgramArguments</key>
  <array>
    <string>{python_path}</string>
    <string>{script_vigia()}</string>
    <string>--vigia</string>
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
                     f"Vigia de sessões instalado como serviço em {plist} — sobe sozinho no "
                     f"login e se reinicia se cair. Log em {log}.",
                     "instalar")


def remover_macos() -> int:
    plist = plist_path()
    subprocess.run(["launchctl", "unload", str(plist)], capture_output=True)
    if plist.exists():
        plist.unlink()
    subprocess.run(["pkill", "-f", "sessoes_os.py --vigia"], capture_output=True)
    return resultado(True, "macOS", "Vigia de sessões removido.", "remover")


def status_macos() -> int:
    plist = plist_path()
    if not plist.exists():
        return resultado(True, "macOS", "Vigia não instalado como serviço.", "status")
    r = subprocess.run(["launchctl", "list"], capture_output=True, text=True)
    ativo = LABEL_LAUNCHD in r.stdout
    return resultado(True, "macOS",
                     f"Vigia instalado — {'ativo' if ativo else 'inativo (rode launchctl load)'}.",
                     "status")


# ── Windows (Agendador de Tarefas via PowerShell) ───────────────────────────

def pythonw_de(python_path: str) -> str:
    p = Path(python_path)
    candidato = p.with_name("pythonw.exe")
    return str(candidato) if candidato.exists() else python_path


def _ps_aspas(s: str) -> str:
    return "'" + s.replace("'", "''") + "'"


def instalar_windows(python_path: str) -> int:
    exe = pythonw_de(python_path)
    # Escopado ao usuário atual (LogonType Interactive, RunLevel Limited) —
    # mesma lição do instalar_servidor_painel.py: sem isso, conta padrão
    # falha com "Acesso negado" (0x80070005).
    script_ps = f"""
$ErrorActionPreference = 'Stop'
$user = "$env:USERDOMAIN\\$env:USERNAME"
$action = New-ScheduledTaskAction -Execute {_ps_aspas(exe)} `
  -Argument ('"{script_vigia()}" --vigia')
$trigger = New-ScheduledTaskTrigger -AtLogOn -User $user
$principal = New-ScheduledTaskPrincipal -UserId $user -LogonType Interactive -RunLevel Limited
$settings = New-ScheduledTaskSettingsSet -RestartCount 3 `
  -RestartInterval (New-TimeSpan -Minutes 1) `
  -ExecutionTimeLimit ([TimeSpan]::Zero) `
  -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
Register-ScheduledTask -TaskName {_ps_aspas(NOME_TAREFA)} -Action $action `
  -Trigger $trigger -Principal $principal -Settings $settings -Force | Out-Null
Start-ScheduledTask -TaskName {_ps_aspas(NOME_TAREFA)}
"""
    r = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", script_ps],
                       capture_output=True, text=True)
    if r.returncode != 0:
        return resultado(False, "Windows",
                         f"Register-ScheduledTask falhou: {r.stderr.strip() or r.stdout.strip()}",
                         "instalar")
    return resultado(True, "Windows",
                     f'Tarefa "{NOME_TAREFA}" criada e iniciada — o vigia sobe sozinho no '
                     f"login e se reinicia se cair.", "instalar")


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
        return resultado(True, "Windows", "Vigia não instalado como tarefa.", "status")
    return resultado(True, "Windows", f'Tarefa "{NOME_TAREFA}" instalada.', "status")


# ── Main ──────────────────────────────────────────────────────────────────

def main() -> int:
    if len(sys.argv) < 2:
        print("Uso: instalar_vigia_sessoes.py <instalar|remover|status> ...", file=sys.stderr)
        return 2
    acao = sys.argv[1]
    sistema = "macOS" if sys.platform == "darwin" else ("Windows" if sys.platform.startswith("win") else "outro")

    if sistema == "outro":
        return resultado(False, sys.platform,
                         "Sistema não suportado pelo serviço automático (só macOS e Windows). "
                         "Rode 'python sessoes_os.py --aplicar' manualmente quando precisar.", acao)

    if acao == "instalar":
        if len(sys.argv) < 3:
            print("Uso: instalar_vigia_sessoes.py instalar <python_path>", file=sys.stderr)
            return 2
        python_path = sys.argv[2]
        if not script_vigia().exists():
            return resultado(False, sistema, f"sessoes_os.py não encontrado em {script_vigia()}", acao)
        if sistema == "macOS":
            return instalar_macos(python_path)
        return instalar_windows(python_path)

    if acao == "remover":
        return remover_macos() if sistema == "macOS" else remover_windows()

    if acao == "status":
        return status_macos() if sistema == "macOS" else status_windows()

    print(f"Ação desconhecida: {acao}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
