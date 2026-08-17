#!/usr/bin/env python3
"""
comprimir_pdf.py — comprime um PDF de anexo do Sistema Auditor. Multiplataforma.

O limite de 10 MB do Sistema Auditor vale para a SOMA dos anexos de CADA auto de
infracao, nao por arquivo: use `limite_mb` para passar o alvo DESTE arquivo dentro
do orcamento do auto (ex.: 3 anexos no mesmo auto -> alvo de ~3 MB cada). Sem o
argumento, assume 10 MB (so serve quando o auto tem um anexo so).

Uso:
    python comprimir_pdf.py <entrada.pdf> <saida.PDF> [limite_mb]

<saida.PDF> pode ser o proprio <entrada.pdf> (comprimir no lugar um anexo que ja
esta com o nome AI_...).

Estratégia:
  1. Se houver Ghostscript no PATH (gs / gswin64c / gswin32c), usa /ebook
     (150 dpi) e, se ainda exceder, /screen (72 dpi). É a compressão mais forte.
  2. Sem Ghostscript, recomprime os streams com pikepdf (pip install pikepdf).
  3. Se mesmo assim exceder o limite, mantém o melhor resultado e sai com
     código 2, avisando que o arquivo continua acima do limite.

NUNCA envie o PDF para serviços de compressão online — documentos de
fiscalização contêm dados sensíveis.
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

import atexit
import os
import shutil
import subprocess
import sys
import tempfile

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


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

    # Comprimir no lugar (entrada == saida): trabalha sobre uma cópia, para nunca
    # ler e gravar o mesmo arquivo. A cópia é apagada ao final (é dado sensível).
    if os.path.abspath(entrada) == os.path.abspath(saida):
        copia = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False).name
        shutil.copyfile(entrada, copia)
        atexit.register(lambda: os.path.exists(copia) and os.remove(copia))
        entrada = copia

    if mb(entrada) <= limite:
        shutil.copyfile(entrada, saida)
        print(f"OK: {saida} ({mb(saida):.1f} MB, já abaixo de {limite:.0f} MB)")
        return

    gs = find_gs()
    if gs:
        melhor = None  # so grava em `saida` um PDF que o Ghostscript gerou de fato
        for preset in ("/ebook", "/screen"):
            tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False).name
            try:
                gs_compress(gs, entrada, tmp, preset)
            except subprocess.CalledProcessError:
                os.remove(tmp)
                continue
            if melhor:
                os.remove(melhor)
            melhor = tmp
            if mb(tmp) <= limite:
                shutil.move(tmp, saida)
                print(f"OK: {saida} ({mb(saida):.1f} MB via Ghostscript {preset})")
                return
        if melhor is None:
            fail(f"Ghostscript não conseguiu processar o PDF: {sys.argv[1]}")
        shutil.move(melhor, saida)
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
        f"AVISO: {saida} ficou com {mb(saida):.1f} MB, ainda acima do alvo de "
        f"{limite:.1f} MB. Considere dividir o PDF, reduzir o número de anexos "
        f"(o limite de 10 MB é a soma dos anexos de cada auto) ou anexar manualmente.",
        file=sys.stderr,
    )
    sys.exit(2)


if __name__ == "__main__":
    main()
