#!/usr/bin/env python3
"""
aft_doctor.py - Verificacao pos-instalacao do AFT Toolkit.

Confere, em linguagem de quem nao e programador, se tudo que o toolkit precisa
esta no lugar: Python, Git, as skills descobertas pelo Claude Code, os arquivos
de configuracao do repo, o perfil do auditor, a pasta de trabalho, as bibliotecas
Python e o NotebookLM (opcional).

Nao altera nada - so le e relata. Imprime um relatorio legivel e, no fim, uma
linha JSON (prefixada com JSON:) para a skill consumir.

Severidades:
  ok    - esta certo
  aviso - falta algo opcional ou que se resolve com /aft-setup
  erro  - falta algo essencial (o toolkit nao funciona direito sem)

Uso: python ~/.claude/skills/_scripts/aft_doctor.py
"""
import json
import shutil
import subprocess
import sys
from importlib.util import find_spec
from pathlib import Path

# A raiz das skills e o avo deste arquivo: .../skills/_scripts/aft_doctor.py
SKILLS_DIR = Path(__file__).resolve().parent.parent
HOME = Path.home()
AFT_DIR = HOME / "Documents" / "AFT"

checks = []


def add(titulo, status, detalhe, dica=""):
    checks.append({"titulo": titulo, "status": status, "detalhe": detalhe, "dica": dica})


def cmd_version(exe, args=("--version",)):
    """Retorna a 1a linha da saida de `exe args`, ou None se nao rodar."""
    path = shutil.which(exe)
    if not path:
        return None
    try:
        out = subprocess.run(
            [path, *args], capture_output=True, text=True, timeout=20
        )
        txt = (out.stdout or out.stderr or "").strip().splitlines()
        return txt[0] if txt else path
    except Exception:
        return path


# 1. Python -------------------------------------------------------------------
ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
if sys.version_info >= (3, 8):
    add("Python", "ok", f"Python {ver}")
else:
    add("Python", "erro", f"Python {ver} (muito antigo)",
        "Instale o Python 3.12 (o /aft-setup faz isso por voce).")

# 2. Git ----------------------------------------------------------------------
git = cmd_version("git")
if git:
    add("Git", "ok", git)
else:
    add("Git", "erro", "Git nao encontrado",
        "No Windows o app desktop exige o Git para abrir sessoes locais. "
        "Instale em git-scm.com e reinicie o Claude Code pela bandeja.")

# 3. Skills descobertas (1o nivel) -------------------------------------------
# O Claude Code so enxerga skills em ~/.claude/skills/<skill>/SKILL.md.
marcos = ["aft-setup", "nova-os", "painel", "gera-ai", "inspecao-inicial"]
faltando_skill = [s for s in marcos if not (SKILLS_DIR / s / "SKILL.md").is_file()]
total_skills = len(list(SKILLS_DIR.glob("*/SKILL.md")))
em_claude = SKILLS_DIR.name == "skills" and SKILLS_DIR.parent.name == ".claude"
if not faltando_skill and em_claude:
    add("Skills instaladas", "ok",
        f"{total_skills} skills em {SKILLS_DIR}")
elif not faltando_skill and not em_claude:
    add("Skills instaladas", "aviso",
        f"{total_skills} skills encontradas, mas fora de ~/.claude/skills "
        f"(estao em {SKILLS_DIR})",
        "O Claude Code so descobre skills no 1o nivel de ~/.claude/skills. "
        "O repositorio precisa SER essa pasta (git clone <url> ~/.claude/skills).")
else:
    add("Skills instaladas", "erro",
        f"Faltam skills no 1o nivel: {', '.join(faltando_skill)}",
        "Provavel clone aninhado (ex.: ~/.claude/skills/aft-toolkit/...). "
        "O repositorio precisa SER a pasta ~/.claude/skills.")

# 4. Arquivos de configuracao do repo ----------------------------------------
cfg = SKILLS_DIR / "config"
need_cfg = ["notebooks.json", "uorgs.csv", "CLAUDE-aft.md"]
faltando_cfg = [f for f in need_cfg if not (cfg / f).is_file()]
if not faltando_cfg:
    add("Config do toolkit", "ok",
        "notebooks.json, uorgs.csv e CLAUDE-aft.md presentes")
