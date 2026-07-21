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
# Sub-linha de detalhes mantida pelo det_sync (nunca editada à mão), logo abaixo
# do checkbox: "  - lavrada dd/mm/aaaa · ciência dd/mm/aaaa · última entrega
# dd/mm/aaaa · Confirmada". Os campos vazios são omitidos pelo sync.
RE_DET_DETALHE = re.compile(r"^\s+-\s+lavrada\s", re.IGNORECASE)
RE_DET_LAVRADA = re.compile(r"lavrada\s+(\d{2}/\d{2}/\d{4})", re.IGNORECASE)
RE_DET_CIENCIA = re.compile(r"ci[eê]ncia\s+(\d{2}/\d{2}/\d{4})", re.IGNORECASE)
RE_DET_ULTIMA = re.compile(r"[uú]ltima\s+entrega\s+(\d{2}/\d{2}/\d{4})", re.IGNORECASE)
# Flag do triângulo amarelo do DET ("Existe atualização pendente"): o item mais
# acionável da sub-linha — pedido de prazo, dispensa, item não aberto.
RE_DET_PENDENTE = re.compile(r"atualiza[çc][ãa]o\s+pendente", re.IGNORECASE)
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
    num_trab = parse_fm(fm, "trabalhadores") or parse_fm(fm, "num_trabalhadores")
    cnae = parse_fm(fm, "cnae")
    grau_risco = parse_fm(fm, "grau_risco")
    ri = parse_fm(fm, "ri") or parse_fm(fm, "os") or ""

    # DETs — uma entrada por linha checkbox da seção.
    dets = []
    secao = extrair_secao(corpo, "Notificações DET") or extrair_secao(corpo, "Notificacoes DET")
    linhas_sec = secao.splitlines()
    for idx, linha in enumerate(linhas_sec):
        cb = RE_CHECKBOX.match(linha.strip())
        if not cb:
            continue
        feito = cb.group(1).strip().lower() == "x"
        resto = re.sub(r"<!--.*?-->", "", cb.group(2)).strip()
        prazo_m = RE_PRAZO.search(resto)
        prazo = parse_data(prazo_m.group(1)) if prazo_m else None
        cod_m = RE_CODIGO_DET.match(resto)
        codigo = cod_m.group(1) if cod_m else None
        if not (prazo or codigo):
            continue
        # Sub-linha de detalhes do det_sync, se presente logo abaixo do checkbox:
        # lavratura, ciência e última entrega vêm do próprio DET.
        lavrada = ciencia = ultima = None
        pendente = False
        if idx + 1 < len(linhas_sec) and RE_DET_DETALHE.match(linhas_sec[idx + 1]):
            det = linhas_sec[idx + 1]
            ml, mc, mu = (RE_DET_LAVRADA.search(det), RE_DET_CIENCIA.search(det),
                          RE_DET_ULTIMA.search(det))
            lavrada = parse_data(ml.group(1)) if ml else None
            ciencia = parse_data(mc.group(1)) if mc else None
            ultima = parse_data(mu.group(1)) if mu else None
            pendente = bool(RE_DET_PENDENTE.search(det))
        dets.append({"codigo": codigo, "prazo": prazo, "feito": feito,
                     "linha": resto, "lavrada": lavrada, "ciencia": ciencia,
                     "ultima_entrega": ultima, "atualizacao_pendente": pendente})

    # Pendências (checkbox) — só as em aberto interessam ao painel.
    pendencias = []
    for linha in extrair_secao(corpo, "Pendências").splitlines():
        cb = RE_CHECKBOX.match(linha.strip())
        if cb and cb.group(1).strip().lower() != "x":
            pendencias.append(cb.group(2).strip())

    # Anotações da auditoria (checkbox) — só as em aberto vão ao painel.
    anotacoes = []
    for linha in extrair_secao(corpo, "Anotações da auditoria").splitlines():
        cb = RE_CHECKBOX.match(linha.strip())
        if cb and cb.group(1).strip().lower() != "x":
            texto_an = re.sub(r"<!--.*?-->", "", cb.group(2)).strip()
            if texto_an:
                anotacoes.append(texto_an)

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
        "cnae": cnae,
        "grau_risco": grau_risco,
        "data_inicio": data_inicio,
        "data_vencimento": data_vencimento,
        "dets": dets,
        "pendencias": pendencias,
        "anotacoes": anotacoes,
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


def listar_docs(pasta: Path) -> list[str]:
    """Relatórios .md na raiz da pasta da OS (analise-preliminar-*.md,
    autos-lavrados.md...), para o modal linkar na rota /doc/ do modo
    interativo. Ficam de fora os .md que o modal já exibe por inteiro:
    memory.md (o card é a ficha) e inspecao-fisica.md (seção própria)."""
    try:
        return sorted(p.name for p in pasta.glob("*.md")
                      if p.is_file()
                      and p.name not in ("memory.md", "inspecao-fisica.md"))
    except OSError:
        return []


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
.venc{background:var(--paper);border:1px solid var(--bds);border-radius:10px;
padding:12px 18px 14px;margin-bottom:24px}
.venc h3{font-size:12.5px;letter-spacing:.08em;text-transform:uppercase;
color:var(--t3);margin:0 0 8px}
.venc ul{margin:0;padding-left:18px;font-size:13.5px}
.venc li{margin-bottom:5px}
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
.pend-card{display:inline-block;font:700 11px var(--sans);background:#F5E4E0;
color:var(--coral-deep);border-radius:20px;padding:2px 10px;margin-top:8px}
.aviso-vazio{background:var(--paper);border:1px dashed var(--bd);border-radius:10px;
padding:26px;text-align:center;color:var(--t3)}
/* Detalhe — modal central amplo */
#veu{display:none;position:fixed;inset:0;background:rgba(20,20,19,.55);z-index:8}
#detalhe{display:none;position:fixed;top:3vh;left:50%;transform:translateX(-50%);
z-index:9;width:80vw;max-height:94vh;background:var(--paper);
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
.doc-link{color:var(--coral-deep);text-decoration:underline;text-underline-offset:2px}
.doc-link:hover{color:var(--coral)}
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
.cmds .rot{flex-basis:100%;font-size:12px;font-weight:700;letter-spacing:.07em;
text-transform:uppercase;color:var(--t1)}
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
.det-item .cod .pend,.pend-card{background:#3D2521;color:#E9A891}
.card:hover{box-shadow:0 3px 14px rgba(0,0,0,.5)}
}
/* ---- Dossiê da OS (tela de detalhe) ---- */
:root{--sans:'Hanken Grotesk',system-ui,-apple-system,'Segoe UI',sans-serif;--ochre:#A8842C}
#detalhe{top:2vh;width:min(1280px,96vw);max-height:96vh;border-radius:18px;
  padding:0 0 34px}
