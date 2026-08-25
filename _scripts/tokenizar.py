#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Monta e confere o mapa de-para (.depara_[CNPJ].json) de uma OS, por script.

Fecha o lado que faltava da pseudonimizacao. O toolkit ja tinha o sentido de
VOLTA -- rehydrate.py, que troca [[TRAB_NN]] pelo nome real no TXT final, por
string-replace deterministico, "NUNCA e o modelo que faz a substituicao... um
CPF/nome errado e inaceitavel". O sentido de IDA (criar o mapa e trocar o nome
pelo token) nao tinha script nenhum: sobrava para o assistente digitar o nome a
mao no JSON. Este script tira o modelo desse caminho.

O que NAO faz, de proposito:
  - nao le PDF nem adivinha nomes: quem informa o nome e o AFT (ou uma lista que
    ele aponte), porque errar um nome aqui contamina o auto;
  - nao coleta CPF de trabalhador (o /aft-gera-ai nao usa: campo fica vazio);
  - nao renumera token existente, nunca -- token ja usado num auto e imutavel.

Uso:
  tokenizar.py <pasta-OS> --add "NOME COMPLETO" [--funcao X] [--admissao dd/mm/aaaa]
                          [--fonte "de onde veio o nome"]
  tokenizar.py <pasta-OS> --add-lista <arquivo.txt>   (um nome por linha; aceita
                          "NOME;funcao;dd/mm/aaaa")
  tokenizar.py <pasta-OS> --autuada "RAZAO SOCIAL LTDA"
  tokenizar.py <pasta-OS> --substituir <arquivo>      (troca nomes reais por tokens)
  tokenizar.py <pasta-OS> --conferir <arquivo>        (token orfao? nome real vazado?)
  tokenizar.py <pasta-OS> --listar [--mostrar]        (mascarado por padrao)

Exit 0 = ok; 1 = achado que exige acao; 2 = erro de uso.
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
import io
import json
import re
import sys
import unicodedata
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

