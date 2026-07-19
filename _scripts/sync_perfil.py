#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sync_perfil.py - re-sincroniza o perfil do AFT (CLAUDE.md) com o template do toolkit.

O template `config/CLAUDE-aft.md` cerca o conteudo gerenciado pelo toolkit com dois
marcadores invisiveis (comentarios HTML) e um numero de versao:

    <!-- AFT-TOOLKIT-PERFIL:INICIO v3 ... -->
    ...conteudo do perfil...
    <!-- AFT-TOOLKIT-PERFIL:FIM -->

Assim o `/aft-atualizar` substitui SOZINHO so o miolo entre os marcadores, sem nunca
tocar no que o AFT escreveu fora deles. Instalacoes antigas (feitas antes dos marcadores)
nao tem o bloco marcado: para essas, `--status` devolve SEM_MARCADOR e a skill oferece
UMA vez a adocao (--adotar-substituir / --adotar-acrescentar); dai em diante viram
automaticas.

Modos:
  --status <template> <alvo>       so relata (nao grava). Imprime uma linha:
                                     SEM_ARQUIVO
                                     SEM_MARCADOR
                                     EM_DIA v<N>
                                     DESATUALIZADO instalada=v<X> template=v<Y>
  --aplicar <template> <alvo>      substitui so o bloco marcado (backup antes).
                                     So age se o alvo ja tiver marcador e estiver velho.
  --adotar-substituir <template> <alvo>   troca o alvo INTEIRO pelo bloco marcado.
  --adotar-acrescentar <template> <alvo>  acrescenta o bloco marcado ao fim do alvo.

Sempre imprime o resultado em uma linha (facil de a skill ler). Nunca apaga nada sem
backup (usa o backup_arquivo.py ao lado). O template SEMPRE precisa ter o marcador.
"""
import os
import re
import subprocess
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

BLOCO_RE = re.compile(
    r"<!--\s*AFT-TOOLKIT-PERFIL:INICIO\s+v(\d+).*?AFT-TOOLKIT-PERFIL:FIM\s*-->",
    re.DOTALL,
)


def fail(msg):
    print(f"ERRO: {msg}", file=sys.stderr)
    sys.exit(2)


def ler(caminho):
    with open(caminho, encoding="utf-8") as f:
        return f.read()


def extrair_bloco(texto):
    """Devolve (versao:int, bloco:str) do texto, ou (None, None) se nao houver marcador."""
    m = BLOCO_RE.search(texto)
    if not m:
        return None, None
    return int(m.group(1)), m.group(0)


def backup(caminho):
    """Copia de seguranca via backup_arquivo.py (mesma convencao do toolkit)."""
    script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backup_arquivo.py")
    if os.path.isfile(script):
        subprocess.run([sys.executable, script, caminho], check=False)


def gravar(caminho, texto):
    with open(caminho, "w", encoding="utf-8") as f:
        f.write(texto)


def bloco_do_template(template_path):
    ver, bloco = extrair_bloco(ler(template_path))
    if ver is None:
        fail(f"template '{template_path}' nao tem o marcador AFT-TOOLKIT-PERFIL")
    return ver, bloco


def cmd_status(template_path, alvo_path):
    ver_t, _ = bloco_do_template(template_path)
    if not os.path.isfile(alvo_path):
        print("SEM_ARQUIVO")
        return
    ver_a, _ = extrair_bloco(ler(alvo_path))
    if ver_a is None:
        print("SEM_MARCADOR")
    elif ver_t > ver_a:
        print(f"DESATUALIZADO instalada=v{ver_a} template=v{ver_t}")
    else:
        print(f"EM_DIA v{ver_a}")


def cmd_aplicar(template_path, alvo_path):
    ver_t, bloco_t = bloco_do_template(template_path)
    if not os.path.isfile(alvo_path):
        print("SEM_ARQUIVO")
        return
    alvo_txt = ler(alvo_path)
    ver_a, _ = extrair_bloco(alvo_txt)
    if ver_a is None:
        print("SEM_MARCADOR")  # nao mexe: sem marcador nao da para isolar o bloco
        return
    if ver_t <= ver_a:
        print(f"EM_DIA v{ver_a}")
        return
    backup(alvo_path)
    novo = BLOCO_RE.sub(lambda _m: bloco_t, alvo_txt, count=1)
    gravar(alvo_path, novo)
    print(f"ATUALIZADO v{ver_a} v{ver_t}")


def cmd_adotar_substituir(template_path, alvo_path):
    ver_t, bloco_t = bloco_do_template(template_path)
    if os.path.isfile(alvo_path):
        backup(alvo_path)
    gravar(alvo_path, bloco_t + "\n")
    print(f"ADOTADO_SUBSTITUIR v{ver_t}")


def cmd_adotar_acrescentar(template_path, alvo_path):
    ver_t, bloco_t = bloco_do_template(template_path)
    if os.path.isfile(alvo_path):
        backup(alvo_path)
        base = ler(alvo_path).rstrip() + "\n\n---\n\n"
    else:
        base = ""
    gravar(alvo_path, base + bloco_t + "\n")
    print(f"ADOTADO_ACRESCENTAR v{ver_t}")


MODOS = {
    "--status": cmd_status,
    "--aplicar": cmd_aplicar,
    "--adotar-substituir": cmd_adotar_substituir,
    "--adotar-acrescentar": cmd_adotar_acrescentar,
}


def main():
    if len(sys.argv) != 4 or sys.argv[1] not in MODOS:
        fail("uso: sync_perfil.py "
             "--status|--aplicar|--adotar-substituir|--adotar-acrescentar "
             "<template> <alvo>")
    MODOS[sys.argv[1]](sys.argv[2], sys.argv[3])


if __name__ == "__main__":
    main()
