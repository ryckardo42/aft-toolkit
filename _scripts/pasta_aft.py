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


def _ext(p) -> str:
    """Caminho no formato ESTENDIDO do Windows (\\\\?\\C:\\...), que dispensa o
    limite de 260 caracteres (MAX_PATH).

    Por que isto existe: as pastas de notificacao baixadas do DET aninham muito
    (OS ATIVAS\\<EMPRESA>\\notificacao-XXX\\NOTIFICACAO_XXX\\NOTIFICACAO_XXX\\
    ITEM_NN_<descricao>\\<arquivo>.pdf) e estouram os 260 caracteres com
    facilidade. Sem este prefixo, o proprio Python nao ENXERGA esses arquivos:
    exists() e is_file() devolvem False e a copia os pula em silencio - foi o
    que aconteceu num teste real (28/07/2026), em que 6 PDFs de uma analise de
    acidente fatal (ASO, PCMSO, CAF/CEF) ficaram para tras.

    Fora do Windows nao ha limite: devolve o caminho como esta."""
    if not sys.platform.startswith("win"):
        return str(p)
    bruto = os.path.abspath(str(p))
    if bruto.startswith("\\\\?\\"):
        return bruto
    if bruto.startswith("\\\\"):  # rede: \\servidor\compartilhamento
        return "\\\\?\\UNC\\" + bruto[2:]
    return "\\\\?\\" + bruto


def _copiar_arvore(origem: Path, destino: Path) -> list[str]:
    """Copia origem -> destino SEMPRE por caminho estendido. Devolve a lista de
    erros (vazia = copia integral). Nao apaga nada: quem apaga e o mover_para,
    e so depois de conferir."""
    import shutil
    erros: list[str] = []
    raiz, alvo_raiz = _ext(origem), _ext(destino)
    for atual, _dirs, arqs in os.walk(raiz):
        rel = os.path.relpath(atual, raiz)
        alvo = alvo_raiz if rel == "." else os.path.join(alvo_raiz, rel)
        try:
            os.makedirs(alvo, exist_ok=True)
        except Exception as e:
            erros.append(f"{rel}: {type(e).__name__}: {e}")
            continue
        for a in arqs:
            try:
                shutil.copy2(os.path.join(atual, a), os.path.join(alvo, a))
            except Exception as e:
                erros.append(f"{os.path.join(rel, a)}: {type(e).__name__}: {e}")
    return erros


def _medir_arvore(alvo: Path) -> tuple[int, int]:
    """(quantidade de arquivos, soma dos bytes) - a conferencia da copia."""
    n = tam = 0
    for atual, _dirs, arqs in os.walk(_ext(alvo)):
        for a in arqs:
            try:
                tam += os.path.getsize(os.path.join(atual, a))
                n += 1
            except Exception:
                pass
    return n, tam


def _apagar_arvore(alvo: Path) -> list[str]:
    """Apaga a arvore de baixo para cima, por caminho estendido. Devolve os
    caminhos que resistiram - normalmente pastas que algum programa mantem
    abertas (o Windows nao deixa remover o diretorio de trabalho de um
    processo). Arquivo que resiste e problema; pasta VAZIA que resiste, nao."""
    resistiram: list[str] = []
    for atual, dirs, arqs in os.walk(_ext(alvo), topdown=False):
        for a in arqs:
            try:
                os.remove(os.path.join(atual, a))
            except Exception:
                resistiram.append(os.path.join(atual, a))
        for d in dirs:
            try:
                os.rmdir(os.path.join(atual, d))
            except Exception:
                resistiram.append(os.path.join(atual, d))
    try:
        os.rmdir(_ext(alvo))
    except Exception:
        resistiram.append(str(alvo))
    return resistiram


