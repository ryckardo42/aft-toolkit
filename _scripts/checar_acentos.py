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

Duas redes complementam a lista, pelo mesmo critério de inequivocidade:

  TERMINAÇÃO — nenhuma palavra portuguesa correta termina em "-cao", "-coes",
  "-oes", "-avel" ou "-ivel" sem acento. Isso alcança vocabulário que nenhuma
  lista teria ("exequivel", "manutencoes") sem precisar prevê-lo um a um.

  RAZÃO SOCIAL — ela é registrada na Receita Federal SEM acento e vai ao auto
  como consta do cadastro, de modo que a conferência de acentuação a ignora.
  Sem isso o script reprovava um auto CORRETO sempre que a autuada se chamasse
  "... PRODUCAO ...", "... MANUTENCAO ..." ou "... SEGURANCA ...", palavras que
  já estavam na lista e são comuns em nome de empresa.

Uso:
    python checar_acentos.py "<arquivo.md>"
Saída: lista de achados com nº da linha; exit 0 se limpo, 1 se encontrou defeito.
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
    "aderencia", "abrangencia", "incidencia", "reincidencia", "competencia",
    "insalubridade_ignore", "periculosidade_ignore", "transferencia",
    "permanencia", "urgencia", "ausencia", "presencia_ignore", "clemencia",
    "tolerancia", "vigilancia", "importancia", "distancia_ignore",
    "circunstancia", "circunstancias", "instancia", "relevancia",
    # substantivos/adjetivos com acento gráfico
    #
    # "analise" saiu da lista: é forma verbal legítima ("a análise que ele
    # analise depois"), e reprovava texto correto. Mesmo motivo de "calculo"
    # (eu calculo), "numero" (eu numero) e "vinculo" (eu vinculo), que também
    # não entram. É o critério que o cabeçalho já declara — só entra a forma
    # cuja versão sem acento NÃO é, ela mesma, palavra portuguesa válida.
    "analise_ignore", "analises_ignore",
    "maquina", "maquinas", "pagina", "paginas",
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
    # Vocabulario de SST e de inspecao colhido em fiscalizacao real
    # (25/08/2026). Ficaram de fora as formas ja cobertas pela rede por
    # terminacao acima, para nao repetir, e as que tem homografo verbal:
    # "ultima" (ele ultima), "medica" e "medico" (eu medico).
    "admissao", "automatica", "automatico", "biologica", "carcaca",
    "carcacas", "codigo", "eletricas", "hidraulica", "hidraulico",
    "higienica", "higienico", "indicio", "indicios", "maxima", "maximo",
    "minima", "minimo", "moveis", "movel", "necessaria", "necessario",
    "orgao", "orgaos", "periodica", "periodico", "pneumatica", "pneumatico",
    "residuo", "residuos", "ruido", "ruidos", "sanitaria", "sanitario",
    "sanitarios", "servico", "servicos", "ultimo", "uteis", "util", "veiculo",
    "veiculos",
]
# remove sentinelas ambíguas
MARCADORES = [m for m in MARCADORES if not m.endswith("_ignore")]
MARCADORES = sorted(set(MARCADORES), key=len, reverse=True)

PADRAO = re.compile(r"(?<![0-9A-Za-zÀ-ÿ])(" + "|".join(MARCADORES) + r")(?![0-9A-Za-zÀ-ÿ])",
                    re.IGNORECASE)

