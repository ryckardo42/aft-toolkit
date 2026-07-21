#!/usr/bin/env python3
"""
Dimensionamento da CIPA — Quadro I da NR-05.
Cálculo determinístico a partir do grau de risco (1-4) e do número de empregados.

ATENÇÃO: os valores do Quadro I são POR REPRESENTAÇÃO (bancada), não o total da CIPA.
Como a CIPA é paritária, o total de integrantes é o DOBRO: metade eleita pelos
empregados, metade designada pelo empregador. O script devolve os dois níveis.

Uso:
    python3 dimensionar_cipa.py <grau_de_risco> <num_empregados> [--json]

Fonte dos dados: Quadro I da NR-05 (leitura visual da tabela oficial, célula a célula).
"""
import json, argparse

# (min, max, efetivos_por_bancada, suplentes_por_bancada). Faixas NÃO cumulativas.
FAIXAS = [(0,19),(20,29),(30,50),(51,80),(81,100),(101,120),(121,140),(141,300),
          (301,500),(501,1000),(1001,2500),(2501,5000),(5001,10000)]

TABELA = {
 1: {(0,19):(0,0), (20,29):(0,0), (30,50):(0,0), (51,80):(0,0), (81,100):(1,1),
     (101,120):(1,1), (121,140):(1,1), (141,300):(1,1), (301,500):(2,2),
     (501,1000):(4,3), (1001,2500):(5,4), (2501,5000):(6,5), (5001,10000):(8,6),
     "grupo":(1,1)},
 2: {(0,19):(0,0), (20,29):(0,0), (30,50):(0,0), (51,80):(1,1), (81,100):(1,1),
     (101,120):(2,1), (121,140):(2,1), (141,300):(3,2), (301,500):(4,3),
     (501,1000):(5,4), (1001,2500):(6,5), (2501,5000):(8,6), (5001,10000):(10,8),
     "grupo":(1,1)},
 3: {(0,19):(0,0), (20,29):(1,1), (30,50):(1,1), (51,80):(2,1), (81,100):(2,1),
     (101,120):(2,1), (121,140):(3,2), (141,300):(4,2), (301,500):(5,4),
     (501,1000):(6,4), (1001,2500):(8,6), (2501,5000):(10,8), (5001,10000):(12,8),
     "grupo":(2,2)},
 4: {(0,19):(0,0), (20,29):(1,1), (30,50):(2,1), (51,80):(3,2), (81,100):(3,2),
     (101,120):(4,2), (121,140):(4,2), (141,300):(4,3), (301,500):(5,4),
     (501,1000):(6,5), (1001,2500):(9,7), (2501,5000):(11,8), (5001,10000):(13,10),
     "grupo":(2,2)},
}

def fmt(x): return f"{x:,}".replace(",", ".")

def dimensionar(gr, n):
    if gr not in (1,2,3,4):
        raise ValueError("Grau de risco deve ser 1, 2, 3 ou 4.")
    if n < 0:
        raise ValueError("Número de empregados deve ser >= 0.")
    memoria = []
    if n <= 10000:
        faixa = next(f for f in FAIXAS if f[0] <= n <= f[1])
        ef, su = TABELA[gr][faixa]
        faixa_txt = f"{fmt(faixa[0])} a {fmt(faixa[1])}"
        memoria.append(f"N = {fmt(n)}: faixa aplicável (única, não cumulativa) = {faixa_txt}, GR {gr}.")
    else:
        exc = n - 10000
        g = -(-exc // 2500)   # cada grupo de 2.500 OU FRAÇÃO conta como 1 grupo
        ef_b, su_b = TABELA[gr][(5001,10000)]
        ef_g, su_g = TABELA[gr]["grupo"]
        ef, su = ef_b + ef_g*g, su_b + su_g*g
        faixa_txt = f"5.001 a 10.000 + {g} grupo(s)"
        memoria.append(f"N = {fmt(n)} > 10.000: base = faixa 5.001 a 10.000 do GR {gr} "
                       f"({ef_b} efetivos / {su_b} suplentes por bancada).")
        memoria.append(f"Excedente = {fmt(n)} − 10.000 = {fmt(exc)}. Cada grupo de 2.500 ou fração "
                       f"conta como 1 grupo → {g} grupo(s). Acréscimo: +{ef_g}/+{su_g} por grupo.")
        memoria.append(f"Por bancada: efetivos {ef_b} + ({ef_g} × {g}) = {ef}; "
                       f"suplentes {su_b} + ({su_g} × {g}) = {su}.")

    if ef == 0 and su == 0:
        memoria.append("Nesta combinação de grau de risco e faixa, o Quadro I não exige "
                       "dimensionamento de CIPA.")
    else:
        memoria.append("Paridade: o total da CIPA é o DOBRO do Quadro I — metade eleita pelos "
                       "empregados, metade designada pelo empregador.")

    return {"grau_de_risco":gr, "num_empregados":n, "faixa":faixa_txt,
            "memoria_de_calculo":memoria,
            "quadro_i_por_bancada":{"efetivos":ef, "suplentes":su},
            "composicao_paritaria_total":{
                "efetivos_total":ef*2, "efetivos_eleitos_pelos_empregados":ef,
                "efetivos_designados_pelo_empregador":ef,
                "suplentes_total":su*2, "suplentes_eleitos_pelos_empregados":su,
                "suplentes_designados_pelo_empregador":su}}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("grau", type=int); ap.add_argument("n", type=int)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    r = dimensionar(a.grau, a.n)
    if a.json:
        print(json.dumps(r, ensure_ascii=False, indent=2)); return
    q, p = r["quadro_i_por_bancada"], r["composicao_paritaria_total"]
    print(f"CIPA — GR {r['grau_de_risco']}, {fmt(r['num_empregados'])} empregados "
          f"(faixa: {r['faixa']})")
    for m in r["memoria_de_calculo"]: print(f"  · {m}")
    print(f"Quadro I (POR BANCADA): ({q['efetivos']}) efetivos e ({q['suplentes']}) suplentes")
    if q["efetivos"] or q["suplentes"]:
        print("Composição paritária total da CIPA:")
        print(f"  Efetivos: {p['efetivos_total']} no total — "
              f"({p['efetivos_eleitos_pelos_empregados']}) eleitos pelos empregados + "
              f"({p['efetivos_designados_pelo_empregador']}) designados pelo empregador")
        print(f"  Suplentes: {p['suplentes_total']} no total — "
              f"({p['suplentes_eleitos_pelos_empregados']}) eleitos pelos empregados + "
              f"({p['suplentes_designados_pelo_empregador']}) designados pelo empregador")
    print(json.dumps(r, ensure_ascii=False))

if __name__ == "__main__":
    main()
