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

# Tipo do item (enum do front): 0 Solicitação de Documento · 1 Exigência do
# Cumprimento de Obrigação · 2 Orientação.
TIPO_SOLICITACAO_DOCUMENTO = 0
TIPO_CUMPRIMENTO_OBRIGACAO = 1
TIPO_ORIENTACAO = 2
# Retorno solicitado: 0 Sem Retorno · 1 Digital · 2 Impresso · 3 Vistoria in loco.
RETORNO_SEM = 0
RETORNO_DIGITAL = 1
RETORNO_IMPRESSO = 2
RETORNO_VISTORIA = 3
STATUS_EM_ELABORACAO = 0
PRAZO_PADRAO_DIAS = 16

# "Todos os tipos de arquivo" marcados — a string vem de config/det-opcoes.json
# (o site concatena os grupos e repete o .txt; reproduzir igual é o que faz a
# tela reconhecer a seleção ao reabrir o item).
def tipos_arquivo_todos() -> str:
    return opcoes()["tipos_de_arquivo"]["todos"]

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


def listar_modelos(token: str, id_modelo=None, cif=None, autoria="T") -> list[dict]:
    """POST /modelos-notificacao com filtro (mesmo corpo do site) — devolve a
    lista de modelos. `id_modelo` é a Identificação que o AFT vê; `cif` filtra
    por auditor (modelo de equipe). Leitura pura.

    `autoria` é o mesmo seletor dos três botões da tela de pesquisa:
      "M" somente meus modelos · "P" somente públicos · "T" todos os cadastrados.
    O padrão aqui é **"T"**, e isso é uma decisão, não um detalhe: o AFT usa
    modelo de COLEGA (identificação + CIF de outro auditor) como se fosse
    canônico da equipe. Até 22/08/2026 este código mandava "M" — copiado do
    filtro PADRÃO do site — e por isso só achava modelo do próprio auditor:
    modelo de colega voltava "não encontrado", sem explicação. Nem todo modelo
    compartilhado é "público": no teste, nem o do AFT nem o do colega apareciam
    em "P", e só "T" alcançava os dois."""
    filtro = {"isPesquisaPadrao": False,
              "idModelo": int(id_modelo) if id_modelo else None,
              "cifAuditor": str(cif) if cif else None,
              "tituloModelo": None, "tituloNotificacao": None,
              "autoria": autoria}
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


def itens_do_modelo(token: str, id_modelo, cif=None) -> list[dict]:
    """Os itens que um modelo do DET carrega — a lista padrão de documentos que
    o AFT (ou um colega) consagrou. Leitura pura.

    Ficam em `modelositem` (minúsculas, como todo o detalhe do modelo), e o
    texto vem SEM o formato canônico da TN-NCO: são frases inteiras, do jeito
    que o auditor as escreveu. Devolve o essencial de cada um, já com os nomes
    que o resto deste módulo usa."""
    modelo = recuperar_modelo(token, id_modelo, cif=cif)
    saida = []
    for it in (modelo.get("modelositem") or []):
        desc = (it.get("descricao") or "").strip()
        if not desc:
            continue
        saida.append({"descricao": desc,
                      "tipo": it.get("tipo"),
                      "retorno": it.get("tipoRetornoSolicitado"),
                      "tiposArquivos": it.get("tiposArquivos"),
                      "preAssinalado": it.get("preAssinalado"),
                      "grupo": it.get("nmgrupo") or it.get("grupo")})
    return saida


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


RE_CABECALHO = re.compile(r"^#{1,6}\s*(.+?)\s*$")


def _indice_secao(linhas: list[str], prefixo: str) -> int | None:
    """Índice do cabeçalho markdown cujo nome começa por `prefixo` (sem acento,
    minúsculas). None se o arquivo não tiver esse cabeçalho."""
    for i, ln in enumerate(linhas):
        m = RE_CABECALHO.match(ln.strip())
        if m and _sem_acento(m.group(1)).lower().startswith(prefixo):
            return i
    return None


def _fim_da_secao(linhas: list[str], inicio: int) -> int:
    """Onde termina a seção que começa em `inicio`: no próximo cabeçalho."""
    for i in range(inicio + 1, len(linhas)):
        if RE_CABECALHO.match(linhas[i].strip()):
            return i
    return len(linhas)


