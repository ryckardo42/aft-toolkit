#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ementas_situacao.py — propõe o preenchimento da folha do item 2.5 (`ementas.md`).

O PRINCÍPIO: O SCRIPT DERIVA, O AFT DECIDE
-------------------------------------------
A situação de cada ementa não é informação nova — na maior parte ela já está
escrita em outro lugar da pasta da OS. Se o AFT tivesse de repetir isso à mão no
`ementas.md`, o toolkit ganharia um QUINTO lugar onde o mesmo fato pode
divergir. Então este script vai buscar nas fontes que já existem:

  autos-lavrados.md (snapshot do Sistema Auditor)  -> Irregular + Autuação
  interdicao-embargo/*.md (RT e termos)            -> Irregular + Interdição/Embargo
  tn-nco-*.md (notificações para correção)         -> Irregular + Notificação

E NÃO deriva o que é juízo do Auditor-Fiscal: `Regular`, `Não aplicável`,
`Não fiscalizada`, `Regularizada` e `Termo de Compromisso` só entram quando o
AFT os marca. O script nunca decide se a empresa está regular.

Toda linha derivada carrega o **lastro** (nº do AI, arquivo do RT, arquivo da
notificação) — sem isso a conferência posterior seria impossível.

NUNCA SOBRESCREVE O QUE O AFT ESCREVEU
---------------------------------------
Situação já preenchida e diferente da derivada vira CONFLITO no relatório, e o
script não a toca. Ação já marcada permanece. O script só acrescenta.

Uso:
    python ementas_situacao.py "<pasta da OS>"             # mostra a proposta
    python ementas_situacao.py "<pasta da OS>" --aplicar   # grava (backup antes)
    python ementas_situacao.py "<pasta da OS>" --json

Exit 0 = ok (com ou sem proposta); 2 = erro de uso.
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
import csv
import io
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ementas_os import (ARQUIVO, Ementa, ErroDeUso, RE_COD,  # noqa: E402
                        ler as ler_folha)

for _fluxo in ("stdout", "stderr"):
    try:
        getattr(sys, _fluxo).reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

DESCRICAO_PENDENTE = "(descrição oficial a confirmar no ementário)"

# Numero de auto como o Sistema Auditor o escreve: 23.402.518-2.
RE_AI = re.compile(r"\b\d{2}\.\d{3}\.\d{3}-\d\b")
# "### Nº 23.284.209-4" -> abre o bloco de um auto no snapshot.
RE_BLOCO_AI = re.compile(r"^###\s*N[ºo°]?\s*(\d{2}\.\d{3}\.\d{3}-\d)")
RE_EMENTA_BLOCO = re.compile(r"^\*\*Ementa\s+(\d{6}-\d)\s*(?:·\s*(.*?))?\*\*")
RE_DESCRICAO = re.compile(r"^\*\*Descrição da ementa:\*\*\s*(.+)")
RE_NR = re.compile(r"\b(NR-\d{2})\b")


def _base_nr():
    """codigo -> NR, a partir da base de gradação (a mesma da /aft-preparacao)."""
    for base in (Path(__file__).resolve().parents[1], Path.home() / ".claude/skills"):
        csvzao = base / "aft-preparacao-acao-fiscal/scripts/gradacao_ementas.csv"
        if csvzao.is_file():
            tabela = {}
            with io.open(str(csvzao), encoding="utf-8") as fh:
                for linha in csv.DictReader(fh, delimiter=";"):
                    tabela[linha["codigo"]] = linha["nr"]
            return tabela
    return {}


# ------------------------------------------------------------- as fontes
def _de_autos_lavrados(pasta):
    """{codigo: {'ai','descricao','frente'}} do snapshot do Sistema Auditor.

    Lê SÓ o '## Detalhamento — autos lavrados'. As seções "Autos substituídos"
    (cancelados) e "Pendentes de transmissão" (ainda não existem no mundo
    jurídico) não podem virar Autuação no Relatório de Inspeção.
    """
    arq = pasta / "autos-lavrados.md"
    if not arq.is_file():
        return {}
    texto = arq.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"^## Detalhamento[^\n]*\n(.*?)(?=^## |\Z)", texto, re.S | re.M)
    if not m:
        return {}
    achados, ai_atual, cod_atual = {}, "", ""
    for linha in m.group(1).splitlines():
        linha = linha.strip()
        mb = RE_BLOCO_AI.match(linha)
        if mb:
            ai_atual, cod_atual = mb.group(1), ""
            continue
        me = RE_EMENTA_BLOCO.match(linha)
        if me and ai_atual:
            cod_atual = me.group(1)
            # "NR-12 item 12.5.9" -> NR-12; "MULH" -> MULH. A frente nem sempre
            # e uma NR: atributos da legislacao trabalhista (MULH, REGISTRO)
            # chegam no mesmo campo.
            rotulo = (me.group(2) or "").strip()
            mn = RE_NR.search(rotulo)
            frente = mn.group(1) if mn else (rotulo.split()[0] if rotulo else "")
            achados.setdefault(cod_atual, {"ai": ai_atual, "descricao": "",
                                           "frente": frente})
            continue
        md = RE_DESCRICAO.match(linha)
        if md and cod_atual and not achados[cod_atual]["descricao"]:
            achados[cod_atual]["descricao"] = md.group(1).strip()
    return achados


def _de_memory_autos(pasta):
    """Autos transmitidos segundo o '## Autos lavrados' do memory.md.

    Só serve de rede quando o snapshot não existe (Sistema Auditor inalcançável,
    OS antiga). Conta apenas a linha COERENTE: marcada [x] e com número de AI.
    """
    memoria = pasta / "memory.md"
    if not memoria.is_file():
        return {}
    texto = memoria.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"^## Autos lavrados[ \t]*\n(.*?)(?=^## |\Z)", texto, re.S | re.M)
    if not m:
        return {}
    achados = {}
    for linha in m.group(1).splitlines():
        linha = linha.strip()
        if not re.match(r"-\s*\[[xX]\]", linha):
            continue
        ai = RE_AI.search(linha)
        if not ai:
            continue
        for cod in RE_COD.findall(linha):
            achados.setdefault(cod, {"ai": ai.group(0), "descricao": "",
                                     "frente": ""})
    return achados


def _de_interdicao(pasta):
    """{codigo: (acao, arquivo)} a partir dos documentos de interdição/embargo."""
    dir_ie = pasta / "interdicao-embargo"
    if not dir_ie.is_dir():
        return {}
    achados = {}
    for arq in sorted(dir_ie.glob("*.md")):
        if ".backups" in arq.parts:
            continue
        texto = arq.read_text(encoding="utf-8", errors="replace")
        pista = (arq.name + " " + texto[:4000]).lower()
        tem_interdicao = "interdi" in pista
        tem_embargo = "embarg" in pista
        acoes = []
        if tem_interdicao:
            acoes.append("Interdição")
        if tem_embargo:
            acoes.append("Embargo")
        if not acoes:
            continue
        for cod in set(RE_COD.findall(texto)):
            achados.setdefault(cod, (acoes, arq.name))
    return achados


def _de_notificacoes(pasta):
    """{codigo: arquivo} a partir dos tn-nco-*.md — os itens trazem [<ementa>]."""
    achados = {}
    for arq in sorted(pasta.glob("tn-nco*.md")):
        texto = arq.read_text(encoding="utf-8", errors="replace")
        for cod in set(re.findall(r"\[(\d{6}-\d)\]", texto)):
            achados.setdefault(cod, arq.name)
    return achados


def _tem_notificacao_lavrada(pasta):
    """A OS tem alguma notificação DET efetivamente lavrada (não rascunho)?"""
    memoria = pasta / "memory.md"
    if not memoria.is_file():
        return None            # não dá para saber
    texto = memoria.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"^## Notificações DET[ \t]*\n(.*?)(?=^## |\Z)", texto, re.S | re.M)
    if not m:
        return None
    bloco = m.group(1)
    for pedaco in re.split(r"\n(?=-\s*\[)", bloco):
        if not pedaco.strip().startswith("-"):
            continue
        if "RASCUNHO" in pedaco.upper():
            continue
        if re.search(r"lavrada\s+\d{2}/\d{2}/\d{4}", pedaco):
            return True
    return False


# ---------------------------------------------------------- a proposta
def propor(pasta):
    pasta = Path(pasta).expanduser()
    folha = ler_folha(pasta)

    autuadas = _de_autos_lavrados(pasta)
    fonte_autos = "autos-lavrados.md"
    if not autuadas:
        autuadas = _de_memory_autos(pasta)
        fonte_autos = "memory.md → ## Autos lavrados"
    interditadas = _de_interdicao(pasta)
    notificadas = _de_notificacoes(pasta)
    nrs = _base_nr()

    mudancas, conflitos, avisos, novas = [], [], [], []

    def alvo(codigo, descricao, frente):
        """A linha da ementa na folha; cria se não existir.

        Ementa que já está na OS tem a PRÓPRIA linha preenchida — é o que o
        SFIT faz na tela. Só quem não está na OS ganha linha nova, e sem o "*".
        """
        e = folha.por_codigo(codigo)
        if e is not None:
            return e
        frente = frente or nrs.get(codigo, "?")
        e = Ementa(codigo, descricao or DESCRICAO_PENDENTE, frente, da_os=False)
        folha.ementas.append(e)
        novas.append((codigo, frente))
        return e

    def aplica(e, situacao, acao, lastro, origem):
        if e.situacao and e.situacao != situacao:
            conflitos.append(
                "%s: a folha diz \"%s\", mas %s indica \"%s\" — não foi alterada."
                % (e.codigo, e.situacao, origem, situacao))
        elif not e.situacao:
            e.situacao = situacao
            mudancas.append("%s: situação -> %s   (%s)" % (e.codigo, situacao, origem))
        if acao and acao not in e.acoes:
            e.acoes.append(acao)
            mudancas.append("%s: ação -> %s   (%s)" % (e.codigo, acao, origem))
        if lastro and lastro not in e.lastro:
            e.lastro = (e.lastro + " · " + lastro).strip(" ·") if e.lastro else lastro

    # 1) Auto transmitido. O SFIT já traz essas linhas prontas; aqui elas
    #    existem para o AFT CONFERIR se chegaram, não para digitar.
    for cod, dado in sorted(autuadas.items()):
        e = alvo(cod, dado["descricao"], dado["frente"])
        aplica(e, "Irregular", "Autuação", "AI %s" % dado["ai"], fonte_autos)

    # 2) Interdição / embargo.
    for cod, (acoes, arquivo) in sorted(interditadas.items()):
        e = alvo(cod, "", "")
        for acao in acoes:
            aplica(e, "Irregular", acao, arquivo, "interdicao-embargo/%s" % arquivo)

    # 3) Notificação para correção — o caminho da dupla visita.
    for cod, arquivo in sorted(notificadas.items()):
        e = alvo(cod, "", "")
        aplica(e, "Irregular", "Notificação", arquivo, arquivo)

    if notificadas and _tem_notificacao_lavrada(pasta) is False:
        avisos.append(
            "há tn-nco-*.md na pasta, mas o memory.md não registra nenhuma notificação "
            "DET lavrada — a ação \"Notificação\" só vale depois de a notificação ser "
            "transmitida no DET. Confira antes de aplicar.")
    if folha.dupla_visita == "sim":
        autuadas_na_folha = [e.codigo for e in folha.ementas if "Autuação" in e.acoes]
        if autuadas_na_folha:
            avisos.append(
                "a folha está marcada como dupla visita, mas há Autuação em: %s."
                % ", ".join(sorted(autuadas_na_folha)))
    pendentes = [e.codigo for e in folha.ementas
                 if e.descricao == DESCRICAO_PENDENTE]
    if pendentes:
        avisos.append(
            "sem a descrição oficial de %s — o script não inventa texto de ementa. "
            "Busque na /aft-consulta e corrija a linha." % ", ".join(sorted(pendentes)))

    return folha, {"mudancas": mudancas, "conflitos": conflitos,
                   "avisos": avisos, "novas": novas,
                   "fonte_autos": fonte_autos if autuadas else ""}


def main():
    ap = argparse.ArgumentParser(
        description="Propõe o preenchimento do ementas.md a partir do que já "
                    "existe na pasta da OS.")
    ap.add_argument("pasta_os", help="pasta da OS (a que contém o memory.md)")
    ap.add_argument("--aplicar", action="store_true",
                    help="grava a proposta no ementas.md (backup antes)")
    ap.add_argument("--json", action="store_true", help="saída estruturada")
    args = ap.parse_args()

    try:
        folha, rel = propor(args.pasta_os)
    except ErroDeUso as e:
        print("ERRO: %s" % e, file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps({"relatorio": rel,
                          "ementas": [e.como_dict() for e in folha.ementas]},
                         ensure_ascii=False, indent=2))
        return 0

    print("=" * 72)
    print("  PROPOSTA DE PREENCHIMENTO — %s" % folha.empregador[:42])
    print("=" * 72)
    if rel["fonte_autos"]:
        print("Autos lidos de: %s" % rel["fonte_autos"])
    if not rel["mudancas"]:
        print("Nada a propor: as fontes da pasta não acrescentam nada à folha.")
    for linha in rel["mudancas"]:
        print("  + %s" % linha)
    if rel["novas"]:
        print("-" * 72)
        for cod, frente in rel["novas"]:
            print("  NOVA linha em %s: %s   (fora da lista da OS)" % (frente, cod))
    if rel["conflitos"]:
        print("-" * 72)
        for c in rel["conflitos"]:
            print("  CONFLITO: %s" % c)
    if rel["avisos"]:
        print("-" * 72)
        for a in rel["avisos"]:
            print("  AVISO: %s" % a)
    print("-" * 72)

    if not args.aplicar:
        print("Nada foi gravado. Rode de novo com --aplicar para escrever no %s."
              % ARQUIVO)
        return 0
    if not rel["mudancas"]:
        print("Nada a gravar.")
        return 0
    if folha.origem != ARQUIVO:
        print("ERRO: esta OS ainda guarda as ementas no memory.md. Rode antes:",
              file=sys.stderr)
        print("      python ementas_os.py \"%s\" --migrar" % args.pasta_os,
              file=sys.stderr)
        return 2
    alvo = folha.gravar()
    print("Gravado: %s   (versão anterior em .backups/)" % alvo)
    print("Confira a folha:  python ementas_os.py \"%s\" --folha" % args.pasta_os)
    return 0


if __name__ == "__main__":
    sys.exit(main())
