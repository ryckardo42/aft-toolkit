#!/usr/bin/env python3
"""
gerar_painel.py — gera um painel HTML local das auditorias do AFT Toolkit.

Varre os memory.md de ~/Documents/AFT/OS ATIVAS/*/ , extrai os dados de cada OS
(empregador, CNPJ, município, status e os prazos de notificações DET) e produz um
painel.html autocontido (abre por duplo-clique, sem servidor) com:
  - contadores no topo (OS ativas, DETs vencidos, DETs vencendo em <= 7 dias,
    notificações não cadastradas);
  - tabela ordenável de OS com o prazo de DET mais urgente de cada uma,
    colorido por urgência (vencido / <= 7 dias / futuro / sem prazo);
  - lista de PDFs de notificação DET encontrados nas pastas das OS mas ainda
    SEM registro no memory.md (com código e datas, quando extraíveis).

É um leitor: NUNCA altera os memory.md. A fonte da verdade são os arquivos.

Uso:
    python gerar_painel.py [PASTA_OS_ATIVAS] [SAIDA_HTML] [SAIDA_ARTIFACT]

  PASTA_OS_ATIVAS (opcional): padrão ~/Documents/AFT/OS ATIVAS
  SAIDA_HTML      (opcional): padrão ~/Documents/AFT/painel.html
  SAIDA_ARTIFACT  (opcional): se informado, grava também uma versão para a
                  tool Artifact do Claude Code (sem <html>/<head>/<body> e sem
                  a coluna Pasta, que é caminho local). Use "" para pular um
                  argumento posicional e manter o padrão.

Imprime no stdout um resumo em JSON (para a skill /painel ecoar).
Usa a biblioteca padrão; se o pdfplumber estiver instalado (o /aft-setup
instala), lê a 1ª página dos PDFs para melhorar a detecção de notificações.
"""
from __future__ import annotations

import datetime
import html
import json
import re
import sys
from pathlib import Path

try:
    import pdfplumber  # opcional: detecção pelo conteúdo da 1ª página
except ImportError:
    pdfplumber = None

RE_FM = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
RE_TITULO = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)
RE_CNPJ_BODY = re.compile(r"\*\*CNPJ:\*\*\s*([\d./-]+)")
RE_PRAZO = re.compile(r"prazo[:\s]+(\d{2}/\d{2}/\d{4})", re.IGNORECASE)
RE_CODIGO_DET = re.compile(r"^-\s*\[[ xX]?\]\s*([A-Z0-9]{6,})", re.MULTILINE)
RE_DATA_ISO = re.compile(r"(\d{4})-(\d{2})-(\d{2})")
RE_DATA_BR = re.compile(r"(\d{2})/(\d{2})/(\d{4})")

# Detecção de notificações DET não cadastradas -------------------------------
# Código de notificação do DET: 12–16 caracteres alfanuméricos maiúsculos com
# pelo menos um dígito e uma letra (ex.: RMNHIHSH9525MU). O lookahead evita
# casar CNPJ (só dígitos) e palavras comuns (só letras).
RE_COD_NOVO = re.compile(r"\b(?=[A-Z0-9]{0,15}\d)(?=[0-9]{0,15}[A-Z])[A-Z0-9]{12,16}\b")
RE_EH_DET = re.compile(r"(?i)domic[ií]lio\s+eletr[oô]nico|notifica[cç][aã]o")
RE_CIENCIA_DOC = re.compile(r"(?i)ci[eê]ncia\D{0,40}(\d{2}/\d{2}/\d{4})")
RE_PRAZO_DOC = re.compile(r"(?i)prazo\D{0,40}(\d{2}/\d{2}/\d{4})")
MAX_PDF_BYTES = 5_000_000  # não abre PDFs maiores (fotos etc.)
MAX_PDFS_POR_OS = 40


def home_os() -> Path:
    if len(sys.argv) >= 2 and sys.argv[1].strip():
        return Path(sys.argv[1])
    return Path.home() / "Documents" / "AFT" / "OS ATIVAS"


def saida_html() -> Path:
    if len(sys.argv) >= 3 and sys.argv[2].strip():
        return Path(sys.argv[2])
    return Path.home() / "Documents" / "AFT" / "painel.html"


def saida_artifact() -> Path | None:
    if len(sys.argv) >= 4 and sys.argv[3].strip():
        return Path(sys.argv[3])
    return None


def parse_fm(fm: str, chave: str) -> str | None:
    m = re.search(rf"^{chave}\s*:\s*(.+?)\s*$", fm, re.MULTILINE)
    if not m:
        return None
    return m.group(1).strip().strip('"').strip("'") or None