def itens_da_tn_nco(texto: str) -> list[dict]:
    """Extrai os itens de um .md de notificação (TN-NCO ou NAD).

    Dois formatos, e o explícito manda:

    1. **Seção `## Itens`** — cada parágrafo dela é um item, siga ou não o
       formato canônico. É o que permite gravar no arquivo os itens que vieram
       de um MODELO do DET, cujo texto é frase corrida ("Carta com nomes,
       telefones e e-mails dos prepostos..."), sem título nem ementa.
    2. **Sem essa seção** — vale a regra de sempre: cada linha no formato
       "*Título* - norma: texto [ementa]" é um item. É o que mantém válidos os
       arquivos gerados antes de 22/08/2026.

    Devolve [{titulo, ementa, descricao}] na ordem do arquivo; `descricao` é o
    texto INTEIRO do item, como vai para o DET."""
    _, corpo = separar_frontmatter(texto)
    linhas = corpo.splitlines()
    i = _indice_secao(linhas, "itens")
    if i is not None:
        trecho = linhas[i + 1:_fim_da_secao(linhas, i)]
        itens = []
        for p in _paragrafos(trecho):
            m = RE_ITEM_TN.match(p)
            itens.append({"titulo": m.group("titulo").strip() if m else None,
                          "ementa": m.group("ementa") if m else None,
                          "descricao": p})
        return itens
    itens = []
    for linha in linhas:
        linha = linha.strip()
        m = RE_ITEM_TN.match(linha)
        if m:
            # a descrição é a linha INTEIRA, com os *asteriscos* do título —
            # é o formato literal do item no DET (confirmado no molde real).
            itens.append({"titulo": m.group("titulo").strip(),
                          "ementa": m.group("ementa"),
                          "descricao": linha})
    return itens


# ── As opções do DET vêm de config/det-opcoes.json ───────────────────────────
# Fonte única: aquele arquivo espelha o formulário "Item Solicitado" do site,
# com as regras de dependência entre os campos (quais retornos cada tipo aceita,
# quando existe prazo, quando o item aceita arquivo). Elas NÃO estão duplicadas
# aqui — se estivessem, um dia divergiriam.
CONFIG_OPCOES = AQUI.parent / "config" / "det-opcoes.json"
_OPCOES: dict | None = None


def opcoes() -> dict:
    """Carrega (uma vez) a tabela de opções do DET. Preguiçoso de propósito: um
    arquivo faltando não pode derrubar o servidor do painel na importação."""
    global _OPCOES
    if _OPCOES is None:
        try:
            _OPCOES = json.loads(CONFIG_OPCOES.read_text(encoding="utf-8"))
        except (OSError, ValueError) as e:
            raise RuntimeError(
                f"não consegui ler as opções do DET em {CONFIG_OPCOES} ({e}). "
                "Rode /aft-atualizar para repor o arquivo.") from e
    return _OPCOES


def _palavras(secao: str) -> dict:
    """{'digital': 1, ...} — as palavras que o AFT escreve no front-matter."""
    return {p: int(cod)
            for cod, o in opcoes()[secao]["opcoes"].items()
            for p in o["palavras_no_frontmatter"]}


def rotulo(secao: str, codigo) -> str:
    o = opcoes()[secao]["opcoes"].get(str(codigo))
    return o["rotulo"] if o else f"desconhecido ({codigo!r})"


def retornos_permitidos(tipo: int) -> list[int]:
    """Os retornos que o site oferece para aquele tipo de item. Fora desta
    lista é combinação que a tela do DET jamais criaria."""
    o = opcoes()["tipo_do_item"]["opcoes"].get(str(tipo))
    return list(o["retornos_permitidos"]) if o else []


def retorno_padrao(tipo: int, preferido: int | None = None) -> int:
    """O retorno a usar para aquele tipo: o preferido, quando o tipo o aceita;
    senão o padrão do próprio tipo. É o que impede um item de Orientação de
    nascer com retorno digital só porque digital é o padrão da skill."""
    permitidos = retornos_permitidos(tipo)
    if preferido is not None and preferido in permitidos:
        return preferido
    o = opcoes()["tipo_do_item"]["opcoes"].get(str(tipo)) or {}
    return o.get("retorno_padrao", RETORNO_SEM)


def aceita_arquivo(retorno: int) -> bool:
    """Só a entrega digital recebe arquivo pelo DET."""
    regra = opcoes()["regras_do_formulario"]["tipos_de_arquivo"]
    return retorno in regra["habilitado_somente_quando_retorno_for"]


def exige_prazo(retorno: int) -> bool:
    regra = opcoes()["regras_do_formulario"]["prazo_de_entrega"]
    return retorno in regra["obrigatorio_quando_retorno_for"]


def _sem_acento(s: str) -> str:
    import unicodedata
    return "".join(c for c in unicodedata.normalize("NFD", s or "")
                   if unicodedata.category(c) != "Mn")


