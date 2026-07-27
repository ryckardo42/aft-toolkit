#!/usr/bin/env python3
"""Monta o RT de Manutenção de Interdição/Embargo (.docx) a partir do template do aft-rt-rgi.

Mantém cabeçalho, rodapé, estilos e o bloco fixo final do template (DO PEDIDO DE
SUSPENSÃO + instruções do SEI + assinatura) e substitui o miolo pelas seções da
manutenção. Uso:

    python3 montar_rt_manutencao.py spec.json

O spec.json (UTF-8):
{
  "template": "/caminho/para/template.docx",
  "output":   "/caminho/para/RT_Manutencao.docx",
  "titulo_linha2": "TERMO DE MANUTENÇÃO DE EMBARGO Nº 3.089.823-4",
  "titulo_linha3": "(Ref. ao Termo de Embargo Nº 1.087.867-0)",   // opcional
  "empregador": "EMPRESA LTDA",
  "cnpj": "00.000.000/0000-00",
  "secoes": [
    {"titulo": "1. OBJETIVO:",
     "blocos": [ {"tipo": "p", "texto": "O presente relatório..."} ]},
    ...
  ],
  "cidade_data": "Goiânia-GO, 18 de julho de 2026.",
  "nome_aft": "FULANO DE TAL"
}

Tipos de bloco: "p" parágrafo, "b" bullet, "q" citação recuada em itálico,
"h2" subtítulo (ex.: 2.1). Em qualquer texto, **trecho** vira negrito.
Requer apenas a biblioteca padrão do Python 3 (funciona no Git Bash/Windows).
"""
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
    else:
        ppr = ('<w:pStyle w:val="Corpodetexto"/><w:spacing w:line="360" w:lineRule="auto"/>'
               '<w:ind w:left="112" w:right="829" w:firstLine="708"/><w:jc w:val="both"/>')
    return (f'<w:p w14:paraId="{pid()}" w14:textId="77777777" w:rsidR="007E66CC" w:rsidRDefault="007E66CC" w:rsidP="00A157A2">'
            f'<w:pPr>{ppr}<w:rPr>{rpr_p}</w:rPr></w:pPr>{runs(text, kind in ("h", "h2"), kind == "q")}</w:p>')


def para_titulo(text):
    """Linha de título centralizada em negrito (mesmo estilo dos blocos 1-2 do template)."""
    rpr = '<w:rFonts w:ascii="Tahoma" w:eastAsiaTheme="minorHAnsi" w:hAnsi="Tahoma" w:cs="Tahoma"/><w:b/><w:bCs/>'
    return (f'<w:p w14:paraId="{pid()}" w14:textId="77777777" w:rsidR="00D23E1C" w:rsidRDefault="00D23E1C" w:rsidP="00CD6010">'
            f'<w:pPr><w:adjustRightInd w:val="0"/><w:ind w:right="424"/><w:jc w:val="center"/>'
            f'<w:rPr>{rpr}</w:rPr></w:pPr>'
            f'<w:r><w:rPr>{rpr}</w:rPr><w:t xml:space="preserve">{esc(text)}</w:t></w:r></w:p>')


def blank():
    return (f'<w:p w14:paraId="{pid()}" w14:textId="77777777" w:rsidR="007E66CC" w:rsidRDefault="007E66CC" w:rsidP="00A157A2">'
            f'<w:pPr><w:pStyle w:val="Corpodetexto"/><w:spacing w:line="360" w:lineRule="auto"/>'
            f'<w:ind w:left="112" w:right="829"/><w:rPr>{RPR}</w:rPr></w:pPr></w:p>')


