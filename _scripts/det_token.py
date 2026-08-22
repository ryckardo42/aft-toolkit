#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
det_token.py — entrega ao painel local o token de sessão do DET.

O painel só conversa com o DET usando o crachá que o próprio site emitiu para o
AFT logado (um JWT de ~30 minutos, sem refresh). Existem DUAS vias para esse
crachá chegar até ele, e a ordem está em `config/canal-token-det.md`:

  1. o NAVEGADOR DO ASSISTENTE (via principal) — o assistente lê o token do
     sessionStorage da aba do DET já logada e o entrega por aqui;
  2. a EXTENSÃO Sync DET (via alternativa) — faz o mesmo sozinha, para quem
     usa um assistente sem navegador.

Este script é o lado comum das duas: recebe o token pela ENTRADA PADRÃO (nunca
como argumento, que ficaria no histórico do shell e nos logs) e o grava na
memória do painel. Ele nunca escreve o token em disco e nunca o imprime.

Uso:
    python det_token.py --status
    python det_token.py --gravar    # o token vem pelo stdin
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request

PORTA_PADRAO = 8347


def _chamar(porta: int, caminho: str, corpo: dict | None = None) -> dict:
    url = f"http://127.0.0.1:{porta}{caminho}"
    dados = json.dumps(corpo).encode("utf-8") if corpo is not None else None
    req = urllib.request.Request(
        url, data=dados,
        headers={"Content-Type": "application/json"} if dados else {})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read().decode("utf-8") or "{}")
    except urllib.error.URLError as e:
        return {"ok": False, "erro": f"painel não respondeu em {url}: {e}"}
    except ValueError as e:
        return {"ok": False, "erro": f"resposta ilegível do painel: {e}"}


def status(porta: int) -> dict:
    """Há token vivo no painel, e por quanto tempo? Usa a recarga a quente, que
    devolve a validade sem derrubar nada e sem expor o token."""
    r = _chamar(porta, "/api/recarregar", {})
    if not r.get("ok"):
        return r
    return {"ok": True, "tem_token": bool(r.get("token_preservado")),
            "validade_s": int(r.get("token_validade_s") or 0)}


def gravar(porta: int, token: str) -> dict:
    token = (token or "").strip()
    if token.count(".") != 2 or len(token) < 100:
        return {"ok": False, "erro": "isto não parece um JWT do DET "
                                     "(esperado tres partes separadas por ponto)"}
    return _chamar(porta, "/api/det-token", {"det_access_token": token})


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--status", action="store_true",
                    help="diz se o painel tem token vivo e por quanto tempo")
    ap.add_argument("--gravar", action="store_true",
                    help="lê o token do stdin e o entrega ao painel")
    ap.add_argument("--porta", type=int, default=PORTA_PADRAO)
    a = ap.parse_args()

    if a.gravar:
        r = gravar(a.porta, sys.stdin.read())
    elif a.status:
        r = status(a.porta)
    else:
        ap.print_help()
        return 2
    # a resposta do painel não contém o token; ainda assim, só repasso o que interessa
    print(json.dumps({k: v for k, v in r.items() if "token" not in k.lower()
                      or k in ("tem_token",)}, ensure_ascii=False))
    return 0 if r.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
