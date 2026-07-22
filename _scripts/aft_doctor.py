#!/usr/bin/env python3
"""
aft_doctor.py - Verificacao pos-instalacao do AFT Toolkit.

Confere, em linguagem de quem nao e programador, se tudo que o toolkit precisa
esta no lugar: Python, Git, as skills descobertas pelo Claude Code, os arquivos
de configuracao do repo, o perfil do auditor, a pasta de trabalho, as bibliotecas
Python e o NotebookLM (opcional).

So le e relata, com UMA excecao: a pasta de trabalho (AFT/OS ATIVAS e
OS ARQUIVADAS) e criada se faltar - criar diretorio vazio e seguro, idempotente,
e sem ela nada do toolkit funciona. Nenhum arquivo e alterado ou apagado.
Imprime um relatorio legivel e, no fim, uma linha JSON (prefixada com JSON:)
para a skill consumir.

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
# Resolvido de verdade na checagem 6 (pasta_aft.py). Este e so o fallback se
# o import falhar - no Windows com OneDrive ele costuma estar errado.
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
marcos = ["aft-setup", "nova-os", "painel", "gera-ai", "auditoria-geral"]
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

# 5b. Deny-list de seguranca (~/.claude/settings.json) -----------------------
# Rede de protecao: impede ler credenciais (~/.ssh, ~/.aws, .env), os mapas
# .depara_*.json (dados reais de trabalhador) e usar ssh/scp/nc. O /aft-setup
# instala a partir de config/settings-aft.json. Marca de referencia: a regra do
# de-para, que e o controle especifico do toolkit.
settings_json = SKILLS_DIR.parent / "settings.json"
MARCO_DENY = "Read(**/.depara_*.json)"
deny_list = []
if settings_json.is_file():
    try:
        _data = json.loads(settings_json.read_text(encoding="utf-8"))
        deny_list = (_data.get("permissions") or {}).get("deny") or []
    except (OSError, json.JSONDecodeError):
        deny_list = []
if MARCO_DENY in deny_list:
    add("Deny-list de seguranca", "ok",
        f"{settings_json} ({len(deny_list)} regras de bloqueio)")
elif settings_json.is_file():
    add("Deny-list de seguranca", "aviso",
        "settings.json existe, mas sem a deny-list do toolkit",
        "Rode /aft-setup para acrescentar os bloqueios de credenciais e do de-para.")
else:
    add("Deny-list de seguranca", "aviso", "~/.claude/settings.json nao existe",
        "Rode /aft-setup para instalar a rede de protecao (impede o Claude de ler "
        "senhas e os dados reais dos trabalhadores).")

# 6. Pasta de trabalho -------------------------------------------------------
# Unica checagem que CONSERTA em vez de so relatar: criar diretorio vazio e
# seguro e idempotente, e sem a pasta nada do toolkit funciona. O caminho vem
# do pasta_aft.py, que resolve a "Documentos" de verdade (no Windows ela quase
# nunca e ~/Documents: o OneDrive redireciona e o idioma muda o nome).
try:
    sys.path.insert(0, str(SKILLS_DIR / "_scripts"))
    from pasta_aft import diagnostico, garantir_estrutura

    diag = diagnostico()
    AFT_DIR = Path(diag["pasta_aft"])
    _, criadas = garantir_estrutura()

    onde = f"{AFT_DIR}"
    if diag["onedrive"]:
        onde += " (dentro do OneDrive - e a sua pasta Documentos de verdade)"
    elif diag["redirecionada"]:
        onde += " (sua pasta Documentos fica fora do caminho padrao)"

    if criadas:
        add("Pasta de trabalho", "ok",
            f"criada agora: {onde}",
            "Suas fiscalizacoes vao para a subpasta 'OS ATIVAS'. "
            "Se ainda nao rodou o /aft-setup, rode - ele grava o aft-config.md "
            "com os seus dados (CIF/UORG).")
    else:
        n_empresas = len(list((AFT_DIR / "OS ATIVAS").glob("*/memory.md")))
        add("Pasta de trabalho", "ok",
            f"{onde} - {n_empresas} empresa(s) em OS ATIVAS")

    # Instalacao anterior pode ter criado uma pasta ORFA no caminho errado
    # (o mkdir ~/Documents/AFT cru, antes desta correcao).
    if diag["duplicadas"]:
        add("Pasta de trabalho duplicada", "aviso",
            "existe outra pasta AFT fora da usada: "
            + ", ".join(diag["duplicadas"]),
            "Provavelmente sobrou de uma instalacao anterior. Se ela tiver "
            "fiscalizacoes dentro, mova as subpastas para "
            f"'{AFT_DIR / 'OS ATIVAS'}' e apague a antiga; se estiver vazia, "
            "pode apagar direto.")
except Exception as e:
    add("Pasta de trabalho", "erro",
        f"nao consegui resolver/criar a pasta de trabalho ({type(e).__name__}: {e})",
        "Rode /aft-setup - ele cria a estrutura e mostra o caminho exato.")

# 7. aft-config.md -----------------------------------------------------------
if (AFT_DIR / "aft-config.md").is_file():
    add("Configuracao do auditor", "ok", f"{AFT_DIR / 'aft-config.md'}")
else:
    add("Configuracao do auditor", "aviso",
        "aft-config.md nao existe (seus dados de CIF/UORG)",
        "Rode /aft-setup para informar nome, CIF e lotacao uma unica vez.")

# 8. Bibliotecas Python ------------------------------------------------------
libs = {
    "pillow": "PIL",            # fotos -> PDF
    "pikepdf": "pikepdf",       # assinaturas/compressao de PDF
    "pypdf": "pypdf",           # leitura de autos lavrados
    "python-docx": "docx",      # gera/edita o RT (.docx) da interdicao
    "pdfplumber": "pdfplumber", # extrai texto de PDFs de fiscalizacao
    "pillow-heif": "pillow_heif",  # fotos HEIC/HEIF do iPhone (opcional)
}
faltando_lib = [nome for nome, mod in libs.items() if find_spec(mod) is None]
if not faltando_lib:
    add("Bibliotecas Python", "ok",
        "pillow, pikepdf, pypdf, python-docx, pdfplumber e pillow-heif instaladas")
else:
    add("Bibliotecas Python", "aviso",
        f"Faltam: {', '.join(faltando_lib)}",
        "Rode /aft-setup (Passo 6) ou: pip install " + " ".join(faltando_lib) +
        " (fotos->PDF, .docx do RT, leitura de PDF e de autos lavrados dependem delas).")

# 8b. python_path no aft-config.md (resolver o Python certo) ------------------
# No Windows, 'python3' pode ser o atalho vazio da Microsoft Store. O /aft-setup
# grava o caminho completo do interpretador em python_path para as skills usarem.
cfg_path = AFT_DIR / "aft-config.md"
py_path_val = None
if cfg_path.is_file():
    import re as _re
    try:
        for _line in cfg_path.read_text(encoding="utf-8").splitlines():
            _m = _re.search(r'python_path:\s*"?([^"#]+?)"?\s*(?:#.*)?$', _line)
            if _m and _m.group(1).strip():
                py_path_val = _m.group(1).strip()
                break
    except OSError:
        pass
if py_path_val and Path(py_path_val).is_file():
    add("Caminho do Python (python_path)", "ok", py_path_val)
elif py_path_val:
    add("Caminho do Python (python_path)", "aviso",
        f"python_path aponta para um arquivo inexistente: {py_path_val}",
        "Rode /aft-setup para regravar o caminho do Python.")
elif cfg_path.is_file():
    add("Caminho do Python (python_path)", "aviso",
        "aft-config.md nao tem python_path",
        "Rode /aft-setup para gravar o caminho completo do Python (evita o atalho "
        "vazio 'python3' da Microsoft Store).")

# 9. NotebookLM (opcional) ---------------------------------------------------
# Checa o CLI e, se presente, o estado da sessao (validacao LOCAL, sem rede).
# A dica nunca manda o AFT ao terminal: aponta para a skill /notebooklm-login.
nlm_path = shutil.which("notebooklm")
if not nlm_path:
    add("NotebookLM (CLI)", "aviso", "comando 'notebooklm' nao encontrado",
        "Opcional: acelera a busca de ementas. Peca ao Claude 'conecte o notebooklm' "
        "(skill /notebooklm-login) - ele instala e faz o login por voce, sem terminal. "
        "Sem ele, as skills usam o Drive ou pedem o codigo da ementa.")
else:
    estado = None
    try:
        out = subprocess.run(
            [nlm_path, "auth", "check", "--json"],
            capture_output=True, text=True, timeout=25,
        )
        raw = (out.stdout or "").strip()
        try:
            estado = json.loads(raw)
        except Exception:
            i, j = raw.find("{"), raw.rfind("}")
            estado = json.loads(raw[i:j + 1]) if i != -1 and j != -1 else None
    except Exception:
        estado = None

    chk = estado.get("checks", {}) if isinstance(estado, dict) else {}
    if estado is None:
        # CLI responde, mas nao foi possivel ler a sessao - reporta so presenca.
        add("NotebookLM (CLI)", "ok", "comando 'notebooklm' disponivel")
    elif estado.get("status") == "ok" or chk.get("sid_cookie"):
        add("NotebookLM (CLI)", "ok",
            "comando disponivel e sessao salva (login local OK)")
    elif not chk.get("storage_exists"):
        add("NotebookLM (CLI)", "aviso", "instalado, mas ainda nao conectado (sem login)",
            "Peca ao Claude 'conecte o notebooklm' (skill /notebooklm-login) - ele abre "
            "o login na sua conta Google e salva sozinho, sem terminal.")
    else:
        add("NotebookLM (CLI)", "aviso",
            "instalado, mas a sessao parece incompleta ou expirada",
            "Peca ao Claude 'reconecte o notebooklm' (skill /notebooklm-login).")

# 9b. Reconexao automatica do NotebookLM (NOTEBOOKLM_REFRESH_CMD) --------------
# Faz o 'notebooklm ask' se reautenticar sozinho ao expirar. Pode estar so no
# ambiente persistente (registro do Windows) e nao no processo atual.
import os as _os
_refresh = _os.environ.get("NOTEBOOKLM_REFRESH_CMD")
if not _refresh and _os.name == "nt":
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as _k:
            _refresh, _ = winreg.QueryValueEx(_k, "NOTEBOOKLM_REFRESH_CMD")
    except (FileNotFoundError, OSError):
        _refresh = None
if _refresh:
    add("Reconexao automatica do NotebookLM", "ok",
        f"NOTEBOOKLM_REFRESH_CMD = {_refresh}")
else:
    add("Reconexao automatica do NotebookLM", "aviso",
        "NOTEBOOKLM_REFRESH_CMD nao configurada",
        "Sem ela, o 'notebooklm ask' nao se reautentica sozinho ao expirar. "
        "Rode /aft-setup (passo 7) ou /notebooklm-login para configurar.")

# 10. Skills - frontmatter e modelos ------------------------------------------
# Tres camadas, todas somente leitura:
#   (a) cada SKILL.md precisa de frontmatter com 'name' igual ao nome da pasta,
#       senao o Claude Code nao aciona a skill direito;
#   (b) o campo 'model', quando presente, deve ser um apelido conhecido ou um ID
#       listado em config/models-validos.json (o mantenedor atualiza a lista e o
#       AFT recebe via /aft-atualizar);
#   (c) IDs datados (ex.: claude-opus-4-8[1m]) sao testados AO VIVO com uma
#       chamada minima 'claude -p' por ID distinto - um modelo indisponivel no
#       plano do AFT quebraria a skill sem mensagem compreensivel. O teste so
#       roda se a CLI 'claude' existir; gasta uma resposta curta de cota.
import re as _re2

ALIAS_MODELOS = {"sonnet", "opus", "haiku"}


def _frontmatter(texto):
    """Le os campos simples (campo: valor) do frontmatter; None se nao houver."""
    linhas = texto.splitlines()
    if not linhas or linhas[0].strip() != "---":
        return None
    campos = {}
    for ln in linhas[1:]:
        if ln.strip() == "---":
            return campos
        m = _re2.match(r"^([A-Za-z][\w-]*):\s*(.*)$", ln)
        if m:
            campos[m.group(1)] = m.group(2).strip()
    return None  # frontmatter nunca fechou


ids_validos = set()
mv = cfg / "models-validos.json"
if mv.is_file():
    try:
        _mv = json.loads(mv.read_text(encoding="utf-8"))
        ids_validos = set(_mv.get("ids") or [])
        ALIAS_MODELOS |= set(_mv.get("aliases") or [])
    except (OSError, json.JSONDecodeError):
        pass

# Skills proprias do colega (prefixo "minha-") sao validadas a parte, com
# tolerancia: sao experimentos do AFT, nao devem derrubar o diagnostico do
# toolkit inteiro nem seguem a politica de model-pinning das oficiais.
quebradas, modelos_suspeitos, ids_datados = [], [], set()
proprias_ok, proprias_quebradas = [], []
for sk in sorted(SKILLS_DIR.glob("*/SKILL.md")):
    pasta = sk.parent.name
    eh_propria = pasta.startswith("minha-")
    try:
        campos = _frontmatter(sk.read_text(encoding="utf-8"))
    except OSError:
        campos = None
    if campos is None or campos.get("name") != pasta:
        (proprias_quebradas if eh_propria else quebradas).append(pasta)
        continue
    if eh_propria:
        proprias_ok.append(pasta)
        continue  # nao aplica a politica de 'model' as skills proprias
    modelo = campos.get("model")
    if not modelo or modelo in ALIAS_MODELOS:
        continue
    if _re2.fullmatch(r"claude-[\w.-]+(\[1m\])?", modelo):
        ids_datados.add(modelo)
        if ids_validos and modelo not in ids_validos:
            modelos_suspeitos.append(f"{pasta} ({modelo})")
    else:
        modelos_suspeitos.append(f"{pasta} ({modelo})")

n_proprias = len(proprias_ok) + len(proprias_quebradas)
n_oficiais = total_skills - n_proprias

if quebradas:
    add("Skills - frontmatter", "erro",
        "SKILL.md com frontmatter invalido ou 'name' diferente da pasta: "
        + ", ".join(quebradas),
        "Essas skills podem nao ser acionadas. Rode 'Atualize o AFT Toolkit' "
        "(/aft-atualizar); se persistir, avise o mantenedor.")
else:
    add("Skills - frontmatter", "ok",
        f"{n_oficiais} SKILL.md oficiais com frontmatter valido e name correto")

if modelos_suspeitos:
    add("Skills - modelos declarados", "aviso",
        "model desconhecido em: " + ", ".join(modelos_suspeitos),
        "Pode ser um modelo descontinuado ou erro de digitacao. Rode 'Atualize "
        "o AFT Toolkit' (/aft-atualizar); se persistir, avise o mantenedor.")
else:
    add("Skills - modelos declarados", "ok",
        "todos os campos 'model' usam apelidos ou IDs da lista valida")

if ids_datados:
    claude_cli = shutil.which("claude")
    if not claude_cli:
        add("Skills - teste dos modelos pinados", "ok",
            "teste ao vivo pulado (CLI 'claude' nao encontrada); "
            "valeu a validacao pela lista acima")
    else:
        indisponiveis, inconclusivos = [], []
        for mid in sorted(ids_datados):
            try:
                r = subprocess.run(
                    [claude_cli, "-p", "Responda apenas: OK", "--model", mid],
                    capture_output=True, text=True, timeout=120,
                    stdin=subprocess.DEVNULL,
                )
                if r.returncode != 0:
                    msg = (r.stderr or r.stdout or "").strip()
                    primeira = msg.splitlines()[0][:100] if msg else "falhou"
                    # So e veredito sobre o MODELO se a mensagem falar dele;
                    # falha de autenticacao/rede da CLI e inconclusiva.
                    if "model" in msg.lower():
                        indisponiveis.append(f"{mid} - {primeira}")
                    else:
                        inconclusivos.append(f"{mid} ({primeira})")
            except subprocess.TimeoutExpired:
                inconclusivos.append(f"{mid} (sem resposta a tempo)")
            except OSError:
                inconclusivos.append(f"{mid} (CLI nao rodou)")
        if indisponiveis:
            add("Skills - teste dos modelos pinados", "erro",
                "modelo(s) indisponivel(is) nesta conta: "
                + "; ".join(indisponiveis),
                "As skills que usam esse modelo vao falhar. Rode 'Atualize o "
                "AFT Toolkit' (/aft-atualizar); se persistir, avise o "
                "mantenedor informando esta mensagem (pode ser limitacao do "
                "seu plano ou modelo descontinuado).")
        elif inconclusivos:
            add("Skills - teste dos modelos pinados", "aviso",
                "teste inconclusivo (falha alheia ao modelo): "
                + "; ".join(inconclusivos),
                "A CLI 'claude' nao conseguiu completar a chamada (login ou "
                "internet), entao nao da para afirmar nada sobre o modelo. "
                "Rode /aft-doctor de novo mais tarde; as skills podem "
                "funcionar normalmente.")
        else:
            add("Skills - teste dos modelos pinados", "ok",
                f"{len(ids_datados)} modelo(s) pinado(s) respondendo: "
                + ", ".join(sorted(ids_datados)))

# 11. Skills proprias do colega (minha-*) -------------------------------------
# So aparece se o AFT tiver criado alguma. Confirma que estao protegidas de
# atualizacoes (padrao 'minha-*/' no .gitignore) e valida com tolerancia.
if n_proprias:
    protegidas = False
    gi = SKILLS_DIR / ".gitignore"
    if gi.is_file():
        try:
            protegidas = "minha-*" in gi.read_text(encoding="utf-8")
        except OSError:
            pass
    nota_protecao = ("protegidas de atualizacoes (.gitignore)" if protegidas else
                     "ATENCAO: o .gitignore nao reserva 'minha-*'; rode /aft-atualizar "
                     "para pegar a protecao antes da proxima atualizacao")
    if proprias_quebradas:
        add("Skills proprias (minha-*)", "aviso",
            f"{n_proprias} skill(s) propria(s); com frontmatter/name a corrigir: "
            + ", ".join(proprias_quebradas) + f" - {nota_protecao}",
            "Sao SUAS skills. Para o Claude Code aciona-las, o 'name' do frontmatter "
            "deve ser igual ao nome da pasta. O /nova-skill cria ja no formato certo.")
    elif not protegidas:
        add("Skills proprias (minha-*)", "aviso",
            f"{n_proprias} skill(s) propria(s) valida(s), mas {nota_protecao}",
            "Rode 'Atualize o AFT Toolkit' (/aft-atualizar) para reservar o namespace.")
    else:
        add("Skills proprias (minha-*)", "ok",
            f"{n_proprias} skill(s) propria(s) valida(s) e {nota_protecao}: "
            + ", ".join(proprias_ok))

# 12. Servidor do painel interativo (parte padrao da instalacao) --------------
# O /aft-setup instala o servidor sempre ligado (127.0.0.1:8347) por padrao e o
# /aft-atualizar garante em quem nao tem. Aqui so conferimos se esta no ar.
import urllib.request as _url

try:
    # A 1a resposta apos o servidor subir pode levar alguns segundos (varre
    # todas as OS ATIVAS antes de responder) - 3s gerava falso "nao responde".
    with _url.urlopen("http://127.0.0.1:8347/", timeout=10) as _r:
        _no_ar = 200 <= _r.status < 500
except Exception:
    _no_ar = False

if _no_ar:
    add("Painel interativo (servidor)", "ok",
        "no ar em http://127.0.0.1:8347 (so na sua maquina)")
else:
    add("Painel interativo (servidor)", "aviso",
        "servidor do painel nao esta respondendo em 127.0.0.1:8347",
        "Ele faz parte da instalacao padrao (sobe sozinho no login). Rode "
        "'Atualize o AFT Toolkit' (/aft-atualizar) para instalar/reparar, ou "
        "peca 'abre o painel interativo' para subir agora. Sem ele, o painel "
        "continua funcionando aberto por duplo-clique (somente leitura).")

# 13. Perfil do auditor (CLAUDE.md) em dia? -----------------------------------
# O perfil instalado carrega um marcador com versao (AFT-TOOLKIT-PERFIL:INICIO vN).
# O /aft-atualizar (Passo 2e) atualiza sozinho quando o template avanca.
_re_marc = _re2.compile(r"AFT-TOOLKIT-PERFIL:INICIO\s+v(\d+)")
_tpl = SKILLS_DIR / "config" / "CLAUDE-aft.md"
_alvo = HOME / ".claude" / "CLAUDE.md"
_v_tpl = None
if _tpl.is_file():
    try:
        _m = _re_marc.search(_tpl.read_text(encoding="utf-8"))
        _v_tpl = int(_m.group(1)) if _m else None
    except OSError:
        pass

if _v_tpl is None:
    add("Perfil do auditor - versao", "aviso",
        "nao foi possivel ler a versao do template do perfil",
        "Rode 'Atualize o AFT Toolkit' (/aft-atualizar); se persistir, avise o "
        "mantenedor.")
elif not _alvo.is_file():
    pass  # a checagem 'Perfil do auditor' (acima) ja acusa a ausencia do arquivo
else:
    try:
        _m = _re_marc.search(_alvo.read_text(encoding="utf-8"))
    except OSError:
        _m = None
    if not _m:
        add("Perfil do auditor - versao", "aviso",
            "perfil de versao antiga (sem marcador de versao)",
            "O /aft-atualizar vai oferecer, uma unica vez, adotar o perfil novo "
            "- que traz protecoes importantes das versoes recentes. Depois "
            "disso ele passa a se atualizar sozinho.")
    elif int(_m.group(1)) < _v_tpl:
        add("Perfil do auditor - versao", "aviso",
            f"perfil desatualizado (v{_m.group(1)} instalada, v{_v_tpl} "
            "disponivel)",
            "Rode 'Atualize o AFT Toolkit' (/aft-atualizar) - a atualizacao do "
            "perfil e automatica e preserva o que voce escreveu por fora.")
    else:
        add("Perfil do auditor - versao", "ok",
            f"perfil em dia (v{_m.group(1)})")

# 14. Vigia de sessoes (sessoes por empresa automaticas) ----------------------
# Servico padrao da instalacao: cria as sessoes do grupo "OS ATIVAS" sozinho
# sempre que o app fecha. Aqui so conferimos se o servico existe.
if sys.platform == "darwin":
    _vigia_ok = (HOME / "Library" / "LaunchAgents" / "br.aft.sessoes-vigia.plist").is_file()
elif sys.platform.startswith("win"):
    try:
        _vigia_ok = subprocess.run(
            ["schtasks", "/Query", "/TN", "AFT Sessoes - Vigia"],
            capture_output=True).returncode == 0
    except OSError:
        _vigia_ok = False
else:
    _vigia_ok = None

if _vigia_ok is True:
    add("Vigia de sessoes", "ok",
        "instalado - as sessoes por empresa (grupo OS ATIVAS) sao criadas "
        "sozinhas quando o app fecha")
elif _vigia_ok is False:
    add("Vigia de sessoes", "aviso",
        "servico do vigia de sessoes nao instalado",
        "Ele faz parte da instalacao padrao. Rode 'Atualize o AFT Toolkit' "
        "(/aft-atualizar) para instalar - ou peca 'instala o vigia de "
        "sessoes'. Sem ele, as sessoes por empresa so sao criadas pedindo "
        "a /sessoes-os.")

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