def mover_para(destino: Path | None = None) -> dict:
    """Move a pasta AFT em uso para `destino` (por omissao, a Documentos real).
    NUNCA sobrescreve: se o destino ja tiver dados, recusa e explica.

    Estrategia em dois tempos:
      1. os.rename - instantaneo, atomico, mesmo volume. E o caminho feliz.
      2. Se o rename for negado (a pasta esta aberta por algum programa - a
         propria sessao do Claude Code, por exemplo) ou for outro disco (o caso
         do HD externo), cai para COPIAR-CONFERIR-APAGAR, sempre com caminho
         estendido. A origem so e apagada depois que a copia confere em numero
         de arquivos e em bytes; se algo falhar no meio, a copia parcial e
         desfeita e a origem fica intacta."""
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
        # "Tem conteudo" = tem ARQUIVO. Pasta vazia nao e dado do AFT: costuma
        # ser o esqueleto que uma mudanca anterior deixou para tras, quando o
        # Windows nao deixou remover um diretorio aberto em algum programa (o
        # caso classico: a pasta que a propria sessao do Claude Code usa como
        # diretorio de trabalho). Recusar por causa dele impediria o AFT de
        # voltar a pasta para o lugar de onde ela saiu.
        n_dest, _ = _medir_arvore(destino)
        if n_dest:
            return {"ok": False, "movido": False,
                    "erro": (f"'{destino}' ja existe e tem {n_dest} arquivo(s) "
                             f"dentro - nao vou escrever por cima. Escolha uma "
                             f"pasta vazia (ou uma que ainda nao exista), ou "
                             f"junte as duas a mao antes de tentar de novo.")}
        try:
            destino.rmdir()  # esqueleto vazio: sai da frente se puder
        except OSError:
            pass  # nao saiu: a copia escreve dentro dele mesmo
    try:
        destino.parent.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        return {"ok": False, "movido": False,
                "erro": f"nao consegui criar '{destino.parent}' ({e})"}

    n_origem, bytes_origem = _medir_arvore(origem)
    sobras: list[str] = []
    try:
        os.rename(origem, destino)  # caminho feliz: instantaneo
        modo = "rename"
    except OSError:
        # Negado (pasta aberta por um programa) ou outro disco: copia conferida.
        modo = "copia"
        erros = _copiar_arvore(origem, destino)
        if erros:
            _apagar_arvore(destino)  # nao deixa copia parcial de dado sigiloso
            amostra = "; ".join(erros[:3])
            return {"ok": False, "movido": False, "erros": erros,
                    "erro": (f"a copia falhou em {len(erros)} item(ns) e foi "
                             f"desfeita - nada foi perdido, a pasta continua em "
                             f"'{origem}'. Primeiros casos: {amostra}")}
        n_dest, bytes_dest = _medir_arvore(destino)
        if (n_dest, bytes_dest) != (n_origem, bytes_origem):
            _apagar_arvore(destino)
            return {"ok": False, "movido": False,
                    "erro": (f"a copia saiu diferente do original "
                             f"({n_dest} arquivos/{bytes_dest} bytes contra "
                             f"{n_origem}/{bytes_origem}) e foi desfeita - nada "
                             f"foi perdido, a pasta continua em '{origem}'.")}
        # So agora a origem pode sair. Pasta VAZIA que resistir (por estar
        # aberta em algum programa) fica para tras sem prejuizo: os dados ja
        # estao no destino conferidos.
        resistiram = _apagar_arvore(origem)
        sobras = [c for c in resistiram if os.path.isfile(c)]
        # A COPIA JA CONFERIU: a mudanca esta consumada e precisa ser gravada.
        # Arquivo que resistiu ao apagamento (tipico: um .docx aberto no Word)
        # e apenas uma copia velha sobrando - virou aviso, nunca falha. Tratar
        # isso como erro seria pior: o ponteiro nao seria gravado e o toolkit
        # continuaria apontando para a pasta de origem, agora esvaziada.
    cfg = destino / "aft-config.md"
    # O ponteiro guardava a pasta ANTIGA - que acabou de deixar de existir. Sem
    # reescrever, a proxima execucao resolveria para um caminho morto e o
    # garantir_estrutura() criaria uma pasta vazia no lugar: todas as OS
    # sumiriam da vista do AFT sem nenhuma mensagem de erro.
    ponteiro_realinhado = ponteiro_gravar(destino) if PONTEIRO.is_file() else False
    # Pastas vazias que resistiram (estavam abertas em algum programa). Nao e
    # defeito: os arquivos ja foram conferidos no destino - so o esqueleto ficou.
    cascas = [c for c in (sobras or []) if not os.path.isfile(c)]
    if origem.is_dir():
        cascas.append(str(origem))
    saida_sobras = {}
    if sobras:
        nomes = ", ".join(os.path.basename(c) for c in sobras[:3])
        saida_sobras = {"sobras": sobras, "aviso_sobras": (
            f"a mudanca foi concluida e conferida, mas {len(sobras)} arquivo(s) "
            f"nao puderam ser apagados da pasta antiga porque estao abertos em "
            f"algum programa ({nomes}). A copia nova ja esta completa em "
            f"'{destino}': feche esses arquivos e apague '{origem}' quando quiser.")}
    return {"ok": True, "movido": True, "de": str(origem),
            "pasta_aft": str(destino),
            "os_ativas": str(destino / "OS ATIVAS"),
            "modo": modo,
            "arquivos": n_origem,
            "pastas_vazias_restantes": sorted(set(cascas)),
            **saida_sobras,
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
