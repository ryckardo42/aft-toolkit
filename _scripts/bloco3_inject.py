#!/usr/bin/env python3
"""
bloco3_inject.py — injeta o Subtítulo 3 (OBSERVAÇÕES) canônico nos autos (AFT Toolkit).

As skills que redigem autos terminam cada auto no bloco 2 (IRREGULARIDADE) + ELEMENTOS
DE CONVICÇÃO, SEM o bloco 3. O /gera-ai chama este script para inserir, em TODO auto, o
bloco 3 único e fixo definido em `config/blocos_auto.md` (entre as marcas <BLOCO3>).

- Insere o bloco 3 imediatamente ANTES de "ELEMENTOS DE CONVICÇÃO:" de cada auto.
- É idempotente e compatível com o legado: se um auto JÁ contém "3) OBSERVAÇÕES" (auto
  antigo, escrito à mão), ele é deixado intacto (não duplica).
- Texto copiado byte a byte do catálogo — nunca reescrito pelo modelo.

Uso:
    python bloco3_inject.py <autos.md> [saida.md]
    # sem saida -> grava no proprio arquivo (in place). Idempotente.
"""
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HEADER_RE = re.compile(r"(=== AUTO(?: DE INFRAÇÃO)? #\d+ ===)")
ELEM_RE = re.compile(r"^ELEMENTOS DE CONVICÇÃO:", re.MULTILINE)
# Reconhece o formato atual ("III - OBSERVAÇÕES") e o legado ("3) OBSERVAÇÕES"),
# para nunca duplicar o bloco num auto que ja o tenha.
JA_TEM_OBS = re.compile(r"^\s*(?:3\)|III\s*[-–)])\s*OBSERVA", re.MULTILINE | re.IGNORECASE)


def carregar_bloco3():
    cfg = os.path.join(os.path.dirname(__file__), "..", "config", "blocos_auto.md")
    cfg = os.path.normpath(cfg)
    linhas = open(cfg, encoding="utf-8").read().splitlines()
    # A marca so vale quando e a LINHA INTEIRA (evita pegar mencoes em prosa,
    # ex.: "entre as marcas `<BLOCO3>` e `</BLOCO3>`").
    try:
        i = linhas.index("<BLOCO3>")
        j = linhas.index("</BLOCO3>", i + 1)
    except ValueError:
        print(f"ERRO: marcas <BLOCO3>/</BLOCO3> (linha inteira) nao encontradas em {cfg}",
              file=sys.stderr)
        sys.exit(2)
    bloco = "\n".join(linhas[i + 1:j]).strip()
    if not bloco:
        print(f"ERRO: bloco 3 vazio em {cfg}", file=sys.stderr)
        sys.exit(2)
    return bloco


def injetar_no_auto(corpo, bloco3):
    if JA_TEM_OBS.search(corpo):
        return corpo, False  # legado: ja tem bloco 3, nao mexe
    m = ELEM_RE.search(corpo)
    if m:
        i = m.start()
        novo = corpo[:i].rstrip() + "\n\n" + bloco3 + "\n\n" + corpo[i:].lstrip("\n")
    else:
        novo = corpo.rstrip() + "\n\n" + bloco3 + "\n"
    return novo, True


def main():
    if len(sys.argv) < 2:
        print("uso: python bloco3_inject.py <autos.md> [saida.md]", file=sys.stderr)
        sys.exit(2)
    entrada = sys.argv[1]
    saida = sys.argv[2] if len(sys.argv) > 2 else entrada
    if not os.path.isfile(entrada):
        print(f"ERRO: arquivo nao encontrado: {entrada}", file=sys.stderr)
        sys.exit(2)

    bloco3 = carregar_bloco3()
    texto = open(entrada, encoding="utf-8").read()

    partes = HEADER_RE.split(texto)
    # partes = [pre, header1, corpo1, header2, corpo2, ...]
    n_inj = 0
    n_skip = 0
    if len(partes) == 1:
        print("AVISO: nenhum cabecalho '=== AUTO ... ===' encontrado; nada a fazer.",
              file=sys.stderr)
        out = texto
    else:
        out = [partes[0]]
        for k in range(1, len(partes), 2):
            header = partes[k]
            corpo = partes[k + 1] if k + 1 < len(partes) else ""
            novo, injetou = injetar_no_auto(corpo, bloco3)
            if injetou:
                n_inj += 1
            else:
                n_skip += 1
            out.append(header)
            out.append(novo)
        out = "".join(out)

    with open(saida, "w", encoding="utf-8") as f:
        f.write(out)
    print(f"Bloco 3 injetado em {n_inj} auto(s); {n_skip} ja tinham (mantidos). "
          f"Saida: {saida}")


if __name__ == "__main__":
    main()
