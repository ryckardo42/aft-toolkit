#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
conferir_rastreamento.py — acha CONTRADIÇÃO entre os registros de auto do memory.md.

O mesmo auto de infração aparece em até quatro lugares: as três seções do
`memory.md` da OS (`## Ementas da OS`, `## Autos de Infração` e
`## Autos lavrados`) e, depois de transmitido, o `autos-lavrados.md` que a
`/aft-autos-lavrados` extrai do Sistema Auditor. Manter os quatro coerentes é
trabalho manual, e numa fiscalização real dois deles se contradisseram: a caixa
marcada `[x]` com o texto ao lado dizendo "pendente de importação".

A convenção que evita isso já existe — status e checkbox mudam JUNTOS, no mesmo
Edit — e não impediu nada, porque convenção escrita não confere arquivo. Este
script confere.

A seção `## Ementas da OS` é a mais perigosa das três, porque alimenta a
avaliação de ementas do Relatório de Inspeção: um "auto lavrado" falso ali entra
em documento oficial. Nela o `[x]` significa "ementa TRATADA nesta fiscalização",
nunca "auto transmitido" — e é essa confusão que o script procura.

O que ele acha:

  1. em `## Autos lavrados`, caixa `[x]` cujo texto diz que o auto ainda não foi
     transmitido ("pendente de importação", "TXT gerado", "em redação");
  2. em `## Autos lavrados`, caixa `[x]` sem número de AI no texto — o `[x]` só
     vale depois de a `/aft-autos-lavrados` confirmar o auto no Sistema Auditor,
     e aí o número real aparece;
  3. em `## Autos lavrados`, caixa `[ ]` cujo texto já traz número de AI;
  4. em `## Ementas da OS`, linha que AFIRMA auto lavrado sem respaldo em
     `## Autos lavrados`.

LIMITE DECLARADO, para o relatório não mentir: isto acha CONTRADIÇÃO entre
registros. Não prova que algum deles está certo — os dois podem estar errados
juntos, e nenhuma leitura de arquivo descobriria isso. Só o Sistema Auditor
responde o que foi de fato transmitido.

O script NUNCA escreve no memory.md. Corrigir é ato do Auditor-Fiscal.

Uso:
    python conferir_rastreamento.py "<pasta da OS>"
    python conferir_rastreamento.py "<pasta da OS>" --resumo

Exit 0 = sem contradição; 1 = há contradição; 2 = erro de uso.
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
import re
import sys
from pathlib import Path

# Numero de auto de infracao como o Sistema Auditor o escreve: 23.402.518-2.
RE_AI = re.compile(r"\b\d{2}\.\d{3}\.\d{3}-\d\b")
RE_EMENTA = re.compile(r"\b(\d{6}-\d)\b")

# Expressoes que dizem, em texto livre, que o auto AINDA NAO foi transmitido.
# A lista e conservadora de proposito: e melhor deixar passar uma forma nova do
# que acusar contradicao onde nao ha.
NAO_TRANSMITIDO = re.compile(
    r"pendente de importa|pendente de transmiss|txt gerado|em reda[çc][ãa]o|"
    r"auto elaborado|n[ãa]o transmitid|aguardando importa", re.I)


def secao(texto, nome):
    """As linhas de item de uma seção '## Nome'. Lista vazia se ela não existe."""
    m = re.search(r"^## %s[ \t]*\n(.*?)(?=^## |\Z)" % re.escape(nome),
                  texto, re.S | re.M)
    if not m:
        return []
    return [l.strip() for l in m.group(1).splitlines() if l.strip().startswith("-")]


def marcado(linha):
    """True se [x], False se [ ], None se a linha não tem caixa."""
    m = re.match(r"-\s*\[([ xX])\]", linha)
    return None if not m else m.group(1).lower() == "x"


class NaoEUmaOS(Exception):
    """A pasta existe, mas nao e uma OS: nao ha memory.md para conferir.

    Isto NAO e contradicao. A primeira versao devolvia a falta do memory.md
    junto com os achados, e o script saia com o codigo de "encontrei
    contradicao" -- de modo que quem apontasse para a pasta errada concluiria
    que a fiscalizacao tem defeito. Erro de uso e erro de uso.
    """


