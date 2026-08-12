#!/usr/bin/env python3
"""
montar_rt.py - monta o Relatorio Tecnico de Interdicao/Embargo (.docx) a partir
do template oficial do toolkit e de um arquivo JSON com os campos.

O template traz placeholders no formato {{chave}} (ver "Dicionario de campos" na
skill /aft-embargo-interdicao). O script substitui cada chave pelo valor, repete os blocos
que se repetem (objetos e fatores de risco), monta as listas reais do Word
(medidas e documentos) e preserva TODO o texto fixo - itens 1, 2 e 8, a
metodologia da NR-3 e as Tabelas 3.1/3.2/3.3 sao juridicamente vinculados.

Dois FORMATOS de RT (campo "formato" do JSON):
  - "topico" (padrao): o layout do template - secoes 4 a 7 tematicas
    (irregularidades, fatores de risco, medidas, documentos), cada uma cobrindo
    todos os objetos de uma vez;
  - "objeto": as secoes 4 a 7 deixam de existir como secoes; cada objeto da
    secao 3 ganha seus proprios sub-blocos (Irregularidade(s), Fator(es) de
    Risco, Medida(s) de Protecao, Documento(s) Solicitado(s)). O bloco fixo da
    metodologia da NR-3 (com as Tabelas 3.1/3.2/3.3) migra para o fim da
    secao 2, antes da lista de objetos; a alinea fixa "Requerimento expresso..."
    do item 6 e dispensada (a exigencia ja consta do item fixo DO PEDIDO DE
    SUSPENSAO, incisos I a III); e a CONCLUSAO renumera sozinha para o item 4
    (a numeracao dos titulos e automatica no Word).

Pontos que ele resolve sozinho:
  - placeholder partido entre runs (o Word quebra {{chave}} em varios pedacos ao
    editar): a substituicao e feita no nivel dos runs, preservando a formatacao;
  - numeracao automatica: medidas e documentos entram como itens de LISTA do
    Word, sem "A)"/"B)" digitados. A alinea fixa "Requerimento expresso..."
    continua sendo o ultimo item do item 6;
  - o item 7 recebe uma lista propria, que reinicia em A);
  - modo "embargo": troca o texto fixo que fala em interdicao (NR-03, 3.2.2.1:
    embargo e para OBRA; 3.2.2.2: interdicao e para maquina/setor/atividade);
  - valida ao final que nenhum {{...}} sobrou no documento.

Uso:
    python montar_rt.py "<dados.json>" "<saida.docx>"

O JSON deve ser gravado com a tool Write (nunca digitado no comando: acentos
viram lixo quando interpolados na linha de comando do Windows). Formato:

{
  "modo": "interdicao" | "embargo",
  "formato": "topico" | "objeto",       // opcional; ausente = "topico"
  "numero_termo": "0012345-6",
  "empregador": "RAZAO SOCIAL LTDA",
  "cnpj": "00.000.000/0000-00",

  "objetos": [
    {"numero_objeto": "1", "tipo_objeto": "MAQUINA",
     "tipo_paralisacao": "TOTAL", "objetos": "descricao do objeto..."}
  ],

  "irregularidades": ["paragrafo 1", "paragrafo 2"],

  "fatores_risco": [
    {"fator_de_risco": "Queda de altura - excesso de risco: Extremo (E)",
     "descricao": "...",
     "fundamentacao_risco_atual": "...",
     "fundamentacao_risco_referencia": "..."}
  ],

  "medidas_protecao": ["medida 1", "medida 2"],
  "documentos_solicitados": ["documento 1", "documento 2"],

  "conclusao": "texto da conclusao/observacao",   // opcional nos dois formatos

  "cidade": "Goiania", "uf": "GO", "data": "29/07/2026",
  "auditor_fiscal": "NOME DO AUDITOR"
}

No formato "objeto", as quatro listas (irregularidades, fatores_risco,
medidas_protecao, documentos_solicitados) saem do nivel de cima e entram DENTRO
de cada objeto:

  "objetos": [
    {"numero_objeto": "1", "tipo_objeto": "MAQUINA",
     "tipo_paralisacao": "TOTAL", "objetos": "descricao...",
     "irregularidades": ["..."],
     "fatores_risco": [{"fator_de_risco": "...", "descricao": "...",
                        "fundamentacao_risco_atual": "...",
                        "fundamentacao_risco_referencia": "..."}],
     "medidas_protecao": ["..."],
     "documentos_solicitados": ["..."]}
  ]

Nao digite "A)", "B)", "3." nem marcadores (-, *) nos textos: a numeracao e
automatica no Word. Depois de montar, use o inserir_foto_docx.py para as fotos.

Exit 0 = documento gerado; 2 = erro de uso/dados; 3 = template incompativel.
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

import json
import random
import re
import shutil
import subprocess
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

AQUI = Path(__file__).resolve().parent
TEMPLATE = AQUI.parent / "aft-embargo-interdicao" / "template.docx"

try:  # cabecalho com a lotacao do AFT (ver _scripts/cabecalho.py)
    from cabecalho import template_personalizado
except Exception:  # sem ele o RT sai com o cabecalho neutro do template
    def template_personalizado(caminho, lotacao=None):
        return str(caminho)

RE_PARAGRAFO = re.compile(r"<w:p\b[^>]*>.*?</w:p>|<w:p\b[^>]*/>", re.S)
RE_TEXTO = re.compile(r"(<w:t\b[^>]*>)(.*?)(</w:t>)", re.S)
RE_CHAVE = re.compile(r"\{\{\s*([A-Za-z0-9_-]+)\s*\}\}")

# Blocos que se repetem: as chaves que os definem, na ordem do template.
BLOCO_OBJETOS = ("numero_objeto", "tipo_objeto", "tipo_paralisacao", "objetos")
BLOCO_FATORES = ("fator_de_risco", "descricao",
                 "fundamentacao_risco_atual", "fundamentacao_risco_referencia")

# Campos simples da capa e do fecho.
SIMPLES = ("numero_termo", "empregador", "cnpj", "Contexto-da-inspecao-fisica",
           "cidade", "uf", "data", "auditor_fiscal")

# Listas reais do Word.
NUMID_MEDIDAS = "19"    # lista ja existente: a alinea fixa "Requerimento" e o ultimo item
NUMID_DOCUMENTOS = "20"  # criada por este script, reiniciando em A)
NUMID_BULLET = "21"      # criada por este script: marcadores das ementas do item 4
ABSTRACT_BULLET = "19"   # abstractNum do marcador (criado junto com o numId 21)

# Padrao do corpo do RT, copiado dos paragrafos fixos do template.
ESPACAMENTO_CORPO = '<w:spacing w:line="360" w:lineRule="auto"/>'
RECUO_CORPO = '<w:ind w:left="112" w:firstLine="708"/>'

# Ordem em que os filhos de <w:pPr> devem aparecer (exigencia do schema OOXML:
# fora de ordem, o Word acusa documento corrompido).
ORDEM_PPR = ("pStyle", "numPr", "tabs", "adjustRightInd", "spacing", "ind", "jc", "rPr")
ABSTRACT_LETRAS = "1"    # abstractNum da lista A) B) C) (upperLetter, "%1)")

OBRIGATORIOS = ("modo", "numero_termo", "empregador", "cnpj",
                "Contexto-da-inspecao-fisica", "objetos",
                "cidade", "uf", "data", "auditor_fiscal")

# As quatro listas de conteudo: no formato "topico" ficam no nivel de cima do
# JSON; no formato "objeto" entram dentro de cada objeto.
LISTAS_CONTEUDO = ("irregularidades", "fatores_risco",
                   "medidas_protecao", "documentos_solicitados")

# numPr que DESLIGA a numeracao herdada do estilo (usado nos rotulos que o
# formato "objeto" clona dos titulos de secao).
NUMPR_DESLIGADO = '<w:numPr><w:ilvl w:val="0"/><w:numId w:val="0"/></w:numPr>'

# Trocas do modo embargo: o template e redigido para interdicao.
TROCAS_EMBARGO = (
    ("TERMO DE INTERDIÇÃO", "TERMO DE EMBARGO"),
    ("OBJETO(S) INTERDITADO(S):", "OBJETO(S) EMBARGADO(S):"),
    ("objetos interditados citados no Termo de Interdição anexo",
     "objetos embargados citados no Termo de Embargo anexo"),
    ("DO PEDIDO DE SUSPENSÃO DA INTERDIÇÃO", "DO PEDIDO DE SUSPENSÃO DO EMBARGO"),
    ("suspensão da interdição", "suspensão do embargo"),
    ("I - o número do Termo de Interdição;", "I - o número do Termo de Embargo;"),
    ("II - a identificação da(s) máquina(s) ou setor de serviço;",
     "II - a identificação da obra ou da frente de trabalho;"),
)


def erro(msg, codigo=2):
    print(f"ERRO: {msg}", file=sys.stderr)
    sys.exit(codigo)


def novo_paraid():
    """paraId valido: hex de 8 digitos < 0x80000000 (valor maior quebra o DOCX)."""
    return f"{random.randint(1, 0x7FFFFFFE):08X}"


def esc(t):
    return str(t).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# --------------------------------------------------------------------------
# Substituicao de {{chave}} respeitando os runs
# --------------------------------------------------------------------------

def texto_do_paragrafo(p):
    return "".join(m.group(2) for m in RE_TEXTO.finditer(p))


def fonte_do_corpo(xml):
    """Descobre a fonte do corpo olhando os placeholders que a declaram.

    O estilo Normal do template e Verdana; o corpo do RT so fica em Tahoma
    porque cada run traz um <w:rFonts> proprio. Placeholder sem esse override
    sai na fonte errada - por isso o script detecta a fonte dominante e a
    aplica nos paragrafos que gera.
    """
    fontes = {}
    for m in RE_PARAGRAFO.finditer(xml):
        p = m.group(0)
        if "{{" not in texto_do_paragrafo(p):
            continue
        for f in re.findall(r'<w:rFonts[^>]*w:ascii="([^"]+)"', p):
            fontes[f] = fontes.get(f, 0) + 1
    return max(fontes, key=fontes.get) if fontes else None


def garantir_fonte(paragrafo, fonte):
    """Poe <w:rFonts> nos runs que nao declaram fonte propria."""
    if not fonte:
        return paragrafo
    rfonts = (f'<w:rFonts w:ascii="{fonte}" w:eastAsia="{fonte}" '
              f'w:hAnsi="{fonte}" w:cs="{fonte}"/>')

    def conserta(m):
        run = m.group(0)
        if "<w:rFonts" in run or "<w:t" not in run:
            return run
        if "<w:rPr>" in run:
            return run.replace("<w:rPr>", "<w:rPr>" + rfonts, 1)
        return re.sub(r"(<w:r\b[^>]*>)", r"\1<w:rPr>" + rfonts + "</w:rPr>", run, count=1)

    return re.sub(r"<w:r\b[^>]*>.*?</w:r>", conserta, paragrafo, flags=re.S)


def remover_desenhos(paragrafo):
    """Tira do paragrafo os runs que carregam imagem (<w:drawing>/<w:pict>).

    Alguns placeholders do template tem uma imagem ANCORADA no mesmo paragrafo
    (o Word prende a figura a um paragrafo qualquer e a posiciona na pagina).
    Ao repetir esse paragrafo para N itens, a imagem seria duplicada N vezes -
    por isso ela e mantida so na primeira copia.
    """
    return re.sub(r"<w:r\b[^>]*>(?:(?!</w:r>).)*?(?:<w:drawing>|<w:pict>).*?</w:r>",
                  "", paragrafo, flags=re.S)


def ajustar_ppr(paragrafo, jc=None, spacing=None, ind=None, numpr=None,
                sem_ind=False, sem_numpr=False):
    """Reescreve o <w:pPr> do paragrafo mantendo a ordem exigida pelo schema."""
    m = re.search(r"<w:pPr>(.*?)</w:pPr>", paragrafo, re.S)
    conteudo = m.group(1) if m else ""

    def pega(tag):
        mm = re.search(r"<w:%s\b[^>]*(?:/>|>.*?</w:%s>)" % (tag, tag), conteudo, re.S)
        return mm.group(0) if mm else None

    atual = {t: pega(t) for t in ORDEM_PPR}
    if jc is not None:
        atual["jc"] = '<w:jc w:val="%s"/>' % jc
    if spacing is not None:
        atual["spacing"] = spacing
    if ind is not None:
        atual["ind"] = ind
    if sem_ind:
        atual["ind"] = None
    if numpr is not None:
        atual["numPr"] = numpr
    if sem_numpr:
        atual["numPr"] = None

    novo = "<w:pPr>" + "".join(atual[t] for t in ORDEM_PPR if atual[t]) + "</w:pPr>"
    if m:
        return paragrafo[:m.start()] + novo + paragrafo[m.end():]
    return re.sub(r"(<w:p\b[^>]*>)", lambda x: x.group(1) + novo, paragrafo, count=1)


def por_paragrafo(bloco, fn):
    """Aplica `fn` a cada <w:p> do bloco (ajustar_ppr so enxerga o primeiro)."""
    saida, ultimo = [], 0
    for m in RE_PARAGRAFO.finditer(bloco):
        saida.append(bloco[ultimo:m.start()])
        saida.append(fn(m.group(0)))
        ultimo = m.end()
    saida.append(bloco[ultimo:])
    return "".join(saida)


def como_corpo(paragrafo, recuo=False):
    """Deixa o paragrafo no padrao do corpo do RT: justificado e entrelinha 1,5."""
    return ajustar_ppr(paragrafo, jc="both", spacing=ESPACAMENTO_CORPO,
                       ind=RECUO_CORPO if recuo else None)


def substituir_no_paragrafo(p, valores):
    """Troca {{chave}} pelos valores dentro de UM paragrafo.

    O Word costuma partir "{{chave}}" em varios <w:t>. A substituicao percorre os
    runs, monta o texto completo, localiza a chave e devolve o valor ao run onde
    ela COMECA - assim o valor herda a formatacao do proprio placeholder e o
    resto do paragrafo (rotulos em negrito, por exemplo) fica intacto.
    """
    runs = list(RE_TEXTO.finditer(p))
    if not runs:
        return p
    textos = [m.group(2) for m in runs]
    # posicao inicial de cada run no texto concatenado
    inicios, acc = [], 0
    for t in textos:
        inicios.append(acc)
        acc += len(t)
    inteiro = "".join(textos)

    ocorrencias = list(RE_CHAVE.finditer(inteiro))
    if not ocorrencias:
        return p

    novos = list(textos)
    for oc in reversed(ocorrencias):          # de tras para frente: indices estaveis
        chave = oc.group(1)
        if chave not in valores:
            continue
        ini, fim = oc.start(), oc.end()
        valor = esc(str(valores[chave]))
        for i, t in enumerate(textos):
            r_ini, r_fim = inicios[i], inicios[i] + len(t)
            if r_fim <= ini or r_ini >= fim:
                continue                       # run fora da chave
            corta_ini = max(ini, r_ini) - r_ini
            corta_fim = min(fim, r_fim) - r_ini
            reposicao = valor if r_ini <= ini < r_fim else ""
            novos[i] = novos[i][:corta_ini] + reposicao + novos[i][corta_fim:]

    partes, ultimo = [], 0
    for m, texto in zip(runs, novos):
        abre = m.group(1)
        if 'xml:space' not in abre:
            abre = abre[:-1] + ' xml:space="preserve">'
        partes.append(p[ultimo:m.start()] + abre + texto + m.group(3))
        ultimo = m.end()
    partes.append(p[ultimo:])
    return "".join(partes)


def substituir_tudo(xml, valores):
    saida, ultimo = [], 0
    for m in RE_PARAGRAFO.finditer(xml):
        saida.append(xml[ultimo:m.start()])
        saida.append(substituir_no_paragrafo(m.group(0), valores))
        ultimo = m.end()
    saida.append(xml[ultimo:])
    return "".join(saida)


# --------------------------------------------------------------------------
# Localizacao e repeticao de blocos
# --------------------------------------------------------------------------

def paragrafos_com_chave(xml, chave):
    alvo = "{{%s}}" % chave
    achados = []
    for m in RE_PARAGRAFO.finditer(xml):
        if alvo in re.sub(r"<[^>]+>", "", m.group(0)) or alvo in texto_do_paragrafo(m.group(0)):
            achados.append(m)
    return achados


def _span_do_bloco(xml, chaves):
    ini = fim = None
    for chave in chaves:
        achados = paragrafos_com_chave(xml, chave)
        if not achados:
            erro(f"placeholder {{{{{chave}}}}} nao encontrado no template. "
                 f"Confira {TEMPLATE}", 3)
        for m in achados:
            ini = m.start() if ini is None else min(ini, m.start())
            fim = m.end() if fim is None else max(fim, m.end())
    return ini, fim


def repetir_bloco(xml, chaves, itens, rotulo, fonte=None, formatar=None):
    """Repete o bloco de paragrafos que contem `chaves`, um por item."""
    ini, fim = _span_do_bloco(xml, chaves)
    molde = xml[ini:fim]
    blocos = []
    for i, item in enumerate(itens, 1):
        faltando = [c for c in chaves if c not in item]
        if faltando:
            erro(f"{rotulo} #{i}: faltam os campos {', '.join(faltando)}")
        copia = substituir_no_bloco(molde, item)
        if i > 1:
            copia = remover_desenhos(copia)
        if formatar:
            copia = por_paragrafo(copia, formatar)
        copia = garantir_fonte(copia, fonte)
        copia = re.sub(r'w14:paraId="[0-9A-Fa-f]+"',
                       lambda _: f'w14:paraId="{novo_paraid()}"', copia)
        blocos.append(copia)
    return xml[:ini] + "".join(blocos) + xml[fim:]


def substituir_no_bloco(bloco, valores):
    saida, ultimo = [], 0
    for m in RE_PARAGRAFO.finditer(bloco):
        saida.append(bloco[ultimo:m.start()])
        saida.append(substituir_no_paragrafo(m.group(0), valores))
        ultimo = m.end()
    saida.append(bloco[ultimo:])
    return "".join(saida)


def expandir_paragrafos(xml, chave, textos, fonte=None, formatar=None):
    """Troca o paragrafo de um placeholder solitario por N paragrafos iguais."""
    achados = paragrafos_com_chave(xml, chave)
    if not achados:
        erro(f"placeholder {{{{{chave}}}}} nao encontrado no template. "
             f"Confira {TEMPLATE}", 3)
    m = achados[0]
    copias = []
    for i, t in enumerate(textos):
        copia = substituir_no_paragrafo(m.group(0), {chave: t})
        if i:                       # imagem ancorada fica so na primeira copia
            copia = remover_desenhos(copia)
        if formatar:
            copia = formatar(copia)
        copia = garantir_fonte(copia, fonte)
        copia = re.sub(r'w14:paraId="[0-9A-Fa-f]+"',
                       lambda _: f'w14:paraId="{novo_paraid()}"', copia)
        copias.append(copia)
    return xml[:m.start()] + "".join(copias) + xml[m.end():]


def virar_lista(paragrafo, numid):
    """Devolve o paragrafo como item de lista real do Word (numeracao automatica),
    ja no padrao do corpo: justificado e entrelinha 1,5. O recuo vem da lista."""
    numpr = '<w:numPr><w:ilvl w:val="0"/><w:numId w:val="%s"/></w:numPr>' % numid
    return ajustar_ppr(paragrafo, jc="both", spacing=ESPACAMENTO_CORPO,
                       numpr=numpr, sem_ind=True)


def expandir_lista(xml, chave, textos, numid, fonte=None):
    achados = paragrafos_com_chave(xml, chave)
    if not achados:
        erro(f"placeholder {{{{{chave}}}}} nao encontrado no template. "
             f"Confira {TEMPLATE}", 3)
    m = achados[0]
    copias = []
    for i, t in enumerate(textos):
        copia = substituir_no_paragrafo(m.group(0), {chave: t})
        if i:
            copia = remover_desenhos(copia)
        copia = garantir_fonte(copia, fonte)
        copia = virar_lista(copia, numid)
        copia = re.sub(r'w14:paraId="[0-9A-Fa-f]+"',
                       lambda _: f'w14:paraId="{novo_paraid()}"', copia)
        copias.append(copia)
    return xml[:m.start()] + "".join(copias) + xml[m.end():]


def garantir_lista_documentos(numbering_xml):
    """Cria o numId do item 7 reaproveitando a lista A) B) C), reiniciando em A)."""
    if f'<w:num w:numId="{NUMID_DOCUMENTOS}"' in numbering_xml:
        return numbering_xml
    novo = (f'<w:num w:numId="{NUMID_DOCUMENTOS}">'
            f'<w:abstractNumId w:val="{ABSTRACT_LETRAS}"/>'
            f'<w:lvlOverride w:ilvl="0"><w:startOverride w:val="1"/></w:lvlOverride>'
            f'</w:num>')
    return numbering_xml.replace("</w:numbering>", novo + "</w:numbering>")


def aplicar_embargo(xml):
    """Troca, no texto fixo, o que fala especificamente em interdicao."""
    for velho, novo in TROCAS_EMBARGO:
        saida, ultimo = [], 0
        for m in RE_PARAGRAFO.finditer(xml):
            p = m.group(0)
            if velho in texto_do_paragrafo(p):
                runs = list(RE_TEXTO.finditer(p))
                inteiro = "".join(r.group(2) for r in runs)
                trocado = inteiro.replace(velho, novo)
                # o paragrafo inteiro passa a caber no primeiro run
                partes, primeiro = [], True
                pos = 0
                for r in runs:
                    abre = r.group(1)
                    if 'xml:space' not in abre:
                        abre = abre[:-1] + ' xml:space="preserve">'
                    conteudo = trocado if primeiro else ""
                    partes.append(p[pos:r.start()] + abre + conteudo + r.group(3))
                    pos = r.end()
                    primeiro = False
                partes.append(p[pos:])
                p = "".join(partes)
            saida.append(xml[ultimo:m.start()])
            saida.append(p)
            ultimo = m.end()
        saida.append(xml[ultimo:])
        xml = "".join(saida)
    return xml


# --------------------------------------------------------------------------

def garantir_lista_bullet(numbering_xml):
    """Cria a lista de MARCADORES usada nas ementas do item 4 (o template nao tem)."""
    if '<w:num w:numId="%s"' % NUMID_BULLET in numbering_xml:
        return numbering_xml
    abstract = (
        '<w:abstractNum w:abstractNumId="%s">'
        '<w:multiLevelType w:val="hybridMultilevel"/>'
        '<w:lvl w:ilvl="0"><w:start w:val="1"/><w:numFmt w:val="bullet"/>'
        '<w:lvlText w:val="&#xF0B7;"/><w:lvlJc w:val="left"/>'
        '<w:pPr><w:ind w:left="720" w:hanging="360"/></w:pPr>'
        '<w:rPr><w:rFonts w:ascii="Symbol" w:hAnsi="Symbol" w:hint="default"/></w:rPr>'
        '</w:lvl></w:abstractNum>' % ABSTRACT_BULLET)
    num = ('<w:num w:numId="%s"><w:abstractNumId w:val="%s"/></w:num>'
           % (NUMID_BULLET, ABSTRACT_BULLET))
    # o abstractNum precisa vir antes dos <w:num>
    primeiro_num = numbering_xml.find("<w:num ")
    if primeiro_num == -1:
        numbering_xml = numbering_xml.replace("</w:numbering>", abstract + "</w:numbering>")
    else:
        numbering_xml = numbering_xml[:primeiro_num] + abstract + numbering_xml[primeiro_num:]
    return numbering_xml.replace("</w:numbering>", num + "</w:numbering>")


def remover_vazio_apos(xml, chave):
    """Tira o paragrafo VAZIO que o template deixa logo depois de um placeholder.

    No item 6 esse paragrafo fica entre as medidas e a alinea fixa
    'Requerimento expresso...', e imprime uma quebra dupla antes do ultimo item.
    """
    achados = paragrafos_com_chave(xml, chave)
    if not achados:
        return xml
    fim = achados[-1].end()
    m = RE_PARAGRAFO.match(xml, fim) or RE_PARAGRAFO.search(xml, fim)
    if not m or m.start() != fim:
        return xml
    if texto_do_paragrafo(m.group(0)).strip() or "<w:drawing>" in m.group(0):
        return xml                      # so remove se estiver realmente vazio
    return xml[:m.start()] + xml[m.end():]


def titulos_de_secao(xml):
    """Localiza os titulos de secao (estilo Ttulo1) por palavra-chave.

    Os titulos nao carregam o numero no texto ("IRREGULARIDADE(S):", sem o
    "4.") - a numeracao vem da lista automatica do Word. Por isso, remover um
    titulo renumera sozinho os seguintes.
    """
    achados = {}
    for m in RE_PARAGRAFO.finditer(xml):
        p = m.group(0)
        if 'w:val="Ttulo1"' not in p:
            continue
        t = texto_do_paragrafo(p).upper()
        if "IRREGULARIDADE" in t:
            achados["irregularidades"] = m
        elif "FATOR" in t and "RELACIONADO" in t:
            achados["fatores"] = m
        elif "MEDIDA" in t:
            achados["medidas"] = m
        elif "DOCUMENTO" in t:
            achados["documentos"] = m
        elif "CONCLUS" in t:
            achados["conclusao"] = m
        elif "OBJETO(S)" in t:
            achados["objetos"] = m
    return achados


def inserir_conclusao(xml, texto, fonte):
    """Poe o texto da conclusao no paragrafo vazio apos o titulo CONCLUSAO.

    O template nao tem placeholder ali - o paragrafo e vazio. O texto entra no
    padrao do corpo (justificado, entrelinha 1,5, recuo de primeira linha).
    """
    tit = titulos_de_secao(xml).get("conclusao")
    if not tit:
        erro("titulo CONCLUSAO/OBSERVACAO nao encontrado no template", 3)
    m = RE_PARAGRAFO.match(xml, tit.end())
    if not m or texto_do_paragrafo(m.group(0)).strip():
        return xml  # sem paragrafo vazio logo apos: nao arrisca sobrescrever
    p = m.group(0)
    t_novo = '<w:t xml:space="preserve">' + esc(texto) + "</w:t>"
    if "</w:r>" in p:
        # o <w:t> entra no fim do run (depois do <w:rPr>, exigencia do schema)
        novo = p.replace("</w:r>", t_novo + "</w:r>", 1)
    elif "</w:p>" in p:
        novo = p.replace("</w:p>", "<w:r>" + t_novo + "</w:r></w:p>")
    else:  # paragrafo autofechado <w:p .../>
        novo = p[:-2].rstrip() + "><w:r>" + t_novo + "</w:r></w:p>"
    novo = como_corpo(novo, recuo=True)
    novo = garantir_fonte(novo, fonte)
    return xml[:m.start()] + novo + xml[m.end():]


def montar_por_objeto(xml, dados, fonte):
    """Formato "objeto": aninha irregularidades, fatores, medidas e documentos
    dentro de cada objeto da secao 3 e remove as secoes tematicas 4 a 7.

    O bloco fixo da metodologia da NR-3 (com as Tabelas 3.1/3.2/3.3), que no
    template vive dentro da secao 4, migra para o fim da secao 2 - ele
    fundamenta a caracterizacao do GIR e precisa vir antes da analise por
    objeto. A alinea fixa "Requerimento expresso..." do item 6 e dispensada
    neste formato: a mesma exigencia ja consta do item fixo DO PEDIDO DE
    SUSPENSAO (incisos I a III).
    """
    titulos = titulos_de_secao(xml)
    faltam = [k for k in ("objetos", "irregularidades", "fatores",
                          "medidas", "documentos", "conclusao") if k not in titulos]
    if faltam:
        erro("titulos de secao nao encontrados no template: " + ", ".join(faltam)
             + f". Confira {TEMPLATE}", 3)
    h3, h4 = titulos["objetos"], titulos["irregularidades"]
    h5, h6 = titulos["fatores"], titulos["medidas"]
    h7, h8 = titulos["documentos"], titulos["conclusao"]

    # moldes (extraidos com os placeholders ainda no lugar)
    obj_ini, obj_fim = _span_do_bloco(xml, BLOCO_OBJETOS)
    molde_obj = xml[obj_ini:obj_fim]

    ps_irr = paragrafos_com_chave(xml, "irregularidades")
    if not ps_irr:
        erro("placeholder {{irregularidades}} nao encontrado no template. "
             f"Confira {TEMPLATE}", 3)
    molde_irr = ps_irr[0].group(0)
    metodologia = xml[ps_irr[0].end():h5.start()]

    sec5 = xml[h5.start():h6.start()]
    f_ini, f_fim = _span_do_bloco(sec5, BLOCO_FATORES)
    molde_fator = sec5[f_ini:f_fim]

    ps_med = paragrafos_com_chave(xml, "medidas_protecao")
    ps_doc = paragrafos_com_chave(xml, "documentos_solicitados")
    for chave, ps in (("medidas_protecao", ps_med), ("documentos_solicitados", ps_doc)):
        if not ps:
            erro(f"placeholder {{{{{chave}}}}} nao encontrado no template. "
                 f"Confira {TEMPLATE}", 3)
    molde_med, molde_doc = ps_med[0].group(0), ps_doc[0].group(0)

    # rotulos dos sub-blocos: o proprio titulo da secao, sem a numeracao
    rotulos = {k: ajustar_ppr(titulos[k].group(0), numpr=NUMPR_DESLIGADO)
               for k in ("irregularidades", "fatores", "medidas", "documentos")}

    def com_paraid(bloco):
        return re.sub(r'w14:paraId="[0-9A-Fa-f]+"',
                      lambda _: f'w14:paraId="{novo_paraid()}"', bloco)

    primeira_copia = set()   # moldes cuja 1a copia mantem a imagem ancorada

    def preparar(molde, rotulo_molde, formatar):
        if rotulo_molde in primeira_copia:
            molde = remover_desenhos(molde)
        else:
            primeira_copia.add(rotulo_molde)
        molde = formatar(molde)
        return com_paraid(garantir_fonte(molde, fonte))

    blocos = []
    for i, obj in enumerate(dados["objetos"], 1):
        faltando = [c for c in BLOCO_OBJETOS if c not in obj]
        if faltando:
            erro(f"objeto #{i}: faltam os campos {', '.join(faltando)}")
        for c in LISTAS_CONTEUDO:
            if not isinstance(obj.get(c), list) or not obj[c]:
                erro(f'objeto #{i}: no formato "objeto", cada objeto precisa da '
                     f'lista "{c}" (nao vazia) dentro dele')

        blocos.append(preparar(
            substituir_no_bloco(molde_obj, {c: obj[c] for c in BLOCO_OBJETOS}),
            "obj", lambda b: por_paragrafo(b, como_corpo)))

        blocos.append(com_paraid(rotulos["irregularidades"]))
        for t in obj["irregularidades"]:
            blocos.append(preparar(
                substituir_no_paragrafo(molde_irr, {"irregularidades": t}),
                "irr", lambda b: virar_lista(b, NUMID_BULLET)))

        blocos.append(com_paraid(rotulos["fatores"]))
        for f in obj["fatores_risco"]:
            faltando = [c for c in BLOCO_FATORES if c not in f]
            if faltando:
                erro(f"objeto #{i}, fator de risco: faltam os campos "
                     + ", ".join(faltando))
            blocos.append(preparar(
                substituir_no_bloco(molde_fator, f),
                "fator", lambda b: por_paragrafo(b, como_corpo)))

        blocos.append(com_paraid(rotulos["medidas"]))
        for t in obj["medidas_protecao"]:
            blocos.append(preparar(
                substituir_no_paragrafo(molde_med, {"medidas_protecao": t}),
                "med", lambda b: virar_lista(b, NUMID_BULLET)))

        blocos.append(com_paraid(rotulos["documentos"]))
        for t in obj["documentos_solicitados"]:
            blocos.append(preparar(
                substituir_no_paragrafo(molde_doc, {"documentos_solicitados": t}),
                "doc", lambda b: virar_lista(b, NUMID_BULLET)))

    composto = "".join(blocos)

    # cirurgia de tras para frente (os offsets anteriores continuam validos)
    xml = xml[:h4.start()] + xml[h8.start():]        # remove as secoes 4 a 7
    xml = xml[:obj_ini] + composto + xml[obj_fim:]   # objetos com sub-blocos
    xml = xml[:h3.start()] + metodologia + xml[h3.start():]  # metodologia -> fim da secao 2
    return xml


def montar(dados, destino):
    faltando = [c for c in OBRIGATORIOS if c not in dados]
    if faltando:
        erro("campos ausentes no JSON: " + ", ".join(faltando))
    if dados["modo"] not in ("interdicao", "embargo"):
        erro('campo "modo" deve ser "interdicao" ou "embargo"')
    formato = dados.get("formato", "topico")
    if formato not in ("topico", "objeto"):
        erro('campo "formato" deve ser "topico" ou "objeto" (ausente = "topico")')
    if not isinstance(dados["objetos"], list) or not dados["objetos"]:
        erro('campo "objetos" deve ser uma lista nao vazia')
    if formato == "topico":
        faltando = [c for c in LISTAS_CONTEUDO if c not in dados]
        if faltando:
            erro('no formato "topico", faltam no JSON: ' + ", ".join(faltando))
        for campo in ("fatores_risco", "medidas_protecao", "documentos_solicitados"):
            if not isinstance(dados[campo], list) or not dados[campo]:
                erro(f'campo "{campo}" deve ser uma lista nao vazia')
    if not TEMPLATE.is_file():
        erro(f"template nao encontrado: {TEMPLATE}", 3)

    tmp = Path("/tmp/RT_montagem")
    if tmp.exists():
        shutil.rmtree(tmp)
    tmp.mkdir(parents=True)
    shutil.copy(template_personalizado(TEMPLATE), tmp / "template.docx")
    r = subprocess.run([sys.executable, str(AQUI / "docx_unpack.py"),
                        str(tmp / "template.docx"), str(tmp / "unpacked")],
                       capture_output=True, text=True)
    if r.returncode != 0:
        erro(f"falha ao desempacotar o template: {r.stderr.strip()}", 3)

    doc = tmp / "unpacked/word/document.xml"
    xml = doc.read_text(encoding="utf-8")

    fonte = fonte_do_corpo(xml)

    if dados["modo"] == "embargo":
        xml = aplicar_embargo(xml)

    if formato == "objeto":
        xml = montar_por_objeto(xml, dados, fonte)
        irregs = [t for o in dados["objetos"] for t in o["irregularidades"]]
        n_fatores = sum(len(o["fatores_risco"]) for o in dados["objetos"])
        n_medidas = sum(len(o["medidas_protecao"]) for o in dados["objetos"])
        n_docs = sum(len(o["documentos_solicitados"]) for o in dados["objetos"])
    else:
        # blocos repetiveis primeiro (o molde ainda tem os placeholders)
        xml = repetir_bloco(xml, BLOCO_OBJETOS, dados["objetos"], "objeto", fonte,
                            formatar=como_corpo)
        xml = repetir_bloco(xml, BLOCO_FATORES, dados["fatores_risco"], "fator de risco",
                            fonte, formatar=como_corpo)

        # item 4: um paragrafo por irregularidade
        irregs = dados["irregularidades"]
        if isinstance(irregs, str):
            irregs = [irregs]
        xml = expandir_paragrafos(
            xml, "irregularidades", irregs, fonte,
            formatar=lambda pg: virar_lista(pg, NUMID_BULLET))

        # itens 6 e 7: listas reais do Word
        xml = remover_vazio_apos(xml, "medidas_protecao")
        xml = expandir_lista(xml, "medidas_protecao", dados["medidas_protecao"],
                             NUMID_MEDIDAS, fonte)
        xml = expandir_lista(xml, "documentos_solicitados",
                             dados["documentos_solicitados"], NUMID_DOCUMENTOS, fonte)
        n_fatores = len(dados["fatores_risco"])
        n_medidas = len(dados["medidas_protecao"])
        n_docs = len(dados["documentos_solicitados"])

    # conclusao (opcional nos dois formatos)
    if dados.get("conclusao"):
        xml = inserir_conclusao(xml, dados["conclusao"], fonte)

    # item 2: contexto da inspecao no padrao do corpo (justificado, com recuo)
    xml = expandir_paragrafos(xml, "Contexto-da-inspecao-fisica",
                              [dados["Contexto-da-inspecao-fisica"]], fonte,
                              formatar=lambda pg: como_corpo(pg, recuo=True))

    # capa e fecho
    xml = substituir_tudo(xml, {c: dados[c] for c in SIMPLES
                                if c != "Contexto-da-inspecao-fisica"})

    sobraram = sorted(set(RE_CHAVE.findall(re.sub(r"<[^>]+>", "", xml))))
    if sobraram:
        erro("placeholders sem valor no documento final: "
             + ", ".join("{{%s}}" % s for s in sobraram))

    doc.write_text(xml, encoding="utf-8")

    numbering = tmp / "unpacked/word/numbering.xml"
    if numbering.is_file():
        nb = garantir_lista_documentos(numbering.read_text(encoding="utf-8"))
        numbering.write_text(garantir_lista_bullet(nb), encoding="utf-8")

    destino = Path(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)
    r = subprocess.run([sys.executable, str(AQUI / "docx_pack.py"),
                        str(tmp / "unpacked"), str(destino)],
                       capture_output=True, text=True)
    if r.returncode != 0:
        erro(f"falha ao empacotar o DOCX: {r.stdout.strip()} {r.stderr.strip()}", 3)

    print(f"OK: {destino}")
    print(f"     modo {dados['modo']} | formato {formato} | "
          f"{len(dados['objetos'])} objeto(s), "
          f"{len(irregs)} irregularidade(s), {n_fatores} fator(es), "
          f"{n_medidas} medida(s), {n_docs} documento(s)")
    return destino


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(2)
    origem = Path(sys.argv[1])
    if not origem.is_file():
        erro(f"arquivo JSON nao encontrado: {origem}")
    try:
        dados = json.loads(origem.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        erro(f"JSON invalido ({e})")
    montar(dados, sys.argv[2])


if __name__ == "__main__":
    main()