def _palavra(mapa: dict, valor) -> int | None:
    """'obrigacao'/'Obrigação'/1 → o enum do DET. None se não reconhecer."""
    if valor is None or valor == "":
        return None
    if isinstance(valor, int) or str(valor).strip().isdigit():
        n = int(valor)
        return n if n in mapa.values() else None
    chave = _sem_acento(str(valor)).strip().lower().replace(" ", "_").replace("-", "_")
    return mapa.get(chave)


def _verdadeiro(valor, padrao: bool = True) -> bool:
    if valor is None or valor == "":
        return padrao
    return _sem_acento(str(valor)).strip().lower() in ("sim", "true", "1", "s", "yes")


def separar_frontmatter(texto: str) -> tuple[str, str]:
    """(front-matter cru, corpo). Sem front-matter, devolve ('', texto).
    Precisa vir ANTES de qualquer leitura de conteúdo: sem isto, as linhas de
    configuração seriam lidas como parte da introdução."""
    m = re.match(r"^---[ \t]*\r?\n(.*?)\r?\n---[ \t]*\r?\n?", texto, re.DOTALL)
    return (m.group(1), texto[m.end():]) if m else ("", texto)


def parametros_do_md(texto: str) -> dict:
    """Lê o bloco `det:` do front-matter da TN-NCO e devolve os parâmetros do
    DET já traduzidos para os enums.

    O formato é o que a /aft-tn-nco grava — YAML simples de propósito, porque
    o toolkit não pode depender de PyYAML (nem todo Windows de AFT tem):

        ---
        det:
          titulo: Termo de Notificação
          prazo: 07/09/2026          # ou prazo_dias: 16
          tipo: obrigacao            # solicitacao | obrigacao | orientacao
          retorno: digital           # sem | digital | impresso | vistoria
          preassinalado: sim
          excecoes:
            - item: 7
              retorno: vistoria
        ---

    Devolve {} quando não há bloco `det:` — arquivo antigo continua valendo.
    """
    fm, _ = separar_frontmatter(texto)
    if not fm:
        return {}
    linhas = fm.splitlines()
    dentro, ind_det = False, 0
    simples: dict = {}
    excecoes: dict = {}
    atual: dict | None = None
    modo_excecoes = False
    for ln in linhas:
        if not ln.strip() or ln.strip().startswith("#"):
            continue
        recuo = len(ln) - len(ln.lstrip())
        chave_valor = re.match(r"^\s*-?\s*([A-Za-z_]+)\s*:\s*(.*?)\s*$", ln)
        if not dentro:
            if re.match(r"^\s*det\s*:\s*$", ln):
                dentro, ind_det = True, recuo
            continue
        if recuo <= ind_det and not re.match(r"^\s*det\s*:\s*$", ln):
            break  # saiu do bloco det:
        if not chave_valor:
            continue
        chave, valor = chave_valor.group(1).lower(), chave_valor.group(2)
        if chave == "excecoes":
            modo_excecoes = True
            continue
        if modo_excecoes:
            if ln.lstrip().startswith("-"):      # começa uma exceção nova
                atual = {}
                if chave == "item":
                    excecoes[int(re.sub(r"\D", "", valor) or 0)] = atual
                    continue
            if atual is None:
                continue
            if chave == "item":
                excecoes[int(re.sub(r"\D", "", valor) or 0)] = atual
            else:
                atual[chave] = valor
        else:
            simples[chave] = valor

    p: dict = {}
    if simples.get("titulo"):
        p["titulo"] = simples["titulo"]
    if simples.get("prazo"):
        p["prazo"] = simples["prazo"]
    if simples.get("prazo_dias"):
        p["prazo_dias"] = int(re.sub(r"\D", "", simples["prazo_dias"]) or 0)
    t = _palavra(_palavras("tipo_do_item"), simples.get("tipo"))
    if t is not None:
        p["tipo"] = t
    r = _palavra(_palavras("retorno_solicitado"), simples.get("retorno"))
    if r is not None:
        p["retorno"] = r
    if "preassinalado" in simples:
        p["preassinalado"] = _verdadeiro(simples["preassinalado"])
    if simples.get("arquivos"):
        p["arquivos"] = simples["arquivos"]
    # o modelo do DET que originou a notificação (identificação e, se for de
    # colega, a CIF dele) — fica no arquivo para a criação não depender da
    # conversa nem do aft-config.md de quem rodar
    if simples.get("modelo"):
        p["modelo"] = re.sub(r"\D", "", simples["modelo"]) or None
    if simples.get("cif"):
        p["cif"] = re.sub(r"\D", "", simples["cif"]) or None
    if excecoes:
        limpas = {}
        for ordem, campos in excecoes.items():
            e = {}
            t = _palavra(_palavras("tipo_do_item"), campos.get("tipo"))
            r = _palavra(_palavras("retorno_solicitado"), campos.get("retorno"))
            if t is not None:
                e["tipo"] = t
            if r is not None:
                e["retorno"] = r
            if campos.get("prazo"):
                e["prazo"] = campos["prazo"]
            if e and ordem:
                limpas[ordem] = e
        if limpas:
            p["excecoes"] = limpas
    return p


