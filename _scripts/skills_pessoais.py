#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
skills_pessoais — protege as skills que o AFT criou, e que o toolkit nao conhece.

O toolkit instala em ~/.claude/skills e o AFT guarda ali tambem as skills dele.
Toda pasta de 1o nivel que NAO pertence ao toolkit e dele: nada nosso pode
apaga-la, renomea-la ou sobrescreve-la, com ou sem o prefixo "minha-".

Em 19/08/2026 uma atualizacao levou junto as skills pessoais de um AFT
(cowork-ingest, cipa-atas, sisos-sync e outras). O .gitignore do repo passou a
ignorar tudo que nao e do toolkit — isso resolve nas instalacoes que sao clone
git. Este script e a rede que vale nos dois modelos: tira um retrato antes de
qualquer atualizacao e sabe repor o que sumir.

Uso:
  skills_pessoais.py --listar
  skills_pessoais.py --backup            # retrato antes de atualizar
  skills_pessoais.py --conferir          # o que sumiu desde o ultimo retrato?
  skills_pessoais.py --restaurar         # repoe o que sumiu (nunca sobrescreve)

Por padrao olha a pasta instalada de verdade (~/.claude/skills). O
atualizar_toolkit.py aponta para outra pasta com --skills/--manifesto, que e o
que permite exercitar a atualizacao inteira contra uma pasta de mentira.
"""
from __future__ import annotations
import argparse, shutil, sys, time
from pathlib import Path

SKILLS = Path.home() / ".claude" / "skills"
# Fora de ~/.claude/skills de proposito: um apagao la nao pode levar o retrato.
GUARDA = Path.home() / ".claude" / "skills-pessoais-backup"
# Lista real do que o toolkit instala, regravada pelo publicar.py a cada
# publicacao. Nao da para deduzir pelo prefixo: "aft-grant" e uma skill PESSOAL
# de um AFT e tem cara de oficial. Palpite pelo nome deixaria ela desprotegida.
MANIFESTO = Path(__file__).with_name("skills_oficiais.txt")
INFRA = {"_scripts", "Template", "agents", "arquitetura", "config", "novidades"}


def oficiais() -> set[str]:
    if MANIFESTO.is_file():
        return {l.strip() for l in MANIFESTO.read_text(encoding="utf-8").splitlines() if l.strip()}
    # Sem manifesto, cai no palpite — pior, mas melhor que nao proteger nada.
    return INFRA | {d.name for d in SKILLS.iterdir()
                    if d.is_dir() and d.name.startswith("aft-")}


def pessoais() -> list[Path]:
    """Pastas de 1o nivel que nao sao do toolkit."""
    if not SKILLS.is_dir():
        return []
    conhecidas = oficiais()
    return sorted(d for d in SKILLS.iterdir()
                  if d.is_dir() and not d.name.startswith(".")
                  and d.name not in conhecidas and d.name not in INFRA)


def fazer_backup() -> Path:
    alvo = GUARDA / time.strftime("%Y%m%d-%H%M%S")
    # O nome tem resolucao de SEGUNDOS: dois retratos no mesmo segundo caiam na
    # mesma pasta e o copytree(dirs_exist_ok) FUNDIA os dois - o retrato passava
    # a mostrar skill que ja nao existia mais, e a conferencia acusava sumico
    # que nao houve. Nome novo em vez de fusao.
    n = 2
    while alvo.exists():
        alvo = GUARDA / (time.strftime("%Y%m%d-%H%M%S") + f"-{n}")
        n += 1
    achadas = pessoais()
    # O retrato e criado MESMO VAZIO, de proposito. Sem isso, quem nao tem
    # skill pessoal hoje continua sendo comparado com um retrato antigo, e uma
    # skill que o proprio AFT apagou reaparece como "sumiu na atualizacao" —
    # acusando o toolkit de um estrago que nao houve.
    alvo.mkdir(parents=True, exist_ok=True)
    if not achadas:
        print("skills_pessoais: nenhuma skill pessoal encontrada — retrato vazio "
              f"em {alvo}")
        return alvo
    for d in achadas:
        shutil.copytree(d, alvo / d.name, dirs_exist_ok=True)
    # so os 5 retratos mais recentes
    retratos = sorted(GUARDA.iterdir(), reverse=True)
    for velho in retratos[5:]:
        shutil.rmtree(velho, ignore_errors=True)
    print(f"skills_pessoais: {len(achadas)} skill(s) guardada(s) em {alvo}")
    return alvo


def ultimo_retrato() -> Path | None:
    if not GUARDA.is_dir():
        return None
    r = sorted((d for d in GUARDA.iterdir() if d.is_dir()), reverse=True)
    return r[0] if r else None


def sumidas() -> tuple[Path | None, list[str]]:
    r = ultimo_retrato()
    if not r:
        return None, []
    agora = {d.name for d in pessoais()}
    return r, sorted(d.name for d in r.iterdir() if d.is_dir() and d.name not in agora)


def main() -> None:
    global SKILLS, GUARDA, MANIFESTO
    ap = argparse.ArgumentParser(description="Protege as skills pessoais do AFT")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--listar", action="store_true")
    g.add_argument("--backup", action="store_true")
    g.add_argument("--conferir", action="store_true")
    g.add_argument("--restaurar", action="store_true")
    ap.add_argument("--skills", help=f"pasta instalada (padrao: {SKILLS}). "
                                     "O retrato vai para a pasta irma "
                                     "'<nome>-pessoais-backup'.")
    ap.add_argument("--manifesto", help="lista do que e do toolkit "
                                        f"(padrao: {MANIFESTO.name} ao lado deste script)")
    a = ap.parse_args()

    if a.skills:
        SKILLS = Path(a.skills).expanduser().resolve()
        GUARDA = SKILLS.parent / (SKILLS.name + "-pessoais-backup")
    if a.manifesto:
        MANIFESTO = Path(a.manifesto).expanduser().resolve()

    if a.listar:
        achadas = pessoais()
        print(f"skills pessoais em {SKILLS}: {len(achadas)}")
        for d in achadas:
            print("  " + d.name)
        return

    if a.backup:
        fazer_backup()
        return

    retrato, faltando = sumidas()
    if not retrato:
        print("skills_pessoais: nao ha retrato anterior — rode --backup primeiro.")
        sys.exit(1)
    if not faltando:
        print(f"skills_pessoais: nada sumiu (retrato de {retrato.name}).")
        return

    if a.conferir:
        print(f"skills_pessoais: {len(faltando)} skill(s) sumiram desde {retrato.name}:")
        for n in faltando:
            print("  " + n)
        print("  repor com: --restaurar")
        sys.exit(3)

    reposto = []
    for n in faltando:
        destino = SKILLS / n
        if destino.exists():       # nunca sobrescreve o que esta la
            continue
        shutil.copytree(retrato / n, destino)
        reposto.append(n)
    print(f"skills_pessoais: {len(reposto)} skill(s) reposta(s) de {retrato.name}")
    for n in reposto:
        print("  " + n)


if __name__ == "__main__":
    main()
