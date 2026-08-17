#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Extrai o texto de um PDF pagina a pagina, com marcador de pagina, e faz a triagem
de confiabilidade de cada pagina.

Serve para o agente aft-extrator-pgr ler documento grande sem gastar o contexto com
a imagem de cada pagina: pagina nativa vira texto exato, de graca. E avisa, pagina a
pagina, onde o texto NAO merece confianca.

Tres alertas, que pedem condutas diferentes:

  SEM TEXTO       pagina escaneada. Ler visualmente (Read com o parametro pages).
  CONTEUDO EM IMAGEM  o texto esta bom, mas parte do conteudo (foto, plaqueta, tabela
                  em figura) so existe na imagem. Conferir visualmente antes de concluir
                  que algo esta ausente.
  TEXTO SUSPEITO  ha camada de texto, mas ela parece lixo de um OCR ruim anterior.
                  Ignorar o texto e ler a pagina visualmente.
  ORDEM EMBARALHADA  os caracteres estao certos, mas a ordem de leitura se perdeu
                  (tabela em coluna estreita sai letra por letra). Nao citar sem
                  conferir a pagina no original.

O terceiro e o mais traicoeiro: o texto parece bom e nao e.

Uso:
    python pdf_texto_paginado.py "documento.pdf"                 # -> ao lado do PDF
    python pdf_texto_paginado.py "documento.pdf" --saida "t.txt"
    python pdf_texto_paginado.py "documento.pdf" --so-resumo     # so o diagnostico