def secoes_da_tn_nco(texto: str) -> dict:
    """Introdução e observações de uma TN-NCO (.md).

    No DET NÃO existe campo "introdução": os dois blocos da tela moram na MESMA
    lista `observacoes`, separados pelo `tipoTexto` (0 = introdução, antes dos
    itens; 1 = observações, depois deles). Confirmado no molde real em
    22/08/2026 — uma notificação lavrada trouxe 2 entradas tipoTexto 0 e 6
    tipoTexto 1, e o campo `introducao` do topo veio nulo.

    O .md da /aft-tn-nco já carrega essa estrutura sem precisar de rótulo:
      - tudo que vem ANTES do primeiro item é a introdução;
      - depois do último item, cada bloco "Rótulo:" seguido de linhas ">" é
        uma observação (o Rótulo vira `titulo`, o texto vira `descricao`).
    Cabeçalhos explícitos (`## Introdução` / `## Observações`), quando o arquivo
    os tiver, mandam mais que a posição — é o que torna o formato à prova de
    edição do AFT sem quebrar os arquivos antigos, que não os têm.

    Devolve {"introducao": [str, ...], "observacoes": [{titulo, descricao}]}.
    """
    _, corpo = separar_frontmatter(texto)   # a configuração não é introdução
    linhas = corpo.splitlines()
    # Com a seção "## Itens" explícita, ela é a fronteira: o que vem antes é
    # introdução, o que vem depois é observação. É o mesmo recorte de sempre,
    # só que declarado em vez de deduzido.
    i = _indice_secao(linhas, "itens")
    if i is not None:
        antes, depois = linhas[:i], linhas[_fim_da_secao(linhas, i):]
        for j, ln in enumerate(depois):
            m = RE_CABECALHO.match(ln.strip())
            if m and _sem_acento(m.group(1)).lower().startswith("observa"):
                depois = depois[j + 1:]
                break
        return {"introducao": [p for p in _paragrafos(antes) if p],
                "observacoes": _blocos_rotulados(depois)}
    idx_itens = [i for i, ln in enumerate(linhas) if RE_ITEM_TN.match(ln.strip())]
    if not idx_itens:
        return {"introducao": [], "observacoes": []}

    def _cabecalho(ln: str) -> str | None:
        m = re.match(r"^#{1,6}\s*(.+?)\s*$", ln.strip())
        return m.group(1).lower() if m else None

    inicio, fim = idx_itens[0], idx_itens[-1]
    antes, depois = linhas[:inicio], linhas[fim + 1:]
    # Cabeçalho explícito recorta melhor que a posição, quando existe.
    for i, ln in enumerate(antes):
        c = _cabecalho(ln)
        if c and c.startswith("introdu"):
            antes = antes[i + 1:]
    for i, ln in enumerate(depois):
        c = _cabecalho(ln)
        if c and c.startswith("observa"):
            depois = depois[i + 1:]
            break

    introducao = [p for p in _paragrafos(antes) if p]
    return {"introducao": introducao, "observacoes": _blocos_rotulados(depois)}


def _paragrafos(linhas: list[str]) -> list[str]:
    """Linhas em parágrafos (separados por linha em branco), sem cabeçalhos
    markdown e sem o "> " de citação."""
    paras, atual = [], []
    for ln in linhas:
        crua = ln.strip()
        if crua.startswith("#"):
            continue
        crua = re.sub(r"^>\s?", "", crua)
        if crua:
            atual.append(crua)
        elif atual:
            paras.append(" ".join(atual))
            atual = []
    if atual:
        paras.append(" ".join(atual))
    return paras


def _blocos_rotulados(linhas: list[str]) -> list[dict]:
    """Blocos "Rótulo:" + linhas ">" viram [{titulo, descricao}]. Texto solto
    sem rótulo vira uma entrada de titulo None — nada se perde."""
    blocos, titulo, corpo = [], None, []

    def fechar():
        nonlocal titulo, corpo
        if corpo:
            blocos.append({"titulo": titulo,
                           "descricao": " ".join(corpo).strip()})
        titulo, corpo = None, []

    for ln in linhas:
        crua = ln.strip()
        if not crua or crua.startswith("#"):
            continue
        if crua.startswith(">"):
            corpo.append(re.sub(r"^>\s?", "", crua))
            continue
        # linha comum: rótulo do bloco seguinte (termina em ":") ou texto solto
        if crua.endswith(":") and len(crua) <= 120:
            fechar()
            titulo = crua[:-1].strip()
        else:
            corpo.append(crua)
    fechar()
    return blocos


