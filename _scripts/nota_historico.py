# -*- coding: utf-8 -*-
"""
nota_historico.py - Guarda-livros do toolkit: nenhuma skill muda sem nota.

Regra da casa (AGENTS.md, secao "Documentacao obrigatoria"): toda skill criada
ou modificada precisa, no mesmo dia, de (1) a nota tecnica dela no cofre
~/Documents/aft-toolkit-history e (2) a entrada correspondente na arquitetura
(arquitetura/arquitetura.json + o bloco ARCH embutido no arquitetura.html).

Este script nao escreve a nota - quem escreve e o assistente, que tem o
contexto do que foi decidido e do porque. O que ele faz e nao deixar esquecer:
roda como gancho do Claude Code e, quando o assistente vai encerrar o turno com
skill mexida e documentacao faltando, devolve a pendencia para ele resolver.

Modos de gancho (instalados no ~/.claude/settings.json):

    --hook-registrar    PostToolUse (Edit|Write): anota quais skills foram
                        mexidas nesta sessao. Silencioso e a prova de falha.
    --hook-verificar    Stop: confere as pendencias e, se houver, faz o
                        assistente continuar trabalhando (exit 2).

Modos de terminal (o assistente pode chamar quando quiser):

    --verificar             o que esta pendente agora (texto na tela)
    --nota-de <skill>       qual nota do cofre cobre aquela skill
    --checar-arquitetura    o arquitetura.json e o bloco ARCH do .html batem?

Para nao virar camisa de forca, cada skill e cobrada UMA vez por sessao: o
gancho lembra, o assistente decide (documentar, ou explicar por que aquela
mudanca nao muda a nota). Loop infinito, nunca.
"""

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

import argparse
import json
import re
import sys
import time
import unicodedata
from datetime import datetime
from pathlib import Path

try:  # console do Windows e cp1252; nunca deixar um acento derrubar o script
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# Cofre das notas tecnicas (Obsidian). Fica FORA do repositorio de proposito:
# a nota conta a historia da decisao, o repositorio guarda o codigo.
PASTA_NOTAS = Path.home() / "Documents" / "aft-toolkit-history"

# Estado por sessao do assistente (o que ja foi mexido, o que ja foi cobrado).
PASTA_ESTADO = Path.home() / ".claude" / ".aft-notas"
VALIDADE_ESTADO_DIAS = 7


# ---------------------------------------------------------------------------
# Onde estamos: raiz do repositorio do toolkit (funciona tambem em worktree)
# ---------------------------------------------------------------------------
def raiz_repo(inicio):
    """Sobe a partir de `inicio` ate achar a raiz do AFT Toolkit. A assinatura
    e ter AGENTS.md e a pasta arquitetura/ com o arquitetura.json - vale tanto
    para ~/Documents/aft-toolkit quanto para qualquer worktree dele."""
    try:
        p = Path(inicio).resolve()
    except Exception:
        return None
    for cand in (p, *p.parents):
        if (cand / "AGENTS.md").is_file() and \
                (cand / "arquitetura" / "arquitetura.json").is_file():
            return cand
    return None


def skill_do_caminho(caminho, raiz):
    """Nome da skill (pasta aft-*) quando o arquivo pertence a uma; senao None.
    Conta o SKILL.md e tudo dentro de scripts/ - sao as duas coisas que mudam
    o comportamento que o AFT sente."""
    try:
        rel = Path(caminho).resolve().relative_to(raiz)
    except Exception:
        return None
    partes = rel.parts
    if len(partes) < 2 or not partes[0].startswith("aft-"):
        return None
    if partes[1] == "SKILL.md" or partes[1] == "scripts":
        return partes[0]
    return None


# ---------------------------------------------------------------------------
# Estado da sessao
# ---------------------------------------------------------------------------
def _limpar_estado_velho():
    limite = time.time() - VALIDADE_ESTADO_DIAS * 86400
    try:
        for f in PASTA_ESTADO.glob("*.json"):
            if f.stat().st_mtime < limite:
                f.unlink()
    except OSError:
        pass


def caminho_estado(sessao):
    seguro = re.sub(r"[^A-Za-z0-9_.-]", "_", str(sessao or "sem-sessao"))[:80]
    return PASTA_ESTADO / (seguro + ".json")


