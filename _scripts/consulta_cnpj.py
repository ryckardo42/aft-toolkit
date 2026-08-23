#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
consulta_cnpj.py - consulta dados cadastrais de empresa na base da Receita
Federal (RFB) a partir do CNPJ, sem necessidade de login ou credencial.

Usa os dados abertos oficiais do CNPJ que a propria RFB publica, servidos por
API publica. Nao depende do SISFGTS, do Sistema Auditor nem de token do SIT.

Uso:
    python3 consulta_cnpj.py 00000000000191
    python3 consulta_cnpj.py 00.000.000/0001-91 --json
    python3 consulta_cnpj.py 00000000000191 --socios
    python3 consulta_cnpj.py --sem-cache 00000000000191

Cache: respostas ficam em ~/Documents/AFT/cache/cnpj/ para nao repetir consulta
da mesma empresa (mais rapido e reduz exposicao do CNPJ na rede).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

CACHE_DIR = Path.home() / "Documents" / "AFT" / "cache" / "cnpj"
TIMEOUT = 30

# Backends publicos servindo os dados abertos da RFB.
BACKENDS = [
    ("brasilapi",   "https://brasilapi.com.br/api/cnpj/v1/{cnpj}"),
    ("minhareceita", "https://minhareceita.org/{cnpj}"),
]


def _dv_ok(d: str) -> bool:
    """Confere os dois digitos verificadores do CNPJ."""
    def calc(base: str) -> str:
        pesos = list(range(2, 10))
        soma = 0
        for i, ch in enumerate(reversed(base)):
            soma += int(ch) * pesos[i % 8]
        r = soma % 11
        return "0" if r < 2 else str(11 - r)
    return d[12] == calc(d[:12]) and d[13] == calc(d[:13])


def limpar_cnpj(bruto: str) -> str:
    d = re.sub(r"\D", "", bruto or "")
    if len(d) != 14:
        raise SystemExit(f"CNPJ invalido: '{bruto}' (esperados 14 digitos, vieram {len(d)})")
    if not _dv_ok(d):
        raise SystemExit(f"CNPJ invalido: {formatar_cnpj(d)} - digito verificador nao confere. "
                         "Confira a digitacao.")
    return d


def formatar_cnpj(d: str) -> str:
    return f"{d[:2]}.{d[2:5]}.{d[5:8]}/{d[8:12]}-{d[12:]}"


def _buscar(url: str) -> dict:
    req = urllib.request.Request(url, headers={
        "Accept": "application/json",
        "User-Agent": "aft-toolkit/consulta_cnpj",
    })
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return json.loads(r.read().decode("utf-8"))


