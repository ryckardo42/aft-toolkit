# -*- coding: utf-8 -*-
"""
portal_toolkit.py - o lado cliente do portal, para o atualizar_toolkit.py.

Aqui mora tudo o que envolve FALAR com o portal `notebooks-aft`: onde fica o
codigo de acesso nesta maquina, como se pergunta ao portal qual e a versao
disponivel, e como cada falha vira frase em portugues com o proximo passo.
Quem aplica o pacote e o atualizar_toolkit.py; este arquivo nao escreve uma
linha dentro da pasta de skills.

ONDE MORA O CODIGO DE ACESSO - E POR QUE NAO E ONDE PARECE OBVIO
----------------------------------------------------------------
Nem na pasta de skills, nem no aft-config.md.

  * FORA DA PASTA DE SKILLS porque e justamente ela que a atualizacao
    substitui: guardar o token em ~/.claude/skills seria perde-lo na primeira
    atualizacao que ele mesmo autorizou - e o AFT ficaria preso, sem entender
    por que o codigo "some" toda vez. Vale igual para o registro da ultima
    consulta.
  * FORA DO aft-config.md porque aquele arquivo e lido, editado e IMPRESSO na
    tela por varias skills e pelo /aft-doctor. Credencial nao mora em arquivo
    que se manda mostrar.

Os dois arquivos ficam na pasta de trabalho do AFT, descoberta pelo
pasta_aft.py (que nunca se presume: pode ter sido movida):

    <pasta AFT>/.aft-toolkit-token      o codigo de acesso, e mais nada
    <pasta AFT>/.aft-toolkit-consulta.json   quando foi a ultima consulta

Tres regras acompanham o token, e as tres sao contrato: o /aft-doctor confere
que ele existe sem imprimir o valor; o erro_ticket.py nao le esse arquivo ao
montar um ticket (e ainda esconde o valor, caso ele apareca num traceback); e
o assistente nunca ecoa o token no chat.

O CONTRATO COM O PORTAL (issue #138)
------------------------------------
Uma unica rota autenticada. O cliente manda Gmail, token e a versao instalada;
o servidor confere o acesso CONTRA A TABELA DELE e responde:

    POST <portal>/api/toolkit/versao
    {"gmail": "...", "token": "...", "versao_instalada": "2026.08.29-abc1234"}

    200  {"versao": "...", "sha256": "...", "novidades": "<markdown>",
          "url": "<endereco assinado, de validade curta, do .zip>"}
    401  {"erro": "token_invalido"}   codigo desconhecido, trocado ou cancelado
    403  {"erro": "sem_acesso"}       o Gmail nao esta liberado para o toolkit

O token vai no CORPO, nunca na URL: endereco vaza em log de servidor, em
historico e em captura de tela. A versao instalada vai junto porque e ela que
permite ao portal montar o changelog DO PERIODO - o AFT quer ler o que mudou
desde a versao dele, nao o changelog inteiro.

Quem decide se ha novidade e o cliente, comparando a versao anunciada com a
instalada. O portal so anuncia o que tem.

UMA CONSULTA POR DIA
--------------------
O /aft-bom-dia vai chamar isto toda manha, e ninguem quer uma chamada de rede
a cada conversa. A resposta fica registrada em .aft-toolkit-consulta.json e
vale ate a data virar. O registro guarda a versao, o changelog e a versao
instalada na hora - nunca a `url` assinada, que expira em minutos e nao serve
para reaproveitar, e nunca o token. Se a versao instalada mudar (o AFT
atualizou), o registro e considerado velho na hora.
"""

from __future__ import annotations

import datetime
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

AQUI = Path(__file__).resolve().parent
if str(AQUI) not in sys.path:  # uma vez so: pasta_estado() e chamada varias vezes
    sys.path.insert(0, str(AQUI))

PORTAL = "https://notebooks-aft.vercel.app"
ROTA = "/api/toolkit/versao"
TIMEOUT = 30  # s

