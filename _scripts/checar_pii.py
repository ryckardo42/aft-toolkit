#!/usr/bin/env python3
"""
checar_pii.py — guard-rail de PII (CPF / PIS-PASEP / contato) para o AFT Toolkit.

Varre um texto, arquivo ou pasta de OS à procura de:

  - CPF e PIS/PASEP — dados de pessoa natural com formato fixo e dígito
    verificador: para cada número encontrado, valida o DV (só reporta o que é
    matematicamente um CPF/PIS real, o que elimina quase todo falso-positivo);
  - e-mail e telefone brasileiro com DDD (10-11 dígitos) — detectáveis por
    padrão com boa precisão. Existem para pegar um contato de pessoa física
    (tipicamente o DENUNCIANTE) que escape para um arquivo de trabalho. O
    telefone/e-mail da própria empresa é esperado em vários arquivos — passe-o
    em --ignorar para não gerar alarme. O rótulo TELEFONE? leva "?" porque um
    número de 10-11 dígitos pode não ser telefone: é aviso, não certeza.

NÃO é anonimizador: não troca, não bloqueia, não toca em nada. É um alarme —
cabe ao AFT decidir. Nome de pessoa continua fora do escopo: detecção de nome
só seria possível por modelo probabilístico — justamente o risco que este
guard-rail evita. CNPJ (14 dígitos) é pessoa jurídica, fora da LGPD, ignorado.

Uso (Windows / Git Bash):
    python checar_pii.py <arquivo.md | pasta_da_OS>        # varre arquivo ou pasta
    python checar_pii.py <...> --depara <depara.json>      # marca o que já está no mapa
    python checar_pii.py <...> --ignorar 6299990000,contato@empresa.com.br
                                                           # contatos esperados (empresa)
    echo "texto" | python checar_pii.py -                  # varre o stdin

Sempre termina com exit 0 (é guard-rail, não bloqueio).
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

import json
import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# 11 dígitos, cada um podendo ser seguido de um separador comum (. - espaço).
# As âncoras (?<!\d) e (?!\d) impedem capturar 11 dígitos de dentro de um
# CNPJ (14 dígitos) ou de qualquer número mais longo.
CANDIDATO_RE = re.compile(r"(?<!\d)(?:\d[.\s-]?){10}\d(?!\d)")

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9][A-Za-z0-9.-]*\.[A-Za-z]{2,}")

# Telefone brasileiro COM DDD: (62) 99999-0000 · 62 3299-0000 · +55 62 99999-0000.
# Exige o DDD (10-11 dígitos no total): número sem DDD (8-9 dígitos) colidiria
# com CEP e outros números comuns. Celular = 9 + 8 dígitos; fixo começa em 2-5.
FONE_RE = re.compile(
    r"(?<!\d)(?:\+?55[\s.-]?)?\(?[1-9]\d\)?[\s.-]?(?:9\d{4}|[2-5]\d{3})[\s.-]?\d{4}(?!\d)"
)

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
        ocupado = []  # spans já reportados como CPF/PIS (evita duplicar como TELEFONE?)
        for m in CANDIDATO_RE.finditer(linha):
            d = so_digitos(m.group())
            rotulo = classificar(d)
            if rotulo:
                ocupado.append(m.span())
                yield n, m.group(), rotulo, d
        for m in EMAIL_RE.finditer(linha):
            yield n, m.group(), "E-MAIL", m.group().lower()
        for m in FONE_RE.finditer(linha):
            if any(a < m.end() and m.start() < b for a, b in ocupado):
                continue
            yield n, m.group(), "TELEFONE?", so_digitos(m.group())


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


def normalizar_ignorado(item):
    """Normaliza um item de --ignorar: e-mail em minúsculas, telefone só dígitos."""
    item = item.strip().lower()
    return item if "@" in item else so_digitos(item)


def esta_ignorado(rotulo, chave, ignorados):
    """True se o achado (e-mail/telefone) é um contato esperado (--ignorar)."""
    if rotulo == "E-MAIL":
        return chave in ignorados
    if rotulo == "TELEFONE?":
        # aceita com ou sem o +55 na frente
        return chave in ignorados or (chave.startswith("55") and chave[2:] in ignorados)
    return False


def main():
    args = sys.argv[1:]
    depara_path = None
    ignorados = set()
    for flag in ("--depara", "--ignorar"):
        if flag in args:
            i = args.index(flag)
            try:
                valor = args[i + 1]
            except IndexError:
                print(f"ERRO: {flag} exige um valor", file=sys.stderr)
                sys.exit(0)
            if flag == "--depara":
                depara_path = valor
            else:
                ignorados = {normalizar_ignorado(v) for v in valor.split(",") if v.strip()}
            args = args[:i] + args[i + 2:]

    if len(args) != 1:
        print(__doc__.strip())
        sys.exit(0)

    conhecidos = cpfs_do_depara(depara_path) if depara_path else set()
    fontes = coletar_fontes(args[0])

    total_docs = 0     # CPF/PIS
    total_contato = 0  # e-mail / telefone
    for origem, texto in fontes:
        for linha, trecho, rotulo, chave in achados_no_texto(texto):
            if rotulo in ("E-MAIL", "TELEFONE?"):
                if esta_ignorado(rotulo, chave, ignorados):
                    continue
                total_contato += 1
                marca = "[contato de pessoa? confira — denunciante nunca fica em .md]"
            else:
                total_docs += 1
                if chave in conhecidos:
                    marca = "[já no de-para]"
                elif depara_path:
                    marca = "[SOLTO — não está no de-para]"
                else:
                    marca = ""
            print(f"  {origem}:{linha}  {rotulo} {trecho.strip()}  {marca}".rstrip())

    print()
    if total_docs == 0 and total_contato == 0:
        print("✓ Nenhum CPF/PIS, e-mail ou telefone detectado.")
    if total_docs:
        print(f"⚠️  {total_docs} ocorrência(s) de PII de alto dano (CPF/PIS) detectada(s).")
        if depara_path:
            print("   Confirme que os números marcados [SOLTO] entram no de-para antes do /aft-gera-ai.")
        else:
            print("   Confirme que cada um está tokenizado no de-para antes de gerar o TXT.")
    if total_contato:
        print(f"⚠️  {total_contato} contato(s) (e-mail/telefone) detectado(s).")
        print("   Se for da própria empresa, tudo bem (use --ignorar para silenciar);")
        print("   contato de pessoa física (ex.: denunciante) não pode ficar no arquivo.")

    sys.exit(0)


if __name__ == "__main__":
    main()
