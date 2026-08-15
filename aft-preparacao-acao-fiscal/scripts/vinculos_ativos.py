#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""vinculos_ativos.py — lê a Relação de Empregados do Estabelecimento (SFIT-WEB).

É o PDF "ImprimirVinculosAtivosPDF": um resumo por faixa etária (homens, mulheres,
PCD, aprendizes) seguido da lista nominal de empregados, com PIS, nome, admissão,
ocupação e as marcas de PCD e aprendiz.

O tratamento é INTEIRAMENTE LOCAL — o PDF nunca sai da máquina e nenhum nome de
trabalhador é lido pelo modelo. O script devolve:

  · o efetivo do estabelecimento (homens + mulheres do quadro-resumo);
  · a composição (PCD, aprendizes, menores de 18) como recorte informativo;
  · quantos profissionais de SESMT constam da lista, nos mesmos rótulos que o
    dimensionar_sesmt.py usa — para confronto direto com o Anexo II da NR-04;
  · os interlocutores prováveis da ação fiscal (RH/DP e produção);
  · a contagem de trabalhadores por ocupação.

PRIVACIDADE: nome só aparece na saída para o pessoal de SESMT e para os
interlocutores — quem o AFT vai procurar e entrevistar. Os demais empregados
viram contagem por ocupação e nada mais; a lista nominal completa não é impressa,
não é gravada e não vai para o chat.

EFETIVO: é `homens + mulheres` da linha "Total" do quadro-resumo. PCD e aprendizes
NÃO se somam a esse número — são recortes dele (na Relação, cada PCD também está
contado como homem ou mulher). O script confere esse total contra o número de
linhas da lista nominal e avisa quando divergirem.

Uso:
    python vinculos_ativos.py "<arquivo.pdf>" [--json]
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
import sys
import unicodedata
from collections import Counter
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):     # console cp1252 no Windows
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Colunas da lista nominal, em pontos (página A4 de 595 pt). O corte é feito
# caractere a caractere: nome comprido encosta na data de admissão sem espaço,
# e só o corte por posição separa os dois corretamente.
COLUNAS = (("idx", 0, 120), ("nome", 120, 288), ("adm", 288, 355),
           ("ocup", 355, 505), ("pcd", 505, 540), ("apr", 540, 10 ** 4))
ESPACO = 1.5        # lacuna (pt) que separa palavras — no PDF não há glifo de espaço
LINHA = 2.5         # tolerância vertical (pt) para agrupar caracteres na mesma linha

RE_DATA = re.compile(r"^\d{2}/\d{2}/\d{4}$")
# Numeros do quadro-resumo vem com ponto de milhar a partir de 1.000 ("1.151").
RE_RESUMO = re.compile(
    r"^(A\s*partir\s*de\s*18|Abaixo\s*de\s*18|Total)\s+"
    + r"\s+".join([r"([\d.]+)"] * 5) + r"\s*$", re.I)
RE_CNPJ = re.compile(r"CNPJ/CPF:\s*([\d./-]{11,20})")
RE_RAZAO = re.compile(r"Raz[ãa]o\s*Social:\s*(.+?)\s*$")
RE_EMISSAO = re.compile(r"Data\s*de\s*Emiss[ãa]o:\s*(\d{2}/\d{2}/\d{4})")
RE_LIMITE = re.compile(r"listagem\s*limitada", re.I)

# Rótulos IDÊNTICOS aos do dimensionar_sesmt.py (Anexo II da NR-04) — é o que
# permite confrontar devido x existente sem tradução no meio do caminho.
SESMT = [
    ("Engenheiro de Segurança do Trabalho", ("engenheiro", "seguranca", "trabalho")),
    ("Médico do Trabalho", ("medico", "trabalho")),
    ("Enfermeiro do Trabalho", ("enfermeiro", "trabalho")),
    ("Auxiliar/Técnico de Enfermagem do Trabalho", ("enfermagem", "trabalho")),
    ("Técnico de Segurança do Trabalho", ("tecnico", "seguranca", "trabalho")),
]

# Interlocutores da ação fiscal: quem costuma prestar as informações. Cada papel
# tem níveis em ordem de hierarquia — o script fica no nível mais alto presente.
INTERLOCUTORES = [
    ("Pessoal / RH", [
        ("gerente", ("gerente",), ("departamento pessoal", "recursos humanos", "pessoal", "rh")),
        ("chefe/coordenador", ("chefe", "coordenador"), ("departamento pessoal", "recursos humanos", "pessoal", "rh")),
        ("supervisor", ("supervisor",), ("departamento pessoal", "recursos humanos", "pessoal", "rh")),
        ("analista/assistente", ("analista", "assistente", "auxiliar", "tecnico"),
         ("departamento pessoal", "recursos humanos", "pessoal", "rh")),
    ]),
    ("Produção", [
        ("gerente", ("gerente",), ("producao",)),
        ("chefe/coordenador", ("chefe", "coordenador"), ("producao",)),
        ("supervisor/encarregado", ("supervisor", "encarregado"), ("producao",)),
    ]),
]
MAX_INTERLOCUTORES = 5     # por papel — evita despejar dezenas de encarregados


