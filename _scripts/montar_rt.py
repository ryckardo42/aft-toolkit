#!/usr/bin/env python3
"""
montar_rt.py - monta o Relatorio Tecnico de Interdicao/Embargo (.docx) a partir
do template oficial do toolkit e de um arquivo JSON com as partes variaveis.

Substitui a edicao manual do document.xml. O script acha cada parte variavel de
dois jeitos e preserva TODO o texto fixo (cabecalho, citacoes, tabelas da NR-3,
pedido de suspensao, SEI, assinatura):

  - pelos MARCADORES "#" que o AFT deixou no template ("#objetos" na secao 3,
    "#irregularidades" na secao 4). Como sao achados pelo texto, o AFT pode
    mover o marcador de lugar no Word que o script continua encontrando;
  - pelo w14:paraId, nas partes sem marcador (capa, secoes 5 a 8, rodape).

O que ele resolve sozinho:
  - paraId novo sempre < 0x80000000 (valor maior corrompe o DOCX no Word);
  - ementas da secao 4 saem como paragrafos de LISTA (numPr), formato que o
    checar_rt_autos.py exige para contar as irregularidades, e entram LOGO APOS
    o titulo "4. IRREGULARIDADE(S):" - antes do bloco fixo da metodologia;
  - remove a linha de exemplo "OBJETO: 1 - ATIVIDADE - Paralisacao: TOTAL", que
    e so um lembrete de formato no template e nao pode sair no documento real;
  - nas quatro linhas da secao 5, ACRESCENTA o valor ao rotulo que ja esta no
    template, em vez de reescrever o rotulo: se o AFT mudar "Descricao:" para
    outra coisa no Word, o script continua correto;
  - modo "embargo" adapta o texto fixo que fala em interdicao (NR-03, 3.2.2.1:
    embargo e para OBRA; 3.2.2.2: interdicao e para maquina/setor/atividade);
  - move o item "A) Requerimento expresso..." da secao 6 para a secao 7, que e
    onde ele pertence (o template o deixa preso ao fim das medidas).

Uso:
    python montar_rt.py "<dados.json>" "<saida.docx>"

O JSON deve ser gravado com a tool Write (nunca digitado no comando: acentos
viram lixo quando interpolados na linha de comando do Windows). Campos:

{
  "modo": "interdicao" | "embargo",
  "numero_termo": "4.123.456-7",
  "empregador": "RAZAO SOCIAL",
  "cnpj": "00.000.000/0001-00",
  "frase_inspecao": "A inspecao fisica foi realizada em DD/MM/AAAA...",
  "paragrafo_preposto": "(opcional) reescreve o ultimo paragrafo da secao 2",
  "objetos":     ["OBJETO: 1 - MAQUINA - ... - Paralisacao: TOTAL", ...],
  "ementas":     ["XXXXXX-X - Descricao. Capitulacao: ...", ...],
  "fator_risco": "(opcional) Mecanico - entra antes do excesso de risco",
  "excesso_risco": "EXTREMO",
  "descricao_risco": "...",
  "risco_atual": "Consequencia SEVERA e probabilidade PROVAVEL. ...",
  "risco_referencia": "Consequencia SEVERA e probabilidade RARA. ...",
  "medidas":     ["A) ...", "B) ...", ...],
  "documentos":  ["B) ...", "C) ...", ...],
  "conclusao":   ["paragrafo 1", "paragrafo 2", ...],
  "cidade_data": "Goiania-GO, 30/07/2026",
  "nome_aft": "NOME DO AUDITOR"
}

Depois de montar, para inserir fotos use o inserir_foto_docx.py.
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
TEMPLATE = AQUI.parent / "aft-rt-rgi" / "template.docx"

# --- paraIds das partes variaveis do template oficial ---
P_TITULO       = "254D1643"   # TERMO DE INTERDICAO No XXXXX
P_EMPREGADOR   = "70FC8FD5"   # EMPREGADOR: XXXX
P_CNPJ         = "2426C45C"   # CNPJ: XXXXX
P_OBJETIVO     = "1EE37096"   # texto fixo da secao 1
P_PREPOSTO     = "5DF58A29"   # ultimo paragrafo da secao 2
P_SEC3_HDR     = "250CF13F"   # 3. OBJETO(S) INTERDITADO(S):
P_OBJETO_EX    = "5D9E20A5"   # linha de exemplo "OBJETO: 1 - ATIVIDADE - ..." (removida)
P_FATOR        = "2D76A9D7"   # Fator de Risco - excesso de risco:
P_DESCRICAO    = "7A311088"   # Descricao:
P_RISCO_ATUAL  = "05821EB3"   # Fundamentacao do risco atual:
P_RISCO_REF    = "6CBD2F6F"   # Fundamentacao do risco de referencia:
P_REQUERIMENTO = "1F8A24BD"   # A) Requerimento expresso ... suspensao da interdicao
P_SEC7_HDR     = "3374AF6A"   # 7. DOCUMENTO(S) SOLICITADO(S):
P_SEC8_HDR     = "0C0AE4AC"   # 8. CONCLUSAO/OBSERVACAO:
P_SUSP_HDR     = "06AC73F1"   # DO PEDIDO DE SUSPENSAO DA INTERDICAO
P_SUSP_TXT     = "20E88645"   # Sanadas as irregularidades ...
P_REQ_I        = "5DBA0D48"   # I - o numero do Termo de Interdicao;
P_REQ_II       = "459C6BAE"   # II - a identificacao da(s) maquina(s) ou setor de servico;
P_CIDADE_DATA  = "1C5BF08E"   # XXXXX-XX, XX/XX/2026
P_NOME_AFT     = "06D83714"   # XXXXXXXX

# Marcadores "#" que o AFT deixou no template para sinalizar onde entra o texto
# gerado. Sao localizados PELO TEXTO (nao por paraId): assim o AFT pode mover o
# marcador de lugar no Word, e o script continua encontrando.
MARCADOR_OBJETOS = "#objetos"
MARCADOR_EMENTAS = "#irregularidades"

OBRIGATORIOS = [
    "modo", "numero_termo", "empregador", "cnpj", "frase_inspecao", "objetos",
    "ementas", "excesso_risco", "descricao_risco", "risco_atual",
    "risco_referencia", "medidas", "documentos", "conclusao", "cidade_data", "nome_aft",
]
# "fator_risco" e "paragrafo_preposto" sao opcionais.

RE_PARAGRAFO = re.compile(r"<w:p\b[^>]*>.*?</w:p>|<w:p\b[^>]*/>", re.S)


def erro(msg, codigo=2):
    print(f"ERRO: {msg}", file=sys.stderr)
    sys.exit(codigo)


def novo_paraid():
    """paraId valido: hex de 8 digitos < 0x80000000 (valor maior quebra o DOCX)."""
    return f"{random.randint(1, 0x7FFFFFFE):08X}"


def esc(t):
    return str(t).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def achar_paragrafo(xml, paraid):
    for m in RE_PARAGRAFO.finditer(xml):
        if f'w14:paraId="{paraid}"' in m.group(0):
            return m
    erro(f"paraId {paraid} nao encontrado - o template mudou? "
         f"Confira {TEMPLATE}", 3)


def achar_marcador(xml, marcador):
    """Localiza o paragrafo que contem um marcador '#...' do template."""
    for m in RE_PARAGRAFO.finditer(xml):
        runs = re.findall(r"<w:r\b[^>]*>.*?</w:r>", m.group(0), re.S)
        t = "".join("".join(re.findall(r"<w:t[^>]*>(.*?)</w:t>", r, re.S)) for r in runs)
        if marcador in t:
            return m
    erro(f"marcador {marcador} nao encontrado no template - ele foi apagado? "
         f"Confira {TEMPLATE}", 3)


def remover_paragrafo(xml, paraid):
    m = achar_paragrafo(xml, paraid)
    return xml[:m.start()] + xml[m.end():]


def texto_do_paragrafo(p):
    runs = re.findall(r"<w:r\b[^>]*>.*?</w:r>", p, re.S)
    return "".join("".join(re.findall(r"<w:t[^>]*>(.*?)</w:t>", r, re.S)) for r in runs)


def _rpr(p):
    """rPr do primeiro run com texto, para clonar a formatacao."""
    for r in re.findall(r"<w:r\b[^>]*>.*?</w:r>", p, re.S):
        if "<w:t" in r:
            m = re.search(r"<w:rPr>.*?</w:rPr>", r, re.S)
            return m.group(0) if m else ""
    return ""


def _monta(attrs_base, ppr, rpr, texto, novo_id=True):
    """novo_id=False preserva o paraId do paragrafo original.
    Trocar o texto de UM paragrafo nao muda a identidade dele - e o paraId
    precisa sobreviver, porque paragrafos ja preenchidos ainda servem de molde
    de formatacao mais adiante (ex.: a secao 1 e o molde da secao 8)."""
    attrs = (re.sub(r'w14:paraId="[0-9A-Fa-f]+"', f'w14:paraId="{novo_paraid()}"', attrs_base)
             if novo_id else attrs_base)
    return (f"<w:p{attrs}>{ppr}<w:r>{rpr}"
            f'<w:t xml:space="preserve">{esc(texto)}</w:t></w:r></w:p>')


def _partes(p):
    ppr = re.search(r"<w:pPr>.*?</w:pPr>", p, re.S)
    return (re.match(r"<w:p\b([^>]*)>", p).group(1),
            ppr.group(0) if ppr else "", _rpr(p))


def substituir_texto(xml, paraid, novo_texto):
    m = achar_paragrafo(xml, paraid)
    attrs, ppr, rpr = _partes(m.group(0))
    return (xml[:m.start()]
            + _monta(attrs, ppr, rpr, novo_texto, novo_id=False)
            + xml[m.end():])


def substituir_por_varios(xml, paraid, textos):
    m = achar_paragrafo(xml, paraid)
    attrs, ppr, rpr = _partes(m.group(0))
    blocos = "".join(_monta(attrs, ppr, rpr, t) for t in textos)
    return xml[:m.start()] + blocos + xml[m.end():]


def marcador_por_varios(xml, marcador, textos):
    """Troca o paragrafo do marcador '#...' por N paragrafos com o mesmo estilo."""
    m = achar_marcador(xml, marcador)
    attrs, ppr, rpr = _partes(m.group(0))
    blocos = "".join(_monta(attrs, ppr, rpr, t) for t in textos)
    return xml[:m.start()] + blocos + xml[m.end():]


def completar_rotulo(xml, paraid, valor):
    """Acrescenta o valor ao rotulo que ja existe no template.
    Assim, se o AFT reescrever o rotulo no Word ('Descricao:' -> 'Descricao do
    risco:'), o script continua correto - ele nunca reescreve o rotulo."""
    rotulo = texto_do_paragrafo(achar_paragrafo(xml, paraid).group(0)).strip()
    return substituir_texto(xml, paraid, f"{rotulo} {valor}")


def inserir_depois(xml, paraid, textos, modelo_paraid):
    """Insere N paragrafos apos o paragrafo alvo, com a formatacao do modelo."""
    alvo = achar_paragrafo(xml, paraid)
    attrs, ppr, rpr = _partes(achar_paragrafo(xml, modelo_paraid).group(0))
    blocos = "".join(_monta(attrs, ppr, rpr, t) for t in textos)
    return xml[:alvo.end()] + blocos + xml[alvo.end():]


def substituir_por_ementas(xml, marcador, ementas):
    """Ementas da secao 4 como paragrafos de LISTA (numPr ilvl 2 / numId 1),
    no lugar do marcador '#irregularidades' - ou seja, logo apos o titulo
    '4. IRREGULARIDADE(S):', antes do bloco fixo da metodologia da NR-3.
    Sem o numPr o checar_rt_autos.py conta zero irregularidades."""
    m = achar_marcador(xml, marcador)
    blocos = []
    for t in ementas:
        blocos.append(
            f'<w:p w14:paraId="{novo_paraid()}" w14:textId="77777777" '
            f'w:rsidR="00B0080B" w:rsidRDefault="00B0080B" w:rsidP="00CD6010">'
            f'<w:pPr><w:pStyle w:val="Corpodetexto"/>'
            f'<w:numPr><w:ilvl w:val="2"/><w:numId w:val="1"/></w:numPr>'
            f'<w:spacing w:line="360" w:lineRule="auto"/><w:ind w:right="424"/>'
            f'<w:jc w:val="both"/><w:rPr><w:rFonts w:ascii="Tahoma" w:hAnsi="Tahoma" '
            f'w:cs="Tahoma"/><w:sz w:val="22"/><w:szCs w:val="22"/></w:rPr></w:pPr>'
            f'<w:r><w:rPr><w:rFonts w:ascii="Tahoma" w:hAnsi="Tahoma" w:cs="Tahoma"/>'
            f'<w:sz w:val="22"/><w:szCs w:val="22"/></w:rPr>'
            f'<w:t xml:space="preserve">{esc(t)}</w:t></w:r></w:p>'
        )
    return xml[:m.start()] + "".join(blocos) + xml[m.end():]


def montar(dados, destino):
    faltando = [c for c in OBRIGATORIOS if c not in dados]
    if faltando:
        erro("campos ausentes no JSON: " + ", ".join(faltando))
    if dados["modo"] not in ("interdicao", "embargo"):
        erro('campo "modo" deve ser "interdicao" ou "embargo"')
    for campo in ("objetos", "ementas", "medidas", "documentos", "conclusao"):
        if not isinstance(dados[campo], list) or not dados[campo]:
            erro(f'campo "{campo}" deve ser uma lista nao vazia')
    if not TEMPLATE.is_file():
        erro(f"template nao encontrado: {TEMPLATE}", 3)

    tmp = Path("/tmp/RT_montagem")
    if tmp.exists():
        shutil.rmtree(tmp)
    tmp.mkdir(parents=True)
    shutil.copy(TEMPLATE, tmp / "template.docx")
    r = subprocess.run([sys.executable, str(AQUI / "docx_unpack.py"),
                        str(tmp / "template.docx"), str(tmp / "unpacked")],
                       capture_output=True, text=True)
    if r.returncode != 0:
        erro(f"falha ao desempacotar o template: {r.stderr.strip()}", 3)

    doc = tmp / "unpacked/word/document.xml"
    xml = doc.read_text(encoding="utf-8")
    embargo = dados["modo"] == "embargo"
    rotulo = "EMBARGO" if embargo else "INTERDIÇÃO"

    # capa
    xml = substituir_texto(xml, P_TITULO, f"TERMO DE {rotulo} Nº {dados['numero_termo']}")
    xml = substituir_texto(xml, P_EMPREGADOR, f"EMPREGADOR: {dados['empregador']}")
    xml = substituir_texto(xml, P_CNPJ, f"CNPJ: {dados['cnpj']}")

    # secao 1 (texto fixo + frase da inspecao)
    base = texto_do_paragrafo(achar_paragrafo(xml, P_OBJETIVO).group(0))
    if embargo:
        base = (base.replace("objetos interditados", "objetos embargados")
                    .replace("Termo de Interdição", "Termo de Embargo"))
    xml = substituir_texto(xml, P_OBJETIVO, base + " " + dados["frase_inspecao"])

    # secao 2 (paragrafo do preposto, opcional)
    if dados.get("paragrafo_preposto"):
        xml = substituir_texto(xml, P_PREPOSTO, dados["paragrafo_preposto"])

    # secao 3 (objetos no marcador #objetos; a linha de exemplo do template sai)
    if embargo:
        xml = substituir_texto(xml, P_SEC3_HDR, "3.  OBJETO(S) EMBARGADO(S):")
    xml = marcador_por_varios(xml, MARCADOR_OBJETOS, dados["objetos"])
    xml = remover_paragrafo(xml, P_OBJETO_EX)

    # secao 4 (ementas em lista, no marcador #irregularidades)
    xml = substituir_por_ementas(xml, MARCADOR_EMENTAS, dados["ementas"])

    # secao 5 (os rotulos vem do template; o script so acrescenta os valores)
    fator = dados.get("fator_risco")
    xml = completar_rotulo(xml, P_FATOR,
                           f"{fator} - {dados['excesso_risco']}" if fator
                           else dados["excesso_risco"])
    xml = completar_rotulo(xml, P_DESCRICAO, dados["descricao_risco"])
    xml = completar_rotulo(xml, P_RISCO_ATUAL, dados["risco_atual"])
    xml = completar_rotulo(xml, P_RISCO_REF, dados["risco_referencia"])

    # secoes 6 e 7: o item "A) Requerimento expresso..." do template esta preso ao
    # fim da secao 6, mas e DOCUMENTO - vai para a primeira posicao da secao 7.
    requerimento = texto_do_paragrafo(achar_paragrafo(xml, P_REQUERIMENTO).group(0))
    if embargo:
        requerimento = requerimento.replace("suspensão da interdição", "suspensão do embargo")
    xml = inserir_depois(xml, P_SEC7_HDR, [requerimento] + dados["documentos"],
                         modelo_paraid=P_REQUERIMENTO)
    xml = substituir_por_varios(xml, P_REQUERIMENTO, dados["medidas"])

    # secao 8 (conclusao)
    xml = inserir_depois(xml, P_SEC8_HDR, dados["conclusao"], modelo_paraid=P_OBJETIVO)

    # texto fixo do pedido de suspensao (so muda no embargo)
    if embargo:
        xml = substituir_texto(xml, P_SUSP_HDR, "DO PEDIDO DE SUSPENSÃO DO EMBARGO")
        t = texto_do_paragrafo(achar_paragrafo(xml, P_SUSP_TXT).group(0))
        xml = substituir_texto(xml, P_SUSP_TXT,
                               t.replace("suspensão da interdição", "suspensão do embargo"))
        xml = substituir_texto(xml, P_REQ_I, "I - o número do Termo de Embargo;")
        xml = substituir_texto(xml, P_REQ_II,
                               "II - a identificação da obra ou da frente de trabalho;")

    # rodape
    xml = substituir_texto(xml, P_CIDADE_DATA, dados["cidade_data"])
    xml = substituir_texto(xml, P_NOME_AFT, dados["nome_aft"])

    doc.write_text(xml, encoding="utf-8")
    destino = Path(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)
    r = subprocess.run([sys.executable, str(AQUI / "docx_pack.py"),
                        str(tmp / "unpacked"), str(destino)],
                       capture_output=True, text=True)
    if r.returncode != 0:
        erro(f"falha ao empacotar o DOCX: {r.stdout.strip()} {r.stderr.strip()}", 3)

    print(f"OK: {destino}")
    print(f"     {len(dados['objetos'])} objeto(s), {len(dados['ementas'])} ementa(s), "
          f"modo {dados['modo']}")
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
