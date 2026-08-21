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
    encontradas na pasta mas ainda sem registro no memory.md;
  - aba CALENDÁRIO: o diário de atividades (letras A-F da tela 2.1 do RI —
    ver /aft-diario e diario_registrar.py) numa grade mensal, com empresas e
    letras por dia, dias úteis sem registro e, no modo interativo, o
    "registrar dia trabalhado". Inclui OS encerradas e OS ARQUIVADAS (o
    calendário é histórico) e as anotações do gancho (.diario-auto.jsonl).

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
                  scan_autos.py da skill /aft-autos-lavrados. Se a pasta PRO não
                  estiver acessível (ex.: VM do Parallels desligada), degrada
                  em silêncio para o último autos-lavrados.md de cada OS.
  --todas         (opcional): também mostra OS com status: encerrada (por
                  padrão elas ficam de fora — é um dashboard do que está EM
                  ANDAMENTO). Não confundir com arquivar: a OS encerrada
                  continua em OS ATIVAS/, só sai da grade; mover a pasta para
                  OS ARQUIVADAS/ é organização de disco, feita à parte.

Compatível com os dois esquemas de memory.md em uso:
  - o padrão do toolkit (/aft-nova-auditoria), e
  - o schema v2 do ecossistema Cowork (front-matter com data_inicio,
    data_vencimento, num_trabalhadores, datas ISO nas linhas de DET).

Imprime no stdout um resumo em JSON (para a skill /aft-painel ecoar).
Usa a biblioteca padrão; se o pdfplumber estiver instalado (o /aft-setup
instala), lê a 1ª página dos PDFs para melhorar a detecção de notificações.
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

import datetime
import html
import json
import re
import subprocess
import sys
from pathlib import Path

# Console do Windows é cp1252: sem isto, o JSON final (nomes de empregador com
# acento) estoura em UnicodeEncodeError antes de terminar de imprimir.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

try:
    import pdfplumber  # opcional: detecção pelo conteúdo da 1ª página
except ImportError:
    pdfplumber = None

RE_FM = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
RE_TITULO = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)
# Identificador do empregador no corpo do memory.md. Pessoa física (produtor
# rural, empregador doméstico) tem CPF/CAEPF no lugar do CNPJ — a linha vem
# rotulada "**CPF:**", e sem isso o card ficava "CNPJ não informado".
RE_CNPJ_BODY = re.compile(r"\*\*(?:CNPJ|CPF|CAEPF|CNPJ/CPF)\s*:\*\*\s*([\d./-]+)")
RE_PRAZO = re.compile(
    r"(?:prazo|entrega\s+at[eé])[:\s]+(\d{2}/\d{2}/\d{4}|\d{4}-\d{2}-\d{2})",
    re.IGNORECASE)
RE_CODIGO_DET = re.compile(r"([A-Z0-9]{6,})")
RE_CHECKBOX = re.compile(r"^-\s*\[([ xX]?)\]\s*(.*)$")
# Item da "Auditoria de documentos": com ou sem checkbox (o formato antigo,
# das OS abertas quando a seção ainda era uma lista de tarefas).
RE_ITEM = re.compile(r"^-\s*(?:\[[ xX]?\]\s*)?(.*)$")
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
# Envelope laranja do DET: mensagem do empregador no canal de comunicação
# esperando resposta do AFT (isPendenciaComunicacaoAuditor na API).
RE_DET_MENSAGEM = re.compile(r"mensagem\s+no\s+canal", re.IGNORECASE)
# Notificação cancelada pelo auditor no DET (status 2): sem efeito legal.
# Aceita também o `status 2` cru — é como as sincronizações antigas gravaram a
# sub-linha, antes de o sync conhecer o nome do status. Só casa dentro da
# sub-linha de detalhes (escrita pela máquina), nunca no texto do AFT.
RE_DET_CANCELADA = re.compile(r"CANCELADA\s+no\s+DET|status\s+2\b", re.IGNORECASE)
# Notificação lavrada mas ainda sem ciência do empregador (ciência tácita em
# até 15 dias) — o det_sync escreve "aguardando ciência" na sub-linha.
RE_DET_AGUARDA = re.compile(r"aguardando\s+ci[eê]ncia", re.IGNORECASE)
# Rótulo e notas da linha do checkbox: além das datas (que viram campos
# estruturados do card), a linha carrega texto do próprio AFT — o tipo da
# notificação ("NAD jornada/ponto") e observações ("itens 3, 4 e 9 não
# entregues — condicionais, verificar antes de cobrar"). Fragmento de data já
# estruturado sai das notas; o resto é preservado ipsis litteris.
RE_DET_FRAG_DATA = re.compile(
    r"(?:lavrada|ci[eê]ncia|entrega\s+at[eé]|prazo)\s*[:\s]\s*"
    r"(?:\d{2}/\d{2}/\d{4}|\d{4}-\d{2}-\d{2})", re.IGNORECASE)
RE_DET_SEM_ROTULO = re.compile(
    r"^(?:prazo|lavrada|entrega|ci[eê]ncia|baixad|respondid|venc)", re.IGNORECASE)
RE_DATA_ISO = re.compile(r"(\d{4})-(\d{2})-(\d{2})")
RE_DATA_BR = re.compile(r"(\d{2})/(\d{2})/(\d{4})")
RE_NR = re.compile(r"NR[-\s]?0?(\d{1,2})\b", re.IGNORECASE)

# Blocos do autos-lavrados.md (formato da skill /aft-autos-lavrados).
RE_BLOCO_AI = re.compile(r"^###\s+N[ºo°]?\s*([\d.\-]+)\s*$", re.MULTILINE)

# Diário de atividades: prefixo de letras [A-F] na coluna Ação do Registro de
# atividades (ver _scripts/diario_registrar.py) e sidecar do gancho automático.
RE_TIPOS_PREFIXO = re.compile(r"^((?:\[[A-F]\])+)\s*")
RE_TIPOS_LETRAS = re.compile(r"\[([A-F])\]")
SIDECAR_DIARIO = ".diario-auto.jsonl"
DIARIO_JANELA_DIAS = 400  # calendário do painel mostra até ~13 meses p/ trás

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
    try:  # resolve a "Documentos" real (Windows: OneDrive/idioma)
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from pasta_aft import pasta_os_ativas
        return pasta_os_ativas()
    except Exception:
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