def parse_data_br(s: str) -> datetime.date | None:
    m = RE_DATA_BR.search(s)
    if not m:
        return None
    d, mo, y = (int(x) for x in m.groups())
    try:
        return datetime.date(y, mo, d)
    except ValueError:
        return None


def extrair_secao(corpo: str, titulo: str) -> str:
    """Devolve o texto da seção '## titulo' até o próximo '## ' (ou o fim)."""
    m = re.search(rf"^##\s+{re.escape(titulo)}\s*$", corpo, re.MULTILINE)
    if not m:
        return ""
    inicio = m.end()
    prox = re.search(r"^##\s+", corpo[inicio:], re.MULTILINE)
    return corpo[inicio: inicio + prox.start()] if prox else corpo[inicio:]


def parse_memory(path: Path) -> dict:
    """Extrai dados de um memory.md, tolerante a formatos antigos."""
    texto = path.read_text(encoding="utf-8", errors="replace")
    pasta = path.parent.name

    fm_match = RE_FM.match(texto)
    fm = fm_match.group(1) if fm_match else ""
    corpo = texto[fm_match.end():] if fm_match else texto

    empregador = parse_fm(fm, "empregador")
    if not empregador:
        m = RE_TITULO.search(corpo)
        empregador = m.group(1).strip() if m else pasta

    cnpj = parse_fm(fm, "cnpj")
    if not cnpj:
        m = RE_CNPJ_BODY.search(corpo)
        cnpj = re.sub(r"\D", "", m.group(1)) if m else ""
    else:
        cnpj = re.sub(r"\D", "", cnpj)
    if not cnpj:
        m = re.search(r"(\d{14})\s*$", pasta)
        cnpj = m.group(1) if m else ""

    municipio = parse_fm(fm, "municipio") or ""
    status = parse_fm(fm, "status") or "em_andamento"

    # Prazos de DET — uma entrada por linha da seção ## Notificações DET.
    dets = []
    secao = extrair_secao(corpo, "Notificações DET") or extrair_secao(corpo, "Notificacoes DET")
    for linha in secao.splitlines():
        if not linha.strip().startswith("-"):
            continue
        prazo_m = RE_PRAZO.search(linha)
        prazo = parse_data_br(linha.split("prazo", 1)[1]) if prazo_m else None
        cod_m = RE_CODIGO_DET.search(linha)
        codigo = cod_m.group(1) if cod_m else None
        if prazo or codigo:
            dets.append({"codigo": codigo, "prazo": prazo})

    return {
        "pasta": pasta,
        "caminho": str(path.parent),
        "empregador": empregador,
        "cnpj": cnpj,
        "municipio": municipio,
        "status": status,
        "dets": dets,
        "memoria": texto,
    }


def texto_primeira_pagina(pdf: Path) -> str:
    """1ª página do PDF via pdfplumber; '' se indisponível/ilegível/grande."""
    if pdfplumber is None:
        return ""
    try:
        if pdf.stat().st_size > MAX_PDF_BYTES:
            return ""
        with pdfplumber.open(pdf) as doc:
            if not doc.pages:
                return ""
            return doc.pages[0].extract_text() or ""
    except Exception:
        return ""


def varrer_notificacoes_novas(pasta: Path, memoria: str) -> list[dict]:
    """PDFs com cara de notificação DET na pasta da OS (e subpastas de 1º
    nível, exceto Autos*) cujo código NÃO aparece no memory.md. Read-only."""
    pdfs: list[Path] = []
    try:
        entradas = sorted(pasta.iterdir())
    except OSError:
        return []
    for e in entradas:
        if e.is_file() and e.suffix.lower() == ".pdf":
            pdfs.append(e)
        elif e.is_dir() and not e.name.startswith((".", "Autos")):
            try:
                pdfs += sorted(p for p in e.iterdir()
                               if p.is_file() and p.suffix.lower() == ".pdf")
            except OSError:
                pass

    novos, vistos = [], set()
    for pdf in pdfs[:MAX_PDFS_POR_OS]:
        alvo = pdf.name
        texto = texto_primeira_pagina(pdf)
        if texto:
            alvo += "\n" + texto[:4000]
        cod_m = RE_COD_NOVO.search(alvo.upper())
        if not cod_m and not RE_EH_DET.search(alvo):
            continue  # nem código, nem cara de notificação
        codigo = cod_m.group(0) if cod_m else None
        if codigo and codigo in memoria:
            continue  # já cadastrada na ficha
        chave = codigo or pdf.name
        if chave in vistos:
            continue
        vistos.add(chave)
        ciencia = RE_CIENCIA_DOC.search(alvo)
        prazo = RE_PRAZO_DOC.search(alvo)
        try:
            mtime = datetime.date.fromtimestamp(pdf.stat().st_mtime)
        except OSError:
            mtime = None
        novos.append({
            "arquivo": pdf.name,
            "codigo": codigo,
            "ciencia": ciencia.group(1) if ciencia else None,
            "prazo": prazo.group(1) if prazo else None,
            "data_arquivo": mtime.strftime("%d/%m/%Y") if mtime else None,
        })
    return novos


