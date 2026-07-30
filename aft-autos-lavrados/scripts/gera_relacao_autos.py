#!/usr/bin/env python3
"""Gera a "Relação de autos lavrados" (.docx) a partir de um
autos-lavrados.md (saída da skill /aft-autos-lavrados).

Uso:
    python3 gera_relacao_autos.py <autos-lavrados.md> [pasta_saida]

- Usa o template `template-relacao-autos.docx` (mesma pasta deste script).
  O cabeçalho do template (logos SIT/AFT) NUNCA é alterado.
- Design padrão: título e datas centralizados entre filetes navy, barra
  lateral navy nos títulos dos autos, texto sempre justificado, fonte Times
  New Roman 12pt em todo o documento.
- Só entram os autos lavrados válidos (seção "Detalhamento" do MD), agrupados
  por data do mais antigo para o mais recente, mantendo a ordem do MD dentro
  de cada data.
- Gera o `relacao-autos.docx` na pasta de saída (por padrão `<pasta da OS>/
  Relacao de autos/`). O documento final é o .docx: o toolkit não converte
  para PDF (se o AFT precisar de um, é Arquivo > Salvar como... > PDF no
  Word) — assim a skill não depende de LibreOffice nem de automação do Word.
- O .docx é montado com a `zipfile` da biblioteca padrão (via
  `_scripts/docx_unpack.py` e `docx_pack.py`). Nada de chamar os comandos
  `zip`/`unzip`: o Windows não os traz, e o Git for Windows distribui só o
  `unzip.exe` — o script morria no meio, com o .docx pela metade.
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

import re
import shutil
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from xml.sax.saxutils import escape

# Ferramentas compartilhadas do toolkit (skills/_scripts). Ficam num pacote
# irmão, então o caminho entra no sys.path na mão.
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_scripts"))
from docx_pack import empacotar          # noqa: E402
from docx_unpack import desempacotar     # noqa: E402

NAVY = "103B5A"  # cor do logo AFT no cabeçalho
TNR = "Times New Roman"
TNR_SZ = 24  # 12pt em vigésimos de ponto

TEMPLATE = Path(__file__).parent / "template-relacao-autos.docx"


def parse_md(md_path: Path):
    text = md_path.read_text(encoding="utf-8")

    m = re.search(r"^#\s*Autos lavrados\s*[—-]\s*(.+)$", text, re.M)
    empresa = m.group(1).strip() if m else md_path.parent.name

    # inscrição: dígitos no fim do nome da pasta da OS (CNPJ 14 ou CPF 11)
    md_folder = md_path.parent.name
    m = re.search(r"(\d{11,14})\s*$", md_folder)
    if m:
        insc = m.group(1)
    else:
        m = re.search(r"\b(\d{14})\b", text)
        insc = m.group(1) if m else ""

    if len(insc) == 14:
        insc_fmt = f"CNPJ {insc[:2]}.{insc[2:5]}.{insc[5:8]}/{insc[8:12]}-{insc[12:]}"
    elif len(insc) == 11:
        insc_fmt = f"CPF {insc[:3]}.{insc[3:6]}.{insc[6:9]}-{insc[9:]}"
    else:
        insc_fmt = insc

    # só a seção de detalhamento (ignora substituídos/pendentes/sem rascunho)
    m = re.search(r"##\s*Detalhamento[^\n]*\n(.*?)(?=\n##\s|\Z)", text, re.S)
    bloco = m.group(1) if m else text

    autos = []
    for chunk in re.split(r"\n###\s+", bloco)[1:]:
        linhas = chunk.strip()
        num = re.match(r"N[ºo°]?\s*([\d.\-]+)", linhas)
        ementa = re.search(r"\*\*Ementa\s+([^\*]+)\*\*", linhas)
        desc = re.search(r"\*\*Descrição da ementa:\*\*\s*(.+)", linhas)
        const = re.search(r"\*\*Constatação:\*\*\s*(.+)", linhas)
        data = re.search(r"\*\*Lavrado em:\*\*\s*(\d{2}/\d{2}/\d{4})", linhas)
        if not (ementa and data):
            continue
        autos.append({
            "num": num.group(1) if num else "",
            "ementa": ementa.group(1).strip(),
            "desc": desc.group(1).strip() if desc else "",
            "const": const.group(1).strip() if const else "",
            "data": data.group(1),
        })

    # agrupa por data, ordena grupos do mais antigo ao mais recente,
    # mantendo a ordem do MD dentro de cada grupo
    grupos = {}
    for a in autos:
        grupos.setdefault(a["data"], []).append(a)
    datas = sorted(grupos, key=lambda d: datetime.strptime(d, "%d/%m/%Y"))
    return empresa, insc_fmt, [(d, grupos[d]) for d in datas]


def run(txt, bold=False, color=None, spacing=None):
    rpr = f'<w:rFonts w:ascii="{TNR}" w:eastAsia="{TNR}" w:hAnsi="{TNR}" w:cs="{TNR}"/>'
    if bold:
        rpr += "<w:b/><w:bCs/>"
    if color:
        rpr += f'<w:color w:val="{color}"/>'
    if spacing:  # espaçamento entre caracteres (vigésimos de ponto)
        rpr += f'<w:spacing w:val="{spacing}"/>'
    rpr += f'<w:sz w:val="{TNR_SZ}"/><w:szCs w:val="{TNR_SZ}"/>'
    return f'<w:r><w:rPr>{rpr}</w:rPr><w:t xml:space="preserve">{escape(txt)}</w:t></w:r>'


def para(runs, before=0, after=0, jc=None, borders=None, ind_left=0):
    ppr = '<w:adjustRightInd w:val="0"/>'
    if borders:  # dict lado -> (tipo, espessura, cor)
        pbdr = "".join(f'<w:{lado} w:val="{v}" w:sz="{sz}" w:space="4" w:color="{cor}"/>'
                       for lado, (v, sz, cor) in borders.items())
        ppr += f"<w:pBdr>{pbdr}</w:pBdr>"
    ppr += (f'<w:spacing w:before="{before}" w:after="{after}"/>'
            f'<w:ind w:left="{ind_left}" w:right="424"/>')
    if jc:
        ppr += f'<w:jc w:val="{jc}"/>'
    return f"<w:p><w:pPr>{ppr}</w:pPr>{runs}</w:p>"


def build_body(empresa, insc_fmt, grupos):
    p = []
    p.append(para(run("RELAÇÃO DE AUTOS LAVRADOS", bold=True, color=NAVY, spacing=40),
                  before=120, after=60, jc="center"))
    p.append(para(run(""), after=120, borders={"bottom": ("double", 8, NAVY)}))
    p.append(para(run("EMPREGADOR  ", bold=True, color=NAVY) + run(empresa),
                  after=60, jc="both"))
    p.append(para(run("INSCRIÇÃO  ", bold=True, color=NAVY) + run(insc_fmt),
                  after=240, jc="both"))

    for data, autos in grupos:
        p.append(para(run(f"LAVRADOS EM {data}", bold=True, color=NAVY, spacing=30),
                      before=280, after=200, jc="center",
                      borders={"top": ("single", 6, NAVY),
                               "bottom": ("single", 6, NAVY)}))
        for a in autos:
            titulo = f"Ementa {a['ementa']}"
            if a["num"]:
                titulo = f"AI nº {a['num']}   ·   {titulo}"
            p.append(para(run(titulo, bold=True, color=NAVY),
                          before=140, after=60, ind_left=170, jc="both",
                          borders={"left": ("single", 24, NAVY)}))
            if a["desc"]:
                p.append(para(run("Descrição da ementa — ", bold=True, color=NAVY)
                              + run(a["desc"]),
                              after=40, ind_left=170, jc="both"))
            if a["const"]:
                p.append(para(run("Constatação — ", bold=True, color=NAVY)
                              + run(a["const"]),
                              after=180, ind_left=170, jc="both"))
    return "".join(p)


def gerar_docx(md_path: Path, out_docx: Path):
    empresa, insc_fmt, grupos = parse_md(md_path)
    if not grupos:
        raise SystemExit("Nenhum auto lavrado encontrado no MD.")

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        desempacotar(TEMPLATE, tmp / "doc")
        doc_xml = (tmp / "doc/word/document.xml").read_text(encoding="utf-8")

        body = build_body(empresa, insc_fmt, grupos)
        sect = re.search(r"<w:sectPr.*?</w:sectPr>", doc_xml, re.S).group(0)
        novo = re.sub(r"<w:body>.*</w:body>",
                      f"<w:body>{body}{sect}</w:body>", doc_xml, flags=re.S)
        (tmp / "doc/word/document.xml").write_text(novo, encoding="utf-8")

        out_tmp = tmp / "out.docx"
        empacotar(tmp / "doc", out_tmp)
        out_docx.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(out_tmp, out_docx)

    total = sum(len(a) for _, a in grupos)
    return total, len(grupos)


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    md_path = Path(sys.argv[1]).expanduser()
    # Layout novo (22/07/2026): a relacao mora em AUTOS/Relacao de autos/. Em OS
    # ainda nao migradas (sem a pasta AUTOS/), mantem o lugar antigo, na raiz.
    if len(sys.argv) > 2:
        pasta_saida = Path(sys.argv[2]).expanduser()
    else:
        base = md_path.parent
        pasta_saida = ((base / "AUTOS" / "Relacao de autos")
                       if (base / "AUTOS").is_dir()
                       else base / "Relacao de autos")

    out_docx = pasta_saida / "relacao-autos.docx"

    total, n_datas = gerar_docx(md_path, out_docx)
    print(f"OK docx: {out_docx} — {total} autos em {n_datas} data(s).")


if __name__ == "__main__":
    main()
