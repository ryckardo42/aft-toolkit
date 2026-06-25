#!/usr/bin/env python3
"""
checar_pii.py — guard-rail de PII de alto dano (CPF / PIS-PASEP) para o AFT Toolkit.

Varre um texto, arquivo ou pasta de OS à procura de CPF e PIS/PASEP — os dois
únicos dados de pessoa natural com formato fixo e dígito verificador, logo os
únicos detectáveis com certeza por regra determinística. Para cada número
encontrado, valida o DV (só reporta o que é matematicamente um CPF/PIS real,
o que elimina quase todo falso-positivo) e avisa o auditor.

NÃO é anonimizador: não troca, não bloqueia, não toca em nada. É um alarme —
existe para pegar o único cenário de risco real: um CPF digitado por engano
que escaparia da tokenização e seguiria em texto claro. Cabe ao AFT decidir.

Por escolha de escopo, NÃO detecta nome, e-mail nem telefone: nome de
trabalhador em contexto é dado pessoal de baixo dano, e detecção de nome só
seria possível por modelo probabilístico — justamente o risco que este
guard-rail evita. CNPJ (14 dígitos) é pessoa jurídica, fora da LGPD, ignorado.

Uso (Windows / Git Bash):
    python checar_pii.py <arquivo.md | pasta_da_OS>        # varre arquivo ou pasta
    python checar_pii.py <...> --depara <depara.json>      # marca o que já está no mapa
    echo "texto" | python checar_pii.py -                  # varre o stdin

Sempre termina com exit 0 (é guard-rail, não bloqueio).
"""
import json
import re
import sys
from pathlib import Path

# 11 dígitos, cada um podendo ser seguido de um separador comum (. - espaço).
# As âncoras (?<!\d) e (?!\d) impedem capturar 11 dígitos de dentro de um
# CNPJ (14 dígitos) ou de qualquer número mais longo.
CANDIDATO_RE = re.compile(r"(?<!\d)(?:\d[.\s-]?){10}\d(?!\d)")

EXTENSOES = {".md", ".txt"}


def so_digitos(s):
    return re.sub(r"\D", "", s)


def cpf_valido(d):
    """d: string de 11 dígitos. True se o DV confere (e não é repetição)."""
    if len(d) != 11 or d == d[0] * 11:
        return False
    for tam in (9, 10):
        soma = sum(int(d[i]) * (tam + 1 - i) for i in range(tam))
        dv = (soma * 10) % 11
        dv = 0 if dv == 10 else dv
        if dv != int(d[tam]):
            return False
    return True


def pis_valido(d):
    """d: string de 11 dígitos. True se o DV do PIS/PASEP confere."""
    if len(d) != 11 or d == d[0] * 11:
        return False
    pesos = [3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    soma = sum(int(d[i]) * pesos[i] for i in range(10))
    dv = 11 - (soma % 11)
    dv = 0 if dv in (10, 11) else dv
    return dv == int(d[10])


def classificar(d):
    """Retorna 'CPF', 'PIS', 'CPF/PIS' ou None para um bloco de 11 dígitos."""
    rotulos = []
    if cpf_valido(d):
        rotulos.append("CPF")
    if pis_valido(d):
        rotulos.append("PIS")
    return "/".join(rotulos) if rotulos else None


def cpfs_do_depara(depara_path):
    """Lê os CPFs já mapeados no de-para da OS (só dígitos), para marcar como conhecidos."""
    try:
        with open(depara_path, encoding="utf-8") as f:
            depara = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        print(f"aviso: não consegui ler o de-para {depara_path}: {e}", file=sys.stderr)
        return set()
    conhecidos = set()
    for trab in depara.get("trabalhadores") or []:
        cpf = so_digitos(str(trab.get("cpf") or ""))
        if cpf:
            conhecidos.add(cpf)
    return conhecidos


def achados_no_texto(texto):
    """Gera (linha, trecho, rotulo, digitos) para cada PII válida no texto."""
    for n, linha in enumerate(texto.splitlines(), start=1):
        for m in CANDIDATO_RE.finditer(linha):
            d = so_digitos(m.group())
            rotulo = classificar(d)
            if rotulo:
                yield n, m.group(), rotulo, d


def coletar_fontes(alvo):
    """Resolve o alvo num [(rótulo_de_origem, texto)]."""
    if alvo == "-":
        return [("<stdin>", sys.stdin.read())]
    p = Path(alvo)
    if not p.exists():
        print(f"ERRO: caminho não encontrado: {alvo}", file=sys.stderr)
        sys.exit(0)  # guard-rail nunca derruba o fluxo
    if p.is_file():
        return [(str(p), p.read_text(encoding="utf-8", errors="replace"))]
    fontes = []
    for arq in sorted(p.rglob("*")):
        if arq.is_file() and arq.suffix.lower() in EXTENSOES:
            fontes.append((str(arq), arq.read_text(encoding="utf-8", errors="replace")))
    return fontes


def main():
    args = sys.argv[1:]
    depara_path = None
    if "--depara" in args:
        i = args.index("--depara")
        try:
            depara_path = args[i + 1]
        except IndexError:
            print("ERRO: --depara exige um caminho", file=sys.stderr)
            sys.exit(0)
        args = args[:i] + args[i + 2:]

    if len(args) != 1:
        print(__doc__.strip())
        sys.exit(0)

    conhecidos = cpfs_do_depara(depara_path) if depara_path else set()
    fontes = coletar_fontes(args[0])

    total = 0
    for origem, texto in fontes:
        for linha, trecho, rotulo, digitos in achados_no_texto(texto):
            total += 1
            if digitos in conhecidos:
                marca = "[já no de-para]"
            elif depara_path:
                marca = "[SOLTO — não está no de-para]"
            else:
                marca = ""
            print(f"  {origem}:{linha}  {rotulo} {trecho.strip()}  {marca}".rstrip())

    print()
    if total == 0:
        print("✓ Nenhum CPF/PIS detectado.")
    else:
        print(f"⚠️  {total} ocorrência(s) de PII de alto dano (CPF/PIS) detectada(s).")
        if depara_path:
            print("   Confirme que os números marcados [SOLTO] entram no de-para antes do /gera-ai.")
        else:
            print("   Confirme que cada um está tokenizado no de-para antes de gerar o TXT.")

    sys.exit(0)


if __name__ == "__main__":
    main()
