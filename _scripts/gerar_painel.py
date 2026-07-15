#!/usr/bin/env python3
"""
gerar_painel.py — gera um painel HTML local das auditorias do AFT Toolkit.

Varre os memory.md de OS ATIVAS/*/ , extrai os dados de cada OS (empregador,
CNPJ, município, status, prazos de DET, pendências, registro de atividades) e
os autos de infração lavrados (do autos-lavrados.md e, opcionalmente, de um
scan ao vivo do Sistema Auditor), e produz um painel.html autocontido (abre
por duplo-clique, sem servidor) no estilo dashboard:
  - contadores no topo (OS ativas, DETs vencidos, DETs vencendo em <= 7 dias,
    notificações não cadastradas, autos lavrados);
  - um CARD por OS, colorido por urgência, com CNPJ, município, dias desde o
    início, NRs autuadas e o prazo de DET mais urgente;
  - clique no card abre o DETALHE da auditoria: DETs com estado, todos os
    autos de infração lavrados (Nº do AI, ementa, constatação, data), autos
    substituídos, pendências, registro de atividades e notificações de DET
    encontradas na pasta mas ainda sem registro no memory.md.

É um leitor: NUNCA altera os memory.md nem o Sistema Auditor. (Quem edita é
o modo interativo — servir_painel.py — que serve este mesmo HTML por
http://127.0.0.1:8347; aí os cards ganham ações mecânicas: marcar DET
respondida, resolver pendência, registrar atividade, status e embargo.)

Uso:
    python gerar_painel.py [PASTA_OS_ATIVAS] [SAIDA_HTML] [SAIDA_ARTIFACT] [--scan] [--todas]

  PASTA_OS_ATIVAS (opcional): padrão ~/Documents/AFT/OS ATIVAS
  SAIDA_HTML      (opcional): padrão <PASTA_OS_ATIVAS>/../painel.html
  SAIDA_ARTIFACT  (opcional): se informado, grava também uma versão para a
                  tool Artifact do Claude Code (sem <html>/<head>/<body> e sem
                  caminhos locais). Use "" para pular um argumento posicional.
  --scan          (opcional): tenta um scan ao vivo dos autos no Sistema
                  Auditor (pasta PRO — Windows ou Mac+Parallels) chamando o
                  scan_autos.py da skill /autos-lavrados. Se a pasta PRO não
                  estiver acessível (ex.: VM do Parallels desligada), degrada
                  em silêncio para o último autos-lavrados.md de cada OS.
  --todas         (opcional): também mostra OS com status: encerrada (por
                  padrão elas ficam de fora — é um dashboard do que está EM
                  ANDAMENTO). Não confundir com arquivar: a OS encerrada
                  continua em OS ATIVAS/, só sai da grade; mover a pasta para
                  OS ARQUIVADAS/ é organização de disco, feita à parte.

Compatível com os dois esquemas de memory.md em uso:
  - o padrão do toolkit (/nova-os), e
  - o schema v2 do ecossistema Cowork (front-matter com data_inicio,
    data_vencimento, num_trabalhadores, datas ISO nas linhas de DET).

Imprime no stdout um resumo em JSON (para a skill /painel ecoar).
Usa a biblioteca padrão; se o pdfplumber estiver instalado (o /aft-setup
instala), lê a 1ª página dos PDFs para melhorar a detecção de notificações.
"""
from __future__ import annotations

import datetime
import html
import json
import re
import subprocess
import sys
from pathlib import Path

try:
    import pdfplumber  # opcional: detecção pelo conteúdo da 1ª página
except ImportError:
    pdfplumber = None

RE_FM = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
RE_TITULO = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)
RE_CNPJ_BODY = re.compile(r"\*\*CNPJ:\*\*\s*([\d./-]+)")
RE_PRAZO = re.compile(
    r"(?:prazo|entrega\s+at[eé])[:\s]+(\d{2}/\d{2}/\d{4}|\d{4}-\d{2}-\d{2})",
    re.IGNORECASE)
RE_CODIGO_DET = re.compile(r"([A-Z0-9]{6,})")
RE_CHECKBOX = re.compile(r"^-\s*\[([ xX]?)\]\s*(.*)$")
RE_DATA_ISO = re.compile(r"(\d{4})-(\d{2})-(\d{2})")
RE_DATA_BR = re.compile(r"(\d{2})/(\d{2})/(\d{4})")
RE_NR = re.compile(r"NR[-\s]?0?(\d{1,2})\b", re.IGNORECASE)

# Blocos do autos-lavrados.md (formato da skill /autos-lavrados).
RE_BLOCO_AI = re.compile(r"^###\s+N[ºo°]?\s*([\d.\-]+)\s*$", re.MULTILINE)

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
SCAN_TIMEOUT = 180  # segundos por OS no scan ao vivo


def argv_posicionais() -> list[str]:
    return [a for a in sys.argv[1:] if a not in ("--scan", "--todas")]


def quer_scan() -> bool:
    return "--scan" in sys.argv[1:]


def quer_todas() -> bool:
    return "--todas" in sys.argv[1:]


def home_os() -> Path:
    pos = argv_posicionais()
    if len(pos) >= 1 and pos[0].strip():
        return Path(pos[0])
    return Path.home() / "Documents" / "AFT" / "OS ATIVAS"


def saida_html(base: Path) -> Path:
    pos = argv_posicionais()
    if len(pos) >= 2 and pos[1].strip():
        return Path(pos[1])
    return base.parent / "painel.html"


def saida_artifact() -> Path | None:
    pos = argv_posicionais()
    if len(pos) >= 3 and pos[2].strip():
        return Path(pos[2])
    return None


def parse_fm(fm: str, chave: str) -> str | None:
    m = re.search(rf"^{chave}\s*:\s*(.+?)\s*$", fm, re.MULTILINE)
    if not m:
        return None
    v = m.group(1).strip().strip('"').strip("'")
    return None if v in ("", "null", "~") else v


def parse_data(s: str) -> datetime.date | None:
    """Aceita dd/mm/aaaa e aaaa-mm-dd."""
    m = RE_DATA_BR.search(s)
    if m:
        d, mo, y = (int(x) for x in m.groups())
    else:
        m = RE_DATA_ISO.search(s)
        if not m:
            return None
        y, mo, d = (int(x) for x in m.groups())
    try:
        return datetime.date(y, mo, d)
    except ValueError:
        return None


