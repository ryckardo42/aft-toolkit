#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""notebook_id.py - traduz a chave de um notebook (nr-12, ementario-sst) no ID
que a conta DESTE AFT enxerga.

Por que este script existe
--------------------------
Cada notebook do NotebookLM comporta 1.000 leitores. A cohort 1 (os notebooks
originais) lotou em 19/08/2026: o catalogo inteiro foi duplicado e quem se
cadastra desde entao entra na cohort 2, que enxerga as COPIAS - outros IDs para
o mesmo conteudo. Logo, nao existe mais "o ID da NR-12": existe o ID da NR-12
para a cohort do AFT.

Antes disso, treze SKILL.md carregavam a mesma linha copiada, lendo o ID direto
do config/notebooks.json. Com dois IDs por notebook essa linha nao teria o que
fazer, e cada nova cohort obrigaria a mexer nos treze arquivos. Agora este e o
unico lugar do toolkit que sabe o que e cohort; as skills so perguntam pela
chave.

Uso (e o que as skills chamam):
    python notebook_id.py nr-12          -> imprime o ID e sai com 0
    python notebook_id.py nr-12 --url    -> imprime o endereco do notebook
    python notebook_id.py --cohort       -> imprime a cohort resolvida (1, 2...)
    python notebook_id.py --listar       -> JSON: chave, titulo e ID de todas
    python notebook_id.py --json nr-12   -> JSON com chave, titulo, id, cohort

Codigos de saida (importam para quem chama):
    0  achou o ID
    2  a chave nao existe no mapa            -> erro de quem chamou
    3  o notebook nao existe para esta cohort -> NAO e erro: a skill segue sem
       essa camada, em silencio, como ja faz quando falta a chave 'interdicoes'
    4  o mapa config/notebooks.json nao foi encontrado

De onde sai a cohort, nesta ordem:
    1. variavel de ambiente AFT_COHORT (escape hatch de teste)
    2. campo `notebooklm_cohort:` do aft-config.md - a fonte normal
    3. sondagem: quais IDs ja estao na colecao da conta (notebooklm list) e,
       se a colecao estiver vazia, qual dos dois IDs o servidor entrega
       (notebooklm metadata). So roda quando o campo esta ausente, e grava o
       resultado no aft-config.md para nao repetir. Ver sondar_cohort().
    4. cohort 1 - o palpite conservador de quem instalou antes da duplicacao
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
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

URL_NOTEBOOK = "https://notebooklm.google.com/notebook/{}"
COHORT_PADRAO = 1
TIMEOUT_SONDA = 45  # s - o gancho de reautenticacao do CLI pode gastar ~25 s

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


# ---------------------------------------------------------------- o mapa

def caminho_mapa() -> Path | None:
    aqui = Path(__file__).resolve()
    for base in (aqui.parent, *aqui.parents):
        alvo = base / "config" / "notebooks.json"
        if alvo.is_file():
            return alvo
    return None


def mapa() -> dict:
    alvo = caminho_mapa()
    if alvo is None:
        return {}
    return json.loads(alvo.read_text(encoding="utf-8"))


# ---------------------------------------------------------------- a cohort

def _config_aft() -> Path | None:
    """O aft-config.md, sem presumir onde fica a pasta de trabalho."""
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from pasta_aft import pasta_aft  # noqa: WPS433
        cfg = pasta_aft() / "aft-config.md"
        return cfg if cfg.is_file() else None
    except Exception:
        return None


def cohort_do_config() -> int | None:
    cfg = _config_aft()
    if cfg is None:
        return None
    try:
        for linha in cfg.read_text(encoding="utf-8").splitlines():
            m = re.match(r'\s*notebooklm_cohort\s*:\s*"?(\d+)"?\s*(?:#.*)?$', linha)
            if m:
                return int(m.group(1))
    except Exception:
        pass
    return None