def ler_estado(sessao):
    f = caminho_estado(sessao)
    if not f.is_file():
        return {}
    try:
        return json.loads(f.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def gravar_estado(sessao, estado):
    try:
        PASTA_ESTADO.mkdir(parents=True, exist_ok=True)
        caminho_estado(sessao).write_text(
            json.dumps(estado, ensure_ascii=False, indent=1), encoding="utf-8")
    except OSError:
        pass


# ---------------------------------------------------------------------------
# Achar a nota que cobre uma skill
#
# O cofre nao tem nome de arquivo padronizado (a nota da /aft-PGR-analise e
# "pgr-analise-skill.md"; a do /aft-gera-ai, "gera-ai-skill.md"; e ha notas que
# cobrem varias skills de uma vez, como "pipeline-autos-revisa-auto-gera-ai").
# Entao a busca e pelo CONTEUDO: quem cita a skill no titulo e a nota dela.
# ---------------------------------------------------------------------------
def _sem_acento(s):
    s = unicodedata.normalize("NFD", str(s or ""))
    return "".join(c for c in s if not unicodedata.combining(c))


def notas_da_skill(skill, pasta=None):
    """(nota_principal, [outras_que_citam]). A principal e a que traz a skill
    no titulo (linha '# ...'); as outras so mencionam."""
    pasta = Path(pasta or PASTA_NOTAS)
    if not pasta.is_dir():
        return None, []
    alvo = _sem_acento(skill).lower()
    principal, citam = None, []
    for f in sorted(pasta.glob("*.md")):
        if f.name == "PROMPT-nova-nota.md":
            continue
        try:
            texto = f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        corpo = _sem_acento(texto).lower()
        if alvo not in corpo:
            continue
        titulo = next((l for l in texto.splitlines() if l.startswith("# ")), "")
        if alvo in _sem_acento(titulo).lower() and principal is None:
            principal = f
        else:
            citam.append(f)
    return principal, citam


# ---------------------------------------------------------------------------
# Arquitetura: o .json e a copia embutida no .html precisam andar juntas
# ---------------------------------------------------------------------------
def arch_do_html(raiz):
    """O objeto ARCH embutido no arquitetura.html, ja parseado (None se nao der)."""
    html = raiz / "arquitetura" / "arquitetura.html"
    if not html.is_file():
        return None
    try:
        texto = html.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    m = re.search(r"^const ARCH = (\{.*?^\});", texto, re.S | re.M)
    if not m:
        return None
    try:
        return json.loads(m.group(1))
    except ValueError:
        return None


def checar_arquitetura(raiz):
    """(ok, mensagem) - o .json e o bloco do .html descrevem a mesma coisa?"""
    caminho = raiz / "arquitetura" / "arquitetura.json"
    try:
        doc = json.loads(caminho.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        return False, f"arquitetura.json ilegível: {e}"
    embutido = arch_do_html(raiz)
    if embutido is None:
        return False, ("não consegui ler o bloco `const ARCH = {...}` do "
                       "arquitetura.html para comparar com o .json")
    if embutido != doc:
        return False, ("o arquitetura.html está DESATUALIZADO: o bloco "
                       "`const ARCH` embutido nele não é igual ao "
                       "arquitetura.json (a página não vai mostrar a mudança). "
                       "Conserte com: python _scripts/nota_historico.py "
                       "--sincronizar-arquitetura")
    return True, "arquitetura.json e o bloco ARCH do .html estão iguais"


def sincronizar_arquitetura(raiz):
    """Reescreve o bloco `const ARCH = {...}` do .html com o texto do .json.

    O .html precisa da copia embutida porque a pagina abre como arquivo local
    (file://) e o navegador proibe buscar o .json ao lado. Entao a fonte de
    verdade e o .json, e o .html e derivado: edite so o .json e rode isto.
    """
    caminho_json = raiz / "arquitetura" / "arquitetura.json"
    caminho_html = raiz / "arquitetura" / "arquitetura.html"
    try:
        texto_json = caminho_json.read_text(encoding="utf-8")
        json.loads(texto_json)  # nunca gravar JSON quebrado dentro do .html
    except (OSError, ValueError) as e:
        return {"ok": False, "erro": f"arquitetura.json ilegível: {e}"}
    try:
        html = caminho_html.read_text(encoding="utf-8")
    except OSError as e:
        return {"ok": False, "erro": f"arquitetura.html ilegível: {e}"}
    m = re.search(r"^const ARCH = (\{.*?^\});", html, re.S | re.M)
    if not m:
        return {"ok": False, "erro": "não achei o bloco `const ARCH = {...}` "
                                     "no arquitetura.html"}
    if m.group(1).strip() == texto_json.strip():
        return {"ok": True, "mudou": False}
    novo = html[:m.start(1)] + texto_json.strip() + html[m.end(1):]
    caminho_html.write_text(novo, encoding="utf-8")
    return {"ok": True, "mudou": True}


def skills_na_arquitetura(raiz):
    try:
        doc = json.loads((raiz / "arquitetura" / "arquitetura.json")
                         .read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return set()
    nomes = set()

    def varrer(o):
        if isinstance(o, dict):
            n = o.get("nome")
            if isinstance(n, str):
                nomes.add(n.lstrip("/").lower())
            for v in o.values():
                varrer(v)
        elif isinstance(o, list):
            for v in o:
                varrer(v)

    varrer(doc)
    return nomes


# ---------------------------------------------------------------------------
# A verificacao propriamente dita
# ---------------------------------------------------------------------------
def pendencias(raiz, mexidas):
    """`mexidas`: {skill: {"desde": epoch}}. Devolve lista de dicts com o que
    falta em cada skill (nota e/ou arquitetura)."""
    na_arq = skills_na_arquitetura(raiz)
    fora = []
    for skill, dados in sorted(mexidas.items()):
        desde = float(dados.get("desde") or 0)
        principal, citam = notas_da_skill(skill)
        falta_nota = None
        if principal is None:
            falta_nota = ("CRIAR a nota (nenhuma no cofre tem esta skill no "
                          "título)" +
                          (f"; citam de passagem: {', '.join(c.name for c in citam)}"
                           if citam else ""))
        else:
            try:
                atualizada = principal.stat().st_mtime >= desde
            except OSError:
                atualizada = False
            if not atualizada:
                falta_nota = (f"ATUALIZAR {principal.name} (acrescentar a seção "
                              f"'## Atualização ({datetime.now().strftime('%d/%m/%Y')})', "
                              "sem reescrever o que já está lá)")
        falta_arq = None
        if skill.lower() not in na_arq:
            falta_arq = "a skill não aparece no arquitetura.json"
        if falta_nota or falta_arq:
            fora.append({"skill": skill, "nota": falta_nota,
                         "arquitetura": falta_arq,
                         "nota_arquivo": principal.name if principal else None})
    return fora


def texto_cobranca(raiz, faltando, arq_ok, arq_msg):
    L = ["DOCUMENTACAO PENDENTE — skill mexida nesta sessão sem a nota/arquitetura em dia.",
         "(regra da casa: AGENTS.md, seção \"Documentação obrigatória\")", ""]
    for item in faltando:
        L.append(f"* /{item['skill']}")
        if item["nota"]:
            L.append(f"    - nota: {item['nota']}")
        if item["arquitetura"]:
            L.append(f"    - arquitetura: {item['arquitetura']}")
    if not arq_ok:
        L += ["", f"* arquitetura: {arq_msg}"]
    L += ["",
          f"Cofre das notas: {PASTA_NOTAS}",
          "Padrão da nota: título; citação inicial com a data e \"verificado no "
          "código\" (listando os arquivos conferidos); o que a skill faz em 1 "
          "frase; como funciona; o que mudou hoje e por quê; limites e "
          "pegadinhas; \"Relação com outras notas\".",
          "Confira no código, nada de memória. Sem dados reais de empresa ou "
          "trabalhador.",
          "",
          "Se a mudança for pequena a ponto de não alterar a nota nem a "
          "arquitetura, diga isso ao AFT em uma linha e siga - esta cobrança "
          "não se repete nesta sessão."]
    return "\n".join(L)


# ---------------------------------------------------------------------------
# Ganchos
# ---------------------------------------------------------------------------
def hook_registrar():
    """PostToolUse (Edit|Write): anota a skill mexida. Silencioso e a prova de
    falha - um gancho que quebra ou demora atrapalha TODA edicao do AFT."""
    try:
        evento = json.load(sys.stdin)
        arq = (evento.get("tool_input") or {}).get("file_path") or ""
        if not arq:
            return 0
        raiz = raiz_repo(Path(arq).parent)
        if raiz is None:
            return 0
        skill = skill_do_caminho(arq, raiz)
        if not skill:
            return 0
        sessao = evento.get("session_id") or "sem-sessao"
        estado = ler_estado(sessao)
        estado.setdefault("raiz", str(raiz))
        mexidas = estado.setdefault("mexidas", {})
        registro = mexidas.setdefault(skill, {"desde": time.time(), "arquivos": []})
        nome = str(Path(arq).name)
        if nome not in registro["arquivos"]:
            registro["arquivos"].append(nome)
        gravar_estado(sessao, estado)
        _limpar_estado_velho()
    except Exception:
        pass
    return 0


def hook_verificar():
    """Stop: se ha skill mexida sem documentacao, devolve a pendencia ao
    assistente (exit 2 = ele continua trabalhando). Cada skill e cobrada uma
    unica vez por sessao."""
    try:
        evento = json.load(sys.stdin)
    except Exception:
        return 0
    try:
        sessao = evento.get("session_id") or "sem-sessao"
        estado = ler_estado(sessao)
        mexidas = estado.get("mexidas") or {}
        if not mexidas:
            return 0
        raiz = Path(estado.get("raiz") or "")
        if not (raiz / "AGENTS.md").is_file():
            return 0
        ja_cobradas = set(estado.get("cobradas") or [])
        pendentes = [p for p in pendencias(raiz, mexidas)
                     if p["skill"] not in ja_cobradas]
        arq_ok, arq_msg = checar_arquitetura(raiz)
        arq_ja_cobrada = bool(estado.get("arq_cobrada"))
        if not pendentes and (arq_ok or arq_ja_cobrada):
            return 0
        estado["cobradas"] = sorted(ja_cobradas | {p["skill"] for p in pendentes})
        if not arq_ok:
            estado["arq_cobrada"] = True
        gravar_estado(sessao, estado)
        sys.stderr.write(texto_cobranca(raiz, pendentes, arq_ok, arq_msg) + "\n")
        return 2
    except Exception:
        return 0  # duvida nenhuma: gancho quebrado nunca trava o trabalho


# ---------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(
        description="Guarda-livros das notas tecnicas do AFT Toolkit")
    ap.add_argument("--hook-registrar", action="store_true",
                    help="gancho PostToolUse (Edit|Write)")
    ap.add_argument("--hook-verificar", action="store_true",
                    help="gancho Stop")
    ap.add_argument("--verificar", action="store_true",
                    help="mostra o que esta pendente nesta sessao")
    ap.add_argument("--sessao", help="id da sessao (com --verificar)")
    ap.add_argument("--nota-de", metavar="SKILL",
                    help="qual nota do cofre cobre esta skill")
    ap.add_argument("--checar-arquitetura", action="store_true",
                    help="compara o arquitetura.json com o bloco ARCH do .html")
    ap.add_argument("--sincronizar-arquitetura", action="store_true",
                    help="regera o bloco ARCH do .html a partir do .json")
    ap.add_argument("--repo", help="raiz do repositorio (padrao: a partir do cwd)")
    args = ap.parse_args()

    if args.hook_registrar:
        sys.exit(hook_registrar())
    if args.hook_verificar:
        sys.exit(hook_verificar())

    raiz = raiz_repo(args.repo or Path(__file__).resolve().parent)
    if raiz is None:
        print("ERRO: não encontrei a raiz do AFT Toolkit (AGENTS.md + "
              "arquitetura/arquitetura.json) a partir daqui.")
        sys.exit(1)

    if args.sincronizar_arquitetura:
        r = sincronizar_arquitetura(raiz)
        if not r["ok"]:
            print("ERRO: " + r["erro"])
            sys.exit(1)
        print("arquitetura.html " + ("atualizado a partir do .json"
                                     if r["mudou"] else "já estava em dia"))
        sys.exit(0)

    if args.checar_arquitetura:
        ok, msg = checar_arquitetura(raiz)
        print(("OK: " if ok else "DIVERGENTE: ") + msg)
        sys.exit(0 if ok else 1)

    if args.nota_de:
        skill = args.nota_de.lstrip("/")
        principal, citam = notas_da_skill(skill)
        print(f"skill: /{skill}")
        print(f"  nota principal: {principal.name if principal else 'NENHUMA - criar'}")
        if citam:
            print("  citada também em: " + ", ".join(c.name for c in citam))
        print(f"  cofre: {PASTA_NOTAS}")
        sys.exit(0)

    if args.verificar:
        estado = ler_estado(args.sessao) if args.sessao else {}
        mexidas = estado.get("mexidas") or {}
        ok, msg = checar_arquitetura(raiz)
        if not mexidas:
            print("Nenhuma skill registrada como mexida" +
                  (f" na sessão {args.sessao}." if args.sessao
                   else " (informe --sessao <id> para consultar uma sessão)."))
        else:
            faltando = pendencias(raiz, mexidas)
            if faltando:
                print(texto_cobranca(raiz, faltando, ok, msg))
            else:
                print("Documentação em dia para: " +
                      ", ".join("/" + s for s in sorted(mexidas)))
        print(("OK: " if ok else "DIVERGENTE: ") + msg)
        sys.exit(0)

    ap.print_help()


if __name__ == "__main__":
    main()
