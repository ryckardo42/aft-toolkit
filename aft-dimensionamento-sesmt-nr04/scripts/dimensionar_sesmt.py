#!/usr/bin/env python3
"""
Dimensionamento do SESMT — Anexo II da NR-04.
Cálculo determinístico a partir do grau de risco (1-4) e do número de trabalhadores.

Uso:
    python3 dimensionar_sesmt.py <grau_de_risco> <num_trabalhadores> [--saude]
    --saude : estabelecimento de saúde (hospital, ambulatório, maternidade, casa de
              saúde/repouso, clínica ou similar) -> aplica a Observação A do Anexo II.

Saída: texto formatado + JSON.
Fonte dos dados: Anexo II da NR-04 (leitura visual da tabela oficial, célula a célula).
"""
import sys, json, argparse

TSE, ENG, AUX, ENF, MED = ("Técnico de Segurança do Trabalho",
                           "Engenheiro de Segurança do Trabalho",
                           "Auxiliar/Técnico de Enfermagem do Trabalho",
                           "Enfermeiro do Trabalho",
                           "Médico do Trabalho")
PROFS = [TSE, ENG, AUX, ENF, MED]

# Flags: "I" = tempo integral; "P" = tempo parcial (mínimo 3 horas / 15h semanais);
# "S" = quantitativo de Aux./Téc. com a opção (***) de substituição por
#       enfermeiro do trabalho em tempo parcial.
# Cada faixa: (min, max, {prof: (qtd, flag)}). Faixas NÃO cumulativas.
FAIXAS = [(50,100),(101,250),(251,500),(501,1000),(1001,2000),(2001,3500),(3501,5000)]

TABELA = {
 1: {
   (50,100):{}, (101,250):{}, (251,500):{},
   (501,1000):{TSE:(1,"I")},
   (1001,2000):{TSE:(1,"I"), MED:(1,"P")},
   (2001,3500):{TSE:(1,"I"), ENG:(1,"P"), AUX:(1,"S"), MED:(1,"P")},
   (3501,5000):{TSE:(2,"I"), ENG:(1,"I"), AUX:(1,"I"), ENF:(1,"P"), MED:(1,"I")},
   "grupo":{TSE:(1,"I"), ENG:(1,"P"), AUX:(1,"I"), MED:(1,"P")},
 },
 2: {
   (50,100):{}, (101,250):{}, (251,500):{},
   (501,1000):{TSE:(1,"I")},
   (1001,2000):{TSE:(1,"I"), ENG:(1,"P"), AUX:(1,"S"), MED:(1,"P")},
   (2001,3500):{TSE:(2,"I"), ENG:(1,"I"), AUX:(1,"S"), MED:(1,"I")},
   (3501,5000):{TSE:(5,"I"), ENG:(1,"I"), AUX:(1,"I"), ENF:(1,"I"), MED:(1,"I")},
   "grupo":{TSE:(1,"I"), ENG:(1,"P"), AUX:(1,"I"), MED:(1,"I")},
 },
 3: {
   (50,100):{},
   (101,250):{TSE:(1,"I")},
   (251,500):{TSE:(2,"I")},
   (501,1000):{TSE:(3,"I"), ENG:(1,"P"), MED:(1,"P")},
   (1001,2000):{TSE:(4,"I"), ENG:(1,"I"), AUX:(1,"S"), MED:(1,"I")},
   (2001,3500):{TSE:(6,"I"), ENG:(1,"I"), AUX:(1,"I"), ENF:(1,"I"), MED:(1,"I")},
   (3501,5000):{TSE:(8,"I"), ENG:(2,"I"), AUX:(1,"I"), ENF:(1,"I"), MED:(2,"I")},
   "grupo":{TSE:(3,"I"), ENG:(1,"I"), AUX:(1,"I"), MED:(1,"I")},
 },
 4: {
   (50,100):{TSE:(1,"I")},
   (101,250):{TSE:(2,"I"), ENG:(1,"P"), MED:(1,"P")},
   (251,500):{TSE:(3,"I"), ENG:(1,"P"), MED:(1,"P")},
   (501,1000):{TSE:(4,"I"), ENG:(1,"I"), AUX:(1,"S"), MED:(1,"I")},
   (1001,2000):{TSE:(5,"I"), ENG:(1,"I"), AUX:(1,"S"), MED:(1,"I")},
   (2001,3500):{TSE:(8,"I"), ENG:(2,"I"), AUX:(1,"I"), ENF:(1,"I"), MED:(2,"I")},
   (3501,5000):{TSE:(10,"I"), ENG:(3,"I"), AUX:(1,"I"), ENF:(1,"I"), MED:(3,"I")},
   "grupo":{TSE:(3,"I"), ENG:(1,"I"), AUX:(1,"I"), MED:(1,"I")},
 },
}

