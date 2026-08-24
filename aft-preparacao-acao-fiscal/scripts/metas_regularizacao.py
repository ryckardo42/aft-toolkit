# -*- coding: utf-8 -*-
"""Destaque das ementas I3/I4 de uma OS para a meta de regularização.

Nos projetos de fiscalização de SST, a fiscalização só "conta" para a meta
quando o AFT consegue a REGULARIZAÇÃO de um mínimo de ementas de gradação
I3 ou I4:

  - regra geral (projetos SST): pelo menos 2 ementas I3/I4 regularizadas;
  - projeto de construção civil: pelo menos 3 ementas I3/I4, e somente
    das NR-10, NR-18 e NR-35 (use --construcao-civil).

Exceções que a skill explica ao AFT (o script apenas lembra):
  - ementas alvo de embargo/interdição contam mesmo sem regularização;
  - empresa sob dupla visita (ME/EPP, art. 627-A da CLT): não se autua,
    mas a regularização das ementas conta normalmente.

Este script NÃO decide nada: cruza os códigos de ementa da OS com a base
local de gradação (gradacao_ementas.csv, gerada do ementário SST) e com a
lista curada de ementas de fácil regularização pelo empregador
(ementas_faceis.csv, notas de 8 a 10 numa régua de 1 a 10). Quem decide a
estratégia da ação fiscal é o AFT.

Uso:
    python metas_regularizacao.py 101059-0 312494-0 ...
    python metas_regularizacao.py --arquivo "<pasta da OS>/memory.md"
    python metas_regularizacao.py --arquivo <texto extraído da OS> --construcao-civil
    (aceita códigos com ou sem hífen; --arquivo pode repetir; --json p/ dado bruto)
"""
import argparse
import csv
import io
import json
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

AQUI = Path(__file__).resolve().parent
RE_COD = re.compile(r"\b(\d{6})-(\d)\b")
NRS_CONSTRUCAO = {"NR-10", "NR-18", "NR-35"}


def normaliza(cod):
    cod = re.sub(r"\D", "", cod)
    if len(cod) != 7:
        return None
    return cod[:6] + "-" + cod[6]


def carrega_base():
    grad, faceis = {}, {}
    with io.open(AQUI / "gradacao_ementas.csv", encoding="utf-8") as fh:
        for linha in csv.DictReader(fh, delimiter=";"):
            grad[linha["codigo"]] = (linha["nr"], linha["gradacao"])
    with io.open(AQUI / "ementas_faceis.csv", encoding="utf-8") as fh:
        for linha in csv.DictReader(fh, delimiter=";"):
            faceis[linha["codigo"]] = (int(linha["nota"]), linha["justificativa"])
    return grad, faceis


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("codigos", nargs="*", help="códigos de ementa (com ou sem hífen)")
    ap.add_argument("--arquivo", action="append", default=[],
                    help="arquivo de texto (memory.md, extrato da OS) de onde extrair os códigos")
    ap.add_argument("--construcao-civil", action="store_true",
                    help="aplica a regra do projeto de construção civil (3 ementas, só NR-10/18/35)")
    ap.add_argument("--json", action="store_true", help="saída estruturada")
    args = ap.parse_args()

    codigos, ordem = set(), []
    for c in args.codigos:
        n = normaliza(c)
        if n and n not in codigos:
            codigos.add(n)
            ordem.append(n)
        elif not n:
            print(f"AVISO: '{c}' não parece código de ementa (7 dígitos) - ignorado.")
    for arq in args.arquivo:
        p = Path(arq)
        if not p.exists():
            sys.exit(f"ERRO: arquivo não encontrado: {arq}")
        texto = p.read_text(encoding="utf-8", errors="replace")
        for m in RE_COD.finditer(texto):
            n = m.group(1) + "-" + m.group(2)
            if n not in codigos:
                codigos.add(n)
                ordem.append(n)

    if not ordem:
        sys.exit("ERRO: nenhum código de ementa informado (argumentos ou --arquivo).")

    grad, faceis = carrega_base()
    linhas = []
    for cod in ordem:
        nr, g = grad.get(cod, ("?", ""))
        nota, justif = faceis.get(cod, (None, ""))
        conta_meta = g in ("I3", "I4") and (
            not args.construcao_civil or nr in NRS_CONSTRUCAO)
        linhas.append({"codigo": cod, "nr": nr, "gradacao": g,
                       "meta": conta_meta, "facil": nota is not None and conta_meta,
                       "nota": nota, "justificativa": justif})

    minimo = 3 if args.construcao_civil else 2
    meta = [l for l in linhas if l["meta"]]
    faceis_os = [l for l in meta if l["facil"]]
    desconhecidas = [l for l in linhas if l["gradacao"] == ""]

    if args.json:
        print(json.dumps({"minimo": minimo,
                          "construcao_civil": args.construcao_civil,
                          "ementas": linhas}, ensure_ascii=False, indent=2))
        return

    def bloco(titulo, itens):
        if not itens:
            return
        print(f"\n{titulo}")
        for l in itens:
            marca = f"  [FÁCIL {l['nota']}/10] {l['justificativa']}" if l["facil"] else ""
            print(f"  {l['codigo']}  {l['gradacao'] or '??'}  ({l['nr']}){marca}")

    print(f"Ementas analisadas: {len(linhas)}"
          + (" - regra do projeto de construção civil (só NR-10/18/35)"
             if args.construcao_civil else ""))
    chave = lambda l: (-(l["nota"] or 0), l["codigo"])
    bloco("== CONTAM PARA A META (I4) ==",
          sorted([l for l in meta if l["gradacao"] == "I4"], key=chave))
    bloco("== CONTAM PARA A META (I3) ==",
          sorted([l for l in meta if l["gradacao"] == "I3"], key=chave))
    fora = [l for l in linhas if not l["meta"] and l["gradacao"]]
    bloco("== NÃO CONTAM PARA A META ==", sorted(fora, key=lambda l: l["codigo"]))
    bloco("== GRADAÇÃO NÃO ENCONTRADA NA BASE (conferir no ementário) ==",
          desconhecidas)

    print(f"\nResumo: {len(meta)} ementa(s) I3/I4 na OS (mínimo para a meta: {minimo})"
          + (f", sendo {len(faceis_os)} de fácil regularização pelo empregador."
             if faceis_os else "."))
    if len(meta) < minimo:
        print("ATENÇÃO: a OS, sozinha, não alcança o mínimo da meta - vale avaliar "
              "com o AFT ementas I3/I4 pertinentes fora da lista da OS.")
    print("Lembretes: ementa alvo de embargo/interdição conta mesmo sem "
          "regularização; sob dupla visita não se autua, mas a regularização "
          "conta. Quem decide a estratégia é o AFT.")


if __name__ == "__main__":
    main()
