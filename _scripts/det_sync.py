#!/usr/bin/env python3
"""
det_sync.py — sincroniza as notificações do DET com os memory.md locais.

É o espelho local do sync do SisOS (extensão Chrome "SisOS — Sync DET"):
a extensão captura o token de sessão do DET no navegador do AFT e o entrega
ao servir_painel.py (endpoint POST /api/det-sync), que chama este módulo.

Para cada OS de OS ATIVAS/ com CNPJ/CPF (ou RI no front-matter), consulta a
API oficial do DET (a MESMA que o site usa, com o token do próprio AFT):

    POST https://auditor-det.sit.trabalho.gov.br/services/auditor/v1/notificacoes/pesquisa

e aplica o resultado na seção `## Notificações DET` do memory.md:
  - notificação nova (código ainda não registrado) → acrescenta
    `- [ ] <CODIGO> — prazo <dd/mm/aaaa>`;
  - prazo de entrega que mudou no DET → atualiza a data na linha existente
    (preservando o formato da linha — dd/mm/aaaa ou aaaa-mm-dd);
  - sob cada checkbox, mantém uma SUB-LINHA DE DETALHES gerada do DET
    (`  - lavrada dd/mm/aaaa · ciência dd/mm/aaaa · última entrega
    dd/mm/aaaa · Confirmada[ · ⚠️ atualização pendente]`) — essa linha
    pertence ao sync: é criada se faltar e regravada quando o DET mudar.
    A flag final espelha o triângulo amarelo do DET (campo itemAtualizado
    da API). O gerar_painel a ignora (ele só lê linhas checkbox);
  - `ri:` vazio no front-matter → preenche (ver ris_conhecidos/ri_mais_recente).

Filtros, nesta ordem:
  1. CONFIRMADAS (status=1) e com data de lavratura — igual ao SisOS;
  2. da(s) fiscalização(ões) DESTA OS, pelo RI: o `ri:` do FRONT-MATTER é o
     identificador canônico da auditoria — só entra notificação daquele(s)
     RI(s) (aceita mais de um no campo, separados por vírgula). A pesquisa é
     por empregador, então o DET devolve também notificações de fiscalizações
     antigas do mesmo CNPJ; sem este filtro elas entram na OS errada.
     Notificação de RI alheio nunca é importada nem descartada em silêncio:
     volta em `ignoradas_detalhe`. Ver "Vínculo notificação × OS".

Alerta "⚠️ atualização pendente" (campo itemAtualizado da API): é dispensável —
o AFT clica no alerta no painel ("já vi"), o servir_painel grava
`<!-- visto: ... -->` na sub-linha e o alerta só volta se houver entrega nova.

O estado do checkbox ([ ]/[x]) NUNCA é alterado — respondida é decisão do AFT.
Cada memory.md alterado recebe backup prévio (backup_arquivo.py) e uma linha
no Registro de atividades. O token é usado em memória e nunca gravado.

Variável de ambiente AFT_DET_DRYRUN=1: consulta o DET e devolve o relatório
completo, mas não grava nada — útil para conferir antes de deixar escrever.

Uso normal: via servir_painel.py. Direto (debug):
    python det_sync.py "<PASTA_OS_ATIVAS>" "<token>"
"""
from __future__ import annotations

import datetime
import json
import re
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

AQUI = Path(__file__).resolve().parent
BACKUP = AQUI / "backup_arquivo.py"

DET_API = ("https://auditor-det.sit.trabalho.gov.br"
           "/services/auditor/v1/notificacoes/pesquisa")
DET_TIMEOUT = 12  # segundos por OS (igual ao SisOS)

RE_FM = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
RE_CHECKBOX = re.compile(r"^\s*-\s*\[[ xX]?\]\s*(.*)$")
RE_CODIGO = re.compile(r"([A-Z0-9]{6,})")
# Data de prazo numa linha de DET (mesma detecção do gerar_painel).
RE_PRAZO_LINHA = re.compile(
    r"((?:prazo|entrega\s+at[eé])[:\s]+)(\d{2}/\d{2}/\d{4}|\d{4}-\d{2}-\d{2})",
    re.IGNORECASE)