def classifica(dias: int | None) -> str:
    if dias is None:
        return "sem-prazo"
    if dias < 0:
        return "vencido"
    if dias <= 7:
        return "urgente"
    return "futuro"


def main() -> int:
    base = home_os()
    hoje = datetime.date.today()

    oss = []
    if base.exists():
        for mem in sorted(base.glob("*/memory.md")):
            try:
                oss.append(parse_memory(mem))
            except Exception as e:  # uma OS ruim não derruba o painel
                oss.append({
                    "pasta": mem.parent.name, "caminho": str(mem.parent),
                    "empregador": mem.parent.name, "cnpj": "", "municipio": "",
                    "status": "erro", "dets": [], "memoria": "", "erro": str(e),
                })

    # Notificações DET nas pastas ainda sem registro no memory.md.
    for os_ in oss:
        try:
            os_["novas"] = varrer_notificacoes_novas(
                Path(os_["caminho"]), os_.get("memoria", ""))
        except Exception:
            os_["novas"] = []
    n_novas = sum(len(o["novas"]) for o in oss)

    # Enriquecer cada OS com o prazo mais urgente (menor dias-restantes).
    n_vencidos = n_urgentes = 0
    for os_ in oss:
        prazos = [d["prazo"] for d in os_["dets"] if d["prazo"]]
        if prazos:
            mais_urgente = min(prazos)
            dias = (mais_urgente - hoje).days
            os_["prazo_top"] = mais_urgente
            os_["dias_top"] = dias
        else:
            os_["prazo_top"] = None
            os_["dias_top"] = None
        os_["classe"] = classifica(os_["dias_top"])
        for d in os_["dets"]:
            if d["prazo"]:
                dd = (d["prazo"] - hoje).days
                if dd < 0:
                    n_vencidos += 1
                elif dd <= 7:
                    n_urgentes += 1

    # Ordena: vencidos primeiro, depois por dias-restantes; sem-prazo ao fim.
    def chave(o):
        return (o["dias_top"] is None, o["dias_top"] if o["dias_top"] is not None else 0)
    oss.sort(key=chave)

    html_out = render_html(oss, hoje, len(oss), n_vencidos, n_urgentes, n_novas)
    destino = saida_html()
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(html_out, encoding="utf-8")

    destino_art = saida_artifact()
    if destino_art:
        destino_art.parent.mkdir(parents=True, exist_ok=True)
        destino_art.write_text(
            render_miolo(oss, hoje, len(oss), n_vencidos, n_urgentes, n_novas,
                         com_pasta=False, artifact=True),
            encoding="utf-8")

    # Resumo no stdout (a skill /painel usa isto para responder em texto).
    resumo = {
        "painel": str(destino),
        "artifact_html": str(destino_art) if destino_art else None,
        "os_ativas": len(oss),
        "dets_vencidos": n_vencidos,
        "dets_vencendo_7d": n_urgentes,
        "notificacoes_nao_cadastradas": n_novas,
        "novas": [
            {"empregador": o["empregador"], **n}
            for o in oss for n in (o.get("novas") or [])
        ],
        "vencendo": [
            {
                "empregador": o["empregador"],
                "prazo": o["prazo_top"].strftime("%d/%m/%Y"),
                "dias": o["dias_top"],
            }
            for o in oss
            if o["dias_top"] is not None and o["dias_top"] <= 7
        ],
    }
    print(json.dumps(resumo, ensure_ascii=False, indent=2))
    return 0


def render_html(oss, hoje, n_os, n_venc, n_urg, n_novas) -> str:
    miolo = render_miolo(oss, hoje, n_os, n_venc, n_urg, n_novas,
                         com_pasta=True, artifact=False)
    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Painel AFT — auditorias em andamento</title>
