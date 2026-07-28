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
  2. O PONTEIRO ~/.claude/aft-pasta.txt - a escolha explicita do AFT, gravada
     pelo /aft-setup ou pelo /aft-doctor. Fica FORA do repositorio das skills
     (~/.claude/skills), entao `git pull` / /aft-atualizar nunca a desfaz.
  3. Uma pasta AFT que JA EXISTA com conteudo, entre os candidatos - nunca
     abandona os dados de quem instalou antes desta correcao.
  4. <Documentos real>/AFT (o caminho canonico).

A subpasta "OS ATIVAS" pode ainda ser redirecionada sozinha pelo campo
`pasta_os:` do aft-config.md (mecanismo antigo do /aft-painel, mantido por
compatibilidade). Ela nao tem o problema do ovo-e-galinha do ponteiro: o
aft-config.md e achado DEPOIS de resolver a pasta AFT.

Uso como biblioteca:
    from pasta_aft import pasta_aft, pasta_os_ativas, garantir_estrutura
Uso no terminal (diagnostico):
    python pasta_aft.py                    # mostra o que resolveu, sem criar
    python pasta_aft.py --criar            # cria AFT/OS ATIVAS e OS ARQUIVADAS
    python pasta_aft.py --path             # so o caminho da pasta AFT
    python pasta_aft.py --os-ativas        # so o caminho de OS ATIVAS
    python pasta_aft.py --definir "<dir>"  # fixa a pasta (grava o ponteiro)
    python pasta_aft.py --definir "<dir>" --mover   # fixa E leva os dados
    python pasta_aft.py --mover            # move para a Documentos real
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

SUBPASTAS = ("OS ATIVAS", "OS ARQUIVADAS")

# Onde fica gravada a escolha do AFT. Mora em ~/.claude/ e NAO em
# ~/.claude/skills/ de proposito: skills/ e o repositorio git do toolkit, e um
# arquivo la dentro seria sobrescrito (ou ignorado) a cada /aft-atualizar.
PONTEIRO = Path.home() / ".claude" / "aft-pasta.txt"

_CABECALHO_PONTEIRO = (
    "# Onde fica a sua pasta de trabalho do AFT Toolkit (OS ATIVAS mora dentro).\n"
    "# Gravado pelo /aft-setup ou pelo /aft-doctor - pode editar a mao: uma linha\n"
    "# com o caminho da pasta. Este arquivo fica FORA do repositorio das skills,\n"
    "# entao atualizar o toolkit (/aft-atualizar) nunca mexe nele.\n"
)


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


def ponteiro_ler() -> Path | None:
    """A pasta que o AFT escolheu, se ele escolheu alguma. Tolerante: aceita
    comentarios com # e ignora linhas em branco. Nunca levanta excecao - um
    ponteiro ilegivel apenas nao vale, e a resolucao segue para os candidatos."""
    try:
        if not PONTEIRO.is_file():
            return None
        for linha in PONTEIRO.read_text(encoding="utf-8").splitlines():
            linha = linha.strip().strip('"')
            if linha and not linha.startswith("#"):
                return Path(os.path.expandvars(linha)).expanduser()
    except Exception:
        pass
    return None


def ponteiro_gravar(destino: Path) -> bool:
    """Fixa a pasta de trabalho. Melhor esforco: devolve False se nao der."""
    try:
        PONTEIRO.parent.mkdir(parents=True, exist_ok=True)
        PONTEIRO.write_text(_CABECALHO_PONTEIRO + str(destino) + "\n",
                            encoding="utf-8")
        return True
    except Exception:
        return False


def ponteiro_apagar() -> bool:
    """Volta ao automatico (a pasta deixa de ser fixada)."""
    try:
        if PONTEIRO.is_file():
            PONTEIRO.unlink()
        return True
    except Exception:
        return False


