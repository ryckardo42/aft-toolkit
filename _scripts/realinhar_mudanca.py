#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
realinhar_mudanca.py - Costura o que a mudanca da pasta de trabalho deixa para tras.

Por que este modulo existe (ticket 29/07/2026): o `pasta_aft.py --definir ...
--mover` move os ARQUIVOS da pasta AFT com seguranca, mas o toolkit tem outras
tres coisas que guardam o caminho antigo POR DENTRO e nao se mexem sozinhas:

  1. As SESSOES do app do Claude Code (uma por empresa, grupo "OS ATIVAS").
     Cada sessao e um `local_<uuid>.json` com os campos `cwd`/`originCwd`
     apontando para a pasta da OS. Sem reescrever, o app mostra "Sessao nao
     encontrada no disco" - foi o que aconteceu com 2 de 8 sessoes numa
     mudanca real.
  2. O HISTORICO de conversa de cada sessao, em ~/.claude/projects/<codificado>,
     onde <codificado> e o cwd com todo caractere que nao seja letra ou numero
     trocado por hifen. Como o cwd nao mudava, a pasta ficava presa no caminho
     velho.
  3. Os SERVICOS do sistema (servidor do painel, rotina diaria e vigia de
     sessoes): a tarefa agendada guarda a pasta de OS congelada na instalacao, e
     o processo que ja esta rodando guarda os caminhos em memoria. Sem
     reinstalar, o painel continua servindo a pasta antiga - e chega a
     recria-la ao salvar o painel.html.

Regra de ouro das sessoes: NAO se escreve num `local_*.json` com o app ABERTO
(ele regrava os arquivos por cima ao fechar). Quando o app esta aberto, este
modulo grava uma PENDENCIA em ~/.claude/aft-realinhar-pendente.json e quem a
executa depois e o vigia de sessoes (que ja vive esperando o app fechar) ou a
/aft-sessoes-os. A pendencia mora fora da pasta AFT de proposito: ela precisa
sobreviver a propria mudanca de pasta.

Uso no terminal:
    python realinhar_mudanca.py --de "<pasta antiga>" --para "<pasta nova>"
    python realinhar_mudanca.py --de ... --para ... --esperar-app
    python realinhar_mudanca.py --pendencias      # executa o que ficou pendente
    python realinhar_mudanca.py --status          # o que esta pendente (nao altera)
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
import time
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

IS_WIN = sys.platform.startswith("win")
SEM_JANELA = {"creationflags": getattr(subprocess, "CREATE_NO_WINDOW", 0)} if IS_WIN else {}

AQUI = Path(__file__).resolve().parent
PROJETOS = Path.home() / ".claude" / "projects"
PENDENCIA = Path.home() / ".claude" / "aft-realinhar-pendente.json"

# Servicos que guardam a pasta de OS por dentro. (nome da tarefa no Windows,
# label do launchd no macOS, script instalador, se precisa da pasta de OS)
SERVICOS = (
    ("Painel AFT - Servidor", "br.aft.painel-servidor",
     "instalar_servidor_painel.py", True, "servidor do painel"),
    ("Painel AFT", "br.aft.painel",
     "instalar_rotina_painel.py", True, "rotina diaria do painel"),
    ("AFT Sessoes - Vigia", "br.aft.sessoes-vigia",
     "instalar_vigia_sessoes.py", False, "vigia de sessoes"),
)


# ── Caminhos ────────────────────────────────────────────────────────────────

LIMITE_PROJETO = 200  # o `ixt` do app


def _hash_js(texto: str) -> int:
    """O hash de 32 bits com sinal que o app usa (o classico `h*31 + c`):
    `t=(t<<5)-t+e.charCodeAt(r)|0`. Percorre unidades UTF-16, como o
    JavaScript - por isso o encode utf-16-le em vez de ord()."""
    h = 0
    bytes_ = texto.encode("utf-16-le", errors="replace")
    for i in range(0, len(bytes_) - 1, 2):
        h = ((h << 5) - h + (bytes_[i] | (bytes_[i + 1] << 8))) & 0xFFFFFFFF
        if h >= 0x80000000:  # o `|0` do JavaScript: volta a ser com sinal
            h -= 0x100000000
    return h


def _base36(n: int) -> str:
    if n == 0:
        return "0"
    digitos = "0123456789abcdefghijklmnopqrstuvwxyz"
    saida = ""
    while n:
        n, r = divmod(n, 36)
        saida = digitos[r] + saida
    return saida


