#!/usr/bin/env python3
"""sessoes_os.py — 1 sessão do Claude Code por empresa fiscalizada, no grupo "OS ATIVAS".

Sincroniza as pastas de OS ATIVAS com a barra lateral do app do Claude Code:
cria (ou reaproveita) uma sessão por empresa, coloca todas no grupo "OS ATIVAS"
e grava o vínculo `sessao_claude:` no front-matter do memory.md de cada OS.

ATENÇÃO — usa o armazenamento interno do app (não documentado):
  - grupos:   claude_desktop_config.json → preferences.epitaxyPrefs.dframe-group-scopes
  - sessões:  claude-code-sessions/<conta>/<usuario>/local_<uuid>.json
O app REGRAVA o config enquanto está aberto; por isso o --aplicar espera o app
FECHAR antes de escrever (e reabre o app ao final). Sempre faz backup antes e
mantém um manifesto para o --desfazer. Se a estrutura interna não for
reconhecida (app mudou), o script ABORTA sem tocar em nada.

Uso:
    python3 sessoes_os.py --status              # o que existe e o que falta (não altera nada)
    python3 sessoes_os.py --aplicar             # vigia: espera o app fechar, aplica e reabre
    python3 sessoes_os.py --aplicar --agora     # aplica já (use só com o app fechado)
    python3 sessoes_os.py --aplicar --sem-reabrir
    python3 sessoes_os.py --desfazer            # restaura o último backup e remove o que criou

Saída do --status termina com uma linha JSON: para consumo pelas skills.
"""
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import time
import unicodedata
import uuid
from pathlib import Path

GRUPO_NOME = "OS ATIVAS"
AGORA_MS = lambda: int(time.time() * 1000)  # noqa: E731

IS_WIN = platform.system() == "Windows"
if IS_WIN:
    APP_SUPPORT = Path(os.environ.get("APPDATA", "")) / "Claude"
else:
    APP_SUPPORT = Path.home() / "Library" / "Application Support" / "Claude"
CONFIG = APP_SUPPORT / "claude_desktop_config.json"
SESSOES_ROOT = APP_SUPPORT / "claude-code-sessions"

PASTA_AFT = Path(os.environ.get("PASTA_AFT", Path.home() / "Documents" / "AFT"))
BACKUPS = PASTA_AFT / ".backups-sessoes"
MANIFESTO = PASTA_AFT / ".sessoes-os-manifesto.json"
LOG = PASTA_AFT / ".sessoes-os.log"


def log(msg):
    linha = f"[{time.strftime('%d/%m/%Y %H:%M:%S')}] {msg}"
    print(linha, flush=True)
    try:
        LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(linha + "\n")
    except OSError:
        pass


def pasta_os_ativas(cli=None):
    if cli:
        return Path(cli)
    p = PASTA_AFT / "OS ATIVAS"
    if p.is_dir() and any(p.iterdir()):
        return p
    antiga = Path.home() / "Documents" / "Cowork OS" / "AFT COWORK" / "OS ATIVAS"
    if not (p.is_dir() and any(p.iterdir())) and antiga.is_dir():
        log(f"AVISO: usando a pasta antiga ({antiga}) — OS ATIVAS nova vazia/ausente.")
        return antiga
    return p