def _origem() -> str:
    """De onde veio o caminho em uso - o /aft-doctor explica isso ao AFT."""
    if os.environ.get("PASTA_AFT", "").strip():
        return "env"
    if ponteiro_ler():
        return "ponteiro"
    candidatas = [d / "AFT" for d in candidatos_documentos()]
    if any(_tem_conteudo(c) for c in candidatas):
        return "dados"
    if any(c.is_dir() for c in candidatas):
        return "existente"
    return "canonico"


def pasta_aft() -> Path:
    """A pasta de trabalho do AFT. Ver a ordem de resolucao no docstring."""
    env = os.environ.get("PASTA_AFT")
    if env and env.strip():
        return Path(env.strip()).expanduser()

    # A escolha explicita do AFT vence os palpites automaticos.
    escolhida = ponteiro_ler()
    if escolhida:
        return escolhida

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


def _pasta_os_do_config(aft: Path) -> Path | None:
    """Campo `pasta_os:` do aft-config.md - permite deixar so a OS ATIVAS em
    outro lugar (mecanismo antigo do /aft-painel, mantido por compatibilidade)."""
    try:
        cfg = aft / "aft-config.md"
        if not cfg.is_file():
            return None
        import re
        for linha in cfg.read_text(encoding="utf-8").splitlines():
            m = re.match(r'\s*pasta_os\s*:\s*"?([^"#]+?)"?\s*$', linha)
            if m and m.group(1).strip():
                return Path(os.path.expandvars(m.group(1).strip())).expanduser()
    except Exception:
        pass
    return None


def pasta_os_ativas() -> Path:
    aft = pasta_aft()
    legado = _pasta_os_do_config(aft)
    # So obedece o campo antigo se ele ainda apontar para uma pasta DE VERDADE.
    # Sem isso, um `pasta_os:` que ficou para tras (ex.: a pasta mudou de lugar
    # e o campo continuou com o caminho velho) mandaria o painel, o vigia e o
    # doctor lerem uma pasta inexistente - e todos diriam "0 empresas" sem erro.
    if legado and legado.is_dir():
        return legado
    return aft / "OS ATIVAS"


def _realinhar_pasta_os(cfg: Path, origem: Path, destino: Path) -> bool:
    """Depois de mudar a pasta de trabalho de lugar, o campo antigo `pasta_os:`
    fica apontando para o caminho de antes. Se ele morava DENTRO da pasta
    antiga (caso comum: e so o padrao escrito por extenso), reescreve para o
    lugar novo. Se apontava para outro canto, o AFT quis a OS separada - nao
    mexe."""
    try:
        if not cfg.is_file():
            return False
        import re
        texto = cfg.read_text(encoding="utf-8")
        m = re.search(r'^(\s*pasta_os\s*:\s*)"?([^"#\n]+?)"?\s*$', texto,
                      flags=re.MULTILINE)
        if not m:
            return False
        atual = Path(os.path.expandvars(m.group(2).strip())).expanduser()
        try:
            relativo = atual.relative_to(origem)
        except ValueError:
            return False  # aponta para fora da pasta antiga: escolha do AFT
        novo = re.sub(r'^(\s*pasta_os\s*:\s*).*$',
                      lambda mm: f'{mm.group(1)}"{destino / relativo}"',
                      texto, count=1, flags=re.MULTILINE)
        if novo != texto:
            cfg.write_text(novo, encoding="utf-8")
            return True
    except Exception:
        pass
    return False