def fmt_cnpj(digs: str) -> str:
    if len(digs) == 14:
        return f"{digs[0:2]}.{digs[2:5]}.{digs[5:8]}/{digs[8:12]}-{digs[12:]}"
    if len(digs) == 11:
        return f"{digs[0:3]}.{digs[3:6]}.{digs[6:9]}-{digs[9:]}"
    return digs


def extrair_secao(corpo: str, titulo: str) -> str:
    """Devolve o texto da seção '## titulo' até o próximo '## ' (ou o fim)."""
    m = re.search(rf"^##\s+{re.escape(titulo)}\s*$", corpo, re.MULTILINE)
    if not m:
        return ""
    inicio = m.end()
    prox = re.search(r"^##\s+", corpo[inicio:], re.MULTILINE)
    return corpo[inicio: inicio + prox.start()] if prox else corpo[inicio:]


def parse_memory(path: Path) -> dict:
    """Extrai dados de um memory.md — tolerante aos dois esquemas em uso."""
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
        m = re.search(r"(\d{11,14})\s*$", pasta)
        cnpj = m.group(1) if m else ""

    # Campos extras do schema v2 (ficam vazios no esquema padrão — sem erro).
    data_inicio = parse_data(parse_fm(fm, "data_inicio") or "")
    data_vencimento = parse_data(parse_fm(fm, "data_vencimento") or "")
    num_trab = parse_fm(fm, "num_trabalhadores")
    ri = parse_fm(fm, "ri") or parse_fm(fm, "os") or ""

    # DETs — uma entrada por linha checkbox da seção.
    dets = []
    secao = extrair_secao(corpo, "Notificações DET") or extrair_secao(corpo, "Notificacoes DET")
    for linha in secao.splitlines():
        cb = RE_CHECKBOX.match(linha.strip())
        if not cb:
            continue
        feito = cb.group(1).strip().lower() == "x"
        resto = re.sub(r"<!--.*?-->", "", cb.group(2)).strip()
        prazo_m = RE_PRAZO.search(resto)
        prazo = parse_data(prazo_m.group(1)) if prazo_m else None
        cod_m = RE_CODIGO_DET.match(resto)
        codigo = cod_m.group(1) if cod_m else None
        if prazo or codigo:
            dets.append({"codigo": codigo, "prazo": prazo, "feito": feito,
                         "linha": resto})

    # Pendências (checkbox) — só as em aberto interessam ao painel.
    pendencias = []
    for linha in extrair_secao(corpo, "Pendências").splitlines():
        cb = RE_CHECKBOX.match(linha.strip())
        if cb and cb.group(1).strip().lower() != "x":
            pendencias.append(cb.group(2).strip())

    # Registro de atividades (tabela markdown).
    atividades = []
    for linha in extrair_secao(corpo, "Registro de atividades").splitlines():
        celulas = [c.strip() for c in linha.strip().strip("|").split("|")]
        if len(celulas) >= 2 and parse_data(celulas[0]):
            atividades.append({"data": celulas[0], "acao": celulas[1],
                               "detalhe": celulas[2] if len(celulas) > 2 else ""})

    # Seção de autos do memory.md (fallback p/ chips de NR quando não há
    # autos-lavrados.md nem scan).
    autos_mem = extrair_secao(corpo, "Autos lavrados")

    return {
        "pasta": pasta,
        "caminho": str(path.parent),
        "empregador": empregador,
        "cnpj": cnpj,
        "municipio": parse_fm(fm, "municipio") or "",
        "status": parse_fm(fm, "status") or "em_andamento",
        "embargo": parse_fm(fm, "embargo_interdicao") or "",
        "ri": ri,
        "num_trabalhadores": num_trab,
        "data_inicio": data_inicio,
        "data_vencimento": data_vencimento,
        "dets": dets,
        "pendencias": pendencias,
        "atividades": atividades,
        "autos_mem": autos_mem,
        "memoria": texto,
    }


def parse_autos_lavrados_md(pasta: Path) -> dict:
    """Lê o autos-lavrados.md da OS (formato da skill /autos-lavrados).
    Devolve {autos, substituidos, pendentes, gerado_em}."""
    arq = pasta / "autos-lavrados.md"
    out = {"autos": [], "substituidos": [], "pendentes": [], "gerado_em": None}
    if not arq.exists():
        return out
    texto = arq.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"Snapshot gerado em (\d{4}-\d{2}-\d{2})", texto)
    if m:
        out["gerado_em"] = m.group(1)

    # Blocos "### Nº <AI>" do detalhamento.
    blocos = RE_BLOCO_AI.split(texto)  # [antes, ai1, corpo1, ai2, corpo2, ...]
    for i in range(1, len(blocos) - 1, 2):
        numero_ai, corpo = blocos[i].strip(), blocos[i + 1]
        auto = {"numero_ai": numero_ai, "ementa": "", "base": "",
                "descricao": "", "constatacao": "", "data": "",
                "status_dup": "unico"}
        m = re.search(r"\*\*Ementa\s+([\d\-]+)(?:\s*[·—-]\s*([^*]*))?\*\*", corpo)
        if m:
            auto["ementa"] = m.group(1)
            auto["base"] = (m.group(2) or "").strip()
        m = re.search(r"\*\*Descrição da ementa:\*\*\s*(.+)", corpo)
        if m:
            auto["descricao"] = m.group(1).strip()
        m = re.search(r"\*\*Constatação:\*\*\s*(.+)", corpo)
        if m:
            auto["constatacao"] = m.group(1).strip()
        m = re.search(r"\*\*Lavrado em:\*\*\s*(.+)", corpo)
        if m:
            auto["data"] = m.group(1).strip()
        out["autos"].append(auto)

    sec = extrair_secao(texto, "Autos substituídos (presumidamente cancelados)")
    out["substituidos"] = [l.strip().lstrip("- ").strip() for l in sec.splitlines()
                           if l.strip().startswith("-")]
    sec = extrair_secao(texto, "Pendentes de transmissão")
    out["pendentes"] = [l.strip().lstrip("- ").strip() for l in sec.splitlines()
                        if l.strip().startswith("-") and "nenhum" not in l.lower()]
    return out


