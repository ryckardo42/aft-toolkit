#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Sincroniza as planilhas de CAT da UF do auditor a partir do espelho no
Google Drive do projeto notebooks-aft (pasta "CATs eSocial por UF").

O espelho e restrito: so os Gmails autorizados do notebooks-aft (os mesmos dos
NotebookLMs) enxergam a pasta. O download usa o rclone, que tem cliente OAuth
verificado pelo Google: o AFT autoriza uma unica vez no navegador ("Permitir")
e dali em diante tudo roda sozinho, inclusive no /aft-atualizar. A fonte
oficial continua sendo a area do ENIT no SharePoint do MTE (caminho manual do
/aft-setup, Passo 2a) - este script e o atalho, nao o substituto.

Uso:
    sincronizar_cats.py --status     # diagnostico: rclone, remote, acesso, UF
    sincronizar_cats.py --conectar   # cria o remote OAuth (abre o navegador)
    sincronizar_cats.py --sync       # baixa/atualiza as planilhas da UF
    sincronizar_cats.py --sync --uf GO   # forca outra UF (raro)

Saida: JSON em uma linha, campo "estado" primeiro. Estados possiveis:
    ok · ja_conectado · rclone_ausente · remote_nao_configurado ·
    sem_acesso · uf_ausente · uf_nao_encontrada · sem_config · erro
Exit code: 0 = ok/ja_conectado · 2 = falta configuracao (nao e defeito) ·
    3 = sem acesso ao espelho · 1 = erro real.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

if os.name == "nt":  # console cp1252 do Windows
    for _s in (sys.stdout, sys.stderr):
        try:
            _s.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

# Pasta "CATs eSocial por UF" no Google Drive do projeto notebooks-aft
# (espelho da base do ENIT; uma subpasta por UF, planilhas .xlsx anuais).
# O ID sozinho nao da acesso: a pasta e restrita aos Gmails autorizados.
DRIVE_FOLDER_ID = "1-38yX-gFrW6YfJP9Wjo5W8ZFgaRTdnuH"
REMOTE = "aftcats"  # nome do remote do rclone criado pelo --conectar

# Pagina de autosservico: AFT com cadastro aprovado nos Notebooks ativa sozinho
# a leitura do espelho (digita o Gmail e clica em "Ativar acesso").
LINK_ATIVACAO = "https://notebooks-aft.vercel.app/aft-toolkit#cats"

DICA_SEM_ACESSO = (
    "Seu Gmail ainda nao tem leitura do espelho de CATs. Ative voce mesmo: abra "
    + LINK_ATIVACAO + " , digite o Gmail do seu cadastro dos Notebooks e clique "
    "em 'Ativar acesso'. A liberacao vale na hora - depois e so sincronizar de novo.")

UFS_VALIDAS = {
    "AC", "AL", "AM", "AP", "BA", "CE", "DF", "ES", "GO", "MA", "MG", "MS",
    "MT", "PA", "PB", "PE", "PI", "PR", "RJ", "RN", "RO", "RR", "RS", "SC",
    "SE", "SP", "TO",
}


def _sair(obj, code=0):
    print(json.dumps(obj, ensure_ascii=False))
    sys.exit(code)


# ---------------------------------------------------------------------------
# rclone
# ---------------------------------------------------------------------------
def _rclone():
    """Caminho do rclone, ou None. Alem do PATH, tenta os lugares onde o
    brew/winget instalam (PATH de sessao recem-instalada pode estar velho)."""
    achado = shutil.which("rclone")
    if achado:
        return achado
    candidatos = [
        "/opt/homebrew/bin/rclone",
        "/usr/local/bin/rclone",
        str(Path.home() / ".local" / "bin" / "rclone"),
        str(Path.home() / "bin" / "rclone"),
        os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WinGet\Links\rclone.exe"),
        os.path.expandvars(r"%ProgramFiles%\rclone\rclone.exe"),
    ]
    for c in candidatos:
        if c and "%" not in c and Path(c).is_file():
            return c
    return None


def _roda_rclone(rclone, args, timeout=120, herdar_saida=False):
    cmd = [rclone] + args
    if herdar_saida:
        return subprocess.run(cmd, timeout=timeout)
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)


