#!/usr/bin/env python3
"""
docx_pack.py — reempacota a pasta descompactada por docx_unpack.py num .docx
válido e valida o XML principal antes de gravar.

Uso:
    python docx_pack.py <pasta_descompactada> <saida.docx>
"""

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

import os
import sys
import xml.etree.ElementTree as ET
import zipfile


def fail(msg):
    print(f"ERRO: {msg}", file=sys.stderr)
    sys.exit(1)


def empacotar(pasta, saida):
    """Reempacota `pasta` (um .docx descompactado) em `saida`, validando o XML
    principal antes. Usa a zipfile da biblioteca padrao — NUNCA o comando `zip`,
    que nao existe numa instalacao limpa do Windows (o Git for Windows traz o
    `unzip.exe`, mas nao o `zip.exe`). Levanta ValueError em caso de problema."""
    doc_xml = os.path.join(pasta, "word", "document.xml")
    if not os.path.isfile(doc_xml):
        raise ValueError(f"não encontrei {doc_xml} — a pasta não parece um docx descompactado")

    # Valida o XML antes de empacotar (um XML quebrado gera docx corrompido).
    try:
        ET.parse(doc_xml)
    except ET.ParseError as e:
        raise ValueError(f"word/document.xml inválido: {e}") from e

    with zipfile.ZipFile(saida, "w", zipfile.ZIP_DEFLATED) as z:
        # [Content_Types].xml primeiro, por convenção OPC.
        ct = os.path.join(pasta, "[Content_Types].xml")
        if os.path.isfile(ct):
            z.write(ct, "[Content_Types].xml")
        for root, _dirs, files in os.walk(pasta):
            for name in files:
                full = os.path.join(root, name)
                rel = os.path.relpath(full, pasta).replace(os.sep, "/")
                if rel == "[Content_Types].xml":
                    continue
                z.write(full, rel)
    return saida


def main():
    if len(sys.argv) != 3:
        fail("uso: docx_pack.py <pasta_descompactada> <saida.docx>")

    pasta, saida = sys.argv[1], sys.argv[2]
    try:
        empacotar(pasta, saida)
    except ValueError as e:
        fail(str(e))

    print(f"OK: {saida}")


if __name__ == "__main__":
    main()