</head>
<body>
{miolo}
</body>
</html>
"""


def render_miolo(oss, hoje, n_os, n_venc, n_urg, n_novas,
                 com_pasta: bool, artifact: bool) -> str:
    cores = {
        "vencido": "#c0392b", "urgente": "#e67e22",
        "futuro": "#27ae60", "sem-prazo": "#7f8c8d", "erro": "#c0392b",
    }
    rotulos = {
        "vencido": "VENCIDO", "urgente": "vence em breve",
        "futuro": "no prazo", "sem-prazo": "sem prazo", "erro": "erro de leitura",
    }

    linhas = []
    for o in oss:
        cls = o["classe"]
        if o["prazo_top"] is not None:
            prazo_txt = o["prazo_top"].strftime("%d/%m/%Y")
            dias = o["dias_top"]
            if dias < 0:
                detalhe = f"{prazo_txt} ({abs(dias)} dia(s) atrás)"
            elif dias == 0:
                detalhe = f"{prazo_txt} (hoje)"
            else:
                detalhe = f"{prazo_txt} (em {dias} dia(s))"
        else:
            detalhe = "—"
        cnpj_fmt = o["cnpj"]
        if len(cnpj_fmt) == 14:
            cnpj_fmt = f"{cnpj_fmt[:2]}.{cnpj_fmt[2:5]}.{cnpj_fmt[5:8]}/{cnpj_fmt[8:12]}-{cnpj_fmt[12:]}"
        n_dets = len(o["dets"])
        col_pasta = (f'<td class="path">{html.escape(o["caminho"])}</td>'
                     if com_pasta else "")
        linhas.append(
            f'<tr data-dias="{o["dias_top"] if o["dias_top"] is not None else 999999}">'
            f'<td><span class="dot" style="background:{cores[cls]}"></span>'
            f'{html.escape(rotulos[cls])}</td>'
            f'<td class="emp">{html.escape(o["empregador"])}</td>'
            f'<td>{html.escape(cnpj_fmt)}</td>'
            f'<td>{html.escape(o["municipio"])}</td>'
            f'<td>{html.escape(detalhe)}</td>'
            f'<td>{n_dets}</td>'
            f'{col_pasta}'
            f'</tr>'
        )
    n_cols = 7 if com_pasta else 6
    corpo_tabela = "\n".join(linhas) if linhas else (
        f'<tr><td colspan="{n_cols}" style="text-align:center;color:#7f8c8d;padding:24px">'
        'Nenhuma OS encontrada em OS ATIVAS. Use /nova-os para cadastrar a primeira.'
        '</td></tr>'
    )
    th_pasta = '<th onclick="sortBy(6)">Pasta</th>' if com_pasta else ""

    # Seção de notificações DET encontradas nas pastas mas fora do memory.md.
    itens_novas = [(o["empregador"], n) for o in oss for n in (o.get("novas") or [])]
    secao_novas = ""
    if itens_novas:
        lis = []
        for emp, n in itens_novas:
            partes = [f"<b>{html.escape(emp)}</b>",
                      f"<code>{html.escape(n['arquivo'])}</code>"]
            if n.get("codigo"):
                partes.append(f"código {html.escape(n['codigo'])}")
            if n.get("prazo"):
                partes.append(f"prazo {html.escape(n['prazo'])}")
            if n.get("ciencia"):
                partes.append(f"ciência {html.escape(n['ciencia'])}")
            if n.get("data_arquivo"):
                partes.append(f"arquivo de {html.escape(n['data_arquivo'])}")
            lis.append("<li>" + " · ".join(partes) + "</li>")
        secao_novas = f"""
<div class="wrap">
  <div class="novas">
    <h2>Notificações DET não cadastradas ({len(itens_novas)})</h2>
    <p>PDFs com cara de notificação encontrados nas pastas das OS, sem registro na
    ficha (memory.md) — confira e cadastre com /nova-os ou edite a ficha da OS.</p>
    <ul>
{chr(10).join(lis)}
    </ul>
  </div>