RE_TOKEN_TRAB = re.compile(r"\[\[TRAB_(\d{2})\]\]")
RE_QUALQUER_TOKEN = re.compile(r"\[\[[A-Z0-9_]+\]\]")
RE_CPF = re.compile(r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b")


def normaliza(nome):
    """Para comparar nomes sem depender de acento, caixa ou espaco duplo."""
    s = unicodedata.normalize("NFKD", nome)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", s).strip().upper()


def mascara(nome):
    partes = nome.split()
    if not partes:
        return "?"
    return partes[0] + " " + " ".join(p[0] + "." for p in partes[1:])


def acha_cnpj(pasta):
    """CNPJ pelo front-matter do memory.md; se nao houver, pelo nome da pasta."""
    mem = pasta / "memory.md"
    if mem.is_file():
        m = re.search(r'^cnpj:\s*"?(\d{11,14})"?', mem.read_text(encoding="utf-8"), re.M)
        if m:
            return m.group(1)
    m = re.search(r"(\d{14}|\d{11})\s*$", pasta.name)
    if m:
        return m.group(1)
    return None


def carrega(caminho):
    if caminho.is_file():
        return json.loads(caminho.read_text(encoding="utf-8"))
    return {"autuada": {}, "trabalhadores": []}


def grava(caminho, mapa):
    caminho.write_text(json.dumps(mapa, ensure_ascii=False, indent=2), encoding="utf-8")


def proximo_token(mapa):
    usados = set()
    for t in mapa.get("trabalhadores", []):
        m = RE_TOKEN_TRAB.match(t.get("token_nome", ""))
        if m:
            usados.add(int(m.group(1)))
    n = 1
    while n in usados:
        n += 1
    if n > 99:
        print("ERRO: mais de 99 trabalhadores; o formato do token e de 2 digitos.",
              file=sys.stderr)
        sys.exit(2)
    return "[[TRAB_%02d]]" % n


def add(mapa, nome, funcao, admissao, fonte):
    """Devolve (token, ja_existia). Nome ja mapeado reaproveita o token."""
    if RE_CPF.search(nome):
        print("ERRO: o nome contem algo com cara de CPF. CPF de trabalhador nao "
              "entra no de-para (o /aft-gera-ai deixa o campo vazio).", file=sys.stderr)
        sys.exit(2)
    alvo = normaliza(nome)
    if not alvo:
        print("ERRO: nome vazio.", file=sys.stderr)
        sys.exit(2)
    for t in mapa.setdefault("trabalhadores", []):
        if normaliza(t.get("nome", "")) == alvo:
            return t["token_nome"], True
    token = proximo_token(mapa)
    entrada = {"token_nome": token, "nome": nome.strip()}
    if funcao:
        entrada["funcao"] = funcao
    if admissao:
        entrada["admissao"] = admissao
    if fonte:
        entrada["fonte"] = fonte
    mapa["trabalhadores"].append(entrada)
    return token, False


def substituir(mapa, caminho):
    """Troca nome real por token, do mais longo para o mais curto (para 'Joao
    Silva Souza' nao virar '[[TRAB_01]] Souza' quando 'Joao Silva' tambem estiver
    mapeado). Casa tambem a forma sem acento e em qualquer caixa."""
    texto = caminho.read_text(encoding="utf-8")
    pares = []
    raz = (mapa.get("autuada") or {}).get("razao_social")
    if raz:
        pares.append((raz, mapa["autuada"]["token"]))
    for t in mapa.get("trabalhadores", []):
        pares.append((t["nome"], t["token_nome"]))
    pares.sort(key=lambda par: len(par[0]), reverse=True)

    trocas = 0
    for real, token in pares:
        # casamento tolerante a acento/caixa/espaco duplo, sem heuristica de apelido
        padrao = r"\s+".join(re.escape(p) for p in real.split())
        padrao = "".join(
            "[%s%s]" % (c.lower(), c.upper()) if c.isalpha() and c.isascii() else c
            for c in padrao)
        novo, n = re.subn(padrao, token.replace("\\", "\\\\"), texto)
        if n == 0:
            # tenta pela forma sem acento (documento as vezes traz sem)
            sem = normaliza(real)
            padrao2 = r"\s+".join(re.escape(p) for p in sem.split())
            novo, n = re.subn(padrao2, token, texto, flags=re.I)
        texto, trocas = novo, trocas + n
    caminho.write_text(texto, encoding="utf-8")
    return trocas


def conferir(mapa, caminho):
    """Token sem par no mapa, e nome real que vazou para o arquivo tokenizado."""
    texto = caminho.read_text(encoding="utf-8")
    conhecidos = {t["token_nome"] for t in mapa.get("trabalhadores", [])}
    raz_tok = (mapa.get("autuada") or {}).get("token")
    if raz_tok:
        conhecidos.add(raz_tok)
    orfaos = sorted(set(RE_QUALQUER_TOKEN.findall(texto)) - conhecidos)

    vazados = []
    for t in mapa.get("trabalhadores", []):
        if normaliza(t["nome"]) in normaliza(texto):
            vazados.append(mascara(t["nome"]))
    return orfaos, vazados, RE_CPF.findall(texto)


def main():
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("pasta_os")
    # Numa OS de GRUPO ECONOMICO a mesma pasta abriga mais de um CNPJ (cada empresa
    # com seu RI e seus autos). O de-para e por CNPJ, entao e preciso poder apontar
    # qual: sem isso, o mapa da segunda empresa teria de ser escrito a mao -- que e
    # exatamente o que este script existe para evitar.
    ap.add_argument("--cnpj", metavar="CNPJ14",
                    help="CNPJ do de-para, quando a OS tem mais de uma empresa "
                         "(grupo economico). Padrao: o CNPJ da propria OS.")
    ap.add_argument("--add", metavar="NOME")
    ap.add_argument("--add-lista", metavar="ARQUIVO")
    ap.add_argument("--autuada", metavar="RAZAO_SOCIAL")
    ap.add_argument("--funcao", default=None)
    ap.add_argument("--admissao", default=None)
    ap.add_argument("--fonte", default=None)
    ap.add_argument("--substituir", metavar="ARQUIVO")
    ap.add_argument("--conferir", metavar="ARQUIVO")
    ap.add_argument("--listar", action="store_true")
    ap.add_argument("--mostrar", action="store_true",
                    help="revela os nomes no --listar (dado sensivel)")
    args = ap.parse_args()

    pasta = Path(args.pasta_os)
    if not pasta.is_dir():
        print("ERRO: pasta nao encontrada: %s" % pasta, file=sys.stderr)
        return 2
    cnpj = re.sub(r"\D", "", args.cnpj) if args.cnpj else acha_cnpj(pasta)
    if args.cnpj and len(cnpj) not in (11, 14):
        print("ERRO: --cnpj deve ter 11 ou 14 digitos.", file=sys.stderr)
        return 2
    if not cnpj:
        print("ERRO: nao consegui descobrir o CNPJ (front-matter `cnpj:` do memory.md "
              "ou final do nome da pasta).", file=sys.stderr)
        return 2
    caminho = pasta / (".depara_%s.json" % cnpj)
    mapa = carrega(caminho)
    mudou = False

    if args.autuada:
        mapa["autuada"] = {"token": "[[AUTUADA]]", "razao_social": args.autuada.strip()}
        mudou = True
        print("autuada -> [[AUTUADA]]")

    if args.add:
        tok, existia = add(mapa, args.add, args.funcao, args.admissao, args.fonte)
        mudou = True
        print("%s -> %s%s" % (mascara(args.add), tok, "  (ja existia)" if existia else ""))

    if args.add_lista:
        for linha in io.open(args.add_lista, encoding="utf-8"):
            linha = linha.strip()
            if not linha or linha.startswith("#"):
                continue
            campos = [c.strip() for c in linha.split(";")]
            nome = campos[0]
            funcao = campos[1] if len(campos) > 1 and campos[1] else args.funcao
            adm = campos[2] if len(campos) > 2 and campos[2] else args.admissao
            tok, existia = add(mapa, nome, funcao, adm, args.fonte)
            mudou = True
            print("%s -> %s%s" % (mascara(nome), tok, "  (ja existia)" if existia else ""))

    if mudou:
        grava(caminho, mapa)
        print("gravado: %s" % caminho.name)

    if args.listar:
        print("\nde-para (%d trabalhador(es)):" % len(mapa.get("trabalhadores", [])))
        raz = (mapa.get("autuada") or {}).get("razao_social")
        if raz:
            print("  [[AUTUADA]]  %s" % (raz if args.mostrar else mascara(raz)))
        for t in mapa.get("trabalhadores", []):
            nome = t["nome"] if args.mostrar else mascara(t["nome"])
            extra = " | %s" % t["funcao"] if t.get("funcao") else ""
            print("  %s  %s%s" % (t["token_nome"], nome, extra))
        if not args.mostrar:
            print("  (nomes mascarados; --mostrar revela, mas o de-para e dado sensivel)")

    if args.substituir:
        alvo = Path(args.substituir)
        if not alvo.is_file():
            print("ERRO: arquivo nao encontrado: %s" % alvo, file=sys.stderr)
            return 2
        n = substituir(mapa, alvo)
        print("substituicoes em %s: %d" % (alvo.name, n))

    if args.conferir:
        alvo = Path(args.conferir)
        if not alvo.is_file():
            print("ERRO: arquivo nao encontrado: %s" % alvo, file=sys.stderr)
            return 2
        orfaos, vazados, cpfs = conferir(mapa, alvo)
        print("\nconferencia de %s" % alvo.name)
        print("  tokens sem par no de-para: %s" % (", ".join(orfaos) if orfaos else "nenhum"))
        print("  nomes reais no arquivo   : %s" % (", ".join(vazados) if vazados else "nenhum"))
        print("  CPF no arquivo           : %d" % len(cpfs))
        if orfaos or vazados or cpfs:
            print("  RESULTADO: REPROVADO - resolva antes de empacotar.")
            return 1
        print("  RESULTADO: APROVADO.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