def parse_inspecao_fisica(pasta: Path) -> dict:
    """Lê o inspecao-fisica.md da OS (relato de campo da /inspecao-fisica) e
    devolve {data, bullets}. ATENÇÃO: pode conter nome/CPF de trabalhador — só
    entra na versão LOCAL do painel, nunca na versão publicada como Artifact."""
    arq = pasta / "inspecao-fisica.md"
    if not arq.exists():
        return {}
    try:
        texto = arq.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return {}
    data = ""
    m = re.search(r"\*\*Data da inspe[çc][ãa]o:\*\*\s*(.+)", texto)
    if m:
        data = m.group(1).strip()
    bullets = [l.strip()[1:].strip().rstrip(";").strip()
               for l in texto.splitlines() if l.strip().startswith("- ")]
    return {"data": data, "bullets": bullets} if bullets else {}


def scan_ao_vivo(os_: dict) -> list[dict] | None:
    """Roda o scan_autos.py da skill /autos-lavrados para a OS (se houver
    identificador com >= 8 dígitos). Devolve a lista de autos VÁLIDOS do
    Sistema Auditor, ou None se o scan não foi possível (sem identificador,
    pasta PRO inacessível, PDFs ausentes...) — o chamador degrada para o .md."""
    ident = os_["cnpj"]
    if len(ident) < 8:
        return None
    script = (Path(__file__).resolve().parent.parent
              / "autos-lavrados" / "scripts" / "scan_autos.py")
    if not script.exists():
        return None
    try:
        proc = subprocess.run(
            [sys.executable, str(script), os_["empregador"], ident],
            capture_output=True, timeout=SCAN_TIMEOUT, text=True)
        dados = json.loads(proc.stdout)
    except Exception:
        return None
    if dados.get("errors") or not dados.get("pasta_auditor"):
        return None
    autos = []
    for a in dados.get("autos", []):
        if a.get("status_duplicidade") == "cancelado_presumido":
            continue
        autos.append({
            "numero_ai": a.get("numero_ai") or "",
            "ementa": a.get("ementa_num") or "",
            "base": "",
            "descricao": " ".join((a.get("ementa_descricao") or "").split())[:400],
            "constatacao": "",
            "data": a.get("data_lavratura") or "",
            "status_dup": a.get("status_duplicidade") or "unico",
        })
    return autos


RE_AUTO_MEM = re.compile(
    r"^-\s*\[[xX]\]\s*Ementa\s+([\d\-]+)\s*[—–-]\s*(.*?)\s*[—–-]\s*AI\s+([\d.\-]+)"
    r"(?:\s*\(lavrado em\s+(\d{2}/\d{2}/\d{4})\))?", re.MULTILINE)


def autos_do_memory(autos_mem: str) -> list[dict]:
    """Fallback fraco: linhas '- [x] Ementa X — resumo — AI Y' da seção
    ## Autos lavrados do memory.md (escritas por /autos-lavrados e /organiza-os),
    para quando não há autos-lavrados.md nem scan ao vivo."""
    autos = []
    for m in RE_AUTO_MEM.finditer(autos_mem):
        autos.append({"numero_ai": m.group(3), "ementa": m.group(1),
                      "base": "", "descricao": m.group(2).strip(),
                      "constatacao": "", "data": m.group(4) or "",
                      "status_dup": "unico"})
    return autos


def mesclar_autos(md: dict, vivo: list[dict] | None,
                  autos_mem: str = "") -> tuple[list[dict], str]:
    """Mescla o scan ao vivo (lista fria, sempre fresca) com o
    autos-lavrados.md (constatações redigidas). Chave: número do AI.
    Sem nenhum dos dois, cai nas linhas [x] do memory.md."""
    if vivo is None:
        if md["autos"]:
            fonte = "autos-lavrados.md"
            if md["gerado_em"]:
                fonte += f" (snapshot de {md['gerado_em']})"
            return md["autos"], fonte
        do_mem = autos_do_memory(autos_mem)
        if do_mem:
            return do_mem, "memory.md (rode /autos-lavrados para detalhar)"
        return [], ""
    por_ai = {a["numero_ai"]: a for a in md["autos"]}
    mesclados = []
    for a in vivo:
        base = dict(a)
        rico = por_ai.get(a["numero_ai"])
        if rico:
            base["constatacao"] = rico.get("constatacao", "")
            base["base"] = rico.get("base", "")
            if rico.get("descricao"):
                base["descricao"] = rico["descricao"]
        mesclados.append(base)
    fonte = "scan ao vivo do Sistema Auditor"
    if md["autos"]:
        fonte += " + autos-lavrados.md"
    return mesclados, fonte


def extrair_nrs(autos: list[dict], autos_mem: str) -> list[str]:
    vistos: dict[str, None] = {}
    for a in autos:
        for campo in ("base", "descricao"):
            for m in RE_NR.finditer(a.get(campo) or ""):
                vistos.setdefault(f"NR-{int(m.group(1)):02d}")
    if not vistos:
        for m in RE_NR.finditer(autos_mem):
            vistos.setdefault(f"NR-{int(m.group(1)):02d}")
    return list(vistos)[:4]


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


# ────────────────────────────────────────────────────────────────────────────
# Renderização — dashboard de cards + painel de detalhe, autocontido.
# Paleta inspirada no SisOS (cream/coral/serif), sem fontes nem libs externas.
# ────────────────────────────────────────────────────────────────────────────

