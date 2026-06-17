#!/usr/bin/env python3
"""
validar_txt.py — validacao pre-importacao do TXT do Sistema Auditor (skill /gera-ai).

Confere o arquivo .txt ANTES de o AFT tentar importar no Sistema Auditor, pegando
em segundos os erros que, de outro modo, so apareceriam como "AI RECUSADO" la dentro
(ex.: CEP vazio, numero de campos errado, ementa malformada, anexo inexistente).

Roda sobre o TXT REAL (latin-1) ja re-hidratado. Tambem aceita o .tokenized.txt
(UTF-8) para uma checagem estrutural antecipada — nesse caso campos com tokens
[[...]] sao tratados como preenchidos.

Uso:
    python validar_txt.py <arquivo.txt>

Saida: relatorio legivel. Exit 0 = tudo ok; exit 1 = ha erro que o Sistema Auditor
recusaria (lista cada AI problematico no mesmo estilo do aviso do sistema).
"""
import os
import re
import sys

try:  # console do Windows (cp1252) nao deve derrubar o relatorio
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

TOKEN = re.compile(r"\[\[[A-Z0-9_]+\]\]")


def is_filled(v):
    """Campo preenchido: nao-vazio ou contendo token (sera re-hidratado)."""
    return bool(v and (v.strip() or TOKEN.search(v)))


def only_digits(v):
    return re.sub(r"\D", "", v or "")


def main():
    if len(sys.argv) != 2:
        print("uso: python validar_txt.py <arquivo.txt>", file=sys.stderr)
        sys.exit(2)

    path = sys.argv[1]
    if not os.path.isfile(path):
        print(f"ERRO: arquivo nao encontrado: {path}", file=sys.stderr)
        sys.exit(2)

    # TXT real do Sistema Auditor e latin-1; o tokenizado e UTF-8. Tentamos os dois.
    raw = open(path, "rb").read()
    try:
        text = raw.decode("utf-8-sig")  # remove BOM se houver
    except UnicodeDecodeError:
        text = raw.decode("latin-1")
    text = text.lstrip("﻿")

    # Cada caractere precisa caber em latin-1 (o Sistema Auditor so aceita esse encoding).
    erros = []
    avisos = []
    for i, ch in enumerate(text):
        try:
            ch.encode("latin-1")
        except UnicodeEncodeError:
            ctx = text[max(0, i - 15):i + 15].replace("\n", " ")
            erros.append(f"Caractere fora do latin-1 (pos {i}): ...{ctx}... "
                         f"(troque travessao/aspas curvas/emoji por equivalente simples)")
            break

    linhas = [l for l in text.split("\n") if l != ""]
    if not linhas:
        print("ERRO: arquivo vazio.", file=sys.stderr)
        sys.exit(1)

    n_tipo1 = 0
    n_tipo6 = 0
    bloco_atual = None  # (cnpj, ementa) para rotular erros do AI corrente

    for ln, linha in enumerate(linhas, start=1):
        campos = linha.split("\t")
        tipo = campos[0]

        if tipo == "1":
            n_tipo1 += 1
            ident = only_digits(campos[1]) if len(campos) > 1 else ""
            ementa = campos[12] if len(campos) > 12 else "?"
            bloco_atual = (ident or "?", ementa)
            rotulo = f"AI CNPJ/CPF:{ident or '?'} Ementa:{ementa}"

            if len(campos) != 23:
                erros.append(f"{rotulo} -> linha tipo 1 com {len(campos)} campos "
                             f"(esperado 23 / 22 tabs).")
            # Identificador: 11 (CPF/CAEPF) ou 14 (CNPJ) digitos.
            if len(ident) not in (11, 14):
                erros.append(f"{rotulo} -> Erro: identificador CNPJ/CPF invalido "
                             f"('{campos[1] if len(campos)>1 else ''}'): "
                             f"deve ter 11 (CPF/CAEPF) ou 14 (CNPJ) digitos.")
            # Razao social (campo 3).
            if len(campos) > 2 and not is_filled(campos[2]):
                erros.append(f"{rotulo} -> Erro: razao social/nome nao informado!")
            # CEP (campo 8) — causa classica de 'AI RECUSADO'.
            if len(campos) > 7 and not is_filled(campos[7]):
                erros.append(f"{rotulo} -> Erro: CEP nao informado! AI seria RECUSADO.")
            # Ementa sem hifen (campo 13 / cod_3): 7 digitos.
            if len(campos) > 12:
                cod3 = campos[12]
                if not re.fullmatch(r"\d{7}", cod3):
                    erros.append(f"{rotulo} -> Erro: codigo de ementa '{cod3}' invalido "
                                 f"(esperado 7 digitos, ementa sem hifen).")

        elif tipo == "5":
            rotulo = (f"AI CNPJ/CPF:{bloco_atual[0]} Ementa:{bloco_atual[1]}"
                      if bloco_atual else f"linha {ln}")
            if len(campos) < 3:
                erros.append(f"{rotulo} -> linha tipo 5 (anexo) malformada "
                             f"({len(campos)} campos, esperado 3).")
            else:
                anexo = campos[1]
                if not TOKEN.search(anexo) and not os.path.isfile(anexo):
                    erros.append(f"{rotulo} -> Erro: anexo nao encontrado no disco: {anexo}")
                if not anexo.upper().endswith(".PDF"):
                    avisos.append(f"{rotulo} -> anexo nao termina em .PDF maiusculo: {anexo}")

        elif tipo == "4":
            rotulo = (f"AI CNPJ/CPF:{bloco_atual[0]} Ementa:{bloco_atual[1]}"
                      if bloco_atual else f"linha {ln}")
            if len(campos) < 5:
                erros.append(f"{rotulo} -> linha tipo 4 (trabalhador) com poucos campos "
                             f"({len(campos)}).")
            else:
                cpf = campos[3]
                if cpf and not TOKEN.search(cpf) and len(only_digits(cpf)) != 11:
                    erros.append(f"{rotulo} -> Erro: CPF de trabalhador invalido "
                                 f"('{cpf}'): 11 digitos.")
                if not is_filled(campos[4]):
                    avisos.append(f"{rotulo} -> data de admissao do trabalhador vazia "
                                  f"(campo obrigatorio no Sistema Auditor).")

        elif tipo == "6":
            n_tipo6 += 1
            cif = only_digits(campos[1]) if len(campos) > 1 else ""
            if len(cif) != 6:
                erros.append(f"Linha tipo 6 (CIF) invalida: '{campos[1] if len(campos)>1 else ''}' "
                             f"(esperado 6 digitos).")

    if n_tipo1 == 0:
        erros.append("Nenhuma linha tipo 1 (auto) encontrada.")
    if n_tipo6 != 1:
        erros.append(f"Esperada exatamente 1 linha tipo 6 (CIF) ao final; "
                     f"encontradas {n_tipo6}.")

    print(f"Arquivo: {path}")
    print(f"Autos (linhas tipo 1): {n_tipo1}")
    if avisos:
        print(f"\nAVISOS ({len(avisos)}):")
        for a in avisos:
            print("  - " + a)
    if erros:
        print(f"\nERROS ({len(erros)}) - o Sistema Auditor recusaria a importacao:")
        for e in erros:
            print("  X " + e)
        print("\nRESULTADO: REPROVADO. Corrija os erros acima antes de importar.")
        sys.exit(1)
    print("\nRESULTADO: APROVADO. O TXT esta integro para importacao no Sistema Auditor.")
    sys.exit(0)


if __name__ == "__main__":
    main()
