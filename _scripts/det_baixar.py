#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
det_baixar.py — baixa os arquivos de uma notificação do DET para a pasta da OS.

Irmão do det_sync.py e mesma via de acesso: a API oficial do DET (a MESMA que o
site usa), com o token de sessão que a extensão Chrome "Sync DET" empresta ao
servir_painel.py. Nenhum navegador envolvido: são 4 ou 5 requisições HTTP e o
download termina em segundos — substitui o fluxo antigo de dirigir o Chrome
clique a clique (10 minutos por notificação).

O que é baixado, e para onde (pasta da OS em OS ATIVAS/) — toda notificação
mora em NOTIFICACOES/, no pacote "<NN> - <CODIGO> <dd-mm-aaaa>" (convenção
pedida pelo AFT em 24/08/2026): NN é a ORDEM DE LAVRATURA entre as
notificações da OS (01 é a primeira emitida) e a data é a de LAVRATURA
(dataEnvio da API do DET) — não a do download. O que chega em cada download
vai para a subpasta do dia, "baixada em <dd-mm-aaaa>", para o AFT saber o que
a empresa apresentou em cada data (entrega parcelada tem prazos diversos):

    NOTIFICACOES/<NN> - <CODIGO> <dd-mm-aaaa>/
        notificacao-<CODIGO>.pdf              o PDF da notificação (estático)
        canal-comunicacao/                    mensagens e anexos (cumulativo)
        baixada em <dd-mm-aaaa>/              uma por dia de download completo
            relatorio-atendimento-<CODIGO>.pdf  fotografia do dia (TODOS os
                                              itens, com hash de cada arquivo)
            historico-itens.md                linha do tempo dos itens no dia
            item<N>_<descrição do item>/      só o que chegou NAQUELE dia
                <arquivo entregue>
                invalidados/<arquivo>         o que o AFT rejeitou/dispensou

Legados são migrados sozinhos na próxima execução: pacote "notificacao-<COD>"
ou "<COD> <data>" (na raiz da OS ou em NOTIFICACOES/) é renomeado para o
padrão — preservando sufixo descritivo que o AFT tenha dado —, PDF solto na
raiz ou em NOTIFICACOES/ é movido para dentro do pacote, e conteúdo que
morava na raiz do pacote desce para a subpasta "baixada em <data>" do dia em
que foi baixado (data de modificação do arquivo). Tudo conta em `movidos`.
O modo --reorganizar aplica essa migração sem rede (usado pela
/aft-organiza-os).

Em vez do ZIP geral do site (que exige segundo request numa URL volátil e
chega sem estrutura), cada arquivo é baixado individualmente pelo endpoint de
arquivos do item — assim a pasta nasce organizada por item, com a descrição
oficial vinda da API (nada de raspar o PDF para adivinhar nomes).

Endpoints (lidos do bundle público do front do DET em 21/08/2026 — chunk 251;
ver a nota sync-det-e-extensao.md para o método de conferência no bundle):

    POST /services/auditor/v1/notificacoes/pesquisa          (codigoNotificacao)
    GET  /services/auditor/v1/notificacoes/{uid}/pdf?numeroDeLinhas=0
    GET  /services/auditor/v1/notificacoes/{uid}/pdf-relatorio-atendimento?tipo=2
    GET  /services/auditor/v1/itens-notificacao?uidNotificacao={uid}
    GET  /services/auditor/v1/arquivos-item?uidItem={uid}
    GET  /services/auditor/v1/arquivos-item/{uid}/blob

Status do arquivo (enum do front): 0 INICIAL e 1 RECEBIDO são entrega válida;
2 REJEITADO e 3 DISPENSADO vão para a subpasta invalidados/ — o AFT os
invalidou no DET, mas continuam sendo evidência.

Idempotente: arquivo que já existe (tamanho > 0) não é baixado de novo.
O token é usado em memória e nunca gravado (regra da extensão). Cada download
registra uma linha no Registro de atividades do memory.md (com backup prévio).

Uso normal: via servir_painel.py (POST /api/det-baixar — botão do painel e a
skill /aft-det-baixar). A skill chama o modo --via-painel, que faz o POST no
servidor local (o token fica lá, abastecido pelo Sincronizar da extensão):
    python det_baixar.py --via-painel "<pasta ou nome da pasta da OS>" <CODIGO>
Direto, com token em mãos (debug):
    python det_baixar.py "<pasta da OS>" "<CODIGO>" "<token>"
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
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

AQUI = Path(__file__).resolve().parent
BACKUP = AQUI / "backup_arquivo.py"

DET_BASE = "https://auditor-det.sit.trabalho.gov.br/services/auditor/v1"
TIMEOUT_JSON = 15   # segundos — respostas pequenas (pesquisa, listas)
TIMEOUT_BLOB = 120  # segundos — arquivos (o DET aceita até 20 MB por arquivo)

# Arquivo entregue: 0 INICIAL · 1 RECEBIDO · 2 REJEITADO · 3 DISPENSADO
STATUS_INVALIDADOS = (2, 3)

# Status do ITEM nos eventos do histórico (enum do front do DET, chunk 251,
# lido em 21/08/2026) — é o que aparece na coluna Status da tela do item.
STATUS_ITEM = {
    0: "Inicial", 1: "Item enviado", 2: "Item recebido", 3: "Item rejeitado",
    4: "Aguardando avaliação de prazo", 5: "Prazo aceito", 6: "Prazo rejeitado",
    7: "Prazo prorrogado", 8: "Não enviado",
    9: "Aguardando avaliação de dispensa", 10: "Item dispensado",
    11: "Dispensa rejeitada", 12: "Dispensa parcial",
    13: "Providência solicitada", 14: "Entrega digital dispensada",
    15: "Item enviado (pendente avaliação de prazo)",
    16: "Não enviado (pendente avaliação de prazo)",
    17: "Item recebido (pendente avaliação de prazo)",
    18: "Item enviado (pendente avaliação de dispensa)",
    19: "Não enviado (pendente avaliação de dispensa)",
    20: "Item recebido (pendente avaliação de dispensa)",
}