def codificar_projeto(caminho) -> str:
    """Nome da pasta de historico em ~/.claude/projects para um `cwd`.

    Espelha exatamente o que o app faz (conferido no binario do claude-code
    2.1.219): troca todo caractere que nao seja letra ou numero por hifen e, se
    o resultado passar de 200 caracteres, corta em 200 e cola um hash do
    caminho original em base 36.

        C:\\Users\\ana\\Documents\\AFT\\OS ATIVAS
        -> C--Users-ana-Documents-AFT-OS-ATIVAS

    Se a regra do app mudar um dia, este modulo simplesmente nao acha a pasta
    antiga e nao migra nada - nunca inventa uma pasta no lugar errado."""
    bruto = str(caminho)
    nome = re.sub(r"[^A-Za-z0-9]", "-", bruto)
    if len(nome) <= LIMITE_PROJETO:
        return nome
    return f"{nome[:LIMITE_PROJETO]}-{_base36(abs(_hash_js(bruto)))}"


def _traduzir(alvo, de: Path, para: Path) -> Path | None:
    """`alvo` reescrito para a pasta nova, ou None se ele nao mora na antiga.
    No Windows a comparacao do pathlib ja ignora maiusculas/minusculas."""
    if not alvo:
        return None
    try:
        rel = Path(str(alvo)).relative_to(de)
    except (ValueError, OSError):
        return None
    return para if str(rel) in (".", "") else para / rel


def _config(pasta_aft: Path) -> dict:
    """Campos do aft-config.md que os servicos precisam (melhor esforco)."""
    dados: dict[str, str] = {}
    try:
        cfg = pasta_aft / "aft-config.md"
        if not cfg.is_file():
            return dados
        texto = cfg.read_text(encoding="utf-8", errors="replace")
        for campo in ("python_path", "rotina_painel", "servidor_painel"):
            m = re.search(rf'^{campo}\s*:\s*"?([^"#\n]*?)"?\s*$', texto, re.MULTILINE)
            if m and m.group(1).strip():
                dados[campo] = m.group(1).strip().replace("\\\\", "\\")
    except Exception:
        pass
    return dados


# ── Pendencia (a mudanca ja aconteceu; falta aplicar com o app fechado) ─────

def pendencia_ler() -> list[dict]:
    try:
        if not PENDENCIA.is_file():
            return []
        dados = json.loads(PENDENCIA.read_text(encoding="utf-8"))
        return [p for p in dados if isinstance(p, dict) and p.get("de") and p.get("para")]
    except Exception:
        return []


def pendencia_gravar(de: Path, para: Path) -> bool:
    """Enfileira uma mudanca para ser aplicada quando o app fechar. Acumula: se
    o AFT mudar a pasta duas vezes antes de reabrir o app, as duas entram na
    fila e sao aplicadas em ordem."""
    try:
        fila = pendencia_ler()
        fila.append({"de": str(de), "para": str(para),
                     "quando": time.strftime("%Y-%m-%d %H:%M:%S")})
        PENDENCIA.parent.mkdir(parents=True, exist_ok=True)
        PENDENCIA.write_text(json.dumps(fila, ensure_ascii=False, indent=2),
                             encoding="utf-8")
        return True
    except Exception:
        return False


def pendencia_limpar() -> bool:
    try:
        if PENDENCIA.is_file():
            PENDENCIA.unlink()
        return True
    except Exception:
        return False


# ── Sessoes do app ──────────────────────────────────────────────────────────

def _sessoes_mod():
    sys.path.insert(0, str(AQUI))
    import sessoes_os  # noqa: PLC0415
    return sessoes_os


def app_aberto() -> bool:
    try:
        return _sessoes_mod().app_aberto()
    except Exception:
        return False