def _observacoes_payload(introducao: list[str],
                         observacoes: list[dict]) -> list[dict]:
    """Monta a lista `observacoes` do DET a partir do que veio do .md.
    `ordem` é uma sequência única sobre os dois grupos (é assim no molde), e
    cada entrada leva o `textoInformativoPadrao` vazio que o site sempre põe —
    a lição dos itens vale aqui: campo ausente quebra o formulário reativo."""
    def stub():
        return {"tipoTexto": 0, "ordem": 0, "titulo": None, "descricao": "",
                "editavel": False, "dataDesativacao": None, "uid": ""}

    saida, ordem = [], 0
    for txt in introducao:
        ordem += 1
        saida.append({"ordem": ordem, "titulo": None, "descricao": txt,
                      "tipoTexto": 0, "uid": "", "textoInformativoPadrao": stub()})
    for ob in observacoes:
        ordem += 1
        saida.append({"ordem": ordem, "titulo": ob.get("titulo") or None,
                      "descricao": ob.get("descricao") or "",
                      "tipoTexto": 1, "uid": "", "textoInformativoPadrao": stub()})
    return saida


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
               id_modelo=None, cif=None, manter_titulo: bool = False) -> dict:
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
            # o .md manda: só uso o modelo se o arquivo não trouxe nada
            if obs and not payload.get("observacoes"):
                payload["observacoes"] = obs
            if txt:
                payload["textosInformativosPadraoAtivos"] = txt
            if modelo.get("tipoAbrangencia") is not None:
                payload["tipoAbrangencia"] = modelo["tipoAbrangencia"]
            # ATENÇÃO ao nome do campo: o DETALHE do modelo devolve as chaves em
            # MINÚSCULAS e com outro nome — `titulonotificacao`, `titulomodelo`,
            # `modelositem` —, diferente do JSON de uma notificação (`titulo`,
            # `itens`). Procurar `titulo` aqui nunca achava nada, e a notificação
            # saía com o título genérico do toolkit em vez do título do modelo
            # (numa NAD, "Notificação para Apresentação de Documentos").
            titulo_do_modelo = modelo.get("titulonotificacao") or modelo.get("titulo")
            if titulo_do_modelo and not manter_titulo:
                payload["titulo"] = titulo_do_modelo
            relato["titulo_do_modelo"] = titulo_do_modelo
            relato["itens_no_modelo"] = len(modelo.get("modelositem") or [])
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


def _prazo_para_iso(prazo) -> str | None:
    """Aceita 'aaaa-mm-dd' ou 'dd/mm/aaaa' e devolve ISO; None se vazio."""
    if not prazo:
        return None
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", str(prazo))
    if m:
        return m.group(0)
    m = re.match(r"(\d{2})/(\d{2})/(\d{4})", str(prazo))
    return f"{m.group(3)}-{m.group(2)}-{m.group(1)}" if m else None


