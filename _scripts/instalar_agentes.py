#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
instalar_agentes.py - Copia os agentes do toolkit para ~/.claude/agents/.

O repositório do toolkit É a pasta ~/.claude/skills; os agentes (subagentes do
Claude Code) vivem em skills/agents/*.md, mas o Claude Code só os descobre em
~/.claude/agents/. Este script faz a cópia (idempotente: só copia o que mudou)
e relata em JSON. Chamado pelo /aft-setup e pelo /aft-atualizar; o /aft-doctor
faz a mesma comparação em modo leitura.

Uso:
  python instalar_agentes.py            # instala/atualiza o que mudou
  python instalar_agentes.py status     # só relata, não copia nada
"""
import json
import shutil
import sys
from pathlib import Path

ORIGEM = Path(__file__).resolve().parent.parent / "agents"
DESTINO = Path.home() / ".claude" / "agents"


def main():
    modo = sys.argv[1] if len(sys.argv) > 1 else "instalar"
    res = {"ok": True, "modo": modo, "origem": str(ORIGEM), "destino": str(DESTINO),
           "instalados": [], "atualizados": [], "em_dia": [], "erros": []}
    if not ORIGEM.is_dir():
        res["ok"] = False
        res["erros"].append("pasta agents/ nao existe no toolkit (rode /aft-atualizar)")
        print(json.dumps(res, ensure_ascii=False))
        return
    fontes = sorted(ORIGEM.glob("*.md"))
    if not fontes:
        res["ok"] = False
        res["erros"].append("nenhum agente encontrado em agents/")
        print(json.dumps(res, ensure_ascii=False))
        return
    for fonte in fontes:
        alvo = DESTINO / fonte.name
        try:
            if alvo.is_file() and alvo.read_bytes() == fonte.read_bytes():
                res["em_dia"].append(fonte.name)
                continue
            estado = "atualizados" if alvo.is_file() else "instalados"
            if modo != "status":
                DESTINO.mkdir(parents=True, exist_ok=True)
                shutil.copy2(fonte, alvo)
            res[estado].append(fonte.name)
        except OSError as exc:
            res["ok"] = False
            res["erros"].append(f"{fonte.name}: {exc}")
    print(json.dumps(res, ensure_ascii=False))


main()
