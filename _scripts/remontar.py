# -*- coding: utf-8 -*-
"""
remontar.py - O passo de remontagem do publicar.py, isolado para ter um
segundo chamador.

O publicar.py sempre fez tres coisas num lugar so, antes de copiar para a
pasta instalada: remontar o NOVIDADES.md a partir de novidades/, sincronizar
o bloco ARCH do arquitetura.html com o arquitetura.json, e regerar o
manifesto _scripts/skills_oficiais.txt a partir de `git ls-files`. O
empacotador do toolkit (que vai gerar o pacote versionado a partir do main)
precisa exatamente dos mesmos tres arquivos em dia antes de zipar - por isso
este passo agora mora aqui, importavel por quem precisar, em vez de dentro
do publicar.py.

Este modulo NAO commita, NAO empurra para o GitHub e NAO toca em nenhuma
pasta instalada: so escreve os tres arquivos MONTADOS dentro da `raiz` que
foi passada, e devolve um relatorio do que mudou para quem chamou decidir o
proximo passo (o publicar.py commita e empurra; o empacotador nao precisa).

Uso isolado, sem tocar em nada:
    python remontar.py --conferir --repo <pasta>
Uso isolado, regravando os arquivos (sem commit):
    python remontar.py --repo <pasta>
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
import subprocess
import sys
from pathlib import Path

try:  # console do Windows e cp1252
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# Os tres arquivos que este passo mantem em dia - usado tanto para regerar o
# manifesto quanto para quem chamou decidir se ha algo para commitar.
MONTADOS = ["NOVIDADES.md", "arquitetura/arquitetura.html",
            "_scripts/skills_oficiais.txt"]

# O que nao vai para fora do repositorio: controle de versao, lixo do sistema
# e o roteiro de instalacao (que so faz sentido aqui dentro). Usado tanto
# pelo publicar.py (copia para a pasta instalada) quanto pelo empacotar.py
# (zip do pacote) - um lugar so, para os dois nunca divergirem no que excluem.
EXCLUIR = {".git", ".gitignore", ".DS_Store", ".backups", ".claude",
           "COMO-INSTALAR.md", "__pycache__", ".github"}


def git(args, cwd, checar=True):
    r = subprocess.run(["git"] + args, cwd=str(cwd), capture_output=True,
                       text=True, encoding="utf-8", errors="replace")
    if checar and r.returncode != 0:
        raise SystemExit(f"ERRO: git {' '.join(args)}\n{r.stderr.strip()}")
    return r.stdout.strip()


def python_atual():
    return sys.executable or "python3"


def rodar_script(raiz, nome, args, conferir):
    script = raiz / "_scripts" / nome
    if not script.is_file():
        return f"{nome}: não encontrado (pulado)"
    if conferir:
        return f"{nome}: rodaria agora"
    r = subprocess.run([python_atual(), str(script)] + args,
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace")
    bruto = (r.stdout or r.stderr).strip()
    saida = bruto.splitlines()
    ultima = saida[-1] if saida else f"terminou ({r.returncode})"
    # Scripts que respondem em JSON: uns numa linha so (instalar_agentes), outros
    # indentado em varias (instalar_servidor_painel) - neste, a ultima linha e um
    # "}" solto, que nao diz nada ao AFT. Tenta a saida INTEIRA antes da ultima.
    for candidato in (bruto, ultima):
        if not candidato.startswith("{"):
            continue
        try:
            d = json.loads(candidato)
        except ValueError:
            continue
        partes = [f"{len(d[k])} {k}" for k in
                  ("instalados", "atualizados", "em_dia", "erros")
                  if isinstance(d.get(k), list) and d[k]]
        ultima = ", ".join(partes) or d.get("detalhe") or "nada a fazer"
        break
    return f"{nome}: {ultima}"


def regenerar_manifesto(raiz):
    """Regrava _scripts/skills_oficiais.txt a partir de `git ls-files` em
    `raiz`. E ela que diz o que NAO e nosso e, portanto, nao pode ser apagado
    da pasta do AFT numa atualizacao; deduzir por prefixo falha, porque
    'aft-grant' e skill pessoal de um AFT e parece oficial."""
    oficiais = sorted({l.split("/")[0] for l in
                       git(["ls-files"], raiz).splitlines() if "/" in l})
    (raiz / "_scripts" / "skills_oficiais.txt").write_text(
        "\n".join(oficiais) + "\n", encoding="utf-8")
    return oficiais


def remontar(raiz, conferir=False):
    """Remonta o NOVIDADES.md, sincroniza a arquitetura e - se `conferir` for
    False - regenera o manifesto skills_oficiais.txt dentro de `raiz`.

    Devolve (linhas, mudou): `linhas` e a lista de textos prontos para
    imprimir (sem indentacao - quem chamou decide o layout); `mudou` e a
    lista de linhas do `git status --porcelain` para os MONTADOS (vazia se
    nada mudou, ou sempre vazia em modo `conferir`, que nunca escreve nada).
    """
    linhas = [
        rodar_script(raiz, "montar_novidades.py",
                     ["--conferir" if conferir else "--montar"], False)
        .replace("montar_novidades.py: ", "NOVIDADES.md: "),
        rodar_script(raiz, "nota_historico.py",
                     ["--checar-arquitetura" if conferir
                      else "--sincronizar-arquitetura"], False)
        .replace("nota_historico.py: ", "arquitetura: "),
    ]
    if conferir:
        return linhas, []
    regenerar_manifesto(raiz)
    bruto = git(["status", "--porcelain", "--"] + MONTADOS, raiz)
    mudou = [l.strip() for l in bruto.splitlines()] if bruto else []
    return linhas, mudou


def main():
    ap = argparse.ArgumentParser(
        description="Remonta NOVIDADES.md, arquitetura e o manifesto - isolado, sem "
                    "commitar nem tocar em pasta instalada")
    ap.add_argument("--conferir", action="store_true",
                    help="so mostra o que seria feito, sem alterar nada")
    ap.add_argument("--repo", required=True, help="raiz do repositorio")
    args = ap.parse_args()

    raiz = Path(args.repo).expanduser().resolve()
    if not (raiz / "AGENTS.md").is_file():
        raise SystemExit(f"ERRO: {raiz} não parece a raiz do AFT Toolkit "
                         "(falta o AGENTS.md).")

    linhas, mudou = remontar(raiz, conferir=args.conferir)
    for l in linhas:
        print(l)
    if mudou:
        print("mudou: " + ", ".join(mudou))
    elif not args.conferir:
        print("nada mudou")


if __name__ == "__main__":
    main()