def preparar_de_os(pasta_os: Path, arquivo_tn: str, titulo=None,
                   prazo_dias=None, token: str = "", id_modelo=None, cif=None,
                   prazo=None, tipo=None, retorno=None, preassinalado=None,
                   overrides=None) -> tuple[dict, list[dict]]:
    """Lê a TN-NCO e o memory.md da OS e devolve (payload, itens) prontos —
    sem escrever nada.

    Precedência de CADA parâmetro, do mais forte para o mais fraco:
      1. o que a chamada mandou (o AFT decidiu agora, na conversa);
      2. o bloco `det:` do front-matter do .md (o que ele decidiu ao redigir);
      3. o padrão do toolkit (obrigação · digital · 16 dias · pré-assinalado).
    É essa ordem que faz o arquivo ser a memória da notificação sem tirar do
    AFT a palavra final. `overrides` = {ordem: {tipo?, retorno?, prazo?}}.
    """
    alvo = (pasta_os / arquivo_tn)
    bruto = alvo.read_text(encoding="utf-8")
    itens = itens_da_tn_nco(bruto)
    if not itens:
        raise RuntimeError(
            f"nenhum item reconhecido em {arquivo_tn} — esperado uma seção "
            "'## Itens' (um parágrafo por item) ou linhas no formato "
            "'*Título* - norma: texto [ementa]'")
    ri, cnpj = ids_do_memory((pasta_os / "memory.md").read_text(encoding="utf-8"))
    if not ri:
        raise RuntimeError("RI não encontrado no memory.md da OS")

    do_md = parametros_do_md(bruto)
    def escolher(da_chamada, chave, padrao):
        if da_chamada is not None:
            return da_chamada
        return do_md.get(chave, padrao)

    titulo = escolher(titulo, "titulo", "Termo de Notificação")
    id_modelo = escolher(id_modelo, "modelo", None)
    cif = escolher(cif, "cif", None)
    tipo = escolher(tipo, "tipo", TIPO_CUMPRIMENTO_OBRIGACAO)
    retorno = escolher(retorno, "retorno", RETORNO_DIGITAL)
    preassinalado = escolher(preassinalado, "preassinalado", True)
    prazo_iso = (_prazo_para_iso(prazo)
                 or _prazo_para_iso(do_md.get("prazo"))
                 or _prazo_iso(prazo_dias or do_md.get("prazo_dias")
                               or PRAZO_PADRAO_DIAS))
    # exceções por item: as do arquivo valem, e as da chamada mandam mais
    combinadas = {k: dict(v) for k, v in (do_md.get("excecoes") or {}).items()}
    for ordem, campos in (overrides or {}).items():
        combinadas.setdefault(ordem, {}).update(campos)

    payload = montar_payload(token, ri, cnpj, titulo, itens, prazo_iso,
                             tipo=tipo, retorno=retorno,
                             preassinalado=preassinalado, overrides=combinadas)
    # Introdução e observações saem do PRÓPRIO .md — é o texto que o AFT
    # revisou. O modelo do DET só entra se o arquivo não trouxer nada
    # (ver `enriquecer`, que não sobrescreve o que já veio daqui).
    secoes = secoes_da_tn_nco(bruto)
    obs = _observacoes_payload(secoes["introducao"], secoes["observacoes"])
    if obs:
        payload["observacoes"] = obs
    enriquecer(payload, token, ri, id_modelo, cif,
               manter_titulo=bool(do_md.get("titulo")))
    payload["_enriquecimento"]["observacoes_do_md"] = len(obs)
    payload["_enriquecimento"]["parametros_do_md"] = do_md or None
    payload["_parametros"] = {"titulo": titulo, "prazo": prazo_iso,
                              "tipo": tipo, "retorno": retorno,
                              "preassinalado": preassinalado,
                              "excecoes": combinadas or None}
    return payload, itens


