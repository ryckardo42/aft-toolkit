#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""cnpjs_endereco.py — enriquece uma lista de CNPJs e aponta indícios de grupo
econômico no mesmo endereço.

Trabalha em duas frentes, combináveis:

  · CNPJs passados na linha de comando: consulta cada um na API aberta
    minhareceita.org (fallback: BrasilAPI) e obtém endereço completo, CNAE,
    telefone, e-mail, sócios e data de abertura. Só o CNPJ (dado público) é
    enviado; nada da fiscalização sai da máquina.
  · `--parse <arquivo.txt>`: lê uma consulta de sistema interno que o AFT colou
    em arquivo (blocos com "CNPJ:", "Razão Social:", "Endereço:"...) e extrai
    os mesmos campos, sem rede nenhuma.

Depois, o DETECTOR (100% local) compara tudo:

  · normaliza o endereço (QUADRA027 == QUADRA 27 == QD 27; LOTE 0001 == LT 1)
    e separa "mesmo endereço" de "mesmo CEP, endereço distinto";
  · marca CNAE de apoio administrativo / fornecimento de mão de obra
    (assinatura clássica da interposição de pessoa jurídica);
  · aponta telefone, e-mail, domínio de e-mail e sócios compartilhados
    entre CNPJs formalmente distintos, e as datas de abertura escalonadas.

A saída é um relatório compacto de INDÍCIOS, a confirmar em campo — quem
conclui é o AFT. O script nunca imprime CPF (nem o mascarado das APIs).

Uso:
    python cnpjs_endereco.py --alvo <cnpj> <cnpj> <cnpj> ...
    python cnpjs_endereco.py --parse "consulta.txt" [--alvo <cnpj>] [<cnpj> ...]
    python cnpjs_endereco.py ... --json
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
import time
import unicodedata
import urllib.error
import urllib.request
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):     # console cp1252 no Windows
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# CNAEs cuja concentração num mesmo endereço é a assinatura da interposição
# de mão de obra por pessoa jurídica ("pejotização" em série).
CNAES_APOIO = {
    "8219999": "apoio administrativo",
    "8211300": "serviços combinados de escritório",
    "7820500": "locação de mão de obra temporária",
    "7830200": "fornecimento e gestão de recursos humanos",
}

# Domínios de e-mail públicos: tê-los em comum não indica nada.
DOMINIOS_PUBLICOS = {
    "gmail.com", "hotmail.com", "outlook.com", "yahoo.com", "yahoo.com.br",
    "uol.com.br", "bol.com.br", "terra.com.br", "icloud.com", "live.com",
}

TIPOS_LOGRADOURO = {
    "RUA", "R", "AVENIDA", "AV", "ALAMEDA", "AL", "TRAVESSA", "TV", "RODOVIA",
    "ROD", "ESTRADA", "EST", "PRACA", "PC", "EIXO", "VIA", "QUADRA", "Q",
}


def _norm(texto):
    """Maiúsculas, sem acento, espaços colapsados."""
    if not texto:
        return ""
    texto = unicodedata.normalize("NFKD", str(texto))
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", texto).strip().upper()


def _so_digitos(texto):
    return re.sub(r"\D", "", str(texto or ""))


def _fmt_cnpj(digitos):
    d = _so_digitos(digitos).zfill(14)
    return f"{d[0:2]}.{d[2:5]}.{d[5:8]}/{d[8:12]}-{d[12:14]}"


def _fmt_data(iso_ou_br):
    """'2021-06-29' -> '29/06/2021'; datas já em dd/mm/aaaa passam direto."""
    if not iso_ou_br:
        return ""
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", str(iso_ou_br))
    if m:
        return f"{m.group(3)}/{m.group(2)}/{m.group(1)}"
    return str(iso_ou_br)


def _ano(data_br):
    m = re.search(r"(\d{4})\s*$", data_br or "")
    return int(m.group(1)) if m else None


# ---------------------------------------------------------------- consultas