#detalhe .topo{display:flex;justify-content:space-between;align-items:center;
  padding:20px 34px 0}
#detalhe .voltar{font:13px var(--sans);color:var(--t3);cursor:pointer;background:none;border:none;padding:0}
#detalhe .voltar:hover{color:var(--coral-deep)}
#detalhe .status-pill{font:600 11.5px/1 var(--sans);letter-spacing:.1em;text-transform:uppercase;
  background:#E1ECE8;color:#38665A;border-radius:20px;padding:6px 12px}
#detalhe .cab{padding:14px 34px 22px;border-bottom:1px solid #E2DECF;
  display:flex;flex-direction:column;gap:6px}
#detalhe h2{font:500 30px var(--serif);letter-spacing:-.01em;margin:0}
#detalhe .cab .meta{display:flex;gap:14px;flex-wrap:wrap;font-size:13px;color:var(--t2)}
#detalhe .cab .meta .sep{color:#C4BFB0}
/* stepper de andamento */
.stepper-os{display:flex;align-items:flex-start;padding:24px 34px 20px;border-bottom:1px solid #E2DECF}
.stepper-os .marco{display:flex;flex-direction:column;align-items:center;gap:7px;width:110px}
.stepper-os .pt{width:14px;height:14px;border-radius:50%;background:var(--paper);border:2px solid #C4BFB0}
.stepper-os .marco.feito .pt{background:var(--teal);border:3px solid var(--paper);box-shadow:0 0 0 1px var(--teal)}
.stepper-os .marco.atual .pt{width:16px;height:16px;background:var(--coral-deep);
  border:3px solid var(--paper);box-shadow:0 0 0 2px var(--coral-deep);margin-top:-1px}
.stepper-os .rot{font:600 12px/1.3 var(--sans);color:var(--t3);text-align:center}
.stepper-os .marco.feito .rot{color:var(--t1)}
.stepper-os .marco.atual .rot{font-weight:700;color:var(--coral-deep)}
.stepper-os .sub{font-size:11px;color:var(--t3);text-align:center}
.stepper-os .lig{flex:1;height:2px;background:#DCD7C8;margin-top:6px}
.stepper-os .lig.feito{background:var(--teal)}
/* próximo passo */
.hero-passo{margin:22px 34px 0;background:#F7E8E2;border:1px solid #E8C7B9;
  border-left:5px solid var(--coral-deep);border-radius:12px;padding:16px 20px;
  display:flex;justify-content:space-between;align-items:center;gap:18px;flex-wrap:wrap}
.hero-passo .rotulo{font:700 11px/1 var(--sans);letter-spacing:.12em;text-transform:uppercase;color:#9E4C34}
.hero-passo p{font:16px/1.45 var(--serif);margin:4px 0 0;color:var(--t1)}
.hero-passo .b1{font:600 13px var(--sans);background:var(--coral-deep);color:var(--paper);
  border:none;border-radius:8px;padding:9px 16px;cursor:pointer}
.hero-passo .b2{font:600 13px var(--sans);background:var(--paper);color:#9E4C34;
  border:1px solid #DCB4A3;border-radius:8px;padding:9px 16px;cursor:pointer}
/* corpo em duas colunas + cards */
#detalhe .corpo2{display:grid;grid-template-columns:1.7fr 1fr;gap:20px;
  padding:20px 34px 6px;align-items:start}
#detalhe .corpo2>div>.cartao{margin-bottom:14px}
#detalhe .cartao{background:var(--paper);border:1px solid var(--bds);border-radius:12px;padding:18px 20px}
#detalhe .cartao h3{font:700 12px/1 var(--sans);letter-spacing:.1em;text-transform:uppercase;
  color:var(--t3);margin:0 0 12px;border:none;padding:0}
#detalhe .cartao .cont{float:right;font:12px var(--sans);color:var(--t3);letter-spacing:0;text-transform:none}
/* DETs como cards com checkbox */
.det-item{display:flex;align-items:flex-start;gap:12px;border:1px solid var(--bds);
  border-radius:10px;padding:11px 14px;cursor:pointer;margin-bottom:8px}
.det-item:hover{border-color:#D2CDBC;background:#FFF}
.det-item .cx{width:18px;height:18px;flex:none;border-radius:5px;border:2px solid #C4BFB0;margin-top:1px}
.det-item.feito .cx{border:none;background:var(--teal);color:var(--paper);
  font:700 12px/18px var(--sans);text-align:center}
.det-item .cod{font:600 13.5px var(--sans);color:var(--t1)}
.det-item .cod .pend{font:700 11px var(--sans);background:#F5E4E0;color:var(--coral-deep);
  border-radius:20px;padding:2px 9px;margin-right:7px;vertical-align:1px;white-space:nowrap}
.det-item .info{font-size:12px;color:var(--t3);line-height:1.45}
.det-item .det-campo{display:flex;gap:6px;line-height:1.6}
.det-item .det-campo .rot{color:var(--t3);min-width:118px}
.det-item .det-campo .val{color:var(--t1);font-weight:600}
.det-item .selo{margin:3px 0 0}
/* timeline */
.tl{display:flex;gap:14px}
.tl .eixo{display:flex;flex-direction:column;align-items:center;width:10px;flex:none}
.tl .pt{width:10px;height:10px;border-radius:50%;background:#C4BFB0;margin-top:3px;flex:none}
.tl.recente .pt{background:var(--coral-deep)}
.tl .fio{flex:1;width:2px;background:#E4E0D2}
.tl .txt{padding-bottom:16px;min-width:0}
.tl .data{font:600 11.5px var(--sans);color:var(--t3)}
.tl .desc{font-size:13.5px;color:#33312C;line-height:1.45;margin-top:2px}
/* coluna direita: comandos por fase */
.fase .frot{font:700 10.5px/1 var(--sans);letter-spacing:.09em;text-transform:uppercase;
  color:#A5A092;display:block;margin:10px 0 6px}
.fase .cmds{margin:0;padding:0;border:none;background:none}
.fase .cmds button{background:#FFF}
/* AUTOS: seção solo, largura total */
.autos-solo-cab{margin:4px 34px 0;padding-top:24px;border-top:1px solid #E2DECF;
  display:flex;justify-content:space-between;align-items:baseline;flex-wrap:wrap;gap:10px}
.autos-solo-cab h3{font:500 23px var(--serif);margin:0;color:var(--t1);
  border:none;padding:0;letter-spacing:0;text-transform:none}
.autos-solo-cab h3 em{color:var(--coral-deep)}
.autos-solo-cab .fonte{font-size:11.5px;color:#A5A092;margin:0}
.autos-chips{margin:12px 34px 0;display:flex;gap:7px;flex-wrap:wrap}
.autos-chips span{font:600 12px var(--sans);background:var(--bds);color:var(--t2);
  border-radius:20px;padding:6px 12px}
.autos-corpo{padding:10px 34px 0;display:flex;flex-direction:column;gap:22px}
.grupo-cab{display:flex;align-items:center;gap:12px;margin-top:4px}
.grupo-cab .grot{font:700 12px/1 var(--sans);letter-spacing:.1em;text-transform:uppercase;
  color:var(--t3);white-space:nowrap}
.grupo-cab .linha{flex:1;height:1px;background:#E2DECF}
.grupo-cab .gcont{font-size:12px;color:#A5A092;white-space:nowrap}
.autos-grid2{display:grid;grid-template-columns:repeat(auto-fill,minmax(380px,1fr));
  gap:12px;align-items:start;margin-top:10px}
.auto-card{background:var(--paper);border:1px solid var(--bds);border-radius:12px;
  padding:15px 18px;display:flex;flex-direction:column;gap:8px}
.auto-card:hover{border-color:#D2CDBC;box-shadow:0 3px 12px rgba(20,20,19,.06)}
.auto-card .lin1{display:flex;justify-content:space-between;align-items:baseline;gap:10px}
.auto-card .num{font:600 16px var(--serif);color:var(--coral-deep)}
.auto-card .quando{font-size:11.5px;color:#A5A092;white-space:nowrap}
.auto-card .tags{display:flex;gap:6px;flex-wrap:wrap}
.auto-card .tag{font:600 11px var(--sans);background:var(--bds);color:var(--t2);border-radius:6px;padding:3px 8px}
.auto-card .tag.base{background:#EFE2D5;color:#8A5A3C}
.auto-card .desc{font:14px/1.5 var(--serif);color:#33312C;margin:0}
.auto-card .constat{font-size:12.5px;line-height:1.55;color:var(--t2);margin:0}
.auto-card .constat b{color:var(--t1)}
/* rodapé da seção de autos */
.autos-rodape{display:grid;grid-template-columns:1fr 1fr;gap:12px;align-items:start;margin:0 34px}
.autos-rodape .cartao h4{font:700 11.5px/1 var(--sans);letter-spacing:.1em;text-transform:uppercase;color:var(--t3);margin:0 0 7px}
.autos-rodape .alerta{background:#F5EEDD;border:1px solid #E4D5AE;border-left:5px solid var(--ochre)}
.autos-rodape .alerta h4{color:#7C5A1E}
.autos-rodape p{margin:0 0 5px;font-size:12.5px;line-height:1.55;color:var(--t2)}
@media (prefers-color-scheme: dark){
  #detalhe .cab,.stepper-os,.autos-solo-cab{border-color:#34302A}
  .hero-passo{background:#3D2521;border-color:#5A3327}
  .det-item:hover,.auto-card:hover{background:#26241F}
  .det-item:hover,.auto-card:hover{border-color:#4A4438}
  .fase .cmds button{background:var(--paper)}
  .tl .fio{background:#3A362E}
  .tl .desc,.auto-card .desc{color:var(--t2)}
  .autos-rodape .alerta{background:#332C1B;border-color:#4A3F22}
  #detalhe .status-pill{background:#233530;color:#8FBCAC}
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
 ['/auditoria-geral','Lê os achados (campo e anotações da auditoria), identifica NR/ementa e redige os autos de infração (NRs + CLT), com gate de dupla visita.'],
 ['/gera-ai','Empacota os autos redigidos no TXT importável pelo Sistema Auditor, com anexos em PDF e pseudonimização reversível.'],
 ['/autos-lavrados','Confere no Sistema Auditor o que já foi transmitido e marca [x]/[ ] no memory.md; cada auto identificado pelo número do AI.'],
 ['/det-630','Auto por omissão de documentos notificados via DET (ementa 001168-1, art. 630 §4º CLT).'],
 ['/tn-nco','Redige a Notificação para Correção de Irregularidades, texto pronto para colar no DET, item por item.'],
 ['/aft-rt-rgi','Relatório Técnico de Interdição/Embargo em .docx + autos derivados das ementas (risco grave e iminente, NR-03).'],
 ['/sfitweb-rel','Relatório Final Simplificado consolidando autos, termos e notificações.']];
function copiaCmd(i,k){copia(CMDS[k][0]+' — OS '+DATA.os[i].empregador)}
function copiaCaminho(i){copia(DATA.os[i].caminho)}
// "Agendar no Google Calendar": URL de template pré-preenchida (evento de dia
// inteiro na data do prazo) — sem login e sem API; o AFT só confirma o Salvar.
function agCal(j){const v=DATA.venc[j];
 const ini=v.prazo_iso.replaceAll('-','');
 const d=new Date(v.prazo_iso+'T12:00:00');d.setDate(d.getDate()+1);
 const fim=d.toISOString().slice(0,10).replaceAll('-','');
 window.open('https://calendar.google.com/calendar/render?action=TEMPLATE&text='+
  encodeURIComponent(v.titulo)+'&dates='+ini+'/'+fim+'&details='+
  encodeURIComponent('Notificação DET '+v.codigo+' — '+v.empregador+' (AFT Toolkit)'),'_blank')}
function agDet(i,k){const o=DATA.os[i];api({acao:'det',pasta:o.pasta,codigo:o.dets[k].codigo})}
function agPend(i,k){const o=DATA.os[i];api({acao:'pendencia',pasta:o.pasta,texto:o.pendencias[k]})}
function agAnot(i,k){const o=DATA.os[i];api({acao:'anotacao_ok',pasta:o.pasta,texto:o.anotacoes[k]})}
function agAnotAdd(i){const el=document.getElementById('anot-txt');const v=(el.value||'').trim();
 if(!v){aviso('Escreva a anotação antes');return}api({acao:'anotacao_add',pasta:DATA.os[i].pasta,texto:v})}
function agStatus(i,v){api({acao:'status',pasta:DATA.os[i].pasta,valor:v})}
function agEmbargo(i,k){api({acao:'embargo',pasta:DATA.os[i].pasta,estado:k?'suspenso':'vigente'})}
function agAtiv(i){const el=document.getElementById('ativ-txt');const v=(el.value||'').trim();
 if(v)api({acao:'atividade',pasta:DATA.os[i].pasta,texto:v})}
// Relatórios .md da OS: no modo interativo viram links para a rota /doc/
// (renderização legível em outra aba); fora dele, texto simples.
function urlDoc(o,d){return '/doc/'+encodeURIComponent(o.pasta)+'/'+encodeURIComponent(d)}
function linkDocs(i,t){const o=DATA.os[i];let s=esc(t);
 if(!ATIVO||!o.pasta||!o.docs)return s;
 for(const d of o.docs){const e=esc(d);
  s=s.split(e).join('<a class="doc-link" target="_blank" href="'+urlDoc(o,d)+'">'+e+'</a>')}
 return s}
// ---- Dossiê da OS (tela de detalhe) ----------------------------------------
// Estágio do andamento da OS: régua fixa de 5 marcos.
const STAGES=['Aberta','Inspecionada','Em instrução','Autuada','Encerrada'];
function stageOS(o){
 if(o.status==='encerrada')return 4;
 if((o.autos||[]).length)return 3;
 if((o.dets||[]).length)return 2;
 if(o.inspecao&&o.inspecao.bullets&&o.inspecao.bullets.length)return 1;
 return 0}
// Grupo de um auto a partir da base legal (fallback: descrição); senão CLT.
function grupoAuto(a){
 const re=/NR[- ]?0?([0-9]{1,2})/i;
 const m=re.exec(a.base||'')||re.exec(a.descricao||'');
 return m?('NR-'+('0'+m[1]).slice(-2)):'CLT / legislação'}
// Próximo passo sugerido — primeira regra que casar; null = sem hero.
function proximoPasso(o){
 const venc=(o.dets||[]).find(d=>!d.feito&&d.urg==='vencido');
 if(venc)return{html:'O DET <b>'+esc(venc.codigo||'?')+'</b> está <b>'+esc(venc.selo||'vencido')+
  '</b> sem entrega — cabe auto por omissão (art. 630 §4º CLT).',cmds:['/det-630','/tn-nco']};
 if((o.pendencias||[]).length)return{html:'Pendência aberta: '+esc(o.pendencias[0]),cmds:[]};
 if(!(o.autos||[]).length&&o.inspecao&&o.inspecao.bullets&&o.inspecao.bullets.length)
  return{html:'Relato de campo registrado e nenhum auto lavrado — redigir os autos.',cmds:['/auditoria-geral']};
 return null}
function copiaPasso(i,k){const pp=proximoPasso(DATA.os[i]);
 if(pp)copia(pp.cmds[k]+' — OS '+DATA.os[i].empregador)}
// Comandos agrupados por fase (índices do array CMDS).
const FASES=[['Campo',[0]],['Autuação',[1,2,3]],['DET / documentos',[4,5]],['Encerramento',[6,7]]];
function stepperHTML(o,st){
 const venc=(o.dets||[]).filter(d=>!d.feito&&d.urg==='vencido').length;
 const autos=o.autos||[],datas=autos.map(a=>a.data).filter(Boolean);
 const subs=[o.inicio||'—',
  (o.inspecao&&o.inspecao.data)||((o.inspecao&&o.inspecao.bullets&&o.inspecao.bullets.length)?'relato registrado':'sem relato de campo'),
  (o.dets||[]).length?(o.dets.length+' DET'+(venc?' · '+venc+' vencido(s)':'')):'sem DET',
  autos.length?(autos.length+' auto(s)'+(datas.length?' · '+datas[0]+(datas.length>1?'–'+datas[datas.length-1]:''):'')):'—',
  o.status==='encerrada'?'concluída':'—'];
 let h='<div class="stepper-os">';
 STAGES.forEach((r,k)=>{
  if(k)h+='<div class="lig'+(k<=st?' feito':'')+'"></div>';
  h+='<div class="marco'+(k<st?' feito':k===st?' atual':'')+'"><span class="pt"></span>'+
   '<span class="rot">'+esc(r)+'</span><span class="sub">'+esc(subs[k])+'</span></div>'});
 return h+'</div>'}
function cartaoDets(o,i){
 let h='<div class="cartao"><h3>Notificações DET <span class="cont">'+(o.dets||[]).length+'</span></h3>';
 if(!(o.dets||[]).length)return h+'<p class="vazio">nenhuma registrada</p></div>';
 h+=o.dets.map((d,k)=>{
  const campos=[['Lavratura',d.lavrada],['Ciência',d.ciencia],
    ['Próxima entrega',d.prox_entrega],['Última entrega',d.ultima_entrega]]
   .filter(c=>c[1]).map(c=>'<div class="det-campo"><span class="rot">'+c[0]+
    '</span><span class="val">'+esc(c[1])+'</span></div>').join('');
  // Fallback p/ notificações ainda sem a sub-linha do det_sync (texto cru).
  const info=campos||esc((d.codigo?d.linha.replace(d.codigo,''):d.linha).replace(/^[ —–-]+/,''));
  return '<div class="det-item'+(d.feito?' feito':'')+'"'+
   (ATIVO&&o.pasta&&d.codigo?' onclick="agDet('+i+','+k+')" title="clique para '+
    (d.feito?'desmarcar':'marcar como checado')+'"':'')+'>'+
   '<span class="cx">'+(d.feito?'✓':'')+'</span><div><div class="cod">'+
   (d.pendente?'<span class="pend">⚠️ atualização pendente</span> ':'')+esc(d.codigo||'?')+'</div>'+
   (info?'<div class="info">'+info+'</div>':'')+
   (d.selo?'<span class="selo '+esc(d.urg)+'">'+esc(d.selo)+'</span>':'')+'</div></div>'}).join('');
 return h+'</div>'}
function cartaoNovas(o){
 return '<div class="cartao"><h3>Notificações na pasta sem registro <span class="cont">'+o.novas.length+
  '</span></h3><ul class="lista">'+o.novas.map(n=>'<li>'+esc(n.codigo||n.arquivo)+
  (n.prazo?' — prazo '+esc(n.prazo):'')+(n.ciencia?' — ciência '+esc(n.ciencia):'')+
  '</li>').join('')+'</ul></div>'}
function cartaoPendencias(o,i){
 return '<div class="cartao"><h3>Pendências da OS <span class="cont">'+o.pendencias.length+
  '</span></h3><ul class="lista">'+o.pendencias.map((s,k)=>'<li>◻ '+esc(s)+
  (ATIVO&&o.pasta?'<button class="mini" onclick="agPend('+i+','+k+')">resolver</button>':'')+
  '</li>').join('')+'</ul></div>'}
function cartaoAnotacoes(o,i){
 const an=o.anotacoes||[];
 let h='<div class="cartao"><h3>Anotações da auditoria <span class="cont">'+an.length+'</span></h3>';
 if(an.length)h+='<ul class="lista">'+an.map((s,k)=>'<li>◻ '+esc(s)+
  (ATIVO&&o.pasta?'<button class="mini" onclick="agAnot('+i+','+k+')">tratada</button>':'')+
  '</li>').join('')+'</ul>';
 else h+='<p class="vazio">nenhuma anotação em aberto</p>';
 if(ATIVO&&o.pasta)h+='<div class="acoes" style="margin:8px 0 0;border:none;background:none;padding:0">'+
  '<span style="flex:1"><input id="anot-txt" style="width:100%" placeholder="anotar constatação (SESMT mal dimensionado, ASO faltando...)" '+
  'onkeydown="if(event.key===&quot;Enter&quot;)agAnotAdd('+i+')">'+
  '<button class="mini" onclick="agAnotAdd('+i+')">anotar</button></span></div>';
 return h+'</div>'}
function cartaoInspecao(o){
 return '<div class="cartao"><h3>Inspeção física'+
  (o.inspecao.data?' <span class="cont">'+esc(o.inspecao.data)+'</span>':'')+'</h3>'+
  '<ul class="insp">'+o.inspecao.bullets.map(b=>'<li>'+esc(b)+'</li>').join('')+'</ul></div>'}
function cartaoTimeline(o,i){
 let h='<div class="cartao"><h3>Registro de atividades <span class="cont">'+(o.atividades||[]).length+'</span></h3>';
 if(!(o.atividades||[]).length)return h+'<p class="vazio">nenhuma atividade registrada</p></div>';
 h+=o.atividades.map((a,k)=>'<div class="tl'+(k===0?' recente':'')+'"><div class="eixo"><span class="pt"></span>'+
  (k<o.atividades.length-1?'<span class="fio"></span>':'')+'</div><div class="txt">'+
  '<div class="data">'+esc(a.data)+'</div><div class="desc">'+linkDocs(i,a.acao)+
  (a.detalhe?' — '+linkDocs(i,a.detalhe):'')+'</div></div></div>').join('');
 return h+'</div>'}
function cartaoAcoes(o,i){
 if(!(ATIVO&&o.pasta))return '';
 const st=['em_andamento','aguardando_resposta','encerrada'];
 if(o.status&&!st.includes(o.status))st.unshift(o.status);
 return '<div class="cartao"><h3>Ações rápidas</h3>'+
  '<div class="acoes" style="margin:0;border:none;background:none;padding:0">'+
  '<span><label>status </label><select onchange="agStatus('+i+',this.value)">'+
  st.map(s=>'<option'+(s===o.status?' selected':'')+'>'+esc(s)+'</option>').join('')+'</select></span>'+
  '<span><label>embargo/interdição </label>'+
  '<button class="mini" onclick="agEmbargo('+i+',0)">vigente</button>'+
  '<button class="mini" onclick="agEmbargo('+i+',1)">suspenso</button></span>'+
  '<span><input id="ativ-txt" placeholder="registrar atividade de hoje..." '+
  'onkeydown="if(event.key===&quot;Enter&quot;)agAtiv('+i+')">'+
  '<button class="mini" onclick="agAtiv('+i+')">registrar</button></span></div></div>'}
function cartaoComandosPorFase(o,i){
 return '<div class="cartao"><h3>Comandos para o Claude Code</h3>'+
  FASES.map(f=>'<div class="fase"><span class="frot">'+esc(f[0])+'</span><div class="cmds">'+
  f[1].map(k=>'<button data-tip="'+esc(CMDS[k][1])+'" onclick="copiaCmd('+i+','+k+')">'+
  esc(CMDS[k][0])+'</button>').join('')+'</div></div>').join('')+'</div>'}
function cartaoRelatorios(o){
 if(!(o.docs&&o.docs.length))return '';
 return '<div class="cartao"><h3>Relatórios da OS <span class="cont">'+o.docs.length+
  '</span></h3><ul class="lista">'+o.docs.map(d=>'<li>'+
  (ATIVO&&o.pasta?'<a class="doc-link" target="_blank" href="'+urlDoc(o,d)+'">'+esc(d)+'</a>':esc(d))+
  '</li>').join('')+'</ul></div>'}
// AUTOS — seção solo, largura total, sempre por último.
function secaoAutos(o,i){
 const autos=o.autos||[];let h='';
 h+='<div class="autos-solo-cab"><h3>Autos de infração <em>lavrados</em> '+
  '<span style="color:var(--t3);font-size:15px">· '+autos.length+'</span></h3>'+
  (o.fonte_autos&&autos.length?'<span class="fonte">fonte: '+esc(o.fonte_autos)+'</span>':'')+'</div>';
 if(!autos.length)return h+'<p class="vazio" style="margin:12px 34px">nenhum auto lavrado encontrado</p>';
 const grupos=new Map();
 autos.forEach(a=>{const g=grupoAuto(a);if(!grupos.has(g))grupos.set(g,[]);grupos.get(g).push(a)});
 h+='<div class="autos-chips">'+[...grupos].map(g=>'<span>'+esc(g[0])+' · '+g[1].length+'</span>').join('')+'</div>';
 h+='<div class="autos-corpo">'+[...grupos].sort((a,b)=>b[1].length-a[1].length).map(g=>
  '<div><div class="grupo-cab"><span class="grot">'+esc(g[0])+'</span><span class="linha"></span>'+
  '<span class="gcont">'+g[1].length+(g[1].length===1?' auto':' autos')+'</span></div>'+
  '<div class="autos-grid2">'+g[1].map(a=>
   '<div class="auto-card"><div class="lin1"><span class="num">Nº '+esc(a.numero_ai)+'</span>'+
   (a.data?'<span class="quando">Lavrado em '+esc(a.data)+'</span>':'')+'</div>'+
   '<div class="tags"><span class="tag">Ementa '+esc(a.ementa)+'</span>'+
   (a.base?'<span class="tag base">'+esc(a.base)+'</span>':'')+'</div>'+
   (a.descricao?'<p class="desc">'+esc(a.descricao)+'</p>':'')+
   (a.constatacao?'<p class="constat"><b>Constatação:</b> '+esc(a.constatacao)+'</p>':'')+
   '</div>').join('')+'</div></div>').join('')+'</div>';
 if((o.substituidos||[]).length||(o.autos_pendentes||[]).length){
  h+='<div class="autos-rodape" style="margin-top:16px">';
  if(o.substituidos.length)h+='<div class="cartao"><h4>Autos substituídos (re-lavratura)</h4>'+
   o.substituidos.map(s=>'<p>'+esc(s)+'</p>').join('')+'</div>';
  if(o.autos_pendentes.length)h+='<div class="cartao alerta"><h4>Pendente de transmissão · '+
   o.autos_pendentes.length+'</h4>'+o.autos_pendentes.map(s=>'<p>'+esc(s)+'</p>').join('')+'</div>';
  h+='</div>'}
 return h}
function abre(i){
 const o=DATA.os[i],st=stageOS(o);
 let h='<div class="topo"><button class="voltar" onclick="fecha()">← voltar ao painel</button>'+
  '<span class="status-pill">'+esc((o.status||'').replace(/_/g,' '))+'</span></div>';
 const meta=[esc(o.cnpj_fmt||'CNPJ não informado'),esc(o.municipio),
  o.ri?'<b>RI '+esc(o.ri)+'</b>':'',
  o.inicio?'Início '+esc(o.inicio)+' ('+esc(o.ha_dias)+')':'',
  o.vencimento?'Vence '+esc(o.vencimento):'',
  o.num_trabalhadores?esc(o.num_trabalhadores)+' trabalhadores':'',
  o.cnae?'CNAE '+esc(o.cnae):'',
  o.grau_risco?'Grau de risco '+esc(o.grau_risco):'',
  o.embargo?'Embargo/interdição: '+esc(o.embargo):'',
  o.caminho?'<span class="pasta-btn" onclick="copiaCaminho('+i+')">copiar caminho da pasta</span>':''
 ].filter(Boolean);
 h+='<div class="cab"><h2>'+esc(o.empregador)+'</h2><div class="meta">'+
  meta.join('<span class="sep">·</span>')+'</div></div>';
 h+=stepperHTML(o,st);
 const pp=proximoPasso(o);
 if(pp)h+='<div class="hero-passo"><div><span class="rotulo">Próximo passo sugerido</span>'+
  '<p>'+pp.html+'</p></div>'+(pp.cmds.length?'<div>'+
  pp.cmds.map((c,k)=>'<button class="'+(k?'b2':'b1')+'" onclick="copiaPasso('+i+','+k+')">'+
  esc(c)+'</button>').join(' ')+'</div>':'')+'</div>';
 h+='<div class="corpo2"><div>';
 h+=cartaoDets(o,i);
 if((o.novas||[]).length)h+=cartaoNovas(o);
 if((o.pendencias||[]).length)h+=cartaoPendencias(o,i);
 if(ATIVO&&o.pasta||(o.anotacoes||[]).length)h+=cartaoAnotacoes(o,i);
 if(o.inspecao&&o.inspecao.bullets&&o.inspecao.bullets.length)h+=cartaoInspecao(o);
 h+=cartaoTimeline(o,i);
 h+='</div><div>';
 h+=cartaoAcoes(o,i);
 h+=cartaoComandosPorFase(o,i);
 h+=cartaoRelatorios(o);
 h+='</div></div>';
 h+=secaoAutos(o,i);
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


def coletar_vencimentos(oss: list[dict], hoje: datetime.date) -> list[dict]:
    """Agenda única de prazos de TODAS as OS, ordenada por data: notificações
    DET com prazo (abertas e checadas — as checadas servem ao /agenda-det, que
    marca ✓ no Google Calendar) e pendências datadas (só as com "prazo <data>"
    no texto; datas soltas — ex. "apólice vencida em 31/05/2025" — não são
    vencimento da pendência). O título dos eventos DET segue a convenção
    'DET <código> <12 primeiros caracteres do empregador>'."""
    itens = []
    for o in oss:
        emp12 = o["empregador"][:12].strip()
        for d in o["dets"]:
            if not d["prazo"]:
                continue
            itens.append({
                "tipo": "det",
                "titulo": f"DET {d['codigo'] or '?'} {emp12}",
                "empregador": o["empregador"],
                "codigo": d["codigo"] or "",
                "prazo_iso": d["prazo"].isoformat(),
                "prazo_br": d["prazo"].strftime("%d/%m/%Y"),
                "dias": (d["prazo"] - hoje).days,
                "checado": d["feito"],
            })
        for p in o["pendencias"]:
            m = RE_PRAZO.search(p)
            dt = parse_data(m.group(1)) if m else None
            if not dt:
                continue
            itens.append({
                "tipo": "pendencia",
                "titulo": datas_para_br(p),
                "empregador": o["empregador"],
                "codigo": "",
                "prazo_iso": dt.isoformat(),
                "prazo_br": dt.strftime("%d/%m/%Y"),
                "dias": (dt - hoje).days,
                "checado": False,
            })
    itens.sort(key=lambda x: (x["prazo_iso"], x["tipo"]))
    return itens


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
            "cnae": o.get("cnae") or "",
            "grau_risco": o.get("grau_risco") or "",
            "inicio": o["data_inicio"].strftime("%d/%m/%Y") if o["data_inicio"] else "",
            "ha_dias": dias_humano(o["data_inicio"], hoje),
            "vencimento": o["data_vencimento"].strftime("%d/%m/%Y") if o["data_vencimento"] else "",
            "caminho": o["caminho"] if com_pasta else "",
            # Relato de campo tem PII (nomes/CPF): só na versão local (com_pasta),
            # nunca na versão publicada como Artifact.
            "inspecao": (o.get("inspecao_fisica") or {}) if com_pasta else {},
            # Relatórios .md também podem conter PII: idem, só na versão local.
            "docs": (o.get("docs") or []) if com_pasta else [],
            "dets": [{"codigo": d["codigo"], "feito": d["feito"],
                      "linha": datas_para_br(d["linha"]),
                      "lavrada": d["lavrada"].strftime("%d/%m/%Y") if d.get("lavrada") else "",
                      "ciencia": d["ciencia"].strftime("%d/%m/%Y") if d.get("ciencia") else "",
                      "prox_entrega": d["prazo"].strftime("%d/%m/%Y") if d["prazo"] else "",
                      "ultima_entrega": d["ultima_entrega"].strftime("%d/%m/%Y") if d.get("ultima_entrega") else "",
                      "pendente": bool(d.get("atualizacao_pendente")),
                      "urg": selo_det(d, hoje)[0], "selo": selo_det(d, hoje)[1]}
                     for d in o["dets"]],
            "novas": o.get("novas") or [],
            "autos": o["autos"],
            "fonte_autos": o["fonte_autos"],
            "substituidos": o["autos_lavrados_md"]["substituidos"],
            "autos_pendentes": o["autos_lavrados_md"]["pendentes"],
            "pendencias": [datas_para_br(p) for p in o["pendencias"]],
            # Anotações podem conter nome/CPF de trabalhador (PII): só na versão
            # local (com_pasta), nunca no Artifact publicado.
            "anotacoes": ([datas_para_br(a) for a in o.get("anotacoes", [])]
                          if com_pasta else []),
            "atividades": [{"data": datas_para_br(a["data"]), "acao": a["acao"],
                            "detalhe": datas_para_br(a["detalhe"])}
                           for a in o["atividades"][-12:][::-1]],
        })
    return out


def render_vencimentos(venc: list[dict]) -> str:
    """Bloco 'Próximos vencimentos', abaixo da grade de cards: a agenda
    consolidada (DETs abertos + pendências datadas) que AINDA NÃO VENCEU —
    o vencido já grita no card e nos contadores, aqui é só o que vem pela
    frente —, com botão que abre o Google Calendar já preenchido (URL de
    template — sem login, sem API)."""
    abertos = [(j, v) for j, v in enumerate(venc) if not v["checado"] and v["dias"] >= 0]
    if not abertos:
        return ""
    lis = []
    for j, v in abertos[:15]:
        classe = classifica(v["dias"])
        if v["dias"] == 0:
            selo = "vence HOJE"
        else:
            selo = f"em {v['dias']}d"
        if v["tipo"] == "det":
            corpo = f"<b>{html.escape(v['titulo'])}</b>"
            botao = (f'<button class="mini" onclick="agCal({j})">'
                     'agendar no Google Calendar</button>' if v["codigo"] else "")
        else:
            corpo = (f"Pendência · {html.escape(v['empregador'][:12].strip())}: "
                     f"{html.escape(v['titulo'][:90])}")
            botao = ""
        lis.append(f'<li class="det-aberto {classe}">{corpo} » {v["prazo_br"]}'
                   f'<span class="selo {classe}">{selo}</span>{botao}</li>')
    resto = ("" if len(abertos) <= 15 else
             f'<li class="vazio">… e mais {len(abertos) - 15} (veja nos cards)</li>')
    return ('<div class="venc"><h3>Próximos vencimentos</h3><ul class="lista">'
            + "".join(lis) + resto + "</ul></div>")


def render_miolo(oss, hoje, n_venc, n_urg, n_novas, n_autos, venc,
                 com_pasta: bool, artifact: bool) -> str:
    cards = []
    for i, o in enumerate(oss):
        classe, rotulo = badge_os(o, hoje)
        chips = "".join(f'<span class="chip">{html.escape(nr)}</span>' for nr in o["nrs"])
        if o["embargo"]:
            chips += f'<span class="chip emb">⛔ {html.escape(o["embargo"][:42])}</span>'
        dets_abertos = sum(1 for d in o["dets"] if not d["feito"])
        pend = any(d.get("atualizacao_pendente") for d in o["dets"])
        pend_selo = ('\n  <div class="pend-card">⚠️ atualização pendente</div>'
                     if pend else "")
        cards.append(f"""
<div class="card {classe}" onclick="abre({i})">
  <h2>{html.escape(o["empregador"])}</h2>
  <div class="meta">{html.escape(fmt_cnpj(o["cnpj"]) if o["cnpj"] else "CNPJ não informado")}{(" · " + html.escape(o["municipio"])) if o["municipio"] else ""}</div>
  <span class="badge {classe}">{html.escape(rotulo)}</span>
  <div class="chips">{chips}</div>
  <div class="rodape-card">
    <span>{len(o["autos"])} auto(s) · {dets_abertos} DET(s) aberto(s)</span>
    <span>{html.escape(dias_humano(o["data_inicio"], hoje))}</span>
  </div>{pend_selo}
</div>""")

    grade = ("".join(cards) if cards else
             '<div class="aviso-vazio">Nenhuma OS encontrada em OS ATIVAS. '
             'Use /nova-os para cadastrar a primeira.</div>')
    dados = {"os": montar_json_os(oss, hoje, com_pasta), "venc": venc}
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
{render_vencimentos(venc)}
<div id="veu"></div><div id="detalhe"></div>
<footer>{rodape}</footer>
<script>const DATA={json_js};{JS}</script>
"""


def render_html(oss, hoje, n_venc, n_urg, n_novas, n_autos, venc) -> str:
    miolo = render_miolo(oss, hoje, n_venc, n_urg, n_novas, n_autos, venc,
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
                    "cnae": "", "grau_risco": "",
                    "data_inicio": None, "data_vencimento": None,
                    "dets": [], "pendencias": [], "anotacoes": [], "atividades": [],
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
        # Relatórios .md da pasta (idem: só na versão local).
        os_["docs"] = listar_docs(Path(os_["caminho"]))
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

    venc = coletar_vencimentos(oss, hoje)

    html_out = render_html(oss, hoje, n_vencidos, n_urgentes, n_novas, n_autos, venc)
    destino = saida_html(base)
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(html_out, encoding="utf-8")

    destino_art = saida_artifact()
    if destino_art:
        destino_art.parent.mkdir(parents=True, exist_ok=True)
        destino_art.write_text(
            render_miolo(oss, hoje, n_vencidos, n_urgentes, n_novas, n_autos, venc,
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
        # Agenda consolidada de prazos (DETs — inclusive checados, para o
        # /agenda-det marcar ✓ no calendário — e pendências datadas).
        "vencimentos": venc,
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
