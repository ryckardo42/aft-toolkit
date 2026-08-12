# -*- coding: utf-8 -*-
"""
instalar_hook_diario.py — instala/remove/consulta o GANCHO do diário de
atividades no `~/.claude/settings.json` do AFT.

O gancho (hook PostToolUse do Claude Code) roda `diario_registrar.py --hook`
depois de TODA edição de arquivo feita pelo Claude. O script do diário decide
sozinho se interessa: só age quando o arquivo editado é um `memory.md` dentro
de `OS ATIVAS/`, anotando o dia trabalhado no sidecar `.diario-auto.jsonl` da
OS (1 linha por dia). É a rede de segurança do diário: mesmo que o Claude
esqueça de registrar a atividade classificada, o DIA trabalhado naquela
empresa nunca se perde.

Mexe SOMENTE na chave hooks.PostToolUse e SOMENTE nas entradas cujo comando
contém "diario_registrar.py" — qualquer outro hook do AFT é preservado.
Reinstalar substitui a entrada antiga (atualiza python_path e caminho).

Uso:
    python instalar_hook_diario.py instalar <python_path>
    python instalar_hook_diario.py remover
    python instalar_hook_diario.py status

Imprime um JSON no stdout: {"ok": bool, "detalhe": "...", "acao": "..."}.
Nunca lança exceção não tratada.
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
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

MARCA = "diario_registrar.py"
MATCHER = "Edit|Write|MultiEdit"


def settings_path() -> Path:
    return Path.home() / ".claude" / "settings.json"


def script_diario() -> Path:
    return Path(__file__).resolve().parent / "diario_registrar.py"


def resultado(ok: bool, detalhe: str, acao: str) -> int:
    print(json.dumps({"ok": ok, "detalhe": detalhe, "acao": acao},
                     ensure_ascii=False, indent=2))
    return 0 if ok else 1


def carregar() -> dict:
    p = settings_path()
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        raise ValueError(f"não consegui ler {p}: {e}")


def gravar(cfg: dict) -> None:
    p = settings_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + "\n",
                 encoding="utf-8")


def entradas_sem_diario(post: list) -> list:
    """As entradas de PostToolUse que NÃO são do diário (preservadas)."""
    fora = []
    for entrada in post:
        cmds = entrada.get("hooks") or []
        if any(MARCA in (c.get("command") or "") for c in cmds):
            continue
        fora.append(entrada)
    return fora


def tem_diario(cfg: dict) -> bool:
    post = (cfg.get("hooks") or {}).get("PostToolUse") or []
    return len(post) != len(entradas_sem_diario(post))


def instalar(python_path: str) -> int:
    alvo = script_diario()
    if not alvo.exists():
        return resultado(False, f"script do diário não encontrado: {alvo}",
                         "instalar")
    try:
        cfg = carregar()
    except ValueError as e:
        return resultado(False, str(e), "instalar")
    comando = f'"{python_path}" "{alvo}" --hook'
    nova = {"matcher": MATCHER,
            "hooks": [{"type": "command", "command": comando}]}
    hooks = cfg.setdefault("hooks", {})
    post = hooks.get("PostToolUse") or []
    ja_tinha = len(post) != len(entradas_sem_diario(post))
    hooks["PostToolUse"] = entradas_sem_diario(post) + [nova]
    gravar(cfg)
    return resultado(True,
                     ("gancho do diário atualizado" if ja_tinha else
                      "gancho do diário instalado")
                     + f" em {settings_path()} (vale a partir da PRÓXIMA sessão"
                       " do Claude Code)",
                     "instalar")


def remover() -> int:
    try:
        cfg = carregar()
    except ValueError as e:
        return resultado(False, str(e), "remover")
    hooks = cfg.get("hooks") or {}
    post = hooks.get("PostToolUse") or []
    fora = entradas_sem_diario(post)
    if len(fora) == len(post):
        return resultado(True, "gancho do diário não estava instalado", "remover")
    if fora:
        hooks["PostToolUse"] = fora
    else:
        hooks.pop("PostToolUse", None)
        if not hooks:
            cfg.pop("hooks", None)
    gravar(cfg)
    return resultado(True, "gancho do diário removido", "remover")


def status() -> int:
    try:
        cfg = carregar()
    except ValueError as e:
        return resultado(False, str(e), "status")
    if tem_diario(cfg):
        return resultado(True, "gancho do diário instalado", "status")
    return resultado(True, "gancho do diário NÃO instalado", "status")


def main() -> int:
    argv = sys.argv[1:]
    if not argv or argv[0] not in ("instalar", "remover", "status"):
        return resultado(False,
                         "uso: instalar <python_path> | remover | status",
                         argv[0] if argv else "")
    if argv[0] == "instalar":
        python_path = argv[1] if len(argv) > 1 and argv[1].strip() else sys.executable
        return instalar(python_path)
    if argv[0] == "remover":
        return remover()
    return status()


if __name__ == "__main__":
    sys.exit(main())