def realinhar_sessoes(de: Path, para: Path) -> dict:
    """Reescreve `cwd`/`originCwd` das sessoes do app que apontam para a pasta
    antiga. Faz backup de cada arquivo antes. Pressupoe o app FECHADO - quem
    checa isso e o chamador (`executar`)."""
    saida: dict = {"corrigidas": [], "ignoradas": [], "erros": [], "cwds": []}
    try:
        so = _sessoes_mod()
        dir_s = so.dir_sessoes()
    except Exception as e:
        saida["erros"].append(f"pasta de sessoes do app nao encontrada ({e})")
        return saida
    if not dir_s:
        saida["erros"].append("pasta de sessoes do app nao encontrada")
        return saida

    backups = para / ".backups-sessoes" / time.strftime("realinhamento-%Y%m%d-%H%M%S")
    for arq in sorted(dir_s.glob("local_*.json")):
        try:
            dados = json.loads(arq.read_text(encoding="utf-8"))
        except Exception:
            continue
        troca = {}
        for campo in ("cwd", "originCwd"):
            novo = _traduzir(dados.get(campo), de, para)
            if novo is not None:
                troca[campo] = str(novo)
        if not troca:
            continue
        antigo_cwd = dados.get("cwd") or dados.get("originCwd")
        if antigo_cwd:
            saida["cwds"].append(str(antigo_cwd))
        destino = Path(troca.get("cwd") or troca.get("originCwd"))
        titulo = dados.get("title") or arq.stem
        # So reescreve quando a pasta nova EXISTE de verdade: uma sessao que
        # apontava para uma OS apagada ha meses continuaria quebrada de todo
        # jeito, e trocar o caminho dela so mudaria o endereco do buraco.
        if not destino.is_dir():
            saida["ignoradas"].append({"sessao": arq.stem, "titulo": titulo,
                                       "motivo": f"'{destino}' nao existe"})
            continue
        try:
            backups.mkdir(parents=True, exist_ok=True)
            shutil.copy2(arq, backups / arq.name)
            dados.update(troca)
            arq.write_text(json.dumps(dados, ensure_ascii=False, indent=2),
                           encoding="utf-8")
            saida["corrigidas"].append({"sessao": arq.stem, "titulo": titulo,
                                        "cwd": troca.get("cwd", "")})
        except Exception as e:
            saida["erros"].append(f"{arq.name}: {type(e).__name__}: {e}")
    if backups.is_dir():
        saida["backup"] = str(backups)
    return saida


# ── Historico de conversa (~/.claude/projects) ──────────────────────────────

def _candidatos_historico(de: Path, para: Path, cwds) -> list[Path]:
    """Pastas antigas que podem ter historico: as que as sessoes usavam, mais a
    propria pasta AFT, as subpastas de OS e as OS de dentro delas. Nunca sai
    varrendo ~/.claude/projects por prefixo: 'AFT' e 'AFT-2' dariam o mesmo
    comeco de nome e um seria migrado no lugar do outro."""
    vistos: list[Path] = []

    def juntar(p: Path) -> None:
        if p not in vistos:
            vistos.append(p)

    for c in cwds:
        try:
            juntar(Path(str(c)))
        except Exception:
            continue
    juntar(de)
    for sub in ("OS ATIVAS", "OS ARQUIVADAS"):
        juntar(de / sub)
        try:
            for d in (para / sub).iterdir():
                if d.is_dir():
                    juntar(de / sub / d.name)
        except OSError:
            pass
    return vistos


def _copiar_sem_sobrescrever(pa, origem: Path, destino: Path) -> list[str]:
    """Copia o que falta de `origem` em `destino`, sem tocar no que ja existe.
    Devolve a lista de erros (vazia = tudo que faltava foi copiado)."""
    erros: list[str] = []
    raiz, alvo_raiz = pa._ext(origem), pa._ext(destino)
    for atual, _dirs, arqs in os.walk(raiz):
        rel = os.path.relpath(atual, raiz)
        alvo = alvo_raiz if rel == "." else os.path.join(alvo_raiz, rel)
        try:
            os.makedirs(alvo, exist_ok=True)
        except Exception as e:
            erros.append(f"{rel}: {type(e).__name__}: {e}")
            continue
        for a in arqs:
            destino_arq = os.path.join(alvo, a)
            if os.path.exists(destino_arq):
                continue
            try:
                shutil.copy2(os.path.join(atual, a), destino_arq)
            except Exception as e:
                erros.append(f"{os.path.join(rel, a)}: {type(e).__name__}: {e}")
    return erros


