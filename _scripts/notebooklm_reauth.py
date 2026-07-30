#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Reconexão silenciosa do NotebookLM (re-auth headless, sem janela, sem AFT).

Quando os cookies do ``storage_state.json`` expiram mas o perfil persistente do
navegador (``~/.notebooklm/profiles/default/browser_profile``) ainda guarda a
sessão Google viva, este script re-emite os cookies dirigindo um navegador
**headless** — nenhuma janela aparece e o AFT não faz nada. É a "camada L3"
(``attempt_headless_reauth``) do próprio notebooklm-py, que existe a partir da
série 0.8.x; em versões 0.7.x o script falha com a orientação de atualizar.

Dois usos:

1. Valor da variável ``NOTEBOOKLM_REFRESH_CMD`` (o gancho nativo da CLI): o
   ``notebooklm`` chama este script sozinho ao detectar sessão expirada. O
   gancho mata o comando em 60 s, por isso com um navegador na linha de
   comando o script faz UMA tentativa (~15-25 s).
2. Chamada direta pela skill /aft-notebooklm-login, antes de abrir janela de
   login: ``python notebooklm_reauth.py`` (sem argumento tenta chrome e depois
   msedge).

Uso:  python notebooklm_reauth.py [chrome|msedge|chromium]
Exit 0 = cookies renovados; exit 1 = não deu (é preciso login por janela);
exit 3 = notebooklm-py antigo demais (sem re-auth headless).

O notebooklm-py mora no venv do pipx, não no Python do sistema — o script
localiza esse venv sozinho e roda a renovação lá dentro.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

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

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Roda DENTRO do venv do notebooklm-py. Sem caminho de usuário interpolado:
# só Path.home(), imune a mojibake de acento no console.
_RUNNER = r"""
import sys
from pathlib import Path
try:
    from notebooklm._auth.headless_reauth import (
        HeadlessReauthStatus, attempt_headless_reauth,
    )
except ImportError:
    print("sem-reauth-headless")
    sys.exit(3)
browser = sys.argv[1]
storage = Path.home() / ".notebooklm" / "profiles" / "default" / "storage_state.json"
res = attempt_headless_reauth(
    storage_path=storage, allow_headless=True, profile="default", browser=browser,
)
print(f"{res.status.value}: {res.reason}")
sys.exit(0 if res.status is HeadlessReauthStatus.SUCCESS else 1)
"""


def _python_do_notebooklm() -> Path | None:
    """Acha o python.exe do venv onde o notebooklm-py está instalado (pipx)."""
    exe = "Scripts/python.exe" if os.name == "nt" else "bin/python"
    raizes: list[Path] = []
    if os.environ.get("PIPX_HOME"):
        raizes.append(Path(os.environ["PIPX_HOME"]) / "venvs")
    raizes += [
        Path.home() / "pipx" / "venvs",            # pipx novo no Windows
        Path.home() / ".local" / "pipx" / "venvs",  # pipx clássico
    ]
    for raiz in raizes:
        cand = raiz / "notebooklm-py" / exe
        if cand.is_file():
            return cand
    # Fallback: instalado via pip --user no próprio interpretador atual?
    try:
        import notebooklm  # noqa: F401
        return Path(sys.executable)
    except ImportError:
        return None


def main() -> int:
    navegadores = [sys.argv[1]] if len(sys.argv) > 1 else ["chrome", "msedge"]

    py = _python_do_notebooklm()
    if py is None:
        print("notebooklm-py não encontrado (nem no pipx, nem neste Python). "
              "Rode a skill /aft-notebooklm-login para instalar.")
        return 1

    for nav in navegadores:
        try:
            r = subprocess.run(
                [str(py), "-c", _RUNNER, nav],
                capture_output=True, text=True, timeout=50,
                encoding="utf-8", errors="replace",
            )
        except subprocess.TimeoutExpired:
            print(f"{nav}: tempo esgotado (50 s)")
            continue
        saida = (r.stdout or "").strip()
        if not saida:
            linhas = (r.stderr or "").strip().splitlines()
            saida = linhas[-1] if linhas else "(sem saída)"
        if r.returncode == 0:
            print(f"{nav}: {saida}")
            print("Cookies do NotebookLM renovados sem janela.")
            return 0
        if r.returncode == 3:
            print("Esta versão do notebooklm-py não tem re-auth headless "
                  "(série 0.7.x, anterior ao rebrand do Gemini Notebook). "
                  "Atualize com /aft-atualizar e tente de novo.")
            return 3
        print(f"{nav}: {saida}")

    print("Não deu para renovar sem janela (a sessão Google do perfil também "
          "expirou, ou o navegador não abriu). Caminho: login por janela "
          "(/aft-notebooklm-login, Passo 3).")
    return 1


if __name__ == "__main__":
    sys.exit(main())
