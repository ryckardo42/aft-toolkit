#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
notificar_pendencias.py — aviso semanal de pendências das auditorias.

Varre os memory.md de OS ATIVAS/*/, conta as pendências em aberto (linhas
"- [ ]" da seção ## Pendências, ignorando OS encerradas) e mostra uma
NOTIFICAÇÃO NATIVA do sistema (macOS ou Windows) com os totais:

    "11 pendências em 4 auditorias — abra o painel para a lista completa."

De propósito, a notificação traz SÓ NÚMEROS — nada de nome de empresa nem
texto de pendência (a notificação aparece até em tela bloqueada). A lista
completa fica na seção "Pendências por auditoria" do painel.

No Windows, clicar na notificação abre o painel (http://127.0.0.1:8347).
No macOS a notificação é informativa (limitação do sistema sem app dedicado).

Sem nenhuma pendência em aberto, não mostra nada (segunda-feira em paz).

Uso:
    python notificar_pendencias.py <pasta_os_ativas>
    python notificar_pendencias.py <pasta_os_ativas> --teste   (mostra mesmo com 0)

Agendado para toda segunda-feira pelo instalar_rotina_pendencias.py.
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

import re
import subprocess
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

PAINEL_URL = "http://127.0.0.1:8347/"
RE_CHECKBOX = re.compile(r"^[-*]\s+\[([ xX])\]\s+(.*)$")
RE_STATUS = re.compile(r"^status:\s*\"?([^\"\n]*)\"?\s*$", re.MULTILINE)


def extrair_secao(corpo: str, titulo: str) -> str:
    m = re.search(rf"^##\s+{re.escape(titulo)}\s*$(.*?)(?=^##\s|\Z)",
                  corpo, re.MULTILINE | re.DOTALL)
    return m.group(1) if m else ""


def contar_pendencias(base: Path) -> tuple[int, int]:
    """(pendências em aberto, auditorias com pendência) — OS encerradas fora,
    como no painel."""
    total = 0
    auditorias = 0
    for mem in sorted(base.glob("*/memory.md")):
        try:
            texto = mem.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        m_st = RE_STATUS.search(texto)
        if m_st and m_st.group(1).strip().lower() == "encerrada":
            continue
        abertas = 0
        for linha in extrair_secao(texto, "Pendências").splitlines():
            cb = RE_CHECKBOX.match(linha.strip())
            if cb and cb.group(1).strip().lower() != "x":
                abertas += 1
        if abertas:
            total += abertas
            auditorias += 1
    return total, auditorias


def notificar_macos(titulo: str, corpo: str) -> bool:
    r = subprocess.run(
        ["osascript", "-e",
         f'display notification "{corpo}" with title "{titulo}"'],
        capture_output=True, text=True)
    return r.returncode == 0


def notificar_windows(titulo: str, corpo: str) -> bool:
    # Toast nativo via WinRT; activationType=protocol faz o clique abrir o
    # painel. AppId do PowerShell: registrado em qualquer Windows 10/11.
    app_id = ("{1AC14E77-02E7-4E5D-B744-2EB1AE5198B7}\\WindowsPowerShell"
              "\\v1.0\\powershell.exe")
    script_ps = f"""
[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
[Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] | Out-Null
$xml = @'
<toast activationType="protocol" launch="{PAINEL_URL}">
  <visual><binding template="ToastGeneric">
    <text>{titulo}</text>
    <text>{corpo}</text>
  </binding></visual>
</toast>
'@
$doc = New-Object Windows.Data.Xml.Dom.XmlDocument
$doc.LoadXml($xml)
$toast = New-Object Windows.UI.Notifications.ToastNotification($doc)
[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier('{app_id}').Show($toast)
"""
    r = subprocess.run(["powershell", "-NoProfile", "-NonInteractive",
                        "-Command", script_ps], capture_output=True, text=True)
    return r.returncode == 0


def main() -> int:
    if len(sys.argv) < 2:
        print("Uso: notificar_pendencias.py <pasta_os_ativas> [--teste]",
              file=sys.stderr)
        return 2
    base = Path(sys.argv[1]).expanduser()
    teste = "--teste" in sys.argv
    if not base.is_dir():
        print(f"pasta não encontrada: {base}", file=sys.stderr)
        return 1

    total, auditorias = contar_pendencias(base)
    if total == 0 and not teste:
        print("0 pendências em aberto — sem notificação.")
        return 0

    titulo = "AFT Toolkit — pendências da semana"
    if total == 0:
        corpo = "Nenhuma pendência em aberto. Boa semana!"
    elif total == 1:
        corpo = "1 pendência em 1 auditoria — abra o painel para ver."
    else:
        s_aud = "auditoria" if auditorias == 1 else "auditorias"
        corpo = (f"{total} pendências em {auditorias} {s_aud} — "
                 "abra o painel para a lista completa.")

    ok = (notificar_macos(titulo, corpo) if sys.platform == "darwin"
          else notificar_windows(titulo, corpo))
    print(f"{total} pendência(s) em {auditorias} auditoria(s) — "
          f"notificação {'exibida' if ok else 'FALHOU'}.")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
