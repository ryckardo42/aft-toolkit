#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pasta_aft.py - Resolve a pasta de trabalho do AFT (~/Documents/AFT) de verdade.

Por que este modulo existe: no Windows, "Documentos" quase nunca fica em
C:\\Users\\<user>\\Documents. Dois motivos se somam:

  1. OneDrive: o backup de pastas redireciona Documentos para dentro do
     OneDrive (C:\\Users\\thiag\\OneDrive\\Documentos).
  2. Idioma: o Windows em portugues chama a pasta de "Documentos", nao
     "Documents".

Um `mkdir ~/Documents/AFT` cru cria uma pasta ORFA que o AFT nunca ve no
Explorer (ele abre "Documentos", que aponta para outro lugar) - foi o que
aconteceu numa instalacao real (22/07/2026). A fonte da verdade no Windows e
o registro (User Shell Folders\\Personal), que ja vem com o caminho correto
qualquer que seja o idioma ou o redirecionamento.

Ordem de resolucao da pasta AFT:
  1. Variavel de ambiente PASTA_AFT (escape hatch: manda em tudo).
  2. Uma pasta AFT que JA EXISTA com conteudo, entre os candidatos - nunca
     abandona os dados de quem instalou antes desta correcao.
  3. <Documentos real>/AFT (o caminho canonico).

Uso como biblioteca:
    from pasta_aft import pasta_aft, pasta_os_ativas, garantir_estrutura
Uso no terminal (diagnostico):
    python pasta_aft.py            # mostra o que resolveu, sem criar nada
    python pasta_aft.py --criar    # cria AFT/OS ATIVAS e OS ARQUIVADAS
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

SUBPASTAS = ("OS ATIVAS", "OS ARQUIVADAS")


def _documentos_registro() -> Path | None:
    """Pasta Documentos pelo registro do Windows - a fonte da verdade.
    Cobre OneDrive e idioma de uma vez. None fora do Windows ou se falhar."""
    if not sys.platform.startswith("win"):
        return None
    try:
        import winreg
        chave = r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders"
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, chave) as k:
            bruto, _ = winreg.QueryValueEx(k, "Personal")
        # O valor costuma vir com variaveis: %USERPROFILE%\OneDrive\Documentos
        caminho = Path(os.path.expandvars(bruto))
        return caminho if caminho.is_dir() else None
    except Exception:
        return None


def candidatos_documentos() -> list[Path]:
    """Candidatos a pasta Documentos, do mais confiavel ao menos. O primeiro
    que existir e a resposta; a lista tambem serve para procurar uma pasta AFT
    ja criada em qualquer um deles."""
    home = Path.home()
    vistos: list[Path] = []

    def juntar(p: Path | None) -> None:
        if p and p not in vistos:
            vistos.append(p)

    juntar(_documentos_registro())
    # OneDrive por variavel de ambiente (Windows sem registro legivel).
    for var in ("OneDriveCommercial", "OneDrive", "OneDriveConsumer"):
        raiz = os.environ.get(var)
        if raiz:
            for nome in ("Documentos", "Documents"):
                juntar(Path(raiz) / nome)
    # Caminhos diretos (macOS/Linux e Windows sem redirecionamento).
    for nome in ("Documents", "Documentos"):
        juntar(home / nome)
    return vistos


def documentos() -> Path:
    """A pasta Documentos real do usuario. Se nenhuma existir (caso raro),
    devolve ~/Documents como ultimo recurso - ai ela sera criada."""
    for c in candidatos_documentos():
        if c.is_dir():
            return c
    return Path.home() / "Documents"


def _tem_conteudo(aft: Path) -> bool:
    """A pasta AFT ja e usada de verdade? (tem OS ATIVAS/ARQUIVADAS ou config)"""
    if not aft.is_dir():
        return False
    if (aft / "aft-config.md").is_file():
        return True
    for sub in SUBPASTAS:
        d = aft / sub
        if d.is_dir() and any(d.iterdir()):
            return True
    return False


def pasta_aft() -> Path:
    """A pasta de trabalho do AFT. Ver a ordem de resolucao no docstring."""
    env = os.environ.get("PASTA_AFT")
    if env and env.strip():
        return Path(env.strip()).expanduser()

    candidatas = [d / "AFT" for d in candidatos_documentos()]
    # 1) Uma que ja tenha dados - prioridade absoluta (nao abandona ninguem).
    for c in candidatas:
        if _tem_conteudo(c):
            return c
    # 2) Uma que ao menos exista.
    for c in candidatas:
        if c.is_dir():
            return c
    # 3) O caminho canonico (sera criado).
    return documentos() / "AFT"


def pasta_os_ativas() -> Path:
    return pasta_aft() / "OS ATIVAS"