def _http_json(url, timeout=25):
    req = urllib.request.Request(url, headers={"User-Agent": "aft-toolkit/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _registro_vazio(cnpj):
    return {
        "cnpj": _so_digitos(cnpj).zfill(14), "razao_social": "", "fantasia": "",
        "situacao": "", "logradouro": "", "numero": "", "complemento": "",
        "bairro": "", "municipio": "", "uf": "", "cep": "", "telefones": [],
        "emails": [], "cnae": "", "cnae_desc": "", "abertura": "", "porte": "",
        "socios": [], "fonte": "",
    }


def consultar_cnpj(cnpj):
    """minhareceita.org com fallback BrasilAPI. Devolve registro ou None."""
    d = _so_digitos(cnpj).zfill(14)
    for nome, url in (("minhareceita.org", f"https://minhareceita.org/{d}"),
                      ("BrasilAPI", f"https://brasilapi.com.br/api/cnpj/v1/{d}")):
        try:
            dado = _http_json(url)
        except Exception:
            continue
        if not dado or not dado.get("razao_social"):
            continue
        reg = _registro_vazio(d)
        reg["fonte"] = nome
        reg["razao_social"] = dado.get("razao_social") or ""
        reg["fantasia"] = dado.get("nome_fantasia") or ""
        reg["situacao"] = dado.get("descricao_situacao_cadastral") or ""
        tipo = dado.get("descricao_tipo_de_logradouro") or ""
        reg["logradouro"] = f"{tipo} {dado.get('logradouro') or ''}".strip()
        reg["numero"] = str(dado.get("numero") or "")
        reg["complemento"] = dado.get("complemento") or ""
        reg["bairro"] = dado.get("bairro") or ""
        reg["municipio"] = dado.get("municipio") or ""
        reg["uf"] = dado.get("uf") or ""
        reg["cep"] = _so_digitos(dado.get("cep"))
        for campo in ("ddd_telefone_1", "ddd_telefone_2"):
            tel = _so_digitos(dado.get(campo))
            if len(tel) >= 8:
                reg["telefones"].append(tel)
        email = (dado.get("email") or "").strip().lower()
        if email:
            reg["emails"].append(email)
        reg["cnae"] = str(dado.get("cnae_fiscal") or "")
        reg["cnae_desc"] = dado.get("cnae_fiscal_descricao") or ""
        reg["abertura"] = _fmt_data(dado.get("data_inicio_atividade"))
        reg["porte"] = dado.get("porte") or ""
        for socio in dado.get("qsa") or []:
            nome_socio = _norm(socio.get("nome_socio") or socio.get("nome") or "")
            if nome_socio:
                reg["socios"].append(nome_socio)
        return reg
    return None


# ------------------------------------------------------------------- parse

RE_CNPJ = re.compile(r"\b(\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2})\b")

CAMPOS_TXT = {
    "razao_social": r"Raz[aã]o Social\s*:\s*(.+)",
    "fantasia": r"Nome Fantasia\s*:\s*(.+)",
    "endereco": r"Endere[cç]o\s*:\s*(.+)",
    "bairro": r"Bairro\s*:\s*(.+)",
    "situacao": r"Sit\.?\s*Cadastral\s*:\s*(\S+)",
    "telefone": r"Telefone\s*:\s*([\d\s().-]+)",
    "email": r"E-?MAIL\s*:\s*(\S+)",
    "cnae": r"CNAE\s*:\s*(\d{7})",
    "abertura": r"In[ií]cio de Ativ\.?\s*:\s*(\d{2}/\d{2}/\d{4})",
}


def parse_texto(caminho):
    """Extrai registros de uma consulta de sistema interno colada em arquivo.

    O texto é dividido pelos CNPJs encontrados; cada bloco é lido pelos rótulos
    usuais ("Razão Social:", "Endereço:", "Município: ... UF:GO CEP:...").
    Campos que não existirem ficam vazios. Nunca captura CPF.
    """
    texto = Path(caminho).read_text(encoding="utf-8", errors="replace")
    achados = list(RE_CNPJ.finditer(texto))
    registros = []
    for i, m in enumerate(achados):
        fim = achados[i + 1].start() if i + 1 < len(achados) else len(texto)
        bloco = texto[m.end():fim]
        reg = _registro_vazio(m.group(1))
        reg["fonte"] = "texto colado"
        for campo, padrao in CAMPOS_TXT.items():
            mm = re.search(padrao, bloco, re.IGNORECASE)
            if not mm:
                continue
            valor = mm.group(1).strip()
            if campo == "endereco":
                reg["logradouro"] = valor          # vem tudo numa linha só
            elif campo == "telefone":
                tel = _so_digitos(valor)
                if len(tel) >= 8:
                    reg["telefones"].append(tel)
            elif campo == "email":
                reg["emails"].append(valor.lower())
            else:
                reg[campo] = valor
        mm = re.search(r"Munic[ií]pio\s*:\s*(?:\d+\s*-\s*)?(.+?)\s+UF\s*:\s*(\w{2})\s+CEP\s*:\s*(\d{5}-?\d{3})",
                       bloco, re.IGNORECASE)
        if mm:
            reg["municipio"], reg["uf"] = mm.group(1).strip(), mm.group(2)
            reg["cep"] = _so_digitos(mm.group(3))
        registros.append(reg)
    # dedup por CNPJ (o mesmo pode aparecer citado duas vezes no texto)
    vistos, unicos = set(), []
    for reg in registros:
        if reg["cnpj"] not in vistos:
            vistos.add(reg["cnpj"])
            unicos.append(reg)
    return unicos


# ---------------------------------------------------------------- detector

def chave_endereco(reg):
    """Chave normalizada do ponto: quadra+lote quando existirem, senão
    logradouro+número. QUADRA027/QD 27 e LOTE 0001/LT 1 viram a mesma chave."""
    texto = _norm(" ".join([reg["logradouro"], reg["numero"], reg["complemento"]]))
    quadra = re.search(r"\b(?:QUADRA|QDA|QD|Q)\.?\s*0*(\d+)", texto)
    lote = re.search(r"\b(?:LOTE|LT)\.?\s*0*(\d+)", texto)
    if quadra and lote:
        return f"CEP {reg['cep']} Q{quadra.group(1)} L{lote.group(1)}"
    palavras = [p for p in _norm(reg["logradouro"]).replace(",", " ").split()
                if p not in TIPOS_LOGRADOURO]
    numero = _so_digitos(reg["numero"]) or "SN"
    return f"CEP {reg['cep']} {' '.join(palavras)} N{numero}"


def _dominio(email):
    return email.rsplit("@", 1)[-1] if "@" in email else ""


def detectar(registros, alvo=None):
    """Cruza os registros e devolve a estrutura de indícios."""
    alvo = _so_digitos(alvo or "").zfill(14) if alvo else None
    reg_alvo = next((r for r in registros if r["cnpj"] == alvo), None)

    compartilhados = {"telefones": {}, "emails": {}, "dominios": {}, "socios": {}}
    for reg in registros:
        for tel in reg["telefones"]:
            compartilhados["telefones"].setdefault(tel, []).append(reg["cnpj"])
        for email in reg["emails"]:
            compartilhados["emails"].setdefault(email, []).append(reg["cnpj"])
            dom = _dominio(email)
            if dom and dom not in DOMINIOS_PUBLICOS:
                compartilhados["dominios"].setdefault(dom, []).append(reg["cnpj"])
        for socio in reg["socios"]:
            compartilhados["socios"].setdefault(socio, []).append(reg["cnpj"])
    # sinal so conta entre RAIZES de CNPJ distintas: matriz e filial da mesma
    # empresa compartilharem telefone ou socio e obvio, nao e indicio.
    for grupo in compartilhados.values():
        for chave in list(grupo):
            grupo[chave] = sorted(set(grupo[chave]))
            if len({c[:8] for c in grupo[chave]}) < 2:
                del grupo[chave]

    chave_alvo = chave_endereco(reg_alvo) if reg_alvo else None
    for reg in registros:
        reg["chave_endereco"] = chave_endereco(reg)
        reg["mesmo_endereco_alvo"] = bool(chave_alvo) and reg["chave_endereco"] == chave_alvo
        reg["cnae_apoio"] = CNAES_APOIO.get(_so_digitos(reg["cnae"]))
        sinais = []
        if reg["cnae_apoio"]:
            sinais.append(f"CNAE de {reg['cnae_apoio']}")
        if any(reg["cnpj"] in c for c in compartilhados["telefones"].values()):
            sinais.append("telefone compartilhado")
        if any(reg["cnpj"] in c for c in compartilhados["emails"].values()):
            sinais.append("e-mail compartilhado")
        elif any(reg["cnpj"] in c for c in compartilhados["dominios"].values()):
            sinais.append("dominio de e-mail compartilhado")
        if any(reg["cnpj"] in c for c in compartilhados["socios"].values()):
            sinais.append("socio em comum")
        reg["sinais"] = sinais

    return {"alvo": alvo, "registros": registros, "compartilhados": compartilhados}


# --------------------------------------------------------------- relatório

def _linha_registro(reg, nomes):
    partes = [f"{_fmt_cnpj(reg['cnpj'])}  {reg['razao_social'] or '(razao social nao obtida)'}"]
    detalhes = []
    if reg["situacao"]:
        detalhes.append(reg["situacao"])
    if reg["cnae"]:
        cnae = f"CNAE {reg['cnae']}"
        if reg["cnae_apoio"]:
            cnae += f" ({reg['cnae_apoio']})"
        detalhes.append(cnae)
    if reg["abertura"]:
        detalhes.append(f"abertura {reg['abertura']}")
    if reg["porte"]:
        detalhes.append(reg["porte"])
    if detalhes:
        partes.append("   " + " | ".join(detalhes))
    endereco = re.sub(r"\s+", " ", " ".join(
        x for x in [reg["logradouro"], reg["numero"], reg["complemento"]] if x))
    if endereco:
        partes.append(f"   {endereco} - CEP {reg['cep']}")
    if reg["sinais"]:
        partes.append("   [!] " + "; ".join(reg["sinais"]))
    return "\n".join(partes)


def imprimir_relatorio(resultado, falhas):
    registros = resultado["registros"]
    comp = resultado["compartilhados"]
    nomes = {r["cnpj"]: (r["razao_social"] or _fmt_cnpj(r["cnpj"])) for r in registros}
    alvo = next((r for r in registros if r["cnpj"] == resultado["alvo"]), None)

    print(f"CNPJs analisados: {len(registros)}")
    if falhas:
        print(f"AVISO: sem dados para {len(falhas)} CNPJ(s) "
              f"(APIs indisponiveis): {', '.join(_fmt_cnpj(c) for c in falhas)}")
    print()

    if alvo:
        print("=== ALVO DA FISCALIZACAO ===")
        print(_linha_registro(alvo, nomes))
        print()
        mesmo = [r for r in registros if r["mesmo_endereco_alvo"] and r is not alvo]
        outros = [r for r in registros if not r["mesmo_endereco_alvo"] and r is not alvo]
        print(f"=== NO MESMO ENDERECO DO ALVO ({len(mesmo)}) ===")
        for reg in sorted(mesmo, key=lambda r: r["abertura"][-4:] if r["abertura"] else ""):
            print(_linha_registro(reg, nomes))
        if outros:
            print()
            print(f"=== MESMO CEP, ENDERECO DISTINTO ({len(outros)}) ===")
            for reg in outros:
                print(_linha_registro(reg, nomes))
    else:
        print("=== CNPJS ANALISADOS (sem alvo definido) ===")
        for reg in registros:
            print(_linha_registro(reg, nomes))

    tem_sinal = any([comp["telefones"], comp["emails"], comp["dominios"], comp["socios"]])
    apoio = [r for r in registros if r["cnae_apoio"]]
    if tem_sinal or len(apoio) >= 2:
        print()
        print("=== INDICIOS DE POSSIVEL GRUPO ECONOMICO ===")
        def _lista(cnpjs):
            return "; ".join(dict.fromkeys(nomes[c] for c in cnpjs))
        for tel, cnpjs in comp["telefones"].items():
            print(f"- Telefone {tel} compartilhado por: " + _lista(cnpjs))
        for email, cnpjs in comp["emails"].items():
            print(f"- E-mail {email} compartilhado por: " + _lista(cnpjs))
        for dom, cnpjs in comp["dominios"].items():
            print(f"- Dominio de e-mail @{dom} compartilhado por: " + _lista(cnpjs))
        for socio, cnpjs in comp["socios"].items():
            print(f"- Socio em comum ({socio}): " + _lista(cnpjs))
        if len(apoio) >= 2:
            anos = sorted({str(_ano(r["abertura"])) for r in apoio if _ano(r["abertura"])})
            print(f"- {len(apoio)} CNPJs de apoio administrativo / mao de obra no local, "
                  f"abertos em: {', '.join(anos) if anos else 'datas nao obtidas'}")
    print()
    print("Indicios extraidos de dados cadastrais publicos - a confirmar em campo. "
          "Quem conclui e o AFT.")


# --------------------------------------------------------------------- cli

def main():
    ap = argparse.ArgumentParser(description="CNPJs no mesmo endereco + detector de grupo economico")
    ap.add_argument("cnpjs", nargs="*", help="CNPJs a consultar nas APIs publicas")
    ap.add_argument("--alvo", help="CNPJ da empresa da OS (referencia da comparacao)")
    ap.add_argument("--parse", help="arquivo .txt com consulta de sistema interno colada")
    ap.add_argument("--json", action="store_true", help="saida estruturada em JSON")
    args = ap.parse_args()

    registros, falhas = [], []
    if args.parse:
        registros.extend(parse_texto(args.parse))

    pendentes = [_so_digitos(c).zfill(14) for c in args.cnpjs]
    if args.alvo and _so_digitos(args.alvo).zfill(14) not in (
            [r["cnpj"] for r in registros] + pendentes):
        pendentes.append(_so_digitos(args.alvo).zfill(14))
    ja_tem = {r["cnpj"] for r in registros}
    for cnpj in pendentes:
        if cnpj in ja_tem:
            continue
        reg = consultar_cnpj(cnpj)
        if reg:
            registros.append(reg)
            ja_tem.add(cnpj)
        else:
            falhas.append(cnpj)
        time.sleep(0.4)                      # cortesia com as APIs abertas

    if not registros:
        print("NENHUM_REGISTRO: nada foi obtido (APIs fora do ar ou arquivo sem CNPJs).")
        sys.exit(0)

    resultado = detectar(registros, alvo=args.alvo)
    if args.json:
        print(json.dumps({"falhas": falhas, **resultado}, ensure_ascii=False, indent=1))
    else:
        imprimir_relatorio(resultado, falhas)


if __name__ == "__main__":
    main()
