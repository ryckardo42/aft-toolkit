# -*- coding: utf-8 -*-
"""
ajuda_arquitetura.py — consulta o arquitetura.json para a skill /aft-ajuda.

Por que este script existe: o catálogo das habilidades, a lista dos scripts
locais, as regras de pseudonimização e os avisos JÁ moram, mantidos, no
arquivo arquitetura/arquitetura.json — que vai instalado junto com as skills
(o publicar.py copia a pasta arquitetura/ inteira). Escrever esses mesmos
dados de novo dentro da /aft-ajuda criaria uma segunda cópia, que divergiria
na primeira habilidade nova. Então a /aft-ajuda LÊ a arquitetura em vez de
repeti-la — regra da casa: uma informação, um lugar.

O arquivo tem 88 KB. Jogá-lo inteiro no contexto a cada pergunta é caro e
desnecessário: este script recorta só o pedaço que responde à pergunta.

Uso (o Claude executa; o AFT nunca digita isto):
    python ajuda_arquitetura.py --listar
        os blocos disponíveis e quantos itens cada um tem

    python ajuda_arquitetura.py --bloco camadas
        despeja um bloco inteiro em texto legível
        (camadas = o catálogo das habilidades, agrupadas por etapa do fluxo)

    python ajuda_arquitetura.py --buscar "PGR"
        procura o termo em todos os blocos e devolve só os itens que casam

    python ajuda_arquitetura.py --skill aft-PGR-analise
        o que uma habilidade faz, em que camada ela está e o modelo que usa

Saída: texto puro, para o modelo ler. Exit 0 sempre que achou o arquivo.
"""
from __future__ import annotations

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
import sys
import unicodedata
from pathlib import Path

# Console do Windows é cp1252: nunca deixar um acento derrubar o script.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def achar_json() -> Path | None:
    """O arquitetura.json ao lado das skills instaladas (ou no repositório)."""
    aqui = Path(__file__).resolve()
    candidatos = [a / "arquitetura" / "arquitetura.json" for a in aqui.parents]
    candidatos.append(Path.home() / ".claude" / "skills" / "arquitetura"
                      / "arquitetura.json")
    for c in candidatos:
        if c.is_file():
            return c
    return None


def sem_acento(s: str) -> str:
    """Compara 'inspecao' com 'inspeção' — o AFT digita dos dois jeitos."""
    return "".join(c for c in unicodedata.normalize("NFD", s.lower())
                   if unicodedata.category(c) != "Mn")


def texto_do_item(item) -> str:
    """Achata um item (str ou dict, com chaves que variam por bloco)."""
    if isinstance(item, str):
        return item
    if isinstance(item, dict):
        partes = []
        for k, v in item.items():
            if isinstance(v, list):
                v = "; ".join(texto_do_item(x) for x in v)
            partes.append(f"{k}: {v}")
        return " · ".join(partes)
    return str(item)


def mostrar_item(item, recuo: str = "  ") -> None:
    if isinstance(item, dict):
        chaves = list(item.items())
        titulo = str(chaves[0][1]) if chaves else ""
        print(f"{recuo}- {titulo}")
        for k, v in chaves[1:]:
            if isinstance(v, list):
                print(f"{recuo}    {k}:")
                for x in v:
                    mostrar_item(x, recuo + "      ")
            else:
                print(f"{recuo}    {k}: {v}")
    else:
        print(f"{recuo}- {item}")


def main() -> int:
    caminho = achar_json()
    if caminho is None:
        print("Nao encontrei o arquitetura.json. Ele deveria estar em "
              "~/.claude/skills/arquitetura/arquitetura.json — rode "
              "/aft-doctor para conferir a instalacao.")
        return 1

    dados = json.loads(caminho.read_text(encoding="utf-8"))
    argv = sys.argv[1:]

    def valor(flag: str) -> str | None:
        if flag in argv and argv.index(flag) + 1 < len(argv):
            return argv[argv.index(flag) + 1]
        return None

    if not argv or "--listar" in argv:
        print(f"Fonte: {caminho}")
        print(f"Projeto: {dados.get('projeto', '')}")
        print(f"Atualizado em: {dados.get('data', '')}\n")
        print("Blocos disponiveis (use --bloco <nome>):")
        for k, v in dados.items():
            if isinstance(v, list):
                print(f"  {k:16} {len(v)} itens")
            elif isinstance(v, dict):
                print(f"  {k:16} {len(v)} campos")
        return 0

    nome = valor("--bloco")
    if nome:
        if nome not in dados:
            print(f"Bloco '{nome}' nao existe. Rode --listar para ver os nomes.")
            return 1
        bloco = dados[nome]
        print(f"=== {nome} ===")
        if isinstance(bloco, list):
            for item in bloco:
                mostrar_item(item)
        elif isinstance(bloco, dict):
            for k, v in bloco.items():
                print(f"  {k}: {v}")
        else:
            print(f"  {bloco}")
        return 0

    termo = valor("--buscar") or valor("--skill")
    so_skill = valor("--skill") is not None
    if termo:
        alvo = sem_acento(termo)
        achou = False
        for chave, bloco in dados.items():
            if not isinstance(bloco, list):
                continue
            if so_skill and chave not in ("camadas", "fluxo", "scripts"):
                continue
            casos = []
            for item in bloco:
                # 'camadas' guarda as habilidades numa lista aninhada.
                if isinstance(item, dict) and isinstance(item.get("skills"), list):
                    filhas = [s for s in item["skills"]
                              if alvo in sem_acento(texto_do_item(s))]
                    if filhas:
                        casos.append({"camada": item.get("nome", ""),
                                      "skills": filhas})
                elif alvo in sem_acento(texto_do_item(item)):
                    casos.append(item)
            if casos:
                achou = True
                print(f"=== {chave} ===")
                for c in casos:
                    mostrar_item(c)
                print()
        if not achou:
            print(f"Nada encontrado para '{termo}' na arquitetura. "
                  "Talvez seja assunto da apostila ou das referencias da "
                  "propria /aft-ajuda.")
        return 0

    print(__doc__)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
