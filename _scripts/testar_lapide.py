# -*- coding: utf-8 -*-
"""
testar_lapide.py - Prova o resgate da instalacao que caiu na lapide.

O PROBLEMA QUE ESTE TESTE GUARDA (issue #153)
---------------------------------------------
Na virada, o repositorio publico e reduzido a lapide: fica so o README e a
/aft-atualizar nova (issue #144). Quem ja tinha o toolkit instalado por
`git clone` - todo mundo, ate a virada - recebe essa reducao pelo caminho de
sempre: a /aft-atualizar ANTIGA da maquina dele manda `git pull`, e o pull
APAGA as ~60 skills de fiscalizacao da pasta dele.

E justamente o AFT retardatario, o unico que a lapide existe para socorrer:
ele nao tem como receber a skill nova sem antes dar o pull que esvazia a pasta.
Sem resgate, ele fica sem ferramenta - possivelmente no meio de uma
fiscalizacao - ate o acesso ao portal sair.

O conteudo nao se perdeu: o historico do git continua na maquina dele. Este
teste prova, contra uma instalacao de mentira, que:

  * o --verificar RECONHECE a pasta reduzida a lapide, e reconhece ANTES de
    falar de codigo de acesso (o retardatario nao tem codigo nenhum);
  * o --resgatar repoe as skills apagadas, sem rede;
  * o resgate NAO desfaz a lapide: a /aft-atualizar nova e o README novo
    continuam os novos - senao o AFT voltaria para a skill velha, que daria
    `git pull` de novo, num circulo;
  * a skill pessoal dele (nao rastreada) atravessa tudo intacta;
  * depois do resgate, a pasta deixa de ser "lapide" e o fluxo normal segue.

Nada real e tocado: tudo acontece numa pasta temporaria.

Uso:
    python testar_lapide.py
    python testar_lapide.py --manter    # nao apaga a area de teste no fim
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

AQUI = Path(__file__).resolve().parent
PY = sys.executable or "python3"

# O que sobra no repositorio publico depois da virada (issue #144).
LAPIDE = ("README.md", "LICENSE", ".gitignore", "aft-atualizar/SKILL.md",
          "_scripts/atualizar_toolkit.py", "_scripts/portal_toolkit.py",
          "_scripts/pasta_aft.py", "_scripts/skills_pessoais.py",
          "_scripts/checar_diff.py", "_scripts/remontar.py")

falhas = []


def checar(condicao, descricao, extra=""):
    marca = "OK  " if condicao else "FALHOU"
    print(f"  [{marca}] {descricao}" + (f"\n           {extra}" if extra and not condicao else ""))
    if not condicao:
        falhas.append(descricao)


def git(args, cwd):
    r = subprocess.run(["git", *args], cwd=str(cwd), capture_output=True,
                       text=True, encoding="utf-8", errors="replace")
    if r.returncode:
        raise SystemExit(f"ERRO: git {' '.join(args)} em {cwd}\n{r.stderr}")
    return r.stdout.strip()


def rodar_script(*args, ambiente=None):
    r = subprocess.run([PY, str(AQUI / "atualizar_toolkit.py"), *args],
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace", env=ambiente)
    try:
        return r.returncode, json.loads(r.stdout)
    except ValueError:
        raise SystemExit(f"saída não era JSON:\n{r.stdout}\n{r.stderr}")


def virar_lapide(repo):
    """Reduz o repositorio publico ao que sobra depois da virada, do mesmo
    jeito que a issue #144 faz: apaga o toolkit e deixa o caminho de volta."""
    for item in list(repo.iterdir()):
        if item.name == ".git":
            continue
        if item.is_dir():
            shutil.rmtree(item)
        else:
            item.unlink()
    for rel in LAPIDE:
        fonte = AQUI.parent / rel
        alvo = repo / rel
        alvo.parent.mkdir(parents=True, exist_ok=True)
        if fonte.is_file():
            shutil.copy2(fonte, alvo)
        else:
            alvo.write_text(f"{rel} da lápide\n", encoding="utf-8")
    # Marca a /aft-atualizar da lapide, para o teste conseguir provar depois
    # que o resgate NAO a substituiu pela versao velha.
    with open(repo / "aft-atualizar" / "SKILL.md", "a", encoding="utf-8") as f:
        f.write("\n<!-- versao da lapide -->\n")
    (repo / "README.md").write_text(
        "# AFT Toolkit\n\nEste repositório mudou de função: o toolkit passou a "
        "ser distribuído pelo portal.\n", encoding="utf-8")
    git(["add", "-A"], repo)
    git(["commit", "-m", "repositorio publico vira lapide"], repo)