def conferir(pasta):
    """Devolve a lista de contradições encontradas (vazia = tudo coerente)."""
    memoria = Path(pasta) / "memory.md"
    if not memoria.is_file():
        raise NaoEUmaOS(
            "nao achei memory.md em %s -- esta pasta nao e uma OS. Aponte para a "
            "pasta da empresa, a que contem o memory.md." % pasta)
    texto = memoria.read_text(encoding="utf-8", errors="replace")
    problemas = []

    lavrados = secao(texto, "Autos lavrados")
    ementas = secao(texto, "Ementas da OS")

    # --- 1) Em "Autos lavrados": a caixa e o texto tem de dizer a mesma coisa.
    transmitidas = set()
    for linha in lavrados:
        m = marcado(linha)
        if m is None:
            continue
        tem_ai = bool(RE_AI.search(linha))
        diz_pendente = bool(NAO_TRANSMITIDO.search(linha))
        codigos = set(RE_EMENTA.findall(linha))
        if m:
            # So conta como transmitida a linha COERENTE: marcada, com numero de
            # AI e sem dizer que esta pendente. Contar a linha contraditoria
            # daria respaldo a si mesma, e o caso 4 nunca dispararia.
            if tem_ai and not diz_pendente:
                transmitidas |= codigos
            if diz_pendente:
                problemas.append(
                    "Autos lavrados: caixa MARCADA [x] mas o texto diz que nao foi "
                    "transmitido -> %s" % linha[:110])
            elif not tem_ai:
                problemas.append(
                    "Autos lavrados: caixa MARCADA [x] sem numero de AI no texto. O [x] "
                    "so vale depois de a /aft-autos-lavrados confirmar o auto no Sistema "
                    "Auditor, e ai o numero real aparece -> %s" % linha[:110])
        else:
            if tem_ai and not diz_pendente:
                problemas.append(
                    "Autos lavrados: caixa VAZIA [ ] mas o texto ja traz numero de AI -> %s"
                    % linha[:110])

    # --- 2) Em "Ementas da OS": [x] que afirma auto lavrado precisa de respaldo.
    #        Aqui o [x] significa "ementa tratada", nunca "auto transmitido" --
    #        entao so se investiga a linha que AFIRMA, em texto, o auto lavrado.
    for linha in ementas:
        if marcado(linha) is not True:
            continue
        if not re.search(r"auto lavrado|lavrado o auto|auto transmitido", linha, re.I):
            continue
        orfas = set(RE_EMENTA.findall(linha)) - transmitidas
        if orfas:
            problemas.append(
                "Ementas da OS: a linha afirma AUTO LAVRADO, mas a ementa %s nao aparece "
                "como transmitida em 'Autos lavrados'. Esta secao alimenta a avaliacao do "
                "Relatorio de Inspecao: um 'auto lavrado' falso aqui entra em documento "
                "oficial -> %s" % (", ".join(sorted(orfas)), linha[:100]))

    # --- 3) Coerencia com o snapshot oficial, quando ele existe.
    oficial = Path(pasta) / "autos-lavrados.md"
    if oficial.is_file() and transmitidas:
        no_oficial = set(RE_EMENTA.findall(
            oficial.read_text(encoding="utf-8", errors="replace")))
        # So acusa o sentido perigoso: o memory.md afirma transmitido e o
        # snapshot do Sistema Auditor nao conhece. O contrario (o snapshot com
        # mais ementas) e normal -- pode ser auto de outra leva ainda nao anotado.
        faltando = transmitidas - no_oficial
        if faltando:
            problemas.append(
                "memory.md marca como transmitida(s) a(s) ementa(s) %s, mas o "
                "autos-lavrados.md (snapshot do Sistema Auditor) nao as traz. Ou o "
                "snapshot esta velho, ou o [x] foi marcado antes da transmissao."
                % ", ".join(sorted(faltando)))

    return problemas


def main():
    ap = argparse.ArgumentParser(
        description="Acha contradicao entre os registros de auto do memory.md.")
    ap.add_argument("pasta_os", help="pasta da OS (a que contem o memory.md)")
    ap.add_argument("--resumo", action="store_true",
                    help="so o veredito, sem cabecalho")
    args = ap.parse_args()

    pasta = Path(args.pasta_os).expanduser()
    if not pasta.is_dir():
        print("ERRO: nao e uma pasta: %s" % pasta, file=sys.stderr)
        return 2

    try:
        problemas = conferir(pasta)
    except NaoEUmaOS as e:
        print("ERRO: %s" % e, file=sys.stderr)
        return 2
    if not args.resumo:
        print("=" * 72)
        print("  RASTREAMENTO DOS AUTOS -- %s" % pasta.name[:52])
        print("=" * 72)
    if problemas:
        for p in problemas:
            print("  CONTRADICAO: %s" % p)
        print("-" * 72)
        print("%d contradicao(oes). Status e checkbox mudam JUNTOS, no mesmo Edit."
              % len(problemas))
        return 1
    print("Sem contradicao entre os registros de auto do memory.md.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