</div>"""

    titulo_art = "<title>Painel AFT</title>\n" if artifact else ""
    rodape = ("AFT Toolkit · painel publicado como artefato · snapshot de "
              f"{hoje.strftime('%d/%m/%Y')} · regenere com a skill /painel."
              if artifact else
              "AFT Toolkit · painel local · regenere com a skill /painel sempre que algo mudar.")

    return f"""{titulo_art}<style>
  * {{ box-sizing: border-box; }}
  body {{ font-family: -apple-system, Segoe UI, Roboto, Arial, sans-serif; margin: 0;
         background: #f4f6f9; color: #1f2d3d; }}
  header {{ background: #1F4E79; color: #fff; padding: 20px 28px; }}
  header h1 {{ margin: 0; font-size: 22px; }}
  header .sub {{ opacity: .8; font-size: 13px; margin-top: 4px; }}
  .cards {{ display: flex; gap: 16px; padding: 20px 28px; flex-wrap: wrap; }}
  .card {{ background: #fff; border-radius: 10px; padding: 16px 20px; min-width: 150px;
          box-shadow: 0 1px 3px rgba(0,0,0,.08); }}
  .card .n {{ font-size: 30px; font-weight: 700; }}
  .card .l {{ font-size: 12px; color: #7f8c8d; text-transform: uppercase; letter-spacing: .04em; }}
  .card.venc .n {{ color: #c0392b; }}
  .card.urg .n {{ color: #e67e22; }}
  .card.nova .n {{ color: #2980b9; }}
  .wrap {{ padding: 0 28px 24px; }}
  table {{ width: 100%; border-collapse: collapse; background: #fff; border-radius: 10px;
          overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,.08); }}
  th, td {{ text-align: left; padding: 11px 14px; font-size: 14px; border-bottom: 1px solid #eef1f4; }}
  th {{ background: #eaf0f6; cursor: pointer; user-select: none; font-size: 12px;
       text-transform: uppercase; letter-spacing: .03em; color: #5a6b7b; }}
  th:hover {{ background: #dde7f1; }}
  tr:last-child td {{ border-bottom: none; }}
  .emp {{ font-weight: 600; }}
  .path {{ font-family: Consolas, monospace; font-size: 11px; color: #7f8c8d; }}
  .dot {{ display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-right: 7px;
         vertical-align: middle; }}
  .novas {{ background: #fff; border-left: 4px solid #2980b9; border-radius: 10px;
           padding: 14px 20px; box-shadow: 0 1px 3px rgba(0,0,0,.08); }}
  .novas h2 {{ margin: 0 0 6px; font-size: 16px; color: #2980b9; }}
  .novas p {{ margin: 0 0 8px; font-size: 13px; color: #5a6b7b; }}
  .novas ul {{ margin: 0; padding-left: 20px; font-size: 14px; }}
  .novas li {{ margin: 4px 0; }}
  .novas code {{ font-size: 12px; background: #f0f3f7; padding: 1px 5px; border-radius: 4px; }}
  footer {{ padding: 0 28px 28px; color: #9aa7b3; font-size: 12px; }}
</style>
<header>
  <h1>Painel AFT — auditorias em andamento</h1>
  <div class="sub">Gerado em {hoje.strftime('%d/%m/%Y')} a partir das fichas locais (memory.md). Somente leitura.</div>
</header>
<div class="cards">
  <div class="card"><div class="n">{n_os}</div><div class="l">OS ativas</div></div>
  <div class="card venc"><div class="n">{n_venc}</div><div class="l">DET vencidos</div></div>
  <div class="card urg"><div class="n">{n_urg}</div><div class="l">DET vencendo (7 dias)</div></div>
  <div class="card nova"><div class="n">{n_novas}</div><div class="l">Notif. não cadastradas</div></div>
</div>
<div class="wrap">
  <table id="t">
    <thead><tr>
      <th onclick="sortBy(0)">Situação</th>
      <th onclick="sortBy(1)">Empregador</th>
      <th onclick="sortBy(2)">CNPJ</th>
      <th onclick="sortBy(3)">Município</th>
      <th onclick="sortBy(4)">Prazo DET mais próximo</th>
      <th onclick="sortBy(5)">Nº DET</th>
      {th_pasta}
    </tr></thead>
    <tbody>
{corpo_tabela}
    </tbody>
  </table>
</div>{secao_novas}
<footer>{rodape}</footer>
<script>
function sortBy(col) {{
  const tb = document.querySelector('#t tbody');
  const rows = Array.from(tb.querySelectorAll('tr'));
  const asc = tb.getAttribute('data-col') !== String(col) || tb.getAttribute('data-asc') !== '1';
  rows.sort((a, b) => {{
    if (col === 4) {{
      return (parseInt(a.dataset.dias) - parseInt(b.dataset.dias)) * (asc ? 1 : -1);
    }}
    const x = a.cells[col].innerText.trim(), y = b.cells[col].innerText.trim();
    return x.localeCompare(y, 'pt-BR') * (asc ? 1 : -1);
  }});
  rows.forEach(r => tb.appendChild(r));
  tb.setAttribute('data-col', col); tb.setAttribute('data-asc', asc ? '1' : '0');
}}
</script>
"""


if __name__ == "__main__":
    sys.exit(main())