def fail(msg):
    print(f"ERRO: {msg}", file=sys.stderr)
    sys.exit(1)


def sem_acento(txt: str) -> str:
    txt = unicodedata.normalize("NFD", txt.lower())
    return "".join(c for c in txt if unicodedata.category(c) != "Mn")


# ------------------------------------------------------------------ leitura
def coluna(x: float) -> str:
    for nome, ini, fim in COLUNAS:
        if ini <= x < fim:
            return nome
    return "?"


def junta(chars) -> str:
    """Texto de uma sequência de caracteres, com espaço onde há lacuna."""
    partes = []
    anterior = None
    for c in chars:
        if anterior is not None and c["x0"] - anterior["x1"] >= ESPACO:
            partes.append(" ")
        partes.append(c["text"])
        anterior = c
    return "".join(partes).strip()


def linhas(pagina):
    """Linhas da página como (texto_inteiro, {coluna: texto})."""
    grupos = []
    for c in sorted(pagina.chars, key=lambda c: (c["top"], c["x0"])):
        if grupos and abs(c["top"] - grupos[-1][0]) <= LINHA:
            grupos[-1][1].append(c)
        else:
            grupos.append((c["top"], [c]))
    for _, chars in grupos:
        chars.sort(key=lambda c: c["x0"])
        cols, atual = {}, None
        for c in chars:
            atual = coluna(c["x0"])
            cols.setdefault(atual, []).append(c)
        yield junta(chars), {k: junta(v) for k, v in cols.items()}


def le_pdf(caminho: Path):
    try:
        import pdfplumber
    except ImportError:
        fail("falta a biblioteca pdfplumber — instale com: "
             f'"{sys.executable}" -m pip install pdfplumber')

    cab = {"cnpj": "", "razao_social": "", "data_emissao": ""}
    resumo, registros, rodape = {}, [], []
    with pdfplumber.open(str(caminho)) as pdf:
        for pagina in pdf.pages:
            for texto, cols in linhas(pagina):
                if not texto:
                    continue
                for chave, padrao in (("cnpj", RE_CNPJ), ("razao_social", RE_RAZAO),
                                      ("data_emissao", RE_EMISSAO)):
                    m = padrao.search(texto)
                    if m and not cab[chave]:
                        cab[chave] = m.group(1).strip()
                m = RE_RESUMO.match(texto)
                if m:
                    faixa = sem_acento(m.group(1)).replace(" ", "_")
                    n = [int(g.replace(".", "")) for g in m.groups()[1:]]
                    resumo[faixa] = {
                        "homens": n[0], "mulheres": n[1], "pcd": n[2],
                        "aprendizes": n[3], "aprendizes_pcd": n[4]}
                    continue
                if RE_LIMITE.search(texto):
                    rodape.append(texto)
                    continue
                idx = cols.get("idx", "")
                if idx.isdigit() and RE_DATA.match(cols.get("adm", "")):
                    registros.append({
                        "n": int(idx), "nome": cols.get("nome", ""),
                        "admissao": cols["adm"], "ocupacao": cols.get("ocup", ""),
                        "pcd": cols.get("pcd", "") == "Sim",
                        "aprendiz": cols.get("apr", "") == "Sim"})
                elif registros and not idx and not cols.get("adm"):
                    # continuação: nome ou ocupação que quebrou para a linha seguinte
                    for campo, chave in (("nome", "nome"), ("ocup", "ocupacao")):
                        if cols.get(campo):
                            registros[-1][chave] = (registros[-1][chave] + " "
                                                    + cols[campo]).strip()
    if not resumo and not registros:
        fail(f"{caminho.name} não parece uma Relação de Empregados do "
             "Estabelecimento (SFIT-WEB): não achei o quadro-resumo nem a lista")
    return cab, resumo, registros, rodape


# ------------------------------------------------------------------ análise
def classifica_sesmt(ocupacao: str):
    o = sem_acento(ocupacao)
    for rotulo, termos in SESMT:
        if all(t in o for t in termos):
            return rotulo
    return None


def acha_interlocutores(registros):
    achados = {}
    for papel, niveis in INTERLOCUTORES:
        for nivel, cargos, areas in niveis:
            gente = [r for r in registros
                     if any(c in sem_acento(r["ocupacao"]) for c in cargos)
                     and any(a in sem_acento(r["ocupacao"]) for a in areas)]
            if gente:
                achados[papel] = {
                    "nivel": nivel,
                    "pessoas": [{"nome": r["nome"], "ocupacao": r["ocupacao"],
                                 "admissao": r["admissao"]}
                                for r in gente[:MAX_INTERLOCUTORES]],
                    "total": len(gente)}
                break
    return achados


