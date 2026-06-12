#!/usr/bin/env python3
"""
comprimir_pdf.py — comprime um PDF para caber no limite de anexo do Sistema
Auditor (10 MB). Multiplataforma.

Uso:
    python comprimir_pdf.py <entrada.pdf> <saida.PDF> [limite_mb]

Estratégia:
  1. Se houver Ghostscript no PATH (gs / gswin64c / gswin32c), usa /ebook
     (150 dpi) e, se ainda exceder, /screen (72 dpi). É a compressão mais forte.
  2. Sem Ghostscript, recomprime os streams com pikepdf (pip install pikepdf).
  3. Se mesmo assim exceder o limite, mantém o melhor resultado e sai com
     código 2, avisando que o arquivo continua acima do limite.

NUNCA envie o PDF para serviços de compressão online — documentos de
fiscalização contêm dados sensíveis.
"""
import os
import shutil
import subprocess
import sys
import tempfile


def fail(msg, code=1):
    print(f"ERRO: {msg}", file=sys.stderr)
    sys.exit(code)


def mb(path):
    return os.path.getsize(path) / (1024 * 1024)


def find_gs():
    for exe in ("gs", "gswin64c", "gswin32c"):
        if shutil.which(exe):
            return exe
    return None


def gs_compress(gs, entrada, saida, preset):
    subprocess.run(
        [
            gs, "-sDEVICE=pdfwrite", "-dCompatibilityLevel=1.4",
            f"-dPDFSETTINGS={preset}", "-dNOPAUSE", "-dQUIET", "-dBATCH",
            f"-sOutputFile={saida}", entrada,
        ],
        check=True,
    )


def main():
    if len(sys.argv) not in (3, 4):
        fail("uso: comprimir_pdf.py <entrada.pdf> <saida.PDF> [limite_mb]")

    entrada, saida = sys.argv[1], sys.argv[2]
    limite = float(sys.argv[3]) if len(sys.argv) == 4 else 10.0

    if not os.path.isfile(entrada):
        fail(f"arquivo não encontrado: {entrada}")

    if mb(entrada) <= limite:
        shutil.copyfile(entrada, saida)
        print(f"OK: {saida} ({mb(saida):.1f} MB, já abaixo de {limite:.0f} MB)")
        return

    gs = find_gs()
    if gs:
        for preset in ("/ebook", "/screen"):
            tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False).name
            try:
                gs_compress(gs, entrada, tmp, preset)
            except subprocess.CalledProcessError:
                continue
            if mb(tmp) <= limite:
                shutil.move(tmp, saida)
                print(f"OK: {saida} ({mb(saida):.1f} MB via Ghostscript {preset})")
                return
        shutil.move(tmp, saida)
    else:
        try:
            import pikepdf
        except ImportError:
            fail("nem Ghostscript nem pikepdf disponíveis. Rode: pip install pikepdf")
        with pikepdf.open(entrada) as pdf:
            pdf.save(saida, compress_streams=True, recompress_flate=True,
                     object_stream_mode=pikepdf.ObjectStreamMode.generate)
        if mb(saida) <= limite:
            print(f"OK: {saida} ({mb(saida):.1f} MB via pikepdf)")
            return

    print(
        f"AVISO: {saida} ficou com {mb(saida):.1f} MB, ainda acima de "
        f"{limite:.0f} MB. Considere dividir o PDF ou anexar manualmente.",
        file=sys.stderr,
    )
    sys.exit(2)


if __name__ == "__main__":
    main()