def _remote_existe(rclone):
    r = _roda_rclone(rclone, ["listremotes"])
    return r.returncode == 0 and (REMOTE + ":") in (r.stdout or "")


# ---------------------------------------------------------------------------
# aft-config.md (pasta_aft.py mora nesta mesma pasta _scripts)
# ---------------------------------------------------------------------------
sys.path.insert(0, str(Path(__file__).resolve().parent))


def _pasta_aft():
    try:
        import pasta_aft as pa
        return Path(pa.pasta_aft())
    except Exception:
        return None


def _campo_config(nome):
    aft = _pasta_aft()
    if not aft:
        return None
    cfg = aft / "aft-config.md"
    if not cfg.is_file():
        return None
    for linha in cfg.read_text(encoding="utf-8").splitlines():
        m = re.match(r'\s*' + re.escape(nome) + r'\s*:\s*"?([^"#]+?)"?\s*$', linha)
        if m and m.group(1).strip():
            return m.group(1).strip()
    return None


def _uf(args):
    uf = (args.uf or _campo_config("uf") or "").strip().upper()
    return uf if uf in UFS_VALIDAS else None


def _pasta_cats():
    """Destino das planilhas. Mesma regra da /aft-relatorio-acidentes
    (base_configurada la e a fonte da verdade): `pasta_cats:` do config quando
    aponta para pasta existente; senao <PASTA_AFT>/CATs (aceita 'CAT'); se
    nenhuma existir, cria <PASTA_AFT>/CATs."""
    cfg = _campo_config("pasta_cats")
    if cfg:
        p = Path(cfg).expanduser()
        if p.is_dir():
            return p
    aft = _pasta_aft()
    if not aft:
        return None
    for nome in ("CATs", "CAT"):
        if (aft / nome).is_dir():
            return aft / nome
    alvo = aft / "CATs"
    alvo.mkdir(parents=True, exist_ok=True)
    return alvo


# ---------------------------------------------------------------------------
# acesso ao espelho
# ---------------------------------------------------------------------------
def _lista_ufs_remotas(rclone):
    """(ok, ufs|mensagem). ok=False com 'sem_acesso' quando o Gmail conectado
    nao enxerga a pasta (nao autorizado ainda, ou conta errada)."""
    r = _roda_rclone(rclone, ["lsf", REMOTE + ":", "--dirs-only", "--max-depth", "1"])
    if r.returncode == 0:
        return True, sorted(d.strip("/") for d in r.stdout.splitlines() if d.strip())
    err = (r.stderr or "").strip()
    if "directory not found" in err.lower() or "404" in err or "notFound" in err:
        return False, "sem_acesso"
    return False, err[-400:]


def _snapshot(pasta):
    out = {}
    for p in pasta.glob("*.xlsx"):
        st = p.stat()
        out[p.name] = (st.st_size, int(st.st_mtime))
    return out


# ---------------------------------------------------------------------------
# comandos
# ---------------------------------------------------------------------------
def cmd_status(args):
    rclone = _rclone()
    est = {
        "estado": "ok",
        "rclone": rclone,
        "remote_configurado": False,
        "uf": _uf(args),
        "pasta_cats": None,
        "acesso": None,
        "instalar_rclone": ("brew install rclone" if sys.platform == "darwin"
                            else "winget install Rclone.Rclone"),
    }
    aft = _pasta_aft()
    if not aft:
        est["estado"] = "sem_config"
        _sair(est, 2)
    est["pasta_cats"] = str(_pasta_cats() or "")
    if not rclone:
        est["estado"] = "rclone_ausente"
        _sair(est, 2)
    if not _remote_existe(rclone):
        est["estado"] = "remote_nao_configurado"
        _sair(est, 2)
    est["remote_configurado"] = True
    ok, res = _lista_ufs_remotas(rclone)
    if ok:
        est["acesso"] = "ok"
        est["ufs_disponiveis"] = res
    elif res == "sem_acesso":
        est["estado"] = est["acesso"] = "sem_acesso"
        _sair(est, 3)
    else:
        est["estado"], est["erro"] = "erro", res
        _sair(est, 1)
    if not est["uf"]:
        est["estado"] = "uf_ausente"
        _sair(est, 2)
    _sair(est, 0)