def gravar_cohort(valor: int) -> bool:
    """Grava (ou corrige) o campo no aft-config.md, dentro do bloco de config."""
    cfg = _config_aft()
    if cfg is None:
        return False
    try:
        linhas = cfg.read_text(encoding="utf-8").splitlines(keepends=True)
    except Exception:
        return False
    nova = f'notebooklm_cohort: "{valor}"\n'
    for i, linha in enumerate(linhas):
        if re.match(r'\s*notebooklm_cohort\s*:', linha):
            linhas[i] = nova
            break
    else:
        # Logo abaixo do gmail/notebooklm_browser, que e onde mora o assunto.
        alvo = next(
            (i for i, l in enumerate(linhas)
             if re.match(r'\s*(gmail|notebooklm_browser)\s*:', l)),
            None,
        )
        bloco = [
            "# Cohort do NotebookLM (1 = notebooks originais; 2 = copias, para quem\n",
            "# se cadastrou depois de 19/08/2026). Sai do portal notebooks-aft:\n",
            nova,
        ]
        if alvo is None:
            fim = next((i for i, l in enumerate(linhas) if i and l.strip() == "---"), len(linhas))
            linhas[fim:fim] = bloco
        else:
            linhas[alvo + 1:alvo + 1] = bloco
    try:
        cfg.write_text("".join(linhas), encoding="utf-8")
        return True
    except Exception:
        return False


def _rodar(cli: str, *args: str) -> tuple[int, str]:
    try:
        r = subprocess.run(
            [cli, "--quiet", *args],
            capture_output=True, text=True, timeout=TIMEOUT_SONDA,
            encoding="utf-8", errors="replace",
        )
    except (subprocess.TimeoutExpired, OSError):
        return 1, ""
    return r.returncode, ((r.stdout or "") + "\n" + (r.stderr or ""))


def _pares(m: dict) -> list:
    """Notebooks que distinguem cohort: os que tem ID diferente em cada uma.

    Os de link publico tem o mesmo endereco para todos e nao provam nada.
    Essenciais primeiro: sao os que o AFT mais provavelmente ja tem.
    """
    itens = [
        (info.get("essencial") or 99, info["ids"])
        for info in m.get("notebooks", {}).values()
        if not info.get("publico") and len(info.get("ids", {})) > 1
    ]
    return [ids for _, ids in sorted(itens, key=lambda x: x[0])]


def _sondar_por_metadata(cli: str, m: dict) -> int | None:
    """Ultimo recurso: pergunta ao servidor, notebook por notebook, qual cohort
    esta conta alcanca.

    Existe por causa do AFT que acabou de se cadastrar: se ele pedir uma ementa
    ANTES de abrir qualquer notebook no navegador, a colecao esta vazia e o
    `list` nao tem o que dizer. O `metadata` nao depende disso - responde pelo
    compartilhamento, e foi medido respondendo a notebook nunca aberto (ver o
    campo `por_sondagem` do notebooklm_acesso.py, instalacao Windows 06/08/2026).

    Custa 1 RPC por tentativa, entao para no primeiro acerto e testa no maximo
    dois notebooks - a cohort ATIVA primeiro, que e a de quem se cadastra hoje.
    Medido em ~4 s no pior caso.

    Pegadinha conhecida: quem alcanca os DOIS lados (o mantenedor, dono das
    copias) recebe a cohort ativa, nao a sua. Nao atrapalha - para ele a etapa 1
    ja respondeu -, mas nao use este atalho isoladamente para diagnosticar.
    """
    ativa = str(m.get("cohort_ativa") or 2)
    for ids in _pares(m)[:2]:
        ordem = sorted(ids, key=lambda c: (c != ativa, c))
        for cohort in ordem:
            codigo, saida = _rodar(cli, "metadata", "-n", ids[cohort], "--json")
            if codigo == 0 and '"error"' not in saida:
                return int(cohort)
            if any(p in saida.lower() for p in
                   ("not authenticated", "session expired", "not logged in")):
                return None  # e problema de login, nao de cohort
    return None