FLAG_TXT = {"I":"tempo integral", "P":"tempo parcial (mínimo de 3 horas)",
            "S":"tempo integral; opção (***): substituível por enfermeiro do trabalho em tempo parcial"}

def grupos_acima_5000(n):
    """Regra (**): cada 4.000 do excedente = 1 grupo; fração só conta se > 2.000."""
    exc = n - 5000
    g, resto = divmod(exc, 4000)
    if resto > 2000:
        g += 1
    return g, exc, resto

def dimensionar(gr, n, saude=False):
    if gr not in (1,2,3,4):
        raise ValueError("Grau de risco deve ser 1, 2, 3 ou 4.")
    if n < 1:
        raise ValueError("Número de trabalhadores deve ser >= 1.")
    memoria = []
    res = {p: {"quantidade":0, "regime":None, "observacoes":[]} for p in PROFS}

    if n < 50:
        memoria.append(f"N = {n} < 50: abaixo da menor faixa do Anexo II. "
                       "Não há dimensionamento de SESMT pela tabela.")
        faixa_txt = "abaixo de 50"
    elif n <= 5000:
        faixa = next(f for f in FAIXAS if f[0] <= n <= f[1])
        faixa_txt = f"{faixa[0]:,} a {faixa[1]:,}".replace(",",".")
        memoria.append(f"N = {n}: faixa aplicável (única, não cumulativa) = {faixa_txt}, GR {gr}.")
        for p,(q,fl) in TABELA[gr][faixa].items():
            res[p]["quantidade"] = q
            res[p]["regime"] = FLAG_TXT[fl]
    else:
        g, exc, resto = grupos_acima_5000(n)
        faixa_txt = f"3.501 a 5.000 + {g} grupo(s)"
        memoria.append(f"N = {n} > 5.000: regra (**). Base = faixa 3.501 a 5.000 do GR {gr}.")
        memoria.append(f"Excedente = {n} − 5.000 = {exc}. Grupos completos de 4.000 = {exc//4000}; "
                       f"fração restante = {resto} ({'> 2.000: conta como grupo' if resto>2000 else '≤ 2.000: não conta'}). "
                       f"Total de grupos = {g}.")
        for p,(q,fl) in TABELA[gr][(3501,5000)].items():
            res[p]["quantidade"] = q
            res[p]["regime"] = FLAG_TXT[fl]
        for p,(q,fl) in TABELA[gr]["grupo"].items():
            res[p]["quantidade"] += q*g
            base = TABELA[gr][(3501,5000)].get(p)
            if base is None:
                res[p]["regime"] = FLAG_TXT[fl]
            res[p]["observacoes"].append(f"acréscimo por grupo: +{q} × {g} ({FLAG_TXT[fl]})")

    for p in PROFS:
        if res[p]["quantidade"] and res[p]["regime"] and p==AUX and "***" in (res[p]["regime"] or ""):
            res[p]["observacoes"].append("Opção do empregador (***): enfermeiro do trabalho em "
                                         "tempo parcial em substituição ao auxiliar/técnico.")
    if saude and n > 500:
        res[ENF]["observacoes"].append("Observação A do Anexo II: estabelecimento de saúde com mais de "
            "500 trabalhadores deve contratar enfermeiro do trabalho em TEMPO INTEGRAL "
            "(prevalece sobre o regime da tabela; se a tabela indicar 0, exige-se 1 em tempo integral).")
        if res[ENF]["quantidade"] == 0:
            res[ENF]["quantidade"] = 1
        res[ENF]["regime"] = "tempo integral (Observação A)"
        memoria.append("Aplicada a Observação A (estabelecimento de saúde, N > 500).")
    if saude:
        memoria.append("Observação B: em estabelecimento de saúde, o técnico de enfermagem do "
                       "trabalho deve ser supervisionado por enfermeiro do trabalho.")

    return {"grau_de_risco":gr, "num_trabalhadores":n, "faixa":faixa_txt,
            "memoria_de_calculo":memoria,
            "dimensionamento":{p:v for p,v in res.items()}}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("grau", type=int); ap.add_argument("n", type=int)
    ap.add_argument("--saude", action="store_true"); ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    r = dimensionar(a.grau, a.n, a.saude)
    if a.json:
        print(json.dumps(r, ensure_ascii=False, indent=2)); return
    print(f"SESMT — GR {r['grau_de_risco']}, {r['num_trabalhadores']} trabalhadores "
          f"(faixa: {r['faixa']})")
    for m in r["memoria_de_calculo"]: print(f"  · {m}")
    print("Dimensionamento mínimo:")
    for p,v in r["dimensionamento"].items():
        if v["quantidade"]:
            print(f"  ({v['quantidade']}) {p} — {v['regime']}")
            for o in v["observacoes"]: print(f"        {o}")
        else:
            print(f"  (0) {p} — não exigido")
    print(json.dumps(r, ensure_ascii=False))

if __name__ == "__main__":
    main()
