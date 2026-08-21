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
mora em NOTIFICACOES/, no pacote "<CODIGO> <dd-mm-aaaa>" (data do primeiro
download; convenção pedida pelo AFT em 21/08/2026 — sem o prefixo
"notificacao-" no nome da pasta):

    NOTIFICACOES/<CODIGO> <dd-mm-aaaa>/
        notificacao-<CODIGO>.pdf              o PDF da notificação
        relatorio-atendimento-<CODIGO>.pdf    o Relatório de Atendimento
        item<N>_<descrição do item>/          um por item solicitado
            <arquivo entregue>
            invalidados/<arquivo>             o que o AFT rejeitou/dispensou

Legados são migrados sozinhos na próxima execução: pacote "notificacao-<COD>"
(na raiz da OS ou em NOTIFICACOES/) é renomeado para o padrão — preservando
sufixo descritivo que o AFT tenha dado (aí só se usa a pasta, sem renomear) —
e PDF solto na raiz ou em NOTIFICACOES/ é movido para dentro do pacote
(conta em `movidos`).

Em vez do ZIP geral do site (que exige segundo request numa URL volátil e
chega sem estrutura), cada arquivo é baixado individualmente pelo endpoint de
arquivos do item — assim a pasta nasce organizada por item, com a descrição
oficial vinda da API (nada de raspar o PDF para adivinhar nomes).

Endpoints (lidos do bundle público do front do DET em 21/08/2026 — chunk 251;
ver a nota sync-det-e-extensao.md para o método de conferência no bundle):

    POST /services/auditor/v1/notificacoes/pesquisa          (codigoNotificacao)
    GET  /services/auditor/v1/notificacoes/{uid}/pdf?numeroDeLinhas=0
    GET  /services/auditor/v1/notificacoes/{uid}/pdf-relatorio-atendimento
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
                corpo: dict | None = None, timeout: int = TIMEOUT_JSON) -> bytes:
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
        method="POST" if corpo is not None else "GET",
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


def pasta_do_pacote(pasta_os: Path, codigo: str, hoje: str | None = None) -> Path:
    """A pasta-pacote da notificação: NOTIFICACOES/<CODIGO> <dd-mm-aaaa>.

    Reusa pacote existente que contenha o código no nome — em NOTIFICACOES/ ou
    na raiz da OS, com ou sem o prefixo legado "notificacao-". Nome "puro"
    (só prefixo/código/data) é RENOMEADO para o padrão, preservando a data que
    já estiver no nome ou, sem data, usando a da última modificação da pasta;
    nome com sufixo descritivo do AFT ("<COD> jornada") é respeitado como
    está. Sem pacote nenhum: NOTIFICACOES/<CODIGO> <hoje> (criada na primeira
    gravação). A data no nome é a do PRIMEIRO download — downloads seguintes
    (entrega parcelada, prorrogação) acumulam no mesmo pacote."""
    hoje = hoje or datetime.date.today().strftime("%d-%m-%Y")
    notifs = pasta_os / "NOTIFICACOES"
    cands: list[Path] = []
    for base in (notifs, pasta_os):
        if base.is_dir():
            cands += sorted(p for p in base.iterdir()
                            if p.is_dir() and codigo in p.name.upper())
    if not cands:
        return notifs / f"{codigo} {hoje}"
    alvo = cands[0]
    resto = alvo.name.upper()
    if resto.startswith("NOTIFICACAO-"):
        resto = resto[len("NOTIFICACAO-"):]
    resto = resto.replace(codigo, "", 1).strip()
    if resto and not RE_SO_DATA.fullmatch(resto):
        return alvo  # sufixo descritivo do AFT: usa sem renomear
    data = resto or datetime.date.fromtimestamp(
        alvo.stat().st_mtime).strftime("%d-%m-%Y")
    novo = notifs / f"{codigo} {data}"
    if novo == alvo:
        return alvo
    if novo.exists():
        return novo  # padrão já existe; nunca mescla pastas sozinho
    notifs.mkdir(parents=True, exist_ok=True)
    alvo.rename(novo)
    return novo


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

    # Tudo fica DENTRO do pacote NOTIFICACOES/<COD> <data>/ — inclusive os
    # 2 PDFs, para não poluir a raiz da OS (convenção do AFT, 21/08/2026).
    # PDF que um download antigo deixou solto (na raiz da OS ou em
    # NOTIFICACOES/) é MOVIDO para dentro (migração, nunca re-baixado).
    raiz = pasta_do_pacote(pasta_os, codigo)
    r["pacote"] = raiz.name

    def _migrar(nome: str) -> None:
        novo = raiz / nome
        for base in (pasta_os, pasta_os / "NOTIFICACOES"):
            antigo = base / nome
            if antigo.is_file() and not novo.exists():
                novo.parent.mkdir(parents=True, exist_ok=True)
                antigo.rename(novo)
                r["movidos"] = r.get("movidos", 0) + 1

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
    # não diz nada). tipo=0/exibeHistorico=true são os padrões do modal do
    # site; o tipo é OBRIGATÓRIO (400 sem ele, constatado em 21/08/2026).
    try:
        _migrar(f"relatorio-atendimento-{codigo}.pdf")
        destino = raiz / f"relatorio-atendimento-{codigo}.pdf"
        novo_pdf = _requisicao(token,
                               f"/notificacoes/{uid}/pdf-relatorio-atendimento",
                               params={"tipo": 0, "exibeHistorico": "true"},
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
            destino = raiz / rot / ("invalidados/" if invalidado else "") / nome
            if invalidado:
                r["invalidados"] += 1
            if destino.exists() and destino.stat().st_size > 0:
                r["ja_existiam"] += 1
                continue
            try:
                conta(_salvar(destino,
                              _requisicao(token, f"/arquivos-item/{arq['uid']}/blob",
                                          timeout=TIMEOUT_BLOB)))
            except TokenExpirado:
                raise
            except Exception as e:
                r["erros"].append(f"{rot}/{nome}: {e}")

    # historico-itens.md: a linha do tempo de cada item, legível. Arquivo
    # DERIVADO do DET — regravado por inteiro a cada download; anotação do AFT
    # não pertence a ele (vai no memory.md).
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
        (raiz / "historico-itens.md").write_text("\n".join(md), encoding="utf-8")

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


def via_painel(pasta: str, codigo: str, porta: int = 8347) -> dict:
    """POST /api/det-baixar no servidor local do painel (o token mora lá).
    `pasta` pode ser o caminho completo ou só o nome da pasta da OS.
    Devolve o JSON da resposta — inclusive o 409 de token vencido, para o
    chamador orientar o Sincronizar sem tratar exceção."""
    corpo = json.dumps({"pasta": Path(pasta).name,
                        "codigo": codigo}).encode("utf-8")
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
    if len(sys.argv) == 4 and sys.argv[1] == "--via-painel":
        print(json.dumps(via_painel(sys.argv[2], sys.argv[3]),
                         ensure_ascii=False, indent=2))
    elif len(sys.argv) == 4:
        print(json.dumps(baixar_notificacao(Path(sys.argv[1]), sys.argv[3],
                                            sys.argv[2]),
                         ensure_ascii=False, indent=2))
    else:
        print("uso: python det_baixar.py --via-painel \"<pasta da OS>\" <CODIGO>\n"
              "     python det_baixar.py \"<pasta da OS>\" <CODIGO> <token>",
              file=sys.stderr)
        sys.exit(1)