def migrar_historicos(de: Path, para: Path, cwds=()) -> dict:
    """Leva as pastas de ~/.claude/projects do nome codificado antigo para o
    novo. Copia-confere-apaga (o mesmo cuidado da mudanca de arquivos); se o
    destino ja existir, junta sem sobrescrever nada."""
    sys.path.insert(0, str(AQUI))
    import pasta_aft as pa  # helpers de caminho estendido/copia conferida
    saida: dict = {"migrados": [], "juntados": [], "erros": []}
    if not PROJETOS.is_dir():
        return saida
    for antigo in _candidatos_historico(de, para, cwds):
        novo = _traduzir(antigo, de, para)
        if novo is None:
            continue
        orig = PROJETOS / codificar_projeto(antigo)
        dest = PROJETOS / codificar_projeto(novo)
        if orig == dest or not orig.is_dir():
            continue
        juntando = dest.exists()
        try:
            if not juntando:
                try:
                    os.rename(orig, dest)  # caminho feliz: instantaneo
                    saida["migrados"].append({"de": orig.name, "para": dest.name})
                    continue
                except OSError:
                    pass
            # Juntando duas pastas de historico: NUNCA escreve por cima de uma
            # transcricao que ja esta la (cada conversa e um arquivo proprio).
            erros = _copiar_sem_sobrescrever(pa, orig, dest) if juntando \
                else pa._copiar_arvore(orig, dest)
            if erros:
                saida["erros"].append(f"{orig.name}: {erros[0]}")
                continue
            resistiram = pa._apagar_arvore(orig)
            if [c for c in resistiram if os.path.isfile(c)]:
                saida["erros"].append(
                    f"{orig.name}: copiado para {dest.name}, mas a pasta antiga "
                    "nao pode ser apagada (arquivo em uso)")
            saida["juntados" if juntando else "migrados"].append(
                {"de": orig.name, "para": dest.name})
        except Exception as e:
            saida["erros"].append(f"{orig.name}: {type(e).__name__}: {e}")
    return saida


# ── Servicos do sistema ─────────────────────────────────────────────────────

def _servico_instalado(tarefa: str, label: str) -> bool:
    if IS_WIN:
        try:
            return subprocess.run(["schtasks", "/Query", "/TN", tarefa],
                                  capture_output=True, **SEM_JANELA).returncode == 0
        except OSError:
            return False
    return (Path.home() / "Library" / "LaunchAgents" / f"{label}.plist").is_file()


def servicos_instalados() -> list[str]:
    return [tarefa for tarefa, label, _s, _p, _n in SERVICOS
            if _servico_instalado(tarefa, label)]


def parar_servicos() -> dict:
    """Derruba os servicos que leem/escrevem na pasta AFT, ANTES de move-la.
    Sem isto o servidor do painel salva o painel.html no meio da mudanca e
    recria a pasta antiga; e o vigia continua com os caminhos velhos em
    memoria. Devolve quais estavam instalados, para reinstalar depois."""
    instalados = servicos_instalados()
    if not instalados:
        return {"instalados": []}
    if IS_WIN:
        partes = [f"Stop-ScheduledTask -TaskName '{t}' -ErrorAction SilentlyContinue"
                  for t in instalados]
        partes.append(
            "Get-CimInstance Win32_Process -Filter \"Name like '%python%'\" | "
            "Where-Object { $_.CommandLine -like '*servir_painel.py*' -or "
            "$_.CommandLine -like '*sessoes_os.py*--vigia*' -or "
            "$_.CommandLine -like '*gerar_painel.py*' } | "
            "ForEach-Object { Stop-Process -Id $_.ProcessId -Force "
            "-ErrorAction SilentlyContinue }")
        try:
            subprocess.run(["powershell", "-NoProfile", "-NonInteractive",
                            "-Command", "; ".join(partes)],
                           capture_output=True, text=True, timeout=120, **SEM_JANELA)
        except (OSError, subprocess.TimeoutExpired) as e:
            return {"instalados": instalados, "erro": f"{type(e).__name__}: {e}"}
    else:
        for tarefa, label, _s, _p, _n in SERVICOS:
            if tarefa in instalados:
                plist = Path.home() / "Library" / "LaunchAgents" / f"{label}.plist"
                subprocess.run(["launchctl", "unload", str(plist)], capture_output=True)
    time.sleep(1)
    return {"instalados": instalados}


def realinhar_servicos(pasta_aft: Path, instalados=None) -> dict:
    """Reinstala com o caminho novo os servicos que ja estavam instalados.
    Nunca instala um servico que o AFT nao tinha."""
    saida: dict = {"reinstalados": [], "falhas": []}
    if instalados is None:
        instalados = servicos_instalados()
    if not instalados:
        return saida
    cfg = _config(pasta_aft)
    python_path = cfg.get("python_path") or sys.executable
    if IS_WIN and not Path(python_path).is_file():
        python_path = sys.executable
    pasta_os = str(pasta_aft / "OS ATIVAS")
    for tarefa, _label, script, precisa_pasta, nome in SERVICOS:
        if tarefa not in instalados:
            continue
        cmd = [sys.executable, str(AQUI / script), "instalar", python_path]
        if precisa_pasta:
            cmd.append(pasta_os)
        if script == "instalar_rotina_painel.py":
            cmd += ["--hora", cfg.get("rotina_painel") or "07:00"]
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=180,
                               **SEM_JANELA)
            if r.returncode == 0:
                saida["reinstalados"].append(nome)
            else:
                saida["falhas"].append(
                    f"{nome}: {(r.stderr or r.stdout or '').strip()[:200]}")
        except (OSError, subprocess.TimeoutExpired) as e:
            saida["falhas"].append(f"{nome}: {type(e).__name__}: {e}")
    return saida