def main():
    if len(sys.argv) != 2:
        sys.exit("uso: montar_rt_manutencao.py spec.json")
    spec = json.load(open(sys.argv[1], encoding="utf-8"))
    tpl_path = os.path.expanduser(spec["template"])
    out_path = os.path.expanduser(spec["output"])

    zin = zipfile.ZipFile(tpl_path)
    xml = zin.read("word/document.xml").decode("utf-8")

    body_m = re.search(r"<w:body>(.*)</w:body>", xml, re.S)
    body = body_m.group(1)
    blocks = re.findall(r"<w:p [^>]*>.*?</w:p>|<w:p/>|<w:tbl>.*?</w:tbl>", body, re.S)
    assert len(blocks) == 134, (
        f"template com {len(blocks)} blocos (esperado 134) — o template.docx mudou; ajuste o script")
    tail_extra = body[body.rfind(blocks[-1]) + len(blocks[-1]):]

    # cabeçalho da 1ª página: bloco 0 (vazio) + 1 (RELATÓRIO TÉCNICO) mantidos;
    # bloco 2 (TERMO DE INTERDIÇÃO Nº XXXXX) substituído pelas linhas do título da manutenção
    head = blocks[0:2]
    head.append(para_titulo(spec["titulo_linha2"]))
    if spec.get("titulo_linha3"):
        head.append(para_titulo(spec["titulo_linha3"]))
    head += blocks[3:9]  # em branco + EMPREGADOR + CNPJ + espaçamento

    # rodapé fixo do template: DO PEDIDO DE SUSPENSÃO + SEI + cidade/data + assinatura
    foot = blocks[97:134]

    # cidade/data (bloco 123 do template, fragmentado em runs) — refeito com run único
    i_cd = 123 - 97
    assert "XXXXX" in foot[i_cd] and "202" in foot[i_cd], "bloco cidade/data mudou de posição no template"
    foot[i_cd] = (f'<w:p w14:paraId="{pid()}" w14:textId="77777777" w:rsidR="00BE1DD9" w:rsidRDefault="000171B9" w:rsidP="00A157A2">'
                  '<w:pPr><w:pStyle w:val="Corpodetexto"/><w:tabs><w:tab w:val="left" w:pos="10377"/></w:tabs>'
                  '<w:spacing w:before="1"/><w:ind w:right="-143"/><w:jc w:val="center"/>'
                  '<w:rPr><w:sz w:val="20"/><w:szCs w:val="20"/></w:rPr></w:pPr>'
                  '<w:r><w:rPr><w:sz w:val="20"/><w:szCs w:val="20"/></w:rPr>'
                  f'<w:t xml:space="preserve">{esc(spec["cidade_data"])}</w:t></w:r></w:p>')

    # seções do miolo
    miolo = []
    for sec in spec["secoes"]:
        miolo.append(para(sec["titulo"], "h"))
        for b in sec["blocos"]:
            miolo.append(para(b["texto"], b.get("tipo", "p")))

    new_body = "".join(head) + blank() + "".join(miolo) + blank() + blank() + "".join(foot) + tail_extra
    new_xml = xml[:body_m.start(1)] + new_body + xml[body_m.end(1):]

    # placeholders remanescentes do template
    new_xml = new_xml.replace("<w:t>XXXX</w:t>", f"<w:t>{esc(spec['empregador'])}</w:t>", 1)
    new_xml = new_xml.replace("<w:t>XXXXX</w:t>", f"<w:t>{esc(spec['cnpj'])}</w:t>", 1)
    new_xml = new_xml.replace("<w:t>XXXXXXXX</w:t>", f"<w:t>{esc(spec['nome_aft'])}</w:t>")

    parseString(new_xml)  # valida o XML antes de empacotar

    if os.path.exists(out_path):
        os.replace(out_path, out_path + ".bak")
    zout = zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED)
    for n in zin.namelist():
        data = new_xml.encode("utf-8") if n == "word/document.xml" else zin.read(n)
        zout.writestr(n, data)
    zout.close()

    # confere que não sobrou placeholder
    restante = re.findall(r"X{4,}", " ".join(re.findall(r"<w:t[^>]*>([^<]*)</w:t>", new_xml)))
    if restante:
        print(f"AVISO: placeholders remanescentes: {restante}")
    print(f"OK -> {out_path}")


if __name__ == "__main__":
    main()