def diagnostico() -> dict:
    """Tudo que o /aft-doctor precisa saber para explicar a situacao."""
    aft = pasta_aft()
    docs = documentos()
    canonico = docs / "AFT"
    # Outras pastas AFT existentes (instalacao anterior no lugar errado).
    outras = [str(d / "AFT") for d in candidatos_documentos()
              if (d / "AFT").is_dir() and (d / "AFT") != aft]
    # "Fora do lugar": a pasta em uso NAO e a da Documentos real. Acontece com
    # quem instalou antes desta correcao - o mkdir cru criou ~/Documents/AFT,
    # os dados foram para la, e o AFT nao acha a pasta pelo Explorer.
    fora = aft.is_dir() and aft != canonico and not os.environ.get("PASTA_AFT")
    return {
        "pasta_aft": str(aft),
        "documentos": str(docs),
        "canonico": str(canonico),
        "existe": aft.is_dir(),
        "faltando": [s for s in SUBPASTAS if not (aft / s).is_dir()],
        "redirecionada": docs != Path.home() / "Documents",
        "onedrive": "onedrive" in str(docs).lower(),
        "duplicadas": outras,
        "por_env": bool(os.environ.get("PASTA_AFT")),
        "fora_do_lugar": fora,
        "destino_sugerido": str(canonico) if fora else "",
    }


def _atualizar_path_windows(config: Path, destino: Path) -> bool:
    """Reescreve `path_windows:` no aft-config.md apos a mudanca de pasta.
    Melhor esforco: se nao der, o /aft-setup conserta depois."""
    try:
        import re
        texto = config.read_text(encoding="utf-8")
        if "path_windows:" not in texto:
            return False
        # Caminho no formato Windows, com as barras escapadas do YAML.
        win = str(destino)
        if sys.platform.startswith("win"):
            win = win.replace("/", "\\")
        novo = re.sub(r'^path_windows\s*:.*$',
                      'path_windows: "%s"' % win.replace("\\", "\\\\"),
                      texto, count=1, flags=re.MULTILINE)
        if novo != texto:
            config.write_text(novo, encoding="utf-8")
            return True
    except Exception:
        pass
    return False


def mover_para_canonico() -> dict:
    """Move a pasta AFT em uso para a Documentos real. NUNCA sobrescreve:
    se o destino ja tiver dados, recusa e explica. Devolve um relatorio."""
    import shutil

    origem = pasta_aft()
    destino = documentos() / "AFT"
    if origem == destino:
        return {"ok": True, "movido": False, "motivo": "ja esta no lugar certo",
                "pasta_aft": str(destino)}
    if not origem.is_dir():
        return {"ok": False, "movido": False,
                "erro": f"a pasta de origem nao existe: {origem}"}
    if destino.is_dir():
        if any(destino.iterdir()):
            return {"ok": False, "movido": False,
                    "erro": (f"o destino ja existe e tem conteudo: {destino}. "
                             "Junte as duas a mao (mova as subpastas de "
                             f"'{origem / 'OS ATIVAS'}' para "
                             f"'{destino / 'OS ATIVAS'}') e apague a antiga.")}
        try:
            destino.rmdir()  # destino vazio: sai da frente
        except OSError as e:
            return {"ok": False, "movido": False,
                    "erro": f"nao consegui remover o destino vazio: {e}"}
    try:
        destino.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(origem), str(destino))
    except Exception as e:
        return {"ok": False, "movido": False,
                "erro": (f"falha ao mover ({type(e).__name__}: {e}). No Windows "
                         "isso costuma ser um servico do toolkit segurando um "
                         "arquivo: pare o vigia de sessoes e o servidor do "
                         "painel e tente de novo.")}
    cfg = destino / "aft-config.md"
    return {"ok": True, "movido": True, "de": str(origem),
            "pasta_aft": str(destino),
            "config_atualizado": _atualizar_path_windows(cfg, destino)
            if cfg.is_file() else False}


def garantir_estrutura() -> tuple[Path, list[str]]:
    """Cria a pasta AFT e as subpastas que faltarem. Idempotente e seguro:
    so cria diretorios, nunca apaga nem move nada. Devolve (pasta, criadas)."""
    aft = pasta_aft()
    criadas: list[str] = []
    if not aft.is_dir():
        aft.mkdir(parents=True, exist_ok=True)
        criadas.append(str(aft))
    for sub in SUBPASTAS:
        d = aft / sub
        if not d.is_dir():
            d.mkdir(parents=True, exist_ok=True)
            criadas.append(str(d))
    return aft, criadas


if __name__ == "__main__":
    import json
    if "--mover" in sys.argv:
        r = mover_para_canonico()
        print(json.dumps({**r, **diagnostico()}, ensure_ascii=False, indent=2))
        sys.exit(0 if r.get("ok") else 1)
    elif "--criar" in sys.argv:
        alvo, criadas = garantir_estrutura()
        print(json.dumps({"ok": True, "pasta_aft": str(alvo),
                          "criadas": criadas, **diagnostico()},
                         ensure_ascii=False, indent=2))
    else:
        print(json.dumps(diagnostico(), ensure_ascii=False, indent=2))