CSS = """
:root{--cream:#F0EEE6;--paper:#FAF9F5;--coral:#CC785C;--coral-deep:#B0593E;
--t1:#141413;--t2:#5A574E;--t3:#8F8B7D;--bd:#DDD9CC;--bds:#E8E4D6;
--teal:#4F8A7C;--serif:'Source Serif 4',Georgia,'Times New Roman',serif;}
*{box-sizing:border-box}
body{margin:0;background:var(--cream);color:var(--t1);
font:15px/1.5 var(--serif);padding:28px clamp(14px,4vw,48px) 60px}
h1{font-size:26px;font-weight:500;margin:0}
h1 em{color:var(--coral);font-style:italic}
.sub{color:var(--t3);font-style:italic;font-size:13px;margin:2px 0 18px}
.contadores{display:flex;gap:12px;flex-wrap:wrap;margin-bottom:24px}
.contador{background:var(--paper);border:1px solid var(--bds);border-radius:10px;
padding:10px 18px;min-width:118px}
.contador b{display:block;font-size:24px;line-height:1.1}
.contador span{font-size:12px;color:var(--t2)}
.contador.alerta b{color:var(--coral-deep)}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:14px}
.card{background:var(--paper);border:1px solid var(--bds);border-left:4px solid var(--teal);
border-radius:10px;padding:14px 16px;cursor:pointer;transition:box-shadow .15s}
.card:hover{box-shadow:0 3px 14px rgba(20,20,19,.10)}
.card.urgente,.card.vencido{border-left-color:var(--coral-deep)}
.card.sem-prazo{border-left-color:var(--bd)}
.card h2{font-size:16px;font-weight:600;margin:0 0 2px;line-height:1.25}
.card .meta{font-size:12.5px;color:var(--t2)}
.badge{display:inline-block;font-size:11.5px;border-radius:20px;padding:2px 10px;
background:#E4EEEB;color:var(--teal);margin-top:8px}
.badge.vencido,.badge.urgente{background:#F5E4E0;color:var(--coral-deep)}
.badge.sem-prazo{background:var(--bds);color:var(--t3)}
.chips{margin-top:8px;min-height:10px}
.chip{display:inline-block;font-size:11px;background:#EFE2D5;color:var(--coral-deep);
border-radius:6px;padding:1px 7px;margin:0 4px 4px 0}
.rodape-card{display:flex;justify-content:space-between;gap:8px;margin-top:10px;
font-size:12px;color:var(--t3)}
.aviso-vazio{background:var(--paper);border:1px dashed var(--bd);border-radius:10px;
padding:26px;text-align:center;color:var(--t3)}
/* Detalhe — modal central amplo */
#veu{display:none;position:fixed;inset:0;background:rgba(20,20,19,.55);z-index:8}
#detalhe{display:none;position:fixed;top:3vh;left:50%;transform:translateX(-50%);
z-index:9;width:min(1060px,95vw);max-height:94vh;background:var(--paper);
border:1px solid var(--bd);border-radius:14px;
box-shadow:0 24px 70px rgba(20,20,19,.35);overflow-y:auto;padding:28px clamp(18px,3vw,40px) 44px}
#detalhe.aberto,#veu.aberto{display:block}
#detalhe h2{font-size:24px;margin:0 6px 2px 0}
#detalhe .fechar{position:sticky;top:-4px;float:right;background:var(--cream);
border:1px solid var(--bd);border-radius:8px;padding:6px 14px;cursor:pointer;
font:inherit;color:var(--t2);z-index:1}
#detalhe h3{font-size:12.5px;letter-spacing:.08em;text-transform:uppercase;
color:var(--t3);border-bottom:1px solid var(--bds);padding-bottom:4px;margin:26px 0 10px}
#detalhe .meta{font-size:14px;color:var(--t2)}
.autos-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:10px}
.insp{background:var(--cream);border:1px solid var(--bds);border-radius:8px;
padding:12px 16px 12px 34px;margin:0}
.insp li{margin-bottom:8px;line-height:1.45}
.auto{border:1px solid var(--bds);border-radius:8px;padding:10px 14px;margin-bottom:10px;
background:var(--cream)}
.auto b.num{color:var(--coral-deep);font-size:15px}
.auto .em{font-size:12.5px;color:var(--t2)}
.auto p{margin:6px 0 0;font-size:13.5px}
.auto .quando{font-size:12px;color:var(--t3);margin-top:4px}
ul.lista{margin:0;padding-left:18px;font-size:13.5px}
ul.lista li{margin-bottom:5px}
/* Notificações DET no detalhe: coral só para o que realmente aperta o prazo. */
.det-ok{color:var(--teal)}
.det-aberto{color:var(--t1)}
.det-aberto.vencido,.det-aberto.urgente{color:var(--coral-deep)}
.selo{display:inline-block;font-size:11px;border-radius:20px;padding:1px 8px;
margin-left:6px;background:var(--bds);color:var(--t3);white-space:nowrap}
.selo.vencido,.selo.urgente{background:#F5E4E0;color:var(--coral-deep)}
/* Seções sem conteúdo: presentes (informam ausência) mas discretas. */
#detalhe h3.vazia{color:var(--bd);border-bottom-color:var(--bds);margin-bottom:4px}
#detalhe h3.vazia + .vazio{margin:0 0 4px}
table.ativ{width:100%;border-collapse:collapse;font-size:12.5px}
table.ativ td{border-top:1px solid var(--bds);padding:5px 8px;vertical-align:top}
table.ativ td:first-child{white-space:nowrap;color:var(--t3)}
.vazio{color:var(--t3);font-style:italic;font-size:13px}
.fonte{font-size:11.5px;color:var(--t3);margin-top:4px;word-break:break-all}
.pasta-btn{font:11.5px var(--serif);background:none;border:none;padding:2px 0;
cursor:pointer;color:var(--t3);text-decoration:underline;text-underline-offset:2px}
.pasta-btn:hover{color:var(--coral-deep)}
footer{margin-top:34px;color:var(--t3);font-size:12px}
/* Modo interativo (servidor local) + botões de copiar comando */
.chip.emb{background:#F5E4E0;color:var(--coral-deep)}
.mini{font:12px var(--serif);background:var(--paper);border:1px solid var(--bd);
border-radius:6px;padding:1px 9px;margin-left:8px;cursor:pointer;color:var(--t2)}
.mini:hover{border-color:var(--coral);color:var(--coral-deep)}
.acoes{display:flex;gap:14px;flex-wrap:wrap;align-items:center;margin:14px 0 2px;
background:var(--cream);border:1px solid var(--bds);border-radius:8px;padding:10px 14px;
font-size:13px}
.acoes label{color:var(--t3);font-size:12px}
.acoes select,.acoes input{font:13px var(--serif);background:var(--paper);
border:1px solid var(--bd);border-radius:6px;padding:3px 8px;color:var(--t1)}
.acoes input{min-width:220px}
.ri-tag{font-weight:700;color:var(--t1)}
.cmds{display:flex;gap:8px;flex-wrap:wrap;margin-top:10px;align-items:center}
.cmds .rot{flex-basis:100%;font-size:11px;letter-spacing:.07em;text-transform:uppercase;
color:var(--t3)}
.cmds button{font:12.5px var(--serif);background:var(--paper);border:1px solid var(--bd);
border-radius:8px;padding:5px 12px;cursor:pointer;color:var(--t2);position:relative}
.cmds button:hover{border-color:var(--coral);color:var(--coral-deep)}
.cmds button::after{content:attr(data-tip);position:absolute;top:calc(100% + 8px);left:0;
width:300px;max-width:70vw;background:var(--t1);color:var(--cream);font-size:12px;
line-height:1.45;padding:9px 12px;border-radius:8px;z-index:30;display:none;
text-align:left;white-space:normal;box-shadow:0 8px 24px rgba(20,20,19,.3);
pointer-events:none}
.cmds button:hover::after{display:block}
#aviso-copiado{position:fixed;bottom:22px;left:50%;transform:translateX(-50%);
background:var(--t1);color:var(--cream);border-radius:8px;padding:8px 18px;
font-size:13px;z-index:20;display:none}
@media (prefers-color-scheme: dark){
:root{--cream:#191917;--paper:#211F1C;--t1:#EDEAE0;--t2:#B5B0A1;--t3:#8F8B7D;
--bd:#3A372F;--bds:#2E2B25}
.badge{background:#233530}.chip{background:#3A2C22}
.badge.vencido,.badge.urgente{background:#3D2521}
.card:hover{box-shadow:0 3px 14px rgba(0,0,0,.5)}
}
"""

