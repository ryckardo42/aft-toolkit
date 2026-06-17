#!/usr/bin/env python3
"""
backup_arquivo.py - copia de seguranca antes de editar arquivos sensiveis (AFT Toolkit).

Convencao do toolkit: ANTES de sobrescrever/editar um arquivo legal existente (.docx do
RT, ou regravar o memory.md de uma OS), faca um backup com este script. Assim uma edicao
errada nunca perde o original.

- Se o arquivo NAO existir (criacao nova), nao ha nada a salvar - sai em silencio (ok).
- O backup vai para uma subpasta `.backups/` ao lado do arquivo, com carimbo de data/hora
  no nome, para nunca sobrescrever um backup anterior.

Uso:
    python backup_arquivo.py "<caminho do arquivo>"
Imprime o caminho do backup criado (ou avisa que nao havia o que salvar).
"""
import os
import shutil
import sys
from datetime import datetime

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def main():
    if len(sys.argv) != 2:
        print("uso: python backup_arquivo.py <arquivo>", file=sys.stderr)
        sys.exit(2)
    arq = sys.argv[1]
    if not os.path.isfile(arq):
        print(f"Sem backup: '{arq}' ainda nao existe (arquivo novo).")
        sys.exit(0)

    pasta = os.path.dirname(os.path.abspath(arq))
    base = os.path.basename(arq)
    stem, ext = os.path.splitext(base)
    bkdir = os.path.join(pasta, ".backups")
    os.makedirs(bkdir, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    dest = os.path.join(bkdir, f"{stem}_{ts}{ext}")
    # Evita colisao improvavel no mesmo segundo.
    n = 1
    while os.path.exists(dest):
        dest = os.path.join(bkdir, f"{stem}_{ts}_{n}{ext}")
        n += 1
    shutil.copy2(arq, dest)
    print(f"Backup criado: {dest}")
    sys.exit(0)


if __name__ == "__main__":
    main()
