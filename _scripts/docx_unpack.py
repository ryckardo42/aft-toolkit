#!/usr/bin/env python3
"""
docx_unpack.py — descompacta um .docx (que é um ZIP) numa pasta, para edição
direta do word/document.xml. Par do docx_pack.py.

Uso:
    python docx_unpack.py <arquivo.docx> <pasta_destino>
"""
import sys
import zipfile


def main():
    if len(sys.argv) != 3:
        print("uso: docx_unpack.py <arquivo.docx> <pasta_destino>", file=sys.stderr)
        sys.exit(1)
    docx, destino = sys.argv[1], sys.argv[2]
    with zipfile.ZipFile(docx) as z:
        z.extractall(destino)
    print(f"OK: {docx} -> {destino}")


if __name__ == "__main__":
    main()