def normaliza(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", s).strip().casefold()


def titulo_bate(titulo_sessao, empregador):
    a, b = normaliza(titulo_sessao), normaliza(empregador)
    if not a or not b:
        return False
    if a == b:
        return True
    menor, maior = (a, b) if len(a) <= len(b) else (b, a)
    return len(menor) >= 6 and maior.startswith(menor)


def ler_oss(pasta):
    """Lista as OS ativas: (pasta, empregador, sessao_claude_atual)."""
    oss = []
    for d in sorted(pasta.iterdir() if pasta.is_dir() else []):
        mem = d / "memory.md"
        if not d.is_dir() or not mem.is_file():
            continue
        texto = mem.read_text(encoding="utf-8", errors="replace")
        m = re.search(r"^empregador:\s*(.+)$", texto, re.MULTILINE)
        empregador = m.group(1).strip().strip('"') if m else d.name
        m = re.search(r"^sessao_claude:\s*\"?([\w-]+)\"?\s*$", texto, re.MULTILINE)
        oss.append({"pasta": d, "empregador": empregador,
                    "sessao": m.group(1) if m else None})
    return oss


def dir_sessoes():
    """Pasta <conta>/<usuario> com os local_*.json (a com mais sessões)."""
    candidatas = [d for d in SESSOES_ROOT.glob("*/*") if d.is_dir()]
    candidatas = [(len(list(d.glob("local_*.json"))), d) for d in candidatas]
    if not candidatas:
        return None
    return max(candidatas)[1]


def ler_sessoes(dir_s):
    sess = []
    for f in dir_s.glob("local_*.json"):
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if d.get("isArchived"):
            continue
        sess.append({"id": d.get("sessionId", f.stem), "titulo": d.get("title", ""),
                     "cwd": d.get("cwd", ""), "arquivo": f})
    return sess


def escopo_key(dir_s):
    return f"{dir_s.parent.name}/{dir_s.name}"


def carregar_config():
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    prefs = cfg.get("preferences", {}).get("epitaxyPrefs")
    if prefs is None:
        raise SystemExit("ERRO: estrutura do config não reconhecida "
                         "(preferences.epitaxyPrefs ausente) — nada foi alterado. "
                         "O app pode ter mudado o formato; rode /aft-atualizar.")
    return cfg


def plano(pasta_cli=None):
    """Monta o plano de sincronização (não altera nada)."""
    if not CONFIG.is_file():
        raise SystemExit(f"ERRO: config do app não encontrado: {CONFIG}")
    dir_s = dir_sessoes()
    if not dir_s:
        raise SystemExit("ERRO: pasta de sessões do app não encontrada.")
    cfg = carregar_config()
    escopo = escopo_key(dir_s)
    scopes = cfg["preferences"]["epitaxyPrefs"].get("dframe-group-scopes", {})
    entrada = scopes.get(escopo, {})
    grupo = next((g for g in entrada.get("groups", [])
                  if g.get("name") == GRUPO_NOME), None)
    atribuidas = set(entrada.get("assignments", {}).keys())

    sessoes = ler_sessoes(dir_s)
    oss = ler_oss(pasta_os_ativas(pasta_cli))
    itens = []
    for o in oss:
        vinculo = o["sessao"]
        sess = None
        if vinculo:
            sess = next((s for s in sessoes if s["id"] == vinculo), None)
        if not sess:
            sess = next((s for s in sessoes if titulo_bate(s["titulo"], o["empregador"])), None)
        no_grupo = bool(sess) and f"code:{sess['id']}" in atribuidas
        itens.append({
            "empregador": o["empregador"], "pasta": str(o["pasta"]),
            "sessao": sess["id"] if sess else None,
            "titulo_sessao": sess["titulo"] if sess else None,
            "criar": sess is None,
            "agrupar": bool(sess) and not no_grupo,
            "vincular": (sess["id"] if sess else None) != vinculo,
        })
    return {"dir_sessoes": dir_s, "escopo": escopo, "cfg": cfg,
            "grupo_existe": grupo is not None, "grupo": grupo,
            "sessoes": sessoes, "itens": itens}


def status(pasta_cli=None):
    p = plano(pasta_cli)
    criar = [i for i in p["itens"] if i["criar"]]
    agrupar = [i for i in p["itens"] if i["agrupar"]]
    vincular = [i for i in p["itens"] if i["vincular"]]
    log(f"OS ativas: {len(p['itens'])} · grupo '{GRUPO_NOME}': "
        f"{'existe' if p['grupo_existe'] else 'NÃO existe (será criado)'}")
    for i in p["itens"]:
        if i["criar"]:
            acao = "CRIAR sessão"
        elif i["agrupar"] or i["vincular"]:
            acao = "ajustar (grupo/vínculo)"
        else:
            acao = "ok"
        extra = f" → {i['titulo_sessao']}" if i["titulo_sessao"] else ""
        log(f"  - {i['empregador']}: {acao}{extra}")
    resumo = {"total": len(p["itens"]), "criar": len(criar),
              "agrupar": len(agrupar), "vincular": len(vincular),
              "grupo_existe": p["grupo_existe"]}
    print("JSON: " + json.dumps(resumo, ensure_ascii=False))
    return resumo


def app_aberto():
    if IS_WIN:
        try:
            saida = subprocess.run(["tasklist", "/FI", "IMAGENAME eq Claude.exe"],
                                   capture_output=True, text=True).stdout
            return "Claude.exe" in saida
        except OSError:
            return False
    return subprocess.run(["pgrep", "-x", "Claude"], capture_output=True).returncode == 0


def reabrir_app():
    try:
        if IS_WIN:
            os.startfile(str(APP_SUPPORT.parent.parent / "Local" / "AnthropicClaude" / "Claude.exe"))  # noqa: P103
        else:
            subprocess.run(["open", "-a", "Claude"], check=False)
        log("App reaberto.")
    except OSError as e:
        log(f"AVISO: não consegui reabrir o app sozinho ({e}) — abra manualmente.")


def modelo_sessao(sessoes):
    """Sessão real mais recente como molde (campos de worktree removidos)."""
    cand = sorted((s["arquivo"] for s in sessoes),
                  key=lambda f: f.stat().st_mtime, reverse=True)
    for f in cand:
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if d.get("sessionId"):
            for k in ("worktreePath", "worktreeName", "branch", "sourceBranch",
                      "writtenBranches", "promptSuggestion", "chromeTabGroupId",
                      "spawnSeed", "scheduledTaskId"):
                d.pop(k, None)
            return d
    raise SystemExit("ERRO: nenhuma sessão existente para usar de molde.")


def grava_vinculo(pasta_os: Path, sessao_id: str):
    mem = pasta_os / "memory.md"
    texto = mem.read_text(encoding="utf-8", errors="replace")
    novo = f'sessao_claude: "{sessao_id}"'
    if re.search(r"^sessao_claude:.*$", texto, re.MULTILINE):
        texto = re.sub(r"^sessao_claude:.*$", novo, texto, count=1, flags=re.MULTILINE)
    else:
        # insere antes do fechamento do front-matter
        m = re.match(r"^---\n.*?\n---", texto, re.DOTALL)
        if not m:
            log(f"AVISO: {mem} sem front-matter — vínculo não gravado.")
            return
        fim = m.end() - 3
        texto = texto[:fim] + novo + "\n" + texto[fim:]
    mem.write_text(texto, encoding="utf-8")


def aplicar(pasta_cli=None, agora=False, reabrir=True):
    p = plano(pasta_cli)
    pend = [i for i in p["itens"] if i["criar"] or i["agrupar"] or i["vincular"]]
    if not pend and p["grupo_existe"]:
        log("Nada a fazer — tudo sincronizado.")
        return 0

    if app_aberto():
        if agora:
            raise SystemExit("ERRO: o app do Claude está ABERTO — com --agora eu não espero. "
                             "Feche o app ou rode sem --agora (modo vigia).")
        log("Aguardando o app do Claude fechar (Cmd+Q)... aplicarei em seguida e reabrirei o app.")
        while app_aberto():
            time.sleep(2)
        log("App fechado. Aguardando 3s para o app terminar de gravar as preferências...")
        time.sleep(3)
        p = plano(pasta_cli)  # relê: o app pode ter regravado o config ao fechar

    # backup do config
    BACKUPS.mkdir(parents=True, exist_ok=True)
    carimbo = time.strftime("%Y%m%d-%H%M%S")
    bkp = BACKUPS / f"claude_desktop_config.{carimbo}.json"
    shutil.copy2(CONFIG, bkp)
    log(f"Backup do config: {bkp}")

    cfg = p["cfg"] = carregar_config()
    prefs = cfg["preferences"]["epitaxyPrefs"]
    scopes = prefs.setdefault("dframe-group-scopes", {})
    entrada = scopes.setdefault(p["escopo"], {"groups": [], "assignments": {}, "order": {}})
    entrada.setdefault("groups", [])
    entrada.setdefault("assignments", {})
    entrada.setdefault("order", {})

    grupo = next((g for g in entrada["groups"] if g.get("name") == GRUPO_NOME), None)
    if not grupo:
        grupo = {"id": f"cg-{uuid.uuid4()}", "name": GRUPO_NOME}
        entrada["groups"].append(grupo)
        log(f"Grupo '{GRUPO_NOME}' criado ({grupo['id']}).")
    gid = grupo["id"]
    ordem = entrada["order"].setdefault(gid, [])

    molde = modelo_sessao(p["sessoes"])
    criadas = []
    for item in p["itens"]:
        sid = item["sessao"]
        if item["criar"]:
            sid = f"local_{uuid.uuid4()}"
            d = dict(molde)
            d.update({
                "sessionId": sid,
                "cliSessionId": str(uuid.uuid4()),
                "cwd": item["pasta"],
                "originCwd": item["pasta"],
                "createdAt": AGORA_MS(),
                "lastActivityAt": AGORA_MS(),
                "lastFocusedAt": AGORA_MS(),
                "isArchived": False,
                "title": item["empregador"],
                "titleSource": "user",
                "completedTurns": 0,
            })
            destino = p["dir_sessoes"] / f"{sid}.json"
            destino.write_text(json.dumps(d, ensure_ascii=False, indent=2),
                               encoding="utf-8")
            criadas.append(sid)
            log(f"Sessão criada: {item['empregador']} ({sid})")
        chave = f"code:{sid}"
        if entrada["assignments"].get(chave) != gid:
            entrada["assignments"][chave] = gid
            log(f"Sessão '{item['empregador']}' atribuída ao grupo.")
        if chave not in ordem:
            ordem.append(chave)
        grava_vinculo(Path(item["pasta"]), sid)

    tmp = CONFIG.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(CONFIG)
    log("Config do app atualizado.")

    manif = {"quando": time.strftime("%Y-%m-%d %H:%M:%S"), "grupo": gid,
             "backup": str(bkp), "sessoes_criadas": criadas}
    MANIFESTO.write_text(json.dumps(manif, ensure_ascii=False, indent=2), encoding="utf-8")

    if reabrir:
        reabrir_app()
    log(f"PRONTO: {len(criadas)} sessão(ões) criada(s); grupo '{GRUPO_NOME}' sincronizado.")
    return 0


def desfazer():
    if not MANIFESTO.is_file():
        raise SystemExit("ERRO: sem manifesto — nada para desfazer.")
    manif = json.loads(MANIFESTO.read_text(encoding="utf-8"))
    if app_aberto():
        log("Aguardando o app fechar para desfazer com segurança...")
        while app_aberto():
            time.sleep(2)
        time.sleep(3)
    bkp = Path(manif["backup"])
    if bkp.is_file():
        shutil.copy2(bkp, CONFIG)
        log(f"Config restaurado de {bkp}")
    dir_s = dir_sessoes()
    for sid in manif.get("sessoes_criadas", []):
        f = dir_s / f"{sid}.json"
        if f.is_file():
            f.unlink()
            log(f"Sessão removida: {sid}")
    reabrir_app()
    log("Desfeito.")
    return 0


def main():
    args = sys.argv[1:]
    pasta = None
    if "--pasta" in args:
        pasta = args[args.index("--pasta") + 1]
    try:
        if "--status" in args:
            status(pasta)
            return 0
        if "--aplicar" in args:
            return aplicar(pasta, agora="--agora" in args,
                           reabrir="--sem-reabrir" not in args)
        if "--desfazer" in args:
            return desfazer()
    except SystemExit as e:
        log(str(e))
        raise
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main())
