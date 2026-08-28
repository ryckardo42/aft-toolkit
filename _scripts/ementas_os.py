#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ementas_os.py — o arquivo `ementas.md` de uma OS: ler, migrar e gravar.

POR QUE ESTE MÓDULO EXISTE
--------------------------
A lista de ementas da OS morava no `## Ementas da OS` do `memory.md`. Numa OS
real ela chegou a 23% do arquivo — e o `memory.md` é lido no início de TODA
conversa da auditoria (é o que o AGENTS.md da pasta manda fazer), de modo que a
lista era relida em toda sessão para servir em três momentos apenas:
preparação, enquadramento e encerramento.

Mas o motivo forte não é o tamanho: é a FUNÇÃO. O item 2.5 do Relatório de
Inspeção ("Ementas fiscalizadas", no SFIT-WEB) exige, de cada ementa, uma
**situação encontrada** e, quando irregular, as **ações aplicadas**. Isso é uma
folha de resposta, não um recorte da Ordem de Serviço. O `ementas.md` é essa
folha.

TRÊS SEÇÕES, PORQUE TRÊS MÃOS DIFERENTES PREENCHEM
--------------------------------------------------
1. **Ementas da OS** — as que vêm com `*` na tela. O AFT responde TODAS,
   inclusive as que não fiscalizou.
2. **Ementas trazidas por autuação** — o Sistema Auditor as transfere sozinho
   para o SFIT quando o auto é transmitido; chegam `Irregular` + `Autuação`, com
   a situação travada. Só entram aqui as que NÃO constavam da OS: a ementa da OS
   que também foi autuada tem a própria linha preenchida, na seção 1.
3. **Ementas incluídas pelo AFT** — fiscalizadas fora da OS e sem auto. São as
   únicas que o AFT digita no campo "Informe as ementas fiscalizadas que não
   constam na OS".

O FORMATO PRESERVA A LINHA ANTIGA, DE PROPÓSITO
------------------------------------------------
A primeira linha de cada ementa é idêntica à que estava no `memory.md`:

    - [x] 312377-4 — Deixar de adotar medidas de proteção... (NR-12)
          situação: Irregular
          ações: Autuação · Notificação
          lastro: AI 23.284.209-4 · tn-nco-2026-08-21.md

Assim o `preparacao_docx.py` e o `metas_regularizacao.py` continuam casando o
mesmo padrão — só mudam de arquivo. As sub-linhas indentadas são a resposta, e
só existem quando há resposta.

A CAIXA É DERIVADA, NUNCA DIGITADA
-----------------------------------
No `memory.md`, `[x]` significava "ementa tratada" — um sentido vago que já
produziu contradição em fiscalização real (ver conferir_rastreamento.py). Aqui
`[x]` quer dizer exatamente "linha respondida, tem situação", e é este módulo
que a recalcula ao gravar. Ninguém marca caixa à mão.

Uso:
    python ementas_os.py "<pasta da OS>"                # resumo do preenchimento
    python ementas_os.py "<pasta da OS>" --folha        # folha para digitar no SFIT
    python ementas_os.py "<pasta da OS>" --json         # dado bruto p/ outros scripts
    python ementas_os.py "<pasta da OS>" --migrar       # memory.md -> ementas.md
    python ementas_os.py "<pasta da OS>" --migrar --conferir   # só mostra o que faria