def montar_payload(token: str, ri: str, cnpj: str, titulo: str,
                   itens: list[dict], prazo_iso: str,
                   tipo: int = TIPO_CUMPRIMENTO_OBRIGACAO,
                   retorno: int = RETORNO_DIGITAL,
                   preassinalado: bool = True,
                   tipos_arquivo: str | None = None,
                   overrides: dict | None = None) -> dict:
    """Corpo do rascunho, PRONTO para conferência — NÃO envia nada.
    Espelha o molde real: casca (auditor/status) + itens com o texto integral.

    `tipo`/`retorno` são o padrão de todos os itens; `preassinalado` idem
    (padrão da skill = marcado); `tipos_arquivo` é a string de extensões (padrão
    = todas). `overrides` mapeia ordem (1-based) → {tipo?, retorno?} para itens
    específicos — usado, p.ex., para o último item ser Orientação/Sem Retorno e
    o penúltimo pedir Vistoria in loco."""
    aud = auditor_do_token(token)
    ni = re.sub(r"\D", "", cnpj or "")
    overrides = overrides or {}
    itens_payload = []
    for i, it in enumerate(itens, 1):
        ov = overrides.get(i, {})
        t = ov.get("tipo", tipo)
        # O retorno tem de ser um dos que o SITE oferece para aquele tipo:
        # Solicitação de Documento só aceita Digital/Impresso, e Orientação só
        # aceita Sem Retorno. Pedir digital num item de Orientação criaria algo
        # que a tela do DET jamais permitiria montar à mão.
        r = retorno_padrao(t, ov.get("retorno", retorno))
        # o item pode ter prazo próprio (o DET aceita): correção de máquina
        # pede mais dias que fornecer água potável
        prazo_do_item = _prazo_para_iso(ov.get("prazo")) or prazo_iso
        if not exige_prazo(r):
            prazo_do_item = None   # Sem Retorno não tem prazo: o site o apaga
        # TODOS os campos que o site põe num item — inclusive os companheiros de
        # data em null. Sem eles, a tela de EDIÇÃO (formulário reativo) tenta
        # criar controle para um campo ausente e quebra (isDatasPadraoValidas /
        # addControl → 'Cannot read properties of undefined'; a de visualização,
        # só leitura, não sofre). Constatado no console do DET em 21/08/2026.
        itens_payload.append({
            "ordem": i,
            "descricao": it["descricao"],
            "tipo": t,
            "tipoRetornoSolicitado": r,
            "tipoRetornoRealizado": None,
            "dataPrazoEntrega": prazo_do_item,
            "dataPeriodoInicio": None,
            "dataPeriodoFim": None,
            "dataAntecipacao": None,
            "horaPrazoEntrega": None,
            "naoExigeDataInicialFinal": True,
            "mensagemInfo": None,
            # SÓ a entrega digital recebe arquivo pelo DET. Em Impresso,
            # Vistoria ou Sem Retorno o site apaga a seleção — mandar extensões
            # ali seria gravar o que a tela não mostraria.
            "tiposArquivos": ((tipos_arquivo or tipos_arquivo_todos())
                              if aceita_arquivo(r) else None),
            "preAssinalado": preassinalado,
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


LIMITE_CAMPO = 1000   # teto de caracteres de todo campo de texto do DET


def revisar_payload(payload: dict) -> list[dict]:
    """Confere o rascunho ANTES de escrever no DET e devolve a lista de
    problemas: [{gravidade, onde, problema}].

    `gravidade` "impede" barra a escrita (é o que garante que só vá ao DET
    dado completo); "aviso" é para o AFT decidir. Isto vive no CÓDIGO, e não
    só no subagente revisor, por um motivo simples: subagente pode ser pulado,
    esquecido ou contornado — esta função não, porque `criar_rascunho` a chama
    sozinha. O revisor cuida do que exige julgamento; aqui ficam as regras
    mecânicas, que não admitem opinião."""
    p, achados = [], []

    def anota(gravidade, onde, problema):
        achados.append({"gravidade": gravidade, "onde": onde, "problema": problema})

    ri = re.sub(r"\D", "", payload.get("ri") or "")
    ni = re.sub(r"\D", "", payload.get("ni") or "")
    if not ri:
        anota("impede", "notificação", "sem RI — o DET não sabe a que fiscalização anexar")
    if len(ni) not in (11, 14):
        anota("impede", "notificação",
              f"CNPJ/CPF do empregador inválido ({len(ni)} dígitos; esperado 14 ou 11)")
    if not (payload.get("titulo") or "").strip():
        anota("impede", "notificação", "sem título")

    itens = payload.get("itens") or []
    if not itens:
        anota("impede", "itens", "notificação sem nenhum item")
    hoje = datetime.date.today()
    for it in itens:
        onde = f"item {it.get('ordem')}"
        desc = (it.get("descricao") or "").strip()
        if not desc:
            anota("impede", onde, "sem texto")
        elif len(desc) > LIMITE_CAMPO:
            anota("impede", onde,
                  f"{len(desc)} caracteres — o DET recusa acima de {LIMITE_CAMPO}")
        if it.get("tipo") not in (TIPO_SOLICITACAO_DOCUMENTO,
                                  TIPO_CUMPRIMENTO_OBRIGACAO, TIPO_ORIENTACAO):
            anota("impede", onde, f"tipo inválido ({it.get('tipo')!r})")
        r = it.get("tipoRetornoSolicitado")
        if r not in (RETORNO_SEM, RETORNO_DIGITAL, RETORNO_IMPRESSO, RETORNO_VISTORIA):
            anota("impede", onde, f"tipo de retorno inválido ({r!r})")
        elif r not in retornos_permitidos(it.get("tipo")):
            permitidos = ", ".join(rotulo("retorno_solicitado", x)
                                   for x in retornos_permitidos(it.get("tipo")))
            anota("impede", onde,
                  f"combinação impossível no DET: item do tipo "
                  f"'{rotulo('tipo_do_item', it.get('tipo'))}' não aceita retorno "
                  f"'{rotulo('retorno_solicitado', r)}' (aceita: {permitidos})")
        prazo = it.get("dataPrazoEntrega")
        if not prazo:
            if exige_prazo(r):
                anota("impede", onde, "sem prazo de entrega")
        else:
            try:
                d = datetime.date.fromisoformat(str(prazo)[:10])
                if d < hoje:
                    anota("impede", onde, f"prazo no passado ({d.strftime('%d/%m/%Y')})")
                elif d == hoje:
                    anota("aviso", onde, "prazo é hoje")
            except ValueError:
                anota("impede", onde, f"prazo em formato inválido ({prazo!r})")
        # tipos de arquivo: o site só os habilita na entrega DIGITAL
        if it.get("tiposArquivos") and not aceita_arquivo(r):
            anota("impede", onde,
                  f"aceita tipos de arquivo, mas o retorno é "
                  f"'{rotulo('retorno_solicitado', r)}' — só a entrega Digital "
                  "recebe arquivo pelo DET")
        if aceita_arquivo(r) and not it.get("tiposArquivos"):
            anota("impede", onde,
                  "entrega digital sem nenhum tipo de arquivo aceito — a empresa "
                  "não teria como anexar")
        # (não se confere aqui o FORMATO do texto do item: um item vindo de
        # modelo do DET é frase corrida, sem título nem ementa, e é legítimo.
        # Julgar a redação é trabalho do subagente revisor, que lê o .md.)

    obs = payload.get("observacoes") or []
    intro = [o for o in obs if o.get("tipoTexto") == 0]
    resto = [o for o in obs if o.get("tipoTexto") == 1]
    if not intro:
        anota("impede", "introdução",
              "a notificação iria sem introdução — nem do .md nem do modelo")
    if not resto:
        anota("aviso", "observações", "a notificação vai sem observações")
    for o in obs:
        if len(o.get("descricao") or "") > LIMITE_CAMPO:
            anota("impede",
                  f"{'introdução' if o.get('tipoTexto') == 0 else 'observação'} "
                  f"{o.get('ordem')}",
                  f"{len(o['descricao'])} caracteres — acima de {LIMITE_CAMPO}")

    ends = payload.get("enderecos") or []
    if not ends:
        anota("aviso", "endereço", "notificação sem endereço do estabelecimento")
    elif not (ends[0].get("uf") or "").strip():
        anota("aviso", "endereço", "endereço veio sem UF")
    return achados


def _impedimentos(achados: list[dict]) -> list[dict]:
    return [a for a in achados if a["gravidade"] == "impede"]


# Linhas em branco que o DET acrescenta ao PDF de um rascunho, para o AFT
# preencher itens à mão no local. É o padrão do próprio site (0 a 100).
LINHAS_PDF_RASCUNHO = 5


def baixar_pdf_rascunho(token: str, uid: str, codigo: str, pasta_os: Path,
                        linhas: int = LINHAS_PDF_RASCUNHO) -> Path:
    """Baixa o PDF de uma notificação EM ELABORAÇÃO e grava no pacote da OS.

    É o "Gerar PDF da Notificação para download" do site:
    GET /notificacoes/{uid}/pdf?numeroDeLinhas=N. No rascunho o site pergunta o
    N (padrão 5) — são linhas em branco para o AFT completar itens à mão na
    empresa; na notificação já lavrada ele manda 0 sem perguntar.

    O arquivo sai como `notificacao-<CODIGO>-rascunho.pdf`, e o sufixo NÃO é
    enfeite: o `det_baixar` grava a versão lavrada como
    `notificacao-<CODIGO>.pdf` e PULA o download quando o arquivo já existe.
    Mesmo nome faria o rascunho ocupar o lugar do documento definitivo, para
    sempre e em silêncio."""
    linhas = max(0, min(int(linhas), 100))
    # rascunho recém-criado pode voltar sem código; o uid sempre existe e serve
    # de nome, para o arquivo nunca virar "notificacao-None-rascunho.pdf"
    codigo = (codigo or uid or "").strip() or uid
    destino = det_baixar.pasta_do_pacote(pasta_os, codigo) / \
        f"notificacao-{codigo}-rascunho.pdf"
    destino.parent.mkdir(parents=True, exist_ok=True)
    bruto = det_baixar._requisicao(token, f"/notificacoes/{uid}/pdf",
                                   params={"numeroDeLinhas": linhas},
                                   timeout=det_baixar.TIMEOUT_BLOB)
    if not bruto:
        raise RuntimeError("o DET devolveu um PDF vazio")
    destino.write_bytes(bruto)
    return destino


def _put_rascunho(token: str, uid: str, corpo: dict) -> dict:
    corpo = {**corpo, "uid": uid}
    bruto = det_baixar._requisicao(
        token, f"/notificacoes/{uid}/rascunho", corpo=corpo, metodo="PUT")
    return json.loads(bruto.decode("utf-8")) if bruto else {}


def criar_rascunho(token: str, corpo: dict) -> dict:
    """ESCREVE: cria a casca (POST /notificacoes) e salva o rascunho
    (PUT /rascunho). NUNCA lavra. Devolve {uid, codigo?, url}. `corpo` é o que
    montar_payload devolveu (já conferido pelo AFT)."""
    barreiras = _impedimentos(revisar_payload(corpo))
    if barreiras:
        detalhe = "; ".join(f"{b['onde']}: {b['problema']}" for b in barreiras)
        raise RuntimeError("rascunho incompleto, nada foi enviado ao DET — " + detalhe)
    corpo = {k: v for k, v in corpo.items()
             if k not in ("_enriquecimento", "_parametros")}
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