# Sub-linha de detalhes mantida pelo sync (sempre começa com "  - lavrada").
RE_DETALHE = re.compile(r"^\s+-\s+lavrada\s", re.IGNORECASE)


# ── Chamada à API do DET ─────────────────────────────────────────────────────

def consultar_det(token: str, cnpj: str, ri: str) -> list[dict]:
    """Notificações do DET para um empregador (CNPJ/CPF) ou RI.
    Mesmo corpo de pesquisa do SisOS. Lança RuntimeError em falha."""
    corpo = {
        "isPesquisaPadrao": False,
        "niEmpregador": cnpj or None,
        "ri": None if cnpj else (ri or None),
        "codigoNotificacao": None,
        "cifAuditor": None,
        "isSomenteMinhas": True,
        "sequencia": 0,
        "ordenacaoCampo": "id",
        "ordenacaoDesc": False,
        "isPendenciaComunicacaoAuditor": False,
        "isPendenciaComunicacaoEmpregador": False,
        "situacaoFisc": None,
    }
    req = urllib.request.Request(
        DET_API,
        data=json.dumps(corpo).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json, text/plain, */*",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=DET_TIMEOUT) as resp:
            dados = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detalhe = e.read().decode("utf-8", errors="replace")[:200]
        raise RuntimeError(f"DET API {e.code}: {detalhe}") from e
    except Exception as e:
        raise RuntimeError(f"DET inacessível: {e}") from e
    return dados.get("notificacoes") or []


def elegiveis(notificacoes: list[dict]) -> list[dict]:
    """Só confirmadas (status=1) com data de lavratura — igual ao SisOS."""
    return [n for n in notificacoes
            if n.get("status") == 1 and n.get("dataEnvio")]


# ── Vínculo notificação × OS (o filtro que importa) ─────────────────────────
#
# A pesquisa no DET é por CNPJ/CPF do EMPREGADOR, e devolve as notificações de
# TODAS as fiscalizações já feitas naquele empregador — inclusive as de anos
# anteriores, já concluídas. O que amarra uma notificação a ESTA OS é o RI
# (Relatório de Inspeção), presente em cada notificação.
#
# REGRA (decidida em 22/07/2026, caso CONSORCIO SQ, RI alheio 319969819): o
# `ri:` do FRONT-MATTER é O identificador canônico da auditoria — só entra
# notificação cujo RI esteja nele. Nada de inferir RI por notificações já
# registradas na ficha: a união antiga fazia um RI de fiscalização antiga
# (registrado na ficha um dia, por engano ou importação) virar "conhecido"
# e puxar as irmãs dele para sempre.
#
# OS que acompanha DUAS fiscalizações do mesmo empregador (ex.: ação fiscal
# normal + investigação de acidente): declare os dois RIs no próprio campo,
# separados por vírgula — `ri: "320038432, 320199999"`. Explícito, decidido
# pelo AFT, nunca inferido.
#
# `ri:` vazio: adota o RI da notificação mais recente (ri_mais_recente) e o
# grava no front-matter — a partir daí a regra estrita vale.
#
# Notificação de RI alheio nunca é importada — mas também nunca é descartada
# em silêncio: volta no relatório (`ignoradas_detalhe`) para o AFT decidir.

def ris_da_os(ri_fm: str) -> set[str]:
    """RIs desta OS = somente o(s) do campo `ri:` do front-matter (9 dígitos
    cada; aceita mais de um, separados por vírgula/espaço)."""
    return set(re.findall(r"\d{9}", ri_fm or ""))


def ri_mais_recente(notifs: list[dict]) -> str:
    """RI da notificação mais recente (por data de lavratura) — usado só quando
    a OS ainda não conhece nenhum RI. Uma OS ativa é a fiscalização em curso,
    então a notificação mais nova é a que a identifica."""
    melhor, quando = "", ""
    for n in notifs:
        ri = re.sub(r"\D", "", n.get("ri") or "")
        env = n.get("dataEnvio") or ""
        if re.fullmatch(r"\d{9}", ri) and env > quando:
            melhor, quando = ri, env
    return melhor


# ── Edição do memory.md (funções puras, testáveis sem rede) ─────────────────

def _data_br(iso: str | None) -> str:
    """'2026-07-31[T...]' → '31/07/2026'; '' se vazio/ilegível."""
    if not iso:
        return ""
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", iso)
    return f"{m.group(3)}/{m.group(2)}/{m.group(1)}" if m else ""


def _data_presente(linha: str, iso: str) -> bool:
    """A data (BR ou ISO) já aparece em algum lugar da linha, em qualquer
    frase? Evita colar '— prazo X' redundante quando a data já está escrita
    de outra forma (ex.: '...vistoria de 30/07/2026')."""
    return _data_br(iso) in linha or iso[:10] in linha


def _mesma_data(txt: str, iso: str | None) -> bool:
    """Compara a data da linha (qualquer formato) com a ISO do DET."""
    if not iso:
        return not txt
    m = re.match(r"(\d{2})/(\d{2})/(\d{4})", txt)
    if m:
        norm = f"{m.group(3)}-{m.group(2)}-{m.group(1)}"
    else:
        norm = txt[:10]
    return norm == iso[:10]


RE_VISTO = re.compile(r"<!--\s*visto:\s*([^\s>]+)\s*-->")


def _fingerprint(n: dict) -> str:
    """Estado da notificação que interessa ao alerta: a última entrega da
    empresa. Se mudar (entrega nova), é novidade de verdade."""
    return (n.get("itemDataUltimaEntrega") or "")[:10] or "sem-entrega"


def _linha_detalhe(n: dict, visto: str = "") -> str:
    """Sub-linha de detalhes de uma notificação (dados vindos do DET).
    Campos vazios são omitidos; status 1 = Confirmada (único elegível).

    `itemAtualizado` é o campo da API por trás do triângulo amarelo do DET
    ("Existe atualização pendente"). Constatado em produção (19-22/07/2026,
    casos SPE CAMETA e CONSORCIO SQ): a API pode CONTINUAR devolvendo true
    mesmo depois de o triângulo sumir na tela (o triângulo apaga quando o
    AFT abre a notificação na interface; o campo, não necessariamente).
    Por isso o alerta é DISPENSÁVEL: quando o AFT clica "já vi" no painel,
    o servir_painel grava `<!-- visto: <última entrega> -->` na sub-linha,
    e o sync só volta a exibir o alerta se a última entrega MUDAR (entrega
    nova da empresa = novidade real). O marcador é preservado a cada
    regravação."""
    partes = []
    if n.get("dataEnvio"):
        partes.append(f"lavrada {_data_br(n['dataEnvio'])}")
    if n.get("dataCiencia"):
        partes.append(f"ciência {_data_br(n['dataCiencia'])}")
    if n.get("itemDataUltimaEntrega"):
        partes.append(f"última entrega {_data_br(n['itemDataUltimaEntrega'])}")
    partes.append("Confirmada" if n.get("status") == 1
                  else f"status {n.get('status')}")
    atualizado = n.get("itemAtualizado")
    if isinstance(atualizado, str):  # blindagem: "false"/"N" são falsos
        atualizado = atualizado.strip().lower() in ("true", "s", "sim", "1")
    if atualizado and _fingerprint(n) != visto:
        partes.append("⚠️ atualização pendente")
    linha = "  - " + " · ".join(partes)
    if visto:
        linha += f" <!-- visto: {visto} -->"
    return linha + "\n"


def aplicar_notificacoes(texto: str, notifs: list[dict]) -> tuple[str, int, int, int]:
    """Aplica as notificações elegíveis na seção ## Notificações DET.
    Devolve (novo_texto, inseridas, prazos_atualizados, detalhes_atualizados).
    Função pura."""
    linhas = texto.splitlines(keepends=True)

    ini = fim = -1
    for i, l in enumerate(linhas):
        if l.strip().startswith("## ") and l.strip()[3:].strip() in (
                "Notificações DET", "Notificacoes DET"):
            ini = i + 1
            break
    if ini < 0:
        # memory.md sem a seção: cria antes da primeira '## ' (ou no fim).
        pos = next((i for i, l in enumerate(linhas)
                    if l.strip().startswith("## ")), len(linhas))
        linhas[pos:pos] = ["## Notificações DET\n", "\n"]
        ini = pos + 1
    fim = next((i for i in range(ini, len(linhas))
                if linhas[i].strip().startswith("## ")), len(linhas))

    # Índice: código → nº da linha (só linhas checkbox da seção).
    por_codigo: dict[str, int] = {}
    for i in range(ini, fim):
        cb = RE_CHECKBOX.match(linhas[i])
        if not cb:
            continue
        cod = RE_CODIGO.match(cb.group(1).strip())
        if cod:
            por_codigo[cod.group(1)] = i

    inseridas = atualizadas = detalhes = 0
    novas: list[str] = []
    inserir_detalhe: list[tuple[int, str]] = []  # (posição, linha) — aplicados no fim
    for n in notifs:
        codigo = (n.get("codigo") or "").strip()
        if not codigo:
            continue
        prazo_iso = n.get("itemDataProximaEntrega")
        i = por_codigo.get(codigo)
        if i is None:
            prazo = _data_br(prazo_iso)
            novas.append(f"- [ ] {codigo}" + (f" — prazo {prazo}\n" if prazo else "\n"))
            novas.append(_linha_detalhe(n))
            inseridas += 1
            continue
        # Já registrada: mantém a sub-linha de detalhes (cria/regrava se mudou),
        # preservando o marcador `visto:` que o AFT tenha gravado pelo painel.
        visto = ""
        if i + 1 < fim and RE_DETALHE.match(linhas[i + 1]):
            mv = RE_VISTO.search(linhas[i + 1])
            visto = mv.group(1) if mv else ""
        det = _linha_detalhe(n, visto)
        if i + 1 < fim and RE_DETALHE.match(linhas[i + 1]):
            if linhas[i + 1] != det:
                linhas[i + 1] = det
                detalhes += 1
        else:
            inserir_detalhe.append((i + 1, det))
            detalhes += 1
        # Atualiza o prazo se mudou (preserva o formato da linha).
        if not prazo_iso:
            continue
        ms = list(RE_PRAZO_LINHA.finditer(linhas[i]))
        if len(ms) == 1:
            m = ms[0]
            if not _mesma_data(m.group(2), prazo_iso):
                # Preserva o formato que a linha já usava (ISO ou dd/mm/aaaa).
                nova_data = prazo_iso[:10] if "-" in m.group(2) else _data_br(prazo_iso)
                linhas[i] = linhas[i][:m.start(2)] + nova_data + linhas[i][m.end(2):]
                atualizadas += 1
        elif not ms and not _data_presente(linhas[i], prazo_iso):
            # Linha sem NENHUM prazo escrito (nem em outra forma) e o DET agora
            # tem um: acrescenta no fim.
            corpo = linhas[i].rstrip("\n")
            linhas[i] = f"{corpo} — prazo {_data_br(prazo_iso)}\n"
            atualizadas += 1
        # 2+ "prazo"/"entrega até" na mesma linha: ambíguo (a API só informa UM
        # próximo prazo por notificação, não por item) — nunca escolhe sozinho
        # qual trocar. A linha fica intocada; o AFT decide manualmente.

    # Sub-linhas de detalhe novas: inseridas de trás para frente, para não
    # deslocar os índices ainda pendentes.
    for pos, det in sorted(inserir_detalhe, reverse=True):
        linhas.insert(pos, det)
        fim += 1

    if novas:
        # Insere após a última linha checkbox — pulando a sub-linha de
        # detalhes dela — ou no início da seção; remove um "_(vazio)_" que
        # esteja sozinho na seção.
        ult = max((i for i in range(ini, fim) if RE_CHECKBOX.match(linhas[i])),
                  default=None)
        if ult is None:
            for i in range(ini, fim):
                if linhas[i].strip() in ("_(vazio)_", "(vazio)"):
                    del linhas[i]
                    fim -= 1
                    break
            pos = ini
            while pos < fim and not linhas[pos].strip():
                pos += 1
            linhas[pos:pos] = novas
        else:
            pos = ult + 1
            if pos < fim and RE_DETALHE.match(linhas[pos]):
                pos += 1
            linhas[pos:pos] = novas

    return "".join(linhas), inseridas, atualizadas, detalhes


def preencher_ri(texto: str, ri: str) -> tuple[str, bool]:
    """Preenche `ri:` no front-matter se estiver vazio. Nunca sobrescreve um RI
    já preenchido. O RI vem decidido de fora (ris_conhecidos/ri_mais_recente) —
    esta função não escolhe RI sozinha."""
    if not re.fullmatch(r"\d{9}", ri or ""):
        return texto, False
    m = RE_FM.match(texto)
    if not m:
        return texto, False
    fm = m.group(1)
    atual = re.search(r"^ri\s*:\s*(.*)$", fm, re.MULTILINE)
    valor = (atual.group(1).strip().strip('"').strip("'") if atual else "")
    if valor not in ("", "null", "~"):
        return texto, False
    if atual:
        fm_novo = fm[:atual.start()] + f'ri: "{ri}"' + fm[atual.end():]
    else:
        fm_novo = fm + f'\nri: "{ri}"'
    return texto[:m.start(1)] + fm_novo + texto[m.end(1):], True


def registrar_atividade(texto: str, detalhe: str) -> str:
    """Linha no Registro de atividades (best-effort: sem a seção, não mexe)."""
    linhas = texto.splitlines(keepends=True)
    ini = next((i + 1 for i, l in enumerate(linhas)
                if l.strip() == "## Registro de atividades"), -1)
    if ini < 0:
        return texto
    fim = next((i for i in range(ini, len(linhas))
                if linhas[i].strip().startswith("## ")), len(linhas))
    ult = max((i for i in range(ini, fim) if linhas[i].strip().startswith("|")),
              default=None)
    if ult is None:
        return texto
    hoje = datetime.date.today().strftime("%d/%m/%Y")
    linhas.insert(ult + 1, f"| {hoje} | Sync DET (extensão) | {detalhe} |\n")
    return "".join(linhas)


# ── Orquestração ─────────────────────────────────────────────────────────────

def identificadores(texto: str, pasta: str) -> tuple[str, str]:
    """(cnpj_ou_cpf, ri) da OS — front-matter, corpo ou nome da pasta."""
    m = RE_FM.match(texto)
    fm = m.group(1) if m else ""

    def campo(chave: str) -> str:
        c = re.search(rf"^{chave}\s*:\s*(.+?)\s*$", fm, re.MULTILINE)
        if not c:
            return ""
        v = c.group(1).strip().strip('"').strip("'")
        return "" if v in ("null", "~") else v

    cnpj = re.sub(r"\D", "", campo("cnpj"))
    if not cnpj:
        m2 = re.search(r"(\d{11,14})\s*$", pasta)
        cnpj = m2.group(1) if m2 else ""
    # `ri:` cru (pode ter mais de um RI, separados por vírgula) — quem extrai
    # os RIs individuais é ris_da_os().
    return cnpj, campo("ri")


def sincronizar_os(pasta_os: Path, token: str,
                   consultar=consultar_det) -> dict:
    """Sincroniza uma OS. `consultar` é injetável para testes."""
    r = {"os": pasta_os.name, "recebidas": 0, "inseridas": 0,
         "prazos_atualizados": 0, "detalhes_atualizados": 0,
         "ri_preenchido": False, "ignoradas": [], "erro": None}
    mem = pasta_os / "memory.md"
    try:
        texto = mem.read_text(encoding="utf-8")
    except OSError as e:
        r["erro"] = f"memory.md ilegível: {e}"
        return r
    cnpj, ri_fm = identificadores(texto, pasta_os.name)
    conhecidos = ris_da_os(ri_fm)
    if not cnpj and not conhecidos:
        r["erro"] = "sem CNPJ/CPF nem RI — pulada"
        return r
    try:
        notifs = elegiveis(consultar(token, cnpj,
                                     sorted(conhecidos)[0] if conhecidos else ""))
    except RuntimeError as e:
        r["erro"] = str(e)
        return r
    r["recebidas"] = len(notifs)
    if not notifs:
        return r

    # Só entram notificações da(s) fiscalização(ões) DESTA OS — o `ri:` do
    # front-matter é o identificador canônico (ver bloco "Vínculo notificação × OS").
    ri_novo = ""
    if not conhecidos:
        # OS ainda sem `ri:`: adota o da notificação mais recente e grava.
        ri_novo = ri_mais_recente(notifs)
        if ri_novo:
            conhecidos = {ri_novo}
    if not conhecidos:
        r["erro"] = ("não foi possível determinar o RI desta OS — nada importado. "
                     "Preencha `ri:` no memory.md e sincronize de novo.")
        return r

    minhas, alheias = [], []
    for n in notifs:
        (minhas if re.sub(r"\D", "", n.get("ri") or "") in conhecidos
         else alheias).append(n)
    # Nunca descartadas em silêncio: voltam no relatório para o AFT decidir.
    r["ignoradas"] = [{"codigo": n.get("codigo"),
                       "ri": re.sub(r"\D", "", n.get("ri") or ""),
                       "situacao": n.get("situacaoRi"),
                       "lavrada": (n.get("dataEnvio") or "")[:10]}
                      for n in alheias]
    if not minhas:
        return r

    (novo, r["inseridas"], r["prazos_atualizados"],
     r["detalhes_atualizados"]) = aplicar_notificacoes(texto, minhas)
    novo, r["ri_preenchido"] = preencher_ri(novo, ri_novo)
    if novo == texto:
        return r

    partes = []
    if r["inseridas"]:
        partes.append(f"{r['inseridas']} notificação(ões) importada(s)")
    if r["prazos_atualizados"]:
        partes.append(f"{r['prazos_atualizados']} prazo(s) atualizado(s)")
    if r["detalhes_atualizados"]:
        partes.append(f"{r['detalhes_atualizados']} detalhe(s) atualizado(s)")
    if r["ri_preenchido"]:
        partes.append(f"RI {ri_novo} preenchido (notificação mais recente)")
    novo = registrar_atividade(novo, " · ".join(partes) or "sem mudanças")

    import os
    if os.environ.get("AFT_DET_DRYRUN"):
        r["dry_run"] = True  # nada é gravado (modo de inspeção)
        return r

    if BACKUP.exists():
        subprocess.run([sys.executable, str(BACKUP), str(mem)],
                       capture_output=True, timeout=30)
    mem.write_text(novo, encoding="utf-8")
    return r


def sincronizar_todas(base: Path, token: str, consultar=consultar_det) -> dict:
    """Sincroniza todas as OS de OS ATIVAS/. Uma OS com erro não derruba as
    demais. Devolve métricas agregadas (mesmo espírito do SisOS)."""
    resultados = [sincronizar_os(mem.parent, token, consultar)
                  for mem in sorted(base.glob("*/memory.md"))]
    erros = [{"os": r["os"], "erro": r["erro"]} for r in resultados if r["erro"]]
    ignoradas = [{"os": r["os"], **ig} for r in resultados for ig in r["ignoradas"]]
    return {
        "ok": True,
        "os_verificadas": len(resultados),
        "notificacoes_recebidas": sum(r["recebidas"] for r in resultados),
        "inseridas": sum(r["inseridas"] for r in resultados),
        "prazos_atualizados": sum(r["prazos_atualizados"] for r in resultados),
        "detalhes_atualizados": sum(r["detalhes_atualizados"] for r in resultados),
        "ris_preenchidos": sum(1 for r in resultados if r["ri_preenchido"]),
        # De outra fiscalização do mesmo empregador — não importadas, relatadas.
        "ignoradas": len(ignoradas),
        "ignoradas_detalhe": ignoradas or None,
        "erros": erros or None,
    }


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("uso: python det_sync.py <PASTA_OS_ATIVAS> <token>", file=sys.stderr)
        sys.exit(1)
    print(json.dumps(sincronizar_todas(Path(sys.argv[1]), sys.argv[2]),
                     ensure_ascii=False, indent=2))