def definir(destino: Path, mover: bool = False) -> dict:
    """Fixa a pasta de trabalho no ponteiro. Com mover=True, leva os dados que
    ja existem para la antes de fixar. Nunca sobrescreve nada."""
    destino = Path(os.path.expandvars(str(destino))).expanduser()
    if not destino.is_absolute():
        # Um caminho relativo iria parar no ponteiro e, depois, ser resolvido
        # contra a pasta de onde cada script foi chamado - lugar diferente a
        # cada execucao. Fixa agora, contra a pasta atual.
        destino = destino.absolute()
    if destino.name.upper() in SUBPASTAS:
        # Erro classico: apontar para a "OS ATIVAS" em vez da pasta que a contem.
        return {"ok": False, "erro": (
            f"'{destino}' e a subpasta de OS, nao a pasta de trabalho. Informe a "
            f"pasta que CONTEM 'OS ATIVAS' (ou seja: '{destino.parent}').")}

    relatorio: dict = {}
    if mover:
        relatorio = mover_para(destino)
        if not relatorio.get("ok"):
            return relatorio

    # Cria a estrutura DIRETO no destino - nao via garantir_estrutura(), que
    # resolveria a pasta de novo e poderia cair em outro lugar (ex.: com a
    # variavel de ambiente PASTA_AFT apontando para um terceiro caminho).
    criadas: list[str] = []
    try:
        for alvo in (destino, *(destino / s for s in SUBPASTAS)):
            if not alvo.is_dir():
                alvo.mkdir(parents=True, exist_ok=True)
                criadas.append(str(alvo))
    except Exception as e:
        return {"ok": False,
                "erro": f"nao consegui criar '{destino}' ({type(e).__name__}: {e})"}

    if not ponteiro_gravar(destino):
        return {"ok": False, "erro": (
            f"a pasta esta pronta em '{destino}', mas nao consegui gravar o "
            f"ponteiro '{PONTEIRO}' - verifique a permissao de escrita.")}

    cfg = destino / "aft-config.md"
    # O mover_para ja pode ter alinhado o path_windows; nao apague esse "True"
    # com o False do segundo passe (que nao acha mais nada para trocar).
    ja_alinhou = bool(relatorio.get("config_atualizado"))
    saida = {**relatorio, "ok": True, "pasta_aft": str(destino),
             "os_ativas": str(destino / "OS ATIVAS"),
             "ponteiro": str(PONTEIRO), "criadas": criadas,
             "config_atualizado": ja_alinhou or (
                 _atualizar_path_windows(cfg, destino) if cfg.is_file() else False)}

    # A variavel de ambiente vence o ponteiro na hora de resolver. Se ela
    # estiver apontando para outro lugar, o AFT acharia que mudou de pasta e
    # nada teria mudado de verdade - avise em vez de mentir "ok".
    env = os.environ.get("PASTA_AFT", "").strip()
    if env and Path(env).expanduser() != destino:
        saida["aviso"] = (
            f"a pasta foi fixada em '{destino}', mas a variavel de ambiente "
            f"PASTA_AFT='{env}' tem prioridade e continuara valendo enquanto "
            "existir. Remova essa variavel para a escolha valer.")
    return saida


