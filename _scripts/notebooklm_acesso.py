#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""notebooklm_acesso.py — quais notebooks do ementário o Claude consegue consultar.

Percorre os notebooks de ``config/notebooks.json`` e testa, um por um, se a conta
Google conectada realmente alcança cada um. Serve para o AFT saber ANTES de
precisar: "estas NRs eu já consulto; nestas o Claude vai falhar".

Por que isso existe
-------------------
O ``notebooklm list`` NÃO lista "o que compartilharam comigo": ele lista os
notebooks **vistos recentemente** (RPC ListRecentlyViewedProjects). Um notebook
compartilhado que o AFT nunca abriu não aparece na lista e responde
``not found`` — inclusive ao ``ask``, que consulta o notebook antes de chegar ao
chat. Ou seja: **não há como ativar um notebook pelo terminal**. O primeiro
acesso é do AFT, pelo navegador: abrir o notebook e escrever um "oi" no chat.
Feito isso uma vez, ele entra na coleção da conta e as skills passam a
consultá-lo para sempre.

Este script não conserta nada — ele MEDE e diz exatamente o que abrir.

Uso:
    python notebooklm_acesso.py            # varre todos os notebooks do mapa
    python notebooklm_acesso.py --json     # idem (a saída sempre é JSON)

Saída: uma linha JSON com
    estado           ok | cli-ausente | sessao-expirada
    total            quantos notebooks o mapa tem
    disponiveis      [{chave, titulo}]            -> o Claude já consulta
    indisponiveis    [{chave, titulo, url}]       -> precisam do primeiro acesso
    erros            [{chave, titulo, detalhe}]   -> falha de rede/CLI, não é acesso
    portal           endereço para solicitar acesso

Um notebook em ``indisponiveis`` pode estar em dois estados que o servidor
responde de forma idêntica (``not found``): (1) o AFT tem acesso mas nunca
abriu; (2) o AFT não tem acesso. O recado ao AFT tem que cobrir os dois.
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
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

PORTAL = "https://notebooks-aft.vercel.app"
URL_NOTEBOOK = "https://notebooklm.google.com/notebook/{}"

# Quantas sondagens em paralelo. Baixo de proposito: cada uma e um processo do
# CLI falando com o Google, e um enxame dispara limite de taxa.
PARALELAS = 4
TIMEOUT = 45  # s por notebook (o gancho de reautenticacao pode gastar ~25 s)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def mapa_notebooks() -> dict:
    """Le o config/notebooks.json que acompanha as skills."""
    aqui = Path(__file__).resolve()
    for base in (aqui.parent, *aqui.parents):
        alvo = base / "config" / "notebooks.json"
        if alvo.is_file():
            return json.loads(alvo.read_text(encoding="utf-8")).get("notebooks", {})
    return {}


def _rodar(cli: str, *args: str) -> tuple[int, str]:
    """Roda o CLI e devolve (codigo, saida stdout+stderr juntas)."""
    try:
        r = subprocess.run(
            [cli, "--quiet", *args],
            capture_output=True, text=True, timeout=TIMEOUT,
            encoding="utf-8", errors="replace",
        )
    except subprocess.TimeoutExpired:
        return 124, "tempo esgotado"
    except OSError as exc:
        return 1, str(exc)
    return r.returncode, ((r.stdout or "") + "\n" + (r.stderr or "")).strip()


def _e_sessao(texto: str) -> bool:
    """A falha e de login (nao de acesso ao notebook)?"""
    t = texto.lower()
    return any(p in t for p in (
        "not authenticated", "authentication", "not logged in",
        "run 'notebooklm login'", "session expired", "sign in",
    ))


def _e_sem_acesso(texto: str) -> bool:
    """O servidor recusou o notebook (rpc_code=5 / not found)?"""
    t = texto.lower()
    return "not found" in t or "rpc_code=5" in t or "permission" in t


