# -*- coding: utf-8 -*-
"""Insere uma fotografia num .docx do toolkit, logo após um parágrafo âncora.

Uso:
  python inserir_foto_docx.py <arquivo.docx> <foto> "<texto do parágrafo âncora>" "<legenda>"

Embute a imagem em word/media/, cria a relação em document.xml.rels e monta o
parágrafo <w:drawing> com a foto centralizada, seguido de um parágrafo de legenda.
A largura é ajustada para caber na mancha do texto (máx. ~15,5 cm).
"""
import re, sys, shutil, subprocess, struct, random
from pathlib import Path

SCRIPTS = Path.home() / '.claude/skills/_scripts'
EMU_POR_CM = 360000
LARGURA_MAX_CM = 15.5


def dimensoes(caminho):
    """Largura/altura em pixels, sem depender de biblioteca externa."""
    data = Path(caminho).read_bytes()
    if data[:8] == b'\x89PNG\r\n\x1a\n':
        w, h = struct.unpack('>II', data[16:24])
        return w, h
    if data[:2] == b'\xff\xd8':                      # JPEG
        i = 2
        while i < len(data) - 9:
            if data[i] != 0xFF:
                i += 1
                continue
            marca = data[i + 1]
            if marca in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7,
                         0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
                h, w = struct.unpack('>HH', data[i + 5:i + 9])
                return w, h
            i += 2 + struct.unpack('>H', data[i + 2:i + 4])[0]
    raise SystemExit('ERRO: formato de imagem não suportado (use PNG ou JPEG).')


def novo_paraid():
    return f'{random.randint(1, 0x7FFFFFFE):08X}'


def inserir(docx, foto, ancora, legenda):
    docx, foto = Path(docx), Path(foto)
    tmp = Path('/tmp/RT_foto')
    if tmp.exists():
        shutil.rmtree(tmp)
    tmp.mkdir(parents=True)
    subprocess.run([sys.executable, str(SCRIPTS / 'docx_unpack.py'),
                    str(docx), str(tmp / 'unpacked')], check=True, capture_output=True)
    raiz = tmp / 'unpacked'

    # 1. copia a imagem para word/media com nome livre
    media = raiz / 'word/media'
    media.mkdir(exist_ok=True)
    ext = foto.suffix.lower().replace('.jpeg', '.jpg')
    n = 1
    while (media / f'foto{n}{ext}').exists():
        n += 1
    nome_media = f'foto{n}{ext}'
    shutil.copy(foto, media / nome_media)

    # 2. cria a relação em document.xml.rels
    rels_path = raiz / 'word/_rels/document.xml.rels'
    rels = rels_path.read_text(encoding='utf-8')
    usados = {int(m) for m in re.findall(r'Id="rId(\d+)"', rels)}
    rid = f'rId{max(usados) + 1}'
    nova_rel = (f'<Relationship Id="{rid}" Type="http://schemas.openxmlformats.org/'
                f'officeDocument/2006/relationships/image" Target="media/{nome_media}"/>')
    rels = rels.replace('</Relationships>', nova_rel + '</Relationships>')
    rels_path.write_text(rels, encoding='utf-8')

    # 3. calcula o tamanho preservando a proporção
    px_w, px_h = dimensoes(foto)
    larg_cm = min(LARGURA_MAX_CM, px_w / 96 * 2.54)
    alt_cm = larg_cm * px_h / px_w
    cx, cy = int(larg_cm * EMU_POR_CM), int(alt_cm * EMU_POR_CM)

    # 4. monta os parágrafos (imagem centralizada + legenda)
    did = random.randint(100, 9999)
    p_img = (
        f'<w:p w14:paraId="{novo_paraid()}" w14:textId="77777777" w:rsidR="00B0080B" '
        f'w:rsidRDefault="00B0080B"><w:pPr><w:spacing w:before="120" w:after="60"/>'
        f'<w:jc w:val="center"/></w:pPr><w:r><w:drawing>'
        f'<wp:inline distT="0" distB="0" distL="0" distR="0">'
        f'<wp:extent cx="{cx}" cy="{cy}"/><wp:effectExtent l="0" t="0" r="0" b="0"/>'
        f'<wp:docPr id="{did}" name="Imagem {did}"/><wp:cNvGraphicFramePr>'
        f'<a:graphicFrameLocks xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
        f'noChangeAspect="1"/></wp:cNvGraphicFramePr>'
        f'<a:graphic xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">'
        f'<a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">'
        f'<pic:pic xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture">'
        f'<pic:nvPicPr><pic:cNvPr id="{did}" name="{nome_media}"/><pic:cNvPicPr/></pic:nvPicPr>'
        f'<pic:blipFill><a:blip r:embed="{rid}"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>'
        f'<pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm>'
        f'<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr>'
        f'</pic:pic></a:graphicData></a:graphic></wp:inline></w:drawing></w:r></w:p>'
    )
    p_leg = (
        f'<w:p w14:paraId="{novo_paraid()}" w14:textId="77777777" w:rsidR="00B0080B" '
        f'w:rsidRDefault="00B0080B"><w:pPr><w:spacing w:after="120"/><w:jc w:val="center"/></w:pPr>'
        f'<w:r><w:rPr><w:rFonts w:ascii="Tahoma" w:hAnsi="Tahoma" w:cs="Tahoma"/>'
        f'<w:i/><w:sz w:val="18"/><w:szCs w:val="18"/></w:rPr>'
        f'<w:t xml:space="preserve">{legenda}</w:t></w:r></w:p>'
    )

    # 5. localiza o parágrafo âncora e insere depois dele
    doc_path = raiz / 'word/document.xml'
    xml = doc_path.read_text(encoding='utf-8')
    alvo = None
    for m in re.finditer(r'<w:p\b[^>]*>.*?</w:p>|<w:p\b[^>]*/>', xml, re.S):
        runs = re.findall(r'<w:r\b[^>]*>.*?</w:r>', m.group(0), re.S)
        t = ''.join(''.join(re.findall(r'<w:t[^>]*>(.*?)</w:t>', r, re.S)) for r in runs)
        if ancora in t:
            alvo = m
    if not alvo:
        raise SystemExit(f'ERRO: parágrafo âncora não encontrado: {ancora!r}')
    xml = xml[:alvo.end()] + p_img + p_leg + xml[alvo.end():]
    doc_path.write_text(xml, encoding='utf-8')

    r = subprocess.run([sys.executable, str(SCRIPTS / 'docx_pack.py'),
                        str(raiz), str(docx)], capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stdout, r.stderr)
        raise SystemExit('ERRO ao empacotar o DOCX')
    print(f'OK: foto inserida em {docx} ({larg_cm:.1f} x {alt_cm:.1f} cm)')


if __name__ == '__main__':
    if len(sys.argv) != 5:
        raise SystemExit(__doc__)
    inserir(*sys.argv[1:5])
