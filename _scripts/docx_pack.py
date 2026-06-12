#!/usr/bin/env python3
"""
docx_pack.py — reempacota a pasta descompactada por docx_unpack.py num .docx
válido e valida o XML principal antes de gravar.

Uso:
    python docx_pack.py <pasta_descompactada> <saida.docx>
"""
import os
import sys
import xml.etree.ElementTree as ET
import zipfile


def fail(msg):
    print(f"ERRO: {msg}", file=sys.stderr)
    sys.exit(1)


def main():
    if len(sys.argv) != 3:
        fail("uso: docx_pack.py <pasta_descompactada> <saida.docx>")

    pasta, saida = sys.argv[1], sys.argv[2]
    doc_xml = os.path.join(pasta, "word", "document.xml")
    if not os.path.isfile(doc_xml):
        fail(f"não encontrei {doc_xml} — a pasta não parece um docx descompactado")

    # Valida o XML antes de empacotar (um XML quebrado gera docx corrompido).
    try:
        ET.parse(doc_xml)
    except ET.ParseError as e:
        fail(f"word/document.xml inválido: {e}")

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

    print(f"OK: {saida}")


if __name__ == "__main__":
    main()