def recentes(cli: str) -> tuple[set[str], str | None]:
    """Ids dos notebooks ja na colecao da conta (vistos recentemente).

    Roda ANTES das sondagens em paralelo: valida a sessao e, se ela estiver
    expirada, deixa o gancho de reautenticacao renovar uma unica vez, em vez de
    quatro processos brigando pelo mesmo arquivo de cookies.
    """
    codigo, saida = _rodar(cli, "list", "--json")
    if codigo != 0:
        return set(), ("sessao-expirada" if _e_sessao(saida) else None)
    try:
        i, j = saida.find("{"), saida.rfind("}")
        dados = json.loads(saida[i:j + 1])
    except Exception:
        return set(), None
    return {n.get("id") for n in dados.get("notebooks", []) if n.get("id")}, None


def sondar(cli: str, chave: str, info: dict) -> dict:
    """Testa um notebook: uma chamada de metadados (1 RPC, sem custo de chat)."""
    nid = info.get("notebook_id", "")
    codigo, saida = _rodar(cli, "metadata", "-n", nid, "--json")
    base = {"chave": chave, "titulo": info.get("title", chave),
            "essencial": info.get("essencial", 0)}
    if codigo == 0 and '"error"' not in saida:
        return {**base, "situacao": "disponivel"}
    if _e_sessao(saida):
        return {**base, "situacao": "sessao"}
    if _e_sem_acesso(saida):
        return {**base, "situacao": "indisponivel", "url": URL_NOTEBOOK.format(nid)}
    return {**base, "situacao": "erro", "detalhe": saida.splitlines()[-1][:200] if saida else "sem saida"}


def main() -> int:
    notebooks = mapa_notebooks()
    saida = {
        "estado": "ok",
        "total": len(notebooks),
        "disponiveis": [],
        "indisponiveis": [],
        "erros": [],
        "portal": PORTAL,
    }

    cli = shutil.which("notebooklm")
    if not cli:
        saida["estado"] = "cli-ausente"
        print(json.dumps(saida, ensure_ascii=False))
        return 0
    if not notebooks:
        saida["estado"] = "mapa-ausente"
        print(json.dumps(saida, ensure_ascii=False))
        return 0

    ja_na_colecao, falha = recentes(cli)
    if falha == "sessao-expirada":
        saida["estado"] = "sessao-expirada"
        print(json.dumps(saida, ensure_ascii=False))
        return 0

    # Quem ja esta na colecao nao precisa de sondagem: economiza ~1 s cada.
    for chave, info in notebooks.items():
        if info.get("notebook_id") in ja_na_colecao:
            saida["disponiveis"].append({
                "chave": chave, "titulo": info.get("title", chave),
                "essencial": info.get("essencial", 0)})
    pendentes = {k: v for k, v in notebooks.items()
                 if v.get("notebook_id") not in ja_na_colecao}

    if pendentes:
        with ThreadPoolExecutor(max_workers=PARALELAS) as pool:
            resultados = list(pool.map(
                lambda kv: sondar(cli, kv[0], kv[1]), pendentes.items()))
        for r in resultados:
            situacao = r.pop("situacao")
            if situacao == "disponivel":
                saida["disponiveis"].append(r)
            elif situacao == "indisponivel":
                saida["indisponiveis"].append(r)
            elif situacao == "sessao":
                saida["estado"] = "sessao-expirada"
            else:
                saida["erros"].append(r)

    # Essenciais primeiro, na ordem do mapa: e essa a fila de cliques que o AFT
    # precisa ver antes de tudo. O resto vem depois, por titulo.
    def _ordem(x: dict) -> tuple:
        e = x.get("essencial") or 0
        return (0, e) if e else (1, 0)

    saida["disponiveis"].sort(key=lambda x: (*_ordem(x), x["titulo"].lower()))
    saida["indisponiveis"].sort(key=lambda x: (*_ordem(x), x["titulo"].lower()))
    saida["essenciais_faltando"] = [
        x["titulo"] for x in saida["indisponiveis"] if x.get("essencial")]
    print(json.dumps(saida, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