JS = """
const P=document.getElementById('detalhe'),V=document.getElementById('veu');
// Modo interativo: só quando o painel vem do servidor local (servir_painel.py).
const ATIVO=location.protocol==='http:'&&['127.0.0.1','localhost'].includes(location.hostname);
function esc(s){const d=document.createElement('span');d.textContent=s==null?'':String(s);return d.innerHTML}
function aviso(t){let a=document.getElementById('aviso-copiado');
 if(!a){a=document.createElement('div');a.id='aviso-copiado';document.body.appendChild(a)}
 a.textContent=t;a.style.display='block';clearTimeout(a._t);
 a._t=setTimeout(()=>a.style.display='none',2200)}
async function api(p){
 try{const r=await fetch('/api/acao',{method:'POST',
  headers:{'Content-Type':'application/json'},body:JSON.stringify(p)});
  const j=await r.json();
  if(!j.ok){aviso('Erro: '+(j.erro||'?'));return}
  sessionStorage.setItem('painel-reabrir',p.pasta);location.reload();
 }catch(e){aviso('Servidor do painel não respondeu — abra pelo http://127.0.0.1:8347')}}
function copia(t){
 const fim=()=>aviso('Copiado — cole no Claude Code: '+t);
 if(navigator.clipboard&&navigator.clipboard.writeText){
  navigator.clipboard.writeText(t).then(fim).catch(()=>copiaVelho(t,fim));
 }else copiaVelho(t,fim)}
function copiaVelho(t,fim){const ta=document.createElement('textarea');ta.value=t;
 document.body.appendChild(ta);ta.select();
 try{document.execCommand('copy');fim()}catch(e){aviso('Não consegui copiar')}
 ta.remove()}
// Ações mecânicas — referenciam DATA por índice (nada de string embutida no HTML).
// Legendas dos comandos: resumo de cada skill vindo da arquitetura do toolkit.
const CMDS=[
 ['/inspecao-fisica','Transforma a narrativa ditada da visita num relato de campo estruturado (inspecao-fisica.md), fiel e sem enquadramento.'],
 ['/inspecao-inicial','Lê o relato de campo, identifica NR/ementa e redige os autos de infração (NRs + CLT), com gate de dupla visita.'],
 ['/gera-ai','Empacota os autos redigidos no TXT importável pelo Sistema Auditor, com anexos em PDF e pseudonimização reversível.'],
 ['/autos-lavrados','Confere no Sistema Auditor o que já foi transmitido e marca [x]/[ ] no memory.md; cada auto identificado pelo número do AI.'],
 ['/det-630','Auto por omissão de documentos notificados via DET (ementa 001168-1, art. 630 §4º CLT).'],
 ['/tn-nco','Redige a Notificação para Correção de Irregularidades, texto pronto para colar no DET, item por item.'],
 ['/aft-rt-rgi','Relatório Técnico de Interdição/Embargo em .docx + autos derivados das ementas (risco grave e iminente, NR-03).'],
 ['/sfitweb-rel','Relatório Final Simplificado consolidando autos, termos e notificações.']];
function copiaCmd(i,k){copia(CMDS[k][0]+' — OS '+DATA.os[i].empregador)}
function copiaCaminho(i){copia(DATA.os[i].caminho)}
function agDet(i,k){const o=DATA.os[i];api({acao:'det',pasta:o.pasta,codigo:o.dets[k].codigo})}
function agPend(i,k){const o=DATA.os[i];api({acao:'pendencia',pasta:o.pasta,texto:o.pendencias[k]})}
function agStatus(i,v){api({acao:'status',pasta:DATA.os[i].pasta,valor:v})}
function agEmbargo(i,k){api({acao:'embargo',pasta:DATA.os[i].pasta,estado:k?'suspenso':'vigente'})}
function agAtiv(i){const el=document.getElementById('ativ-txt');const v=(el.value||'').trim();
 if(v)api({acao:'atividade',pasta:DATA.os[i].pasta,texto:v})}
function abre(i){
 const o=DATA.os[i];let h='<button class="fechar" onclick="fecha()">fechar ✕</button>';
 h+='<h2>'+esc(o.empregador)+'</h2>';
 h+='<div class="meta">'+esc(o.cnpj_fmt||'CNPJ não informado')+
    (o.municipio?' · '+esc(o.municipio):'')+
    (o.ri?' · <span class="ri-tag">RI '+esc(o.ri)+'</span>':'')+'</div>';
 const l2=[];
 if(o.inicio)l2.push('Início: '+esc(o.inicio)+' ('+esc(o.ha_dias)+')');
 if(o.vencimento)l2.push('Vence: '+esc(o.vencimento));
 if(o.num_trabalhadores)l2.push(esc(o.num_trabalhadores)+' trabalhadores');
 if(o.embargo)l2.push('Embargo/interdição: '+esc(o.embargo));
 if(l2.length)h+='<div class="meta">'+l2.join(' · ')+'</div>';
 if(o.caminho)h+='<div><button class="pasta-btn" onclick="copiaCaminho('+i+')">copiar caminho da pasta</button></div>';
 if(ATIVO&&o.pasta){
  const st=['em_andamento','aguardando_resposta','encerrada'];
  if(o.status&&!st.includes(o.status))st.unshift(o.status);
  h+='<div class="acoes"><span><label>status </label><select onchange="agStatus('+i+',this.value)">'+
     st.map(s=>'<option'+(s===o.status?' selected':'')+'>'+esc(s)+'</option>').join('')+'</select></span>'+
     '<span><label>embargo/interdição </label>'+
     '<button class="mini" onclick="agEmbargo('+i+',0)">vigente</button>'+
     '<button class="mini" onclick="agEmbargo('+i+',1)">suspenso</button></span>'+
     '<span><input id="ativ-txt" placeholder="registrar atividade de hoje..." '+
     'onkeydown="if(event.key===&quot;Enter&quot;)agAtiv('+i+')">'+
     '<button class="mini" onclick="agAtiv('+i+')">registrar</button></span></div>';}
 h+='<div class="cmds"><span class="rot">comandos prontos para o Claude Code — clique para copiar, passe o mouse para a legenda</span>'+
    CMDS.map((c,k)=>'<button data-tip="'+esc(c[1])+'" onclick="copiaCmd('+i+','+k+')">'+
    esc(c[0])+'</button>').join('')+'</div>';
 h+='<h3'+(o.dets.length?'':' class="vazia"')+'>Notificações DET ('+o.dets.length+')</h3>';
 h+=o.dets.length?'<ul class="lista">'+o.dets.map((d,k)=>'<li class="'+
    (d.feito?'det-ok':'det-aberto '+esc(d.urg))+'">'+
    (d.feito?'✔ ':'◻ ')+esc(d.linha)+
    (d.selo?'<span class="selo '+esc(d.urg)+'">'+esc(d.selo)+'</span>':'')+
    (ATIVO&&o.pasta&&d.codigo?'<button class="mini" onclick="agDet('+i+','+k+')">'+
     (d.feito?'desmarcar':'marcar como checado')+'</button>':'')+
    '</li>').join('')+'</ul>':'<p class="vazio">nenhuma registrada</p>';
 if(o.novas.length){h+='<h3>Notificações na pasta sem registro ('+o.novas.length+')</h3><ul class="lista">'+
    o.novas.map(n=>'<li>'+esc(n.codigo||n.arquivo)+(n.prazo?' — prazo '+esc(n.prazo):'')+
    (n.ciencia?' — ciência '+esc(n.ciencia):'')+'</li>').join('')+'</ul>';}
 if(o.inspecao && o.inspecao.bullets && o.inspecao.bullets.length){
    h+='<h3>Inspeção física'+(o.inspecao.data?' — '+esc(o.inspecao.data):'')+'</h3>';
    h+='<ul class="insp">'+o.inspecao.bullets.map(b=>'<li>'+esc(b)+'</li>').join('')+'</ul>';}
 h+='<h3'+(o.autos.length?'':' class="vazia"')+'>Autos de infração lavrados ('+o.autos.length+')</h3>';
 if(o.fonte_autos&&o.autos.length)h+='<div class="fonte">fonte: '+esc(o.fonte_autos)+'</div>';
 h+=o.autos.length?'<div class="autos-grid">'+o.autos.map(a=>'<div class="auto"><b class="num">Nº '+esc(a.numero_ai)+'</b>'+
    ' <span class="em">Ementa '+esc(a.ementa)+(a.base?' · '+esc(a.base):'')+'</span>'+
    (a.descricao?'<p>'+esc(a.descricao)+'</p>':'')+
    (a.constatacao?'<p><b>Constatação:</b> '+esc(a.constatacao)+'</p>':'')+
    (a.data?'<div class="quando">Lavrado em '+esc(a.data)+'</div>':'')+'</div>').join('')+'</div>'
    :'<p class="vazio">nenhum auto lavrado encontrado</p>';
 if(o.substituidos.length){h+='<h3>Autos substituídos (cancelados)</h3><ul class="lista">'+
    o.substituidos.map(s=>'<li>'+esc(s)+'</li>').join('')+'</ul>';}
 if(o.autos_pendentes.length){h+='<h3>Pendentes de transmissão</h3><ul class="lista">'+
    o.autos_pendentes.map(s=>'<li>'+esc(s)+'</li>').join('')+'</ul>';}
 if(o.pendencias.length){h+='<h3>Pendências da OS</h3><ul class="lista">'+
    o.pendencias.map((s,k)=>'<li>◻ '+esc(s)+
    (ATIVO&&o.pasta?'<button class="mini" onclick="agPend('+i+','+k+')">resolver</button>':'')+
    '</li>').join('')+'</ul>';}
 if(o.atividades.length){h+='<h3>Registro de atividades (recentes)</h3><table class="ativ">'+
    o.atividades.map(a=>'<tr><td>'+esc(a.data)+'</td><td>'+esc(a.acao)+
    (a.detalhe?' — '+esc(a.detalhe):'')+'</td></tr>').join('')+'</table>';}
 P.innerHTML=h;P.classList.add('aberto');V.classList.add('aberto');P.scrollTop=0;
}
function fecha(){P.classList.remove('aberto');V.classList.remove('aberto')}
V.addEventListener('click',fecha);
document.addEventListener('keydown',e=>{if(e.key==='Escape')fecha()});
// Depois de uma ação, reabre o mesmo card (a página recarrega para refletir a edição).
(function(){const alvo=sessionStorage.getItem('painel-reabrir');
 if(!alvo)return;sessionStorage.removeItem('painel-reabrir');
 const i=DATA.os.findIndex(o=>o.pasta===alvo);if(i>=0)abre(i)})();
"""


