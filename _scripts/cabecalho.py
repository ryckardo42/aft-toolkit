#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cabecalho.py - Cabecalho institucional com a LOTACAO do AFT nos .docx do toolkit.

Todo documento do toolkit sai com o mesmo cabecalho: brasao da Republica, tres
linhas de texto e os logos SIT e AFT, com um filete embaixo.

    Ministerio do Trabalho e Emprego
    Secretaria de Inspecao do Trabalho
    <lotacao do AFT>            (ex.: Gerencia Regional do Trabalho e Emprego
                                 em Nova Iguacu - RJ)

As duas primeiras linhas sao fixas; a terceira vem do campo `lotacao` do
aft-config.md (gravado pelo /aft-setup). Sem lotacao configurada, o cabecalho
sai com as duas linhas fixas - nunca com a lotacao de outra pessoa.

Como e aplicado: os templates .docx do repositorio continuam neutros (sao os
mesmos para todos os AFTs). Quem gera um documento pede aqui uma COPIA
PERSONALIZADA do template - gravada em <pasta AFT>/.templates/ e refeita
sozinha quando a lotacao ou o template mudam:

    import cabecalho
    tpl = cabecalho.template_personalizado(TEMPLATE)   # devolve str (caminho)
    doc = Document(tpl)

A troca e cirurgica: mexe SO na parte de cabecalho do .docx (word/headerN.xml,
suas relacoes e imagens). Corpo, rodape, estilos, numeracao e placeholders do
template ficam intactos - por isso serve tambem para o template do RT de
interdicao/embargo, que e texto juridicamente vinculado.

Nada aqui pode derrubar a geracao de um documento: qualquer falha devolve o
template original e o documento sai com o cabecalho antigo.

Uso no terminal (as skills /aft-setup e /aft-atualizar chamam assim):
    python cabecalho.py --status      # JSON: lotacao em uso e de onde veio
    python cabecalho.py --preparar    # refaz as copias personalizadas
    python cabecalho.py --aplicar "<arquivo.docx>" [--lotacao "..."]
