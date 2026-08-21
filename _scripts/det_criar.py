#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
det_criar.py — redige RASCUNHO de notificação DET pela API oficial.

IRMÃO de escrita do det_baixar.py (que é leitura). Usa a MESMA via — o token
de sessão emprestado pela extensão ao servidor do painel — mas agora para
CRIAR uma notificação nova, em estado de rascunho, para um RI existente.

Fronteira dura, técnica (a própria API do DET a impõe) e inegociável:
  - POST /notificacoes           cria a casca (status EM_ELABORACAO)
  - PUT  /notificacoes/{uid}/rascunho   preenche o rascunho (RI, itens...)
  - PUT  /notificacoes/{uid}/lavratura  LAVRA — ato de autoridade, efeito legal
Este módulo faz APENAS as duas primeiras. A LAVRATURA nunca é chamada aqui:
é sempre um clique do AFT, no site, depois de revisar o rascunho. Regra de
ouro do perfil: o assistente redige a minuta, o AFT decide e transmite.

Estrutura confirmada no molde real (RMNHLB58LINBKP, 21/08/2026):
  - casca:  POST /notificacoes  {cpfAuditor, status:0 (EM_ELABORACAO),
            tipoGeracao:0, auditores:[{cpf,nome,cif}], rascunho:"<json>"}
  - item:   {ordem, descricao, tipo, tipoRetornoSolicitado, dataPrazoEntrega,
            status:0, preAssinalado:false, versao:1}
            tipo:   0 SOLICITACAO_DOCUMENTO · 1 CUMPRIMENTO_OBRIGACAO · 2 ORIENTACAO
            retorno:0 SEM_RETORNO · 1 DIGITAL · 2 IMPRESSO · 3 VISTORIA_IN_LOCO
  A descrição do item é o texto integral no formato "*Título* - norma:
  texto [ementa]" — o MESMO da TN-NCO do AFT, então entra literal.

