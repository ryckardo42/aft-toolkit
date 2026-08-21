#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
det_criar.py — redige RASCUNHO de notificação DET pela API oficial.

IRMÃO de escrita do det_baixar.py (que é leitura). Usa a MESMA via — o token
de sessão emprestado pela extensão ao servidor do painel — mas agora para
CRIAR uma notificação nova, em estado de rascunho, para um RI existente.

Fronteira dura, técnica (a própria API do DET a impõe) e inegociável:
  - POST /notificacoes           cria a casca (status EM_ELABORACAO)
  - PUT  /notificacoes/{uid}/rascunho   preenche o rascunho (RI, itens...)
  - PUT  /notificacoes/{uid}/lavratura  LAVRA — ato de autoridade, efeito legal
Este módulo faz APENAS as duas primeiras. A LAVRATURA nunca é chamada aqui:
é sempre um clique do AFT, no site, depois de revisar o rascunho. Regra de
ouro do perfil: o assistente redige a minuta, o AFT decide e transmite.

Estado atual (21/08/2026): FASE DE DESCOBERTA. Só `recuperar_crua` — leitura
do JSON completo de uma notificação real, para servir de molde à construção
do rascunho. A criação em si entra depois que o molde estiver conferido.
"""
from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import det_baixar  # noqa: E402  (pesquisar_por_codigo, TokenExpirado, _requisicao)


def recuperar_crua(token: str, codigo: str) -> dict:
    """JSON completo de uma notificação (GET /notificacoes/{uid}), pelo código.
    Leitura pura — serve de MOLDE para montar o rascunho. Lança TokenExpirado
    (401/403) ou RuntimeError."""
    n = det_baixar.pesquisar_por_codigo(token, codigo)
    if not n:
        raise RuntimeError(f"notificação {codigo} não encontrada no DET")
    uid = n.get("uid")
    if not uid:
        raise RuntimeError(f"notificação {codigo} veio sem uid")
    bruto = det_baixar._requisicao(token, f"/notificacoes/{uid}")
    return json.loads(bruto.decode("utf-8"))


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if len(sys.argv) != 3:
        print("uso: python det_criar.py <CODIGO> <token>", file=sys.stderr)
        sys.exit(1)
    print(json.dumps(recuperar_crua(sys.argv[2], sys.argv[1]),
                     ensure_ascii=False, indent=2))