def diagnostico() -> dict:
    """Tudo que o /aft-doctor precisa saber para explicar a situacao."""
    aft = pasta_aft()
    docs = documentos()
    canonico = docs / "AFT"
    # Outras pastas AFT existentes (instalacao anterior no lugar errado).
    outras = [str(d / "AFT") for d in candidatos_documentos()
              if (d / "AFT").is_dir() and (d / "AFT") != aft]
    origem = _origem()
    # "Fora do lugar": a pasta em uso NAO e a da Documentos real POR ACIDENTE.
    # Acontece com quem instalou antes da correcao de 22/07/2026 - o mkdir cru
    # criou ~/Documents/AFT, os dados foram para la, e o AFT nao acha a pasta
    # pelo Explorer. Se o caminho veio do ponteiro ou do env, a pasta esta onde
    # o AFT MANDOU: nao e defeito, e escolha - nao reclame dela.
    escolhida = origem in ("env", "ponteiro")
    fora = aft.is_dir() and aft != canonico and not escolhida
    return {
        "pasta_aft": str(aft),
        "os_ativas": str(pasta_os_ativas()),
        "documentos": str(docs),
        "canonico": str(canonico),
        "existe": aft.is_dir(),
        "faltando": [s for s in SUBPASTAS if not (aft / s).is_dir()],
        "redirecionada": docs != Path.home() / "Documents",
        "onedrive": "onedrive" in str(docs).lower(),
        "duplicadas": outras,
        "origem": origem,
        "escolhida": escolhida,
        "ponteiro": str(PONTEIRO),
        "ponteiro_existe": PONTEIRO.is_file(),
        "por_env": origem == "env",
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


def mover_para(destino: Path | None = None) -> dict:
    """Move a pasta AFT em uso para `destino` (por omissao, a Documentos real).
    NUNCA sobrescreve: se o destino ja tiver dados, recusa e explica."""
    import shutil

    origem = pasta_aft()
    if destino:
        destino = Path(os.path.expandvars(str(destino))).expanduser()
        if not destino.is_absolute():
            destino = destino.absolute()
    else:
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
    # O ponteiro guardava a pasta ANTIGA - que acabou de deixar de existir. Sem
    # reescrever, a proxima execucao resolveria para um caminho morto e o
    # garantir_estrutura() criaria uma pasta vazia no lugar: todas as OS
    # sumiriam da vista do AFT sem nenhuma mensagem de erro.
    ponteiro_realinhado = ponteiro_gravar(destino) if PONTEIRO.is_file() else False
    return {"ok": True, "movido": True, "de": str(origem),
            "pasta_aft": str(destino),
            "os_ativas": str(destino / "OS ATIVAS"),
            "ponteiro_realinhado": ponteiro_realinhado,
            "pasta_os_realinhado": _realinhar_pasta_os(cfg, origem, destino),
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

    def _valor(flag: str) -> str | None:
        """O argumento que vem depois de `flag` (ou None)."""
        if flag in sys.argv:
            i = sys.argv.index(flag)
            if i + 1 < len(sys.argv) and not sys.argv[i + 1].startswith("--"):
                return sys.argv[i + 1]
        return None

    # Acessores enxutos: as skills chamam estes e usam a saida como caminho.
    # Uma linha, sem JSON, para poder ir direto num comando.
    if "--path" in sys.argv:
        print(pasta_aft())
    elif "--os-ativas" in sys.argv:
        print(pasta_os_ativas())
    elif any(a.split("=")[0] == "--definir" for a in sys.argv[1:]):
        alvo = _valor("--definir")
        if not alvo:
            print(json.dumps({"ok": False, "erro": (
                'informe a pasta separada por espaco: '
                '--definir "<caminho>" [--mover]')},
                ensure_ascii=False, indent=2))
            sys.exit(1)
        r = definir(Path(alvo), mover="--mover" in sys.argv)
        # O relatorio da operacao vem DEPOIS do diagnostico: quem acabou de
        # mudar a pasta sabe melhor onde ela esta do que uma releitura.
        print(json.dumps({**diagnostico(), **r}, ensure_ascii=False, indent=2))
        sys.exit(0 if r.get("ok") else 1)
    elif "--soltar" in sys.argv:  # volta a resolucao automatica
        ok = ponteiro_apagar()
        print(json.dumps({**diagnostico(), "ok": ok, "ponteiro_apagado": ok},
                         ensure_ascii=False, indent=2))
        sys.exit(0 if ok else 1)
    elif "--mover" in sys.argv:
        r = mover_para(Path(_valor("--mover")) if _valor("--mover") else None)
        print(json.dumps({**diagnostico(), **r}, ensure_ascii=False, indent=2))
        sys.exit(0 if r.get("ok") else 1)
    elif "--criar" in sys.argv:
        alvo, criadas = garantir_estrutura()
        print(json.dumps({"ok": True, "pasta_aft": str(alvo),
                          "criadas": criadas, **diagnostico()},
                         ensure_ascii=False, indent=2))
    else:
        print(json.dumps(diagnostico(), ensure_ascii=False, indent=2))