"""

import sys
import os
import io
import re
import tempfile
import unicodedata

try:
    import pdfplumber
except ImportError:
    print("Falta a biblioteca pdfplumber. Instale com: python -m pip install pdfplumber")
    sys.exit(1)

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


MIN_CHARS = 60             # abaixo disso a pagina nao tem texto util
MIN_PALAVRAS_LING = 40     # so avalia portugues se houver texto suficiente

# Um sinal FORTE sozinho condena a camada de texto; dois FRACOS somados tambem.
LIXO_FORTE, LIXO_FRACO = 0.030, 0.015        # caracteres estranhos
# Glifo sem mapeamento vira "(cid:NN)" no texto. Um ou outro num rodape e inofensivo
# (fonte que nao mapeou o simbolo); o que condena a pagina e a fonte inteira quebrada,
# quando boa parte do texto sai assim. Por isso a checagem e proporcional, nao booleana.
CID_FORTE, CID_MIN = 0.020, 5                # 2% da pagina E ao menos 5 marcadores
PERDIDO_FORTE, PERDIDO_MIN = 0.010, 3        # idem para caractere perdido
# A quantidade minima evita o artefato de pagina curta: num rodape de 350 caracteres,
# um unico marcador ja daria 2,6%. Fonte quebrada produz dezenas deles, nunca um.
ACENTO_FORTE, ACENTO_FRACO = 0.010, 0.025    # texto em portugues tem 4% a 8%
STOP_FRACO = 0.100                           # palavras comuns do portugues

# Ordem embaralhada: em pagina normal as linhas de 1-2 caracteres nao passam de 3%;
# em tabela virada letra por letra passam de 40%. O corte fica no meio, com folga.
ORDEM_LINHAS_CURTAS = 0.15
ORDEM_MIN_LINHAS = 10

# Pagina com muita imagem pode ter texto perfeito e, ainda assim, esconder a informacao
# que importa dentro das figuras (plaqueta, tabela em foto, rotulo de componente). Medido
# em documento real: PGR comum fica em 2% (so o logo do cabecalho); laudo de NR-12 cheio
# de foto passa de 25%. Este alerta SOMA aos outros, nao substitui: o texto continua bom,
# so pode estar incompleto.
IMAGEM_RELEVANTE = 0.15

PONTUACAO_OK = set(" .,;:!?()[]{}/-_'\"%$@#&*+=<>|\\\n\t\r°ºª§")

STOPWORDS = set("""
a o as os um uma uns umas de do da dos das em no na nos nas por para com sem sob
sobre ao aos que quando onde como qual quais e ou mas nao sim ser sao foi era
deve devera devem ter tem havera ha entre ate apos antes cada seu sua seus suas
este esta estes estas esse essa isso aquilo pelo pela pelos pelas se lhe mais
menos muito pouco todo toda todos todas outro outra conforme segundo mediante
""".split())


def _sem_acento(txt):
    return unicodedata.normalize("NFKD", txt).encode("ascii", "ignore").decode("ascii")


def diagnosticar(texto, cobertura_imagem=0.0):
    """Devolve a lista de (alerta, motivo) que se aplicam a pagina. Uma pagina pode ter
    mais de um alerta: o texto pode estar embaralhado E haver conteudo em imagem."""
    if len(texto.strip()) < MIN_CHARS:
        return [("SEM TEXTO",
                 "pagina sem texto extraivel (%d caracteres)" % len(texto.strip()))]

    extra = []
    if cobertura_imagem >= IMAGEM_RELEVANTE:
        extra.append(("CONTEUDO EM IMAGEM",
                      "%.0f%% da pagina e imagem: pode haver dado fora do texto"
                      % (100 * cobertura_imagem)))

    # --- ordem de leitura: caracteres certos, sequencia errada ---
    linhas = [l.strip() for l in texto.split("\n") if l.strip()]
    if len(linhas) >= ORDEM_MIN_LINHAS:
        # So conta linha curta que tenha LETRA solta: e essa a assinatura da coluna
        # virada ("c", "i", "r"). Numero sozinho numa linha ("1", "12") e normal em
        # formulario e em sumario, e nao indica embaralhamento.
        curtas = sum(1 for l in linhas
                     if len(l) <= 2 and any(c.isalpha() for c in l))
        taxa_curtas = curtas / float(len(linhas))
        if taxa_curtas >= ORDEM_LINHAS_CURTAS:
            return [("ORDEM EMBARALHADA",
                     "%.0f%% das linhas tem 1 ou 2 caracteres: a tabela saiu virada"
                     % (100 * taxa_curtas))] + extra

    # --- sanidade da camada de texto ---
    letras = [c for c in texto if c.isalpha()]
    acentuadas = [c for c in letras if _sem_acento(c) != c]
    estranhos = [c for c in texto if not c.isalnum() and c not in PONTUACAO_OK]
    tokens = [t.strip(".,;:()[]{}\"'").lower() for t in texto.split()]
    tokens = [t for t in tokens if t]
    stop = [t for t in tokens if _sem_acento(t) in STOPWORDS]

    taxa_lixo = len(estranhos) / float(max(len(texto), 1))
    taxa_acentos = len(acentuadas) / float(max(len(letras), 1))
    taxa_stop = len(stop) / float(max(len(tokens), 1))

    fortes, fracos = [], []
    n_car = float(max(len(texto), 1))
    cids = re.findall(r"\(cid:\d+\)", texto)
    taxa_cid = sum(len(m) for m in cids) / n_car
    n_perdido = texto.count("\ufffd")
    taxa_perdido = n_perdido / n_car
    if taxa_cid >= CID_FORTE and len(cids) >= CID_MIN:
        fortes.append("fonte sem mapeamento: %.0f%% da pagina em marcadores (cid:NN)"
                      % (100 * taxa_cid))
    if taxa_perdido >= PERDIDO_FORTE and n_perdido >= PERDIDO_MIN:
        fortes.append("caracteres perdidos na extracao (%.1f%%)" % (100 * taxa_perdido))
    if taxa_lixo > LIXO_FORTE:
        fortes.append("caracteres estranhos demais (%.1f%%)" % (100 * taxa_lixo))
    elif taxa_lixo > LIXO_FRACO:
        fracos.append("caracteres estranhos acima do normal (%.1f%%)" % (100 * taxa_lixo))

    # A acentuacao vale ate em tabela: celula em portugues tem acento ("Ruido",
    # "Exposicao"). Ja as palavras comuns ("de", "para") faltam em tabela por
    # natureza - por isso stopwords aqui e so sinal FRACO, nunca condena sozinho.
    if len(tokens) >= MIN_PALAVRAS_LING:
        if taxa_acentos < ACENTO_FORTE:
            fortes.append("texto em portugues praticamente sem acentos (%.1f%%)"
                          % (100 * taxa_acentos))
        elif taxa_acentos < ACENTO_FRACO:
            fracos.append("acentuacao abaixo do esperado (%.1f%%)" % (100 * taxa_acentos))
        if taxa_stop < STOP_FRACO:
            fracos.append("poucas palavras comuns do portugues (%.1f%%)" % (100 * taxa_stop))

    if fortes:
        return [("TEXTO SUSPEITO", "; ".join(fortes))] + extra
    if len(fracos) >= 2:
        return [("TEXTO SUSPEITO",
                 "dois sinais fracos somados: " + "; ".join(fracos))] + extra
    return extra


AVISO = {
    "SEM TEXTO": "[PAGINA SEM TEXTO EXTRAIVEL - PRECISA DE LEITURA VISUAL]",
    "TEXTO SUSPEITO": "[TEXTO SUSPEITO NESTA PAGINA - NAO CONFIAR NO TEXTO ACIMA, "
                      "LER A PAGINA VISUALMENTE]",
    "ORDEM EMBARALHADA": "[ORDEM DE LEITURA EMBARALHADA NESTA PAGINA - NAO CITAR SEM "
                         "CONFERIR A PAGINA NO ORIGINAL]",
    "CONTEUDO EM IMAGEM": "[PARTE DESTA PAGINA E IMAGEM - O TEXTO ACIMA PODE ESTAR "
                          "INCOMPLETO; CONFERIR A PAGINA VISUALMENTE]",
}


def faixas(nums):
    if not nums:
        return "nenhuma"
    nums = sorted(nums)
    partes, ini, ant = [], nums[0], nums[0]
    for n in nums[1:]:
        if n == ant + 1:
            ant = n
            continue
        partes.append(str(ini) if ini == ant else "%d-%d" % (ini, ant))
        ini = ant = n
    partes.append(str(ini) if ini == ant else "%d-%d" % (ini, ant))
    return ", ".join(partes)


def main():
    args = list(sys.argv[1:])
    if not args:
        print(__doc__)
        sys.exit(1)

    so_resumo = "--so-resumo" in args
    if so_resumo:
        args.remove("--so-resumo")

    saida = None
    if "--saida" in args:
        k = args.index("--saida")
        saida = args[k + 1] if len(args) > k + 1 else None
        del args[k:k + 2]

    pdf_path = args[0]
    if not os.path.isfile(pdf_path):
        print("Arquivo nao encontrado: %s" % pdf_path)
        sys.exit(1)
    if not saida:
        # NUNCA ao lado do PDF: o intermediario e uma copia integral do texto do
        # documento, e a pasta da OS nao e lugar para copia sobrando. Vai para a pasta
        # temporaria do sistema, e o caminho aparece na tela.
        saida = os.path.join(tempfile.gettempdir(),
                             os.path.splitext(os.path.basename(pdf_path))[0] + "_texto.txt")

    partes = []
    alertas = {"SEM TEXTO": [], "TEXTO SUSPEITO": [], "ORDEM EMBARALHADA": [],
               "CONTEUDO EM IMAGEM": []}
    total_car = 0

    with pdfplumber.open(pdf_path) as pdf:
        n = len(pdf.pages)
        for i, page in enumerate(pdf.pages, start=1):
            try:
                txt = page.extract_text() or ""
            except Exception:
                txt = ""
            total_car += len(txt)

            area_pag = max(float(page.width) * float(page.height), 1.0)
            area_img = 0.0
            for im in (page.images or []):
                try:
                    area_img += abs(float(im["x1"]) - float(im["x0"])) * \
                                abs(float(im["bottom"]) - float(im["top"]))
                except Exception:
                    pass
            cobertura = min(area_img / area_pag, 1.0)

            corpo = txt.strip()
            for alerta, motivo in diagnosticar(txt, cobertura):
                alertas[alerta].append(i)
                corpo = "%s\n%s (%s)" % (corpo, AVISO[alerta], motivo)
            partes.append("===== PAGINA %d =====\n%s" % (i, corpo))

    if not so_resumo:
        with io.open(saida, "w", encoding="utf-8") as f:
            f.write("\n\n".join(partes))

    print("PDF: %s" % os.path.basename(pdf_path))
    print("Paginas: %d" % n)
    print("Caracteres de texto nativo: %d (aprox. %d mil tokens)"
          % (total_car, round(total_car / 4.0 / 1000)))
    print("Paginas SEM texto extraivel (ler visualmente): %s"
          % faixas(alertas["SEM TEXTO"]))
    print("Paginas com TEXTO SUSPEITO (ignorar o texto, ler visualmente): %s"
          % faixas(alertas["TEXTO SUSPEITO"]))
    print("Paginas com ORDEM EMBARALHADA (nao citar sem conferir no original): %s"
          % faixas(alertas["ORDEM EMBARALHADA"]))
    print("Paginas com CONTEUDO EM IMAGEM (o texto pode estar incompleto): %s"
          % faixas(alertas["CONTEUDO EM IMAGEM"]))
    # Documento praticamente sem camada de texto: a leitura tera de ser toda visual.
    # E uma condicao de outra ordem, e a skill precisa tratar antes de decidir qualquer
    # coisa - por isso sai destacada, e nao diluida na lista de paginas.
    if n and len(alertas["SEM TEXTO"]) >= 0.8 * n:
        print("")
        print("*** DOCUMENTO SEM CAMADA DE TEXTO (%d de %d paginas escaneadas) ***"
              % (len(alertas["SEM TEXTO"]), n))
        print("    Nao ha texto para extrair: toda a leitura sera visual, pagina a")
        print("    pagina. E mais lenta e menos confiavel - avise o AFT e delegue ao")
        print("    agente extrator mesmo que o documento seja curto.")
        print("")

    nao_confiaveis = set(alertas["SEM TEXTO"] + alertas["TEXTO SUSPEITO"] +
                         alertas["ORDEM EMBARALHADA"])
    print("Paginas de texto confiavel: %d de %d" % (n - len(nao_confiaveis), n))
    print("  (a pagina so com CONTEUDO EM IMAGEM conta como confiavel: o texto dela esta")
    print("   bom, apenas pode nao contar tudo o que a pagina mostra)")
    if not so_resumo:
        print("Texto paginado gravado em: %s" % saida)


if __name__ == "__main__":
    main()