"""
from __future__ import annotations

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

import argparse
import hashlib
import json
import re
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

AQUI = Path(__file__).resolve().parent
SKILLS = AQUI.parent
IMAGENS = SKILLS / "config" / "cabecalho"
UORGS_CSV = SKILLS / "config" / "uorgs.csv"

# Muda quando o desenho do cabecalho muda: entra na chave do cache, entao as
# copias personalizadas antigas sao refeitas sozinhas na proxima geracao.
VERSAO = 1

LINHA_1 = "Ministério do Trabalho e Emprego"
LINHA_2 = "Secretaria de Inspeção do Trabalho"

FONTE = "Calibri"          # o cabecalho nao segue a fonte do corpo (Times/Verdana)
COR_TEXTO = "404040"
COR_FILETE = "272727"
TAM = "18"                 # 9pt, em meios-pontos

EMU_CM = 360000

# (arquivo, largura_cm, altura_cm) - proporcao original de cada imagem
BRASAO = ("brasao.png", 1.45, 1.57)
SIT = ("sit.png", 2.80, 1.21)
LOGO_AFT = ("aft.png", 1.45, 1.22)

# Largura das 4 colunas, em centesimos de porcento (5000 = 100% da area de
# texto). Em porcentagem o cabecalho acompanha as margens de cada documento -
# o modelo_docx, por exemplo, troca as margens depois de abrir o template.
# Calibradas para a area de texto mais estreita entre os templates (15 cm):
# cada coluna de imagem cabe a sua, e o resto sobra para as tres linhas.
LARGURAS_PCT = (525, 3000, 975, 500)

NS_HDR = (
    'xmlns:wpc="http://schemas.microsoft.com/office/word/2010/wordprocessingCanvas" '
    'xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006" '
    'xmlns:o="urn:schemas-microsoft-com:office:office" '
    'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
    'xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math" '
    'xmlns:v="urn:schemas-microsoft-com:vml" '
    'xmlns:wp14="http://schemas.microsoft.com/office/word/2010/wordprocessingDrawing" '
    'xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" '
    'xmlns:w10="urn:schemas-microsoft-com:office:word" '
    'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" '
    'xmlns:w14="http://schemas.microsoft.com/office/word/2010/wordml" '
    'xmlns:wpg="http://schemas.microsoft.com/office/word/2010/wordprocessingGroup" '
    'xmlns:wps="http://schemas.microsoft.com/office/word/2010/wordprocessingShape" '
    'mc:Ignorable="w14 wp14"'
)
NS_A = "http://schemas.openxmlformats.org/drawingml/2006/main"
NS_PIC = "http://schemas.openxmlformats.org/drawingml/2006/picture"
NS_REL = "http://schemas.openxmlformats.org/package/2006/relationships"
TIPO_IMAGEM = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/image"

PREFIXO_MEDIA = "aft-cabecalho-"   # nome das imagens dentro do .docx


# --------------------------------------------------------------- a lotacao
def _frontmatter(texto: str) -> dict:
    """Campos simples (chave: valor) do front-matter do aft-config.md."""
    campos = {}
    for linha in texto.splitlines():
        if linha.strip() == "---" and campos:
            break
        m = re.match(r'\s*([a-z_]+)\s*:\s*"?([^"#]*?)"?\s*$', linha)
        if m:
            campos[m.group(1)] = m.group(2).strip()
    return campos


def _config() -> dict:
    """Campos do aft-config.md; {} se nao houver config (nunca levanta)."""
    try:
        sys.path.insert(0, str(AQUI))
        from pasta_aft import pasta_aft  # noqa: PLC0415
        cfg = Path(pasta_aft()) / "aft-config.md"
        if cfg.is_file():
            return _frontmatter(cfg.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        pass
    return {}


_MINUSCULAS = {"de", "do", "da", "dos", "das", "e", "em", "no", "na", "nos", "nas"}


def titulo_uorg(nome: str) -> str:
    """'GERENCIA REGIONAL DO TRABALHO EM X' -> 'Gerencia Regional do Trabalho em X'.

    So arruma as maiusculas da tabela de UORGs: nao corrige nem completa o nome
    da unidade (quem confere a redacao da propria lotacao e o AFT, no
    /aft-setup).
    """
    palavras = []
    for i, p in enumerate(nome.strip().split()):
        baixa = p.lower()
        palavras.append(baixa if i and baixa in _MINUSCULAS else baixa.capitalize())
    return " ".join(palavras)


def lotacao_pela_uorg(uorg: str) -> str:
    """Nome da unidade na tabela oficial de UORGs, pelo codigo de 9 digitos."""
    uorg = (uorg or "").strip()
    if not uorg or not UORGS_CSV.is_file():
        return ""
    for linha in UORGS_CSV.read_text(encoding="utf-8", errors="replace").splitlines()[1:]:
        campos = linha.split(";")
        if len(campos) >= 4 and campos[0].strip() == uorg:
            nome = titulo_uorg(campos[1])
            uf = campos[2].strip()
            return f"{nome} - {uf}" if uf else nome
    return ""


def lotacao_configurada() -> tuple[str, str]:
    """(linha da lotacao, de onde veio: 'config' | 'uorg' | 'ausente').

    O campo `lotacao` presente e VAZIO e uma resposta valida do AFT ("nao quero
    minha unidade no cabecalho"): vale como 'config' para ninguem perguntar de
    novo nem cair na deducao pela tabela de UORGs.
    """
    cfg = _config()
    if "lotacao" in cfg:
        return cfg["lotacao"].strip(), "config"
    lot = lotacao_pela_uorg(cfg.get("uorg", ""))
    if lot:
        return lot, "uorg"
    return "", "ausente"


# ------------------------------------------------------- montagem do XML
def _imagem(rid: str, ident: int, nome: str, larg_cm: float, alt_cm: float) -> str:
    cx, cy = int(larg_cm * EMU_CM), int(alt_cm * EMU_CM)
    return (
        '<w:r><w:rPr><w:noProof/></w:rPr><w:drawing>'
        '<wp:inline distT="0" distB="0" distL="0" distR="0">'
        f'<wp:extent cx="{cx}" cy="{cy}"/>'
        '<wp:effectExtent l="0" t="0" r="0" b="0"/>'
        f'<wp:docPr id="{ident}" name="{nome}"/>'
        f'<wp:cNvGraphicFramePr><a:graphicFrameLocks xmlns:a="{NS_A}" noChangeAspect="1"/>'
        '</wp:cNvGraphicFramePr>'
        f'<a:graphic xmlns:a="{NS_A}"><a:graphicData uri="{NS_PIC}">'
        f'<pic:pic xmlns:pic="{NS_PIC}">'
        f'<pic:nvPicPr><pic:cNvPr id="{ident}" name="{nome}"/><pic:cNvPicPr/></pic:nvPicPr>'
        f'<pic:blipFill><a:blip r:embed="{rid}"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>'
        '<pic:spPr><a:xfrm><a:off x="0" y="0"/>'
        f'<a:ext cx="{cx}" cy="{cy}"/></a:xfrm>'
        '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr>'
        '</pic:pic></a:graphicData></a:graphic></wp:inline></w:drawing></w:r>'
    )


def _paragrafo(conteudo: str, alinhamento: str = "left") -> str:
    return (
        '<w:p><w:pPr>'
        '<w:spacing w:before="0" w:after="0" w:line="240" w:lineRule="auto"/>'
        '<w:ind w:left="0" w:right="0" w:firstLine="0"/>'
        f'<w:jc w:val="{alinhamento}"/>'
        f'<w:rPr><w:rFonts w:ascii="{FONTE}" w:hAnsi="{FONTE}" w:cs="{FONTE}"/>'
        f'<w:b/><w:bCs/><w:color w:val="{COR_TEXTO}"/>'
        f'<w:sz w:val="{TAM}"/><w:szCs w:val="{TAM}"/></w:rPr>'
        f'</w:pPr>{conteudo}</w:p>'
    )


def _linha_texto(texto: str) -> str:
    return _paragrafo(
        '<w:r>'
        f'<w:rPr><w:rFonts w:ascii="{FONTE}" w:hAnsi="{FONTE}" w:cs="{FONTE}"/>'
        f'<w:b/><w:bCs/><w:color w:val="{COR_TEXTO}"/>'
        f'<w:sz w:val="{TAM}"/><w:szCs w:val="{TAM}"/></w:rPr>'
        f'<w:t xml:space="preserve">{escape(texto)}</w:t></w:r>'
    )


def _celula(largura_pct: int, conteudo: str) -> str:
    return (
        '<w:tc><w:tcPr>'
        f'<w:tcW w:w="{largura_pct}" w:type="pct"/>'
        '<w:vAlign w:val="center"/>'
        f'</w:tcPr>{conteudo}</w:tc>'
    )


def header_xml(lotacao: str) -> str:
    """XML completo da parte de cabecalho (word/headerN.xml)."""
    linhas = [LINHA_1, LINHA_2]
    if lotacao.strip():
        linhas.append(lotacao.strip())
    texto = "".join(_linha_texto(l) for l in linhas)

    celulas = (
        _celula(LARGURAS_PCT[0], _paragrafo(
            _imagem("rId1", 101, "Brasão da República", BRASAO[1], BRASAO[2]), "left")) +
        _celula(LARGURAS_PCT[1], texto) +
        _celula(LARGURAS_PCT[2], _paragrafo(
            _imagem("rId2", 102, "Inspeção do Trabalho", SIT[1], SIT[2]), "right")) +
        _celula(LARGURAS_PCT[3], _paragrafo(
            _imagem("rId3", 103, "Auditoria-Fiscal do Trabalho", LOGO_AFT[1], LOGO_AFT[2]),
            "right"))
    )

    grade = "".join(f'<w:gridCol w:w="{int(9354 * p / 5000)}"/>' for p in LARGURAS_PCT)

    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\r\n'
        f'<w:hdr {NS_HDR}>'
        '<w:tbl><w:tblPr>'
        '<w:tblW w:w="5000" w:type="pct"/>'
        '<w:tblBorders>'
        '<w:top w:val="nil"/><w:left w:val="nil"/>'
        f'<w:bottom w:val="single" w:sz="6" w:space="0" w:color="{COR_FILETE}"/>'
        '<w:right w:val="nil"/><w:insideH w:val="nil"/><w:insideV w:val="nil"/>'
        '</w:tblBorders>'
        '<w:tblCellMar>'
        '<w:top w:w="0" w:type="dxa"/><w:left w:w="40" w:type="dxa"/>'
        '<w:bottom w:w="60" w:type="dxa"/><w:right w:w="40" w:type="dxa"/>'
        '</w:tblCellMar>'
        '<w:tblLook w:val="0000" w:firstRow="0" w:lastRow="0" w:firstColumn="0"'
        ' w:lastColumn="0" w:noHBand="1" w:noVBand="1"/>'
        f'</w:tblPr><w:tblGrid>{grade}</w:tblGrid>'
        f'<w:tr>{celulas}</w:tr>'
        '</w:tbl>'
        + _paragrafo("")      # o Word exige um paragrafo depois da tabela
        + '</w:hdr>'
    )


def _rels_xml() -> str:
    rels = "".join(
        f'<Relationship Id="rId{i}" Type="{TIPO_IMAGEM}" '
        f'Target="media/{PREFIXO_MEDIA}{arq}"/>'
        for i, (arq, _, _) in enumerate((BRASAO, SIT, LOGO_AFT), start=1)
    )
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\r\n'
            f'<Relationships xmlns="{NS_REL}">{rels}</Relationships>')


# ------------------------------------------------- troca dentro do .docx
def _partes_cabecalho(pecas: dict) -> list:
    """Partes de cabecalho PADRAO do documento (uma por secao, sem repetir).

    Documento de uma secao so - o caso de todos os templates do toolkit - devolve
    uma parte. Se um dia um documento tiver secoes diferentes (uma paisagem, por
    exemplo), todas trocam de cabecalho, e nao so a ultima.
    """
    doc = pecas.get("word/document.xml", b"").decode("utf-8", "replace")
    rels = pecas.get("word/_rels/document.xml.rels", b"").decode("utf-8", "replace")
    ids = re.findall(r'<w:headerReference[^>]*w:type="default"[^>]*r:id="(rId\d+)"', doc)
    if not ids:
        ids = re.findall(r'<w:headerReference[^>]*r:id="(rId\d+)"', doc)

    partes = []
    for rid in ids:
        alvo = re.search(rf'Id="{rid}"[^>]*Target="([^"]+)"', rels)
        if alvo:
            parte = "word/" + alvo.group(1).lstrip("/").replace("../", "")
            if parte not in partes:
                partes.append(parte)
    return partes


def _content_types(xml: bytes) -> bytes:
    """Garante o Default para png (as imagens do cabecalho sao png)."""
    texto = xml.decode("utf-8", "replace")
    if re.search(r'<Default[^>]*Extension="png"', texto, re.I):
        return xml
    pos = texto.index(">", texto.index("<Types ")) + 1
    novo = texto[:pos] + '<Default Extension="png" ContentType="image/png"/>' + texto[pos:]
    return novo.encode("utf-8")


def _limpar_midia_orfa(pecas: dict) -> None:
    """Tira as imagens que ficaram sem dono depois da troca do cabecalho."""
    usadas = set()
    for nome, dados in pecas.items():
        if nome.endswith(".rels"):
            for alvo in re.findall(r'Target="([^"]+)"', dados.decode("utf-8", "replace")):
                usadas.add(alvo.rsplit("/", 1)[-1])
    for nome in [n for n in pecas if n.startswith("word/media/")]:
        if nome.rsplit("/", 1)[-1] not in usadas:
            del pecas[nome]


def aplicar_em_docx(origem, destino, lotacao: str) -> None:
    """Grava em `destino` o .docx de `origem` com o cabecalho institucional.

    Mexe so nas partes de cabecalho: o resto do pacote e copiado byte a byte.
    Levanta ValueError se o documento nao tiver cabecalho para substituir.
    """
    origem, destino = Path(origem), Path(destino)
    with zipfile.ZipFile(origem) as z:
        ordem = z.namelist()
        pecas = {n: z.read(n) for n in ordem}

    partes = [p for p in _partes_cabecalho(pecas) if p in pecas]
    if not partes:
        raise ValueError(f"documento sem cabeçalho padrão para substituir: {origem}")

    for parte in partes:
        pecas[parte] = header_xml(lotacao).encode("utf-8")
        pecas[parte.replace("word/", "word/_rels/") + ".rels"] = _rels_xml().encode("utf-8")
    for arq, _, _ in (BRASAO, SIT, LOGO_AFT):
        img = IMAGENS / arq
        if not img.is_file():
            raise ValueError(f"imagem do cabeçalho não encontrada: {img}")
        pecas[f"word/media/{PREFIXO_MEDIA}{arq}"] = img.read_bytes()
    if "[Content_Types].xml" in pecas:
        pecas["[Content_Types].xml"] = _content_types(pecas["[Content_Types].xml"])
    _limpar_midia_orfa(pecas)

    novos = [n for n in pecas if n not in ordem]
    destino.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destino, "w", zipfile.ZIP_DEFLATED) as z:
        for nome in [n for n in ordem if n in pecas] + novos:
            z.writestr(nome, pecas[nome])


def aplicar_no_arquivo(caminho, lotacao: str | None = None) -> None:
    """Troca o cabecalho de um .docx JA GRAVADO, no proprio arquivo.

    Para quem monta o documento do zero (sem template do toolkit): grave o
    .docx com a parte de cabecalho ja criada - no python-docx,
    `secao.header.is_linked_to_previous = False` - e chame isto depois.
    """
    if lotacao is None:
        lotacao, _ = lotacao_configurada()
    caminho = Path(caminho)
    with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp:
        temporario = Path(tmp.name)
    aplicar_em_docx(caminho, temporario, lotacao)
    shutil.move(str(temporario), str(caminho))


# ------------------------------------------- copia personalizada (cache)
def pasta_cache() -> Path:
    """<pasta AFT>/.templates - fora do repositorio, sobrevive a atualizacao."""
    try:
        sys.path.insert(0, str(AQUI))
        from pasta_aft import pasta_aft  # noqa: PLC0415
        return Path(pasta_aft()) / ".templates"
    except Exception:
        return Path(tempfile.gettempdir()) / "aft-templates"


def template_personalizado(caminho, lotacao: str | None = None) -> str:
    """Caminho de uma copia do template com o cabecalho da lotacao do AFT.

    Refaz a copia quando o template do toolkit muda, quando a lotacao muda ou
    quando o desenho do cabecalho muda (VERSAO). Em qualquer erro devolve o
    template original - gerar documento com cabecalho antigo e melhor do que
    nao gerar.
    """
    origem = Path(caminho)
    try:
        if lotacao is None:
            lotacao, _ = lotacao_configurada()
        chave = hashlib.md5(
            origem.read_bytes() + f"|{VERSAO}|{lotacao}".encode("utf-8")
        ).hexdigest()[:10]
        destino = pasta_cache() / f"{origem.stem}-{chave}.docx"
        if destino.is_file():
            return str(destino)
        aplicar_em_docx(origem, destino, lotacao)
        for velho in destino.parent.glob(f"{origem.stem}-*.docx"):
            if velho != destino:
                velho.unlink(missing_ok=True)
        return str(destino)
    except Exception:
        return str(origem)


def _tem_texto(docx: Path) -> bool:
    """True se o corpo do .docx tem algum texto (nao e mais um modelo vazio)."""
    try:
        with zipfile.ZipFile(docx) as z:
            corpo = z.read("word/document.xml").decode("utf-8", "replace")
        return any(t.strip() for t in re.findall(r"<w:t[^>]*>([^<]*)</w:t>", corpo))
    except Exception:
        return True     # na duvida, preserva o arquivo do AFT


TEMPLATES_DO_TOOLKIT = (
    SKILLS / "aft-modelo-docx" / "scripts" / "template-cabecalho.docx",
    SKILLS / "aft-embargo-interdicao" / "template.docx",
    SKILLS / "aft-autos-lavrados" / "scripts" / "template-relacao-autos.docx",
)


def preparar() -> dict:
    """Refaz as copias personalizadas e a do Template com cabecalho da pasta AFT."""
    lotacao, origem = lotacao_configurada()
    feitos, falhas = [], []
    for tpl in TEMPLATES_DO_TOOLKIT:
        if not tpl.is_file():
            continue
        saida = template_personalizado(tpl, lotacao)
        (feitos if saida != str(tpl) else falhas).append(tpl.name)

    avulso = ""
    try:
        base = SKILLS / "Template" / "Template com cabeçalho.docx"
        if base.is_file():
            sys.path.insert(0, str(AQUI))
            from pasta_aft import pasta_aft  # noqa: PLC0415
            alvo = Path(pasta_aft()) / "Template com cabeçalho.docx"
            if alvo.is_file() and _tem_texto(alvo):
                avulso = "preservado"   # o AFT escreveu algo ali: nao e mais um modelo
            else:
                aplicar_em_docx(base, alvo, lotacao)
                avulso = str(alvo)
    except Exception:
        avulso = ""

    return {"lotacao": lotacao, "origem_lotacao": origem,
            "templates": feitos, "falharam": falhas,
            "template_avulso": avulso, "cache": str(pasta_cache())}


def main() -> int:
    ap = argparse.ArgumentParser(description="Cabeçalho institucional dos .docx do toolkit")
    ap.add_argument("--status", action="store_true", help="mostra a lotação em uso")
    ap.add_argument("--preparar", action="store_true", help="refaz as cópias personalizadas")
    ap.add_argument("--aplicar", metavar="DOCX", help="troca o cabeçalho de um .docx")
    ap.add_argument("--saida", metavar="DOCX", help="com --aplicar: grava em outro arquivo")
    ap.add_argument("--lotacao", metavar="TEXTO", help="usa esta lotação em vez da do config")
    args = ap.parse_args()

    if args.aplicar:
        lot = args.lotacao if args.lotacao is not None else lotacao_configurada()[0]
        origem = Path(args.aplicar)
        destino = Path(args.saida) if args.saida else origem
        if destino == origem:
            aplicar_no_arquivo(origem, lot)
        else:
            aplicar_em_docx(origem, destino, lot)
        print(json.dumps({"ok": True, "arquivo": str(destino), "lotacao": lot},
                         ensure_ascii=False))
        return 0

    if args.preparar:
        print(json.dumps(preparar(), ensure_ascii=False, indent=2))
        return 0

    lotacao, origem = lotacao_configurada()
    print(json.dumps({"lotacao": lotacao, "origem": origem,
                      "linhas_fixas": [LINHA_1, LINHA_2],
                      "cache": str(pasta_cache())}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