def cmd_conectar(args):
    rclone = _rclone()
    if not rclone:
        _sair({"estado": "rclone_ausente",
               "instalar": ("brew install rclone" if sys.platform == "darwin"
                            else "winget install Rclone.Rclone")}, 2)
    if _remote_existe(rclone):
        _sair({"estado": "ja_conectado", "remote": REMOTE}, 0)
    # Abre o navegador para o OAuth (cliente verificado do rclone). O AFT
    # escolhe a conta Gmail autorizada do notebooks-aft e clica em Permitir.
    # scope=drive.readonly: leitura apenas; root_folder_id prende o remote a
    # pasta do espelho - o rclone nao lista nada alem dela.
    try:
        r = _roda_rclone(rclone, [
            "config", "create", REMOTE, "drive",
            "scope=drive.readonly",
            "root_folder_id=" + DRIVE_FOLDER_ID,
        ], timeout=args.timeout, herdar_saida=True)
    except subprocess.TimeoutExpired:
        _sair({"estado": "erro",
               "erro": "tempo esgotado esperando a autorizacao no navegador"}, 1)
    if r.returncode != 0 or not _remote_existe(rclone):
        _sair({"estado": "erro", "erro": "rclone config create falhou"}, 1)
    ok, res = _lista_ufs_remotas(rclone)
    if ok:
        _sair({"estado": "ok", "remote": REMOTE, "ufs_disponiveis": res}, 0)
    if res == "sem_acesso":
        _sair({"estado": "sem_acesso", "remote": REMOTE,
               "dica": ("A conta conectou, mas nao enxerga o espelho de CATs. "
                        "Ou a conta escolhida no navegador foi outra, ou falta "
                        "ativar o acesso. " + DICA_SEM_ACESSO)}, 3)
    _sair({"estado": "erro", "erro": res}, 1)


def cmd_sync(args):
    rclone = _rclone()
    if not rclone:
        _sair({"estado": "rclone_ausente"}, 2)
    if not _remote_existe(rclone):
        _sair({"estado": "remote_nao_configurado"}, 2)
    uf = _uf(args)
    if not uf:
        _sair({"estado": "uf_ausente",
               "dica": "campo uf: ausente do aft-config.md (rode /aft-setup) e nenhum --uf valido"}, 2)
    destino = _pasta_cats()
    if not destino:
        _sair({"estado": "sem_config", "dica": "rode /aft-setup primeiro"}, 2)
    ok, res = _lista_ufs_remotas(rclone)
    if not ok:
        if res == "sem_acesso":
            _sair({"estado": "sem_acesso", "dica": DICA_SEM_ACESSO}, 3)
        _sair({"estado": "erro", "erro": res}, 1)
    if uf not in res:
        _sair({"estado": "uf_nao_encontrada", "uf": uf, "ufs_disponiveis": res}, 1)

    antes = _snapshot(destino)
    # copy (nunca sync): so acrescenta/atualiza, jamais apaga o que o AFT
    # tiver posto na pasta a mao. --include so .xlsx (e o que a base le).
    r = _roda_rclone(rclone, [
        "copy", "%s:%s" % (REMOTE, uf), str(destino),
        "--update", "--include", "*.xlsx",
    ], timeout=args.timeout)
    if r.returncode != 0:
        _sair({"estado": "erro", "erro": (r.stderr or "").strip()[-400:]}, 1)
    depois = _snapshot(destino)
    novos = sorted(n for n in depois if n not in antes)
    atualizados = sorted(n for n in depois if n in antes and depois[n] != antes[n])
    _sair({"estado": "ok", "uf": uf, "pasta": str(destino),
           "novos": novos, "atualizados": atualizados,
           "total_xlsx": len(depois)}, 0)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--status", action="store_true")
    g.add_argument("--conectar", action="store_true")
    g.add_argument("--sync", action="store_true")
    ap.add_argument("--uf", help="força outra UF (padrão: campo uf: do aft-config.md)")
    ap.add_argument("--timeout", type=int, default=300)
    args = ap.parse_args()
    if args.status:
        cmd_status(args)
    elif args.conectar:
        cmd_conectar(args)
    else:
        cmd_sync(args)


if __name__ == "__main__":
    main()