Exit 0 = ok; 1 = nada a fazer/lista vazia; 2 = erro de uso.
"""

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

import argparse
import json
import re
import shutil
import sys
import unicodedata
from datetime import datetime
from pathlib import Path

# O console do Windows abre em cp1252 e razao social tem acento: sem isto,
# "FUNDICAO" sai "FUNDI??O". errors=replace impede que um caractere fora do
# alcance derrube a leitura.
for _fluxo in ("stdout", "stderr"):
    try:
        getattr(sys, _fluxo).reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

ARQUIVO = "ementas.md"

# As tres secoes, na ordem em que sao gravadas. A chave e o identificador
# interno; o titulo e o que o AFT le.
SECOES = [
    ("os", "1. Ementas da OS",
     "as que vêm com `*` na tela do SFIT; responda todas, inclusive as não fiscalizadas"),
    ("autuacao", "2. Ementas trazidas por autuação",
     "autuadas FORA da lista da OS — o SFIT as acrescenta sozinho, já `Irregular` + "
     "`Autuação`; aqui só se confere se chegaram"),
    ("aft", "3. Ementas incluídas pelo AFT",
     "fiscalizadas fora da OS e sem auto — digitadas no campo "
     "\"Informe as ementas fiscalizadas que não constam na OS\""),
]
TITULO_SECAO = dict((k, t) for k, t, _ in SECOES)

# Os quatro valores do combo "Situação encontrada".
SITUACOES = ["Regular", "Irregular", "Não aplicável", "Não fiscalizada"]
# O SFIT exige comentario/justificativa nestas duas.
EXIGEM_COMENTARIO = ["Não aplicável", "Não fiscalizada"]

# As dez caixas de "Ações a serem aplicadas", na ordem da tela, mais "Autuação",
# que NAO e caixa: o proprio SFIT a preenche quando o auto e transmitido no
# Sistema Auditor. Fica na lista porque precisa ser representada na folha.
ACOES = [
    "Autuação",
    "Regularizada",
    "Termo de Compromisso",
    "Notificação",
    "Embargo",
    "Suspensão de Embargo",
    "Interdição",
    "Suspensão de Interdição",
    "Outros",
    "Manutenção de Embargo",
    "Manutenção de Interdição",
]
ACAO_DO_SISTEMA = "Autuação"

# "- [ ] 312309-0 — Deixar de adotar medidas (...). (NR-12)"
RE_LINHA = re.compile(
    r"^-\s*\[([ xX])\]\s*(\d{6}-\d)\s*[—–-]\s*(.+?)\s*\(([^()]+)\)\s*$")
# Sub-linha "      situação: Irregular"
RE_SUB = re.compile(r"^\s+([A-Za-zÀ-ÿ]+):\s*(.*)$")
RE_FM = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
# Codigo de ementa isolado. As bordas \b impedem casar o miolo do numero da OS
# (11929169-0) ou da demanda (3980890-4).
RE_COD = re.compile(r"\b(\d{6}-\d)\b")

SEPARADOR_ACOES = " · "
VAZIO = "_(vazio)_"


class ErroDeUso(Exception):
    """Pasta que nao e uma OS, arquivo que nao da para ler. Nao e defeito."""


def _sem_acento(texto):
    return "".join(c for c in unicodedata.normalize("NFD", texto)
                   if unicodedata.category(c) != "Mn").lower()


def _canonico(valor, universo):
    """Casa um valor digitado com a forma oficial, ignorando acento e caixa.

    O AFT (e o assistente) escreve "nao aplicavel", "NOTIFICACAO", "interdição".
    Tudo isso tem de virar o mesmo valor — senão a conferência acusa contradição
    onde só houve teclado sem acento.
    """
    alvo = _sem_acento(valor.strip())
    for oficial in universo:
        if _sem_acento(oficial) == alvo:
            return oficial
    return None


# --------------------------------------------------------------- modelo
class Ementa(object):
    def __init__(self, codigo, descricao, frente, secao="os"):
        self.codigo = codigo
        self.descricao = descricao
        self.frente = frente
        self.secao = secao
        self.situacao = ""
        self.acoes = []
        self.comentario = ""
        self.lastro = ""

    @property
    def respondida(self):
        return bool(self.situacao)

    def como_dict(self):
        return {"codigo": self.codigo, "descricao": self.descricao,
                "frente": self.frente, "secao": self.secao,
                "situacao": self.situacao, "acoes": list(self.acoes),
                "comentario": self.comentario, "lastro": self.lastro,
                "respondida": self.respondida}

    def linha(self):
        marca = "x" if self.respondida else " "
        return "- [%s] %s — %s (%s)" % (marca, self.codigo, self.descricao,
                                        self.frente)

    def sublinhas(self):
        saida = []
        if self.situacao:
            saida.append("      situação: %s" % self.situacao)
        if self.acoes:
            saida.append("      ações: %s" % SEPARADOR_ACOES.join(self.acoes))
        if self.comentario:
            saida.append("      comentário: %s" % self.comentario)
        if self.lastro:
            saida.append("      lastro: %s" % self.lastro)
        return saida


class Folha(object):
    """O `ementas.md` inteiro: front-matter + as ementas das três seções."""

    def __init__(self, pasta, empregador="", origem=""):
        self.pasta = Path(pasta)
        self.empregador = empregador
        self.origem = origem          # "ementas.md" ou "memory.md" (retrocompat.)
        self.os_sfit = ""
        self.dupla_visita = ""        # "sim" | "nao" | "" (desconhecido)
        self.ementas = []

    # -- consulta ------------------------------------------------------
    def por_codigo(self, codigo):
        for e in self.ementas:
            if e.codigo == codigo:
                return e
        return None

    def da_secao(self, chave):
        return [e for e in self.ementas if e.secao == chave]

    @property
    def caminho(self):
        return self.pasta / ARQUIVO

    # -- gravacao ------------------------------------------------------
    def texto(self):
        linhas = ["---"]
        linhas.append('os_sfit: "%s"' % self.os_sfit)
        linhas.append(("dupla_visita: %s" % (self.dupla_visita or "")).rstrip())
        linhas.append("atualizado: %s" % datetime.now().strftime("%d/%m/%Y"))
        linhas.append("---")
        linhas.append("# Ementas fiscalizadas — %s" % (self.empregador or self.pasta.name))
        linhas.append("")
        linhas.append("_Folha de resposta do item 2.5 do Relatório de Inspeção "
                      "(SFIT-WEB): de cada ementa, a **situação encontrada** e, quando "
                      "irregular, as **ações aplicadas**._")
        linhas.append("")
        linhas.append("_A caixa `[x]` é calculada: significa \"linha respondida\", "
                      "e o `ementas_os.py` a recalcula ao gravar — não marque à mão._")
        for chave, titulo, explicacao in SECOES:
            linhas.append("")
            linhas.append("## %s" % titulo)
            linhas.append("_(%s)_" % explicacao)
            itens = self.da_secao(chave)
            if not itens:
                linhas.append(VAZIO)
                continue
            for e in itens:
                linhas.append(e.linha())
                linhas.extend(e.sublinhas())
        linhas.append("")
        return "\n".join(linhas)

    def gravar(self):
        alvo = self.caminho
        if alvo.exists():
            _backup(alvo)
        alvo.write_text(self.texto(), encoding="utf-8")
        return alvo


def _backup(arquivo: Path):
    """Copia de seguranca em .backups/, mesma convencao do backup_arquivo.py."""
    destino_dir = arquivo.parent / ".backups"
    destino_dir.mkdir(exist_ok=True)
    carimbo = datetime.now().strftime("%Y%m%d-%H%M%S")
    destino = destino_dir / ("%s_%s%s" % (arquivo.stem, carimbo, arquivo.suffix))
    n = 1
    while destino.exists():
        destino = destino_dir / ("%s_%s_%d%s" % (arquivo.stem, carimbo, n,
                                                 arquivo.suffix))
        n += 1
    shutil.copy2(str(arquivo), str(destino))
    return destino


# --------------------------------------------------------------- leitura
def _campo_fm(fm, chave):
    # [ \t]* e nao \s*: \s atravessa a quebra de linha, e num campo vazio
    # ("dupla_visita:") o valor lido virava a linha SEGUINTE do front-matter.
    m = re.search(r"^%s:[ \t]*(.*)$" % re.escape(chave), fm, re.M)
    return m.group(1).strip().strip('"').strip("'") if m else ""


def _corta_fm(texto):
    m = RE_FM.match(texto)
    return (m.group(1), texto[m.end():]) if m else ("", texto)


def _secao_do_titulo(titulo):
    """Casa '## 2. Ementas trazidas por autuação' com a chave interna."""
    limpo = _sem_acento(titulo.lstrip("#").strip())
    limpo = re.sub(r"^\d+\.\s*", "", limpo)
    for chave, oficial, _ in SECOES:
        if limpo.startswith(_sem_acento(oficial.split(". ", 1)[-1])):
            return chave
    # "## Ementas da OS" — o titulo antigo, do memory.md.
    if limpo.startswith("ementas da os"):
        return "os"
    return None


def _ler_itens(corpo, secao_padrao="os"):
    """Extrai as ementas de um corpo markdown, respeitando os títulos de seção."""
    ementas = []
    secao_atual = None
    atual = None
    for linha in corpo.splitlines():
        if linha.startswith("## "):
            secao_atual = _secao_do_titulo(linha)
            atual = None
            continue
        if secao_atual is None:
            continue
        m = RE_LINHA.match(linha.strip())
        if m:
            atual = Ementa(m.group(2), m.group(3).strip(), m.group(4).strip(),
                           secao_atual or secao_padrao)
            ementas.append(atual)
            continue
        if atual is None or not linha.strip():
            continue
        ms = RE_SUB.match(linha)
        if not ms:
            continue
        chave, valor = _sem_acento(ms.group(1)), ms.group(2).strip()
        if not valor:
            continue
        if chave == "situacao":
            atual.situacao = _canonico(valor, SITUACOES) or valor
        elif chave in ("acoes", "acao"):
            for pedaco in re.split(r"[·;]", valor):
                pedaco = pedaco.strip()
                if not pedaco:
                    continue
                atual.acoes.append(_canonico(pedaco, ACOES) or pedaco)
        elif chave in ("comentario", "justificativa"):
            atual.comentario = valor
        elif chave == "lastro":
            atual.lastro = valor
    return ementas


def ler(pasta):
    """A folha de uma OS. Cai de volta no memory.md enquanto ela não existir.

    É este fallback que torna a migração reversível: script novo lê OS antiga
    sem nenhuma conversão prévia, e OS já migrada continua respondendo igual.
    """
    pasta = Path(pasta).expanduser()
    if not pasta.is_dir():
        raise ErroDeUso("não é uma pasta: %s" % pasta)

    memoria = pasta / "memory.md"
    empregador = ""
    if memoria.is_file():
        fm, _ = _corta_fm(memoria.read_text(encoding="utf-8", errors="replace"))
        empregador = _campo_fm(fm, "empregador")

    alvo = pasta / ARQUIVO
    if alvo.is_file():
        texto = alvo.read_text(encoding="utf-8", errors="replace")
        fm, corpo = _corta_fm(texto)
        folha = Folha(pasta, empregador or pasta.name, origem=ARQUIVO)
        folha.os_sfit = _campo_fm(fm, "os_sfit")
        folha.dupla_visita = _sem_acento(_campo_fm(fm, "dupla_visita"))
        folha.ementas = _ler_itens(corpo)
        return folha

    folha = Folha(pasta, empregador or pasta.name, origem="memory.md")
    if not memoria.is_file():
        raise ErroDeUso(
            "não achei %s nem memory.md em %s — esta pasta não é uma OS."
            % (ARQUIVO, pasta))
    texto = memoria.read_text(encoding="utf-8", errors="replace")
    _, corpo = _corta_fm(texto)
    folha.os_sfit = _os_do_memory(corpo)
    folha.ementas = _ler_itens(corpo)
    return folha


def _os_do_memory(corpo):
    """'**OS (SFIT):** 11929169-0 · **Demanda:** 3980890-4' -> o nº da OS."""
    m = re.search(r"^\*\*OS \(SFIT\):\*\*\s*(.+)$", corpo, re.M)
    return m.group(1).split("·")[0].strip() if m else ""


# ------------------------------------------------------------- migração
PONTEIRO = ("## Ementas da OS\n"
            "_(a lista e a folha de resposta do item 2.5 do Relatório de Inspeção "
            "moram em `ementas.md`, nesta mesma pasta)_\n\n")


def migrar(pasta, conferir=False):
    """Recorta a seção do memory.md e grava o ementas.md. Devolve o relatório."""
    pasta = Path(pasta).expanduser()
    memoria = pasta / "memory.md"
    if not memoria.is_file():
        raise ErroDeUso("não achei memory.md em %s — esta pasta não é uma OS." % pasta)
    if (pasta / ARQUIVO).is_file():
        return {"feito": False, "motivo": "%s já existe" % ARQUIVO,
                "ementas": 0, "descartadas": []}

    texto = memoria.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"^## Ementas da OS[ \t]*\n(.*?)(?=^## |\Z)", texto, re.S | re.M)
    if not m:
        return {"feito": False, "motivo": "memory.md não tem '## Ementas da OS'",
                "ementas": 0, "descartadas": []}

    fm, corpo = _corta_fm(texto)
    folha = Folha(pasta, _campo_fm(fm, "empregador") or pasta.name, origem=ARQUIVO)
    folha.os_sfit = _os_do_memory(corpo)
    folha.ementas = _ler_itens("## Ementas da OS\n" + m.group(1))
    if not folha.ementas:
        return {"feito": False, "motivo": "a seção existe mas está vazia",
                "ementas": 0, "descartadas": []}

    # A caixa mudou de sentido: no memory.md o [x] queria dizer "ementa tratada";
    # aqui quer dizer "linha respondida". Como nada foi respondido ainda, as
    # marcadas voltam a [ ] -- e cada uma e NOMEADA no relatorio, para o AFT ver
    # exatamente o que a migracao mexeu.
    descartadas = [e.codigo for e in folha.ementas if not e.respondida
                   and _tinha_marca(m.group(1), e.codigo)]

    if conferir:
        return {"feito": False, "motivo": "conferência (nada gravado)",
                "ementas": len(folha.ementas), "descartadas": descartadas}

    _backup(memoria)
    novo = texto[:m.start()] + PONTEIRO + texto[m.end():]
    memoria.write_text(novo, encoding="utf-8")
    folha.gravar()
    return {"feito": True, "motivo": "", "ementas": len(folha.ementas),
            "descartadas": descartadas}


def _tinha_marca(bloco, codigo):
    for linha in bloco.splitlines():
        m = RE_LINHA.match(linha.strip())
        if m and m.group(2) == codigo:
            return m.group(1).lower() == "x"
    return False


# ------------------------------------------------------------ relatórios
def _render_folha(folha):
    """A folha na ordem da tela do SFIT, para o AFT digitar conferindo."""
    saida = []
    saida.append("=" * 72)
    saida.append("  ITEM 2.5 — EMENTAS FISCALIZADAS — %s" % folha.empregador[:40])
    saida.append("=" * 72)
    if folha.os_sfit:
        saida.append("  OS SFIT nº %s" % folha.os_sfit)
    if folha.dupla_visita == "sim":
        saida.append("  DUPLA VISITA concedida — irregularidade se NOTIFICA, não se autua.")
    elif folha.dupla_visita == "nao":
        saida.append("  Sem dupla visita — irregularidade encontrada deve ser autuada.")
    for chave, titulo, _ in SECOES:
        itens = folha.da_secao(chave)
        if not itens:
            continue
        saida.append("")
        saida.append("-- %s " % titulo + "-" * max(0, 66 - len(titulo)))
        for e in itens:
            situacao = e.situacao or "(A RESPONDER)"
            saida.append("  %s  %-8s  %s" % (e.codigo, e.frente, situacao))
            if e.acoes:
                for acao in e.acoes:
                    sufixo = "   (o SFIT preenche)" if acao == ACAO_DO_SISTEMA else ""
                    saida.append("              - %s%s" % (acao, sufixo))
            if e.comentario:
                saida.append("              comentário: %s" % e.comentario)
    faltam = [e for e in folha.ementas if not e.respondida]
    saida.append("")
    saida.append("-" * 72)
    saida.append("%d ementa(s) na folha; %d ainda sem situação."
                 % (len(folha.ementas), len(faltam)))
    if folha.origem != ARQUIVO:
        saida.append("Fonte: memory.md (esta OS ainda não foi migrada — use --migrar).")
    return "\n".join(saida)


def _render_resumo(folha):
    saida = []
    saida.append("Folha de ementas — %s" % folha.empregador)
    saida.append("Fonte: %s" % folha.origem)
    for chave, titulo, _ in SECOES:
        itens = folha.da_secao(chave)
        respondidas = len([e for e in itens if e.respondida])
        saida.append("  %-34s %3d ementa(s), %d respondida(s)"
                     % (titulo, len(itens), respondidas))
    por_situacao = {}
    for e in folha.ementas:
        if e.situacao:
            por_situacao[e.situacao] = por_situacao.get(e.situacao, 0) + 1
    if por_situacao:
        saida.append("  Situações: " + ", ".join(
            "%s %d" % (s, por_situacao[s]) for s in SITUACOES if s in por_situacao))
    return "\n".join(saida)


def main():
    ap = argparse.ArgumentParser(
        description="Lê, migra e grava o ementas.md (folha do item 2.5 do RI).")
    ap.add_argument("pasta_os", help="pasta da OS (a que contém o memory.md)")
    ap.add_argument("--folha", action="store_true",
                    help="imprime a folha na ordem da tela do SFIT")
    ap.add_argument("--json", action="store_true", help="dado bruto")
    ap.add_argument("--migrar", action="store_true",
                    help="recorta '## Ementas da OS' do memory.md e cria o ementas.md")
    ap.add_argument("--conferir", action="store_true",
                    help="com --migrar: só mostra o que faria, sem gravar")
    args = ap.parse_args()

    try:
        if args.migrar:
            rel = migrar(args.pasta_os, conferir=args.conferir)
            if not rel["feito"]:
                print("Nada a migrar: %s" % rel["motivo"])
                if rel["ementas"]:
                    print("  (%d ementa(s) seriam movidas)" % rel["ementas"])
                return 1 if not rel["ementas"] else 0
            print("Migrado: %d ementa(s) do memory.md para %s"
                  % (rel["ementas"], ARQUIVO))
            print("  memory.md agora aponta para o arquivo novo (backup em .backups/)")
            if rel["descartadas"]:
                print("  ATENÇÃO: a caixa mudou de sentido ([x] agora é \"linha "
                      "respondida\"). Voltaram a [ ]: %s"
                      % ", ".join(rel["descartadas"]))
            return 0

        folha = ler(args.pasta_os)
    except ErroDeUso as e:
        print("ERRO: %s" % e, file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps({"empregador": folha.empregador, "origem": folha.origem,
                          "os_sfit": folha.os_sfit,
                          "dupla_visita": folha.dupla_visita,
                          "ementas": [e.como_dict() for e in folha.ementas]},
                         ensure_ascii=False, indent=2))
        return 0
    if not folha.ementas:
        print("Nenhuma ementa registrada nesta OS.")
        return 1
    print(_render_folha(folha) if args.folha else _render_resumo(folha))
    return 0


if __name__ == "__main__":
    sys.exit(main())