def rotulo_e_notas(resto: str, codigo: str | None) -> tuple[str, str]:
    """(rótulo, notas) da linha do checkbox de uma notificação DET — o que o
    AFT escreveu além do código e das datas. Rótulo = 1º segmento curto sem
    cara de data ("NAD jornada/ponto"); notas = o resto da linha, menos os
    fragmentos de data que o card já mostra como campos estruturados."""
    descr = resto[len(codigo):] if codigo and resto.startswith(codigo) else resto
    descr = descr.strip().lstrip("—–-: ").strip()
    rotulo = ""
    # 1º segmento até , ; ou —, sem quebrar dentro de parênteses:
    # "Termo de Notificação (Dupla Visita, NR-01/07/10/12)" é um rótulo só.
    m = re.match(r"(?:\([^)]*\)|[^,;—(])+", descr)
    if m:
        cand = m.group(0).strip()
        if cand and len(cand) <= 60 and not RE_DET_SEM_ROTULO.match(cand):
            rotulo = cand
            descr = descr[m.end():]
    notas = RE_DET_FRAG_DATA.sub("", descr)
    notas = re.sub(r"\s*[,;]\s*(?=[,;])", "", notas)   # separadores órfãos em série
    notas = re.sub(r"\s{2,}", " ", notas).strip(" ,;—–-")
    return rotulo, notas


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

    cnpj = parse_fm(fm, "cnpj") or parse_fm(fm, "cpf") or parse_fm(fm, "caepf")
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
        pendente = aguarda = mensagem = cancelada = False
        if idx + 1 < len(linhas_sec) and RE_DET_DETALHE.match(linhas_sec[idx + 1]):
            det = linhas_sec[idx + 1]
            ml, mc, mu = (RE_DET_LAVRADA.search(det), RE_DET_CIENCIA.search(det),
                          RE_DET_ULTIMA.search(det))
            lavrada = parse_data(ml.group(1)) if ml else None
            ciencia = parse_data(mc.group(1)) if mc else None
            ultima = parse_data(mu.group(1)) if mu else None
            pendente = bool(RE_DET_PENDENTE.search(det))
            aguarda = bool(RE_DET_AGUARDA.search(det))
            mensagem = bool(RE_DET_MENSAGEM.search(det))
            cancelada = bool(RE_DET_CANCELADA.search(det))
        rotulo, notas = rotulo_e_notas(resto, codigo)
        dets.append({"codigo": codigo, "prazo": prazo, "feito": feito,
                     "linha": resto, "rotulo": rotulo, "notas": notas,
                     "lavrada": lavrada, "ciencia": ciencia,
                     "ultima_entrega": ultima, "atualizacao_pendente": pendente,
                     "aguardando_ciencia": aguarda, "mensagem_canal": mensagem,
                     "cancelada": cancelada})

    # Pendências (checkbox) — só as em aberto interessam ao painel.
    pendencias = []
    for linha in extrair_secao(corpo, "Pendências").splitlines():
        cb = RE_CHECKBOX.match(linha.strip())
        if cb and cb.group(1).strip().lower() != "x":
            pendencias.append(cb.group(2).strip())

    # Auditoria de documentos — o que a análise documental apurou (PGR, ASO,
    # atas de CIPA...). Não é checklist: entra tudo, na ordem do arquivo.
    # Aceita o nome antigo da seção para não quebrar OS já abertas.
    anotacoes = []
    sec_doc = (extrair_secao(corpo, "Auditoria de documentos")
               or extrair_secao(corpo, "Anotações da auditoria"))
    for linha in sec_doc.splitlines():
        m_it = RE_ITEM.match(linha.strip())
        if m_it:
            texto_an = re.sub(r"<!--.*?-->", "", m_it.group(1)).strip()
            if texto_an:
                anotacoes.append(texto_an)

    # Registro de atividades (tabela markdown). Linhas do diário de atividades
    # começam com letras [A-F] na coluna Ação (tipos da tela 2.1 do RI — ver
    # diario_registrar.py); linhas antigas sem letra seguem valendo (tipos="").
    atividades = []
    for linha in extrair_secao(corpo, "Registro de atividades").splitlines():
        celulas = [c.strip() for c in linha.strip().strip("|").split("|")]
        if len(celulas) >= 2 and parse_data(celulas[0]):
            acao = celulas[1]
            m_t = RE_TIPOS_PREFIXO.match(acao)
            tipos = "".join(RE_TIPOS_LETRAS.findall(m_t.group(1))) if m_t else ""
            if m_t:
                acao = acao[m_t.end():].strip()
            atividades.append({"data": celulas[0], "acao": acao, "tipos": tipos,
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
    """Lê o autos-lavrados.md da OS (formato da skill /aft-autos-lavrados).
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
    """Relatórios .md da pasta da OS (analise-preliminar-*.md,
    autos-lavrados.md...) — raiz e 1 nível de subpasta (interdicao-embargo/
    autos.md, Acidentes/Relatorio-*.md), para o modal linkar na rota /doc/
    do modo interativo. Ficam de fora os .md que o modal já exibe por
    inteiro: memory.md (o card é a ficha), inspecao-fisica.md (seção
    própria) e email.md (cartão próprio, com botão de copiar)."""
    try:
        docs = [p.name for p in pasta.glob("*.md")
                if p.is_file()
                and p.name not in ("memory.md", "inspecao-fisica.md",
                                   "email.md")]
        docs += [f"{p.parent.name}/{p.name}" for p in pasta.glob("*/*.md")
                 if p.is_file() and not p.parent.name.startswith(".")
                 and not p.name.startswith(".")]
        return sorted(docs)
    except OSError:
        return []


def parse_emails(pasta: Path) -> list[dict]:
    """Lê o email.md da OS (e-mails redigidos pela /aft-email) e devolve
    [{titulo, assunto, corpo}], do mais recente para o mais antigo — cada
    e-mail é um bloco '## <título>' com o corpo dentro de uma cerca ```.
    O painel mostra cada um com botão de copiar, para o AFT colar no cliente
    de e-mail. Só entra na versão LOCAL do painel (ver montar_json_os)."""
    arq = pasta / "email.md"
    if not arq.exists():
        return []
    try:
        texto = arq.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    out = []
    for bloco in re.split(r"^##\s+", texto, flags=re.M)[1:]:
        linhas = bloco.splitlines()
        titulo = linhas[0].strip() if linhas else ""
        corpo = re.search(r"^```[^\n]*\n(.*?)^```", bloco, re.M | re.S)
        if not (titulo and corpo):
            continue
        assunto = re.search(r"\*\*Assunto:\*\*\s*(.+)", bloco)
        out.append({"titulo": titulo,
                    "assunto": assunto.group(1).strip() if assunto else "",
                    "corpo": corpo.group(1).rstrip()})
    return out[:8]


def parse_inspecao_fisica(pasta: Path) -> dict:
    """Lê o inspecao-fisica.md da OS (relato de campo da /aft-inspecao-fisica) e
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
    if not texto.strip():
        return {}
    # `texto` é o arquivo como está no disco: é o que o painel abre para editar.
    return {"data": data, "bullets": bullets, "texto": texto}


def scan_ao_vivo(os_: dict) -> list[dict] | None:
    """Roda o scan_autos.py da skill /aft-autos-lavrados para a OS (se houver
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
    ## Autos lavrados do memory.md (escritas por /aft-autos-lavrados e /aft-organiza-os),
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
            return do_mem, "memory.md (rode /aft-autos-lavrados para detalhar)"
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
                if e.name.upper() == "NOTIFICACOES":
                    # Os PDFs da notificação moram um nível abaixo, dentro do
                    # pacote "<CODIGO> <dd-mm-aaaa>/" (ou "notificacao-*/" nos
                    # legados) — convenção de 21/08/2026.
                    for sub in sorted(p for p in e.iterdir() if p.is_dir()):
                        pdfs += sorted(p for p in sub.iterdir()
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


def data_criacao(o: dict, criado_em: float) -> datetime.date:
    """Quando a auditoria foi criada, na ordem de confiança das fontes.

    O carimbo de criação do arquivo (`criado_em`) é o último recurso: ele muda
    quando a pasta é copiada, restaurada ou recriada por sincronização, e sai
    igual para todas as OS criadas no mesmo lote. As fontes de dentro da ficha
    sobrevivem a isso.
    """
    # 1. linha "OS cadastrada" do Registro de atividades (escrita pela
    #    /aft-nova-auditoria no dia do cadastro).
    for a in o.get("atividades") or []:
        if re.match(r"\s*(\[[A-F]\]\s*)?OS cadastrada", a.get("acao") or "", re.I):
            d = parse_data(a.get("data") or "")
            if d:
                return d
    # 2. OS antiga, sem essa linha: o mais cedo entre o início da fiscalização
    #    e a primeira atividade registrada.
    cands = [d for d in (parse_data((a.get("data") or ""))
                         for a in o.get("atividades") or []) if d]
    if o.get("data_inicio"):
        cands.append(o["data_inicio"])
    if cands:
        return min(cands)
    # 3. sem nada dentro da ficha: o carimbo do arquivo.
    return datetime.date.fromtimestamp(criado_em) if criado_em else datetime.date.min


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
.ordena{display:flex;align-items:center;gap:8px;margin:0 0 12px}
.ordena label{font:11px var(--sans);font-weight:700;letter-spacing:.08em;
text-transform:uppercase;color:var(--t3)}
.ordena select{font:13px var(--serif);color:var(--t1);background:var(--paper);
border:1px solid var(--bd);border-radius:8px;padding:5px 10px;cursor:pointer}
.ordena select:focus{outline:none;border-color:var(--coral-deep);
box-shadow:0 0 0 3px rgba(176,89,62,.18)}
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
/* Mensagem do empregador no canal de comunicacao do DET, no mesmo molde */
.msg-card{display:inline-block;font:700 11px var(--sans);background:#FCEBD8;
color:#9A5B12;border-radius:20px;padding:2px 10px;margin-top:8px;margin-right:6px}
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
/* E-mails redigidos pela /aft-email: texto pronto para copiar e colar. */
.email-item{border-top:1px solid var(--bds);padding:10px 0 4px}
.email-item:first-of-type{border-top:none;padding-top:2px}
.email-tit{font-size:13.5px;font-weight:600;line-height:1.3}
.email-ass{font-size:12.5px;color:var(--t2);margin-top:2px}
.email-item details{margin:6px 0}
.email-item summary{font-size:12px;color:var(--t3);cursor:pointer}
.email-corpo{white-space:pre-wrap;font:12.5px/1.5 var(--serif);background:var(--cream);
border:1px solid var(--bds);border-radius:8px;padding:10px 12px;margin:6px 0 0;
max-height:280px;overflow-y:auto}
.email-item .mini{margin:6px 6px 0 0}
footer{margin-top:34px;color:var(--t3);font-size:12px}
/* Modo interativo (servidor local) + botões de copiar comando */
.chip.emb{background:#F5E4E0;color:var(--coral-deep)}
.mini{font:12px var(--serif);background:var(--paper);border:1px solid var(--bd);
border-radius:6px;padding:1px 9px;margin-left:8px;cursor:pointer;color:var(--t2)}
.mini:hover{border-color:var(--coral);color:var(--coral-deep)}
/* Botão de ação dentro de lista (resolvido, editar): fundo preenchido, senão
   some no cartão e não se lê como botão. */
.mini.acao{background:#EFE2D5;border-color:var(--bd);color:var(--coral-deep);font-weight:600}
.mini.acao:hover{background:var(--coral-deep);border-color:var(--coral-deep);color:var(--paper)}
/* Constatação da auditoria de documentos, em edição no lugar. */
.cons-campo{width:100%;box-sizing:border-box;margin:0 0 6px;font:13.5px var(--serif);
color:var(--t1);background:var(--paper);border:1px solid #C9C3B2;border-radius:6px;
padding:5px 10px}
.cons-campo:focus{outline:none;border-color:var(--coral-deep);
box-shadow:0 0 0 3px rgba(176,89,62,.18)}
.cons-edita .mini{margin-left:0;margin-right:8px}
/* Relato de campo em edição: o inspecao-fisica.md inteiro num campo só. */
.insp-campo{width:100%;box-sizing:border-box;min-height:220px;resize:vertical;
font:13.5px/1.55 var(--serif);color:var(--t1);background:var(--paper);
border:1px solid #C9C3B2;border-radius:8px;padding:12px 14px}
.insp-campo:focus{outline:none;border-color:var(--coral-deep);
box-shadow:0 0 0 3px rgba(176,89,62,.18)}
.insp-rodape{display:flex;justify-content:space-between;align-items:center;margin-top:10px}
.insp-rodape .mini{margin-left:0;margin-right:8px}
.dica-edicao{font:11.5px var(--sans);color:var(--t3)}
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
.det-item .cod .msg,.msg-card{background:#3B2E1B;color:#E8BE85}
.card:hover{box-shadow:0 3px 14px rgba(0,0,0,.5)}
.mini.acao{background:#3A2C22;border-color:#4A382B;color:#E9A891}
.mini.acao:hover{background:#C8694A;border-color:#C8694A;color:#191917}
.cons-campo,.insp-campo{background:#2A2722;border-color:#4A463C}
.cons-campo:focus,.insp-campo:focus{border-color:#E9A891;
box-shadow:0 0 0 3px rgba(233,168,145,.25)}
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
#detalhe .cartao h3 .mini{text-transform:none;letter-spacing:0}
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
.det-item .cod .rotulo{font:500 12.5px var(--sans);color:var(--t2);margin-left:8px}
.det-item .campos{display:flex;flex-wrap:wrap;column-gap:8px;line-height:1.6}
.det-item .det-campo{white-space:nowrap}
.det-item .det-campo .rot{color:var(--t3)}
.det-item .det-campo .val{color:var(--t1);font-weight:600}
.det-item .campos .sep{color:var(--t3);opacity:.55}
.det-item .notas{color:var(--t2);margin-top:2px}
.det-item .selo{margin:3px 0 0}
/* Envelope laranja do DET: mensagem do empregador aguardando resposta do AFT */
.det-item .cod .msg{font:700 11px var(--sans);background:#FCEBD8;color:#9A5B12;
  border-radius:20px;padding:2px 9px;margin-right:7px;vertical-align:1px;white-space:nowrap}
/* Cancelada no DET: visível, mas apagada — não cobra nada do AFT */
.det-item.cancelada{cursor:default;opacity:.6;background:repeating-linear-gradient(
  135deg,transparent,transparent 7px,rgba(143,139,125,.06) 7px,rgba(143,139,125,.06) 14px)}
.det-item.cancelada:hover{border-color:var(--bds);background:none}
.det-item.cancelada .cod{text-decoration:line-through;color:var(--t3)}
/* neutraliza o verde herdado do [x]: cancelada não é "checada pelo AFT" */
.det-item.cancelada .cx{background:none;border:2px solid var(--bd);color:var(--t3);
  font:700 11px/14px var(--sans);text-align:center}
.selo.cancelada{background:var(--bds);color:var(--t3)}
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
/* ---- Zonas de escrita (rebaixo + campo + CTA) ---- */
.entrada{background:var(--cream);border:1px solid var(--bds);border-radius:10px;
  padding:14px 16px;margin-top:12px}
.entrada.acento{border-left:4px solid var(--coral-deep)}
.entrada > label{display:block;margin-bottom:8px;font-family:var(--sans);font-size:11px;
  font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:var(--t2)}
.entrada input[type=text],.entrada textarea{width:100%;box-sizing:border-box;
  min-height:42px;padding:10px 14px;font-family:var(--serif);font-size:15px;line-height:1.5;
  color:var(--t1);background:var(--paper);border:1px solid #C9C3B2;border-radius:8px}
.entrada input::placeholder,.entrada textarea::placeholder{color:var(--t3);opacity:1}
.entrada input:focus,.entrada textarea:focus{outline:none;border-color:var(--coral-deep);
  box-shadow:0 0 0 3px rgba(176,89,62,.18)}
.entrada .cta{height:42px;padding:0 20px;font-family:var(--serif);font-size:15px;font-weight:600;
  color:var(--paper);background:var(--coral-deep);border:1px solid var(--coral-deep);
  border-radius:8px;cursor:pointer}
.entrada .cta:hover{background:var(--coral);border-color:var(--coral)}
.entrada .cta:disabled{background:#E2DECF;border-color:var(--bd);color:var(--t3);cursor:default}
.entrada .linha{display:flex;gap:10px;align-items:stretch}
.entrada .rodape{display:flex;justify-content:space-between;align-items:center;margin-top:10px}
.entrada .dica{font-family:var(--sans);font-size:11.5px;color:var(--t3)}
@media (prefers-color-scheme: dark){
  .entrada{background:#1E1C1A}
  .entrada input[type=text],.entrada textarea{background:#2A2722;border-color:#4A463C}
  .entrada input:focus,.entrada textarea:focus{border-color:#E9A891;
    box-shadow:0 0 0 3px rgba(233,168,145,.25)}
  .entrada .cta{background:#C8694A;border-color:#C8694A;color:#191917}
  .entrada .cta:hover{background:#E09070;border-color:#E09070}
  .entrada .cta:disabled{background:#2E2B25;border-color:#3A372F;color:var(--t3)}
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
/* ---- Abas (Auditorias | Calendário) ---- */
.abas{display:flex;gap:8px;margin:0 0 18px}
.aba{font:600 13px var(--sans);background:var(--paper);border:1px solid var(--bd);
border-radius:20px;padding:7px 18px;cursor:pointer;color:var(--t2)}
.aba:hover{border-color:var(--coral);color:var(--coral-deep)}
.aba.ativa{background:var(--coral-deep);border-color:var(--coral-deep);color:#FAF9F5}
/* ---- Calendário de trabalho (diário de atividades) ---- */
.cal-topo{display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin-bottom:14px}
.cal-topo h2{font:500 22px var(--serif);margin:0 10px 0 0}
.cal-topo .mini{margin:0}
.cal-cont{margin-left:auto;font:13px var(--sans);color:var(--t2)}
.cal-cont b{color:var(--teal);font-size:16px}
.cal-wrap{display:grid;grid-template-columns:minmax(0,2.2fr) minmax(270px,1fr);
gap:16px;align-items:start}
.cal-grade{background:var(--paper);border:1px solid var(--bds);border-radius:12px;
overflow:hidden}
.cal-sem{display:grid;grid-template-columns:repeat(7,1fr);border-bottom:1px solid var(--bds)}
.cal-sem span{font:700 10.5px var(--sans);letter-spacing:.08em;text-transform:uppercase;
color:var(--t3);text-align:center;padding:9px 4px}
.cal-corpo{display:grid;grid-template-columns:repeat(7,1fr)}
.cal-dia{min-height:88px;border-top:1px solid var(--bds);border-left:1px solid var(--bds);
padding:6px 7px;cursor:pointer;overflow:hidden}
.cal-corpo .cal-dia:nth-child(7n+1){border-left:none}
.cal-dia:hover{background:var(--cream)}
.cal-dia .n{font:600 12.5px var(--sans);color:var(--t2)}
.cal-dia.fora{opacity:.35;cursor:default}
.cal-dia.fora:hover{background:transparent}
.cal-dia.fds .n{color:var(--t3)}
.cal-dia.hoje .n{background:var(--coral-deep);color:#FAF9F5;border-radius:50%;
display:inline-block;min-width:22px;height:22px;line-height:22px;text-align:center}
.cal-dia.sel{background:#F1E6D8}
.cal-dia.vago .n{border-bottom:2px dotted var(--coral)}
.cal-ev{font:11px var(--sans);color:var(--t2);margin-top:4px;display:flex;
align-items:center;gap:5px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.cal-ev .pt-ev{width:6px;height:6px;border-radius:50%;background:var(--teal);flex:none}
.cal-ev.auto .pt-ev{background:var(--bd)}
.cal-ev b{font:700 10px var(--sans);color:var(--coral-deep);letter-spacing:.5px}
.cal-mais{font:10.5px var(--sans);color:var(--t3);margin-top:3px}
.cal-lado{background:var(--paper);border:1px solid var(--bds);border-radius:12px;
padding:16px 18px}
.cal-lado h3{font:700 11px var(--sans);letter-spacing:.1em;text-transform:uppercase;
color:var(--t3);margin:0 0 4px;border:none;padding:0}
.cal-lado h2{font:500 20px var(--serif);margin:0 0 12px}
.cal-item{border:1px solid var(--bds);border-radius:10px;padding:10px 12px;margin-bottom:8px}
.cal-item .emp{font:600 13px var(--sans)}
.cal-item .tipos{margin:5px 0 2px}
.tipo-tag{display:inline-block;font:700 10.5px var(--sans);background:#EFE2D5;
color:var(--coral-deep);border-radius:5px;padding:2px 7px;margin:0 4px 3px 0}
.tipo-tag.gen{background:var(--bds);color:var(--t3)}
.cal-item .txt{font-size:12.5px;color:var(--t2);line-height:1.45;margin-top:2px}
.cal-legenda{margin-top:14px;font:11.5px var(--sans);color:var(--t3);display:flex;
flex-wrap:wrap;gap:6px 14px}
.cal-legenda b{color:var(--coral-deep)}
.cal-legenda .pt-ev{display:inline-block;width:6px;height:6px;border-radius:50%;
background:var(--bd)}
.cal-form{border-top:1px solid var(--bds);margin-top:12px;padding-top:10px}
.cal-form label{font:11.5px var(--sans);color:var(--t3);display:block;margin:9px 0 3px}
.cal-form select,.cal-form input[type=text]{width:100%;font:13px var(--serif);
background:var(--cream);border:1px solid var(--bd);border-radius:6px;padding:5px 8px;
color:var(--t1)}
.cal-tipos label{display:flex;align-items:flex-start;gap:6px;margin:0 0 3px;
font:12px var(--serif);color:var(--t1);cursor:pointer}
.cal-tipos b{font:700 11px var(--sans);color:var(--coral-deep)}
@media (max-width:900px){.cal-wrap{grid-template-columns:1fr}}
@media (prefers-color-scheme: dark){
.aba.ativa{color:#191917}
.cal-dia.hoje .n{color:#191917}
.cal-dia.sel{background:#2E2820}
.tipo-tag{background:#3A2C22}
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
async function api(p,semReabrir){
 try{const r=await fetch('/api/acao',{method:'POST',
  headers:{'Content-Type':'application/json'},body:JSON.stringify(p)});
  const j=await r.json();
  if(!j.ok){aviso('Erro: '+(j.erro||'?'));return}
  if(!semReabrir)sessionStorage.setItem('painel-reabrir',p.pasta);
  location.reload();
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
 ['/aft-inspecao-fisica','Transforma a narrativa ditada da visita num relato de campo estruturado (inspecao-fisica.md), fiel e sem enquadramento.'],
 ['/aft-auditoria-geral','Lê os achados (campo e auditoria de documentos), identifica NR/ementa e redige os autos de infração (NRs + CLT), com gate de dupla visita.'],
 ['/aft-gera-ai','Empacota os autos redigidos no TXT importável pelo Sistema Auditor, com anexos em PDF e pseudonimização reversível.'],
 ['/aft-autos-lavrados','Confere no Sistema Auditor o que já foi transmitido e marca [x]/[ ] no memory.md; cada auto identificado pelo número do AI.'],
 ['/aft-det-630','Auto por omissão de documentos notificados via DET (ementa 001168-1, art. 630 §4º CLT).'],
 ['/aft-tn-nco','Redige a Notificação para Correção de Irregularidades, texto pronto para colar no DET, item por item.'],
 ['/aft-embargo-interdicao','Relatório Técnico de Interdição/Embargo em .docx + autos derivados das ementas (risco grave e iminente, NR-03).'],
 ['/aft-relatorio','Relatório Final Simplificado consolidando autos, termos e notificações.']];
function copiaCmd(i,k){copia(CMDS[k][0]+' — OS '+DATA.os[i].empregador)}
function copiaCaminho(i){copia(DATA.os[i].caminho)}
// E-mail redigido pela /aft-email: copia o corpo cru, pronto para colar no
// cliente de e-mail (aviso diferente do de comando — nada de "cole no Claude").
function copiaEmail(i,k,so){const e=DATA.os[i].emails[k];
 const t=so==='assunto'?e.assunto:e.corpo;
 const fim=()=>aviso(so==='assunto'?'Assunto copiado':'E-mail copiado — cole no seu e-mail');
 if(navigator.clipboard&&navigator.clipboard.writeText){
  navigator.clipboard.writeText(t).then(fim).catch(()=>copiaVelho(t,fim));
 }else copiaVelho(t,fim)}
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
function agDetVisto(i,k){const o=DATA.os[i];api({acao:'det_visto',pasta:o.pasta,codigo:o.dets[k].codigo})}
// "baixar arquivos": o servidor busca na API do DET (com o token do último
// Sincronizar) o PDF da notificação, o Relatório de Atendimento e os arquivos
// entregues, direto na pasta da OS. Pode levar alguns segundos.
async function agDetBaixar(i,k,ev,b){ev.stopPropagation();
 const o=DATA.os[i];b.disabled=true;const rot=b.textContent;b.textContent='baixando…';
 try{const r=await fetch('/api/det-baixar',{method:'POST',
  headers:{'Content-Type':'application/json'},
  body:JSON.stringify({pasta:o.pasta,codigo:o.dets[k].codigo})});
  const j=await r.json();
  if(j.ok){const e=(j.erros||[]).length;
   aviso(j.baixados?j.baixados+' arquivo(s) baixado(s) na pasta da OS'+
    (e?' — '+e+' com erro':''):'nada novo — tudo já estava baixado')}
  else aviso((j.token_expirado?'⚠️ ':'Erro: ')+(j.erro||'?'));
 }catch(e){aviso('Servidor do painel não respondeu — abra pelo http://127.0.0.1:8347')}
 b.disabled=false;b.textContent=rot}
function agPend(i,k){const o=DATA.os[i];api({acao:'pendencia',pasta:o.pasta,texto:o.pendencias[k]})}
function agPendAdd(i){const el=document.getElementById('pend-txt');const v=(el.value||'').trim();
 if(!v){aviso('Escreva a pendência antes');return}
 api({acao:'pendencia_add',pasta:DATA.os[i].pasta,texto:v})}
// CTA das zonas de escrita: ativo somente com texto no campo.
function cta(el){const b=el.closest('.entrada').querySelector('.cta');
 if(b)b.disabled=!el.value.trim()}
// Constatação da auditoria de documentos: o item vira campo no próprio lugar.
// O valor entra pelo .value (o esc() do painel não protege atributo).
function agAnotEdit(i,k){
 const li=document.getElementById('cons-'+k);if(!li||li.querySelector('input'))return;
 li.innerHTML='<input type="text" class="cons-campo"><span class="cons-edita">'+
  '<button class="mini acao" onclick="agAnotSalva('+i+','+k+')">salvar</button>'+
  '<button class="mini" onclick="abre('+i+')">cancelar</button></span>';
 const c=li.querySelector('input');c.value=DATA.os[i].anotacoes[k];c.focus();
 c.setSelectionRange(c.value.length,c.value.length);
 c.onkeydown=e=>{if(e.key==='Enter')agAnotSalva(i,k);if(e.key==='Escape')abre(i)}}
function agAnotSalva(i,k){
 const o=DATA.os[i],li=document.getElementById('cons-'+k);
 const v=(li.querySelector('input').value||'').trim();
 if(!v){aviso('A constatação não pode ficar vazia');return}
 if(v===o.anotacoes[k]){abre(i);return}
 api({acao:'constatacao_edit',pasta:o.pasta,texto:o.anotacoes[k],novo:v})}
function agAnotAdd(i){const el=document.getElementById('anot-txt');const v=(el.value||'').trim();
 if(!v){aviso('Escreva a constatação antes');return}api({acao:'anotacao_add',pasta:DATA.os[i].pasta,texto:v})}
function agStatus(i,v){api({acao:'status',pasta:DATA.os[i].pasta,valor:v})}
function agEmbargo(i,k){api({acao:'embargo',pasta:DATA.os[i].pasta,estado:k?'suspenso':'vigente'})}
function agAtiv(i){const el=document.getElementById('ativ-txt');const v=(el.value||'').trim();
 if(v)api({acao:'atividade',pasta:DATA.os[i].pasta,texto:v})}
// Relatórios .md da OS: no modo interativo viram links para a rota /doc/
// (renderização legível em outra aba); fora dele, texto simples.
function urlDoc(o,d){return '/doc/'+encodeURIComponent(o.pasta)+'/'+encodeURIComponent(d)}
function linkDocs(i,t){const o=DATA.os[i];let s=esc(t);
 if(!ATIVO||!o.pasta||!o.docs||!o.docs.length)return s;
 // Em duas fases, nomes mais longos primeiro (nome -> marcador -> link):
 // "autos.md" não pode quebrar o link de "interdicao-embargo/autos.md" que o
 // contém, nem casar dentro do HTML já inserido do link de outro documento.
 const ds=[...o.docs].sort((a,b)=>b.length-a.length),trocas=[];
 ds.forEach((d,k)=>{const e=esc(d),m='\\u0001'+k+'\\u0001';
  if(s.indexOf(e)>=0){s=s.split(e).join(m);trocas.push([m,d,e])}});
 for(const [m,d,e] of trocas)
  s=s.split(m).join('<a class="doc-link" target="_blank" href="'+urlDoc(o,d)+'">'+e+'</a>');
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
  '</b> sem entrega — cabe auto por omissão (art. 630 §4º CLT).',cmds:['/aft-det-630','/aft-tn-nco']};
 if((o.pendencias||[]).length)return{html:'Pendência aberta: '+esc(o.pendencias[0]),cmds:[]};
 if(!(o.autos||[]).length&&o.inspecao&&o.inspecao.bullets&&o.inspecao.bullets.length)
  return{html:'Relato de campo registrado e nenhum auto lavrado — redigir os autos.',cmds:['/aft-auditoria-geral']};
 return null}
function copiaPasso(i,k){const pp=proximoPasso(DATA.os[i]);
 if(pp)copia(pp.cmds[k]+' — OS '+DATA.os[i].empregador)}
// Comandos agrupados por fase (índices do array CMDS).
const FASES=[['Campo',[0]],['Autuação',[1,2,3]],['DET / documentos',[4,5]],['Encerramento',[6,7]]];
function stepperHTML(o,st){
 const venc=(o.dets||[]).filter(d=>!d.feito&&d.urg==='vencido').length;
 const nDets=(o.dets||[]).filter(d=>!d.cancelada).length;
 const autos=o.autos||[],datas=autos.map(a=>a.data).filter(Boolean);
 const subs=[o.inicio||'—',
  (o.inspecao&&o.inspecao.data)||((o.inspecao&&o.inspecao.bullets&&o.inspecao.bullets.length)?'relato registrado':'sem relato de campo'),
  nDets?(nDets+' DET'+(venc?' · '+venc+' vencido(s)':'')):'sem DET',
  autos.length?(autos.length+' auto(s)'+(datas.length?' · '+datas[0]+(datas.length>1?'–'+datas[datas.length-1]:''):'')):'—',
  o.status==='encerrada'?'concluída':'—'];
 let h='<div class="stepper-os">';
 STAGES.forEach((r,k)=>{
  if(k)h+='<div class="lig'+(k<=st?' feito':'')+'"></div>';
  h+='<div class="marco'+(k<st?' feito':k===st?' atual':'')+'"><span class="pt"></span>'+
   '<span class="rot">'+esc(r)+'</span><span class="sub">'+esc(subs[k])+'</span></div>'});
 return h+'</div>'}
function cartaoDets(o,i){
 // Contador só do que vale: cancelada no DET não é notificação viva.
 const vivas=(o.dets||[]).filter(d=>!d.cancelada).length;
 let h='<div class="cartao"><h3>Notificações DET <span class="cont">'+vivas+'</span></h3>';
 if(!(o.dets||[]).length)return h+'<p class="vazio">nenhuma registrada</p></div>';
 h+=o.dets.map((d,k)=>{
  // Datas em linha única (Lavratura · Ciência · entregas) — o texto do AFT
  // (rótulo + notas) é o que merece a largura do card.
  const campos=[['Lavratura',d.lavrada],['Ciência',d.ciencia],
    ['Próxima entrega',d.prox_entrega],['Última entrega',d.ultima_entrega]]
   .filter(c=>c[1]).map(c=>'<span class="det-campo"><span class="rot">'+c[0]+
    '</span> <span class="val">'+esc(c[1])+'</span></span>').join('<span class="sep">·</span>');
  // Cancelada no DET: fica visível (o AFT precisa saber que foi cancelada),
  // mas apagada e sem clique — não há o que marcar numa notificação sem efeito.
  return '<div class="det-item'+(d.feito?' feito':'')+(d.cancelada?' cancelada':'')+'"'+
   (ATIVO&&o.pasta&&d.codigo&&!d.cancelada?' onclick="agDet('+i+','+k+')" title="clique para '+
    (d.feito?'desmarcar':'marcar como checado')+'"':'')+'>'+
   '<span class="cx">'+(d.cancelada?'✕':d.feito?'✓':'')+'</span><div><div class="cod">'+
   (d.mensagem?'<span class="msg" title="o empregador mandou mensagem no canal de comunicação desta notificação e ela aguarda resposta sua — responda no DET">✉️ mensagem no DET</span> ':'')+
   (d.pendente&&!d.cancelada?'<span class="pend"'+(ATIVO&&o.pasta&&d.codigo?
    ' style="cursor:pointer" title="clique se já viu esta atualização no DET — o alerta some e só volta se houver entrega nova"'+
    ' onclick="event.stopPropagation();agDetVisto('+i+','+k+')"':'')+
    '>⚠️ atualização pendente</span> ':'')+
   (d.aguarda&&!d.cancelada?'<span class="pend">⏳ aguardando ciência</span> ':'')+esc(d.codigo||'?')+
   (d.rotulo?'<span class="rotulo">'+esc(d.rotulo)+'</span>':'')+'</div>'+
   (campos?'<div class="info campos">'+campos+'</div>':'')+
   (d.notas?'<div class="info notas">'+esc(d.notas)+'</div>':'')+
   (ATIVO&&o.pasta&&d.codigo&&!d.cancelada?'<button class="mini acao" '+
    'title="baixa da API do DET o PDF da notificação, o Relatório de Atendimento e os arquivos entregues, organizados por item na pasta da OS (precisa de um Sincronizar na aba do DET nos últimos 25 min)" '+
    'onclick="agDetBaixar('+i+','+k+',event,this)">⬇ baixar arquivos</button>':'')+
   (d.selo?'<span class="selo '+esc(d.urg)+'">'+esc(d.selo)+'</span>':'')+'</div></div>'}).join('');
 return h+'</div>'}
function cartaoNovas(o){
 return '<div class="cartao"><h3>Notificações na pasta sem registro <span class="cont">'+o.novas.length+
  '</span></h3><ul class="lista">'+o.novas.map(n=>'<li>'+esc(n.codigo||n.arquivo)+
  (n.prazo?' — prazo '+esc(n.prazo):'')+(n.ciencia?' — ciência '+esc(n.ciencia):'')+
  '</li>').join('')+'</ul></div>'}
function cartaoPendencias(o,i){
 const ps=o.pendencias||[];
 let h='<div class="cartao"><h3>Pendências da OS <span class="cont">'+ps.length+'</span></h3>';
 if(ps.length)h+='<ul class="lista">'+ps.map((s,k)=>'<li>◻ '+esc(s)+
  (ATIVO&&o.pasta?'<button class="mini acao" onclick="agPend('+i+','+k+')">resolvido</button>':'')+
  '</li>').join('')+'</ul>';
 else h+='<p class="vazio">nenhuma pendência em aberto</p>';
 if(ATIVO&&o.pasta)h+='<div class="entrada">'+
  '<label for="pend-txt">Nova pendência</label><div class="linha">'+
  '<input id="pend-txt" type="text" placeholder="ex.: cobrar o AEJ de julho na próxima visita" '+
  'oninput="cta(this)" onkeydown="if(event.key===&quot;Enter&quot;)agPendAdd('+i+')">'+
  '<button class="cta" disabled onclick="agPendAdd('+i+')">registrar</button></div></div>';
 return h+'</div>'}
function cartaoAnotacoes(o,i){
 const an=o.anotacoes||[];
 let h='<div class="cartao"><h3>Auditoria de documentos <span class="cont">'+an.length+'</span></h3>';
 if(an.length)h+='<ul class="lista">'+an.map((s,k)=>'<li id="cons-'+k+'">'+esc(s)+
  (ATIVO&&o.pasta?'<button class="mini acao" onclick="agAnotEdit('+i+','+k+')">editar</button>':'')+
  '</li>').join('')+'</ul>';
 else h+='<p class="vazio">nenhuma constatação registrada</p>';
 if(ATIVO&&o.pasta)h+='<div class="entrada">'+
  '<label for="anot-txt">Nova constatação</label><div class="linha">'+
  '<input id="anot-txt" type="text" placeholder="ex.: PGR sem inventário de riscos químicos" '+
  'oninput="cta(this)" onkeydown="if(event.key===&quot;Enter&quot;)agAnotAdd('+i+')">'+
  '<button class="cta" disabled onclick="agAnotAdd('+i+')">anotar</button></div></div>';
 return h+'</div>'}
function cartaoInspecao(o,i){
 const bs=o.inspecao.bullets||[];
 return '<div class="cartao" id="insp-cartao"><h3>Inspeção física'+
  (ATIVO&&o.pasta&&o.inspecao.texto?
   '<button class="mini acao" onclick="agInspEdit('+i+')">editar</button>':'')+
  (o.inspecao.data?' <span class="cont">'+esc(o.inspecao.data)+'</span>':'')+'</h3>'+
  (bs.length?'<ul class="insp">'+bs.map(b=>'<li>'+esc(b)+'</li>').join('')+'</ul>':
   '<p class="vazio">relato sem itens em lista</p>')+'</div>'}
// Relato de campo: o cartão vira um campo com o inspecao-fisica.md tal como
// está no disco — dá para corrigir uma frase, acrescentar uma lembrança ou
// registrar uma visita nova. Aqui o Enter é quebra de linha (é texto longo):
// quem salva é Ctrl/⌘ + Enter, ou o botão.
function agInspEdit(i){
 const cx=document.getElementById('insp-cartao');if(!cx||cx.querySelector('textarea'))return;
 cx.innerHTML='<h3>Inspeção física</h3><textarea class="insp-campo"></textarea>'+
  '<div class="insp-rodape"><span>'+
  '<button class="mini acao" onclick="agInspSalva('+i+')">salvar</button>'+
  '<button class="mini" onclick="abre('+i+')">cancelar</button></span>'+
  '<span class="dica-edicao">Ctrl (⌘) + Enter salva · Esc desiste</span></div>';
 const t=cx.querySelector('textarea');t.value=DATA.os[i].inspecao.texto||'';
 t.style.height=Math.min(t.scrollHeight+12,620)+'px';
 // Abre no começo do relato, como quem relê o documento: preencher o campo
 // joga o cursor (e a rolagem) para o fim, e aí não se vê o que se está editando.
 t.focus();t.setSelectionRange(0,0);t.scrollTop=0;
 t.onkeydown=e=>{if(e.key==='Enter'&&(e.metaKey||e.ctrlKey))agInspSalva(i);
  if(e.key==='Escape')abre(i)}}
function agInspSalva(i){
 const o=DATA.os[i],t=document.querySelector('#insp-cartao textarea');
 if(!t.value.trim()){aviso('O relato não pode ficar vazio');return}
 if(t.value.trim()===(o.inspecao.texto||'').trim()){abre(i);return}
 api({acao:'inspecao_edit',pasta:o.pasta,texto:t.value})}
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
  '</div>'+
  '<div class="entrada"><label for="ativ-txt">Registrar atividade</label><div class="linha">'+
  '<input id="ativ-txt" type="text" placeholder="ex.: análise do PGR entregue pela empresa" '+
  'oninput="cta(this)" onkeydown="if(event.key===&quot;Enter&quot;)agAtiv('+i+')">'+
  '<button class="cta" disabled onclick="agAtiv('+i+')">registrar</button></div></div></div>'}
function cartaoComandosPorFase(o,i){
 return '<div class="cartao"><h3>Comandos para o Claude Code</h3>'+
  FASES.map(f=>'<div class="fase"><span class="frot">'+esc(f[0])+'</span><div class="cmds">'+
  f[1].map(k=>'<button data-tip="'+esc(CMDS[k][1])+'" onclick="copiaCmd('+i+','+k+')">'+
  esc(CMDS[k][0])+'</button>').join('')+'</div></div>').join('')+'</div>'}
// E-MAILS — redigidos pela /aft-email, com botão de copiar e prévia expansível.
function cartaoEmails(o,i){
 const es=o.emails||[];if(!es.length)return '';
 return '<div class="cartao"><h3>E-mails <span class="cont">'+es.length+'</span></h3>'+
  es.map((e,k)=>'<div class="email-item"><div class="email-tit">'+esc(e.titulo)+'</div>'+
   (e.assunto?'<div class="email-ass">Assunto: '+esc(e.assunto)+'</div>':'')+
   '<details><summary>ver o texto</summary><pre class="email-corpo">'+esc(e.corpo)+'</pre></details>'+
   '<button class="mini" onclick="copiaEmail('+i+','+k+')">copiar e-mail</button>'+
   (e.assunto?'<button class="mini" onclick="copiaEmail('+i+','+k+',\\'assunto\\')">copiar assunto</button>':'')+
   '</div>').join('')+'</div>'}
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
let ABERTA=null; // pasta da OS do card aberto (p/ reabrir após auto-refresh)
function abre(i){
 const o=DATA.os[i],st=stageOS(o);ABERTA=o.pasta||null;
 let h='<div class="topo"><button class="voltar" onclick="fecha()">← voltar ao painel</button>'+
  '<span class="status-pill">'+esc((o.status||'').replace(/_/g,' '))+'</span></div>';
 const meta=[esc(o.cnpj_fmt||'CNPJ/CPF não informado'),esc(o.municipio),
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
 if(ATIVO&&o.pasta||(o.pendencias||[]).length)h+=cartaoPendencias(o,i);
 if(ATIVO&&o.pasta||(o.anotacoes||[]).length)h+=cartaoAnotacoes(o,i);
 if(o.inspecao&&((o.inspecao.bullets||[]).length||o.inspecao.texto))h+=cartaoInspecao(o,i);
 h+=cartaoTimeline(o,i);
 h+='</div><div>';
 h+=cartaoAcoes(o,i);
 h+=cartaoComandosPorFase(o,i);
 h+=cartaoEmails(o,i);
 h+=cartaoRelatorios(o);
 h+='</div></div>';
 h+=secaoAutos(o,i);
 P.innerHTML=h;P.classList.add('aberto');V.classList.add('aberto');P.scrollTop=0;
}
function fecha(){P.classList.remove('aberto');V.classList.remove('aberto');ABERTA=null}
V.addEventListener('click',fecha);
document.addEventListener('keydown',e=>{if(e.key==='Escape')fecha()});
// Depois de uma ação, reabre o mesmo card (a página recarrega para refletir a edição).
(function(){const alvo=sessionStorage.getItem('painel-reabrir');
 if(!alvo)return;sessionStorage.removeItem('painel-reabrir');
 const i=DATA.os.findIndex(o=>o.pasta===alvo);if(i>=0)abre(i)})();
// Auto-refresh: o servidor expõe /api/estado com um carimbo da última mudança
// nos memory.md — inclusive as gravadas pelo sync da extensão Chrome do DET.
// Quando o carimbo muda, a página recarrega sozinha (o GET / regenera o
// painel), preservando o card aberto. Só no modo interativo (http local).
if(ATIVO){let carimbo=null;
 setInterval(async()=>{try{
  const r=await fetch('/api/estado');const j=await r.json();
  if(!j.ok||j.estado==null)return;
  if(carimbo===null){carimbo=j.estado;return}
  if(j.estado===carimbo)return;
  carimbo=j.estado;
  const a=document.activeElement; // não derruba o AFT no meio de uma digitação
  if(a&&(a.tagName==='INPUT'||a.tagName==='TEXTAREA'))return;
  if(P.classList.contains('aberto')&&ABERTA)sessionStorage.setItem('painel-reabrir',ABERTA);
  location.reload();
 }catch(e){}},4000)}
// ---- Calendário de trabalho (diário de atividades) --------------------------
// Dados: DATA.diario = entradas {d (ISO), emp, os (pasta), t (letras A-F),
// acao, det, auto (gancho automático), arq (OS arquivada)}. As letras seguem
// a tela 2.1 do RI; ver /aft-diario e _scripts/diario_registrar.py.
const DIARIO=DATA.diario||[];
const TIPOS_ROT={A:'Preparação/planejamento da fiscalização',B:'Início da fiscalização',
 C:'Inspeção/auditoria/entrevista no estabelecimento',
 D:'Análise de documentos fora do estabelecimento',
 E:'Elaboração de documentos / lançamento em sistemas',F:'Fim da fiscalização'};
const MESES=['janeiro','fevereiro','março','abril','maio','junho','julho',
 'agosto','setembro','outubro','novembro','dezembro'];
const porDia={};DIARIO.forEach(e=>{(porDia[e.d]=porDia[e.d]||[]).push(e)});
let calAno,calMes,calSel=null;
(function(){const h=(DATA.hoje||'').split('-');calAno=+h[0]||2026;calMes=(+h[1]||1)-1;
 try{const j=JSON.parse(sessionStorage.getItem('painel-cal')||'null');
  if(j){if(j.ano)calAno=j.ano;if(j.mes!=null)calMes=j.mes;calSel=j.sel||null}}catch(e){}})();
function salvaCal(){sessionStorage.setItem('painel-cal',
 JSON.stringify({ano:calAno,mes:calMes,sel:calSel}))}
function mudaVista(v){
 document.getElementById('vista-painel').style.display=v==='cal'?'none':'';
 document.getElementById('vista-cal').style.display=v==='cal'?'':'none';
 document.getElementById('aba-painel').classList.toggle('ativa',v!=='cal');
 document.getElementById('aba-cal').classList.toggle('ativa',v==='cal');
 sessionStorage.setItem('painel-vista',v);
 if(v==='cal')desenhaCal()}
function calNav(n){calMes+=n;if(calMes<0){calMes=11;calAno--}
 if(calMes>11){calMes=0;calAno++}salvaCal();desenhaCal()}
function calHoje(){const h=(DATA.hoje||'').split('-');calAno=+h[0];calMes=+h[1]-1;
 calSel=DATA.hoje;salvaCal();desenhaCal()}
function isoDe(a,m,d){return a+'-'+String(m+1).padStart(2,'0')+'-'+String(d).padStart(2,'0')}
function calSelDia(a,m,d){calSel=isoDe(a,m,d);salvaCal();desenhaCal()}
function resumoLetras(es){const s=new Set();
 es.forEach(e=>(e.t||'').split('').forEach(l=>s.add(l)));
 return [...s].sort().join('·')}
function desenhaCal(){
 const alvo=document.getElementById('vista-cal');if(!alvo)return;
 const ini=new Date(calAno,calMes,1).getDay(); // 0 = domingo
 const nDias=new Date(calAno,calMes+1,0).getDate();
 const chaveMes=calAno+'-'+String(calMes+1).padStart(2,'0');
 const diasTrab=new Set(DIARIO.filter(e=>e.d.slice(0,7)===chaveMes).map(e=>e.d)).size;
 let h='<div class="cal-topo"><h2>'+MESES[calMes]+' de '+calAno+'</h2>'+
  '<button class="mini" onclick="calNav(-1)">‹ anterior</button>'+
  '<button class="mini" onclick="calNav(1)">próximo ›</button>'+
  '<button class="mini" onclick="calHoje()">hoje</button>'+
  '<span class="cal-cont"><b>'+diasTrab+'</b> dia'+(diasTrab===1?'':'s')+
  ' trabalhado'+(diasTrab===1?'':'s')+' neste mês</span></div>';
 h+='<div class="cal-wrap"><div><div class="cal-grade">';
 h+='<div class="cal-sem">'+['dom','seg','ter','qua','qui','sex','sáb']
  .map(d=>'<span>'+d+'</span>').join('')+'</div><div class="cal-corpo">';
 const antes=new Date(calAno,calMes,0).getDate();
 for(let i=0;i<ini;i++)
  h+='<div class="cal-dia fora"><span class="n">'+(antes-ini+1+i)+'</span></div>';
 for(let d=1;d<=nDias;d++){
  const iso=isoDe(calAno,calMes,d),es=porDia[iso]||[];
  const dow=new Date(calAno,calMes,d).getDay(),fds=dow===0||dow===6;
  const cls=['cal-dia'];if(fds)cls.push('fds');
  if(iso===DATA.hoje)cls.push('hoje');if(iso===calSel)cls.push('sel');
  if(!es.length&&!fds&&iso<DATA.hoje)cls.push('vago');
  const por={};es.forEach(e=>{(por[e.emp]=por[e.emp]||[]).push(e)});
  const emps=Object.keys(por);let evs='';
  emps.slice(0,3).forEach(emp=>{const g=por[emp],letras=resumoLetras(g);
   evs+='<div class="cal-ev'+(g.every(e=>e.auto)?' auto':'')+'">'+
    '<span class="pt-ev"></span>'+esc(emp.slice(0,22))+
    (letras?' <b>'+letras+'</b>':'')+'</div>'});
  if(emps.length>3)evs+='<div class="cal-mais">+'+(emps.length-3)+' empresa(s)</div>';
  h+='<div class="'+cls.join(' ')+'" onclick="calSelDia('+calAno+','+calMes+','+d+')">'+
   '<span class="n">'+d+'</span>'+evs+'</div>'}
 const resto=(7-(ini+nDias)%7)%7;
 for(let i=1;i<=resto;i++)
  h+='<div class="cal-dia fora"><span class="n">'+i+'</span></div>';
 h+='</div></div>';
 h+='<div class="cal-legenda">'+Object.keys(TIPOS_ROT).map(l=>
  '<span><b>'+l+'</b> '+esc(TIPOS_ROT[l])+'</span>').join('')+
  '<span><span class="pt-ev"></span> dia anotado sozinho, sem classificação · '+
  'pontilhado = dia útil sem registro</span></div></div>';
 h+=ladoCal();
 alvo.innerHTML=h+'</div>'}
function ladoCal(){
 let h='<div class="cal-lado"><h3>Dia selecionado</h3>';
 if(!calSel)h+='<p class="vazio">clique num dia do calendário</p>';
 else{const p=calSel.split('-');
  h+='<h2>'+(+p[2])+' de '+MESES[+p[1]-1]+'</h2>';
  const es=porDia[calSel]||[];
  if(!es.length)h+='<p class="vazio">nenhum trabalho registrado neste dia</p>';
  else{const por={};es.forEach(e=>{(por[e.emp]=por[e.emp]||[]).push(e)});
   for(const emp in por){
    h+='<div class="cal-item"><div class="emp">'+esc(emp)+
     (por[emp][0].arq?' <span class="selo">OS arquivada</span>':'')+'</div>';
    por[emp].forEach(e=>{
     const tags=(e.t||'').split('').filter(Boolean).map(l=>
      '<span class="tipo-tag">'+l+' · '+esc(TIPOS_ROT[l]||'')+'</span>').join('');
     h+='<div class="tipos">'+(tags||'<span class="tipo-tag gen">'+
      (e.auto?'anotado sozinho, sem classificação':'sem classificação')+'</span>')+'</div>';
     if(e.acao&&!e.auto)h+='<div class="txt">'+esc(e.acao)+
      (e.det?' — '+esc(e.det):'')+'</div>'});
    h+='</div>'}}}
 if(ATIVO)h+=formCal();
 return h+'</div>'}
function formCal(){
 const oss=DATA.os.filter(o=>o.pasta);if(!oss.length)return '';
 const base=calSel||DATA.hoje||'';
 const dbr=base?base.split('-').reverse().join('/'):'';
 return '<div class="cal-form"><h3>Registrar dia trabalhado</h3>'+
  '<label>auditoria</label><select id="cal-os">'+oss.map(o=>
   '<option value="'+esc(o.pasta)+'">'+esc(o.empregador)+'</option>').join('')+'</select>'+
  '<label>data</label><input type="text" id="cal-data" value="'+esc(dbr)+'">'+
  '<label>atividades (cumulativas)</label><div class="cal-tipos">'+
  Object.keys(TIPOS_ROT).map(l=>'<label><input type="checkbox" class="cal-tp" value="'+l+
   '"> <b>'+l+'</b> '+esc(TIPOS_ROT[l])+'</label>').join('')+'</div>'+
  '<label>detalhe (opcional)</label>'+
  '<input type="text" id="cal-det" placeholder="ex.: análise do PGR">'+
  '<button class="mini" style="margin:10px 0 0" onclick="calRegistrar()">registrar</button></div>'}
function calRegistrar(){
 const pasta=document.getElementById('cal-os').value;
 const data=(document.getElementById('cal-data').value||'').trim();
 const tipos=[...document.querySelectorAll('.cal-tp:checked')].map(c=>c.value).join('');
 const det=(document.getElementById('cal-det').value||'').trim();
 if(!tipos){aviso('Marque pelo menos uma atividade (A-F)');return}
 if(!/^[0-9]{2}[/][0-9]{2}[/][0-9]{4}$/.test(data)){aviso('Data no formato dd/mm/aaaa');return}
 api({acao:'atividade',pasta:pasta,texto:det,data:data,tipos:tipos},true)}
// Ordem dos cards. A grade nasce por data de criação da auditoria; a opção
// "prazo de DET" só reposiciona os mesmos cards (cada um carrega a sua posição
// em data-det), sem regerar a página. A escolha vale para as próximas aberturas.
function ordena(v){
 document.querySelectorAll('.grid .card').forEach(c=>{
  c.style.order=v==='det'?(c.dataset.det||0):''});
 localStorage.setItem('painel-ordem',v)}
(function(){const sel=document.getElementById('ordem');if(!sel)return;
 const v=localStorage.getItem('painel-ordem')||'criada';
 sel.value=v;ordena(v)})();
// Restaura a vista (Auditorias | Calendário) escolhida antes do reload.
(function(){if(sessionStorage.getItem('painel-vista')==='cal')mudaVista('cal')})();
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


def det_cobra_acao(d: dict) -> bool:
    """Notificação que ainda pesa sobre o AFT: não checada e não cancelada.
    Cancelada pelo auditor no DET (status 2) não tem efeito legal nenhum — não
    conta prazo, não colore card, não vai para a agenda do Google Calendar."""
    return not d["feito"] and not d.get("cancelada")


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
    if d.get("cancelada"):
        return "cancelada", "cancelada no DET"
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
    DET com prazo (abertas e checadas — as checadas servem ao /aft-agenda-det, que
    marca ✓ no Google Calendar) e pendências datadas (só as com "prazo <data>"
    no texto; datas soltas — ex. "apólice vencida em 31/05/2025" — não são
    vencimento da pendência). O título dos eventos DET segue a convenção
    'DET <código> <12 primeiros caracteres do empregador>'."""
    itens = []
    for o in oss:
        emp12 = o["empregador"][:12].strip()
        for d in o["dets"]:
            # Cancelada no DET não vira compromisso nem evento de calendário.
            if not d["prazo"] or d.get("cancelada"):
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


def ler_sidecar_diario(pasta: Path) -> list[str]:
    """Datas ISO anotadas pelo gancho automático do diário (1 por dia)."""
    arq = pasta / SIDECAR_DIARIO
    if not arq.exists():
        return []
    datas = []
    try:
        for linha in arq.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                d = (json.loads(linha) or {}).get("data") or ""
            except json.JSONDecodeError:
                continue
            if RE_DATA_ISO.fullmatch(d):
                datas.append(d)
    except OSError:
        return []
    return datas


def coletar_diario(oss: list[dict], base: Path, hoje: datetime.date) -> list[dict]:
    """DIÁRIO DE ATIVIDADES consolidado, para a aba Calendário: uma entrada por
    (dia, OS, linha do Registro de atividades), com as letras [A-F] da tela 2.1
    do RI. Inclui TODAS as OS de OS ATIVAS (mesmo encerradas — calendário é
    histórico) e também OS ARQUIVADAS (OS arquivada no meio do mês não pode
    sumir da agenda mensal). O sidecar do gancho (.diario-auto.jsonl) entra
    como "dia trabalhado sem classificação" apenas nos dias em que a OS não tem
    linha registrada na tabela."""
    piso = hoje - datetime.timedelta(days=DIARIO_JANELA_DIAS)
    fontes = [(o, False) for o in oss]
    arq_dir = base.parent / "OS ARQUIVADAS"
    if arq_dir.exists():
        for mem in sorted(arq_dir.glob("*/memory.md")):
            try:
                fontes.append((parse_memory(mem), True))
            except Exception:
                continue  # ficha arquivada ruim não derruba o painel
    entradas = []
    for o, arquivada in fontes:
        emp = o.get("empregador") or o.get("pasta") or "?"
        pasta = o.get("pasta") or ""
        dias_na_tabela = set()
        for a in o.get("atividades") or []:
            d = parse_data(a["data"])
            if not d or d < piso or d > hoje + datetime.timedelta(days=60):
                continue
            dias_na_tabela.add(d.isoformat())
            entradas.append({"d": d.isoformat(), "emp": emp, "os": pasta,
                             "ri": o.get("ri") or "",
                             "t": a.get("tipos") or "", "acao": a["acao"],
                             "det": datas_para_br(a.get("detalhe") or ""),
                             "auto": False, "arq": arquivada})
        try:
            datas_auto = ler_sidecar_diario(Path(o["caminho"]))
        except Exception:
            datas_auto = []
        for d_iso in sorted(set(datas_auto)):
            d = parse_data(d_iso)
            if not d or d < piso or d_iso in dias_na_tabela:
                continue
            entradas.append({"d": d_iso, "emp": emp, "os": pasta,
                             "ri": o.get("ri") or "",
                             "t": "", "acao": "trabalho na auditoria (anotado sozinho)",
                             "det": "", "auto": True, "arq": arquivada})
    entradas.sort(key=lambda e: (e["d"], e["emp"].lower()))
    return entradas


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
            # E-mails redigidos (email.md): texto que o AFT vai mandar para
            # fora — idem, nunca no Artifact publicado.
            "emails": (o.get("emails") or []) if com_pasta else [],
            "dets": [{"codigo": d["codigo"], "feito": d["feito"],
                      "linha": datas_para_br(d["linha"]),
                      "rotulo": d.get("rotulo") or "",
                      "notas": datas_para_br(d.get("notas") or ""),
                      "lavrada": d["lavrada"].strftime("%d/%m/%Y") if d.get("lavrada") else "",
                      "ciencia": d["ciencia"].strftime("%d/%m/%Y") if d.get("ciencia") else "",
                      "prox_entrega": d["prazo"].strftime("%d/%m/%Y") if d["prazo"] else "",
                      "ultima_entrega": d["ultima_entrega"].strftime("%d/%m/%Y") if d.get("ultima_entrega") else "",
                      "pendente": bool(d.get("atualizacao_pendente")),
                      "mensagem": bool(d.get("mensagem_canal")),
                      "cancelada": bool(d.get("cancelada")),
                      "aguarda": bool(d.get("aguardando_ciencia")),
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
                            "tipos": a.get("tipos") or "",
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


def render_pendencias(oss: list[dict]) -> str:
    """Bloco 'Pendências por auditoria', abaixo dos vencimentos: TODAS as
    pendências em aberto ([ ] do ## Pendências do memory.md), agrupadas por
    OS na mesma ordem dos cards. É o destino do aviso semanal de segunda
    (notificar_pendencias.py) — a notificação traz só os números, a lista
    completa mora aqui."""
    grupos = []
    for o in oss:
        pend = o.get("pendencias") or []
        if not pend:
            continue
        lis = "".join(f"<li>◻ {html.escape(datas_para_br(p))}</li>" for p in pend)
        grupos.append(f"<p><b>{html.escape(o['empregador'])}</b></p>"
                      f'<ul class="lista">{lis}</ul>')
    if not grupos:
        return ""
    total = sum(len(o.get("pendencias") or []) for o in oss)
    return (f'<div class="venc"><h3>Pendências por auditoria '
            f'<span style="float:right">{total}</span></h3>'
            + "".join(grupos) + "</div>")


def render_miolo(oss, hoje, n_venc, n_urg, n_novas, n_autos, venc, diario,
                 com_pasta: bool, artifact: bool) -> str:
    cards = []
    for i, o in enumerate(oss):
        classe, rotulo = badge_os(o, hoje)
        chips = "".join(f'<span class="chip">{html.escape(nr)}</span>' for nr in o["nrs"])
        if o["embargo"]:
            chips += f'<span class="chip emb">⛔ {html.escape(o["embargo"][:42])}</span>'
        # Cancelada no DET nao conta como aberta nem carrega alerta: ela nao
        # cobra nada do AFT (mesma regra do detalhe, ver det_cobra_acao).
        dets_abertos = sum(1 for d in o["dets"] if det_cobra_acao(d))
        vivas = [d for d in o["dets"] if not d.get("cancelada")]
        # Mensagem do empregador no canal de comunicacao (envelope laranja do
        # DET): aviso de primeira linha, tao acionavel quanto o triangulo, e
        # antes so aparecia ao abrir a OS. Vem primeiro por exigir resposta.
        n_msg = sum(1 for d in vivas if d.get("mensagem_canal"))
        msg_selo = ('\n  <div class="msg-card" title="mensagem do empregador no canal '
                    'de comunicacao do DET, aguardando resposta sua">✉️ mensagem no DET'
                    + (f' · {n_msg}' if n_msg > 1 else '') + '</div>') if n_msg else ""
        pend = any(d.get("atualizacao_pendente") for d in vivas)
        pend_selo = ('\n  <div class="pend-card">⚠️ atualização pendente</div>'
                     if pend else "")
        cards.append(f"""
<div class="card {classe}" data-det="{o.get('ord_det', i)}" onclick="abre({i})">
  <h2>{html.escape(o["empregador"])}</h2>
  <div class="meta">{html.escape(fmt_cnpj(o["cnpj"]) if o["cnpj"] else "CNPJ/CPF não informado")}{(" · " + html.escape(o["municipio"])) if o["municipio"] else ""}</div>
  <span class="badge {classe}">{html.escape(rotulo)}</span>
  <div class="chips">{chips}</div>
  <div class="rodape-card">
    <span>{len(o["autos"])} auto(s) · {dets_abertos} DET(s) aberto(s)</span>
    <span>{html.escape(dias_humano(o["data_inicio"], hoje))}</span>
  </div>{msg_selo}{pend_selo}
</div>""")

    grade = ("".join(cards) if cards else
             '<div class="aviso-vazio">Nenhuma OS encontrada em OS ATIVAS. '
             'Use /aft-nova-auditoria para cadastrar a primeira.</div>')
    # Sem com_pasta (Artifact publicado), o nome da pasta sai também do diário.
    diario_pub = diario if com_pasta else [{**e, "os": ""} for e in diario]
    dias_mes = len({e["d"] for e in diario if e["d"][:7] == hoje.strftime("%Y-%m")})
    dados = {"os": montar_json_os(oss, hoje, com_pasta), "venc": venc,
             "diario": diario_pub, "hoje": hoje.isoformat()}
    json_js = json.dumps(dados, ensure_ascii=False).replace("</", "<\\/")
    titulo_art = "<title>Painel AFT</title>\n" if artifact else ""
    rodape = ("AFT Toolkit · painel publicado como artefato · snapshot de "
              f"{hoje.strftime('%d/%m/%Y')} · regenere com a skill /aft-painel."
              if artifact else
              "AFT Toolkit · painel local · aberto pelo arquivo é somente "
              "leitura; pelo modo interativo (http://127.0.0.1:8347, via "
              "servir_painel.py) os cards ganham ações — ver skill /aft-painel.")
    return f"""{titulo_art}<style>{CSS}</style>
<h1>Painel <em>AFT</em></h1>
<p class="sub">Gerado em {hoje.strftime("%d/%m/%Y")} a partir das fichas locais (memory.md) · clique num card para o detalhe da auditoria</p>
<div class="abas">
  <button id="aba-painel" class="aba ativa" onclick="mudaVista('painel')">Auditorias</button>
  <button id="aba-cal" class="aba" onclick="mudaVista('cal')">Calendário</button>
</div>
<div id="vista-painel">
<div class="contadores">
  <div class="contador"><b>{len(oss)}</b><span>OS ativas</span></div>
  <div class="contador{' alerta' if n_venc else ''}"><b>{n_venc}</b><span>DETs vencidos</span></div>
  <div class="contador{' alerta' if n_urg else ''}"><b>{n_urg}</b><span>vencendo em ≤ 7 dias</span></div>
  <div class="contador{' alerta' if n_novas else ''}"><b>{n_novas}</b><span>notif. sem registro</span></div>
  <div class="contador"><b>{n_autos}</b><span>autos lavrados</span></div>
  <div class="contador"><b>{dias_mes}</b><span>dias trabalhados no mês</span></div>
</div>
<div class="ordena">
  <label for="ordem">ordenar por</label>
  <select id="ordem" onchange="ordena(this.value)">
    <option value="criada">auditoria mais recente</option>
    <option value="det">prazo de DET mais urgente</option>
  </select>
</div>
<div class="grid">{grade}</div>
{render_vencimentos(venc)}
{render_pendencias(oss)}
</div>
<div id="vista-cal" style="display:none"></div>
<div id="veu"></div><div id="detalhe"></div>
<footer>{rodape}</footer>
<script>const DATA={json_js};{JS}</script>
"""


def render_html(oss, hoje, n_venc, n_urg, n_novas, n_autos, venc, diario) -> str:
    miolo = render_miolo(oss, hoje, n_venc, n_urg, n_novas, n_autos, venc, diario,
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
            # Momento em que a OS entrou no painel = criação do memory.md
            # (st_birthtime no macOS; no Windows st_ctime é a criação).
            try:
                st = mem.stat()
                criado_em = getattr(st, "st_birthtime", None) or st.st_ctime
            except OSError:
                criado_em = 0.0
            try:
                oss.append(parse_memory(mem) | {"criado_em": criado_em})
            except Exception as e:  # uma OS ruim não derruba o painel
                oss.append({
                    "criado_em": criado_em,
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
    oss_todas = list(oss)  # diário/calendário é histórico: inclui encerradas
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
        # E-mails redigidos pela /aft-email (idem: só na versão local).
        os_["emails"] = parse_emails(Path(os_["caminho"]))
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
        prazos = [d["prazo"] for d in os_["dets"] if d["prazo"] and det_cobra_acao(d)]
        os_["prazo_top"] = min(prazos) if prazos else None
        os_["dias_top"] = (os_["prazo_top"] - hoje).days if prazos else None
        os_["classe"] = classifica(os_["dias_top"])
        for d in os_["dets"]:
            if d["prazo"] and det_cobra_acao(d):
                dd = (d["prazo"] - hoje).days
                if dd < 0:
                    n_vencidos += 1
                elif dd <= 7:
                    n_urgentes += 1

    # Ordem padrão dos cards: auditoria criada mais recentemente primeiro.
    # (Até 10/08/2026 era por urgência de DET; hoje a urgência é a outra opção
    # do seletor "ordenar por", e a agenda do rodapé continua cobrindo prazos.)
    for os_ in oss:
        os_["criada"] = data_criacao(os_, os_.get("criado_em", 0.0))
    oss.sort(key=lambda o: (-o["criada"].toordinal(),
                            -o.get("criado_em", 0.0),
                            (o["empregador"] or "").lower()))

    # Posição de cada OS na ordem por urgência de DET: prazo aberto mais
    # próximo de vencer (ou já vencido) primeiro; OS sem prazo aberto no fim,
    # preservando entre elas a ordem por criação. O seletor do painel troca de
    # uma para a outra sem regerar a página.
    por_det = sorted(range(len(oss)),
                     key=lambda k: (oss[k]["prazo_top"] is None,
                                    oss[k]["prazo_top"] or datetime.date.max, k))
    for pos, k in enumerate(por_det):
        oss[k]["ord_det"] = pos

    venc = coletar_vencimentos(oss, hoje)
    diario = coletar_diario(oss_todas, base, hoje)
    dias_mes = len({e["d"] for e in diario if e["d"][:7] == hoje.strftime("%Y-%m")})

    html_out = render_html(oss, hoje, n_vencidos, n_urgentes, n_novas, n_autos,
                           venc, diario)
    destino = saida_html(base)
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(html_out, encoding="utf-8")

    destino_art = saida_artifact()
    if destino_art:
        destino_art.parent.mkdir(parents=True, exist_ok=True)
        destino_art.write_text(
            render_miolo(oss, hoje, n_vencidos, n_urgentes, n_novas, n_autos, venc,
                         diario, com_pasta=False, artifact=True),
            encoding="utf-8")

    # Resumo no stdout (a skill /aft-painel usa isto para responder em texto).
    resumo = {
        "painel": str(destino),
        "artifact_html": str(destino_art) if destino_art else None,
        "os_ativas": len(oss),
        "os_encerradas_ocultas": 0 if quer_todas() else n_encerradas,
        "dets_vencidos": n_vencidos,
        "dets_vencendo_7d": n_urgentes,
        "notificacoes_nao_cadastradas": n_novas,
        "autos_lavrados": n_autos,
        "dias_trabalhados_no_mes": dias_mes,
        "scan_ao_vivo": {"pedido": scan, "os_com_scan_ok": n_scan_ok},
        # Agenda consolidada de prazos (DETs — inclusive checados, para o
        # /aft-agenda-det marcar ✓ no calendário — e pendências datadas).
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