def rodar(base, ambiente):
    from testar_aplicador import repo_de_mentira  # o mesmo repo de sempre

    print("Montando o repositório público de mentira (estado de antes)...")
    repo = repo_de_mentira(AQUI.parent, base / "publico")

    print("\n1. Instalação antiga do AFT, feita por git clone")
    instalacao = base / "skills-de-mentira"
    git(["clone", "--quiet", str(repo), str(instalacao)], base)
    pessoal = instalacao / "sisos-sync" / "SKILL.md"
    pessoal.parent.mkdir(parents=True, exist_ok=True)
    pessoal.write_text("skill pessoal, sem o prefixo minha-\n", encoding="utf-8")
    checar((instalacao / "aft-painel").is_dir(),
           "a instalação antiga tem as skills de fiscalização")
    checar((instalacao / "_scripts" / "skills_oficiais.txt").is_file(),
           "e tem o manifesto do toolkit")

    print("\n2. A virada: o AFT retardatário dá o git pull de sempre")
    virar_lapide(repo)
    git(["pull", "--quiet", "origin", "main"], instalacao)
    checar(not (instalacao / "aft-painel").is_dir(),
           "o pull da lápide APAGOU as skills de fiscalização "
           "(é este o estrago que o resgate desfaz)")
    checar(pessoal.is_file(),
           "a skill pessoal dele sobreviveu ao pull (não é rastreada)")
    checar((instalacao / "aft-atualizar" / "SKILL.md").read_text(
        encoding="utf-8").endswith("<!-- versao da lapide -->\n"),
        "e a /aft-atualizar nova chegou pela lápide")

    print("\n3. O --verificar reconhece a pasta reduzida à lápide")
    # Sem código de acesso nenhum na máquina: é a situação real do
    # retardatário, e mesmo assim o estado da lápide tem de vir primeiro.
    codigo, res = rodar_script("--verificar", "--destino", str(instalacao),
                               ambiente=ambiente)
    checar(res.get("estado") == "lapide",
           "o estado da lápide vem antes da conversa sobre código de acesso",
           str(res.get("estado")))
    checar(res.get("resgate_disponivel") is True,
           "e ele diz que dá para trazer as skills de volta agora")
    detalhe = res.get("detalhe", "")
    checar("perderam" in detalhe or "perdeu" in detalhe or "não se perdeu" in detalhe,
           "a explicação tranquiliza: o conteúdo não se perdeu", detalhe)
    checar("notebooks-aft" in detalhe,
           "e conduz ao cadastro no portal na mesma mensagem", detalhe)

    print("\n4. O resgate repõe o toolkit, sem rede")
    codigo, res = rodar_script("--resgatar", "--destino", str(instalacao),
                               ambiente=ambiente)
    checar(codigo == 0 and res.get("ok"), "o resgate correu bem",
           str(res.get("detalhe")))
    checar((instalacao / "aft-painel" / "SKILL.md").is_file(),
           "as skills de fiscalização voltaram para a pasta")
    checar((instalacao / "_scripts" / "skills_oficiais.txt").is_file(),
           "o manifesto voltou junto")
    checar(pessoal.read_text(encoding="utf-8").startswith("skill pessoal"),
           "a skill pessoal continua intacta")

    print("\n5. O resgate não desfaz a lápide")
    checar((instalacao / "aft-atualizar" / "SKILL.md").read_text(
        encoding="utf-8").endswith("<!-- versao da lapide -->\n"),
        "a /aft-atualizar continua sendo a NOVA - senão o AFT voltaria à "
        "skill velha e daria git pull de novo, em círculo")
    checar("portal" in (instalacao / "README.md").read_text(encoding="utf-8"),
           "e o README continua sendo o da lápide")

    print("\n6. Depois do resgate, a pasta não é mais lápide")
    codigo, res = rodar_script("--verificar", "--destino", str(instalacao),
                               ambiente=ambiente)
    checar(res.get("estado") != "lapide",
           "o --verificar volta ao fluxo normal", str(res.get("estado")))
    checar(res.get("estado") == "sem_token",
           "e passa a pedir o código de acesso, que é o próximo passo real",
           str(res.get("estado")))
    codigo, res = rodar_script("--resgatar", "--destino", str(instalacao),
                               ambiente=ambiente)
    checar(codigo == 2 and res.get("erro") == "nada_a_resgatar",
           "e resgatar de novo não faz nada", str(res.get("erro")))

    print("\n7. A skill ensina o resgate")
    skill = (AQUI.parent / "aft-atualizar" / "SKILL.md").read_text(encoding="utf-8")
    checar("--resgatar" in skill,
           "a /aft-atualizar documenta o resgate")
    checar("lapide" in skill or "lápide" in skill,
           "e explica o estado da lápide ao assistente")


def main():
    ap = argparse.ArgumentParser(description="Prova o resgate da lápide")
    ap.add_argument("--manter", action="store_true",
                    help="não apaga a área de teste no fim")
    args = ap.parse_args()

    sys.path.insert(0, str(AQUI))
    base = Path(tempfile.mkdtemp(prefix="aft-teste-lapide-"))
    # PASTA_AFT de mentira: o --verificar procura o codigo de acesso na pasta
    # de trabalho do AFT, e nada aqui pode encostar na pasta real.
    ambiente = dict(os.environ, PASTA_AFT=str(base / "AFT-de-mentira"))
    print(f"Área de teste: {base}\n")
    try:
        rodar(base, ambiente)
    finally:
        if args.manter:
            print(f"\nÁrea de teste mantida em {base}")
        else:
            shutil.rmtree(base, ignore_errors=True)

    print()
    if falhas:
        print(f"{len(falhas)} verificação(ões) FALHARAM:")
        for f in falhas:
            print(f"  - {f}")
        sys.exit(1)
    print("Todas as verificações passaram.")


if __name__ == "__main__":
    main()