ARQUIVO_TOKEN = ".aft-toolkit-token"
ARQUIVO_CONSULTA = ".aft-toolkit-consulta.json"

# Estados que o cliente sabe traduzir. Os quatro primeiros sao os da issue #142.
ESTADOS = ("ok", "sem_token", "token_invalido", "sem_acesso", "sem_novidade",
           "sem_gmail", "portal_indisponivel")


# --------------------------------------------------------- onde ficam as coisas

def pasta_estado() -> Path:
    """A pasta de trabalho do AFT. Fora da pasta de skills, sempre - ver o
    cabecalho. Se o pasta_aft.py nao puder responder (defeito ou maquina meio
    instalada), cai para ~/.claude, que tambem sobrevive a atualizacao."""
    try:
        from pasta_aft import pasta_aft as _pasta_aft
        return Path(_pasta_aft())
    except Exception:
        return Path.home() / ".claude"


def caminho_token() -> Path:
    return pasta_estado() / ARQUIVO_TOKEN


def caminho_consulta() -> Path:
    return pasta_estado() / ARQUIVO_CONSULTA


# ------------------------------------------------------------------- o token

# Caracteres que grudam no codigo sem aparecer na tela. O BOM e o mais comum:
# no Windows, arquivo salvo pelo Bloco de Notas ou pelo PowerShell ganha um, e
# lido no console cp1252 ele vira tres caracteres na frente do codigo. Zero-width
# e hifen suave vem de copiar de dentro de um e-mail em HTML.
INVISIVEIS = "\ufeff\u200b\u200c\u200d\u2060\u00ad"
ASPAS = "\"'\u2018\u2019\u201c\u201d\u00ab\u00bb`"

# Mesma regra do portal (api/_lib/toolkit.js, pareceCodigo). Vive nos dois lados
# de proposito: o que nao tem forma de codigo nunca chega a ser gravado aqui, e
# nunca chega a ser consultado la.
PREFIXO_CODIGO = "aft_"
_CORPO_CODIGO = re.compile(r"[A-Za-z0-9_-]+")


def limpar_codigo(valor: str) -> str:
    """Tira do codigo o que gruda nele sem aparecer: espaco em volta, BOM,
    caracteres de largura zero e aspas que vieram junto na copia."""
    valor = (valor or "").strip().strip(ASPAS).strip()
    return "".join(c for c in valor if c not in INVISIVEIS).strip()


def parece_codigo(valor: str) -> bool:
    """O valor tem forma de codigo de acesso? Espelha a conferencia do portal."""
    return (isinstance(valor, str)
            and valor.startswith(PREFIXO_CODIGO)
            and len(PREFIXO_CODIGO) + 20 <= len(valor) <= 200
            and _CORPO_CODIGO.fullmatch(valor[len(PREFIXO_CODIGO):]) is not None)


def ler_token() -> str | None:
    """O codigo de acesso, ou None se nao houver. Nunca levanta excecao: falta
    de token e um estado previsto, nao um acidente.

    Le com utf-8-sig e passa pelo `limpar_codigo` para que uma instalacao que
    ja gravou um codigo sujo (antes desta correcao) volte a funcionar sozinha,
    sem o AFT ter de regravar nada."""
    try:
        valor = caminho_token().read_text(encoding="utf-8-sig")
    except OSError:
        return None
    return limpar_codigo(valor) or None


