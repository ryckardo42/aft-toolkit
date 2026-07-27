#!/usr/bin/env python3
"""
Enquadramento CNAE → Grau de Risco (Anexo I da NR-04).

Uso:
    python3 enquadrar_cnae.py <cnae>            # busca por código, em qualquer formato
    python3 enquadrar_cnae.py --busca "termo"   # busca textual na denominação
    [--json]                                    # saída apenas em JSON

Formatos de código aceitos (todos normalizados para a classe XX.XX-X do Anexo I):
    01.15-6 | 0115-6 | 0115600 | 0115-6/00 | 01156 | 3250-7/01 etc.
O Anexo I usa o nível de CLASSE (5 dígitos + verificador). Subclasses (formato
XXXX-X/XX) são reduzidas à classe correspondente.

Base de dados: cnae_gr.json — 673 códigos, gerada do Anexo I da NR-04 e validada
integralmente contra o PDF oficial (zero divergências).
"""
import sys, os, json, re, argparse, unicodedata

AQUI = os.path.dirname(os.path.abspath(__file__))
DB = json.load(open(os.path.join(AQUI, "cnae_gr.json"), encoding="utf-8"))

def sem_acento(s):
    return unicodedata.normalize("NFD", s).encode("ascii","ignore").decode().lower()

def normalizar_codigo(entrada):
    """Extrai os dígitos e devolve a classe no formato XX.XX-X, ou None."""
    dig = re.sub(r"\D", "", entrada)
    if len(dig) < 5:
        return None
    d = dig[:5]  # classe = 4 dígitos + verificador; subclasse tem 7 dígitos
    return f"{d[0:2]}.{d[2:4]}-{d[4]}"

def por_codigo(entrada):
    cod = normalizar_codigo(entrada)
    if cod is None:
        return {"erro": f"'{entrada}' não contém um código CNAE reconhecível (mínimo 5 dígitos)."}
    reg = DB.get(cod)
    if reg is None:
        return {"erro": f"Classe {cod} não consta no Anexo I da NR-04. Confira o código "
                        f"(a tabela usa a CNAE 2.0 em nível de classe).",
                "codigo_normalizado": cod}
    return {"codigo_informado": entrada, "classe_cnae": cod,
            "denominacao": reg["denominacao"], "grau_de_risco": reg["gr"],
            "fonte": "Anexo I da NR-04"}

def por_texto(termo, limite=15):
    t = sem_acento(termo)
    palavras = t.split()
    resultados = []
    for cod, reg in DB.items():
        den = sem_acento(reg["denominacao"])
        if all(p in den for p in palavras):
            resultados.append({"classe_cnae": cod, "denominacao": reg["denominacao"],
                               "grau_de_risco": reg["gr"]})
    resultados.sort(key=lambda r: (len(r["denominacao"]), r["classe_cnae"]))
    return {"termo": termo, "total": len(resultados), "resultados": resultados[:limite]}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cnae", nargs="?", help="código CNAE em qualquer formato")
    ap.add_argument("--busca", help="busca textual na denominação")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    if not a.cnae and not a.busca:
        ap.error("informe um código CNAE ou --busca \"termo\"")
    r = por_texto(a.busca) if a.busca else por_codigo(a.cnae)
    if a.json:
        print(json.dumps(r, ensure_ascii=False, indent=2)); return
    if "erro" in r:
        print(f"⚠ {r['erro']}"); sys.exit(1)
    if "resultados" in r:
        print(f"Busca por \"{r['termo']}\" — {r['total']} resultado(s):")
        for x in r["resultados"]:
            print(f"  {x['classe_cnae']}  GR {x['grau_de_risco']}  {x['denominacao']}")
        if r["total"] > len(r["resultados"]):
            print(f"  ... e mais {r['total']-len(r['resultados'])}. Refine o termo.")
    else:
        print(f"CNAE {r['classe_cnae']} — {r['denominacao']}")
        print(f"Grau de Risco: {r['grau_de_risco']} (Anexo I da NR-04)")
    print("Lembrete (item 4.5.1 da NR-04): para dimensionar o SESMT, aplica-se o MAIOR grau "
          "de risco entre a atividade econômica principal e a preponderante no estabelecimento.")
if __name__ == "__main__":
    main()
