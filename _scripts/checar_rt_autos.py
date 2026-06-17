#!/usr/bin/env python3
"""
checar_rt_autos.py - coerencia entre a Secao 4 do RT (.docx) e os autos (autos.md).

Ao editar o RT (trocar ementas por itens da NR, tirar/incluir irregularidades), o RT e
o autos.md podem desalinhar. Este verificador compara os dois e SINALIZA divergencias
para o AFT revisar (nao bloqueia, nao corrige - so aponta).

Sinais comparados (robustos, de baixo falso-positivo):
  1. CONTAGEM: nº de irregularidades na Secao 4 do RT x nº de autos no autos.md.
  2. NRs ENVOLVIDAS: conjunto de NRs citadas na Secao 4 x nos autos (pega casos como
     "NR-35 no RT mas sem auto de NR-35", ou "NR-01 nos autos mas nao no RT").
  3. CODIGOS DE EMENTA: se o RT trouxer codigos (formato XXXXXX-X), compara os conjuntos.

NAO faz casamento por subitem (33.3.1 x 33.3.2 etc.) porque a relacao item-de-NR x
ementa e muitos-para-muitos e geraria ruido. Lista os dois lados para conferencia manual.

Uso:
    python checar_rt_autos.py "<RT.docx>" "<autos.md>"
Exit 0 = sem divergencia detectada; 1 = ha divergencia (revisar).
"""
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

CODE_RE = re.compile(r"\d{6}-\d")
NR_RE = re.compile(r"NR[-\s]?0*(\d{1,2})", re.IGNORECASE)


def nrs(texto):
    return {int(n) for n in NR_RE.findall(texto)}


def codes(texto):
    return set(CODE_RE.findall(texto))


def ler_secao4_rt(rt_path):
    """Retorna (itens_de_lista, texto_completo_da_secao4)."""
    import docx
    doc = docx.Document(rt_path)
    paras = doc.paragraphs
    ini = fim = None
    for i, p in enumerate(paras):
        t = p.text.strip().upper()
        if ini is None and t.startswith("4.") and "IRREGULARIDADE" in t:
            ini = i
        elif ini is not None and t.startswith("5.") and ("FATOR" in t or "RISCO" in t):
            fim = i
            break
    if ini is None:
        return None, None
    sec = paras[ini + 1:(fim if fim is not None else len(paras))]
    itens = []
    for p in sec:
        pPr = p._p.pPr
        eh_lista = pPr is not None and pPr.numPr is not None
        if eh_lista and p.text.strip():
            itens.append(p.text.strip())
    texto = "\n".join(p.text for p in sec)
    return itens, texto


def ler_autos(autos_path):
    """Retorna lista de (codigo, descricao) e o texto completo."""
    texto = open(autos_path, encoding="utf-8").read()
    blocos = re.split(r"=== AUTO(?: DE INFRAÇÃO)? #\d+ ===", texto)
    autos = []
    for b in blocos:
        m = re.search(r"Ementa:\s*(\d{6}-\d)\s*-\s*(.*)", b)
        if m:
            autos.append((m.group(1), m.group(2).strip()))
    return autos, texto


def main():
    if len(sys.argv) != 3:
        print("uso: python checar_rt_autos.py <RT.docx> <autos.md>", file=sys.stderr)
        sys.exit(2)
    rt_path, autos_path = sys.argv[1], sys.argv[2]
    for p in (rt_path, autos_path):
        if not os.path.isfile(p):
            print(f"ERRO: arquivo nao encontrado: {p}", file=sys.stderr)
            sys.exit(2)

    itens_rt, texto_rt = ler_secao4_rt(rt_path)
    if itens_rt is None:
        print("ERRO: nao encontrei a 'Secao 4 - IRREGULARIDADE(S)' no RT.", file=sys.stderr)
        sys.exit(2)
    autos, texto_autos = ler_autos(autos_path)

    nrs_rt, nrs_au = nrs(texto_rt), nrs(texto_autos)
    cod_rt, cod_au = codes(texto_rt), codes(texto_autos)

    div = []  # divergencias

    print("=" * 64)
    print("  COERENCIA RT  x  autos.md")
    print("=" * 64)
    print(f"Secao 4 do RT : {len(itens_rt)} irregularidade(s)")
    print(f"autos.md      : {len(autos)} auto(s)")
    if len(itens_rt) != len(autos):
        div.append(f"Contagem divergente: RT={len(itens_rt)} x autos={len(autos)}.")

    print("\nNRs na Secao 4 do RT : " + (", ".join(f"NR-{n:02d}" for n in sorted(nrs_rt)) or "-"))
    print("NRs nos autos        : " + (", ".join(f"NR-{n:02d}" for n in sorted(nrs_au)) or "-"))
    so_rt = nrs_rt - nrs_au
    so_au = nrs_au - nrs_rt
    if so_rt:
        div.append("NR(s) no RT sem auto correspondente: "
                   + ", ".join(f"NR-{n:02d}" for n in sorted(so_rt)))
    if so_au:
        div.append("NR(s) nos autos sem item no RT: "
                   + ", ".join(f"NR-{n:02d}" for n in sorted(so_au)))

    if cod_rt:
        print("\nO RT contem codigos de ementa - comparando codigos:")
        c_so_au = cod_au - cod_rt
        c_so_rt = cod_rt - cod_au
        if c_so_rt:
            div.append("Ementa(s) no RT sem auto: " + ", ".join(sorted(c_so_rt)))
        if c_so_au:
            div.append("Ementa(s) nos autos sem respaldo no RT: " + ", ".join(sorted(c_so_au)))
    else:
        print("\n(O RT usa itens de NR, sem codigos de ementa - comparacao por NR + contagem.)")

    print("\n--- Autos (autos.md) ---")
    for i, (c, d) in enumerate(autos, 1):
        print(f"  {i:>2}. {c}  {d[:70]}")
    print("\n--- Irregularidades (Secao 4 do RT) ---")
    for i, t in enumerate(itens_rt, 1):
        print(f"  {i:>2}. {t[:80]}")

    print("\n" + "-" * 64)
    if div:
        print(f"DIVERGENCIAS ({len(div)}) - revise:")
        for d in div:
            print("  ! " + d)
        print("\nObs.: contagem e NR sao sinais; confira a lista acima item a item.")
        sys.exit(1)
    print("Sem divergencias de contagem/NR/codigo. Confira mesmo assim a lista acima.")
    sys.exit(0)


if __name__ == "__main__":
    main()