`montar_payload` NÃO toca a rede: devolve o corpo pronto para o AFT conferir
(pré-visualização). `criar_rascunho` é o único que escreve, e só a casca + o
rascunho — nunca a lavratura.
"""
from __future__ import annotations

import base64
import datetime
import json
import re
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import det_baixar  # noqa: E402  (pesquisar_por_codigo, TokenExpirado, _requisicao)

DET_BASE = det_baixar.DET_BASE

TIPO_CUMPRIMENTO_OBRIGACAO = 1
RETORNO_DIGITAL = 1
STATUS_EM_ELABORACAO = 0
PRAZO_PADRAO_DIAS = 16

# Uma linha da TN-NCO: "*Título* - norma: texto [123456-7]"
RE_ITEM_TN = re.compile(
    r'^\*(?P<titulo>.+?)\*\s*-\s*(?P<resto>.+?)\s*\[(?P<ementa>\d{6}-\d)\]\.?\s*$')


def recuperar_crua(token: str, codigo: str) -> dict:
    """JSON completo de uma notificação (GET /notificacoes/{uid}), pelo código.
    Leitura pura — serviu de MOLDE para o formato do rascunho."""
    n = det_baixar.pesquisar_por_codigo(token, codigo)
    if not n:
        raise RuntimeError(f"notificação {codigo} não encontrada no DET")
    uid = n.get("uid")
    if not uid:
        raise RuntimeError(f"notificação {codigo} veio sem uid")
    return json.loads(det_baixar._requisicao(token, f"/notificacoes/{uid}").decode("utf-8"))


def listar_modelos(token: str, id_modelo=None, cif=None) -> list[dict]:
    """POST /modelos-notificacao com filtro (mesmo corpo do site) — devolve a
    lista de modelos. `id_modelo` é a Identificação que o AFT vê; `cif` filtra
    por auditor (modelo de equipe). Leitura pura."""
    filtro = {"isPesquisaPadrao": False,
              "idModelo": int(id_modelo) if id_modelo else None,
              "cifAuditor": str(cif) if cif else None,
              "tituloModelo": None, "tituloNotificacao": None, "autoria": "M"}
    r = json.loads(det_baixar._requisicao(
        token, "/modelos-notificacao", corpo=filtro, metodo="POST").decode("utf-8"))
    return r if isinstance(r, list) else (r.get("modelos") or [])


def recuperar_modelo(token: str, id_modelo, cif=None) -> dict:
    """Modelo de notificação do AFT pela Identificação (ex.: 521). Lista com
    filtro para achar o uid real e recupera o detalhe (GET /{uid}). Traz a
    introdução/observações e textos padrão que o AFT consagrou no DET.
    RuntimeError se a Identificação não bater com nenhum modelo."""
    modelos = listar_modelos(token, id_modelo=id_modelo, cif=cif)
    alvo = None
    for m in modelos:
        if str(m.get("idModelo") or m.get("identificacao") or "") == str(id_modelo):
            alvo = m
            break
    alvo = alvo or (modelos[0] if len(modelos) == 1 else None)
    if not alvo:
        raise RuntimeError(f"modelo de identificação {id_modelo} não encontrado "
                           f"({len(modelos)} modelos no filtro)")
    uid = alvo.get("uid")
    if not uid:
        return alvo
    return json.loads(det_baixar._requisicao(
        token, f"/modelos-notificacao/{uid}").decode("utf-8"))


def recuperar_detalhe_ri(token: str, ri: str) -> dict:
    """Detalhe da fiscalização (GET /fiscalizacoes/detalhe/{ri}) — é de onde o
    site tira o estabelecimento/endereço do RI."""
    ri = re.sub(r"\D", "", ri or "")
    return json.loads(det_baixar._requisicao(
        token, f"/fiscalizacoes/detalhe/{ri}").decode("utf-8"))


def _sem_uids(o):
    """Cópia recursiva sem chaves 'uid' — conteúdo reaproveitado de modelo ou
    detalhe não pode carregar identidade de outro registro."""
    if isinstance(o, dict):
        return {k: _sem_uids(v) for k, v in o.items() if k != "uid"}
    if isinstance(o, list):
        return [_sem_uids(x) for x in o]
    return o


def _cacar_enderecos(o, achados: list | None = None) -> list[dict]:
    """Caça recursiva por objetos com cara de endereço (logradouro/cep) na
    resposta do detalhe do RI — o nome exato da chave não está em contrato."""
    achados = achados if achados is not None else []
    if isinstance(o, dict):
        chaves = {k.lower() for k in o}
        if ("logradouro" in chaves or "cep" in chaves) and o not in achados:
            achados.append(o)
        else:
            for v in o.values():
                _cacar_enderecos(v, achados)
    elif isinstance(o, list):
        for v in o:
            _cacar_enderecos(v, achados)
    return achados


def _secao_do_modelo(modelo: dict, chave: str) -> list:
    """Uma lista de conteúdo do modelo (observacoes, textos padrão) sem os
    uids do modelo — vai ser gravada num registro novo."""
    v = modelo.get(chave)
    return _sem_uids(v) if isinstance(v, list) else []


def auditor_do_token(token: str) -> dict:
    """{cpf, nome, cif} do AFT lidos do próprio JWT (sit_username, name,
    sit_cif) — o site monta a casca com esses três campos."""
    p = token.split(".")[1]
    p += "=" * (-len(p) % 4)
    d = json.loads(base64.urlsafe_b64decode(p).decode("utf-8"))
    return {"cpf": d.get("sit_username") or d.get("unique_name") or "",
            "nome": d.get("name") or "", "cif": str(d.get("sit_cif") or "")}


def itens_da_tn_nco(texto: str) -> list[dict]:
    """Extrai os itens de uma TN-NCO (.md). Cada linha "*Título* - norma:
    texto [ementa]" vira um item. Devolve [{titulo, ementa, descricao}] na
    ordem do arquivo; `descricao` é a linha INTEIRA (texto do item no DET)."""
    itens = []
    for linha in texto.splitlines():
        linha = linha.strip()
        m = RE_ITEM_TN.match(linha)
        if m:
            # a descrição é a linha INTEIRA, com os *asteriscos* do título —
            # é o formato literal do item no DET (confirmado no molde real).
            itens.append({"titulo": m.group("titulo").strip(),
                          "ementa": m.group("ementa"),
                          "descricao": linha})
    return itens


def _prazo_iso(dias: int, hoje: datetime.date | None = None) -> str:
    hoje = hoje or datetime.date.today()
    return (hoje + datetime.timedelta(days=dias)).strftime("%Y-%m-%d")


def ids_do_memory(texto: str) -> tuple[str, str]:
    """(ri, cnpj) do front-matter do memory.md. Só dígitos."""
    fm = re.match(r"^---\s*\n(.*?)\n---", texto, re.DOTALL)
    corpo = fm.group(1) if fm else texto[:800]
    def campo(ch):
        m = re.search(rf'^{ch}\s*:\s*"?([^"\n]+)"?', corpo, re.MULTILINE)
        return re.sub(r"\D", "", m.group(1)) if m else ""
    return campo("ri"), (campo("cnpj") or campo("cpf") or campo("caepf"))


def enriquecer(payload: dict, token: str, ri: str,
               id_modelo=None, cif=None) -> dict:
    """Acrescenta ao payload o que o modelo 521 e o detalhe do RI trazem —
    introdução/observações (do modelo), textos padrão (do modelo), e o
    endereço/estabelecimento (do RI). Defensivo: o que não vier fica de fora,
    e o payload ganha `_enriquecimento` com a contagem do que entrou, para
    conferência. NÃO escreve nada."""
    relato = {"modelo": None, "observacoes": 0, "textos": 0, "enderecos": 0}
    if id_modelo:
        try:
            modelo = recuperar_modelo(token, id_modelo, cif=cif)
            obs = _secao_do_modelo(modelo, "observacoes")
            txt = _secao_do_modelo(modelo, "textosInformativosPadraoAtivos")
            if obs:
                payload["observacoes"] = obs
            if txt:
                payload["textosInformativosPadraoAtivos"] = txt
            if modelo.get("tipoAbrangencia") is not None:
                payload["tipoAbrangencia"] = modelo["tipoAbrangencia"]
            if modelo.get("titulo"):
                payload["titulo"] = modelo["titulo"]
            relato.update(modelo=bool(modelo), observacoes=len(obs), textos=len(txt))
        except Exception as e:
            relato["modelo_erro"] = str(e)[:150]
    try:
        detalhe = recuperar_detalhe_ri(token, ri)
        ends = _sem_uids(_cacar_enderecos(detalhe))
        # O site usa o endereço de fiscalização (tipo 2, com uf). O detalhe do
        # RI traz vários endereços; preferir tipo==2 e, entre eles, o que tem
        # uf preenchida — senão o endereço sai errado (tipo 0, uf vazia).
        ends.sort(key=lambda e: (e.get("tipo") != 2, not e.get("uf")))
        escolhido = ends[:1] if ends else []
        # o endereço do rascunho carrega uid "" (registro novo)
        for e in escolhido:
            e["uid"] = ""
        if escolhido:
            payload["enderecos"] = escolhido
        relato["enderecos"] = len(escolhido)
        relato["endereco_tipo"] = escolhido[0].get("tipo") if escolhido else None
        relato["endereco_uf"] = escolhido[0].get("uf") if escolhido else None
    except Exception as e:
        relato["ri_erro"] = str(e)[:150]
    payload["_enriquecimento"] = relato
    return payload


def preparar_de_os(pasta_os: Path, arquivo_tn: str, titulo: str,
                   prazo_dias: int, token: str, id_modelo=None, cif=None
                   ) -> tuple[dict, list[dict]]:
    """Lê a TN-NCO e o memory.md da OS e devolve (payload, itens) prontos —
    sem escrever nada. O endpoint usa isto para montar antes de criar."""
    alvo = (pasta_os / arquivo_tn)
    itens = itens_da_tn_nco(alvo.read_text(encoding="utf-8"))
    if not itens:
        raise RuntimeError(f"nenhum item reconhecido em {arquivo_tn} "
                           "(formato esperado: *Título* - norma: texto [ementa])")
    ri, cnpj = ids_do_memory((pasta_os / "memory.md").read_text(encoding="utf-8"))
    if not ri:
        raise RuntimeError("RI não encontrado no memory.md da OS")
    prazo = _prazo_iso(prazo_dias)
    payload = montar_payload(token, ri, cnpj, titulo, itens, prazo)
    enriquecer(payload, token, ri, id_modelo, cif)
    return payload, itens


def montar_payload(token: str, ri: str, cnpj: str, titulo: str,
                   itens: list[dict], prazo_iso: str,
                   tipo: int = TIPO_CUMPRIMENTO_OBRIGACAO,
                   retorno: int = RETORNO_DIGITAL) -> dict:
    """Corpo do rascunho, PRONTO para conferência — NÃO envia nada.
    Espelha o molde real: casca (auditor/status) + itens com o texto integral."""
    aud = auditor_do_token(token)
    ni = re.sub(r"\D", "", cnpj or "")
    itens_payload = []
    for i, it in enumerate(itens, 1):
        # TODOS os campos que o site põe num item — inclusive os companheiros de
        # data em null. Sem eles, a tela de EDIÇÃO (formulário reativo) tenta
        # criar controle para um campo ausente e quebra (isDatasPadraoValidas /
        # addControl → 'Cannot read properties of undefined'; a de visualização,
        # só leitura, não sofre). Constatado no console do DET em 21/08/2026.
        itens_payload.append({
            "ordem": i,
            "descricao": it["descricao"],
            "tipo": tipo,
            "tipoRetornoSolicitado": retorno,
            "tipoRetornoRealizado": None,
            "dataPrazoEntrega": prazo_iso,
            "dataPeriodoInicio": None,
            "dataPeriodoFim": None,
            "dataAntecipacao": None,
            "horaPrazoEntrega": None,
            "naoExigeDataInicialFinal": True,
            "mensagemInfo": None,
            "tiposArquivos": None,
            "preAssinalado": False,
            "status": 0,
            "versao": 1,
        })
    return {
        "cpfAuditor": aud["cpf"],
        "status": STATUS_EM_ELABORACAO,
        "tipoGeracao": 0,
        "tipoAbrangencia": 1,
        "tipoNi": 0 if len(ni) == 14 else 1,   # 0 = CNPJ, 1 = CPF (14 vs 11)
        "auditores": [aud],
        "ri": re.sub(r"\D", "", ri or ""),
        "ni": ni,
        "titulo": titulo,
        "dataPrazoEntregaPadrao": prazo_iso,
        "dataPeriodoInicioPadrao": None,
        "dataPeriodoFimPadrao": None,
        "horaPrazoEntregaPadrao": None,
        "estabelecimentos": [],
        "contatos": [],
        "entregas": [],
        "itens": itens_payload,
    }


def _put_rascunho(token: str, uid: str, corpo: dict) -> dict:
    corpo = {**corpo, "uid": uid}
    bruto = det_baixar._requisicao(
        token, f"/notificacoes/{uid}/rascunho", corpo=corpo, metodo="PUT")
    return json.loads(bruto.decode("utf-8")) if bruto else {}


def criar_rascunho(token: str, corpo: dict) -> dict:
    """ESCREVE: cria a casca (POST /notificacoes) e salva o rascunho
    (PUT /rascunho). NUNCA lavra. Devolve {uid, codigo?, url}. `corpo` é o que
    montar_payload devolveu (já conferido pelo AFT)."""
    corpo = {k: v for k, v in corpo.items() if k != "_enriquecimento"}
    casca = {"cpfAuditor": corpo["cpfAuditor"], "status": STATUS_EM_ELABORACAO,
             "tipoGeracao": 0, "auditores": corpo["auditores"]}
    casca["rascunho"] = json.dumps(casca, ensure_ascii=False)
    criada = json.loads(det_baixar._requisicao(
        token, "/notificacoes", corpo=casca, metodo="POST").decode("utf-8"))
    uid = criada.get("uid")
    if not uid:
        raise RuntimeError(f"casca criada sem uid: {str(criada)[:200]}")
    salvo = _put_rascunho(token, uid, corpo)
    return {"uid": uid, "codigo": (salvo or criada).get("codigo"),
            "url": "https://auditor-det.sit.trabalho.gov.br/notificacao/"
                   "auditor/criar-notificacao"}


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if len(sys.argv) == 3:  # descoberta do molde
        print(json.dumps(recuperar_crua(sys.argv[2], sys.argv[1]),
                         ensure_ascii=False, indent=2))
    else:
        print("uso: python det_criar.py <CODIGO> <token>  (leitura do molde)",
              file=sys.stderr)
        sys.exit(1)
