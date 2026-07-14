#!/usr/bin/env python3
"""Gera a "Relação de autos lavrados" (.docx + .pdf) a partir de um
autos-lavrados.md (saída da skill /autos-lavrados).

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
  Relacao de autos/`) e tenta também `relacao-autos.pdf` (mesmo conteúdo
  visual) via LibreOffice `soffice --headless`, se instalado. Se o soffice
  não estiver disponível, o script avisa e orienta a exportar o PDF
  manualmente a partir do .docx (Word: Arquivo > Salvar como... > PDF) — a
  ausência do PDF nunca impede a geração do .docx.
"""
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from xml.sax.saxutils import escape

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
        subprocess.run(["unzip", "-q", str(TEMPLATE), "-d", str(tmp / "doc")], check=True)
        doc_xml = (tmp / "doc/word/document.xml").read_text(encoding="utf-8")

        body = build_body(empresa, insc_fmt, grupos)
        sect = re.search(r"<w:sectPr.*?</w:sectPr>", doc_xml, re.S).group(0)
        novo = re.sub(r"<w:body>.*</w:body>",
                      f"<w:body>{body}{sect}</w:body>", doc_xml, flags=re.S)
        (tmp / "doc/word/document.xml").write_text(novo, encoding="utf-8")

        out_tmp = tmp / "out.docx"
        subprocess.run(["zip", "-Xrq", str(out_tmp), "."], cwd=tmp / "doc", check=True)
        out_docx.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(out_tmp, out_docx)

    total = sum(len(a) for _, a in grupos)
    return total, len(grupos)


def gerar_pdf(docx_path: Path, pdf_path: Path, timeout=25):
    """Converte docx -> pdf sem alterar o visual, best-effort, só via
    LibreOffice `soffice --headless --convert-to pdf` (se instalado) —
    conversão headless, não depende de automação nem de diálogos de
    permissão do sistema. Levanta RuntimeError com instrução para exportar
    manualmente se o soffice não estiver disponível ou falhar.

    Propositalmente NÃO usa docx2pdf/Word aqui: a biblioteca docx2pdf chama
    sys.exit(1) internamente quando a automação do Word falha, o que encerra
    o processo Python inteiro em vez de permitir tratar o erro — e em
    ambientes sandboxed (ex.: Terminal sem permissão de Automação no macOS)
    essa falha é o caso comum, não a exceção."""
    soffice = shutil.which("soffice")
    if soffice:
        try:
            with tempfile.TemporaryDirectory() as tmp:
                subprocess.run(
                    [soffice, "--headless", "--convert-to", "pdf",
                     "--outdir", tmp, str(docx_path)],
                    check=True, timeout=timeout,
                )
                gerado = Path(tmp) / (docx_path.stem + ".pdf")
                if gerado.exists():
                    shutil.copy(gerado, pdf_path)
                    return "soffice"
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            pass

    raise RuntimeError(
        "PDF não gerado automaticamente (LibreOffice/soffice não está "
        "instalado ou a conversão falhou nesta máquina). Abra o "
        f"{docx_path.name} no Word, confira os dados e use "
        "Arquivo > Salvar como... > formato PDF para gerar o PDF manualmente."
    )


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    md_path = Path(sys.argv[1]).expanduser()
    pasta_saida = (Path(sys.argv[2]).expanduser() if len(sys.argv) > 2
                   else md_path.parent / "Relacao de autos")

    out_docx = pasta_saida / "relacao-autos.docx"
    out_pdf = pasta_saida / "relacao-autos.pdf"

    total, n_datas = gerar_docx(md_path, out_docx)
    print(f"OK docx: {out_docx} — {total} autos em {n_datas} data(s).")

    try:
        motor = gerar_pdf(out_docx, out_pdf)
        print(f"OK pdf: {out_pdf} (via {motor})")
    except (RuntimeError, subprocess.TimeoutExpired) as e:
        print(f"AVISO: {e}")


if __name__ == "__main__":
    main()
