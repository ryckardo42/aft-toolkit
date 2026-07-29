#!/usr/bin/env python3
"""
docx_unpack.py — descompacta um .docx (que é um ZIP) numa pasta, para edição
direta do word/document.xml. Par do docx_pack.py.

Uso:
    python docx_unpack.py <arquivo.docx> <pasta_destino>
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

import sys
import zipfile


def desempacotar(docx, destino):
    """Extrai o .docx em `destino`. Usa a zipfile da biblioteca padrao — NUNCA
    o comando `unzip`, que nao existe numa instalacao limpa do Windows."""
    with zipfile.ZipFile(docx) as z:
        z.extractall(destino)
    return destino


def main():
    if len(sys.argv) != 3:
        print("uso: docx_unpack.py <arquivo.docx> <pasta_destino>", file=sys.stderr)
        sys.exit(1)
    docx, destino = sys.argv[1], sys.argv[2]
    desempacotar(docx, destino)
    print(f"OK: {docx} -> {destino}")


if __name__ == "__main__":
    main()
