#!/usr/bin/env python3
"""Monta o RT de Levantamento TOTAL de Interdicao/Embargo (.docx) a partir do template do aft-rt-rgi.

Mantem o cabecalho institucional (logos MTE/SIT), os estilos e a fonte do
template e monta o miolo com as 7 secoes do levantamento. Diferente do RT de
manutencao, NAO carrega o bloco fixo final "DO PEDIDO DE SUSPENSAO" nem as
instrucoes do SEI: com o levantamento total a medida se encerra e essas
instrucoes deixam de fazer sentido. Uso:

    python3 montar_rt_levantamento.py spec.json

O spec.json (UTF-8):
{
  "template": "~/.claude/skills/aft-rt-rgi/template.docx",
  "output":   "/caminho/RT_Levantamento_4145339-5.docx",
  "titulo_linha2": "TERMO DE LEVANTAMENTO DE INTERDICAO N 9.999.999-9",
  "titulo_linha3": "(Ref. ao Termo de Interdicao N 4.145.339-5)",   // opcional
  "empregador": "EMPRESA LTDA",
  "rotulo_documento": "CNPJ",              // ou "CPF", "CAEPF"
  "numero_documento": "00.000.000/0000-00",
  "secoes": [
    {"titulo": "1. OBJETIVO:",
     "blocos": [ {"tipo": "p", "texto": "O presente relatorio..."} ]},
    ...
  ],
  "cidade_data": "Goiania-GO, 03/08/2026.",
  "nome_aft": "FULANO DE TAL",
  "cif": "35807-0"                          // opcional
}

Tipos de bloco: "p" paragrafo, "b" bullet, "q" citacao recuada em italico,
"h2" subtitulo (ex.: 2.1), "m" linha sem recuo de primeira linha (linha de
objeto, rotulos). Em qualquer texto, **trecho** vira negrito.
Requer apenas a biblioteca padrao do Python 3 (funciona no Git Bash/Windows).
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
import os
import random
import re
import sys
import zipfile
from xml.dom.minidom import parseString

RPR = '<w:rFonts w:ascii="Tahoma" w:hAnsi="Tahoma" w:cs="Tahoma"/><w:sz w:val="22"/><w:szCs w:val="22"/>'


def pid():
    return f"{random.randint(1, 0x7FFFFFFE):08X}"


def esc(t):
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def runs(text, base_bold=False, italic=False):
    out = []
    for i, part in enumerate(re.split(r"\*\*(.+?)\*\*", text, flags=re.S)):
        if not part:
            continue
        bold = base_bold or (i % 2 == 1)
        rpr = RPR + ("<w:b/><w:bCs/>" if bold else "") + ("<w:i/><w:iCs/>" if italic else "")
        out.append(f'<w:r><w:rPr>{rpr}</w:rPr><w:t xml:space="preserve">{esc(part)}</w:t></w:r>')
    return "".join(out)


def para(text, kind="p"):
    rpr_p = RPR + ("<w:b/><w:bCs/>" if kind in ("h", "h2") else "")
    if kind == "h":
        ppr = ('<w:pStyle w:val="Corpodetexto"/><w:spacing w:before="360" w:after="120" w:line="360" w:lineRule="auto"/>'
               '<w:ind w:left="112" w:right="424"/><w:jc w:val="both"/>')
    elif kind == "h2":
        ppr = ('<w:pStyle w:val="Corpodetexto"/><w:spacing w:before="240" w:after="60" w:line="360" w:lineRule="auto"/>'
               '<w:ind w:left="112" w:right="424"/><w:jc w:val="both"/>')
    elif kind == "q":
        ppr = ('<w:pStyle w:val="Corpodetexto"/><w:spacing w:before="120" w:after="120" w:line="276" w:lineRule="auto"/>'
               '<w:ind w:left="1418" w:right="829"/><w:jc w:val="both"/>')
    elif kind == "b":
        ppr = ('<w:pStyle w:val="Corpodetexto"/><w:spacing w:before="60" w:after="60" w:line="320" w:lineRule="auto"/>'
               '<w:ind w:left="1134" w:right="829" w:hanging="340"/><w:jc w:val="both"/>')
        text = "•\t" + text
    elif kind == "m":
        ppr = ('<w:pStyle w:val="Corpodetexto"/><w:spacing w:line="360" w:lineRule="auto"/>'
               '<w:ind w:left="112" w:right="829"/><w:jc w:val="both"/>')
    else:
        ppr = ('<w:pStyle w:val="Corpodetexto"/><w:spacing w:line="360" w:lineRule="auto"/>'
               '<w:ind w:left="112" w:right="829" w:firstLine="708"/><w:jc w:val="both"/>')
    return (f'<w:p w14:paraId="{pid()}" w14:textId="77777777" w:rsidR="007E66CC" w:rsidRDefault="007E66CC" w:rsidP="00A157A2">'
            f'<w:pPr>{ppr}<w:rPr>{rpr_p}</w:rPr></w:pPr>{runs(text, kind in ("h", "h2"))}</w:p>')


def para_titulo(text):
    """Linha de titulo centralizada em negrito (mesmo estilo dos blocos 1-2 do template)."""
    rpr = '<w:rFonts w:ascii="Tahoma" w:eastAsiaTheme="minorHAnsi" w:hAnsi="Tahoma" w:cs="Tahoma"/><w:b/><w:bCs/>'
    return (f'<w:p w14:paraId="{pid()}" w14:textId="77777777" w:rsidR="00D23E1C" w:rsidRDefault="00D23E1C" w:rsidP="00CD6010">'
            f'<w:pPr><w:adjustRightInd w:val="0"/><w:ind w:right="424"/><w:jc w:val="center"/>'
            f'<w:rPr>{rpr}</w:rPr></w:pPr>'
            f'<w:r><w:rPr>{rpr}</w:rPr><w:t xml:space="preserve">{esc(text)}</w:t></w:r></w:p>')


def para_centro(text, bold=False, sz=None):
    """Linha centralizada (cidade/data e assinatura)."""
    rpr = RPR if sz is None else f'<w:rFonts w:ascii="Tahoma" w:hAnsi="Tahoma" w:cs="Tahoma"/><w:sz w:val="{sz}"/><w:szCs w:val="{sz}"/>'
    if bold:
        rpr += "<w:b/><w:bCs/>"
    return (f'<w:p w14:paraId="{pid()}" w14:textId="77777777" w:rsidR="00BE1DD9" w:rsidRDefault="000171B9" w:rsidP="00A157A2">'
            f'<w:pPr><w:pStyle w:val="Corpodetexto"/><w:spacing w:before="1"/><w:ind w:right="-143"/>'
            f'<w:jc w:val="center"/><w:rPr>{rpr}</w:rPr></w:pPr>'
            f'<w:r><w:rPr>{rpr}</w:rPr><w:t xml:space="preserve">{esc(text)}</w:t></w:r></w:p>')


def blank():
    return (f'<w:p w14:paraId="{pid()}" w14:textId="77777777" w:rsidR="007E66CC" w:rsidRDefault="007E66CC" w:rsidP="00A157A2">'
            f'<w:pPr><w:pStyle w:val="Corpodetexto"/><w:spacing w:line="360" w:lineRule="auto"/>'
            f'<w:ind w:left="112" w:right="829"/><w:rPr>{RPR}</w:rPr></w:pPr></w:p>')


def main():
    if len(sys.argv) != 2:
        sys.exit("uso: montar_rt_levantamento.py spec.json")
    spec = json.load(open(sys.argv[1], encoding="utf-8"))
    tpl_path = os.path.expanduser(spec["template"])
    out_path = os.path.expanduser(spec["output"])

    zin = zipfile.ZipFile(tpl_path)
    xml = zin.read("word/document.xml").decode("utf-8")

    body_m = re.search(r"<w:body>(.*)</w:body>", xml, re.S)
    body = body_m.group(1)
    blocks = re.findall(r"<w:p [^>]*>.*?</w:p>|<w:p/>|<w:tbl>.*?</w:tbl>", body, re.S)

    # cabecalho da 1a pagina: tudo ate a linha "RELATORIO TECNICO" (inclusive),
    # localizada pelo texto para nao depender de posicao fixa no template
    i_rt = next((i for i, b in enumerate(blocks)
                 if "".join(re.findall(r"<w:t[^>]*>([^<]*)</w:t>", b)).strip() == "RELATÓRIO TÉCNICO"), None)
    if i_rt is None:
        sys.exit("linha 'RELATÓRIO TÉCNICO' não encontrada — o template.docx do aft-rt-rgi mudou; ajuste o script")
    head = blocks[: i_rt + 1]
    tail_extra = body[body.rfind(blocks[-1]) + len(blocks[-1]):]  # sectPr do template

    # titulo + identificacao do empregador
    topo = [para_titulo(spec["titulo_linha2"])]
    if spec.get("titulo_linha3"):
        topo.append(para_titulo(spec["titulo_linha3"]))
    topo.append(blank())
    topo.append(para(f"**EMPREGADOR:** {spec['empregador']}", "m"))
    topo.append(para(f"**{spec.get('rotulo_documento', 'CNPJ')}:** {spec['numero_documento']}", "m"))

    # secoes do miolo
    miolo = []
    for sec in spec["secoes"]:
        miolo.append(para(sec["titulo"], "h"))
        for b in sec["blocos"]:
            miolo.append(para(b["texto"], b.get("tipo", "p")))

    # fecho: cidade/data + assinatura (sem o bloco fixo de pedido de suspensao/SEI)
    fecho = [blank(), blank(), para_centro(spec["cidade_data"], sz=20),
             blank(), blank(), blank(),
             para_centro(spec["nome_aft"], bold=True),
             para_centro("Auditor-Fiscal do Trabalho")]
    if spec.get("cif"):
        fecho.append(para_centro(f"CIF: {spec['cif']}"))

    new_body = "".join(head) + "".join(topo) + blank() + "".join(miolo) + "".join(fecho) + tail_extra
    new_xml = xml[:body_m.start(1)] + new_body + xml[body_m.end(1):]

    parseString(new_xml)  # valida o XML antes de empacotar

    # confere que nenhum placeholder do template sobrou no corpo novo
    textos = " ".join(re.findall(r"<w:t[^>]*>([^<]*)</w:t>", new_body))
    restante = re.findall(r"\{\{[^}]*\}\}|X{4,}", textos)
    if restante:
        sys.exit(f"placeholders remanescentes no documento: {restante}")

    if os.path.exists(out_path):
        os.replace(out_path, out_path + ".bak")
    zout = zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED)
    for n in zin.namelist():
        data = new_xml.encode("utf-8") if n == "word/document.xml" else zin.read(n)
        zout.writestr(n, data)
    zout.close()
    print(f"OK -> {out_path}")


if __name__ == "__main__":
    main()