# Rede por TERMINAÇÃO, complementar à lista acima. Em português não existe
# palavra correta terminada assim SEM acento: toda palavra com estas
# terminações leva acento. Isso alcança vocabulário que nenhuma lista teria —
# "aderencia", "exequivel", "manutencoes" — sem precisar prevê-lo um a um.
#
# Ficaram DE FORA, de propósito, as terminações que produziriam falso-positivo
# em texto bem escrito: "-orio/-oria" (auditoria, categoria, maioria são
# corretas sem acento), "-ario/-aria" (padaria, maquinaria) e "-ico" (rico).
# Guarda que reprova texto correto é desligada por quem a usa, e aí deixa de
# proteger de tudo — mesmo critério da lista acima, que já exclui os ambíguos.
#
# Duas outras ficaram de fora depois de reprovarem texto CORRETO no teste desta
# mudança, contra os autos reais de fiscalizações já encerradas:
#   "-aes"   pegaria SOBRENOME grafado corretamente sem acento (há vários, e um
#            deles apareceu no corpo de um auto real durante este teste);
#   "-encia" e "-ancia" têm homógrafo VERBAL — em "o que evidencia que...",
#            "evidencia" é verbo e está certo sem acento, como "influencia",
#            "diferencia" e "presencia". Os substantivos úteis dessa família
#            entraram na lista MARCADORES acima, um a um, que é onde o critério
#            de inequivocidade pode ser aplicado palavra por palavra.
SUFIXOS = re.compile(
    r"(?<![0-9A-Za-zÀ-ÿ])(\w{2,}(?:cao|coes|oes|avel|aveis|ivel|iveis))"
    r"(?![0-9A-Za-zÀ-ÿ])", re.IGNORECASE)

# Identificador em CamelCase não é prosa: é nome de pasta, de arquivo ou de
# variável, e ali a grafia sem acento é a correta. Sem esta exclusão a rede por
# terminação reprova o caminho "C:\SistemasAFT\...\AutosDeInfracao\PRO" citado
# no corpo de um relatório — outro caso apanhado no teste desta mudança.
CAMELCASE = re.compile(r"^.[a-zà-ÿ]*[A-ZÀ-Ü]")

# RAZÃO SOCIAL. Ela é registrada na Receita Federal SEM acento e tem de ser
# escrita no auto exatamente como consta do cadastro — grafá-la "MÓVEIS" seria
# divergir do registro, e o art. 8º da Portaria MTP nº 667/2021 não admite
# corrigir o sujeito passivo depois. Nos documentos ela aparece como sequência
# de palavras em CAIXA ALTA.
#
# Sem esta máscara o script REPROVA HOJE um auto correto sempre que a autuada
# se chama "... PRODUCAO ...", "... PROTECAO ...", "... MANUTENCAO ...",
# "... REFRIGERACAO ..." ou "... SEGURANCA ..." — todas na lista acima, e todas
# comuns em razão social brasileira. Foi assim que o defeito apareceu: numa
# fiscalização real, a razão social da autuada terminava em "DECORACOES".
# O "E" e o "&" entram como CONECTOR de uma letra so. Sem isso, uma razao social
# que comece imediatamente antes do conector -- "MOVEIS E DECORACOES LTDA" -- tinha
# a primeira palavra deixada de fora da mascara, e "MOVEIS" caia na lista de
# palavras sem acento. Achado em 27/08/2026, no teste que consolidou esta guarda
# com a do metodo: o nome COMPLETO da autuada passava (a corrida comeca antes e
# cobre tudo), e so o nome comecado no conector falhava -- falso positivo raro e
# por isso mais dificil de achar. Continua exigindo ao menos uma palavra de 2+
# letras na corrida: letra solta no meio de prosa nao vira mascara.
CAIXA_ALTA = re.compile(
    r"(?<![0-9A-Za-zÀ-ÿ])[A-ZÀ-ÜÇ][A-ZÀ-ÜÇ0-9&./\-]*"
    r"(?:\s+(?:[A-ZÀ-ÜÇ0-9&./\-]{2,}|E|&))*"
    r"\s+[A-ZÀ-ÜÇ0-9&./\-]{2,}"
    r"(?:\s+(?:[A-ZÀ-ÜÇ0-9&./\-]{2,}|E|&))*(?![0-9A-Za-zÀ-ÿ])")


# Trecho entre crases e LITERAL, nao prosa: caminho de arquivo, nome de pasta,
# comando. A convencao do toolkit escreve todos assim, e varios sao legitimamente
# sem acento porque a pasta se chama exatamente assim no disco --
# `interdicao-embargo/`, `caderno-constatacoes.md`, `NOTIFICACOES/`. Acusa-los
# ensina a ignorar a saida da guarda, que e o pior efeito possivel num
# verificador (a mesma licao dos alarmes falsos ja corrigidos no metodo).
CODIGO = re.compile(r"`[^`]*`")

