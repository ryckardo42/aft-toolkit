#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""notebooklm_consulta.py - consulta um notebook pela CHAVE, e sabe explicar a falha.

Faz duas coisas que antes ficavam espalhadas por dez SKILL.md:

  1. resolve a chave (nr-12, ementario-sst) no ID da cohort deste AFT, chamando
     o notebook_id.py;
  2. roda o `notebooklm ask` e TRADUZ a falha, em vez de deixar toda falha virar
     "NotebookLM indisponivel".

Por que o item 2 importa
------------------------
O Google so poe um notebook compartilhado na colecao da conta depois que a
pessoa **interage com o chat dele uma vez** - abrir o link nao basta. Antes
disso, qualquer consulta responde `not found` (rpc_code=5). As skills tratavam
isso como indisponibilidade e seguiam sem ementario, caladas: o AFT perdia a
camada mais importante do enquadramento e nunca sabia que bastava um "oi".

E nao da para o toolkit dar esse "oi" por ele: a interacao com o chat consome
uma das ~50 consultas diarias da conta. Registrar os 47 notebooks de uma vez
gastaria o dia inteiro de quota antes de o AFT fiscalizar qualquer coisa. Por
isso o registro e SOB DEMANDA - e este script e quem descobre a hora.

Uso:
    python notebooklm_consulta.py <chave> [argumentos extras do ask]

    python notebooklm_consulta.py nr-12 --prompt-file pergunta.txt
    python notebooklm_consulta.py ementario-sst "Qual a ementa para ...?"

O `--notebook <id>` e o `--json` sao postos por este script; o resto e repassado
ao `notebooklm ask` sem alteracao.

Saida e codigos:
    0  sucesso - o stdout e o JSON do proprio CLI, intacto (as skills continuam
       lendo `answer` e `references[].cited_text` como sempre)
    3  o notebook nao existe para a cohort deste AFT -> siga sem essa camada
    5  PRIMEIRO ACESSO PENDENTE -> stdout traz {"estado": "primeiro-acesso",
       "titulo", "url"}. Mostre o recado ao AFT (uma linha, com o link), espere
       o "pronto" e repita a MESMA consulta.
    6  sessao do NotebookLM caida -> /aft-notebooklm-login
    2  chave desconhecida · 4 mapa ausente · 1 outra falha (rede, CLI)
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
from pathlib import Path

TIMEOUT = 180  # s - o ask pensa, e o gancho de reautenticacao pode gastar ~25 s

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).resolve().parent))
from notebook_id import SAIDA, resolver  # noqa: E402


def _e_sessao(texto: str) -> bool:
    t = texto.lower()
    return any(p in t for p in (
        "not authenticated", "authentication", "not logged in",
        "run 'notebooklm login'", "session expired", "sign in",
    ))


def _e_primeiro_acesso(texto: str) -> bool:
    """O servidor recusou o notebook: `not found` / rpc_code=5.

    A resposta e a MESMA para "tem acesso e nunca interagiu" e para "nao tem
    acesso" - o Google nao distingue os dois. O recado ao AFT precisa cobrir os
    dois casos, e por isso ele fala em abrir o notebook E em pedir acesso no
    portal se ele nao abrir.
    """
    t = texto.lower()
    return "not found" in t or "rpc_code=5" in t or "permission" in t


def main(argv: list[str]) -> int:
    if not argv:
        print("uso: notebooklm_consulta.py <chave> [args do ask]", file=sys.stderr)
        return 2
    chave, extras = argv[0], argv[1:]

    r = resolver(chave)
    if r["estado"] != "ok":
        if r["estado"] == "sem-copia":
            print(f"notebook '{chave}' nao existe para a cohort {r['cohort']}", file=sys.stderr)
        elif r["estado"] == "chave-desconhecida":
            print(f"chave '{chave}' nao esta em config/notebooks.json", file=sys.stderr)
        else:
            print("config/notebooks.json nao encontrado", file=sys.stderr)
        return SAIDA.get(r["estado"], 1)

    cli = shutil.which("notebooklm")
    if not cli:
        print("comando notebooklm nao encontrado", file=sys.stderr)
        return 1

    try:
        p = subprocess.run(
            [cli, "--quiet", "ask", "--notebook", r["id"], "--json", *extras],
            capture_output=True, text=True, timeout=TIMEOUT,
            encoding="utf-8", errors="replace",
        )
    except subprocess.TimeoutExpired:
        print("o NotebookLM nao respondeu a tempo", file=sys.stderr)
        return 1
    except OSError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    saida = (p.stdout or "") + "\n" + (p.stderr or "")
    if p.returncode == 0 and '"error"' not in saida:
        sys.stdout.write(p.stdout)
        return 0
    if _e_sessao(saida):
        print("sessao do NotebookLM caida - rode /aft-notebooklm-login", file=sys.stderr)
        return 6
    if _e_primeiro_acesso(saida):
        print(json.dumps({"estado": "primeiro-acesso", "chave": chave,
                          "titulo": r["titulo"], "url": r["url"]}, ensure_ascii=False))
        return 5
    print((saida.strip().splitlines() or ["falha sem detalhe"])[-1][:300], file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