else:
    add("Config do toolkit", "erro",
        f"Faltam em config/: {', '.join(faltando_cfg)}",
        "Instalacao incompleta. Rode 'Atualize o AFT Toolkit' (git pull) "
        "ou reclone o repositorio.")

# 5. Perfil do auditor (~/.claude/CLAUDE.md) ---------------------------------
claude_md = SKILLS_DIR.parent / "CLAUDE.md"
if claude_md.is_file():
    add("Perfil do auditor", "ok", f"{claude_md} instalado")
else:
    add("Perfil do auditor", "aviso", "~/.claude/CLAUDE.md nao existe",
        "Rode /aft-setup para instalar o perfil (faz o Claude saber que voce e AFT).")

# 6. Pasta de trabalho -------------------------------------------------------
if AFT_DIR.is_dir():
    sub = [d for d in ("OS ATIVAS", "OS ARQUIVADAS") if not (AFT_DIR / d).is_dir()]
    if not sub:
        add("Pasta de trabalho", "ok", f"{AFT_DIR} (OS ATIVAS, OS ARQUIVADAS)")
    else:
        add("Pasta de trabalho", "aviso",
            f"{AFT_DIR} existe, mas falta: {', '.join(sub)}",
            "Rode /aft-setup para criar a estrutura de pastas.")
else:
    add("Pasta de trabalho", "aviso", f"{AFT_DIR} nao existe",
        "Rode /aft-setup para criar a pasta de trabalho.")

# 7. aft-config.md -----------------------------------------------------------
if (AFT_DIR / "aft-config.md").is_file():
    add("Configuracao do auditor", "ok", f"{AFT_DIR / 'aft-config.md'}")
else:
    add("Configuracao do auditor", "aviso",
        "aft-config.md nao existe (seus dados de CIF/UORG)",
        "Rode /aft-setup para informar nome, CIF e lotacao uma unica vez.")

# 8. Bibliotecas Python ------------------------------------------------------
libs = {"pillow": "PIL", "pikepdf": "pikepdf", "pypdf": "pypdf"}
faltando_lib = [nome for nome, mod in libs.items() if find_spec(mod) is None]
if not faltando_lib:
    add("Bibliotecas Python", "ok", "pillow, pikepdf e pypdf instaladas")
else:
    add("Bibliotecas Python", "aviso",
        f"Faltam: {', '.join(faltando_lib)}",
        "Rode /aft-setup (Passo 6) ou: pip install " + " ".join(faltando_lib) +
        " (fotos->PDF, compressao e leitura de autos lavrados dependem delas).")

# 9. NotebookLM (opcional) ---------------------------------------------------
nlm = cmd_version("notebooklm", ("--help",))
if nlm:
    add("NotebookLM (CLI)", "ok", "comando 'notebooklm' disponivel")
else:
    add("NotebookLM (CLI)", "aviso", "comando 'notebooklm' nao encontrado",
        "Opcional: acelera a busca de ementas. Instale com "
        "pipx install \"notebooklm-py[browser]\" e rode /aft-setup (Passo 7). "
        "Sem ele, as skills usam o Drive ou pedem o codigo da ementa.")

# ----------------------------------------------------------------------------
resumo = {
    "ok": sum(1 for c in checks if c["status"] == "ok"),
    "avisos": sum(1 for c in checks if c["status"] == "aviso"),
    "erros": sum(1 for c in checks if c["status"] == "erro"),
}

icone = {"ok": "[OK]   ", "aviso": "[AVISO]", "erro": "[ERRO] "}
print("=" * 60)
print("  AFT TOOLKIT - Verificacao pos-instalacao (/aft-doctor)")
print("=" * 60)
for c in checks:
    print(f"{icone[c['status']]} {c['titulo']}: {c['detalhe']}")
    if c["dica"] and c["status"] != "ok":
        print(f"         -> {c['dica']}")
print("-" * 60)
print(f"  {resumo['ok']} ok | {resumo['avisos']} avisos | {resumo['erros']} erros")
print("=" * 60)
print("JSON:" + json.dumps({"resumo": resumo, "checks": checks}, ensure_ascii=False))

sys.exit(1 if resumo["erros"] else 0)