# Trecho que e CAMINHO ou NOME DE ARQUIVO: tem barra entre palavras, ou termina em
# extensao conhecida. Deliberadamente estreito -- nao basta ser palavra sem acento,
# tem de parecer caminho de verdade.
#
# PORTADO do checar_texto_oficial.py (27/08/2026), que ja resolvia isto e por isso
# ACEITAVA um texto que este script REPROVAVA: duas guardas de acentuacao dando
# vereditos opostos sobre a mesma frase. Guarda que reprova o documento correto e
# desligada por quem a usa, e ai deixa de proteger de tudo.
CAMINHO = re.compile(
    r"(?:[A-Za-zÀ-ÿ0-9_.\-]+[\\/])+[A-Za-zÀ-ÿ0-9_.\-]*"
    r"|\b[A-Za-zÀ-ÿ0-9_\-]+\.(?:md|py|docx|pdf|json|txt|csv|xlsx|html|zip)\b")


def mascarar_nomes_proprios(linha):
    """Troca por espaços o que não é prosa, preservando as colunas.

    Duas classes saem da conferência: sequências em CAIXA ALTA (razão social, que
    vai no auto sem acento, como consta do cadastro da RFB) e trechos entre crases
    (caminho, nome de arquivo, comando -- literais do disco).

    Preservar o comprimento importa: o número da coluna continua valendo para o
    trecho de contexto que o relatório imprime.
    """
    linha = CODIGO.sub(lambda m: " " * len(m.group(0)), linha)
    linha = CAMINHO.sub(lambda m: " " * len(m.group(0)), linha)
    return CAIXA_ALTA.sub(lambda m: " " * len(m.group(0)), linha)


def main():
    # -h/--help responde com o proprio docstring. Antes, "--help" era tratado
    # como caminho de arquivo: o script levantava FileNotFoundError e o
    # mecanismo de ticket registrava isso como DEFEITO DO TOOLKIT -- um relato
    # de bug gerado por alguem perguntando como usar a ferramenta.
    if any(a in ("-h", "--help") for a in sys.argv[1:]):
        print(__doc__ or "uso: python checar_acentos.py <arquivo>")
        return 0
    if len(sys.argv) < 2:
        print("uso: python checar_acentos.py <arquivo>", file=sys.stderr)
        return 2
    caminho = sys.argv[1]
    try:
        texto = open(caminho, encoding="utf-8").read()
    except UnicodeDecodeError:
        texto = open(caminho, encoding="latin-1").read()

    # FRONT-MATTER (--- ... ---) e CONFIGURACAO, nao prosa: os valores sao enums
    # da API de destino, escritos sem acento de proposito ("tipo: obrigacao", que o
    # det_criar.py documenta como "solicitacao | obrigacao | orientacao"), e os
    # comentarios ali sao anotacao de trabalho do AFT. Acusa-los reprovava TODA
    # notificacao real -- a do acervo dava 9 ocorrencias, nenhuma delas erro de
    # grafia. Guarda que reprova o documento correto ensina a ignorar a guarda.
    # As linhas continuam contando: o numero de linha do relatorio segue valendo.
    linhas = texto.splitlines()
    if linhas and linhas[0].strip() == "---":
        for k in range(1, len(linhas)):
            if linhas[k].strip() == "---":
                for j in range(0, k + 1):
                    linhas[j] = " " * len(linhas[j])
                break

    achados = []
    for i, linha in enumerate(linhas, 1):
        # A razão social vai no auto sem acento, como consta do cadastro da RFB:
        # ela sai da conferência, e só ela. O resto da linha continua valendo.
        conferivel = mascarar_nomes_proprios(linha)
        # ignora a linha de OBSERVAÇÕES já injetada com marcadores #13#10 (boilerplate)
        vistos = set()
        for padrao in (PADRAO, SUFIXOS):
            for m in padrao.finditer(conferivel):
                token = m.group(1)
                if m.start() in vistos:      # a lista e a terminação podem casar
                    continue                 # a mesma palavra; conta uma vez só
                if padrao is SUFIXOS and CAMELCASE.match(token):
                    continue                 # identificador, não prosa
                vistos.add(m.start())
                ini = max(0, m.start() - 30)
                fim = min(len(linha), m.end() + 30)
                trecho = linha[ini:fim].replace("\t", " ")
                achados.append((i, token, trecho))
    achados.sort(key=lambda a: a[0])

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
