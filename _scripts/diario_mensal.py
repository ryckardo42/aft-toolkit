# -*- coding: utf-8 -*-
"""
diario_mensal.py — consolida o DIÁRIO DE ATIVIDADES de um mês (skill /aft-diario).

Varre o `## Registro de atividades` de TODAS as OS — OS ATIVAS **e**
OS ARQUIVADAS (OS arquivada no meio do mês não pode sumir da agenda) — mais os
sidecars `.diario-auto.jsonl` do gancho automático, e monta:

  1. a AGENDA MENSAL: dia a dia, o que foi feito e em qual empresa, com a
     lista dos dias úteis SEM nenhum registro (os buracos a lembrar);
  2. POR AUDITORIA: as linhas prontas para transcrever na tela
     "2.1 Atividades" do RI (SFIT-WEB), com o texto oficial de cada opção.

Grava `<pasta AFT>/diario/diario-AAAA-MM.md` e imprime um resumo JSON no
stdout (a skill /aft-diario traduz para o AFT).

Uso:
    python diario_mensal.py [AAAA-MM] [PASTA_OS_ATIVAS]

  AAAA-MM          (opcional): mês a consolidar; padrão = mês corrente.
  PASTA_OS_ATIVAS  (opcional): padrão resolvido via pasta_aft.py.

Feriados: exclui sábados, domingos e os feriados nacionais fixos + Sexta-feira
Santa. Carnaval (seg/ter) e Corpus Christi entram como "possível não útil"
(ponto facultativo no serviço público federal) — o AFT decide; os dias
considerados aparecem no relatório para conferência.

Reaproveita o parser do painel (gerar_painel.parse_memory / coletar_diario):
uma única fonte de verdade para ler as fichas. Read-only sobre as OS.
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

import datetime
import json
import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gerar_painel as gp  # noqa: E402  (parser único das fichas)

# Texto OFICIAL das opções da tela 2.1 do RI, por letra do diário.
RI_OFICIAL = {
    "A": ["Preparação/planejamento da fiscalização"],
    "B": ["Início da Fiscalização"],
    "C": ["Inspeção do ambiente de trabalho",
          "Auditoria e análise de documentos (físicos ou digitais) no "
          "estabelecimento do empregador",
          "Entrevista com empregados da empresa no estabelecimento do "
          "empregador"],
    "D": ["Auditoria e análise de documentos (físicos ou digitais) fora do "
          "estabelecimento do empregador"],
    "E": ["Lançamento de dados em sistemas",
          "Elaboração e/ou emissão de documentos"],
    "F": ["Fim da Fiscalização"],
}

DOW = ["seg", "ter", "qua", "qui", "sex", "sáb", "dom"]
MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho",
         "agosto", "setembro", "outubro", "novembro", "dezembro"]


def pascoa(ano: int) -> datetime.date:
    """Domingo de Páscoa (algoritmo de Meeus/Jones/Butcher, gregoriano)."""
    a = ano % 19
    b, c = divmod(ano, 100)
    d, e = divmod(b, 4)
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = divmod(c, 4)
    m = (32 + 2 * e + 2 * i - h - k) % 7
    n = (a + 11 * h + 22 * m) // 451
    mes, dia = divmod(h + m - 7 * n + 114, 31)
    return datetime.date(ano, mes, dia + 1)


def feriados(ano: int) -> tuple[dict[datetime.date, str], dict[datetime.date, str]]:
    """(feriados nacionais, possíveis não úteis/ponto facultativo)."""
    fixos = {
        datetime.date(ano, 1, 1): "Confraternização Universal",
        datetime.date(ano, 4, 21): "Tiradentes",
        datetime.date(ano, 5, 1): "Dia do Trabalho",
        datetime.date(ano, 9, 7): "Independência",
        datetime.date(ano, 10, 12): "Nossa Senhora Aparecida",
        datetime.date(ano, 11, 2): "Finados",
        datetime.date(ano, 11, 15): "Proclamação da República",
        datetime.date(ano, 11, 20): "Dia da Consciência Negra",
        datetime.date(ano, 12, 25): "Natal",
    }
    p = pascoa(ano)
    fixos[p - datetime.timedelta(days=2)] = "Sexta-feira Santa"
    facultativos = {
        p - datetime.timedelta(days=48): "Carnaval (segunda)",
        p - datetime.timedelta(days=47): "Carnaval (terça)",
        p + datetime.timedelta(days=60): "Corpus Christi",
    }
    return fixos, facultativos


def mes_pedido() -> tuple[int, int]:
    for a in sys.argv[1:]:
        m = re.fullmatch(r"(\d{4})-(\d{2})", a.strip())
        if m:
            return int(m.group(1)), int(m.group(2))
    hoje = datetime.date.today()
    return hoje.year, hoje.month


def base_os() -> Path:
    for a in sys.argv[1:]:
        a = a.strip()
        if a and not re.fullmatch(r"\d{4}-\d{2}", a) and not a.startswith("--"):
            return Path(a)
    try:
        from pasta_aft import pasta_os_ativas
        return pasta_os_ativas()
    except Exception:
        return Path.home() / "Documents" / "AFT" / "OS ATIVAS"


def br(d: datetime.date) -> str:
    return d.strftime("%d/%m/%Y")


def agrupar_ri(entradas: list[dict]) -> list[dict]:
    """Por OS: linhas (data → letras → textos oficiais) para a tela do RI.
    Entradas automáticas (sem letra) ficam de fora — não dá para transcrever
    o que não foi classificado; elas aparecem na agenda como pendência."""
    por_os: dict[str, dict] = {}
    for e in entradas:
        if not e["t"]:
            continue
        o = por_os.setdefault(e["emp"], {"emp": e["emp"], "ri": e.get("ri") or "",
                                         "arquivada": e.get("arq", False),
                                         "por_dia": {}})
        o["por_dia"].setdefault(e["d"], set()).update(e["t"])
    out = []
    for emp in sorted(por_os, key=str.lower):
        o = por_os[emp]
        linhas = []
        for d_iso in sorted(o["por_dia"]):
            letras = "".join(sorted(o["por_dia"][d_iso]))
            textos = []
            for l in letras:
                textos += RI_OFICIAL.get(l, [])
            linhas.append({"data": br(datetime.date.fromisoformat(d_iso)),
                           "letras": letras, "texto_ri": " | ".join(textos)})
        out.append({"emp": emp, "ri": o["ri"], "arquivada": o["arquivada"],
                    "linhas": linhas})
    return out


def montar_md(ano: int, mes: int, agenda: list[dict], vagos: list[dict],
              por_os: list[dict], fer_mes: dict, fac_mes: dict,
              dias_trab: int) -> str:
    hoje = datetime.date.today()
    L = [f"# Diário de atividades — {MESES[mes - 1]}/{ano}", ""]
    L.append(f"_(gerado em {br(hoje)} pela /aft-diario, a partir do Registro de "
             "atividades das OS — ATIVAS e ARQUIVADAS — e das anotações "
             "automáticas do gancho; regenerável a qualquer momento)_")
    L += ["", f"**Dias com trabalho registrado no mês: {dias_trab}**", ""]
    if fer_mes:
        L.append("Feriados considerados: " + " · ".join(
            f"{br(d)} ({n})" for d, n in sorted(fer_mes.items())))
    if fac_mes:
        L.append("Possíveis não úteis (ponto facultativo — o AFT decide): "
                 + " · ".join(f"{br(d)} ({n})" for d, n in sorted(fac_mes.items())))
    if fer_mes or fac_mes:
        L.append("")

    L += ["## Agenda do mês", "",
          "| Dia | Semana | Empresas e atividades |",
          "|-----|--------|----------------------|"]
    for dia in agenda:
        if not dia["itens"] and dia["util"]:
            L.append(f"| {dia['dia']:02d} | {dia['dow']} | — |")
            continue
        if not dia["itens"]:
            continue  # fim de semana/feriado sem trabalho: fora da agenda
        por_emp: dict[str, set] = {}
        auto_emp: set = set()
        for e in dia["itens"]:
            por_emp.setdefault(e["emp"], set()).update(e["t"])
            if e["auto"] and not e["t"]:
                auto_emp.add(e["emp"])
        partes = []
        for emp in sorted(por_emp, key=str.lower):
            letras = "".join(sorted(por_emp[emp]))
            rot = f"**{emp}**"
            if letras:
                rot += f" [{letras}]"
            elif emp in auto_emp:
                rot += " _(anotado sozinho, sem classificação)_"
            partes.append(rot)
        rotulo_dia = f"{dia['dia']:02d}"
        if not dia["util"]:
            rotulo_dia += " (*)"
        L.append(f"| {rotulo_dia} | {dia['dow']} | {' · '.join(partes)} |")
    L += ["", "_(*) = fim de semana, feriado ou ponto facultativo com trabalho "
          "registrado._", ""]

    L.append("## Dias úteis sem registro")
    L.append("")
    if vagos:
        L.append("Confira antes de fechar o mês — trabalho administrativo, "
                 "curso, férias ou dia a completar no diário:")
        L.append("")
        for v in vagos:
            L.append(f"- {v['dia']:02d}/{mes:02d} ({v['dow']})")
    else:
        L.append("Nenhum — todos os dias úteis do mês têm registro. ✅")
    L.append("")

    L += ["## Por auditoria — pronto para a tela 2.1 Atividades do RI", ""]
    if not por_os:
        L.append("_Nenhuma atividade classificada no mês._")
    for o in por_os:
        titulo = f"### {o['emp']}"
        extras = []
        if o["ri"]:
            extras.append(f"RI {o['ri']}")
        if o["arquivada"]:
            extras.append("OS arquivada")
        if extras:
            titulo += f" _({' · '.join(extras)})_"
        L += [titulo, "",
              "| Data | Letras | Atividade (texto do RI) |",
              "|------|--------|--------------------------|"]
        for lin in o["linhas"]:
            # O separador oficial do RI é "|": escapado para não quebrar a
            # célula da tabela markdown.
            texto = lin["texto_ri"].replace("|", "\\|")
            L.append(f"| {lin['data']} | {lin['letras']} | {texto} |")
        L.append("")
    L.append("_Marque 'Não incluir sábados, domingos e feriados nacionais' na "
             "tela do RI conforme o caso; a Competência para Aferição do RI é "
             "decisão do AFT._")
    return "\n".join(L) + "\n"


def main() -> int:
    ano, mes = mes_pedido()
    base = base_os()
    if not base.exists():
        print(json.dumps({"ok": False, "erro": f"pasta não existe: {base}"},
                         ensure_ascii=False))
        return 1

    hoje = datetime.date.today()
    oss = []
    for mem in sorted(base.glob("*/memory.md")):
        try:
            oss.append(gp.parse_memory(mem))
        except Exception:
            continue  # ficha ruim não derruba o consolidado
    todas = gp.coletar_diario(oss, base, hoje)
    chave = f"{ano:04d}-{mes:02d}"
    entradas = [e for e in todas if e["d"][:7] == chave]

    fer, fac = feriados(ano)
    fer_mes = {d: n for d, n in fer.items() if d.month == mes and d.year == ano}
    fac_mes = {d: n for d, n in fac.items() if d.month == mes and d.year == ano}

    n_dias = (datetime.date(ano + (mes == 12), (mes % 12) + 1, 1)
              - datetime.date(ano, mes, 1)).days
    por_dia: dict[str, list] = {}
    for e in entradas:
        por_dia.setdefault(e["d"], []).append(e)

    agenda, vagos = [], []
    for dia in range(1, n_dias + 1):
        d = datetime.date(ano, mes, dia)
        util = d.weekday() < 5 and d not in fer_mes and d not in fac_mes
        itens = por_dia.get(d.isoformat(), [])
        agenda.append({"dia": dia, "dow": DOW[d.weekday()], "util": util,
                       "itens": itens})
        if util and not itens and d <= hoje:
            vagos.append({"dia": dia, "dow": DOW[d.weekday()]})

    por_os = agrupar_ri(entradas)
    dias_trab = len(por_dia)

    md = montar_md(ano, mes, agenda, vagos, por_os, fer_mes, fac_mes, dias_trab)
    destino = base.parent / "diario" / f"diario-{chave}.md"
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(md, encoding="utf-8")

    print(json.dumps({
        "ok": True,
        "mes": chave,
        "arquivo": str(destino),
        "dias_trabalhados": dias_trab,
        "dias_uteis_sem_registro": [f"{v['dia']:02d}/{mes:02d} ({v['dow']})"
                                    for v in vagos],
        "feriados_no_mes": [f"{br(d)} {n}" for d, n in sorted(fer_mes.items())],
        "possiveis_nao_uteis": [f"{br(d)} {n}" for d, n in sorted(fac_mes.items())],
        "empresas_no_mes": [{"emp": o["emp"], "ri": o["ri"],
                             "dias_classificados": len(o["linhas"]),
                             "arquivada": o["arquivada"]} for o in por_os],
        "entradas_sem_classificacao": sum(1 for e in entradas
                                          if e["auto"] and not e["t"]),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
