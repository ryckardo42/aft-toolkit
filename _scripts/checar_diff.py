#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
checar_diff.py — guard-rail de supply-chain para a atualizacao do AFT Toolkit.

Antes de o /aft-atualizar rodar `git pull`, este script varre o que esta CHEGANDO
do repositorio (as linhas ADICIONADAS no diff HEAD..origin/main) a procura de sinais
de codigo malicioso que poderiam entrar numa atualizacao envenenada: caracteres
Unicode invisiveis (usados para esconder instrucoes do olho humano) e padroes de
exfiltracao / execucao remota (cano para shell, ANTHROPIC_BASE_URL, auto-aprovacao de
MCP, base64 escondido, etc.).

NAO bloqueia nada e NAO altera o repositorio: e um alarme. Le o diff, relata o que
achou em linguagem simples e termina com exit 0 (guard-rail nunca derruba o fluxo).
Cabe a skill PARAR e mostrar os achados ao AFT antes de dar o pull — uma atualizacao
de skills e um artefato de cadeia de suprimentos e merece a mesma desconfianca de
qualquer codigo de terceiro.

Uso (rode DEPOIS de `git fetch origin`):
    python checar_diff.py                 # diffa HEAD..origin/main no repo das skills
    python checar_diff.py <ref_base> <ref_topo>
    git diff HEAD..origin/main | python checar_diff.py -   # le o diff do stdin
"""
import re
import subprocess
import sys
from pathlib import Path

# Raiz das skills: avo deste arquivo (.../skills/_scripts/checar_diff.py).
SKILLS_DIR = Path(__file__).resolve().parent.parent

# Unicode invisivel / de controle de direcao: zero-width, word joiner, BOM e os
# bidi overrides (U+202A-202E). Humanos nao veem; o modelo le.
INVISIVEL_RE = re.compile(r"[​‌‍⁠﻿‪-‮]")

# Padroes de alto sinal numa ATUALIZACAO de skills/scripts. Cada um e (rotulo, regex).
PADROES = [
    ("redireciona a API da Anthropic", re.compile(r"ANTHROPIC_BASE_URL", re.I)),
    ("auto-aprova servidores MCP", re.compile(r"enableAllProjectMcpServers", re.I)),
    ("cano de download para shell", re.compile(r"(?:curl|wget|iwr|invoke-webrequest)[^\n|]*\|\s*(?:ba|z|tc|da)?sh\b", re.I)),
    ("baixa e executa script remoto", re.compile(r"(?:curl|wget)[^\n]*\bhttps?://[^\n]*\b(?:-o|>)\s*\S+\.(?:sh|ps1|py)\b", re.I)),
    ("decodifica conteudo escondido (base64)", re.compile(r"base64\s+(?:-d|--decode|-D)\b", re.I)),
    ("executa string dinamica", re.compile(r"\b(?:eval|exec)\s*\(\s*(?:base64|requests|urllib|os\.popen|subprocess)", re.I)),
    ("le credencial sensivel", re.compile(r"(?:id_rsa|id_ed25519|\.aws/credentials|\.ssh/)", re.I)),
    ("exfiltra por requisicao de rede", re.compile(r"(?:requests|urllib|httpx)\.(?:post|put)\s*\(", re.I)),
]


def linhas_adicionadas(diff):
    """Gera (arquivo, linha_diff_n, texto) de cada linha ADICIONADA no diff unificado.

    So as linhas que comecam com '+' (e nao o cabecalho '+++') interessam: e o
    conteudo novo que esta entrando. Linhas de contexto e removidas sao ignoradas.
    """
    arquivo = "?"
    for n, linha in enumerate(diff.splitlines(), start=1):
        if linha.startswith("+++ "):
            arquivo = linha[4:].lstrip("b/").strip() or "?"
            continue
        if linha.startswith("+") and not linha.startswith("+++"):
            yield arquivo, n, linha[1:]


def achados(diff):
    """Lista (arquivo, n, motivo, trecho) para cada linha adicionada suspeita."""
    out = []
    for arquivo, n, texto in linhas_adicionadas(diff):
        if INVISIVEL_RE.search(texto):
            out.append((arquivo, n, "Unicode invisivel/oculto", texto.strip()[:120]))
        for rotulo, rx in PADROES:
            if rx.search(texto):
                out.append((arquivo, n, rotulo, texto.strip()[:120]))
    return out


def obter_diff():
    """Resolve o diff a varrer: stdin (-), refs dadas, ou HEAD..origin/main."""
    args = sys.argv[1:]
    if args == ["-"]:
        return sys.stdin.read()
    if len(args) == 2:
        base, topo = args
    else:
        base, topo = "HEAD", "origin/main"
    try:
        out = subprocess.run(
            ["git", "-C", str(SKILLS_DIR), "diff", f"{base}..{topo}"],
            capture_output=True, text=True, timeout=30,
        )
    except (OSError, subprocess.SubprocessError) as e:
        print(f"aviso: nao consegui rodar o git diff ({e}). Pulei a varredura.", file=sys.stderr)
        return ""
    if out.returncode != 0:
        msg = (out.stderr or "").strip()
        print(f"aviso: git diff falhou ({msg}). Rodou `git fetch origin` antes?", file=sys.stderr)
        return ""
    return out.stdout


def main():
    diff = obter_diff()
    if not diff.strip():
        print("Nada a varrer (sem novidades no diff, ou git indisponivel).")
        sys.exit(0)

    encontrados = achados(diff)
    print()
    if not encontrados:
        print("✓ Varredura de seguranca: nada suspeito nas linhas que estao chegando.")
    else:
        print(f"⚠️  {len(encontrados)} sinal(is) suspeito(s) na atualizacao que esta chegando:")
        print()
        for arquivo, n, motivo, trecho in encontrados:
            print(f"  {arquivo}  [{motivo}]")
            print(f"    + {trecho}")
        print()
        print("   NAO de o `git pull` ainda. Mostre estes achados ao AFT e confirme que")
        print("   a atualizacao e legitima (autor/commit conhecido) antes de prosseguir.")
    sys.exit(0)


if __name__ == "__main__":
    main()
