#!/usr/bin/env python3
"""
nlm_ask.py — consulta ao NotebookLM com auto-reautenticacao (AFT Toolkit).

A sessao do NotebookLM expira de tempos em tempos e, no meio de uma skill, a
consulta de ementa falha com "Authentication expired" / "Run 'notebooklm login'".
Este wrapper resolve isso sozinho: roda o `notebooklm ask`; se detectar sessao
expirada, dispara o refresh silencioso (login pelo perfil persistente do navegador
do AFT, que reaproveita a sessao ja aberta) e tenta a consulta UMA vez de novo.

As skills devem chamar este wrapper em vez de `notebooklm ask` diretamente, para
nunca abortar a tarefa por causa de token vencido.

Uso (igual ao `notebooklm ask`, repassa os argumentos):
    python nlm_ask.py -n <notebook_id> --prompt-file <arquivo.txt>
    python nlm_ask.py -n <notebook_id> "pergunta curta"

Exit 0 = resposta impressa no stdout. Exit != 0 = falhou mesmo apos reautenticar
(ex.: sem rede, ou login exige acao do AFT — nesse caso oriente /notebooklm-login).
"""
import os
import re
import shutil
import subprocess
import sys

AUTH_FAIL = re.compile(r"authentication expired|run 'notebooklm login'|not.*authenticat|"
                       r"redirected to:\s*https://accounts\.google", re.IGNORECASE)


def find_notebooklm():
    exe = shutil.which("notebooklm")
    if exe:
        return exe
    cand = os.path.expanduser(r"~\.local\bin\notebooklm.exe")
    if os.path.isfile(cand):
        return cand
    cand2 = os.path.expanduser("~/.local/bin/notebooklm")
    if os.path.isfile(cand2):
        return cand2
    return "notebooklm"  # ultima tentativa: confia no PATH


def read_browser():
    """Le notebooklm_browser do aft-config.md (default chrome)."""
    cfg = os.path.expanduser("~/Documents/AFT/aft-config.md")
    try:
        for line in open(cfg, encoding="utf-8"):
            m = re.search(r"notebooklm_browser:\s*\"?([a-zA-Z]+)", line)
            if m:
                return m.group(1).lower()
    except OSError:
        pass
    return "chrome"


def run_ask(exe, args):
    proc = subprocess.run([exe, "--quiet", "ask"] + args,
                          capture_output=True, text=True, encoding="utf-8", errors="replace")
    return proc.returncode, (proc.stdout or ""), (proc.stderr or "")


def refresh_login(exe, browser):
    """Reautentica em silencio pelo perfil persistente do navegador do AFT."""
    nav = {"edge": "msedge"}.get(browser, browser)  # edge usa 'msedge' no login por janela
    print(f"[nlm_ask] sessao do NotebookLM expirada; reconectando via {nav}...",
          file=sys.stderr)
    proc = subprocess.run([exe, "login", "--browser", nav],
                          capture_output=True, text=True, encoding="utf-8",
                          errors="replace", timeout=320)
    return proc.returncode == 0 or "Authentication saved" in (proc.stdout or "")


def main():
    args = sys.argv[1:]
    if not args:
        print("uso: python nlm_ask.py -n <id> (--prompt-file <f> | \"pergunta\")",
              file=sys.stderr)
        sys.exit(2)

    exe = find_notebooklm()
    code, out, err = run_ask(exe, args)
    combined = out + "\n" + err

    if code != 0 and AUTH_FAIL.search(combined):
        if refresh_login(exe, read_browser()):
            code, out, err = run_ask(exe, args)  # 1 retry
        else:
            print("[nlm_ask] nao foi possivel reautenticar automaticamente. "
                  "Rode /notebooklm-login.", file=sys.stderr)

    if out:
        print(out, end="" if out.endswith("\n") else "\n")
    if code != 0 and err:
        print(err, file=sys.stderr)
    sys.exit(code)


if __name__ == "__main__":
    main()