# ── Orquestracao ────────────────────────────────────────────────────────────

def executar(de, para, esperar_app: bool = False, reabrir: bool = False) -> dict:
    """Aplica o realinhamento de sessoes + historico de uma mudanca ja feita.
    Com o app ABERTO nao escreve nada: enfileira a pendencia (a menos que
    `esperar_app`, quando espera o app fechar e aplica em seguida)."""
    de, para = Path(de), Path(para)
    if de == para:
        return {"ok": True, "nada_a_fazer": True}
    aberto = app_aberto()
    if aberto and not esperar_app:
        gravou = pendencia_gravar(de, para)
        return {"ok": True, "adiado": True, "pendencia_gravada": gravou,
                "pendencia": str(PENDENCIA),
                "aviso": ("o app do Claude esta aberto, entao as sessoes por empresa "
                          "so podem ser corrigidas depois que ele fechar - o vigia de "
                          "sessoes faz isso sozinho no proximo fechamento do app.")}
    if aberto:
        so = _sessoes_mod()
        while so.app_aberto():
            time.sleep(2)
        so.espera_gravacao_config()

    sess = realinhar_sessoes(de, para)
    hist = migrar_historicos(de, para, sess.get("cwds", []))
    if reabrir:
        try:
            _sessoes_mod().reabrir_app()
        except Exception:
            pass
    return {"ok": not sess.get("erros") and not hist.get("erros"),
            "adiado": False,
            "sessoes_corrigidas": sess.get("corrigidas", []),
            "sessoes_ignoradas": sess.get("ignoradas", []),
            "historicos_migrados": hist.get("migrados", []),
            "historicos_juntados": hist.get("juntados", []),
            "backup_sessoes": sess.get("backup", ""),
            "erros": (sess.get("erros", []) + hist.get("erros", []))}


def executar_pendencias(esperar_app: bool = False) -> dict:
    """Executa a fila deixada por uma mudanca feita com o app aberto. Chamado
    pelo vigia de sessoes (que ja espera o app fechar) e pela /aft-sessoes-os."""
    fila = pendencia_ler()
    if not fila:
        return {"ok": True, "pendencias": 0}
    if app_aberto() and not esperar_app:
        return {"ok": True, "pendencias": len(fila), "adiado": True}
    feitos, restantes = [], []
    for p in fila:
        r = executar(p["de"], p["para"], esperar_app=esperar_app)
        if r.get("adiado"):
            restantes.append(p)
        else:
            feitos.append({**p, "resultado": r})
    if restantes:
        try:
            PENDENCIA.write_text(json.dumps(restantes, ensure_ascii=False, indent=2),
                                 encoding="utf-8")
        except Exception:
            pass
    else:
        pendencia_limpar()
    return {"ok": True, "pendencias": len(fila), "aplicadas": feitos,
            "restantes": len(restantes)}


def main() -> int:
    args = sys.argv[1:]

    def valor(flag):
        if flag in args:
            i = args.index(flag)
            if i + 1 < len(args) and not args[i + 1].startswith("--"):
                return args[i + 1]
        return None

    if "--status" in args:
        print(json.dumps({"pendentes": pendencia_ler(),
                          "arquivo": str(PENDENCIA),
                          "app_aberto": app_aberto(),
                          "servicos_instalados": servicos_instalados()},
                         ensure_ascii=False, indent=2))
        return 0
    if "--pendencias" in args:
        r = executar_pendencias(esperar_app="--esperar-app" in args)
        print(json.dumps(r, ensure_ascii=False, indent=2))
        return 0 if r.get("ok") else 1
    de, para = valor("--de"), valor("--para")
    if de and para:
        r = executar(de, para, esperar_app="--esperar-app" in args,
                     reabrir="--reabrir" in args)
        print(json.dumps(r, ensure_ascii=False, indent=2))
        return 0 if r.get("ok") else 1
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main())