def sondar_cohort(m: dict | None = None) -> int | None:
    """Descobre a cohort do AFT, em duas tentativas.

    1. Pelos notebooks que JA estao na colecao da conta. O `notebooklm list`
       devolve os vistos recentemente - ou seja, os que o AFT ja abriu no
       navegador. Como cada um so recebe acesso aos da sua cohort, basta ver de
       que lado caem os IDs conhecidos. E barato: uma chamada para tudo.
    2. Colecao vazia (o AFT acabou de se cadastrar e ainda nao abriu nada) ->
       pergunta ao servidor, com `metadata`, qual dos dois IDs ele alcanca.

    Devolve None so quando nada disso conclui: sem CLI, sem sessao, ou sem
    acesso concedido ainda.
    """
    cli = shutil.which("notebooklm")
    if not cli:
        return None
    m = m if m is not None else mapa()
    codigo, saida = _rodar(cli, "list", "--json")
    if codigo != 0:
        return None
    vistos = set(re.findall(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
                            saida.lower()))
    placar: dict[int, int] = {}
    for ids in _pares(m):
        for cohort, nid in ids.items():
            if nid.lower() in vistos:
                placar[int(cohort)] = placar.get(int(cohort), 0) + 1
    if placar:
        return max(placar, key=placar.get)
    return _sondar_por_metadata(cli, m)


def cohort(m: dict | None = None, sondar: bool = True) -> int:
    env = os.environ.get("AFT_COHORT", "").strip()
    if env.isdigit():
        return int(env)
    do_config = cohort_do_config()
    if do_config is not None:
        return do_config
    if sondar:
        achada = sondar_cohort(m)
        if achada is not None:
            gravar_cohort(achada)
            return achada
    return COHORT_PADRAO


# ---------------------------------------------------------------- resolucao

def resolver(chave: str, m: dict | None = None, c: int | None = None) -> dict:
    """{'estado': ok|sem-mapa|chave-desconhecida|sem-copia, 'id', 'titulo', ...}"""
    m = m if m is not None else mapa()
    if not m:
        return {"estado": "sem-mapa"}
    info = m.get("notebooks", {}).get(chave)
    if info is None:
        return {"estado": "chave-desconhecida", "chave": chave}
    c = c if c is not None else cohort(m)
    ids = info.get("ids", {})
    # Link publico: mesmo endereco para todas as cohorts, sem teto de leitores.
    nid = ids.get("1") if info.get("publico") else ids.get(str(c))
    base = {"chave": chave, "titulo": info.get("title", chave), "cohort": c,
            "publico": bool(info.get("publico"))}
    if not nid:
        return {**base, "estado": "sem-copia"}
    return {**base, "estado": "ok", "id": nid, "url": URL_NOTEBOOK.format(nid)}


SAIDA = {"ok": 0, "chave-desconhecida": 2, "sem-copia": 3, "sem-mapa": 4}


def main(argv: list[str]) -> int:
    args = [a for a in argv if not a.startswith("--")]
    flags = {a for a in argv if a.startswith("--")}
    m = mapa()

    if "--cohort" in flags:
        print(cohort(m))
        return 0

    if "--listar" in flags:
        c = cohort(m)
        itens = []
        for chave in sorted(m.get("notebooks", {})):
            r = resolver(chave, m, c)
            itens.append({k: r.get(k) for k in ("chave", "titulo", "estado", "id", "url")})
        print(json.dumps({"cohort": c, "notebooks": itens}, ensure_ascii=False))
        return 0

    if not args:
        print("uso: notebook_id.py <chave>  |  --cohort  |  --listar", file=sys.stderr)
        return 2

    r = resolver(args[0], m)
    if "--json" in flags:
        print(json.dumps(r, ensure_ascii=False))
        return SAIDA.get(r["estado"], 1)

    if r["estado"] == "ok":
        print(r["url"] if "--url" in flags else r["id"])
        return 0
    if r["estado"] == "sem-copia":
        print(f"notebook '{args[0]}' nao existe para a cohort {r['cohort']}", file=sys.stderr)
    elif r["estado"] == "chave-desconhecida":
        print(f"chave '{args[0]}' nao esta em config/notebooks.json", file=sys.stderr)
    else:
        print("config/notebooks.json nao encontrado", file=sys.stderr)
    return SAIDA.get(r["estado"], 1)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
