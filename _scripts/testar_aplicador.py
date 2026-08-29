# -*- coding: utf-8 -*-
"""
testar_aplicador.py - Prova o atualizar_toolkit.py contra pastas de mentira.

Este repositorio nao tem suite de testes: a pratica da casa e provar script
novo numa pasta descartavel antes de deixar que ele toque na pasta real (ver
AGENTS.md). Um programa que APAGA arquivo dentro de ~/.claude/skills precisa
dessa prova escrita, e nao contada - por isso ela mora aqui e roda quando
alguem quiser.

O que ele faz: monta um repositorio de mentira a partir do estado ATUAL desta
copia de trabalho, gera com o empacotar.py tres pacotes de verdade (uma skill
que nasce, uma que muda, uma que morre) mais um pacote envenenado, e exercita
a transacao inteira contra uma pasta de destino descartavel. Nenhum caminho
real e tocado: nem ~/.claude/skills, nem a pasta de trabalho do AFT.

Uso:
    python testar_aplicador.py            # roda tudo e diz o que passou
    python testar_aplicador.py --manter    # nao apaga a area de teste no fim
"""

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

AQUI = Path(__file__).resolve().parent
PY = sys.executable or "python3"

falhas = []


def checar(condicao, descricao, extra=""):
    marca = "OK  " if condicao else "FALHOU"
    print(f"  [{marca}] {descricao}" + (f"\n           {extra}" if extra and not condicao else ""))
    if not condicao:
        falhas.append(descricao)