def datas_para_br(texto: str) -> str:
    """Troca datas ISO (aaaa-mm-dd) por dd/mm/aaaa NA EXIBIÇÃO. As fichas do
    schema v2 usam ISO nas linhas de DET e o resto do painel usa dd/mm/aaaa;
    misturar os dois no mesmo modal confunde. Os memory.md não são tocados."""
    return RE_DATA_ISO.sub(lambda m: f"{m.group(3)}/{m.group(2)}/{m.group(1)}", texto)


def dias_humano(d: datetime.date | None, hoje: datetime.date) -> str:
    if not d:
        return ""
    n = (hoje - d).days
    if n == 0:
        return "hoje"
    if n == 1:
        return "ontem"
    if n < 0:
        return "em breve"
    return f"há {n} dias"


def badge_os(os_: dict, hoje: datetime.date) -> tuple[str, str]:
    """(classe css, rótulo) do card: urgência do DET aberto + vencimento da OS."""
    if os_["data_vencimento"]:
        dv = (os_["data_vencimento"] - hoje).days
        if dv < 0:
            return "vencido", "OS vencida"
        if dv <= 30 and (os_["dias_top"] is None or dv < os_["dias_top"]):
            return "urgente", f"OS vence em {dv}d"
    d = os_["dias_top"]
    if d is None:
        return "sem-prazo", "sem prazo aberto"
    if d < 0:
        return "vencido", f"DET vencido há {-d}d"
    if d == 0:
        return "urgente", "DET vence HOJE"
    if d <= 7:
        return "urgente", f"DET vence em {d}d"
    return "futuro", f"DET em {d}d"


