#!/usr/bin/env python3
"""
rehydrate.py — re-hidratação determinística de autos pseudonimizados (skill /gera-ai).

Troca os tokens [[AUTUADA]] / [[TRAB_NN]] / [[CPF_NN]] de um TXT tokenizado pelos
valores reais lidos de um mapa de-para JSON, produzindo o TXT real importável pelo
Sistema Auditor.

NUNCA é o modelo que faz a substituição — é este script, por string-replace exato,
para garantir a fidelidade do documento legal (um CPF/nome errado é inaceitável).

Uso:
    python3 rehydrate.py <tokenized.txt> <depara.json> <saida.txt>

Aborta (exit 1) se:
  - algum valor real do de-para estiver vazio;
  - algum CPF real não tiver exatamente 11 dígitos numéricos;
  - sobrar qualquer token [[...]] não resolvido no arquivo de saída.
"""
import json
import re
import sys

TOKEN_RE = re.compile(r"\[\[[A-Z0-9_]+\]\]")


def fail(msg):
    print(f"ERRO: {msg}", file=sys.stderr)
    sys.exit(1)


def build_mapping(depara):
    """Constrói dict token->valor real a partir do de-para, validando cada entrada."""
    mapping = {}

    autuada = depara.get("autuada") or {}
    tok = autuada.get("token")
    razao = autuada.get("razao_social")
    if tok:
        if not razao or not razao.strip():
            fail(f"razao_social vazia para o token {tok}")
        mapping[tok] = razao

    for i, trab in enumerate(depara.get("trabalhadores") or [], start=1):
        tok_nome = trab.get("token_nome")
        nome = trab.get("nome")
        tok_cpf = trab.get("token_cpf")
        cpf = trab.get("cpf")
        if tok_nome:
            if not nome or not nome.strip():
                fail(f"nome vazio para o token {tok_nome} (trabalhador #{i})")
            mapping[tok_nome] = nome
        if tok_cpf:
            if not (isinstance(cpf, str) and cpf.isdigit() and len(cpf) == 11):
                fail(
                    f"cpf inválido para o token {tok_cpf} (trabalhador #{i}): "
                    f"deve ser string de 11 dígitos, recebeu {cpf!r}"
                )
            mapping[tok_cpf] = cpf

    if not mapping:
        fail("de-para não contém nenhum token mapeável")
    return mapping


def main():
    if len(sys.argv) != 4:
        fail("uso: rehydrate.py <tokenized.txt> <depara.json> <saida.txt>")

    tokenized_path, depara_path, out_path = sys.argv[1:4]

    with open(tokenized_path, encoding="utf-8") as f:
        content = f.read()
    with open(depara_path, encoding="utf-8") as f:
        depara = json.load(f)

    mapping = build_mapping(depara)

    for token, real in mapping.items():
        content = content.replace(token, real)

    # Nenhum token órfão pode sobrar — TXT legal não pode conter placeholder.
    orphans = sorted(set(TOKEN_RE.findall(content)))
    if orphans:
        fail("tokens não resolvidos sobraram na saída: " + ", ".join(orphans))

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"OK: {len(mapping)} token(s) re-hidratado(s) -> {out_path}")


if __name__ == "__main__":
    main()