def consultar(cnpj: str, usar_cache=True) -> tuple[dict, str]:
    """Retorna (dados, origem). Tenta cache, depois cada backend em ordem."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache = CACHE_DIR / f"{cnpj}.json"

    if usar_cache and cache.exists():
        d = json.loads(cache.read_text(encoding="utf-8"))
        return d, f"cache ({d.get('_consultado_em','?')[:10]})"

    erros = []
    for nome, tpl in BACKENDS:
        try:
            d = _buscar(tpl.format(cnpj=cnpj))
            d["_backend"] = nome
            d["_consultado_em"] = datetime.now(timezone.utc).isoformat()
            cache.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
            return d, nome
        except urllib.error.HTTPError as e:
            if e.code in (400, 404):
                raise SystemExit(
                    f"CNPJ {formatar_cnpj(cnpj)} nao encontrado na base da RFB.\n"
                    "  (numero valido, mas sem registro - confira se e realmente esse CNPJ)")
            erros.append(f"{nome}: HTTP {e.code}")
        except Exception as e:  # rede, timeout, JSON
            erros.append(f"{nome}: {type(e).__name__}")
    raise SystemExit("Nenhum servico respondeu. Tentativas -> " + " | ".join(erros))


def g(d: dict, *chaves, padrao=""):
    """Primeiro valor nao vazio entre varias chaves (os backends divergem em nomes)."""
    for k in chaves:
        v = d.get(k)
        if v not in (None, "", []):
            return v
    return padrao


def exibir(d: dict, origem: str, mostrar_socios=False):
    cnpj = re.sub(r"\D", "", str(g(d, "cnpj", "estabelecimento", padrao="")))
    situacao = str(g(d, "descricao_situacao_cadastral", "situacao_cadastral")).upper()
    porte = str(g(d, "porte", "codigo_porte")).upper()
    simples = g(d, "opcao_pelo_simples")
    mei = g(d, "opcao_pelo_mei")

    print()
    print("=" * 72)
    print(f"  {g(d, 'razao_social', 'nome_empresarial')}")
    print("=" * 72)
    fant = g(d, "nome_fantasia")
    if fant:
        print(f"  Nome fantasia......: {fant}")
    print(f"  CNPJ...............: {formatar_cnpj(cnpj) if len(cnpj)==14 else cnpj}")

    marca = "" if situacao == "ATIVA" else "   <<< ATENCAO"
    print(f"  Situacao cadastral.: {situacao}{marca}")
    mot = g(d, "descricao_motivo_situacao_cadastral")
    if mot and str(mot).upper() not in ("SEM MOTIVO", ""):
        print(f"     motivo..........: {mot}")
    dtsit = g(d, "data_situacao_cadastral")
    if dtsit:
        print(f"     desde...........: {dtsit}")

    print(f"  Abertura...........: {g(d, 'data_inicio_atividade', 'data_abertura')}")
    print(f"  Natureza juridica..: {g(d, 'natureza_juridica')}")
    print(f"  Porte..............: {porte}")

    reg = []
    if simples is True:
        reg.append("Simples Nacional")
    if mei is True:
        reg.append("MEI")
    if reg:
        print(f"  Regime.............: {', '.join(reg)}")

    cnae = g(d, "cnae_fiscal")
    cnae_ds = g(d, "cnae_fiscal_descricao")
    if cnae:
        print(f"  CNAE principal.....: {cnae}  {cnae_ds}")
    sec = d.get("cnaes_secundarios") or []
    if sec:
        print(f"  CNAEs secundarios..: {len(sec)}")
        for c in sec[:5]:
            print(f"     {c.get('codigo')}  {str(c.get('descricao'))[:52]}")
        if len(sec) > 5:
            print(f"     (+{len(sec)-5} outros)")

    # endereco
    log = " ".join(str(x) for x in [g(d, "descricao_tipo_de_logradouro"), g(d, "logradouro")] if x)
    num = g(d, "numero")
    comp = g(d, "complemento")
    partes = [p for p in [f"{log}, {num}".strip(", "), comp, g(d, "bairro")] if p]
    print(f"  Endereco...........: {' - '.join(partes)}")
    print(f"                       {g(d,'municipio')}/{g(d,'uf')}  CEP {g(d,'cep')}")

    # a RFB guarda ate 3 numeros; o campo "fax" quase sempre e so um 2o telefone
    tels = [str(t).strip() for t in
            [g(d, "ddd_telefone_1"), g(d, "ddd_telefone_2"), g(d, "ddd_fax")] if t]
    tels = list(dict.fromkeys(tels))          # remove repetidos
    for i, t in enumerate(tels):
        rot = "Telefone" if i == 0 else "  tambem"
        print(f"  {rot}...........: {t}")
    if g(d, "email"):
        print(f"  E-mail.............: {g(d,'email')}")

    qsa = d.get("qsa") or []
    if qsa:
        print(f"  Quadro societario..: {len(qsa)} socio(s)" +
              ("" if mostrar_socios else "   (use --socios para listar)"))
        if mostrar_socios:
            for s in qsa:
                nome = g(s, "nome_socio", "nome")
                qual = g(s, "qualificacao_socio", "qualificacao")
                print(f"     - {nome}  ({qual})")

    print()
    print(f"  [origem: {origem} | dados abertos da RFB]")
    print()


# --- modo --os: campos prontos para o memory.md da OS -------------------------
def fmt_cnae(c) -> str:
    """7 digitos -> XXXX-X/XX (formato usado no memory.md e na NR-04)."""
    d = re.sub(r"\D", "", str(c or ""))
    return f"{d[:4]}-{d[4]}/{d[5:7]}" if len(d) == 7 else str(c or "")


def fmt_cep(c) -> str:
    d = re.sub(r"\D", "", str(c or ""))
    return f"{d[:5]}-{d[5:]}" if len(d) == 8 else str(c or "")


def fmt_tel(t) -> str:
    d = re.sub(r"\D", "", str(t or ""))
    if len(d) in (10, 11):
        return f"({d[:2]}) {d[2:-4]}-{d[-4:]}"
    return str(t or "")


def _data_br(iso) -> str:
    s = str(iso or "")
    if re.match(r"^\d{4}-\d{2}-\d{2}", s):
        a, m, dd = s[:10].split("-")
        return f"{dd}/{m}/{a}"
    return s


def modo_os(d: dict):
    """Imprime chave=valor com o que o memory.md da OS precisa.

    Só imprime linha de campo que tem valor - assim a skill não escreve campo
    vazio na ficha. Nada aqui decide nada: é dado bruto para o AFT conferir.
    """
    log = " ".join(str(x) for x in [g(d, "descricao_tipo_de_logradouro"), g(d, "logradouro")] if x)
    num = g(d, "numero")
    end = ", ".join(p for p in [f"{log}, {num}".strip(", "), g(d, "complemento"), g(d, "bairro")] if p)
    cep = fmt_cep(g(d, "cep"))
    if end and cep:
        end = f"{end}, CEP {cep}"

    tels = [fmt_tel(t) for t in
            [g(d, "ddd_telefone_1"), g(d, "ddd_telefone_2"), g(d, "ddd_fax")] if t]
    tels = list(dict.fromkeys(tels))

    sec = "; ".join(fmt_cnae(c.get("codigo")) for c in (d.get("cnaes_secundarios") or []))

    campos = [
        ("razao_social",       g(d, "razao_social")),
        ("nome_fantasia",      g(d, "nome_fantasia")),
        ("situacao",           str(g(d, "descricao_situacao_cadastral")).upper()),
        ("situacao_desde",     _data_br(g(d, "data_situacao_cadastral"))),
        ("abertura",           _data_br(g(d, "data_inicio_atividade"))),
        ("municipio",          g(d, "municipio")),
        ("uf",                 g(d, "uf")),
        ("cnae",               fmt_cnae(g(d, "cnae_fiscal"))),
        ("cnae_descricao",     g(d, "cnae_fiscal_descricao")),
        ("cnaes_secundarios",  sec),
        ("natureza_juridica",  g(d, "natureza_juridica")),
        ("porte",              str(g(d, "porte")).upper()),
        ("simples",            "sim" if g(d, "opcao_pelo_simples") is True else ""),
        ("mei",                "sim" if g(d, "opcao_pelo_mei") is True else ""),
        ("endereco",           end),
        ("telefone",           tels[0] if tels else ""),
        ("telefone2",          tels[1] if len(tels) > 1 else ""),
        ("email",              g(d, "email")),
        ("socios",             str(len(d.get("qsa") or []) or "")),
    ]
    for k, v in campos:
        if str(v).strip():
            print(f"{k}={v}")


def main():
    p = argparse.ArgumentParser(description="Consulta dados de CNPJ na base da RFB (dados abertos).")
    p.add_argument("cnpj", help="CNPJ com ou sem pontuacao")
    p.add_argument("--json", action="store_true", help="imprime o JSON completo")
    p.add_argument("--socios", action="store_true", help="lista o quadro societario")
    p.add_argument("--sem-cache", action="store_true", help="ignora o cache e consulta de novo")
    p.add_argument("--os", action="store_true",
                   help="saida chave=valor com os campos do memory.md (para as skills)")
    a = p.parse_args()

    cnpj = limpar_cnpj(a.cnpj)
    dados, origem = consultar(cnpj, usar_cache=not a.sem_cache)

    if a.json:
        print(json.dumps(dados, ensure_ascii=False, indent=2))
    elif a.os:
        modo_os(dados)
    else:
        exibir(dados, origem, mostrar_socios=a.socios)


if __name__ == "__main__":
    main()
