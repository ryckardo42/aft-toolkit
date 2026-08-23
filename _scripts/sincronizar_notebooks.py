#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""sincronizar_notebooks.py - traz os IDs do mapa do SITE para o config/notebooks.json.

FERRAMENTA DO MANTENEDOR, nao do AFT. O portal notebooks-aft tem o seu proprio
mapa (assets/notebooks-map.json), que e quem manda: e de la que sai o link em
que o AFT clica. O toolkit tinha uma copia a mao desse mapa, e as duas
divergiram em silencio - nomes de chave diferentes, notebooks presentes so de um
lado. Este script existe para nao acontecer de novo.

O que ele faz, e o que NAO faz:

  - atualiza os IDs por cohort de cada notebook (o campo 'ids');
  - acrescenta notebook novo que apareceu no site (titulo = label do site);
  - avisa, sem apagar nada, o que existe so de um lado.

Nao mexe em 'title', 'essencial' nem 'publico': essa metainformacao e do toolkit
(o site nao a tem) e continua morando no config/notebooks.json. Notebook de link
publico e pulado de proposito - o endereco dele nao muda com a cohort.

Uso:
    python sincronizar_notebooks.py --site "<caminho do notebooks-map.json>"
    python sincronizar_notebooks.py --site "<caminho>" --conferir   # so relata
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def caminho_mapa() -> Path | None:
    aqui = Path(__file__).resolve()
    for base in (aqui.parent, *aqui.parents):
        alvo = base / "config" / "notebooks.json"
        if alvo.is_file():
            return alvo
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--site", required=True, help="assets/notebooks-map.json do portal")
    ap.add_argument("--conferir", action="store_true", help="relata sem gravar")
    a = ap.parse_args()

    destino = caminho_mapa()
    if destino is None:
        print("config/notebooks.json nao encontrado", file=sys.stderr)
        return 4
    doc = json.loads(destino.read_text(encoding="utf-8"))
    site_doc = json.loads(Path(a.site).read_text(encoding="utf-8"))
    site = {n["key"]: n for n in site_doc.get("notebooks", [])}

    mudancas, avisos = [], []
    usadas = set()
    for chave, info in doc.get("notebooks", {}).items():
        sk = info.get("chave_site", chave)
        if info.get("publico"):
            usadas.add(sk)
            continue
        s = site.get(sk)
        if s is None:
            avisos.append(f"so no toolkit: {chave} (chave_site '{sk}' nao esta no site)")
            continue
        usadas.add(sk)
        novos = {"1": s.get("cohort1")}
        for n in range(2, 10):  # cohort 3, 4... entram sozinhas quando o site as criar
            v = s.get(f"cohort{n}")
            if v:
                novos[str(n)] = v
        novos = {k: v for k, v in novos.items() if v}
        if novos != info.get("ids"):
            mudancas.append(f"{chave}: {info.get('ids')} -> {novos}")
            info["ids"] = novos

    for sk, s in site.items():
        if sk in usadas:
            continue
        novos = {"1": s["cohort1"]}
        if s.get("cohort2"):
            novos["2"] = s["cohort2"]
        doc["notebooks"][sk] = {"title": s.get("label", sk), "ids": novos}
        mudancas.append(f"NOVO {sk} ({s.get('label', sk)})")

    doc["notebooks"] = dict(sorted(doc["notebooks"].items()))
    for campo in ("cohort_ativa", "cap_por_notebook"):
        if campo in site_doc and site_doc[campo] != doc.get(campo):
            mudancas.append(f"{campo}: {doc.get(campo)} -> {site_doc[campo]}")
            doc[campo] = site_doc[campo]

    for x in avisos:
        print("aviso:", x)
    if not mudancas:
        print("mapa ja em dia com o site")
        return 0
    for m in mudancas:
        print(("[conferir] " if a.conferir else "") + m)
    if not a.conferir:
        destino.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n",
                           encoding="utf-8")
        print(f"gravado: {destino}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
