# -*- coding: utf-8 -*-
"""
empacotar.py - Produz o pacote versionado do toolkit a partir do main.

Parte da migracao da distribuicao (issue #138): em vez de `git pull` num
repositorio publico, o AFT passa a atualizar por um pacote .zip carimbado com
versao, publicado no portal `notebooks-aft`. Este script cuida so do lado
"produzir o pacote" - subir para o portal e a rota autenticada sao trabalho
de outro repositorio.

Como ele funciona, em ordem:

  1. confere que a copia em --repo esta no main e sem trabalho em aberto -
     nunca empacota estado de worktree nem mudanca nao commitada;
  2. carimba a versao a partir do PROPRIO COMMIT de HEAD (data do commit +
     hash curto) - nao do relogio. E o que garante que rodar duas vezes no
     mesmo commit sempre produz a mesma versao;
  3. cria um worktree git DESCARTAVEL no mesmo commit (o padrao que o resto
     do toolkit ja usa para isolar sessoes - ver AGENTS.md) e roda a
     remontagem (remontar.py, issue #139) dentro dele: NOVIDADES.md,
     arquitetura.html e o manifesto skills_oficiais.txt saem em dia, sem
     tocar na copia original em --repo;
  4. escreve o carimbo de versao (_scripts/versao.txt) dentro do worktree;
  5. zipa o worktree - sem o .git do worktree, sem os arquivos que so fazem
     sentido no repositorio - e calcula o sha256 do pacote;
  6. remove o worktree descartavel.

Uso:
    python empacotar.py --repo <copia limpa do main> --saida <pasta>
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
import hashlib
import json
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from remontar import git, remontar, EXCLUIR  # noqa: E402  (path acima e proposital)

try:  # console do Windows e cp1252
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ARQUIVO_VERSAO = "versao.txt"


def _copia_limpa_do_main(raiz):
    ramo = git(["branch", "--show-current"], raiz)
    if ramo != "main":
        raise SystemExit(
            f"ERRO: {raiz} está no ramo '{ramo}', não em 'main'.\n"
            "  O pacote só pode ser montado a partir do main.")
    sujo = git(["status", "--porcelain"], raiz)
    if sujo:
        raise SystemExit(
            f"ERRO: {raiz} tem mudança não commitada:\n  " +
            "\n  ".join(sujo.splitlines()[:5]) +
            "\n  Empacotar exige uma cópia limpa do main - "
            "commite ou descarte antes de tentar de novo.")


def carimbo_versao(raiz):
    """(versao, commit, data) do HEAD de `raiz`. So olha metadados do proprio
    commit - nunca o relogio - para que empacotar duas vezes o mesmo commit
    sempre devolva a mesma versao."""
    commit = git(["rev-parse", "HEAD"], raiz)
    data = git(["show", "-s", "--format=%cs", "HEAD"], raiz)  # AAAA-MM-DD
    versao = f"{data.replace('-', '.')}-{commit[:7]}"
    return versao, commit, data


def _worktree_descartavel(raiz, commit):
    """Cria um worktree git desligado (--detach) de `raiz` no `commit`, numa
    pasta temporaria propria. Devolve o Path do worktree; quem chamar precisa
    remove-lo com `_remover_worktree` no final (inclusive em erro)."""
    base = Path(tempfile.mkdtemp(prefix="aft-empacotar-"))
    wt = base / "toolkit"
    git(["worktree", "add", "--detach", str(wt), commit], raiz)
    return wt, base


def _remover_worktree(raiz, wt, base):
    git(["worktree", "remove", "--force", str(wt)], raiz, checar=False)
    shutil.rmtree(base, ignore_errors=True)


def escrever_carimbo(worktree, versao, commit, data):
    texto = f"versao: {versao}\ncommit: {commit}\ndata: {data}\n"
    (worktree / "_scripts" / ARQUIVO_VERSAO).write_text(texto, encoding="utf-8")


def _arquivos_do_pacote(worktree):
    """Todo arquivo do worktree, exceto o que esta em EXCLUIR (por nome de
    qualquer componente do caminho)."""
    for caminho in sorted(worktree.rglob("*")):
        if caminho.is_dir():
            continue
        partes = caminho.relative_to(worktree).parts
        if any(p in EXCLUIR for p in partes):
            continue
        yield caminho


def montar_zip(worktree, destino_zip):
    with zipfile.ZipFile(destino_zip, "w", zipfile.ZIP_DEFLATED) as z:
        for caminho in _arquivos_do_pacote(worktree):
            z.write(caminho, caminho.relative_to(worktree))


def sha256_de(caminho):
    h = hashlib.sha256()
    with open(caminho, "rb") as f:
        for bloco in iter(lambda: f.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


def empacotar(raiz, pasta_saida):
    _copia_limpa_do_main(raiz)
    versao, commit, data = carimbo_versao(raiz)

    wt, base = _worktree_descartavel(raiz, commit)
    try:
        linhas, _ = remontar(wt, conferir=False)
        for l in linhas:
            print("  " + l)
        escrever_carimbo(wt, versao, commit, data)

        pasta_saida = Path(pasta_saida).expanduser()
        pasta_saida.mkdir(parents=True, exist_ok=True)
        zip_path = pasta_saida / f"aft-toolkit-{versao}.zip"
        montar_zip(wt, zip_path)
    finally:
        _remover_worktree(raiz, wt, base)

    soma = sha256_de(zip_path)
    (pasta_saida / f"{zip_path.name}.sha256").write_text(
        f"{soma}  {zip_path.name}\n", encoding="utf-8")
    return {"versao": versao, "commit": commit, "zip": str(zip_path),
            "sha256": soma}


def main():
    ap = argparse.ArgumentParser(
        description="Produz o pacote versionado do toolkit a partir do main")
    ap.add_argument("--repo", required=True, help="cópia limpa do main")
    ap.add_argument("--saida", required=True, help="pasta onde gravar o pacote")
    args = ap.parse_args()

    raiz = Path(args.repo).expanduser().resolve()
    if not (raiz / "AGENTS.md").is_file():
        raise SystemExit(f"ERRO: {raiz} não parece a raiz do AFT Toolkit "
                         "(falta o AGENTS.md).")

    info = empacotar(raiz, args.saida)
    print(json.dumps(info, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
