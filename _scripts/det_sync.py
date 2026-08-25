#!/usr/bin/env python3
"""
det_sync.py — sincroniza as notificações do DET com os memory.md locais.

É o espelho local do sync do SisOS (extensão Chrome "SisOS — Sync DET"):
a extensão captura o token de sessão do DET no navegador do AFT e o entrega
ao servir_painel.py (endpoint POST /api/det-sync), que chama este módulo.

Para cada OS de OS ATIVAS/ com CNPJ/CPF (ou RI no front-matter), consulta a
API oficial do DET (a MESMA que o site usa, com o token do próprio AFT):

    POST https://auditor-det.sit.trabalho.gov.br/services/auditor/v1/notificacoes/pesquisa

e aplica o resultado na seção `## Notificações DET` do memory.md:
  - notificação nova (código ainda não registrado) → acrescenta
    `- [ ] <CODIGO> — prazo <dd/mm/aaaa>`;
  - prazo de entrega que mudou no DET → atualiza a data na linha existente
    (preservando o formato da linha — dd/mm/aaaa ou aaaa-mm-dd);
  - sob cada checkbox, mantém uma SUB-LINHA DE DETALHES gerada do DET
    (`  - lavrada dd/mm/aaaa · ciência dd/mm/aaaa · última entrega
    dd/mm/aaaa · Confirmada[ · ⚠️ atualização pendente]`) — essa linha
    pertence ao sync: é criada se faltar e regravada quando o DET mudar.
    A flag final espelha o triângulo amarelo do DET (campo itemAtualizado
    da API). O gerar_painel a ignora (ele só lê linhas checkbox);
  - `ri:` vazio no front-matter → preenche (ver ris_conhecidos/ri_mais_recente).

Filtros, nesta ordem:
  1. CONFIRMADAS (status=1) e com data de lavratura — igual ao SisOS;
  2. da(s) fiscalização(ões) DESTA OS, pelo RI: o `ri:` do FRONT-MATTER é o
     identificador canônico da auditoria — só entra notificação daquele(s)
     RI(s) (aceita mais de um no campo, separados por vírgula). A pesquisa é
     por empregador, então o DET devolve também notificações de fiscalizações
     antigas do mesmo CNPJ; sem este filtro elas entram na OS errada.
     Notificação de RI alheio nunca é importada nem descartada em silêncio:
     volta em `ignoradas_detalhe`. Ver "Vínculo notificação × OS".

Alerta "⚠️ atualização pendente" (campo itemAtualizado da API): ESPELHA o DET —
aparece enquanto a API disser true e some quando ela disser false. Não há
dispensa por clique (havia até 25/08/2026; o AFT a vetou depois de apagar sem
querer o alerta de uma pendência viva). Quem apaga o triângulo é o próprio DET,
quando a notificação é aberta lá — o /aft-det-baixar faz isso ao baixar.

O estado do checkbox ([ ]/[x]) NUNCA é alterado — respondida é decisão do AFT.
Cada memory.md alterado recebe backup prévio (backup_arquivo.py) e uma linha
no Registro de atividades. O token é usado em memória e nunca gravado.

Variável de ambiente AFT_DET_DRYRUN=1: consulta o DET e devolve o relatório
completo, mas não grava nada — útil para conferir antes de deixar escrever.

Uso normal: via servir_painel.py. Direto (debug):
    python det_sync.py "<PASTA_OS_ATIVAS>" "<token>"
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
import json
import re
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

AQUI = Path(__file__).resolve().parent
BACKUP = AQUI / "backup_arquivo.py"

DET_API = ("https://auditor-det.sit.trabalho.gov.br"
           "/services/auditor/v1/notificacoes/pesquisa")
DET_ITENS = ("https://auditor-det.sit.trabalho.gov.br"
             "/services/auditor/v1/itens-notificacao")
DET_TIMEOUT = 12  # segundos por OS (igual ao SisOS)

# Tradução do nº de status de cada item (coluna "Status" da tela do DET) para
# texto legível. É o MESMO enum do det_baixar (uma fonte só — regra "uma
# informação, um lugar" do AGENTS.md); importado de lá. Sem ele, o resumo por
# item é simplesmente omitido (best-effort).
try:
    from det_baixar import STATUS_ITEM
except Exception:  # standalone sem o sibling no path, ou falha de import
    STATUS_ITEM = {}

RE_FM = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
RE_CHECKBOX = re.compile(r"^\s*-\s*\[[ xX]?\]\s*(.*)$")
RE_CODIGO = re.compile(r"([A-Z0-9]{6,})")
# Data de prazo numa linha de DET (mesma detecção do gerar_painel).
RE_PRAZO_LINHA = re.compile(
    r"((?:prazo|entrega\s+at[eé])[:\s]+)(\d{2}/\d{2}/\d{4}|\d{4}-\d{2}-\d{2})",
    re.IGNORECASE)
# Sub-linha de detalhes mantida pelo sync (sempre começa com "  - lavrada").
RE_DETALHE = re.compile(r"^\s+-\s+lavrada\s", re.IGNORECASE)


# ── Chamada à API do DET ─────────────────────────────────────────────────────

def consultar_det(token: str, cnpj: str, ri: str) -> list[dict]:
    """Notificações do DET para um empregador (CNPJ/CPF) ou RI.
    Mesmo corpo de pesquisa do SisOS. Lança RuntimeError em falha."""
    corpo = {
        "isPesquisaPadrao": False,
        "niEmpregador": cnpj or None,
        "ri": None if cnpj else (ri or None),
        "codigoNotificacao": None,
        "cifAuditor": None,
        "isSomenteMinhas": True,
        "sequencia": 0,
        "ordenacaoCampo": "id",
        "ordenacaoDesc": False,
        "isPendenciaComunicacaoAuditor": False,
        "isPendenciaComunicacaoEmpregador": False,
        "situacaoFisc": None,
    }
    req = urllib.request.Request(
        DET_API,
        data=json.dumps(corpo).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json, text/plain, */*",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=DET_TIMEOUT) as resp:
            dados = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detalhe = e.read().decode("utf-8", errors="replace")[:200]
        raise RuntimeError(f"DET API {e.code}: {detalhe}") from e
    except Exception as e:
        raise RuntimeError(f"DET inacessível: {e}") from e
    return dados.get("notificacoes") or []


def snippet_canal(token: str, uid: str) -> str:
    """Última mensagem do EMPREGADOR no canal de comunicação da notificação,
    resumida (90 chars) para a sub-linha da ficha. Best-effort: qualquer
    falha devolve '' — o envelope continua aparecendo sem o texto."""
    base = "https://auditor-det.sit.trabalho.gov.br/services/auditor/v1"
    req = urllib.request.Request(
        f"{base}/notificacoes/{uid}/canal-comunicacao",
        headers={"Authorization": f"Bearer {token}",
                 "Accept": "application/json, text/plain, */*"})
    try:
        with urllib.request.urlopen(req, timeout=DET_TIMEOUT) as resp:
            canal = json.loads(resp.read().decode("utf-8"))
    except Exception:
        return ""
    registros = canal if isinstance(canal, list) else next(
        (v for v in (canal or {}).values()
         if isinstance(v, list) and v and isinstance(v[0], dict)), [])
    texto = ""
    for reg in registros:
        if (reg.get("tipoRegistroComunicacao") in (None, "M")
                and reg.get("tipoUsuarioEmissor") == "E" and reg.get("texto")):
            texto = reg["texto"]  # fica com a última (a lista vem cronológica)
    texto = re.sub(r"\s+", " ", texto).replace('"', "'").strip()
    if len(texto) > 90:
        texto = texto[:90]
        if " " in texto:
            texto = texto.rsplit(" ", 1)[0]
        texto += "…"
    return texto


def codigos_abertos(texto: str) -> set[str]:
    """Códigos das notificações ainda EM ABERTO (`- [ ]`) na seção
    `## Notificações DET` da ficha.

    É o gate do resumo de itens: enquanto o AFT não marcar a notificação como
    respondida, o status dos itens interessa — independentemente do triângulo
    amarelo, que ele pode ter dispensado no painel ou apagado ao abrir a
    notificação no DET (ver resumo_itens). Só a seção do DET é varrida: a de
    Pendências também tem checkboxes, e um texto em maiúsculas ali poderia
    passar por código de notificação."""
    linhas = texto.splitlines()
    ini = next((i + 1 for i, l in enumerate(linhas)
                if l.strip().startswith("## ")
                and l.strip()[3:].strip() in ("Notificações DET",
                                              "Notificacoes DET")), -1)
    if ini < 0:
        return set()
    fim = next((i for i in range(ini, len(linhas))
                if linhas[i].strip().startswith("## ")), len(linhas))
    abertos = set()
    for l in linhas[ini:fim]:
        m = re.match(r"^\s*-\s*\[([ xX]?)\]\s*(.*)$", l)
        if not m or m.group(1).lower() == "x":
            continue
        cod = RE_CODIGO.match(m.group(2).strip())
        if cod:
            abertos.add(cod.group(1))
    return abertos


def resumo_itens(token: str, uid: str) -> str:
    """Resumo do status de cada item de uma notificação, para a sub-linha da
    ficha — o que está por trás do triângulo amarelo (quantos itens aguardam a
    avaliação do AFT, quantos foram entregues, etc.).

    UMA requisição a /itens-notificacao: cada item já traz o campo `status`
    (o mesmo número da coluna "Status" da tela do DET — verificado na API em
    24/08/2026, notificação da BUENO 28: item com status 4 == "Prazo
    Solicitado" na tela). Não é preciso varrer /eventos-item por item.

    Best-effort: qualquer falha (ou o enum ausente) devolve '' — a sub-linha
    continua aparecendo sem o resumo. Devolve algo como
    'itens: 5 aguardando avaliação de prazo' ou
    'itens: 3 aguardando avaliação de prazo, 1 recebido, 1 enviado'."""
    if not STATUS_ITEM:
        return ""
    req = urllib.request.Request(
        f"{DET_ITENS}?uidNotificacao={uid}",
        headers={"Authorization": f"Bearer {token}",
                 "Accept": "application/json, text/plain, */*"})
    try:
        with urllib.request.urlopen(req, timeout=DET_TIMEOUT) as resp:
            itens = json.loads(resp.read().decode("utf-8"))
    except Exception:
        return ""
    if not isinstance(itens, list) or not itens:
        return ""
    # Conta por status, na ordem em que os status aparecem (saída estável).
    contagem: dict[int, int] = {}
    for it in itens:
        st = it.get("status")
        contagem[st] = contagem.get(st, 0) + 1
    partes = []
    for st, qtd in sorted(contagem.items(),
                          key=lambda kv: (kv[0] is None, kv[0])):
        # Rótulo sem "status N" cru: um número solto poderia colidir com a
        # deteção de "status 2" (cancelada) do gerar_painel. Status conhecido
        # nunca cai no fallback; desconhecido vira "outros". Tira o prefixo
        # "Item " ("Item enviado" → "enviado") para o resumo não ficar clunky.
        rot = re.sub(r"^item\s+", "", (STATUS_ITEM.get(st) or "outros"),
                     flags=re.IGNORECASE).lower()
        partes.append(f"{qtd} {rot}")
    total = sum(contagem.values())
    # Vírgula entre os grupos (nunca ' · ': esse é o separador da sub-linha).
    return f"itens: {', '.join(partes)}" if partes else ""


# Status da notificação no DET. Os três valores são os do enum do próprio
# DET, lidos do código do site em 19/08/2026 (chunk 251 do front Angular):
#   0 EM_ELABORACAO ("ainda em elaboração")
#   1 CONFIRMADA    ("enviada para o empregador")
#   2 CANCELADA     ("cancelada pelo auditor")
# Confere com o caso MENINA TEIMOSA: a notificação que a tela do DET mostra
# como "Cancelada" era a que a ficha registrava como `status 2`.
STATUS_CONFIRMADA = 1
STATUS_CANCELADA = 2


def _flag(valor) -> bool:
    """Booleano da API, tolerante a string ('false'/'N' são falsos)."""
    if isinstance(valor, str):
        return valor.strip().lower() in ("true", "s", "sim", "1")
    return bool(valor)


def elegiveis(notificacoes: list[dict]) -> list[dict]:
    """Toda notificação LAVRADA (com dataEnvio) entra — inclusive as que ainda
    aguardam ciência do empregador (que pode demorar até 15 dias, com ciência
    tácita). A existência da notificação é fato relevante para o painel desde a
    lavratura; o estado real (Confirmada / aguardando ciência / status N) vai
    na sub-linha de detalhes e é atualizado a cada sync. (O SisOS filtra por
    status=1 — Confirmada —; aqui o filtro foi relaxado de propósito para o
    painel local refletir a NAD recém-lavrada.)"""
    return [n for n in notificacoes if n.get("dataEnvio")]


# ── Vínculo notificação × OS (o filtro que importa) ─────────────────────────
#
# A pesquisa no DET é por CNPJ/CPF do EMPREGADOR, e devolve as notificações de
# TODAS as fiscalizações já feitas naquele empregador — inclusive as de anos
# anteriores, já concluídas. O que amarra uma notificação a ESTA OS é o RI
# (Relatório de Inspeção), presente em cada notificação.
#
# REGRA (decidida em 22/07/2026, caso CONSORCIO SQ, RI alheio 319969819): o
# `ri:` do FRONT-MATTER é O identificador canônico da auditoria — só entra
# notificação cujo RI esteja nele. Nada de inferir RI por notificações já
# registradas na ficha: a união antiga fazia um RI de fiscalização antiga
# (registrado na ficha um dia, por engano ou importação) virar "conhecido"
# e puxar as irmãs dele para sempre.
#
# OS que acompanha DUAS fiscalizações do mesmo empregador (ex.: ação fiscal
# normal + investigação de acidente): declare os dois RIs no próprio campo,
# separados por vírgula — `ri: "320038432, 320199999"`. Explícito, decidido
# pelo AFT, nunca inferido.
#
# `ri:` vazio: adota o RI da notificação mais recente (ri_mais_recente) e o
# grava no front-matter — a partir daí a regra estrita vale.
#
# Notificação de RI alheio nunca é importada — mas também nunca é descartada
# em silêncio: volta no relatório (`ignoradas_detalhe`) para o AFT decidir.

def ris_da_os(ri_fm: str) -> set[str]:
    """RIs desta OS = somente o(s) do campo `ri:` do front-matter (9 dígitos
    cada; aceita mais de um, separados por vírgula/espaço)."""
    return set(re.findall(r"\d{9}", ri_fm or ""))


def ri_mais_recente(notifs: list[dict]) -> str:
    """RI da notificação mais recente (por data de lavratura) — usado só quando
    a OS ainda não conhece nenhum RI. Uma OS ativa é a fiscalização em curso,
    então a notificação mais nova é a que a identifica."""
    melhor, quando = "", ""
    for n in notifs:
        ri = re.sub(r"\D", "", n.get("ri") or "")
        env = n.get("dataEnvio") or ""
        if re.fullmatch(r"\d{9}", ri) and env > quando:
            melhor, quando = ri, env
    return melhor


# ── Edição do memory.md (funções puras, testáveis sem rede) ─────────────────

def _data_br(iso: str | None) -> str:
    """'2026-07-31[T...]' → '31/07/2026'; '' se vazio/ilegível."""
    if not iso:
        return ""
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", iso)
    return f"{m.group(3)}/{m.group(2)}/{m.group(1)}" if m else ""


def _data_presente(linha: str, iso: str) -> bool:
    """A data (BR ou ISO) já aparece em algum lugar da linha, em qualquer
    frase? Evita colar '— prazo X' redundante quando a data já está escrita
    de outra forma (ex.: '...vistoria de 30/07/2026')."""
    return _data_br(iso) in linha or iso[:10] in linha


def _mesma_data(txt: str, iso: str | None) -> bool:
    """Compara a data da linha (qualquer formato) com a ISO do DET."""
    if not iso:
        return not txt
    m = re.match(r"(\d{2})/(\d{2})/(\d{4})", txt)
    if m:
        norm = f"{m.group(3)}-{m.group(2)}-{m.group(1)}"
    else:
        norm = txt[:10]
    return norm == iso[:10]


def _linha_detalhe(n: dict, msg: str = "", itens_resumo: str = "") -> str:
    """Sub-linha de detalhes de uma notificação (dados vindos do DET).
    Campos vazios são omitidos; status 1 = Confirmada (único elegível).

    `itemAtualizado` é o campo da API por trás do triângulo amarelo do DET
    ("Existe atualização pendente"). O alerta ESPELHA o DET: aparece enquanto
    a API disser true e some quando ela disser false — nada mais.

    Até 25/08/2026 ele era "dispensável": um clique no painel gravava
    `<!-- visto: X -->` na sub-linha e o alerta sumia localmente até haver
    entrega nova. Isso nasceu de um susto de julho/2026 (casos SPE CAMETA e
    CONSORCIO SQ), quando o campo parecia ficar preso em true. O AFT vetou a
    dispensa em 25/08/2026, com razão: ele havia clicado SEM QUERER e perdeu
    de vista uma pendência que continuava viva no DET (BUENO 28, cinco itens
    com pedido de prazo). Um alerta que some por engano é pior que um alerta
    teimoso — e a saída legítima existe: o triângulo apaga de verdade quando
    o AFT abre a notificação no DET, o que o /aft-det-baixar já faz ao
    registrar a visualização (confirmado em produção em 21/08/2026)."""
    partes = []
    if n.get("dataEnvio"):
        partes.append(f"lavrada {_data_br(n['dataEnvio'])}")
    if n.get("dataCiencia"):
        partes.append(f"ciência {_data_br(n['dataCiencia'])}")
    if n.get("itemDataUltimaEntrega"):
        partes.append(f"última entrega {_data_br(n['itemDataUltimaEntrega'])}")
    if n.get("status") == STATUS_CANCELADA:
        partes.append("CANCELADA no DET")
    elif n.get("status") == STATUS_CONFIRMADA:
        partes.append("Confirmada")
    elif not n.get("dataCiencia"):
        partes.append(f"aguardando ciência (status {n.get('status')})")
    else:
        partes.append(f"status {n.get('status')}")
    if _flag(n.get("itemAtualizado")):
        partes.append("⚠️ atualização pendente")
    # Resumo do status dos itens: buscado para toda notificação em aberto (ver
    # codigos_abertos). Fica na sub-linha com o marcador 📋; o gerar_painel o
    # lê, mostra no dossiê e conta os "aguardando avaliação" num selo do card,
    # que ACUMULA com o ⚠️ — o triângulo diz que há novidade, o 📋 diz o quê.
    if itens_resumo:
        partes.append(f"📋 {itens_resumo}")
    # Envelope laranja da tela do DET: o componente app-pendencia-comunicacao
    # do site só aparece quando `isPendenciaComunicacaoAuditor` é verdadeiro
    # (lido do código do front em 19/08/2026) — é a coluna ao lado do triângulo
    # amarelo. Significa mensagem no canal de comunicação da notificação
    # esperando resposta do AFT. Diferente do triângulo, some sozinho quando o
    # AFT responde no DET: por isso não é dispensável por clique.
    if _flag(n.get("isPendenciaComunicacaoAuditor")):
        # O trecho da última mensagem do empregador (quando o sync conseguiu
        # buscá-lo) vai na própria sub-linha — o painel o mostra no cartão.
        partes.append("✉️ mensagem no canal de comunicação"
                      + (f': "{msg}"' if msg else ""))
    return "  - " + " · ".join(partes) + "\n"


def aplicar_notificacoes(texto: str, notifs: list[dict],
                         msgs: dict[str, str] | None = None,
                         resumos: dict[str, str] | None = None
                         ) -> tuple[str, int, int, int, list[str]]:
    """Aplica as notificações elegíveis na seção ## Notificações DET.
    Devolve (novo_texto, inseridas, prazos_atualizados, detalhes_atualizados,
    canceladas). Função pura.

    Notificação CANCELADA pelo auditor no DET não tem efeito legal: nunca é
    inserida na ficha (regra pedida em 19/08/2026, caso MENINA TEIMOSA). A que
    já estava registrada — porque foi cancelada DEPOIS de importada — não é
    apagada em silêncio: a sub-linha passa a dizer "CANCELADA no DET", o painel
    a mostra riscada e ela deixa de contar prazo. Quem apaga a linha é o AFT."""
    linhas = texto.splitlines(keepends=True)

    ini = fim = -1
    for i, l in enumerate(linhas):
        if l.strip().startswith("## ") and l.strip()[3:].strip() in (
                "Notificações DET", "Notificacoes DET"):
            ini = i + 1
            break
    if ini < 0:
        # memory.md sem a seção: cria antes da primeira '## ' (ou no fim).
        pos = next((i for i, l in enumerate(linhas)
                    if l.strip().startswith("## ")), len(linhas))
        linhas[pos:pos] = ["## Notificações DET\n", "\n"]
        ini = pos + 1
    fim = next((i for i in range(ini, len(linhas))
                if linhas[i].strip().startswith("## ")), len(linhas))

    # Índice: código → nº da linha (só linhas checkbox da seção).
    por_codigo: dict[str, int] = {}
    for i in range(ini, fim):
        cb = RE_CHECKBOX.match(linhas[i])
        if not cb:
            continue
        cod = RE_CODIGO.match(cb.group(1).strip())
        if cod:
            por_codigo[cod.group(1)] = i

    inseridas = atualizadas = detalhes = 0
    canceladas: list[str] = []
    novas: list[str] = []
    inserir_detalhe: list[tuple[int, str]] = []  # (posição, linha) — aplicados no fim
    msgs = msgs or {}
    resumos = resumos or {}
    for n in notifs:
        codigo = (n.get("codigo") or "").strip()
        if not codigo:
            continue
        cancelada = n.get("status") == STATUS_CANCELADA
        if cancelada:
            canceladas.append(codigo)
        prazo_iso = n.get("itemDataProximaEntrega")
        i = por_codigo.get(codigo)
        if i is None:
            if cancelada:
                continue  # nunca entra na ficha; volta no relatório
            prazo = _data_br(prazo_iso)
            novas.append(f"- [ ] {codigo}" + (f" — prazo {prazo}\n" if prazo else "\n"))
            novas.append(_linha_detalhe(n, msgs.get(codigo, ""),
                                        resumos.get(codigo, "")))
            inseridas += 1
            continue
        # Já registrada: mantém a sub-linha de detalhes (cria/regrava se mudou).
        # A linha é remontada do zero, então o marcador `<!-- visto: -->` da
        # antiga dispensa por clique (removida em 25/08/2026) sai sozinho.
        det = _linha_detalhe(n, msgs.get(codigo, ""), resumos.get(codigo, ""))
        if i + 1 < fim and RE_DETALHE.match(linhas[i + 1]):
            if linhas[i + 1] != det:
                linhas[i + 1] = det
                detalhes += 1
        else:
            inserir_detalhe.append((i + 1, det))
            detalhes += 1
        # Atualiza o prazo se mudou (preserva o formato da linha). Cancelada
        # não tem prazo a perseguir: a sub-linha já a marcou, o resto fica.
        if cancelada or not prazo_iso:
            continue
        ms = list(RE_PRAZO_LINHA.finditer(linhas[i]))
        if len(ms) == 1:
            m = ms[0]
            if not _mesma_data(m.group(2), prazo_iso):
                # Preserva o formato que a linha já usava (ISO ou dd/mm/aaaa).
                nova_data = prazo_iso[:10] if "-" in m.group(2) else _data_br(prazo_iso)
                linhas[i] = linhas[i][:m.start(2)] + nova_data + linhas[i][m.end(2):]
                atualizadas += 1
        elif not ms and not _data_presente(linhas[i], prazo_iso):
            # Linha sem NENHUM prazo escrito (nem em outra forma) e o DET agora
            # tem um: acrescenta no fim.
            corpo = linhas[i].rstrip("\n")
            linhas[i] = f"{corpo} — prazo {_data_br(prazo_iso)}\n"
            atualizadas += 1
        # 2+ "prazo"/"entrega até" na mesma linha: ambíguo (a API só informa UM
        # próximo prazo por notificação, não por item) — nunca escolhe sozinho
        # qual trocar. A linha fica intocada; o AFT decide manualmente.

    # Sub-linhas de detalhe novas: inseridas de trás para frente, para não
    # deslocar os índices ainda pendentes.
    for pos, det in sorted(inserir_detalhe, reverse=True):
        linhas.insert(pos, det)
        fim += 1

    if novas:
        # Insere após a última linha checkbox — pulando a sub-linha de
        # detalhes dela — ou no início da seção; remove um "_(vazio)_" que
        # esteja sozinho na seção.
        ult = max((i for i in range(ini, fim) if RE_CHECKBOX.match(linhas[i])),
                  default=None)
        if ult is None:
            for i in range(ini, fim):
                if linhas[i].strip() in ("_(vazio)_", "(vazio)"):
                    del linhas[i]
                    fim -= 1
                    break
            pos = ini
            while pos < fim and not linhas[pos].strip():
                pos += 1
            linhas[pos:pos] = novas
        else:
            pos = ult + 1
            if pos < fim and RE_DETALHE.match(linhas[pos]):
                pos += 1
            linhas[pos:pos] = novas

    return "".join(linhas), inseridas, atualizadas, detalhes, canceladas


def preencher_ri(texto: str, ri: str) -> tuple[str, bool]:
    """Preenche `ri:` no front-matter se estiver vazio. Nunca sobrescreve um RI
    já preenchido. O RI vem decidido de fora (ris_conhecidos/ri_mais_recente) —
    esta função não escolhe RI sozinha."""
    if not re.fullmatch(r"\d{9}", ri or ""):
        return texto, False
    m = RE_FM.match(texto)
    if not m:
        return texto, False
    fm = m.group(1)
    atual = re.search(r"^ri\s*:\s*(.*)$", fm, re.MULTILINE)
    valor = (atual.group(1).strip().strip('"').strip("'") if atual else "")
    if valor not in ("", "null", "~"):
        return texto, False
    if atual:
        fm_novo = fm[:atual.start()] + f'ri: "{ri}"' + fm[atual.end():]
    else:
        fm_novo = fm + f'\nri: "{ri}"'
    return texto[:m.start(1)] + fm_novo + texto[m.end(1):], True


def registrar_atividade(texto: str, detalhe: str) -> str:
    """Linha no Registro de atividades (best-effort: sem a seção, não mexe)."""
    linhas = texto.splitlines(keepends=True)
    ini = next((i + 1 for i, l in enumerate(linhas)
                if l.strip() == "## Registro de atividades"), -1)
    if ini < 0:
        return texto
    fim = next((i for i in range(ini, len(linhas))
                if linhas[i].strip().startswith("## ")), len(linhas))
    ult = max((i for i in range(ini, fim) if linhas[i].strip().startswith("|")),
              default=None)
    if ult is None:
        return texto
    hoje = datetime.date.today().strftime("%d/%m/%Y")
    linhas.insert(ult + 1, f"| {hoje} | Sync DET (extensão) | {detalhe} |\n")
    return "".join(linhas)


# ── Orquestração ─────────────────────────────────────────────────────────────

def identificadores(texto: str, pasta: str) -> tuple[str, str]:
    """(cnpj_ou_cpf, ri) da OS — front-matter, corpo ou nome da pasta."""
    m = RE_FM.match(texto)
    fm = m.group(1) if m else ""

    def campo(chave: str) -> str:
        c = re.search(rf"^{chave}\s*:\s*(.+?)\s*$", fm, re.MULTILINE)
        if not c:
            return ""
        v = c.group(1).strip().strip('"').strip("'")
        return "" if v in ("null", "~") else v

    # Empregador pessoa física (rural, doméstico) é identificado por CPF/CAEPF:
    # aceita as três chaves, o valor é sempre só dígitos.
    cnpj = re.sub(r"\D", "", campo("cnpj") or campo("cpf") or campo("caepf"))
    if not cnpj:
        m2 = re.search(r"(\d{11,14})\s*$", pasta)
        cnpj = m2.group(1) if m2 else ""
    # `ri:` cru (pode ter mais de um RI, separados por vírgula) — quem extrai
    # os RIs individuais é ris_da_os().
    return cnpj, campo("ri")


def sincronizar_os(pasta_os: Path, token: str,
                   consultar=consultar_det, canal=snippet_canal,
                   resumo=resumo_itens) -> dict:
    """Sincroniza uma OS. `consultar`, `canal` e `resumo` são injetáveis
    para testes."""
    r = {"os": pasta_os.name, "recebidas": 0, "inseridas": 0,
         "prazos_atualizados": 0, "detalhes_atualizados": 0,
         "ri_preenchido": False, "ignoradas": [], "canceladas": [],
         "erro": None}
    mem = pasta_os / "memory.md"
    try:
        texto = mem.read_text(encoding="utf-8")
    except OSError as e:
        r["erro"] = f"memory.md ilegível: {e}"
        return r
    cnpj, ri_fm = identificadores(texto, pasta_os.name)
    conhecidos = ris_da_os(ri_fm)
    if not cnpj and not conhecidos:
        r["erro"] = "sem CNPJ/CPF nem RI — pulada"
        return r
    try:
        notifs = elegiveis(consultar(token, cnpj,
                                     sorted(conhecidos)[0] if conhecidos else ""))
    except RuntimeError as e:
        r["erro"] = str(e)
        return r
    r["recebidas"] = len(notifs)
    if not notifs:
        return r

    # Só entram notificações da(s) fiscalização(ões) DESTA OS — o `ri:` do
    # front-matter é o identificador canônico (ver bloco "Vínculo notificação × OS").
    ri_novo = ""
    if not conhecidos:
        # OS ainda sem `ri:`: adota o da notificação mais recente e grava.
        ri_novo = ri_mais_recente(notifs)
        if ri_novo:
            conhecidos = {ri_novo}
    if not conhecidos:
        r["erro"] = ("não foi possível determinar o RI desta OS — nada importado. "
                     "Preencha `ri:` no memory.md e sincronize de novo.")
        return r

    minhas, alheias = [], []
    for n in notifs:
        (minhas if re.sub(r"\D", "", n.get("ri") or "") in conhecidos
         else alheias).append(n)
    # Nunca descartadas em silêncio: voltam no relatório para o AFT decidir.
    r["ignoradas"] = [{"codigo": n.get("codigo"),
                       "ri": re.sub(r"\D", "", n.get("ri") or ""),
                       "situacao": n.get("situacaoRi"),
                       "lavrada": (n.get("dataEnvio") or "")[:10]}
                      for n in alheias]
    if not minhas:
        return r

    # Envelope aceso: busca o trecho da última mensagem do empregador para a
    # sub-linha (uma requisição extra só nas notificações com pendência).
    msgs = {}
    for n in minhas:
        if _flag(n.get("isPendenciaComunicacaoAuditor")) and n.get("uid"):
            trecho = canal(token, n["uid"])
            if trecho:
                msgs[(n.get("codigo") or "").strip()] = trecho

    # Status dos itens para a sub-linha: uma requisição extra por notificação
    # ainda EM ABERTO na ficha (checkbox `- [ ]`), não por triângulo aceso.
    # O triângulo é péssimo gate: some quando o AFT o dispensa no painel ou
    # abre a notificação no DET, e o resumo sumia junto — informação de ESTADO
    # (o que cada item aguarda) desaparecendo por causa de um alerta de
    # NOVIDADE. Constatado com o AFT em 25/08/2026, caso BUENO 28. Notificação
    # já marcada como respondida não é consultada: o custo fica no que importa.
    # ...OU com o triângulo aceso, mesmo já marcada como respondida: o AFT
    # pode ter dado a notificação por tratada e o DET continuar acusando
    # novidade (caso real BUENO 28, 25/08/2026 — checkbox [x], ⚠️ aceso e
    # cinco itens ainda esperando a decisão dele). Sem esta segunda porta, o
    # card mostrava o ⚠️ sozinho, sem dizer o quê — o defeito que o AFT
    # mandou corrigir. Os dois selos têm de andar juntos.
    abertos = codigos_abertos(texto)
    resumos = {}
    for n in minhas:
        cod = (n.get("codigo") or "").strip()
        if (cod in abertos or _flag(n.get("itemAtualizado"))) and n.get("uid"):
            res = resumo(token, n["uid"])
            if res:
                resumos[cod] = res

    (novo, r["inseridas"], r["prazos_atualizados"],
     r["detalhes_atualizados"], r["canceladas"]) = aplicar_notificacoes(
        texto, minhas, msgs, resumos)
    novo, r["ri_preenchido"] = preencher_ri(novo, ri_novo)
    if novo == texto:
        return r

    partes = []
    if r["inseridas"]:
        partes.append(f"{r['inseridas']} notificação(ões) importada(s)")
    if r["prazos_atualizados"]:
        partes.append(f"{r['prazos_atualizados']} prazo(s) atualizado(s)")
    if r["detalhes_atualizados"]:
        partes.append(f"{r['detalhes_atualizados']} detalhe(s) atualizado(s)")
    if r["ri_preenchido"]:
        partes.append(f"RI {ri_novo} preenchido (notificação mais recente)")
    if r["canceladas"]:
        partes.append(f"{len(r['canceladas'])} cancelada(s) no DET")
    novo = registrar_atividade(novo, " · ".join(partes) or "sem mudanças")

    import os
    if os.environ.get("AFT_DET_DRYRUN"):
        r["dry_run"] = True  # nada é gravado (modo de inspeção)
        return r

    if BACKUP.exists():
        subprocess.run([sys.executable, str(BACKUP), str(mem)],
                       capture_output=True, timeout=30)
    mem.write_text(novo, encoding="utf-8")
    return r


# Quantas OS são consultadas ao mesmo tempo. O gargalo do sync é a espera pelo
# servidor do DET (~6 s por OS), não a nossa CPU: em fila, 16 OS levavam ~105 s.
# 5 de cada vez derruba isso para ~25 s sem martelar o DET (o site do governo faz
# várias requisições simultâneas ao abrir uma tela; 5 é conservador). Cada OS
# escreve no seu próprio memory.md, então não há concorrência de escrita.
SYNC_PARALELO = 5


def sincronizar_todas(base: Path, token: str, consultar=consultar_det,
                      canal=snippet_canal, resumo=resumo_itens) -> dict:
    """Sincroniza todas as OS de OS ATIVAS/. Uma OS com erro não derruba as
    demais. Devolve métricas agregadas (mesmo espírito do SisOS).

    As OS são consultadas em PARALELO (SYNC_PARALELO por vez); a ordem do
    relatório é preservada (executor.map devolve na ordem de entrada)."""
    from concurrent.futures import ThreadPoolExecutor
    pastas = [mem.parent for mem in sorted(base.glob("*/memory.md"))]
    if not pastas:
        resultados = []
    elif len(pastas) == 1:
        resultados = [sincronizar_os(pastas[0], token, consultar, canal, resumo)]
    else:
        with ThreadPoolExecutor(max_workers=min(SYNC_PARALELO, len(pastas))) as ex:
            resultados = list(ex.map(
                lambda p: sincronizar_os(p, token, consultar, canal, resumo),
                pastas))
    erros = [{"os": r["os"], "erro": r["erro"]} for r in resultados if r["erro"]]
    ignoradas = [{"os": r["os"], **ig} for r in resultados for ig in r["ignoradas"]]
    canceladas = [{"os": r["os"], "codigo": c}
                  for r in resultados for c in r["canceladas"]]
    return {
        "ok": True,
        "os_verificadas": len(resultados),
        "notificacoes_recebidas": sum(r["recebidas"] for r in resultados),
        "inseridas": sum(r["inseridas"] for r in resultados),
        "prazos_atualizados": sum(r["prazos_atualizados"] for r in resultados),
        "detalhes_atualizados": sum(r["detalhes_atualizados"] for r in resultados),
        "ris_preenchidos": sum(1 for r in resultados if r["ri_preenchido"]),
        # De outra fiscalização do mesmo empregador — não importadas, relatadas.
        "ignoradas": len(ignoradas),
        "ignoradas_detalhe": ignoradas or None,
        # Canceladas pelo auditor no DET: não entram na ficha, mas o AFT fica
        # sabendo que existem (pode ser um cancelamento que ele não esperava).
        "canceladas": len(canceladas),
        "canceladas_detalhe": canceladas or None,
        "erros": erros or None,
    }


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("uso: python det_sync.py <PASTA_OS_ATIVAS> <token>", file=sys.stderr)
        sys.exit(1)
    print(json.dumps(sincronizar_todas(Path(sys.argv[1]), sys.argv[2]),
                     ensure_ascii=False, indent=2))
