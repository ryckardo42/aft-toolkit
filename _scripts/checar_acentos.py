#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
checar_acentos.py — detector de texto pt-br sem acentuação em minutas de auto.

Motivação: o encoding final do TXT do Sistema Auditor (ISO-8859-1 / latin-1)
SUPORTA todos os acentos do português (ç ã õ á é í ó ú â ê ô à). O que o latin-1
NAO aceita e travessao (—), aspas curvas e emojis. Ainda assim, é fácil um texto
sair "chapado" (sem acento) por engano na redação — e isso é uma falha de qualidade
do auto, não uma exigência de encoding. Este script pega esse defeito de forma
determinística, antes do empacotamento.

Estratégia (alta precisão, quase zero falso-positivo): procura ocorrências, como
PALAVRA INTEIRA, de formas ASCII (sem acento) de palavras portuguesas que
praticamente NUNCA são grafadas sem acento. Em um texto corretamente acentuado,
essas formas simplesmente não aparecem (a versão certa contém ç/ã/á/... e não casa
com a busca ASCII). Se aparecem, o texto perdeu acento.

Só entram na lista formas cuja versão sem acento não é, ela mesma, uma palavra
portuguesa válida (evita falso-positivo). Por isso NÃO estão aqui casos ambíguos
como "para/pára", "e/é", "esta/está", "so/só", "as/às".

Uso:
    python checar_acentos.py "<arquivo.md>"
Saída: lista de achados com nº da linha; exit 0 se limpo, 1 se encontrou defeito.
"""
import sys
import re

# Formas ASCII (sem acento) que, como palavra inteira, denunciam perda de acento.
# Mantida conservadora: cada entrada é inequívoca em pt-br.
MARCADORES = [
    # advérbio/negação e verbos muito frequentes
    "nao", "sao", "esta_ignore",  # 'esta' é ambíguo -> removido logo abaixo
    "voce", "ha_ignore",
    # substantivos/adjetivos em -ção, -são, -ncia, etc.
    "organizacao", "comunicacao", "protecao", "inspecao", "avaliacao",
    "producao", "acao", "acoes", "infracao", "infracoes", "identificacao",
    "situacao", "gradacao", "classificacao", "descricao", "informacao",
    "informacoes", "implantacao", "documentacao", "atualizacao", "aplicacao",
    "constatacao", "elaboracao", "notificacao", "capitulacao", "individualizacao",
    "caracterizacao", "exposicao", "manutencao", "prevencao", "refrigeracao",
    "deteccao", "condicao", "condicoes", "observacao", "observacoes",
    "ocorrencia", "ocorrencias", "consequencia", "frequencia", "referencia",
    "emergencia", "existencia", "advertencia", "eficiencia",
    # substantivos/adjetivos com acento gráfico
    "analise", "analises", "maquina", "maquinas", "pagina", "paginas",
    "area", "areas", "nivel", "niveis", "criterio", "criterios", "periodo",
    "periodos", "seguranca", "amonia", "quimico", "quimicos", "quimica",
    "fisico", "fisicos", "fisica", "mecanico", "mecanicos", "mecanica",
    "ergonomico", "ergonomicos", "ergonomica", "biologico", "biologicos",
    "unico", "unica", "unicos", "especifico", "especificos", "especifica",
    "tecnico", "tecnica", "tecnicos", "proprio", "propria", "proximo",
    "obrigatorio", "obrigatoria", "alinea", "alineas", "responsavel",
    "responsaveis", "cambara_ignore", "camara", "camaras", "electrico_ignore",
    "eletrico", "eletrica", "eletricos", "explosao", "corrosao", "reducao",
    "distancia", "vitima", "vitimas", "obitos", "obito", "saude", "tambem",
    "porem", "alem", "atraves", "apos", "ja_ignore",
]
# remove sentinelas ambíguas
MARCADORES = [m for m in MARCADORES if not m.endswith("_ignore")]
MARCADORES = sorted(set(MARCADORES), key=len, reverse=True)

PADRAO = re.compile(r"(?<![0-9A-Za-zÀ-ÿ])(" + "|".join(MARCADORES) + r")(?![0-9A-Za-zÀ-ÿ])",
                    re.IGNORECASE)


def main():
    if len(sys.argv) < 2:
        print("uso: python checar_acentos.py <arquivo>", file=sys.stderr)
        return 2
    caminho = sys.argv[1]
    try:
        texto = open(caminho, encoding="utf-8").read()
    except UnicodeDecodeError:
        texto = open(caminho, encoding="latin-1").read()

    achados = []
    for i, linha in enumerate(texto.splitlines(), 1):
        # ignora a linha de OBSERVAÇÕES já injetada com marcadores #13#10 (boilerplate)
        for m in PADRAO.finditer(linha):
            token = m.group(1)
            ini = max(0, m.start() - 30)
            fim = min(len(linha), m.end() + 30)
            trecho = linha[ini:fim].replace("\t", " ")
            achados.append((i, token, trecho))

    if not achados:
        print("OK: nenhum indicio de texto sem acentuacao pt-br.")
        return 0

    print("REPROVADO: %d ocorrencia(s) de palavra pt-br sem acento "
          "(o latin-1 aceita acentos; corrija a grafia):" % len(achados))
    # agrupa por token para leitura
    for ln, tok, trecho in achados[:60]:
        print("  linha %-4d  '%s'  ...%s..." % (ln, tok, trecho.strip()))
    if len(achados) > 60:
        print("  ... e mais %d ocorrencia(s)." % (len(achados) - 60))
    return 1


if __name__ == "__main__":
    sys.exit(main())