def _data_nome(iso: str | None) -> str | None:
    """'2026-08-20T...' → '20-08-2026' (formato das datas em nome de pasta);
    None se vazio/estranho."""
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", str(iso or ""))
    return f"{m.group(3)}-{m.group(2)}-{m.group(1)}" if m else None


def _data_hora_br(iso: str | None) -> str:
    """'2026-08-19T10:11:22...' → '19/08/2026 10:11'; '' se vazio."""
    if not iso:
        return ""
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})[T ](\d{2}):(\d{2})", str(iso))
    if m:
        return f"{m.group(3)}/{m.group(2)}/{m.group(1)} {m.group(4)}:{m.group(5)}"
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", str(iso))
    return f"{m.group(3)}/{m.group(2)}/{m.group(1)}" if m else str(iso)


def _texto_plano(t: str | None, limite: int = 0) -> str:
    """Texto de API para arquivo/linha: colapsa quebras e espaços; corta na
    última palavra inteira quando `limite` > 0."""
    t = re.sub(r"\s+", " ", t or "").strip()
    if limite and len(t) > limite:
        t = t[:limite]
        if " " in t:
            t = t.rsplit(" ", 1)[0]
        t += "…"
    return t


def _registros_canal(canal) -> list[dict]:
    """A lista de registros do canal, onde quer que a API a tenha posto
    (a resposta é um objeto; o nome exato da lista não está no contrato)."""
    if isinstance(canal, list):
        return [x for x in canal if isinstance(x, dict)]
    if isinstance(canal, dict):
        for chave in ("registros", "mensagens", "comunicacoes", "eventos"):
            v = canal.get(chave)
            if isinstance(v, list):
                return [x for x in v if isinstance(x, dict)]
        for v in canal.values():
            if isinstance(v, list) and v and isinstance(v[0], dict):
                return v
    return []


class TokenExpirado(RuntimeError):
    """401/403 do DET: o token de sessão venceu (dura ~30 min)."""


# ── HTTP (urllib puro, como no det_sync) ─────────────────────────────────────