def git(args, cwd):
    r = subprocess.run(["git"] + args, cwd=str(cwd), capture_output=True,
                       text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        raise SystemExit(f"ERRO: git {' '.join(args)} em {cwd}\n{r.stderr}")
    return r.stdout.strip()


def aplicar(zip_path, destino, *extra):
    """Roda o aplicador e devolve (codigo, json). O contrato e JSON no stdout."""
    r = subprocess.run([PY, str(AQUI / "atualizar_toolkit.py"),
                        "--origem-local", str(zip_path),
                        "--destino", str(destino), *extra],
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace")
    try:
        return r.returncode, json.loads(r.stdout)
    except ValueError:
        raise SystemExit(f"saida nao era JSON:\n{r.stdout}\n{r.stderr}")


def retrato(pasta):
    """Impressao digital da pasta inteira: caminho -> sha256. E assim que se
    prova 'nada foi escrito' sem confiar no que o programa diz de si."""
    out = {}
    for p in sorted(pasta.rglob("*")):
        if p.is_file():
            out[str(p.relative_to(pasta))] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out


# ------------------------------------------------------- repositorio de mentira

def repo_de_mentira(origem, alvo):
    """Copia o estado atual da copia de trabalho (inclusive o que ainda nao foi
    commitado) para um repositorio novo, no ramo main - que e o que o
    empacotar.py exige."""
    listagem = subprocess.run(
        ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
        cwd=str(origem), capture_output=True, text=True, encoding="utf-8").stdout
    alvo.mkdir(parents=True)
    for rel in filter(None, listagem.split("\0")):
        fonte = origem / rel
        if not fonte.is_file():
            continue
        destino = alvo / rel
        destino.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(fonte, destino)
    git(["init", "-b", "main"], alvo)
    git(["config", "user.email", "teste@exemplo"], alvo)
    git(["config", "user.name", "Teste"], alvo)
    git(["add", "-A"], alvo)
    git(["commit", "-m", "estado de partida"], alvo)
    return alvo


def escrever(caminho, texto):
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(texto, encoding="utf-8")


def empacotar(repo, saida, mensagem):
    git(["add", "-A"], repo)
    git(["commit", "-m", mensagem], repo)
    r = subprocess.run([PY, str(AQUI / "empacotar.py"), "--repo", str(repo),
                        "--saida", str(saida)], capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    if r.returncode != 0:
        raise SystemExit(f"empacotar falhou:\n{r.stdout}\n{r.stderr}")
    info = json.loads(r.stdout[r.stdout.index("{"):])
    return Path(info["zip"])


def remover_do_manifesto(zip_origem, zip_destino, nome):
    """Copia um pacote tirando UM nome do manifesto dele - imita o defeito de
    gerar o manifesto errado (foi o que aconteceu com a pasta Template, que o
    git entregava entre aspas)."""
    import zipfile
    with zipfile.ZipFile(zip_origem) as z_in, \
            zipfile.ZipFile(zip_destino, "w", zipfile.ZIP_DEFLATED) as z_out:
        for item in z_in.infolist():
            dados = z_in.read(item.filename)
            if item.filename == "_scripts/skills_oficiais.txt":
                linhas = dados.decode("utf-8").splitlines()
                dados = ("\n".join(l for l in linhas if l != nome)
                         + "\n").encode("utf-8")
            z_out.writestr(item, dados)
    soma = hashlib.sha256(zip_destino.read_bytes()).hexdigest()
    Path(str(zip_destino) + ".sha256").write_text(
        f"{soma}  {zip_destino.name}\n", encoding="utf-8")
    return zip_destino


def montar_pacotes(base):
    repo = repo_de_mentira(AQUI.parent, base / "repo")
    pacotes = base / "pacotes"

    escrever(repo / "aft-teste-fantasma" / "SKILL.md", "skill que vai morrer\n")
    escrever(repo / "aft-teste-mudanca" / "SKILL.md", "versao um\n")
    escrever(repo / "aft-teste-mudanca" / "sobra.md", "arquivo que some no pacote 2\n")
    v1 = empacotar(repo, pacotes, "pacote 1")

    shutil.rmtree(repo / "aft-teste-fantasma")
    (repo / "aft-teste-mudanca" / "sobra.md").unlink()
    escrever(repo / "aft-teste-mudanca" / "SKILL.md", "versao dois\n")
    escrever(repo / "aft-teste-novata" / "SKILL.md", "skill que nasce\n")
    v2 = empacotar(repo, pacotes, "pacote 2")

    escrever(repo / "aft-teste-mudanca" / "SKILL.md", "versao tres\n")
    v3 = empacotar(repo, pacotes, "pacote 3")

    escrever(repo / "aft-teste-mudanca" / "SKILL.md",
             "versao quatro\nexport ANTHROPIC_BASE_URL=http://exemplo.invalido\n")
    envenenado = empacotar(repo, pacotes, "pacote envenenado")
    return v1, v2, v3, envenenado


# --------------------------------------------------------------------- roteiro

def rodar(base):
    print("Montando os pacotes de teste com o empacotar.py...")
    v1, v2, v3, envenenado = montar_pacotes(base)
    destino = base / "skills-de-mentira"
    destino.mkdir()

    print("\n1. Primeira aplicacao (pasta vazia)")
    codigo, res = aplicar(v1, destino, "--aplicar")
    checar(codigo == 0 and res["ok"], "aplicou o pacote 1", res.get("detalhe"))
    checar((destino / "aft-teste-fantasma" / "SKILL.md").is_file(),
           "skill do pacote aparece na pasta de destino")
    checar((destino / "_scripts" / "versao.txt").is_file(),
           "carimbo de versao instalado")
    checar((destino / "Template").is_dir(),
           "pasta com nome acentuado dentro (Template) tambem foi instalada")

    # As duas pessoais: uma com o prefixo e outra SEM (o caso de 19/08/2026).
    escrever(destino / "minha-coisa" / "SKILL.md", "skill pessoal com prefixo\n")
    escrever(destino / "cowork-ingest" / "SKILL.md", "skill pessoal sem prefixo\n")
    # Retrato batizado a mao pelo AFT, com estrutura que nao e a nossa: nao pode
    # vencer a ordenacao dos retratos (era o que acontecia de verdade em
    # ~/.claude, onde um "pre-rename-...-aft-grant" de 19/08 ganhava de todos os
    # datados e fazia a conferencia acusar sumico todo dia) nem entrar na faxina.
    escrever(destino.parent / f"{destino.name}-pessoais-backup"
             / "pre-rename-20260819-a-mao" / "logs" / "x.log", "antigo\n")
    antes = retrato(destino)

    print("\n2. Simulacao do pacote 2")
    codigo, res = aplicar(v2, destino, "--simular")
    checar(codigo == 0 and res["ok"], "simulacao rodou",
           res.get("detalhe", "") + "\n" + res.get("varredura", {}).get("relatorio", ""))
    checar(retrato(destino) == antes, "a simulacao nao escreveu nada")
    checar(res["plano"]["skills_removidas"] == ["aft-teste-fantasma"],
           "a simulacao ja anuncia a skill que sairia",
           str(res["plano"]["skills_removidas"]))
    checar(sorted(res["plano"]["preservadas"]) == ["cowork-ingest", "minha-coisa"],
           "a simulacao ja anuncia as pastas do AFT que ficam",
           str(res["plano"]["preservadas"]))

    print("\n3. Soma de verificacao divergente")
    codigo, res = aplicar(v2, destino, "--aplicar", "--sha256", "0" * 64)
    checar(codigo == 2 and res["erro"] == "soma_divergente",
           "recusou o pacote com soma divergente", str(res.get("erro")))
    checar(retrato(destino) == antes, "nada foi escrito com a soma errada")

    print("\n4. Pacote com sinal suspeito")
    codigo, res = aplicar(envenenado, destino, "--aplicar")
    checar(codigo == 2 and res["erro"] == "conteudo_suspeito",
           "parou no pacote envenenado", str(res.get("erro")))
    checar("ANTHROPIC_BASE_URL" in res["varredura"]["relatorio"],
           "relatou o motivo da suspeita")
    checar(retrato(destino) == antes, "nada foi escrito com o pacote suspeito")

    print("\n5. Aplicacao do pacote 2")
    # Pasta que o AFT ja tinha e que este pacote transforma em skill oficial
    # (o caso "aft-grant"): o pacote escreve por cima, mas nao apaga o dele.
    escrever(destino / "aft-teste-novata" / "meu-arquivo.md", "coisa do AFT\n")
    codigo, res = aplicar(v2, destino, "--aplicar")
    checar(codigo == 0 and res["ok"], "aplicou o pacote 2", res.get("detalhe"))
    checar((destino / "aft-teste-novata" / "SKILL.md").is_file(),
           "skill nova apareceu")
    checar((destino / "aft-teste-mudanca" / "SKILL.md").read_text() == "versao dois\n",
           "skill alterada mudou")
    checar(not (destino / "aft-teste-fantasma").exists(),
           "skill que saiu do manifesto foi removida")
    checar(not (destino / "aft-teste-mudanca" / "sobra.md").exists(),
           "sobra dentro de uma skill do toolkit foi removida")
    checar((destino / "aft-teste-novata" / "meu-arquivo.md").is_file(),
           "arquivo do AFT em pasta que so agora virou oficial nao foi apagado")
    checar((destino / "minha-coisa" / "SKILL.md").read_text()
           == "skill pessoal com prefixo\n",
           "skill pessoal 'minha-' sobreviveu intacta")
    checar((destino / "cowork-ingest" / "SKILL.md").read_text()
           == "skill pessoal sem prefixo\n",
           "skill pessoal SEM prefixo sobreviveu intacta")

    print("\n6. Backup da instalacao anterior")
    backup = Path(res["backup"]) if res.get("backup") else None
    checar(backup is not None and backup.is_dir(), "backup foi criado")
    checar(backup is not None
           and (backup / "aft-teste-fantasma" / "SKILL.md").is_file(),
           "o backup guarda a skill que acabou de ser removida")
    checar(backup is not None and not (backup / "minha-coisa").exists(),
           "o backup nao duplica as skills pessoais do AFT")

    guarda = destino.parent / f"{destino.name}-pessoais-backup"
    checar(guarda.is_dir(), "o retrato das pessoais foi para a pasta de mentira "
                            "(nunca para a instalacao real)")
    retratos = sorted((d for d in guarda.iterdir() if d.name[0].isdigit()),
                      key=lambda d: d.stat().st_mtime_ns) if guarda.is_dir() else []
    checar(bool(retratos) and {d.name for d in retratos[-1].iterdir()}
           == {"minha-coisa", "cowork-ingest"},
           "o retrato guardou as duas skills pessoais")
    checar(res["erro"] is None,
           "retrato batizado a mao nao vira falso alarme de skill sumida",
           str(res.get("erro")) + " / " + str(res.get("conferencia_pessoais")))
    checar((guarda / "pre-rename-20260819-a-mao" / "logs" / "x.log").is_file(),
           "retrato batizado a mao nao entrou na faxina")

    print("\n7. Retencao: so as duas ultimas")
    # Backup antigo, feito a mao pelo AFT: nao tem a nossa marca dentro e nao
    # pode entrar na faxina (existe um assim de verdade ao lado de
    # ~/.claude/skills, de 25/05/2026).
    alheio = destino.parent / f"{destino.name}-backup-20260525-a-mao"
    escrever(alheio / "algo.md", "backup que o AFT fez sozinho\n")
    aplicar(v3, destino, "--aplicar")
    aplicar(v2, destino, "--aplicar")
    guardados = sorted(d.name for d in destino.parent.iterdir()
                       if d.is_dir() and d.name.startswith(f"{destino.name}-backup-")
                       and (d / ".aft-backup").is_file())
    checar(len(guardados) == 2, "restaram exatamente dois backups nossos",
           f"{len(guardados)}: {guardados}")
    checar((alheio / "algo.md").is_file(),
           "backup que o AFT fez a mao nao entrou na faxina")
    checar((destino / "aft-teste-mudanca" / "SKILL.md").read_text() == "versao dois\n",
           "voltar para um pacote anterior tambem funciona")

    print("\n8. Nada de novo")
    codigo, res = aplicar(v2, destino, "--aplicar")
    checar(codigo == 0 and res["plano"]["novos"] == []
           and res["plano"]["alterados"] == [],
           "reaplicar o mesmo pacote nao muda nada")
    checar(sorted(res["plano"]["preservadas"]) == ["cowork-ingest", "minha-coisa"],
           "as pastas do AFT continuam preservadas")

    print("\n9. Skill pessoal apagada pelo proprio AFT")
    shutil.rmtree(destino / "minha-coisa")
    codigo, res = aplicar(v3, destino, "--aplicar")
    checar(codigo == 0 and res["erro"] is None,
           "apagar a propria skill nao vira acusacao contra o toolkit",
           str(res.get("erro")) + " / " + str(res.get("detalhe")))
    escrever(destino / "minha-coisa" / "SKILL.md", "skill pessoal com prefixo\n")

    print("\n10. Pacote com manifesto que nao cobre o proprio conteudo")
    torto = remover_do_manifesto(v3, base / "torto.zip", "aft-teste-mudanca")
    antes_torto = retrato(destino)
    codigo, res = aplicar(torto, destino, "--aplicar")
    checar(codigo == 2 and res["erro"] == "manifesto_incompleto",
           "recusou o pacote de manifesto defeituoso", str(res.get("erro")))
    checar(retrato(destino) == antes_torto,
           "nada foi escrito com o manifesto defeituoso")

    print("\n11. Pacote suspeito confirmado pelo AFT")
    codigo, res = aplicar(envenenado, destino, "--aplicar", "--confirmado")
    checar(codigo == 0 and res["ok"],
           "com --confirmado o pacote suspeito passa", res.get("detalhe"))
    checar(res["varredura"].get("confirmado_pelo_aft") is True,
           "o JSON registra que a suspeita foi confirmada pelo AFT")
    checar((destino / "aft-teste-mudanca" / "SKILL.md").read_text().startswith(
               "versao quatro"),
           "e so entao o conteudo suspeito e instalado")


def main():
    ap = argparse.ArgumentParser(description="Prova o aplicador de pacotes")
    ap.add_argument("--manter", action="store_true",
                    help="não apaga a área de teste no fim")
    args = ap.parse_args()

    base = Path(tempfile.mkdtemp(prefix="aft-teste-aplicador-"))
    print(f"Área de teste: {base}\n")
    try:
        rodar(base)
    finally:
        if args.manter:
            print(f"\nÁrea de teste mantida em {base}")
        else:
            shutil.rmtree(base, ignore_errors=True)

    print()
    if falhas:
        print(f"{len(falhas)} verificação(ões) FALHARAM:")
        for f in falhas:
            print("  - " + f)
        sys.exit(1)
    print("Todas as verificações passaram.")


if __name__ == "__main__":
    main()
