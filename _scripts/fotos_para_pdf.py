#!/usr/bin/env python3
"""
fotos_para_pdf.py — converte uma foto de evidência em PDF A4 (200 dpi) para anexo
de auto de infração no Sistema Auditor. Multiplataforma (Windows/macOS/Linux).

Uso:
    python fotos_para_pdf.py <foto_entrada> <saida.PDF>

Requisitos: Pillow (pip install pillow). Para fotos HEIC/HEIF de iPhone,
instale também pillow-heif (pip install pillow-heif); sem ele, o script aborta
pedindo que a foto seja convertida para JPG antes.

Regras aplicadas:
  - Corrige orientação EXIF (fotos verticais de celular não saem deitadas).
  - Normaliza para RGB.
  - Reduz para no máximo A4 a 200 dpi (1654x2339) — PDFs gigantes travam o
    Sistema Auditor.
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

from PIL import Image, ImageOps

A4_MAX = (1654, 2339)  # A4 a 200 dpi


def fail(msg):
    print(f"ERRO: {msg}", file=sys.stderr)
    sys.exit(1)


def main():
    if len(sys.argv) != 3:
        fail("uso: fotos_para_pdf.py <foto_entrada> <saida.PDF>")

    origem, destino = sys.argv[1], sys.argv[2]

    if origem.lower().endswith((".heic", ".heif")):
        try:
            import pillow_heif  # noqa: F401

            pillow_heif.register_heif_opener()
        except ImportError:
            fail(
                "foto HEIC/HEIF detectada e pillow-heif não está instalado. "
                "Rode: pip install pillow-heif  (ou converta a foto para JPG antes)"
            )

    img = Image.open(origem)
    img = ImageOps.exif_transpose(img)  # CRÍTICO: senão fotos verticais saem deitadas
    if img.mode != "RGB":
        img = img.convert("RGB")
    img.thumbnail(A4_MAX)
    img.save(destino, "PDF", resolution=200.0)
    print(f"OK: {destino}")


if __name__ == "__main__":
    main()