def selo_det(d: dict, hoje: datetime.date) -> tuple[str, str]:
    """(classe, rótulo) da urgência de UMA notificação DET, para o detalhe.
    A grade já mostra a urgência da OS; aqui o AFT vê de qual DET ela vem."""
    if d["feito"]:
        return "ok", ""
    if not d["prazo"]:
        return "neutro", ""
    n = (d["prazo"] - hoje).days
    if n < 0:
        return "vencido", f"vencido há {-n}d"
    if n == 0:
        return "urgente", "vence HOJE"
    if n <= 7:
        return "urgente", f"vence em {n}d"
    return "neutro", f"em {n}d"


def montar_json_os(oss: list[dict], hoje: datetime.date, com_pasta: bool) -> list[dict]:
    out = []
    for o in oss:
        out.append({
            "empregador": o["empregador"],
            "cnpj_fmt": fmt_cnpj(o["cnpj"]) if o["cnpj"] else "",
            "municipio": o["municipio"],
            # Nome da pasta = chave das ações do modo interativo (só local).
            "pasta": o["pasta"] if com_pasta else "",
            "status": o["status"],
            "embargo": o["embargo"],
            "ri": o["ri"],
            "num_trabalhadores": o["num_trabalhadores"] or "",
            "inicio": o["data_inicio"].strftime("%d/%m/%Y") if o["data_inicio"] else "",
            "ha_dias": dias_humano(o["data_inicio"], hoje),
            "vencimento": o["data_vencimento"].strftime("%d/%m/%Y") if o["data_vencimento"] else "",
            "caminho": o["caminho"] if com_pasta else "",
            # Relato de campo tem PII (nomes/CPF): só na versão local (com_pasta),
            # nunca na versão publicada como Artifact.
            "inspecao": (o.get("inspecao_fisica") or {}) if com_pasta else {},
            "dets": [{"codigo": d["codigo"], "feito": d["feito"],
                      "linha": datas_para_br(d["linha"]),
                      "urg": selo_det(d, hoje)[0], "selo": selo_det(d, hoje)[1]}
                     for d in o["dets"]],
            "novas": o.get("novas") or [],
            "autos": o["autos"],
            "fonte_autos": o["fonte_autos"],
            "substituidos": o["autos_lavrados_md"]["substituidos"],
            "autos_pendentes": o["autos_lavrados_md"]["pendentes"],
            "pendencias": [datas_para_br(p) for p in o["pendencias"]],
            "atividades": [{"data": datas_para_br(a["data"]), "acao": a["acao"],
                            "detalhe": datas_para_br(a["detalhe"])}
                           for a in o["atividades"][-12:][::-1]],
        })
    return out


def render_miolo(oss, hoje, n_venc, n_urg, n_novas, n_autos,
                 com_pasta: bool, artifact: bool) -> str:
    cards = []
    for i, o in enumerate(oss):
        classe, rotulo = badge_os(o, hoje)
        chips = "".join(f'<span class="chip">{html.escape(nr)}</span>' for nr in o["nrs"])
        if o["embargo"]:
            chips += f'<span class="chip emb">⛔ {html.escape(o["embargo"][:42])}</span>'
        dets_abertos = sum(1 for d in o["dets"] if not d["feito"])
        cards.append(f"""
<div class="card {classe}" onclick="abre({i})">
  <h2>{html.escape(o["empregador"])}</h2>
  <div class="meta">{html.escape(fmt_cnpj(o["cnpj"]) if o["cnpj"] else "CNPJ não informado")}{(" · " + html.escape(o["municipio"])) if o["municipio"] else ""}</div>
  <span class="badge {classe}">{html.escape(rotulo)}</span>
  <div class="chips">{chips}</div>
  <div class="rodape-card">
    <span>{len(o["autos"])} auto(s) · {dets_abertos} DET(s) aberto(s)</span>
    <span>{html.escape(dias_humano(o["data_inicio"], hoje))}</span>
  </div>
</div>""")

    grade = ("".join(cards) if cards else
             '<div class="aviso-vazio">Nenhuma OS encontrada em OS ATIVAS. '
             'Use /nova-os para cadastrar a primeira.</div>')
    dados = {"os": montar_json_os(oss, hoje, com_pasta)}
    json_js = json.dumps(dados, ensure_ascii=False).replace("</", "<\\/")
    titulo_art = "<title>Painel AFT</title>\n" if artifact else ""
    rodape = ("AFT Toolkit · painel publicado como artefato · snapshot de "
              f"{hoje.strftime('%d/%m/%Y')} · regenere com a skill /painel."
              if artifact else
              "AFT Toolkit · painel local · aberto pelo arquivo é somente "
              "leitura; pelo modo interativo (http://127.0.0.1:8347, via "
              "servir_painel.py) os cards ganham ações — ver skill /painel.")
    return f"""{titulo_art}<style>{CSS}</style>
<h1>Painel <em>AFT</em></h1>
<p class="sub">Gerado em {hoje.strftime("%d/%m/%Y")} a partir das fichas locais (memory.md) · clique num card para o detalhe da auditoria</p>
<div class="contadores">
  <div class="contador"><b>{len(oss)}</b><span>OS ativas</span></div>
  <div class="contador{' alerta' if n_venc else ''}"><b>{n_venc}</b><span>DETs vencidos</span></div>
  <div class="contador{' alerta' if n_urg else ''}"><b>{n_urg}</b><span>vencendo em ≤ 7 dias</span></div>
  <div class="contador{' alerta' if n_novas else ''}"><b>{n_novas}</b><span>notif. sem registro</span></div>
  <div class="contador"><b>{n_autos}</b><span>autos lavrados</span></div>
</div>
<div class="grid">{grade}</div>
<div id="veu"></div><div id="detalhe"></div>
<footer>{rodape}</footer>
<script>const DATA={json_js};{JS}</script>
"""


