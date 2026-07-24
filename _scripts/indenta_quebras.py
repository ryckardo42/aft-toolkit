#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
indenta_quebras.py — recuo de primeira linha nos autos do Sistema Auditor.

O campo do auto no .txt é uma linha única e usa o comando #13#10 (CR+LF) como
quebra de linha. Sem recuo, ao importar, os parágrafos ficam grudados / confusos.
Este script insere 8 espaços após cada #13#10 que precede TEXTO real, criando o
recuo de primeira linha em cada parágrafo e subtítulo.

Regra (espelha o padrão do arquivo de referência AI_5 de Autos 22-07):
  - #13#10 seguido de " . " (marcador de linha em branco entre subtítulos):
    NÃO recebe os 8 espaços — o ponto continua com 1 espaço de cada lado.
  - #13#10 seguido de qualquer outro conteúdo (parágrafo, subtítulo, alínea):
    recebe exatamente 8 espaços logo após.

Opera apenas sobre o campo de texto do auto (campo 18, índice 17) de cada linha
tipo 1 do .txt. É idempotente: rodar de novo não duplica o recuo (normaliza para
exatamente 8 espaços). Preserva o encoding do arquivo.

Uso:
    python indenta_quebras.py "<arquivo.txt>"
"""
import sys
import re

INDENT = " " * 8
# #13#10 NÃO seguido de " . " (marcador de linha em branco), consumindo os espaços
# já existentes logo após, para normalizar em exatamente 8 (idempotência).
PADRAO = re.compile(r"#13#10(?! \. ) *")


def indentar_campo(campo: str) -> str:
    return PADRAO.sub("#13#10" + INDENT, campo)


def main():
    if len(sys.argv) < 2:
        print("uso: python indenta_quebras.py <arquivo.txt>", file=sys.stderr)
        return 2
    caminho = sys.argv[1]

    encoding = "utf-8"
    try:
        conteudo = open(caminho, encoding="utf-8").read()
    except UnicodeDecodeError:
        encoding = "latin-1"
        conteudo = open(caminho, encoding="latin-1").read()

    linhas = conteudo.split("\n")
    total_breaks = 0
    for i, linha in enumerate(linhas):
        if not linha.startswith("1\t"):
            continue
        campos = linha.split("\t")
        if len(campos) < 18:
            continue
        antes = campos[17]
        depois = indentar_campo(antes)
        total_breaks += len(PADRAO.findall(antes))
        campos[17] = depois
        linhas[i] = "\t".join(campos)

    novo = "\n".join(linhas)
    with open(caminho, "w", encoding=encoding, newline="") as f:
        f.write(novo)

    print("OK: recuo aplicado. %d quebra(s) #13#10 de conteudo indentada(s) "
          "(8 espacos); marcadores de linha em branco ' . ' preservados. "
          "Encoding: %s." % (total_breaks, encoding))
    return 0


if __name__ == "__main__":
    sys.exit(main())