def analisa(caminho: Path):
    cab, resumo, registros, rodape = le_pdf(caminho)
    total = resumo.get("total") or {}
    efetivo = (total.get("homens", 0) + total.get("mulheres", 0)) or None

    # Autoconferências: o quadro-resumo e a lista nominal têm de contar a mesma
    # gente. Divergência significa lista truncada ou leitura incompleta — e o
    # efetivo é justamente o que alimenta SESMT e CIPA.
    observacoes = []
    if efetivo and registros and efetivo != len(registros):
        observacoes.append(
            f"O quadro-resumo indica {efetivo} empregados (homens + mulheres), "
            f"mas a lista nominal traz {len(registros)}"
            + (f" — o PDF avisa: \"{rodape[0]}\"" if rodape else "")
            + ". Confirme o efetivo em campo antes de dimensionar SESMT e CIPA.")
    for campo, marca in (("pcd", "pcd"), ("aprendizes", "aprendiz")):
        declarado, na_lista = total.get(campo, 0), sum(1 for r in registros if r[marca])
        if registros and declarado != na_lista:
            observacoes.append(
                f"O quadro-resumo declara {declarado} {campo}, mas a lista nominal "
                f"marca {na_lista}. Confirme em campo.")

    equipe = {rotulo: {"quantidade": 0, "pessoas": []} for rotulo, _ in SESMT}
    for r in registros:
        rotulo = classifica_sesmt(r["ocupacao"])
        if rotulo:
            equipe[rotulo]["quantidade"] += 1
            equipe[rotulo]["pessoas"].append(
                {"nome": r["nome"], "ocupacao": r["ocupacao"],
                 "admissao": r["admissao"]})

    return {
        "arquivo": caminho.name,
        "cnpj": re.sub(r"\D", "", cab["cnpj"]),
        "razao_social": cab["razao_social"],
        "data_emissao": cab["data_emissao"],
        "resumo": resumo,
        "efetivo": efetivo,
        "listados": len(registros),
        "composicao": {
            "homens": total.get("homens", 0), "mulheres": total.get("mulheres", 0),
            "pcd": total.get("pcd", 0), "aprendizes": total.get("aprendizes", 0),
            "aprendizes_pcd": total.get("aprendizes_pcd", 0),
            "menores_de_18": sum((resumo.get("abaixo_de_18") or {}).get(k, 0)
                                 for k in ("homens", "mulheres")),
        },
        "sesmt_na_lista": equipe,
        "interlocutores": acha_interlocutores(registros),
        "ocupacoes": dict(Counter(r["ocupacao"] for r in registros).most_common()),
        "observacoes": observacoes,
        "nota_rodape": rodape,
    }


# ------------------------------------------------------------------- saída
def imprime(d):
    c = d["composicao"]
    print(f"Relação de Empregados — {d['arquivo']}")
    if d["cnpj"]:
        print(f"CNPJ {d['cnpj']}"
              + (f" · emitida em {d['data_emissao']}" if d["data_emissao"] else ""))
    print(f"\nEfetivo do estabelecimento: {d['efetivo']} "
          f"({c['homens']} homens + {c['mulheres']} mulheres)")
    print(f"Recortes (já incluídos no efetivo): PCD {c['pcd']} · "
          f"aprendizes {c['aprendizes']} (PCD {c['aprendizes_pcd']}) · "
          f"menores de 18 {c['menores_de_18']}")
    print(f"Lista nominal: {d['listados']} trabalhadores · "
          f"{len(d['ocupacoes'])} ocupações distintas")

    print("\nSESMT na lista de vínculos:")
    for rotulo, dados in d["sesmt_na_lista"].items():
        nomes = "; ".join(p["nome"] for p in dados["pessoas"])
        print(f"  {dados['quantidade']:>2}  {rotulo}" + (f" — {nomes}" if nomes else ""))

    print("\nInterlocutores prováveis:")
    if not d["interlocutores"]:
        print("  (nenhum cargo de RH/DP ou de produção identificado na lista)")
    for papel, dados in d["interlocutores"].items():
        for p in dados["pessoas"]:
            print(f"  {papel}: {p['nome']} — {p['ocupacao']} "
                  f"(admissão {p['admissao']})")
        if dados["total"] > len(dados["pessoas"]):
            print(f"  {papel}: (+{dados['total'] - len(dados['pessoas'])} no mesmo nível)")

    for obs in d["observacoes"]:
        print(f"\nAVISO: {obs}")
    for nota in d["nota_rodape"]:
        print(f"\nNota do PDF: {nota}")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("pdf", help="Relação de Empregados do Estabelecimento (PDF)")
    ap.add_argument("--json", action="store_true", help="saída apenas em JSON")
    a = ap.parse_args()

    caminho = Path(a.pdf)
    if not caminho.is_file():
        fail(f"arquivo não encontrado: {caminho}")
    d = analisa(caminho)
    if a.json:
        print(json.dumps(d, ensure_ascii=False, indent=2))
    else:
        imprime(d)


if __name__ == "__main__":
    main()