def _requisicao(token: str, caminho: str, *, params: dict | None = None,
                corpo: dict | None = None, timeout: int = TIMEOUT_JSON,
                metodo: str | None = None) -> bytes:
    url = DET_BASE + caminho
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(
        url,
        data=json.dumps(corpo).encode("utf-8") if corpo is not None else None,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json, text/plain, */*",
        },
        # metodo explícito vence (POST casca, PUT rascunho); senão infere.
        method=metodo or ("POST" if corpo is not None else "GET"),
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read()
    except urllib.error.HTTPError as e:
        if e.code in (401, 403):
            raise TokenExpirado(
                "token do DET expirado — clique em Sincronizar na aba do DET "
                "e tente de novo") from e
        detalhe = e.read().decode("utf-8", errors="replace")[:200]
        raise RuntimeError(f"DET API {e.code} em {caminho}: {detalhe}") from e
    except Exception as e:
        raise RuntimeError(f"DET inacessível ({caminho}): {e}") from e


def _json_api(token: str, caminho: str, **kw):
    return json.loads(_requisicao(token, caminho, **kw).decode("utf-8"))


def pesquisar_por_codigo(token: str, codigo: str) -> dict | None:
    """A notificação com esse código, ou None. Mesmo corpo de pesquisa do
    det_sync, mas pelo código (chave única — inclui as da equipe)."""
    corpo = {
        "isPesquisaPadrao": False,
        "niEmpregador": None,
        "ri": None,
        "codigoNotificacao": codigo,
        "cifAuditor": None,
        "isSomenteMinhas": False,
        "sequencia": 0,
        "ordenacaoCampo": "id",
        "ordenacaoDesc": False,
        "isPendenciaComunicacaoAuditor": False,
        "isPendenciaComunicacaoEmpregador": False,
        "situacaoFisc": None,
    }
    dados = _json_api(token, "/notificacoes/pesquisa", corpo=corpo)
    for n in dados.get("notificacoes") or []:
        if (n.get("codigo") or "").strip() == codigo:
            return n
    return None


# ── Nomes seguros de pasta/arquivo (funções puras, testáveis sem rede) ───────

_RE_PROIBIDOS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def _limpo(nome: str) -> str:
    """Nome utilizável em pasta/arquivo no macOS E no Windows: troca os
    caracteres proibidos por espaço e apara pontas (ponto final é inválido
    no Windows). Acentos ficam."""
    nome = _RE_PROIBIDOS.sub(" ", nome or "")
    return re.sub(r"\s+", " ", nome).strip().strip(".").strip()


def pasta_do_item(ordem, descricao: str) -> str:
    """`item<N>_<descrição>` — descrição oficial da API, cortada em 40
    caracteres na última palavra inteira (mesma convenção do fluxo antigo)."""
    desc = _limpo(descricao)
    if len(desc) > 40:
        desc = desc[:40]
        if " " in desc:
            desc = desc.rsplit(" ", 1)[0]
    base = f"item{ordem}"
    return f"{base}_{desc}" if desc else base


def nome_do_arquivo(nome: str, usados: set[str]) -> str:
    """Nome do arquivo como veio do DET, saneado; colisão no mesmo item
    ganha sufixo -2, -3..."""
    limpo = _limpo(nome) or "arquivo"
    candidato, n = limpo, 1
    while candidato.lower() in usados:
        n += 1
        raiz, ponto, ext = limpo.rpartition(".")
        candidato = f"{raiz}-{n}.{ext}" if ponto else f"{limpo}-{n}"
    usados.add(candidato.lower())
    return candidato


RE_SO_DATA = re.compile(r"\d{2}-\d{2}-\d{4}")
RE_NUMERO = re.compile(r"^\d{2} - ")
# Um pacote de notificação em NOTIFICACOES/: "[NN - ]<CODIGO> <data>[ sufixo]"
RE_PACOTE = re.compile(
    r"^(?:(\d{2}) - )?([A-Z0-9]{6,}) (\d{2})-(\d{2})-(\d{4})(?: .*)?$")


def _data_mtime(p: Path) -> str:
    return datetime.date.fromtimestamp(p.stat().st_mtime).strftime("%d-%m-%Y")


def pasta_do_pacote(pasta_os: Path, codigo: str, hoje: str | None = None,
                    lavratura: str | None = None) -> Path:
    """A pasta-pacote da notificação: NOTIFICACOES/<NN> - <CODIGO> <dd-mm-aaaa>.

    Reusa pacote existente que contenha o código no nome — em NOTIFICACOES/ ou
    na raiz da OS, com ou sem numeração, com ou sem o prefixo legado
    "notificacao-" — e o RENOMEIA para o padrão, preservando sufixo descritivo
    que o AFT tenha dado ("<COD> <data> jornada"). A data no nome é a de
    LAVRATURA (`lavratura`, dd-mm-aaaa, vinda da API); sem ela, mantém a data
    que já estiver no nome ou, em último caso, usa a da última modificação da
    pasta. Sem pacote nenhum: NOTIFICACOES/<CODIGO> <lavratura ou hoje>
    (criada na primeira gravação). O prefixo "NN - " não é decidido aqui: é a
    renumerar_pacotes() que o dá, pela ordem das datas de lavratura."""
    hoje = hoje or datetime.date.today().strftime("%d-%m-%Y")
    notifs = pasta_os / "NOTIFICACOES"
    cands: list[Path] = []
    for base in (notifs, pasta_os):
        if base.is_dir():
            cands += sorted(p for p in base.iterdir()
                            if p.is_dir() and codigo in p.name.upper())
    if not cands:
        return notifs / f"{codigo} {lavratura or hoje}"
    alvo = cands[0]
    resto = RE_NUMERO.sub("", alvo.name)
    if resto.upper().startswith("NOTIFICACAO-"):
        resto = resto[len("NOTIFICACAO-"):]
    i = resto.upper().find(codigo)
    if i >= 0:
        resto = resto[:i] + resto[i + len(codigo):]
    m = RE_SO_DATA.search(resto)
    data_no_nome = m.group(0) if m else ""
    sufixo = (resto[:m.start()] + resto[m.end():]) if m else resto
    sufixo = re.sub(r"\s+", " ", sufixo).strip(" -_.")
    data = lavratura or data_no_nome or _data_mtime(alvo)
    novo = notifs / (f"{codigo} {data}" + (f" {sufixo}" if sufixo else ""))
    if novo.name == RE_NUMERO.sub("", alvo.name) and alvo.parent == notifs:
        return alvo  # já no padrão (a menos do número, que é da renumeração)
    if novo.exists():
        return novo  # padrão já existe; nunca mescla pastas sozinho
    notifs.mkdir(parents=True, exist_ok=True)
    alvo.rename(novo)
    return novo


def renumerar_pacotes(notifs: Path, seguir: Path | None = None) -> Path | None:
    """Prefixa cada pacote com "NN - " pela ordem de lavratura — a data no
    nome da pasta (pedido do AFT em 24/08/2026: ao abrir NOTIFICACOES/, a
    primeira notificação da fiscalização é a 01). Notificação antiga baixada
    depois entra no lugar certo e as outras são renumeradas. Pasta que não
    tem cara de pacote (sem "<CODIGO> <data>" no nome) fica intocada.
    Devolve o caminho atualizado de `seguir` (que pode ter sido renomeado)."""
    if not notifs.is_dir():
        return seguir
    pacotes = []
    for p in sorted(notifs.iterdir()):
        m = RE_PACOTE.fullmatch(p.name) if p.is_dir() else None
        if m:
            num, codigo, d, mes, ano = m.groups()
            pacotes.append(((ano, mes, d), int(num) if num else 99, codigo, p))
    pacotes.sort(key=lambda t: t[:3])
    for n, (_, _, _, p) in enumerate(pacotes, start=1):
        novo = notifs / f"{n:02d} - {RE_NUMERO.sub('', p.name)}"
        if novo == p or novo.exists():
            continue
        p.rename(novo)
        if seguir == p:
            seguir = novo
    return seguir


def migrar_pacote_para_dias(raiz: Path) -> int:
    """Layout antigo (relatório, historico-itens.md e pastas item<N> na RAIZ
    do pacote) → subpastas "baixada em <dd-mm-aaaa>": cada arquivo desce para
    a pasta do dia em que foi baixado (data de modificação — no layout antigo
    é a data do download). Devolve quantos arquivos moveu. Idempotente: com o
    layout novo não há nada na raiz para mover."""
    if not raiz.is_dir():
        return 0
    movidos = 0

    def _desce(arq: Path, rel: Path) -> None:
        nonlocal movidos
        destino = raiz / f"baixada em {_data_mtime(arq)}" / rel
        if destino.exists():
            return
        destino.parent.mkdir(parents=True, exist_ok=True)
        arq.rename(destino)
        movidos += 1

    for arq in sorted(raiz.iterdir()):
        nome = arq.name
        if arq.is_file() and (nome.startswith("relatorio-atendimento-")
                              or nome == "historico-itens.md"):
            _desce(arq, Path(nome))
        elif arq.is_dir() and re.match(r"^item\d+", nome):
            for f in sorted(arq.rglob("*")):
                if f.is_file():
                    _desce(f, Path(nome) / f.relative_to(arq))
            for d in sorted(arq.rglob("*"), reverse=True):
                if d.is_dir() and not any(d.iterdir()):
                    d.rmdir()
            if not any(arq.iterdir()):
                arq.rmdir()
    return movidos


def reorganizar(pasta_os: Path) -> dict:
    """Aplica a convenção de 24/08/2026 a uma OS SEM rede e sem token (é o
    modo --reorganizar, usado pela /aft-organiza-os): desce o conteúdo da
    raiz de cada pacote para as subpastas "baixada em <data>" e renumera os
    pacotes pela ordem das datas nos nomes. NÃO corrige a data de lavratura
    no nome (isso pede a API ou a leitura do PDF — a /aft-organiza-os ajusta
    a data antes de chamar aqui)."""
    notifs = pasta_os / "NOTIFICACOES"
    r = {"ok": True, "pasta": pasta_os.name, "movidos": 0, "renumerados": []}
    if not notifs.is_dir():
        return r
    for p in sorted(notifs.iterdir()):
        if p.is_dir() and RE_PACOTE.fullmatch(p.name):
            r["movidos"] += migrar_pacote_para_dias(p)
    antes = {p.name for p in notifs.iterdir() if p.is_dir()}
    renumerar_pacotes(notifs)
    r["renumerados"] = sorted(
        p.name for p in notifs.iterdir() if p.is_dir() and p.name not in antes)
    return r


def registrar_atividade(texto: str, detalhe: str) -> str:
    """Linha no Registro de atividades (best-effort, como no det_sync)."""
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
    linhas.insert(ult + 1, f"| {hoje} | Download DET (painel) | {detalhe} |\n")
    return "".join(linhas)


# ── Download de uma notificação ──────────────────────────────────────────────

def _salvar(destino: Path, conteudo: bytes) -> bool:
    """Grava se ainda não existe (idempotência). True = gravou agora."""
    if destino.exists() and destino.stat().st_size > 0:
        return False
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_bytes(conteudo)
    return True


def baixar_so_notificacao(pasta_os: Path, token: str, codigo: str) -> dict:
    """Baixa SÓ o documento da notificação (o PDF), sem os arquivos que o
    empregador entregou, sem o Relatório de Atendimento e sem o canal.

    Serve para ler o que foi notificado sem puxar megabytes de anexos — o caso
    de quem quer o histórico de notificações de uma empresa, não o conteúdo das
    entregas.

    **Não registra a visualização no DET, de propósito.** O download completo
    faz as mesmas leituras que o site faz ao abrir a notificação, e com isso
    apaga o triângulo amarelo de "atualização pendente". Aqui não: o AFT não
    olhou o que a empresa entregou, então o alerta tem de continuar na tela
    dele. Apagar o aviso sem ter visto o conteúdo seria mentir para o próprio
    auditor."""
    codigo = (codigo or "").strip().upper()
    if not re.fullmatch(r"[A-Z0-9]{6,}", codigo):
        raise ValueError(f"código de notificação inválido: {codigo!r}")
    r = {"ok": True, "codigo": codigo, "pasta": pasta_os.name,
         "so_notificacao": True, "baixados": 0, "ja_existiam": 0, "erros": []}
    n = pesquisar_por_codigo(token, codigo)
    if not n:
        raise RuntimeError(f"notificação {codigo} não encontrada no DET "
                           "(confira o código)")
    uid = n.get("uid")
    if not uid:
        raise RuntimeError(f"notificação {codigo} veio sem uid na pesquisa")
    raiz = pasta_do_pacote(pasta_os, codigo, lavratura=_data_nome(n.get("dataEnvio")))
    if raiz.is_dir():  # pacote existente entra na ordem certa mesmo sem baixar
        raiz = renumerar_pacotes(raiz.parent, raiz) or raiz
    destino = raiz / f"notificacao-{codigo}.pdf"
    r["pacote"] = str(raiz)
    if destino.exists() and destino.stat().st_size > 0:
        r["ja_existiam"] = 1
        return r
    raiz.mkdir(parents=True, exist_ok=True)
    # numeroDeLinhas=0 é o que o próprio site passa no download direto
    bruto = _requisicao(token, f"/notificacoes/{uid}/pdf",
                        params={"numeroDeLinhas": 0}, timeout=TIMEOUT_BLOB)
    if not bruto:
        raise RuntimeError("o DET devolveu um PDF vazio")
    destino.write_bytes(bruto)
    raiz = renumerar_pacotes(raiz.parent, raiz) or raiz
    r["pacote"] = str(raiz)
    r["baixados"] = 1
    r["arquivo"] = str(raiz / destino.name)
    return r


def baixar_notificacao(pasta_os: Path, token: str, codigo: str) -> dict:
    """Baixa os 2 PDFs e os arquivos de todos os itens para a pasta da OS.
    Um arquivo com erro não derruba os demais; token vencido derruba tudo
    (TokenExpirado sobe para o chamador avisar o AFT)."""
    codigo = (codigo or "").strip().upper()
    if not re.fullmatch(r"[A-Z0-9]{6,}", codigo):
        raise ValueError(f"código de notificação inválido: {codigo!r}")
    r = {"ok": True, "codigo": codigo, "pasta": pasta_os.name,
         "baixados": 0, "ja_existiam": 0, "invalidados": 0,
         "itens": 0, "sem_arquivo": 0, "eventos": 0,
         "mensagens_canal": 0, "anexos_canal": 0, "erros": []}

    n = pesquisar_por_codigo(token, codigo)
    if not n:
        raise RuntimeError(f"notificação {codigo} não encontrada no DET "
                           "(confira o código)")
    uid = n.get("uid")
    if not uid:
        raise RuntimeError(f"notificação {codigo} veio sem uid na pesquisa")

    def conta(gravou: bool):
        r["baixados" if gravou else "ja_existiam"] += 1

    # Tudo fica DENTRO do pacote NOTIFICACOES/<NN> - <COD> <data>/ — inclusive
    # os 2 PDFs, para não poluir a raiz da OS (convenção do AFT, 21/08/2026;
    # numeração, data de lavratura e subpasta do dia em 24/08/2026). PDF que um
    # download antigo deixou solto (na raiz da OS ou em NOTIFICACOES/) é
    # MOVIDO para dentro (migração, nunca re-baixado), e o conteúdo que morava
    # na raiz do pacote desce para a subpasta do dia em que foi baixado.
    raiz = pasta_do_pacote(pasta_os, codigo,
                           lavratura=_data_nome(n.get("dataEnvio")))
    raiz.mkdir(parents=True, exist_ok=True)
    movidos = migrar_pacote_para_dias(raiz)
    if movidos:
        r["movidos"] = movidos
    raiz = renumerar_pacotes(raiz.parent, raiz) or raiz
    r["pacote"] = raiz.name
    hoje = datetime.date.today().strftime("%d-%m-%Y")
    dia = raiz / f"baixada em {hoje}"
    r["dia"] = dia.name

    def _migrar(nome: str, para_o_dia_do_arquivo: bool = False) -> None:
        for base in (pasta_os, pasta_os / "NOTIFICACOES"):
            antigo = base / nome
            if not antigo.is_file():
                continue
            novo = (raiz / f"baixada em {_data_mtime(antigo)}" / nome
                    if para_o_dia_do_arquivo else raiz / nome)
            if not novo.exists():
                novo.parent.mkdir(parents=True, exist_ok=True)
                antigo.rename(novo)
                r["movidos"] = r.get("movidos", 0) + 1

    def _ja_baixado(rel: Path) -> bool:
        """O arquivo já veio num download anterior? (procura em todas as
        subpastas "baixada em <data>" do pacote)"""
        for d in raiz.glob("baixada em *"):
            f = d / rel
            if f.is_file() and f.stat().st_size > 0:
                return True
        return False

    # PDF da notificação: documento estático — baixa uma vez, depois pula.
    # numeroDeLinhas=0 é o que o próprio site passa no download direto.
    try:
        _migrar(f"notificacao-{codigo}.pdf")
        destino = raiz / f"notificacao-{codigo}.pdf"
        if destino.exists() and destino.stat().st_size > 0:
            r["ja_existiam"] += 1
        else:
            conta(_salvar(destino,
                          _requisicao(token, f"/notificacoes/{uid}/pdf",
                                      params={"numeroDeLinhas": 0},
                                      timeout=TIMEOUT_BLOB)))
    except TokenExpirado:
        raise
    except Exception as e:
        r["erros"].append(f"PDF da notificação: {e}")

    # Relatório de Atendimento: é uma FOTOGRAFIA do estado da notificação —
    # entrega nova da empresa o deixa velho. Por isso é baixado SEMPRE e
    # regravado (o DET carimba data de emissão no PDF, então comparar bytes
    # não diz nada). O tipo é OBRIGATÓRIO (400 "Parâmetro de URL tipo
    # inválido" sem ele, constatado em 21/08/2026) e MUDA O CONTEÚDO do PDF:
    # é o rádio "Itens da notificação" do modal do site (chunk 251 do bundle
    # do auditor-det, componente app-modal-emitir-relatorio-atendimento,
    # conferido em 23/08/2026) —
    #     tipo=0  Somente Não Entregues  (padrão do modal; relatório de exceção)
    #     tipo=1  Somente Entregues
    #     tipo=2  Todos os Itens
    # Aqui se pede SEMPRE tipo=2. Com tipo=0, numa empresa que atendeu tudo o
    # PDF sai dizendo "não consta item para o critério selecionado", com 0
    # itens e 0 arquivos — parece download vazio, e quem o lesse esperando o
    # inventário do que foi entregue concluiria o contrário do que ele diz.
    # tipo=2 é superconjunto: traz o que faltou (a prova de omissão do art.
    # 630, §4º, da CLT) E o que veio, com status, histórico e MD5/SHA1 de cada
    # arquivo. exibeHistorico=true é o padrão do modal e se mantém.
    # Vai para a subpasta DO DIA (convenção de 24/08/2026): cada "baixada em
    # <data>" guarda a fotografia daquele dia — as dos dias anteriores ficam.
    try:
        _migrar(f"relatorio-atendimento-{codigo}.pdf", para_o_dia_do_arquivo=True)
        destino = dia / f"relatorio-atendimento-{codigo}.pdf"
        novo_pdf = _requisicao(token,
                               f"/notificacoes/{uid}/pdf-relatorio-atendimento",
                               params={"tipo": 2, "exibeHistorico": "true"},
                               timeout=TIMEOUT_BLOB)
        if not destino.exists() or destino.stat().st_size == 0:
            conta(_salvar(destino, novo_pdf))
        else:
            destino.write_bytes(novo_pdf)
            r["relatorio_refrescado"] = True
    except TokenExpirado:
        raise
    except Exception as e:
        r["erros"].append(f"Relatório de Atendimento: {e}")

    # Arquivos entregues e histórico de eventos, item a item.
    historico: list[tuple[str, list[dict]]] = []
    itens = _json_api(token, "/itens-notificacao", params={"uidNotificacao": uid})
    r["itens"] = len(itens or [])
    for item in itens or []:
        uid_item = item.get("uid")
        rot = pasta_do_item(item.get("ordem", "?"), item.get("descricao") or "")
        if not uid_item:
            r["erros"].append(f"{rot}: item sem uid")
            continue
        # Eventos do item: pedidos de prorrogação, justificativas, mudanças de
        # status. É onde mora a história de um item SEM entrega (a lacuna
        # constatada no caso real de 21/08/2026: notificação só com pedidos de
        # prazo baixava "nada" e não contava a história).
        try:
            evs = _json_api(token, "/eventos-item", params={"uidItem": uid_item})
        except TokenExpirado:
            raise
        except Exception as e:
            evs = []
            r["erros"].append(f"{rot}: eventos: {e}")
        if evs:
            r["eventos"] += len(evs)
            historico.append((rot, evs))
        try:
            arquivos = _json_api(token, "/arquivos-item",
                                 params={"uidItem": uid_item})
        except TokenExpirado:
            raise
        except Exception as e:
            r["erros"].append(f"{rot}: {e}")
            continue
        if not arquivos:
            r["sem_arquivo"] += 1
            continue
        usados: set[str] = set()
        for arq in arquivos:
            nome = nome_do_arquivo(arq.get("nome") or "", usados)
            invalidado = arq.get("status") in STATUS_INVALIDADOS
            rel = Path(rot) / ("invalidados" if invalidado else "") / nome
            if invalidado:
                r["invalidados"] += 1
            # Já veio num dia anterior (qualquer "baixada em <data>")? Não
            # baixa de novo: a pasta do dia só recebe o que chegou HOJE.
            if _ja_baixado(rel):
                r["ja_existiam"] += 1
                continue
            try:
                conta(_salvar(dia / rel,
                              _requisicao(token, f"/arquivos-item/{arq['uid']}/blob",
                                          timeout=TIMEOUT_BLOB)))
            except TokenExpirado:
                raise
            except Exception as e:
                r["erros"].append(f"{rot}/{nome}: {e}")

    # historico-itens.md: a linha do tempo de cada item, legível. Arquivo
    # DERIVADO do DET — gravado por inteiro a cada download, na pasta DO DIA
    # (o de cada dia é a fotografia daquele dia); anotação do AFT não pertence
    # a ele (vai no memory.md).
    if historico:
        md = [f"# Histórico dos itens — notificação {codigo}", "",
              "Gerado do DET pelo AFT Toolkit (arquivo derivado: regravado a "
              "cada download). Pedidos de prorrogação, justificativas e "
              "mudanças de status de cada item solicitado.", ""]
        for rot, evs in historico:
            md.append(f"## {rot}")
            for ev in evs:
                linha = "- " + (_data_hora_br(ev.get("dataEvento")) or "sem data")
                st = ev.get("status")
                linha += " · " + STATUS_ITEM.get(st, f"status {st}")
                if ev.get("dataAntecipacao"):
                    linha += f" · nova data {_data_hora_br(ev['dataAntecipacao'])}"
                obs = _texto_plano(ev.get("observacao"))
                if obs:
                    linha += f" · justificativa: {obs}"
                md.append(linha)
            md.append("")
        dia.mkdir(parents=True, exist_ok=True)
        (dia / "historico-itens.md").write_text("\n".join(md), encoding="utf-8")

    # Canal de comunicação: mensagens trocadas naquela notificação. Vai para
    # canal-comunicacao/ no pacote — mensagens.md (derivado, regravado), os
    # anexos e o histórico oficial em PDF (refrescado a cada download).
    # SOMENTE LEITURA: registrar ciência/responder é ato do AFT, no site.
    try:
        canal = _json_api(token, f"/notificacoes/{uid}/canal-comunicacao")
    except TokenExpirado:
        raise
    except Exception:
        canal = None  # canal desabilitado/inexistente não é erro
    registros = _registros_canal(canal)
    if registros:
        pasta_canal = raiz / "canal-comunicacao"
        pasta_canal.mkdir(parents=True, exist_ok=True)
        md = [f"# Canal de comunicação — notificação {codigo}", "",
              "Gerado do DET pelo AFT Toolkit (arquivo derivado: regravado a "
              "cada download). O histórico oficial em PDF está ao lado "
              "(historico-canal.pdf).", ""]
        usados: set[str] = set()
        for reg in registros:
            tipo = reg.get("tipoRegistroComunicacao")
            quando = _data_hora_br(reg.get("createdAt")) or "sem data"
            emissor = {"A": "AUDITOR", "E": "EMPREGADOR"}.get(
                reg.get("tipoUsuarioEmissor"), "")
            nome_emissor = _texto_plano(reg.get("nomeEmissor")
                                        or reg.get("usuarioEmissor"))
            quem = f"{emissor} ({nome_emissor})" if nome_emissor else emissor
            if tipo == "B":
                md.append(f"- {quando} · {quem or 'AUDITOR'} desabilitou o canal")
                continue
            if tipo == "D":
                md.append(f"- {quando} · {quem or 'AUDITOR'} habilitou o canal")
                continue
            r["mensagens_canal"] += 1
            md.append(f"- {quando} · {quem or 'mensagem'}: "
                      f"{_texto_plano(reg.get('texto')) or '(sem texto)'}")
            if reg.get("arquivoNome") and reg.get("uid"):
                nome = nome_do_arquivo(reg["arquivoNome"], usados)
                md.append(f"  - anexo: {nome}")
                destino = pasta_canal / nome
                if destino.exists() and destino.stat().st_size > 0:
                    r["ja_existiam"] += 1
                else:
                    try:
                        conta(_salvar(destino, _requisicao(
                            token,
                            f"/notificacoes/{uid}/arquivos-canal-comunicacao/"
                            f"{reg['uid']}/blob", timeout=TIMEOUT_BLOB)))
                        r["anexos_canal"] += 1
                    except TokenExpirado:
                        raise
                    except Exception as e:
                        r["erros"].append(f"canal/{nome}: {e}")
        (pasta_canal / "mensagens.md").write_text("\n".join(md) + "\n",
                                                  encoding="utf-8")
        try:
            (pasta_canal / "historico-canal.pdf").write_bytes(_requisicao(
                token, f"/notificacoes/{uid}/pdf-historico-canal-comunicacao",
                timeout=TIMEOUT_BLOB))
        except TokenExpirado:
            raise
        except Exception as e:
            r["erros"].append(f"canal/historico-canal.pdf: {e}")

    # Espelha o "abrir a notificação" do site: GET do detalhe da notificação e
    # de cada item — as mesmas chamadas que o front dispara quando o AFT abre
    # a tela e o "Visualizar Item Solicitado". É isso que faz o DET registrar
    # a visualização e apagar o triângulo amarelo "Existe atualização
    # pendente" (sem estas leituras, o alerta continuava aceso mesmo com tudo
    # baixado — constatado pelo AFT em 21/08/2026, caso real).
    try:
        _json_api(token, f"/notificacoes/{uid}")
        for item in itens or []:
            if item.get("uid"):
                _json_api(token, f"/itens-notificacao/{item['uid']}",
                          params={"uidNotificacao": uid})
        r["visto_no_det"] = True
    except TokenExpirado:
        raise
    except Exception as e:
        r["visto_no_det"] = False
        r["erros"].append(f"registro de visualização no DET: {e}")

    _registrar_no_memory(pasta_os, r)
    return r


def _registrar_no_memory(pasta_os: Path, r: dict) -> None:
    """Linha de atividade na ficha — só quando algo foi baixado agora."""
    if not r["baixados"]:
        return
    mem = pasta_os / "memory.md"
    if not mem.exists():
        return
    try:
        texto = mem.read_text(encoding="utf-8")
        partes = [f"{r['codigo']}: {r['baixados']} arquivo(s) baixado(s)"]
        if r["ja_existiam"]:
            partes.append(f"{r['ja_existiam']} já existia(m)")
        if r["erros"]:
            partes.append(f"{len(r['erros'])} erro(s)")
        novo = registrar_atividade(texto, " · ".join(partes))
        if novo == texto:
            return
        if BACKUP.exists():
            subprocess.run([sys.executable, str(BACKUP), str(mem)],
                           capture_output=True, timeout=30)
        mem.write_text(novo, encoding="utf-8")
    except Exception as e:
        r["erros"].append(f"registro no memory.md: {e}")


# ── Varredura do DET (passo opcional da /aft-organiza-os) ────────────────────

RE_CHECKBOX_DET = re.compile(r"^\s*-\s*\[[ xX]\]\s*\**\s*([A-Z0-9]{8,})")


def codigos_da_ficha(texto: str) -> list[dict]:
    """As notificações da seção `## Notificações DET` de um memory.md:
    [{codigo, pendente, cancelada}]. `pendente` vem da sub-linha de detalhes
    do sync ("atualização pendente" = entrega nova no DET); `cancelada` idem
    ("CANCELADA no DET"). Função pura, testável sem rede."""
    linhas = texto.splitlines()
    ini = next((i + 1 for i, l in enumerate(linhas)
                if l.strip() == "## Notificações DET"), -1)
    if ini < 0:
        return []
    fim = next((i for i in range(ini, len(linhas))
                if linhas[i].strip().startswith("## ")), len(linhas))
    out: list[dict] = []
    for l in linhas[ini:fim]:
        m = RE_CHECKBOX_DET.match(l)
        if m:
            out.append({"codigo": m.group(1), "pendente": False,
                        "cancelada": False})
        elif out and l.strip().startswith("-"):
            if "atualização pendente" in l:
                out[-1]["pendente"] = True
            if "CANCELADA no DET" in l:
                out[-1]["cancelada"] = True
    return out


def varredura(base: Path, porta: int = 8347) -> dict:
    """Varre o DET para TODAS as OS de OS ATIVAS (pedido do AFT em
    24/08/2026 — o passo opcional da /aft-organiza-os):

    1. pede ao painel um sync das fichas (POST /api/det-sync sem corpo — usa
       o token que a via 1 ou a extensão deixou na RAM): notificação nova
       entra na seção `## Notificações DET` de cada memory.md;
    2. baixa o pacote COMPLETO (PDF + relatório + arquivos entregues) das
       notificações SEM pacote local em NOTIFICACOES/ e SEM alerta pendente.
       Notificação com o triângulo amarelo ("atualização pendente" na ficha)
       NUNCA entra no lote — regra do AFT (24/08/2026): o download completo
       apagaria o alerta em silêncio, e o triângulo é o aviso de que há
       entrega que o auditor ainda não viu. Elas voltam em `pendentes`, para
       baixa INDIVIDUAL (/aft-det-baixar <código>), que aí sim apaga o
       alerta como ato consciente. As já em dia ficam quietas.

    Token vencido no meio devolve token_expirado com o parcial — renovar e
    rodar de novo é seguro (tudo idempotente). Notificação de empresa SEM
    OS não entra: criar OS é papel da /aft-nova-auditoria."""
    r = {"ok": True, "sync": None, "os": [], "baixadas": 0,
         "sem_novidade": 0, "pendentes": 0, "canceladas": 0, "erros": []}

    # O painel roda sob um vigia (launchd/Agendador de Tarefas) que o reergue
    # sozinho em ~10 s quando cai. Queda no meio do lote vira PAUSA, não
    # falha: toda conexão recusada ganha uma segunda chance após 15 s (caso
    # real de 24/08/2026: o servidor caiu entre dois downloads da primeira
    # varredura e os 9 códigos seguintes falharam à toa).
    ESPERA_VIGIA = 15

    for tentativa in (1, 2):
        req = urllib.request.Request(
            f"http://127.0.0.1:{porta}/api/det-sync", data=b"{}",
            headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=600) as resp:
                r["sync"] = json.loads(resp.read().decode("utf-8"))
            break
        except urllib.error.HTTPError as e:
            try:
                corpo = json.loads(e.read().decode("utf-8"))
            except Exception:
                corpo = {}
            if corpo.get("token_expirado"):
                return {"ok": False, "token_expirado": True,
                        "erro": corpo.get("erro") or "token do DET ausente/vencido"}
            r["erros"].append(f"sync das fichas: {corpo.get('erro') or e.code}")
            break
        except Exception as e:
            if tentativa == 1:
                time.sleep(ESPERA_VIGIA)
                continue
            return {"ok": False, "painel_fora": True,
                    "erro": f"servidor do painel não respondeu ({e}) — "
                            "suba com instalar_servidor_painel.py reiniciar"}

    for pasta in sorted(p for p in base.iterdir()
                        if p.is_dir() and (p / "memory.md").is_file()):
        try:
            texto = (pasta / "memory.md").read_text(encoding="utf-8")
        except OSError as e:
            r["erros"].append(f"{pasta.name}: memory.md ilegível: {e}")
            continue
        ros = {"os": pasta.name, "baixadas": [], "pendentes": [], "erros": []}
        notifs = pasta / "NOTIFICACOES"
        for nf in codigos_da_ficha(texto):
            codigo = nf["codigo"]
            if nf["cancelada"]:
                r["canceladas"] += 1
                continue
            if nf["pendente"]:
                # Triângulo amarelo: fora do lote, SEMPRE (mesmo sem pacote
                # local) — baixa individual preserva o alerta como aviso.
                ros["pendentes"].append(codigo)
                r["pendentes"] += 1
                continue
            tem_pacote = notifs.is_dir() and any(
                codigo in q.name.upper()
                for q in notifs.iterdir() if q.is_dir())
            if tem_pacote:
                r["sem_novidade"] += 1
                continue
            res = via_painel(pasta.name, codigo, porta)
            if res.get("painel_fora"):  # painel caiu: o vigia o reergue
                time.sleep(ESPERA_VIGIA)
                res = via_painel(pasta.name, codigo, porta)
            if res.get("token_expirado"):
                r.update(ok=False, token_expirado=True,
                         erro="token venceu no meio da varredura — renove e "
                              "rode de novo (o que já veio não baixa de novo)")
                if ros["baixadas"] or ros["pendentes"] or ros["erros"]:
                    r["os"].append(ros)
                return r
            if res.get("ok"):
                ros["baixadas"].append({
                    "codigo": codigo, "pacote": res.get("pacote"),
                    "baixados": res.get("baixados", 0),
                    "ja_existiam": res.get("ja_existiam", 0)})
                r["baixadas"] += 1
            else:
                ros["erros"].append(f"{codigo}: {res.get('erro') or res}")
        if ros["baixadas"] or ros["pendentes"] or ros["erros"]:
            r["os"].append(ros)
        r["erros"] += [f"{pasta.name} · {e}" for e in ros["erros"]]
    return r


def via_painel(pasta: str, codigo: str, porta: int = 8347,
               so_notificacao: bool = False) -> dict:
    """POST /api/det-baixar no servidor local do painel (o token mora lá).
    `pasta` pode ser o caminho completo ou só o nome da pasta da OS.
    Devolve o JSON da resposta — inclusive o 409 de token vencido, para o
    chamador orientar o Sincronizar sem tratar exceção."""
    corpo = json.dumps({"pasta": Path(pasta).name, "codigo": codigo,
                        "so_notificacao": bool(so_notificacao)}).encode("utf-8")
    req = urllib.request.Request(
        f"http://127.0.0.1:{porta}/api/det-baixar", data=corpo,
        headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=600) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            return json.loads(e.read().decode("utf-8"))
        except Exception:
            return {"ok": False, "erro": f"painel respondeu {e.code}"}
    except Exception as e:
        return {"ok": False, "painel_fora": True,
                "erro": f"servidor do painel não respondeu ({e}) — "
                        "suba com instalar_servidor_painel.py reiniciar"}


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):  # console Windows é cp1252
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    argv = [a for a in sys.argv[1:] if a != "--so-notificacao"]
    so_notif = "--so-notificacao" in sys.argv
    porta = 8347
    if "--porta" in argv:  # instância de teste do painel (debug)
        i = argv.index("--porta")
        porta = int(argv[i + 1])
        del argv[i:i + 2]
    if len(argv) == 3 and argv[0] == "--via-painel":
        print(json.dumps(via_painel(argv[1], argv[2], porta,
                                    so_notificacao=so_notif),
                         ensure_ascii=False, indent=2))
    elif len(argv) == 2 and argv[0] == "--reorganizar":
        print(json.dumps(reorganizar(Path(argv[1])),
                         ensure_ascii=False, indent=2))
    elif len(argv) == 2 and argv[0] == "--varredura":
        print(json.dumps(varredura(Path(argv[1]), porta),
                         ensure_ascii=False, indent=2))
    elif len(argv) == 3:
        motor = baixar_so_notificacao if so_notif else baixar_notificacao
        print(json.dumps(motor(Path(argv[0]), argv[2], argv[1]),
                         ensure_ascii=False, indent=2))
    else:
        print("uso: python det_baixar.py [--so-notificacao] --via-painel "
              "\"<pasta da OS>\" <CODIGO>\n"
              "     python det_baixar.py [--so-notificacao] \"<pasta da OS>\" "
              "<CODIGO> <token>\n"
              "     python det_baixar.py --reorganizar \"<pasta da OS>\"\n"
              "     python det_baixar.py --varredura \"<pasta OS ATIVAS>\"\n\n"
              "  --so-notificacao: baixa só o PDF do documento — sem os arquivos\n"
              "  entregues pelo empregador, e sem apagar o alerta amarelo do DET\n"
              "  --reorganizar: sem rede — aplica às pastas de NOTIFICACOES/ a\n"
              "  convenção de 24/08/2026 (numeração e subpastas por dia)\n"
              "  --varredura: sync das fichas + download do que falta em todas\n"
              "  as OS (token já no painel; passo opcional da /aft-organiza-os)",
              file=sys.stderr)
        sys.exit(1)