def gravar_token(valor: str) -> Path:
    """Guarda o codigo de acesso. Devolve o caminho; nunca devolve o valor.

    Confere a FORMA antes de gravar. Em 30/08/2026 uma AFT colou o codigo
    certo, o arquivo temporario tinha um BOM, este metodo respondeu ok:true e
    o portal recusou com "codigo antigo, trocado ou cancelado" - mensagem que
    descrevia uma causa que nao era a dela e mandou pedir um codigo novo, que
    daria no mesmo. Guardar em silencio o que nunca vai funcionar e pior do que
    recusar na hora."""
    valor = limpar_codigo(valor)
    if not valor:
        raise ValueError("o código de acesso veio vazio")
    if len(valor.split()) > 1:
        raise ValueError("o código de acesso não pode ter espaço no meio - "
                         "cole só o código, sem texto em volta")
    if not parece_codigo(valor):
        raise ValueError(
            "isto não tem forma de código de acesso: o código começa com "
            f"'{PREFIXO_CODIGO}' e vem depois só com letras, números, '-' e '_'. "
            "Confira se copiou o código inteiro do e-mail, sem cortar o começo "
            "nem levar texto junto, e cole de novo.")
    alvo = caminho_token()
    alvo.parent.mkdir(parents=True, exist_ok=True)
    alvo.write_text(valor + "\n", encoding="utf-8")
    try:  # so o dono le (no Windows nao existe, e nao faz falta)
        os.chmod(alvo, 0o600)
    except OSError:
        pass
    return alvo


def tem_token() -> bool:
    return ler_token() is not None


# -------------------------------------------------------------------- o Gmail

def gmail() -> str | None:
    """O e-mail do cadastro, lido do aft-config.md. E o mesmo campo que as
    skills do NotebookLM ja usam - nao se inventa um segundo lugar para a
    mesma informacao."""
    try:
        cfg = pasta_estado() / "aft-config.md"
        for linha in cfg.read_text(encoding="utf-8").splitlines():
            m = re.match(r'\s*gmail\s*:\s*"?([^"#\s]+)"?', linha)
            if m:
                return m.group(1).strip()
    except OSError:
        pass
    return None


# ------------------------------------------------------- registro da consulta

def _hoje() -> str:
    return datetime.date.today().isoformat()


