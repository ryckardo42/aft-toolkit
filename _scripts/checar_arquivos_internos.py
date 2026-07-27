#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
checar_arquivos_internos.py — impede que referências ao nosso ambiente de trabalho
vazem para dentro do texto do auto de infração.

O auto é documento legal entregue ao autuado e juntado ao processo administrativo.
Arquivos internos do AFT Toolkit (inspecao-fisica.md, memory.md, analise-PGR.md,
.depara_*.json, pastas "OS ATIVAS", nomes de skill /aft-*, caminhos do computador do
auditor) NAO sao elementos de conviccao, nao vao anexos ao auto e nao devem ser
citados em nenhum subtitulo — muito menos em ELEMENTOS DE CONVICCAO.

Elemento de conviccao e o que instrui o auto: a propria inspecao fisica (o fato de
ter sido realizada, com data e local), o documento apresentado pela empresa, o
registro fotografico anexado, a consulta a sistema oficial. O relato interno que o
auditor escreveu para si mesmo nao e prova.

Opera sobre:
  - autos.md  -> varre apenas de "=== AUTO DE INFRACAO" em diante (o cabecalho de
                 trabalho do arquivo nao vai para o TXT e e ignorado de proposito);
  - .txt do Sistema Auditor -> varre os campos 18 (texto) e 19 (elementos de
                 conviccao) de cada linha tipo 1.

Uso:
    python checar_arquivos_internos.py <arquivo>

Saida: exit 0 se limpo; exit 1 listando cada ocorrencia com o trecho ao redor.
"""
import sys
import re

PADROES = [
    (re.compile(r"[\w\-]+\.(?:md|json|ya?ml)\b", re.I),
     "arquivo de trabalho interno"),
    (re.compile(r"\.tokenized\.txt\b|\.depara\b", re.I),
     "artefato interno do /aft-gera-ai"),
    (re.compile(r"\bOS ATIVAS\b|\bOS ARQUIVADAS\b", re.I),
     "pasta de trabalho do auditor"),
    (re.compile(r"[A-Za-z]:\\(?:Documents|Users|SistemasAFT)|/Documents/AFT\b"),
     "caminho do computador do auditor"),
    (re.compile(r"/aft-[a-z0-9\-]+"),
     "nome de skill do toolkit"),
    (re.compile(r"\bAFT Toolkit\b", re.I),
     "referencia ao toolkit"),
    (re.compile(r"\bAutos \d{2}-\d{2}\b"),
     "pasta de lavratura"),
    (re.compile(r"\[\[[A-Z_0-9]+\]\]"),
     "token de pseudonimizacao nao re-hidratado"),
]


def trechos_do_arquivo(caminho):
    """Devolve [(rotulo, texto)] das regioes que de fato vao para o auto."""
    try:
        conteudo = open(caminho, encoding="utf-8").read()
    except UnicodeDecodeError:
        conteudo = open(caminho, encoding="latin-1").read()

    linhas_tipo1 = [l for l in conteudo.split("\n") if l.startswith("1\t")]
    if linhas_tipo1:
        regioes = []
        for i, linha in enumerate(linhas_tipo1, 1):
            campos = linha.split("\t")
            if len(campos) > 17:
                regioes.append(("auto %d / texto" % i, campos[17]))
            if len(campos) > 18:
                regioes.append(("auto %d / ELEMENTOS DE CONVICCAO" % i, campos[18]))
        return regioes

    m = re.search(r"===\s*AUTO", conteudo)
    if m:
        return [("autos.md", conteudo[m.start():])]
    return [("arquivo", conteudo)]


def main():
    if len(sys.argv) < 2:
        print("uso: python checar_arquivos_internos.py <arquivo>", file=sys.stderr)
        return 2

    achados = []
    for rotulo, texto in trechos_do_arquivo(sys.argv[1]):
        for padrao, motivo in PADROES:
            for m in padrao.finditer(texto):
                ini = max(0, m.start() - 45)
                fim = min(len(texto), m.end() + 45)
                ctx = texto[ini:fim].replace("\t", " ").replace("\n", " ")
                achados.append((rotulo, m.group(0), motivo, ctx.strip()))

    if not achados:
        print("OK: nenhuma referencia a arquivo/pasta interna no texto do auto.")
        return 0

    print("REPROVADO: %d referencia(s) ao ambiente de trabalho dentro do auto." % len(achados))
    print("O auto e documento legal entregue ao autuado: arquivo interno nao e")
    print("elemento de conviccao e nao vai anexo. Descreva a PROVA, nao o arquivo.")
    print("Ex.: em vez de 'ver relato em inspecao-fisica.md', escreva apenas")
    print("'Inspecao fisica realizada em dd/mm/aaaa no setor X do estabelecimento'.")
    print("")
    for rotulo, achado, motivo, ctx in achados[:40]:
        print("  [%s] '%s' (%s)" % (rotulo, achado, motivo))
        print("      ...%s..." % ctx)
    if len(achados) > 40:
        print("  ... e mais %d ocorrencia(s)." % (len(achados) - 40))
    return 1


if __name__ == "__main__":
    sys.exit(main())