def render_html(oss, hoje, n_venc, n_urg, n_novas, n_autos) -> str:
    miolo = render_miolo(oss, hoje, n_venc, n_urg, n_novas, n_autos,
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


def main() -> int:
    base = home_os()
    hoje = datetime.date.today()
    scan = quer_scan()

    oss = []
    if base.exists():
        for mem in sorted(base.glob("*/memory.md")):
            try:
                oss.append(parse_memory(mem))
            except Exception as e:  # uma OS ruim não derruba o painel
                oss.append({
                    "pasta": mem.parent.name, "caminho": str(mem.parent),
                    "empregador": mem.parent.name, "cnpj": "", "municipio": "",
                    "status": "erro", "embargo": "", "ri": "", "num_trabalhadores": None,
                    "data_inicio": None, "data_vencimento": None,
                    "dets": [], "pendencias": [], "atividades": [],
                    "autos_mem": "", "memoria": "", "erro": str(e),
                })

    # Por padrão, OS encerradas somem do painel (é um dashboard de auditorias
    # EM ANDAMENTO) — mudar o status para "encerrada" pelo modo interativo já
    # basta para o card sumir na próxima geração. --todas mostra tudo, para
    # conferência pontual. Não confundir com arquivar (mover a pasta para
    # OS ARQUIVADAS/, convenção do README): aqui a OS continua em OS ATIVAS,
    # só oculta; arquivar é organização de disco, feita à parte quando o AFT
    # quiser.
    n_encerradas = sum(1 for o in oss if o.get("status") == "encerrada")
    if not quer_todas():
        oss = [o for o in oss if o.get("status") != "encerrada"]

    n_scan_ok = 0
    for os_ in oss:
        # Notificações DET nas pastas ainda sem registro no memory.md.
        try:
            os_["novas"] = varrer_notificacoes_novas(
                Path(os_["caminho"]), os_.get("memoria", ""))
        except Exception:
            os_["novas"] = []
        # Relato de campo (só entra na versão local — ver montar_json_os).
        os_["inspecao_fisica"] = parse_inspecao_fisica(Path(os_["caminho"]))
        # Autos lavrados: autos-lavrados.md + scan ao vivo (opcional).
        os_["autos_lavrados_md"] = parse_autos_lavrados_md(Path(os_["caminho"]))
        vivo = scan_ao_vivo(os_) if scan else None
        if vivo is not None:
            n_scan_ok += 1
        os_["autos"], os_["fonte_autos"] = mesclar_autos(
            os_["autos_lavrados_md"], vivo, os_.get("autos_mem", ""))
        os_["nrs"] = extrair_nrs(os_["autos"], os_.get("autos_mem", ""))

    n_novas = sum(len(o["novas"]) for o in oss)
    n_autos = sum(len(o["autos"]) for o in oss)

    # Prazo mais urgente por OS — só DETs em aberto ([ ]) contam para urgência.
    n_vencidos = n_urgentes = 0
    for os_ in oss:
        prazos = [d["prazo"] for d in os_["dets"] if d["prazo"] and not d["feito"]]
        os_["prazo_top"] = min(prazos) if prazos else None
        os_["dias_top"] = (os_["prazo_top"] - hoje).days if prazos else None
        os_["classe"] = classifica(os_["dias_top"])
        for d in os_["dets"]:
            if d["prazo"] and not d["feito"]:
                dd = (d["prazo"] - hoje).days
                if dd < 0:
                    n_vencidos += 1
                elif dd <= 7:
                    n_urgentes += 1

    # Ordena: vencidos primeiro, depois por dias-restantes; sem-prazo ao fim.
    def chave(o):
        return (o["dias_top"] is None, o["dias_top"] if o["dias_top"] is not None else 0)
    oss.sort(key=chave)

    html_out = render_html(oss, hoje, n_vencidos, n_urgentes, n_novas, n_autos)
    destino = saida_html(base)
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(html_out, encoding="utf-8")

    destino_art = saida_artifact()
    if destino_art:
        destino_art.parent.mkdir(parents=True, exist_ok=True)
        destino_art.write_text(
            render_miolo(oss, hoje, n_vencidos, n_urgentes, n_novas, n_autos,
                         com_pasta=False, artifact=True),
            encoding="utf-8")

    # Resumo no stdout (a skill /painel usa isto para responder em texto).
    resumo = {
        "painel": str(destino),
        "artifact_html": str(destino_art) if destino_art else None,
        "os_ativas": len(oss),
        "os_encerradas_ocultas": 0 if quer_todas() else n_encerradas,
        "dets_vencidos": n_vencidos,
        "dets_vencendo_7d": n_urgentes,
        "notificacoes_nao_cadastradas": n_novas,
        "autos_lavrados": n_autos,
        "scan_ao_vivo": {"pedido": scan, "os_com_scan_ok": n_scan_ok},
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


if __name__ == "__main__":
    sys.exit(main())