def consulta_registrada(versao_instalada: str | None,
                        base: str = PORTAL) -> dict | None:
    """A resposta de hoje, se ja houver uma. None quando a data virou, quando
    o AFT atualizou desde entao, quando a resposta veio de outro endereco (um
    ensaio contra portal de mentira nao pode responder pelo portal de verdade
    pelo resto do dia), ou quando nao ha registro nenhum."""
    try:
        dados = json.loads(caminho_consulta().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(dados, dict) or dados.get("dia") != _hoje():
        return None
    if dados.get("versao_instalada") != versao_instalada:
        return None
    if dados.get("portal") != base:
        return None
    resposta = dados.get("resposta")
    return resposta if isinstance(resposta, dict) else None


def registrar_consulta(resposta: dict, versao_instalada: str | None,
                       base: str = PORTAL) -> None:
    """Guarda a resposta do dia. A `url` assinada NAO entra (expira em minutos)
    e o token nunca chega aqui. Falha de escrita e silenciosa de proposito:
    disco cheio nao pode impedir a atualizacao de acontecer."""
    limpa = {k: v for k, v in resposta.items() if k != "url"}
    try:
        caminho_consulta().parent.mkdir(parents=True, exist_ok=True)
        caminho_consulta().write_text(json.dumps(
            {"dia": _hoje(), "quando": datetime.datetime.now().isoformat(timespec="seconds"),
             "portal": base, "versao_instalada": versao_instalada,
             "resposta": limpa},
            ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError:
        pass


# ------------------------------------------------------------ a conversa em si

def _erro_do_corpo(bruto: bytes) -> str | None:
    """O campo `erro` do corpo, quando o portal manda um dos nomes que este
    cliente conhece. E o que desempata um 403 que e falta de acesso de um 403
    que e token cancelado."""
    try:
        dados = json.loads(bruto.decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        return None
    nome = dados.get("erro") if isinstance(dados, dict) else None
    return nome if nome in ESTADOS else None


def consultar(gmail_do_aft: str, token: str, versao_instalada: str | None,
              base: str = PORTAL) -> dict:
    """Pergunta ao portal qual e a versao disponivel.

    Devolve sempre um dicionario com `estado` - nunca levanta excecao e NUNCA
    inclui o token no que devolve. Estado "ok" traz versao, sha256, novidades
    e a url assinada do pacote.
    """
    corpo = json.dumps({"gmail": gmail_do_aft, "token": token,
                        "versao_instalada": versao_instalada or ""}).encode("utf-8")
    req = urllib.request.Request(
        base.rstrip("/") + ROTA, data=corpo, method="POST",
        headers={"Content-Type": "application/json",
                 "User-Agent": "aft-toolkit/atualizar"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            dados = json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        # Mapa do contrato. O corpo, quando traz um `erro` conhecido, vence o
        # codigo - e ele que distingue os dois motivos possiveis de um 403.
        try:
            nome = _erro_do_corpo(e.read())
        except Exception:
            nome = None
        if nome in ("token_invalido", "sem_acesso"):
            return {"estado": nome}
        if e.code == 401:
            return {"estado": "token_invalido"}
        if e.code == 403:
            return {"estado": "sem_acesso"}
        return {"estado": "portal_indisponivel",
                "detalhe_tecnico": f"o portal respondeu {e.code}"}
    except urllib.error.URLError as e:
        # Sem rede, DNS fora, portal no chao, certificado recusado. O motivo
        # tecnico vai junto porque e ele que distingue "sua internet caiu" de
        # "o portal esta fora do ar" - mas nao substitui a frase em portugues.
        return {"estado": "portal_indisponivel",
                "detalhe_tecnico": str(getattr(e, "reason", e))}
    except (ValueError, OSError) as e:
        return {"estado": "portal_indisponivel",
                "detalhe_tecnico": f"resposta ilegível do portal ({e})"}

    if not isinstance(dados, dict) or not dados.get("versao") or not dados.get("sha256"):
        return {"estado": "portal_indisponivel",
                "detalhe_tecnico": "o portal respondeu sem versão ou sem soma "
                                   "de verificação"}
    return {"estado": "ok", "versao": str(dados["versao"]),
            "sha256": str(dados["sha256"]).strip().lower(),
            "novidades": dados.get("novidades") or "",
            "url": dados.get("url") or ""}


def verificar(versao_instalada: str | None, base: str = PORTAL,
              forcar: bool = False) -> dict:
    """A consulta completa: token, Gmail, registro do dia e portal.

    Sempre devolve `estado`. Com `forcar`, ignora o registro do dia - e o que o
    AFT usa quando soube por fora que saiu versao nova.
    """
    if not forcar:
        guardada = consulta_registrada(versao_instalada, base)
        if guardada:
            return {**guardada, "de_registro": True}

    token = ler_token()
    if not token:
        return {"estado": "sem_token"}
    endereco = gmail()
    if not endereco:
        return {"estado": "sem_gmail"}

    resposta = consultar(endereco, token, versao_instalada, base=base)
    if resposta["estado"] == "ok":
        registrar_consulta(resposta, versao_instalada, base)
    return resposta


def baixar(url: str, alvo: Path) -> None:
    """Traz o pacote para um arquivo local. A conferencia do sha256 e a
    descompactacao segura sao do atualizar_toolkit.py - aqui so se baixa."""
    req = urllib.request.Request(url, headers={"User-Agent": "aft-toolkit/atualizar"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r, open(alvo, "wb") as f:
        while True:
            bloco = r.read(1 << 20)
            if not bloco:
                break
            f.write(bloco)


# ------------------------------------------------- as falhas, em portugues

LINK = f"{PORTAL}/aft-toolkit"


def mensagem(estado: str, **dados) -> str:
    """A frase que o AFT le. Toda falha diz o que aconteceu E o proximo passo -
    ele nao e programador e nao tem por que deduzir nada. Sem jargao, sem nome
    de arquivo de codigo, e nunca o valor do token."""
    if estado == "sem_token":
        return (
            "Falta nesta máquina o código de acesso ao toolkit. Ele chega uma "
            "única vez, no e-mail de liberação do portal, e depois nunca mais "
            f"incomoda.\n\nPróximo passo: peça o acesso em {LINK} com a sua "
            "conta Google. Quando o código chegar, é só me passar que eu "
            "guardo — não precisa de conta no GitHub nem de senha nova.")
    if estado == "token_invalido":
        # A frase NOMEIA o e-mail consultado de proposito. O portal procura o
        # seu cadastro por ele: com o e-mail de outra pessoa na ficha, ele acha
        # o cadastro dela e compara o seu codigo com o dela - e recusa, sempre.
        # Em 30/08/2026 uma AFT herdou a ficha de um colega e ficou presa nisso
        # por horas, porque a mensagem so falava em "codigo antigo" e mandava
        # pedir outro: cada codigo novo falhava igual. Sem o e-mail na tela nao
        # ha como o AFT distinguir as duas causas - e elas pedem saidas opostas.
        quem = dados.get("gmail")
        return (
            "O portal não aceitou o código de acesso guardado nesta máquina"
            + (f", consultando com o e-mail {quem}" if quem else "")
            + ".\n\nSão duas causas possíveis, e a saída é diferente em cada uma:"
            "\n\n1. O e-mail acima não é o seu do portal. Acontece quando a "
            "ficha de configuração foi copiada de um colega. Aí o problema não "
            "é o código, e pedir um novo não resolve: me diga qual e-mail você "
            "usou no portal que eu corrijo a ficha."
            "\n\n2. O e-mail está certo, e então o código é antigo — foi "
            f"trocado ou cancelado. Peça um novo em {LINK} e me passe."
            "\n\nNada foi alterado na sua pasta.")
    if estado == "sem_acesso":
        quem = dados.get("gmail")
        return (
            "O portal reconheceu esta máquina, mas o e-mail do seu cadastro"
            + (f" ({quem})" if quem else "")
            + " ainda não está liberado para receber o toolkit.\n\n"
            f"Próximo passo: peça a liberação em {LINK}, com a mesma conta "
            "Google. Quem já usa os ementários do NotebookLM costuma ser "
            "liberado na hora.")
    if estado == "sem_gmail":
        return (
            "Não sei qual é o e-mail do seu cadastro no portal — é por ele que "
            "o portal reconhece você. Ele deveria estar na sua ficha de "
            "configuração (aft-config.md), na linha que começa com `gmail:`."
            "\n\nPróximo passo: me diga qual e-mail você usou no portal que eu "
            "escrevo na ficha e repito a consulta.")
    if estado == "sem_novidade":
        versao = dados.get("versao") or "a atual"
        return (
            f"Você já está com a versão mais recente do toolkit ({versao}). "
            "Não há nada para instalar.")
    if estado == "portal_indisponivel":
        motivo = dados.get("detalhe_tecnico")
        return (
            "Não consegui falar com o portal agora"
            + (f" ({motivo})" if motivo else "")
            + ". Pode ser a sua conexão ou o portal fora do ar por alguns "
            "minutos.\n\nPróximo passo: tente de novo mais tarde. Nada foi "
            "alterado na sua pasta, e o toolkit que você já tem continua "
            "funcionando normalmente.")
    # Qualquer outra coisa - inclusive defeito nosso. Nao se finge que foi a
    # rede: o AFT precisa saber que isto merece um relato ao mantenedor.
    motivo = dados.get("detalhe_tecnico")
    return (
        "Não consegui completar a consulta ao portal"
        + (f" ({motivo})" if motivo else "")
        + ".\n\nPróximo passo: tente de novo. Se acontecer outra vez, isto é "
        "defeito do toolkit e vale registrar com /aft-erro. Nada foi alterado "
        "na sua pasta.")
