# -*- coding: utf-8 -*-
"""
publicar.py - Levar o toolkit ate a maquina do AFT, sempre a partir do main.

O PERIGO QUE ESTE SCRIPT RESOLVE e silencioso. Cada sessao do assistente
trabalha numa copia propria do repositorio (um worktree, dentro de
.claude/worktrees/). Quando a sessao terminava e copiava dali para
~/.claude/skills - que e a pasta que o AFT REALMENTE usa -, ela levava junto o
estado velho de tudo o que outra sessao tinha publicado nesse meio-tempo. O
repositorio continuava certo, o GitHub tambem; so a pasta instalada voltava no
tempo. Sem conflito, sem erro na tela, sem ninguem perceber.

A regra que este script impoe: a copia instalada sai SEMPRE da copia principal,
e so quando ela esta identica ao main publicado no GitHub. Worktree nao publica.

O que ele faz, em ordem:

  1. acha a copia principal (mesmo sendo chamado de dentro de um worktree);
  2. busca o main do GitHub e traz a copia principal para ele (fast-forward);
  3. remonta o NOVIDADES.md a partir da pasta novidades/ (ver montar_novidades.py)
     e o bloco ARCH do arquitetura.html a partir do arquitetura.json - se algum
     dos dois mudou, commita e empurra. Isso acontece AQUI, num lugar so, que e
     o que impede duas sessoes de colidirem nesses dois arquivos;
  4. copia a copia principal para ~/.claude/skills (sem apagar as skills
     pessoais `minha-*` e as que nao existem no repositorio);
  5. reinstala os subagentes (agents/ -> ~/.claude/agents/);
  6. avisa se o perfil do auditor (CLAUDE.md) ficou para tras.

Uso:
    python publicar.py              publica
    python publicar.py --conferir   so diz o que faria, sem mexer em nada
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
import subprocess
import sys
from pathlib import Path

from remontar import git, rodar_script, remontar, MONTADOS, EXCLUIR

try:  # console do Windows e cp1252
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

DESTINO = Path.home() / ".claude" / "skills"


def _repo_a_partir_de(pasta):
    """Clone principal do repositorio que contem `pasta` - de dentro de um
    worktree, o `git-common-dir` ja aponta para o .git do principal. Devolve
    None se ali nao ha repositorio, ou se ele nao e o AFT Toolkit."""
    try:
        if not Path(pasta).is_dir():
            return None
    except OSError:
        return None
    comum = git(["rev-parse", "--git-common-dir"], pasta, checar=False)
    if not comum:
        return None
    p = Path(comum)
    if not p.is_absolute():
        p = (Path(pasta) / p).resolve()
    raiz = p.parent
    if (raiz / "AGENTS.md").is_file() and (raiz / "arquitetura").is_dir():
        return raiz
    return None


def copia_principal(inicio=None):
    """Onde publicar a partir de. Procura primeiro na pasta em que o comando
    esta rodando - e nao na do proprio arquivo .py, que na maquina do AFT fica
    em ~/.claude/skills e nem sequer e um repositorio."""
    for cand in ([inicio] if inicio else
                 [Path.cwd(), Path(__file__).resolve().parent]):
        raiz = _repo_a_partir_de(cand)
        if raiz:
            return raiz
    raise SystemExit(
        "ERRO: não encontrei o repositório do AFT Toolkit a partir daqui.\n"
        "  Rode o publicar de dentro do repositório (ou de um worktree dele):\n"
        "    cd ~/Documents/aft-toolkit && python _scripts/publicar.py")


def main():
    ap = argparse.ArgumentParser(
        description="Publica o toolkit em ~/.claude/skills, sempre a partir do main")
    ap.add_argument("--conferir", action="store_true",
                    help="so mostra o que seria feito, sem alterar nada")
    ap.add_argument("--destino", help=f"pasta instalada (padrao: {DESTINO})")
    args = ap.parse_args()

    conferir = args.conferir
    destino = Path(args.destino).expanduser() if args.destino else DESTINO
    raiz = copia_principal()
    print(f"Cópia principal: {raiz}")
    if conferir:
        print("(modo conferência: nada será alterado)")

    # 1. A copia principal precisa estar em main e sem trabalho em aberto -----
    ramo = git(["branch", "--show-current"], raiz)
    sujo = git(["status", "--porcelain"], raiz)
    if ramo != "main":
        raise SystemExit(
            f"ERRO: a cópia principal está no ramo '{ramo}', não em 'main'.\n"
            "  Publicar a partir de outro ramo é o que faz mudança de outra "
            "sessão sumir da pasta instalada.\n"
            "  Leve a cópia principal para o main antes de publicar.")
    if sujo:
        raise SystemExit(
            "ERRO: a cópia principal tem trabalho em aberto:\n  " +
            "\n  ".join(sujo.splitlines()[:5]) +
            "\n  Resolva isso antes de publicar (o publicar não decide por você "
            "o que fazer com trabalho não commitado).")

    # 2. Trazer o main do GitHub --------------------------------------------
    git(["fetch", "origin", "main"], raiz)
    local = git(["rev-parse", "HEAD"], raiz)
    remoto = git(["rev-parse", "origin/main"], raiz)
    if local != remoto:
        atras = git(["rev-list", "--count", "HEAD..origin/main"], raiz)
        frente = git(["rev-list", "--count", "origin/main..HEAD"], raiz)
        if frente != "0":
            raise SystemExit(
                f"ERRO: a cópia principal tem {frente} commit(s) que não estão "
                "no GitHub.\n  Empurre ou desfaça antes de publicar.")
        if conferir:
            print(f"  traria {atras} commit(s) novo(s) do GitHub")
        else:
            git(["pull", "--ff-only", "origin", "main"], raiz)
            print(f"  main atualizado: {atras} commit(s) novo(s) do GitHub")
    else:
        print("  main já estava em dia com o GitHub")

    # 3. Regerar os dois arquivos montados, num lugar so ---------------------
    # (extraido para remontar.py na issue #139: e o mesmo passo que o
    # empacotador do toolkit vai reusar, sem duplicar esta logica)
    linhas, gerados = remontar(raiz, conferir=conferir)
    for l in linhas:
        print("  " + l)
    if not conferir and gerados:
        # Isto era regravado mais adiante e NUNCA commitado — o publicar
        # sujava a copia principal e, na vez seguinte, o proprio guarda-corpo
        # do passo 1 recusava publicar por causa da sujeira que ele mesmo
        # tinha feito (constatado em 24/08/2026, duas vezes no mesmo dia).
        git(["add"] + MONTADOS, raiz)
        git(["commit", "-m",
             "chore: remonta NOVIDADES.md, a arquitetura e o manifesto\n\n"
             "Gerado por _scripts/publicar.py na copia principal - um lugar\n"
             "so, para duas sessoes nunca colidirem nestes arquivos."],
            raiz)
        git(["push", "origin", "main"], raiz)
        print(f"  regerados e publicados: {', '.join(gerados)}")

    # 4. Copiar para a pasta instalada ---------------------------------------
    if not destino.is_dir():
        raise SystemExit(f"ERRO: pasta instalada não existe: {destino}")

    # 4a. Retrato das skills PESSOAIS antes de mexer na pasta instalada.
    # O rsync abaixo nao apaga (nao usa --delete), mas o retrato e barato e cobre
    # qualquer outro caminho que toque em ~/.claude/skills. Em 19/08/2026 um AFT
    # perdeu as skills pessoais dele numa atualizacao; retrato antes, confere
    # depois, e o prejuizo vira um comando de reposicao.
    if not conferir:
        # (o manifesto que este retrato consulta ja foi regravado e commitado
        # no passo 3, junto com os outros arquivos montados)
        print("  " + rodar_script(raiz, "skills_pessoais.py", ["--backup"], False))
    cmd = ["rsync", "-a", "--itemize-changes"]
    if conferir:
        cmd.append("--dry-run")
    cmd += [f"--exclude={e}" for e in EXCLUIR]
    cmd += [str(raiz) + "/", str(destino) + "/"]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                       errors="replace")
    if r.returncode != 0:
        raise SystemExit(f"ERRO ao copiar para {destino}:\n{r.stderr.strip()}")
    # O rsync marca em cada linha o que mudou: '+' = arquivo novo, 'c'/'s' =
    # conteudo ou tamanho diferentes, so 't' = mesmo arquivo com outra data.
    # Misturar os dois faria o relatorio dizer "148 atualizados" quando nada de
    # fato mudou - e, pior, esconderia os arquivos novos entre os inalterados.
    conteudo, so_data = [], []
    for linha in r.stdout.splitlines():
        if not linha or linha.startswith(".d") or linha.endswith("/"):
            continue
        marca, _, nome = linha.partition(" ")
        mudou = any(c in marca[2:] for c in ("+", "c", "s"))
        (conteudo if mudou else so_data).append(nome.strip())
    verbo = "seriam atualizados" if conferir else "atualizados"
    print(f"  {destino}: {len(conteudo)} arquivo(s) {verbo}"
          + (f" (+{len(so_data)} só com data/hora diferente)" if so_data else ""))
    for nome in conteudo[:10]:
        print("      " + nome)
    if len(conteudo) > 10:
        print(f"      ... e mais {len(conteudo) - 10}")

    # 4b. Nenhuma skill pessoal pode ter sumido no caminho.
    if not conferir:
        try:
            print("  " + rodar_script(raiz, "skills_pessoais.py", ["--conferir"], False))
        except SystemExit:
            print("  ATENCAO: skill pessoal sumiu na publicacao. Reponha com:")
            print("      python3 ~/.claude/skills/_scripts/skills_pessoais.py --restaurar")

    # 5 e 6. Subagentes e perfil do auditor ----------------------------------
    print("  " + rodar_script(raiz, "instalar_agentes.py", [], conferir))
    print("  " + rodar_script(raiz, "sync_perfil.py",
                              ["--status", str(raiz / "config" / "CLAUDE-aft.md"),
                               str(Path.home() / ".claude" / "CLAUDE.md")], False))

    # 7. Reiniciar o servidor do painel ---------------------------------------
    # O servico fica de pe por semanas e faz `import det_sync` UMA VEZ, na
    # partida: trocar o arquivo no disco nao recarrega o modulo. Sem este passo,
    # mudanca em det_sync.py/servir_painel.py e publicada e nao vale - em
    # silencio, ate a maquina reiniciar. (O gerar_painel.py escapa disso porque
    # o servidor o chama como subprocesso a cada carregamento da pagina.)
    # Constatado em 19/08/2026: o sync do DET rodou com codigo de 4 dias antes.
    print("  " + rodar_script(raiz, "instalar_servidor_painel.py",
                              ["reiniciar"], conferir))

    print("PUBLICADO" if not conferir else "CONFERÊNCIA CONCLUÍDA (nada mudou)")


if __name__ == "__main__":
    main()
