#!/usr/bin/env python3
"""
checar_arquivo_aberto.py - detecta se um arquivo esta aberto/bloqueado (AFT Toolkit).

No Windows, enquanto o AFT estiver com o .docx (RT, autos) aberto no Word, qualquer
tentativa de gravar por cima falha com "Permission denied" - e o erro aparece so no meio
da operacao. Este script checa ANTES: se o arquivo estiver bloqueado, a skill avisa o AFT
para fechar (a menor acao possivel) e so entao grava, sem erro cru.

Como detecta:
  1. Teste autoritativo: tenta abrir o arquivo para escrita (modo 'r+b', sem truncar).
     Se o Word/Excel o mantem com lock de escrita, isso falha com PermissionError - e e
     exatamente a mesma condicao que faria o save falhar.
  2. Pista do Office: presenca do arquivo-dono "~$..." que o Word/Excel cria ao abrir o
     documento (usado so para deixar a mensagem mais clara).

Uso:
    python checar_arquivo_aberto.py "<arquivo>"
Exit 0 = livre (ou inexistente: nada a bloquear); 1 = bloqueado (peca para fechar).
"""
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def arquivo_dono_office(path):
    """Caminho do '~$' que o Word/Excel cria ao abrir (regra: ~$ + nome[2:])."""
    d = os.path.dirname(os.path.abspath(path))
    base = os.path.basename(path)
    return os.path.join(d, "~$" + base[2:]) if len(base) > 2 else None


def bloqueado_para_escrita(path):
    try:
        with open(path, "r+b"):
            return False
    except PermissionError:
        return True
    except OSError:
        # Outro erro de IO -> trata como bloqueado, por seguranca.
        return True


def main():
    if len(sys.argv) != 2:
        print("uso: python checar_arquivo_aberto.py <arquivo>", file=sys.stderr)
        sys.exit(2)
    path = sys.argv[1]

    if not os.path.exists(path):
        print(f"LIVRE: '{path}' nao existe (arquivo novo) - nada a bloquear.")
        sys.exit(0)

    locked = bloqueado_para_escrita(path)
    dono = arquivo_dono_office(path)
    tem_dono = bool(dono and os.path.exists(dono))

    if locked or tem_dono:
        pista = " (parece estar aberto no Word/Excel)" if tem_dono else ""
        print(f"ABERTO: '{os.path.basename(path)}' esta bloqueado para gravacao{pista}.")
        print("  -> Peca ao AFT para FECHAR o arquivo no Word/Excel e tente de novo.")
        sys.exit(1)

    print(f"LIVRE: '{os.path.basename(path)}' pode ser gravado.")
    sys.exit(0)


if __name__ == "__main__":
    main()
