#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
lre_folha.py — AFT Toolkit
Cruza o LRE (vinculos, grupo idA) com as bases de FGTS da folha (grupo idM)
e os afastamentos (grupo idK) que o SISFGTS baixa do eSocial e audita a
REMUNERACAO declarada de cada vinculo, mes a mes.

O que aponta (sempre como INDICIO, nunca prova):

1. BURACOS NA FOLHA - mes dentro do vinculo sem NENHUMA base de remuneracao
   mensal declarada (tpValor 11) e sem afastamento que o justifique. Pode ser
   fraude, trabalho sem registro de remuneracao ou afastamento nao declarado.
2. 13o SEM BASE - ano trabalhado sem nenhuma base de 13o salario (tpValor 12).
3. REMUNERACAO ABAIXO DO CONTRATUAL - os ultimos 3 meses fechados abaixo de
   90% do salario contratual do LRE. So compara o presente com o presente:
   comparar meses antigos com o salario ATUAL do LRE acusaria falsamente
   qualquer trabalhador que ja recebeu aumento.
4. DESLIGADO SEM BASE RESCISORIA - dispensa sem justa causa ou rescisao
   antecipada pelo empregador (mtvdeslig 02/03) sem nenhuma base rescisoria
   de FGTS (tpValor 21/22).

IMPORTANTE: o arquivo traz a base DECLARADA de FGTS, nao o recolhimento.
Quem aponta FGTS em atraso e o proprio SISFGTS - esta analise olha a
remuneracao e o vinculo, nao o debito.

Grava, dentro da pasta da OS:

  eSocial/Folha_painel.html   painel interativo por trabalhador (grade mensal)
  eSocial/Folha_analise.csv   um vinculo por linha, com os meses furados
  eSocial/folha.md            resumo SEM nome e SEM CPF (para o /aft-painel)
  eSocial/folha_resumo.json   numeros agregados (sem PII)

Tudo local: nenhuma chamada de rede, nenhuma dependencia externa.
O HTML e autocontido (CSS/JS embutidos, sem CDN) e contem DADOS PESSOAIS.

Uso:
  python lre_folha.py "<pasta da OS>" <CNPJ14> ["<EMPREGADOR>"] [--sisfgts "<base>"]

Significado dos tipos de base (tpValor do S-5003), conferido empiricamente:
11 = remuneracao mensal; 12 = 13o salario (anual "AAAA" ou parcela mensal);
21/22 = bases rescisorias (so aparecem em desligados; nas dispensas sem justa
causa deste conjunto de teste, 61 de 62 as tinham; pedidos de demissao e justa
causa, nenhuma). Tipos 13/14 existem mas nao tem leiaute confirmado - ficam
visiveis no detalhe como "outras bases", sem juizo.
"""
import csv
import json
import re
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from lre_esocial import (achar_sisfgts, achar_partes_grupo, ler_partes,
                         d_iso, fmt_d, fmt_cpf_mascarado, fmt_cnpj, fmt_identificador, MTV, UNID)

TP_MENSAL = 11
TP_13 = 12
TP_RESCISAO = (21, 22)
LIMIAR_CONTRATUAL = 0.90    # abaixo de 90% do salario contratual
MESES_RECENTES = 3          # quantos meses fechados comparar com o contratual
DIAS_AFASTADO_MES = 20      # afastamento cobre o mes se >= 20 dias dele
COD_FERIAS = "15"           # ferias sao remuneradas: nao justificam buraco
MTV_EXIGE_RESCISORIA = ("02", "03")


def ym(dt):
    return f"{dt.year:04d}-{dt.month:02d}"


def ym_add(s, n):
    y, m = int(s[:4]), int(s[5:7])
    y, m = y + (m - 1 + n) // 12, (m - 1 + n) % 12 + 1
    return f"{y:04d}-{m:02d}"


def ym_range(a, b):
    """Meses de a ate b, inclusive."""
    out, s = [], a
    while s <= b:
        out.append(s)
        s = ym_add(s, 1)
    return out


def dias_no_mes(s_ym, ini, fim):
    """Quantos dias do mes s_ym o intervalo [ini, fim] cobre."""
    y, m = int(s_ym[:4]), int(s_ym[5:7])
    from calendar import monthrange
    m_ini, m_fim = date(y, m, 1), date(y, m, monthrange(y, m)[1])
    a, b = max(ini, m_ini), min(fim, m_fim)
    return (b - a).days + 1 if a <= b else 0


def f_val(s):
    try:
        return float(s)
    except (TypeError, ValueError):
        return 0.0


def auditar_vinculo(v, bases, afasts, jan_ini, jan_fim, hoje):
    dtadm, dtdes = d_iso(v.get("dtadm")), d_iso(v.get("dtdeslig"))
    if not dtadm:
        return None
    # Vinculo que veio por sucessao/cessao: a folha NESTE CNPJ so comeca na
    # transferencia (sucessaovinc_dttransf) -- os meses anteriores foram
    # declarados pelo empregador de origem e nao sao buraco.
    transf = d_iso(v.get("sucessaovinc_dttransf"))
    ini = max(ym(transf) if transf else ym(dtadm), ym(dtadm), jan_ini)
    fim = min(ym(dtdes), jan_fim) if dtdes else jan_fim
    if ini > fim:
        return None   # vinculo fora da janela da folha

    mensal, tredec, outras = {}, {}, []
    for r in bases:
        tv, p = r.get("tpValor"), r.get("perapur") or ""
        val = f_val(r.get("remFGTS"))
        if tv == TP_MENSAL and len(p) == 7:
            mensal[p] = mensal.get(p, 0.0) + val
        elif tv == TP_13 and p:
            tredec[p[:4]] = tredec.get(p[:4], 0.0) + val
        else:
            outras.append({"tp": tv, "per": p, "val": val})

    afast_dias = {}   # mes -> dias afastado (qualquer codigo, exceto ferias)
    for r in afasts:
        if r.get("codmotafast") == COD_FERIAS:
            continue
        a_i = d_iso(r.get("dtiniafast"))
        if not a_i:
            continue
        a_t = d_iso(r.get("dttermafast")) or hoje
        s = ym(a_i)
        while s <= ym(a_t):
            afast_dias[s] = afast_dias.get(s, 0) + dias_no_mes(s, a_i, a_t)
            s = ym_add(s, 1)

    meses = ym_range(ini, fim)
    grade, buracos, afastados = {}, [], []
    for s in meses:
        if s in mensal:
            grade[s] = round(mensal[s], 2)
        elif afast_dias.get(s, 0) >= DIAS_AFASTADO_MES:
            grade[s] = "A"
            afastados.append(s)
        elif dtdes and s == ym(dtdes):
            grade[s] = "D"   # mes do desligamento: verbas vao para a rescisao
        else:
            grade[s] = "B"
            buracos.append(s)

    # 13o: ano fechado, com pelo menos 3 meses de base mensal, sem
    # desligamento naquele ano (13o de desligado vai para a rescisao)
    anos_sem_13 = []
    for ano in sorted({s[:4] for s in meses}):
        if int(ano) >= hoje.year:
            continue
        if dtdes and str(dtdes.year) == ano:
            continue
        n_meses = sum(1 for s in meses if s[:4] == ano and s in mensal)
        if n_meses >= 3 and ano not in tredec:
            anos_sem_13.append(ano)

    # ultimos meses fechados vs salario contratual (so salario mensal e ativo)
    sal = f_val(v.get("vrsalfx"))
    abaixo = []
    if not dtdes and v.get("undsalfixo") == 5 and sal > 0:
        recentes = [s for s in meses[-MESES_RECENTES:] if s in mensal]
        if len(recentes) == MESES_RECENTES and all(
                mensal[s] < sal * LIMIAR_CONTRATUAL for s in recentes):
            abaixo = recentes

    # base rescisoria nas dispensas por iniciativa do empregador
    sem_rescisoria = False
    if dtdes and v.get("mtvdeslig") in MTV_EXIGE_RESCISORIA and ym(dtdes) >= jan_ini:
        sem_rescisoria = not any(r.get("tpValor") in TP_RESCISAO for r in bases)

    com_base = [mensal[s] for s in meses if s in mensal]
    return {"mat": v.get("matricula", ""), "nome": v.get("nmtrab", ""),
            "cpf": fmt_cpf_mascarado(v.get("cpftrab")), "adm": dtadm, "des": dtdes,
            "ativo": not dtdes, "mtv": v.get("mtvdeslig"),
            "sal": sal, "unid": v.get("undsalfixo"),
            "ini": ini, "fim": fim, "meses": len(meses),
            "com_base": len(com_base),
            "media": round(sum(com_base) / len(com_base), 2) if com_base else 0,
            "grade": grade, "buracos": buracos, "afastados": afastados,
            "anos_sem_13": anos_sem_13, "tredec": tredec, "abaixo": abaixo,
            "sem_rescisoria": sem_rescisoria, "outras": outras}


def auditar(lre, folha, afast, hoje):
    pers = sorted(p for p in {r.get("perapur") or "" for r in folha
                              if r.get("tpValor") == TP_MENSAL} if len(p) == 7)
    if not pers:
        raise ValueError("A folha (idM) foi lida mas nao ha bases mensais "
                         "(tpValor 11).")
    jan_ini, jan_fim = pers[0], pers[-1]
    b_por, a_por = {}, {}
    for r in folha:
        b_por.setdefault((r.get("cpftrab"), r.get("matricula")), []).append(r)
    for r in afast:
        a_por.setdefault((r.get("cpftrab"), r.get("matricula")), []).append(r)
    trabs = []
    for v in lre:
        k = (v.get("cpftrab"), v.get("matricula"))
        t = auditar_vinculo(v, b_por.get(k, []), a_por.get(k, []),
                            jan_ini, jan_fim, hoje)
        if t:
            trabs.append(t)
    return jan_ini, jan_fim, trabs


# ------------------------------------------------------------------- saidas
def fmt_ym(s):
    return f"{s[5:7]}/{s[:4]}" if len(s) == 7 else s


def fmt_moeda(x):
    return f"{x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def montar_linhas(trabs):
    out = []
    for t in trabs:
        anos = sorted({s[:4] for s in ym_range(t["ini"], t["fim"])})
        grade = []
        for ano in anos:
            cels = []
            for m in range(1, 13):
                s = f"{ano}-{m:02d}"
                if s < t["ini"] or s > t["fim"]:
                    cels.append(None)
                else:
                    cels.append(t["grade"][s])
            grade.append({"ano": ano, "m": cels,
                          "t13": round(t["tredec"].get(ano, 0), 2) or None})
        out.append({
            "mat": t["mat"], "nome": t["nome"], "cpf": t["cpf"],
            "adm": fmt_d(t["adm"]), "des": fmt_d(t["des"]), "ativo": t["ativo"],
            "mtv": (MTV.get(t["mtv"], t["mtv"]) if t["mtv"] else ""),
            "sal": t["sal"], "salF": fmt_moeda(t["sal"]),
            "unid": UNID.get(t["unid"], ""),
            "media": t["media"], "mediaF": fmt_moeda(t["media"]),
            "meses": t["meses"], "comBase": t["com_base"],
            "nBuracos": len(t["buracos"]),
            "buracos": [fmt_ym(s) for s in t["buracos"]],
            "nAfast": len(t["afastados"]),
            "sem13": t["anos_sem_13"],
            "abaixo": [f"{fmt_ym(s)}" for s in t["abaixo"]],
            "semResc": t["sem_rescisoria"],
            "outras": [{"tp": o["tp"], "per": fmt_ym(o["per"]),
                        "val": fmt_moeda(o["val"])} for o in t["outras"]],
            "grade": grade,
        })
    out.sort(key=lambda x: (-x["nBuracos"], -len(x["sem13"]), x["nome"]))
    return out


def gravar_csv(destino, trabs):
    cols = ["MATRICULA", "NOME", "CPF", "SITUACAO", "ADMISSAO", "DESLIGAMENTO",
            "SALARIO_CONTRATUAL", "MEDIA_BASE_MENSAL", "MESES_NO_PERIODO",
            "MESES_COM_BASE", "MESES_AFASTADO", "BURACOS", "BURACOS_MESES",
            "ANOS_SEM_13", "RECENTES_ABAIXO_CONTRATUAL", "SEM_BASE_RESCISORIA"]
    with open(destino, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(cols)
        for t in trabs:
            w.writerow([
                t["mat"], t["nome"], t["cpf"],
                "ativo" if t["ativo"] else "desligado",
                fmt_d(t["adm"]), fmt_d(t["des"]),
                str(t["sal"]).replace(".", ","),
                str(t["media"]).replace(".", ","),
                t["meses"], t["com_base"], len(t["afastados"]),
                len(t["buracos"]),
                " | ".join(fmt_ym(s) for s in t["buracos"]),
                " | ".join(t["anos_sem_13"]),
                " | ".join(fmt_ym(s) for s in t["abaixo"]),
                "S" if t["sem_rescisoria"] else "N"])


def agregar(trabs, jan_ini, jan_fim, hoje):
    cb = [t for t in trabs if t["buracos"]]
    s13 = [t for t in trabs if t["anos_sem_13"]]
    ab = [t for t in trabs if t["abaixo"]]
    sr = [t for t in trabs if t["sem_rescisoria"]]
    return {
        "janela": f"{fmt_ym(jan_ini)} a {fmt_ym(jan_fim)}",
        "hoje": fmt_d(hoje), "vinculos": len(trabs),
        "trab_buracos": len(cb),
        "meses_buraco": sum(len(t["buracos"]) for t in trabs),
        "trab_sem_13": len(s13),
        "anos_sem_13": sum(len(t["anos_sem_13"]) for t in trabs),
        "trab_abaixo": len(ab),
        "trab_sem_rescisoria": len(sr),
    }


def gravar_md(destino, meta, ag):
    """Resumo em markdown SEM nome e SEM CPF (aparece no /aft-painel)."""
    L = []
    L.append("# Folha - auditoria da remuneração pelo eSocial (LRE + bases de FGTS)\n")
    L.append(f"- **Estabelecimento:** {meta['cnpj']}")
    L.append(f"- **Fonte:** SISFGTS, grupos `idA_LRE`, `idM_FOLHA` e `idK_AFAST`")
    L.append(f"- **Extraído em:** {meta['gerado']} · **folha disponível:** {ag['janela']}")
    L.append(f"- **Painel:** [Folha_painel.html](Folha_painel.html) "
             f"· **Planilha:** [Folha_analise.csv](Folha_analise.csv)\n")
    L.append("## Quadro geral\n")
    L.append("| Indicador | Valor |")
    L.append("|---|---|")
    L.append(f"| Vínculos com folha no período | {ag['vinculos']} |")
    L.append(f"| **Trabalhadores com buraco na folha** (mês sem base e sem afastamento) | **{ag['trab_buracos']}** |")
    L.append(f"| &nbsp;&nbsp;· meses furados no total | {ag['meses_buraco']} |")
    L.append(f"| **Trabalhadores com ano sem base de 13º** | **{ag['trab_sem_13']}** ({ag['anos_sem_13']} ano(s)) |")
    L.append(f"| Ativos com os últimos {MESES_RECENTES} meses abaixo de "
             f"{int(LIMIAR_CONTRATUAL*100)}% do salário contratual | {ag['trab_abaixo']} |")
    L.append(f"| Dispensados pelo empregador sem base rescisória de FGTS | {ag['trab_sem_rescisoria']} |")
    L.append("")
    L.append("## Como o indício é apurado\n")
    L.append(f"> Base mensal declarada de FGTS (tpValor 11 do S-5003) de cada vínculo, "
             f"mês a mês, no período em que há folha baixada ({ag['janela']}). Mês sem base "
             f"só vira buraco se nenhum afastamento cobrir 20 dias ou mais dele (férias não "
             f"justificam buraco: são remuneradas). O 13º é cobrado por ano fechado com pelo "
             f"menos 3 meses de base e sem desligamento no ano. A comparação com o salário "
             f"contratual olha só os últimos {MESES_RECENTES} meses fechados — comparar meses antigos "
             f"com o salário atual do LRE acusaria falsamente quem já teve aumento.\n>\n"
             f"> **O arquivo traz a base declarada, não o recolhimento** — quem aponta FGTS "
             f"em atraso é o próprio SISFGTS. **É indício, não prova**: confirmar na folha de "
             f"pagamento e nos recibos antes de autuar; ementa e capitulação pelo `/aft-consulta`.\n")
    L.append("---\n")
    L.append("_Gerado pela `/aft-lre-esocial` a partir dos arquivos do SISFGTS. "
             "Os dados nominais estão no painel e no CSV desta mesma pasta: "
             "arquivos locais com dados pessoais — não publicar._")
    destino.write_text("\n".join(L), encoding="utf-8")


HTML = r"""<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Folha eSocial - __EMPREGADOR__</title>
<style>
:root{--bg:#f5f6f8;--card:#fff;--tx:#1c2430;--mut:#6b7684;--bd:#dfe3e8;
 --ac:#1f4e79;--ac2:#e8eef5;--warn:#b3261e;--warnbg:#fdeceb;--ok:#1b6b3a;--okbg:#e8f4ec;
 --amb:#8a6d00;--ambbg:#fdf4d7;}
@media (prefers-color-scheme:dark){:root{--bg:#14181d;--card:#1c2229;--tx:#e6eaef;
 --mut:#98a3b0;--bd:#2d353f;--ac:#6ea8dc;--ac2:#23303d;--warn:#f2837a;
 --warnbg:#37211f;--ok:#7fc79b;--okbg:#1c2b22;--amb:#e5c766;--ambbg:#332b12;}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--tx);
 font:14px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif}
.wrap{max-width:1400px;margin:0 auto;padding:20px}
header h1{margin:0 0 4px;font-size:20px}
header .sub{color:var(--mut);font-size:13px}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin:18px 0}
.card{background:var(--card);border:1px solid var(--bd);border-radius:10px;padding:14px}
.card .n{font-size:26px;font-weight:600;line-height:1.1}
.card .l{color:var(--mut);font-size:12px;margin-top:4px}
.card.w .n{color:var(--warn)}.card.g .n{color:var(--ok)}.card.a .n{color:var(--amb)}
.bar{background:var(--card);border:1px solid var(--bd);border-radius:10px;padding:12px;
 margin-bottom:14px;display:flex;gap:10px;flex-wrap:wrap;align-items:center}
#q{flex:1;min-width:170px;max-width:340px;padding:10px 12px;border:1px solid var(--bd);border-radius:8px;
 background:var(--bg);color:var(--tx);font-size:14px}
#q:focus{outline:2px solid var(--ac);outline-offset:-1px}
.chip{padding:7px 13px;border:1px solid var(--bd);border-radius:20px;background:var(--bg);
 color:var(--tx);cursor:pointer;font-size:13px}
.chip:hover{border-color:var(--ac)}
.chip.on{background:var(--ac);color:#fff;border-color:var(--ac)}
.cnt{color:var(--mut);font-size:13px;margin-left:auto}
.tw{background:var(--card);border:1px solid var(--bd);border-radius:10px;overflow:auto}
table{width:100%;border-collapse:collapse;font-size:13px}
th{position:sticky;top:0;background:var(--ac2);text-align:left;padding:10px;font-weight:600;
 cursor:pointer;white-space:nowrap;border-bottom:1px solid var(--bd)}
th:hover{color:var(--ac)}th .ar{opacity:.45;font-size:10px}
td{padding:9px 10px;border-bottom:1px solid var(--bd);vertical-align:top}
tr.r{cursor:pointer}tr.r:hover td{background:var(--ac2)}
tr.bur td:first-child{box-shadow:inset 3px 0 0 var(--warn)}
.tag{display:inline-block;padding:1px 7px;border-radius:10px;font-size:11px;font-weight:600}
.t-a{background:var(--okbg);color:var(--ok)}
.t-d{background:var(--bg);color:var(--mut);border:1px solid var(--bd)}
.t-w{background:var(--warnbg);color:var(--warn)}
.t-m{background:var(--ambbg);color:var(--amb)}
.nm{font-weight:600}.sm{color:var(--mut);font-size:11.5px}.nw{white-space:nowrap}
.det td{background:var(--bg);padding:14px}
.det table{font-size:11.5px;width:auto}.det th{position:static;cursor:default;padding:5px 7px}
.det td.c{padding:5px 7px;text-align:right;white-space:nowrap}
.c-b{background:var(--warnbg);color:var(--warn);font-weight:700;text-align:center!important}
.c-a{background:var(--ambbg);color:var(--amb);text-align:center!important}
.c-x{color:var(--mut);text-align:center!important}
.note{background:var(--warnbg);border:1px solid var(--warn);color:var(--warn);
 border-radius:8px;padding:11px 13px;margin:14px 0;font-size:12.5px}
.pg{display:flex;gap:6px;align-items:center;justify-content:center;padding:12px;flex-wrap:wrap}
.pg button{padding:6px 11px;border:1px solid var(--bd);border-radius:7px;background:var(--card);
 color:var(--tx);cursor:pointer;font-size:13px;min-width:36px}
.pg button:hover:not(:disabled){border-color:var(--ac);color:var(--ac)}
.pg button.on{background:var(--ac);color:#fff;border-color:var(--ac)}
.pg button:disabled{opacity:.35;cursor:default}
.pg .info{color:var(--mut);font-size:12.5px;margin:0 8px}
.foot{color:var(--mut);font-size:11.5px;margin:18px 0 40px;text-align:center}
.empty{padding:40px;text-align:center;color:var(--mut)}
mark{background:#ffe38a;color:#000;padding:0 1px;border-radius:2px}
@media (prefers-color-scheme:dark){mark{background:#7a6320;color:#fff}}
</style></head><body><div class="wrap">
<header><h1 id="hEmp"></h1>
<div class="sub">CNPJ <b id="mCnpj"></b> &middot; bases de FGTS da folha (eSocial via SISFGTS)
 &middot; extraído em <span id="mGer"></span> &middot; folha disponível: <b id="mJan"></b></div></header>
<div class="cards">
 <div class="card"><div class="n" id="cTot"></div><div class="l">Vínculos com folha no período</div></div>
 <div class="card w"><div class="n" id="cBur"></div><div class="l">Com buraco na folha<br><span id="cBurSub" style="font-size:11px"></span></div></div>
 <div class="card w"><div class="n" id="c13"></div><div class="l">Com ano sem base de 13º<br><span id="c13Sub" style="font-size:11px"></span></div></div>
 <div class="card a"><div class="n" id="cAb"></div><div class="l">Últimos meses abaixo do salário contratual</div></div>
 <div class="card a"><div class="n" id="cSr"></div><div class="l">Dispensados sem base rescisória de FGTS</div></div>
</div>
<div class="note"><b>É indício, não prova.</b> A grade mostra a base mensal de FGTS declarada
 (tpValor 11 do S-5003). Mês sem base só vira <b>buraco</b> se nenhum afastamento cobrir 20 dias
 ou mais dele (férias não justificam: são remuneradas). O 13º é cobrado por ano fechado com pelo
 menos 3 meses de base e sem desligamento no ano. A comparação com o salário contratual olha só os
 <b>últimos meses fechados</b> — meses antigos abaixo do salário atual do LRE são normais para quem
 recebeu aumento. <b>O arquivo traz a base declarada, não o recolhimento</b>: FGTS em atraso quem
 aponta é o próprio SISFGTS. Confirmar na folha de pagamento antes de autuar.</div>
<div class="bar">
 <input id="q" type="search" placeholder="Buscar por nome, CPF ou matrícula..." autocomplete="off">
 <button class="chip on" data-f="todos">Todos</button>
 <button class="chip" data-f="buracos">Com buraco</button>
 <button class="chip" data-f="sem13">Sem 13º</button>
 <button class="chip" data-f="abaixo">Abaixo do contratual</button>
 <button class="chip" data-f="semResc">Sem base rescisória</button>
 <button class="chip" data-f="regular">Sem indício</button>
 <span class="cnt" id="cnt"></span></div>
<div class="tw"><table><thead><tr>
 <th data-s="mat">Matríc. <span class="ar">&#9662;</span></th>
 <th data-s="nome">Nome <span class="ar">&#9662;</span></th>
 <th data-s="ativo">Situação <span class="ar">&#9662;</span></th>
 <th data-s="meses">Meses no período <span class="ar">&#9662;</span></th>
 <th data-s="nBuracos">Buracos <span class="ar">&#9662;</span></th>
 <th data-s="sal">Salário contratual <span class="ar">&#9662;</span></th>
 <th data-s="media">Média da base mensal <span class="ar">&#9662;</span></th>
</tr></thead><tbody id="tb"></tbody></table>
<div class="empty" id="empty" style="display:none">Nenhum trabalhador corresponde à busca.</div>
<div class="pg" id="pg"></div></div>
<div class="foot">Arquivo local com dados pessoais de trabalhadores.
 Não publicar, não anexar em e-mail, não enviar a serviços externos.</div>
</div>
<script>
const D=__DADOS__, M=__META__;
const MESES=['jan','fev','mar','abr','mai','jun','jul','ago','set','out','nov','dez'];
hEmp.textContent='Folha eSocial — '+M.empregador;
mCnpj.textContent=M.cnpj; mGer.textContent=M.gerado; mJan.textContent=M.janela;
cTot.textContent=M.vinculos; cBur.textContent=M.trabBuracos;
cBurSub.textContent=M.mesesBuraco+' mes(es) sem base e sem afastamento';
c13.textContent=M.trabSem13; c13Sub.textContent=M.anosSem13+' ano(s) no total';
cAb.textContent=M.trabAbaixo; cSr.textContent=M.trabSemResc;
function esc(s){return String(s??'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));}
let filtro='todos',termo='',ord='nBuracos',asc=false,pag=1,tam=50;
function norm(s){return String(s??'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();}
function hl(s,t){s=esc(s); if(!t)return s;
 const n=norm(s),q=norm(t); let i=n.indexOf(q); if(i<0)return s;
 return s.slice(0,i)+'<mark>'+s.slice(i,i+t.length)+'</mark>'+s.slice(i+t.length);}
function filtrar(){const t=norm(termo);
 return D.filter(x=>{
  if(filtro==='buracos'&&!x.nBuracos)return false;
  if(filtro==='sem13'&&!x.sem13.length)return false;
  if(filtro==='abaixo'&&!x.abaixo.length)return false;
  if(filtro==='semResc'&&!x.semResc)return false;
  if(filtro==='regular'&&(x.nBuracos||x.sem13.length||x.abaixo.length||x.semResc))return false;
  if(!t)return true;
  return norm(x.nome).includes(t)||norm(x.cpf).includes(t)||norm(x.mat).includes(t);
 }).sort((a,b)=>{let p=a[ord],q=b[ord];
  if(typeof p==='boolean'){p=p?1:0;q=q?1:0;}
  if(p==null)p=-1; if(q==null)q=-1;
  if(typeof p==='number'||typeof q==='number'){p=p||0;q=q||0;return asc?p-q:q-p;}
  return asc?String(p).localeCompare(String(q),'pt-BR'):String(q).localeCompare(String(p),'pt-BR');});}
function render(){
 const L=filtrar(), tot=L.length, np=Math.max(1,Math.ceil(tot/tam));
 if(pag>np)pag=np;
 const ini=(pag-1)*tam, fat=L.slice(ini,ini+tam);
 cnt.textContent = tot? `${ini+1}–${Math.min(ini+tam,tot)} de ${tot}`+(tot!==D.length?` (${D.length} no total)`:'') : `0 de ${D.length}`;
 empty.style.display=tot?'none':'block';
 tb.innerHTML=fat.map((x,i)=>{
  const sit=x.ativo?'<span class="tag t-a">ativo</span>':'<span class="tag t-d">desligado</span>';
  const badges=(x.nBuracos?` <span class="tag t-w">${x.nBuracos} buraco${x.nBuracos>1?'s':''}</span>`:'')+
    (x.sem13.length?' <span class="tag t-w">sem 13º</span>':'')+
    (x.abaixo.length?' <span class="tag t-m">abaixo do contratual</span>':'')+
    (x.semResc?' <span class="tag t-m">sem base rescisória</span>':'');
  return `<tr class="r${x.nBuracos?' bur':''}" data-i="${i}">
   <td>${esc(x.mat)}</td>
   <td><span class="nm">${hl(x.nome,termo)}</span><div class="sm">${esc(x.cpf)}</div></td>
   <td>${sit}${badges}</td>
   <td>${x.comBase} de ${x.meses} com base</td>
   <td>${x.nBuracos||'&mdash;'}</td>
   <td class="nw">${x.sal?'R$&nbsp;'+x.salF:'&mdash;'}<div class="sm">${esc(x.unid)}</div></td>
   <td class="nw">R$&nbsp;${x.mediaF}</td></tr>`;}).join('');
 tb.querySelectorAll('tr.r').forEach(tr=>tr.onclick=()=>detalhe(tr,fat[+tr.dataset.i]));
 paginar(np,tot);}
function paginar(np,tot){
 if(np<=1&&tot<=tam){pg.innerHTML=tot>20?opcTam():'';return;}
 let h=`<button ${pag===1?'disabled':''} data-p="1">&laquo;</button>`+
       `<button ${pag===1?'disabled':''} data-p="${pag-1}">&lsaquo;</button>`;
 const a=Math.max(1,pag-2), b=Math.min(np,pag+2);
 if(a>1)h+=`<span class="info">...</span>`;
 for(let i=a;i<=b;i++)h+=`<button class="${i===pag?'on':''}" data-p="${i}">${i}</button>`;
 if(b<np)h+=`<span class="info">...</span>`;
 h+=`<button ${pag===np?'disabled':''} data-p="${pag+1}">&rsaquo;</button>`+
    `<button ${pag===np?'disabled':''} data-p="${np}">&raquo;</button>`+
    `<span class="info">página ${pag} de ${np}</span>`+opcTam();
 pg.innerHTML=h;
 pg.querySelectorAll('button[data-p]').forEach(b2=>b2.onclick=()=>{
   pag=+b2.dataset.p; render(); document.querySelector('.tw').scrollIntoView({block:'start'});});
 const s=pg.querySelector('select'); if(s)s.onchange=()=>{tam=+s.value;pag=1;render();};}
function opcTam(){return `<select>${[25,50,100,250,500].map(n=>
  `<option value="${n}"${n===tam?' selected':''}>${n} por página</option>`).join('')}</select>`;}
function cel(v){
 if(v===null)return '<td class="c c-x">&middot;</td>';
 if(v==='B')return '<td class="c c-b" title="mês sem base e sem afastamento">SEM BASE</td>';
 if(v==='A')return '<td class="c c-a" title="afastamento cobre 20 dias ou mais do mês">afast.</td>';
 if(v==='D')return '<td class="c c-x" title="mês do desligamento: verbas na rescisão">deslig.</td>';
 return `<td class="c">${v.toLocaleString('pt-BR',{minimumFractionDigits:2})}</td>`;}
function detalhe(tr,x){
 const nx=tr.nextElementSibling;
 if(nx&&nx.classList.contains('det')){nx.remove();return;}
 tb.querySelectorAll('tr.det').forEach(e=>e.remove());
 const linhas=x.grade.map(g=>{
  const t13=g.t13?`<td class="c">${g.t13.toLocaleString('pt-BR',{minimumFractionDigits:2})}</td>`
    :(x.sem13.includes(g.ano)?'<td class="c c-b">SEM 13º</td>':'<td class="c c-x">&middot;</td>');
  return `<tr><td class="c"><b>${g.ano}</b></td>${g.m.map(cel).join('')}${t13}</tr>`;}).join('');
 const extra=[
  x.abaixo.length?`<div class="sm" style="margin-top:6px">Últimos meses abaixo de 90% do salário contratual: ${x.abaixo.map(esc).join(', ')}</div>`:'',
  x.semResc?`<div class="sm" style="margin-top:6px;color:var(--warn)">Desligamento por iniciativa do empregador (${esc(x.mtv)}) sem nenhuma base rescisória de FGTS (tpValor 21/22).</div>`:'',
  x.outras.length?`<div class="sm" style="margin-top:6px">Outras bases: ${x.outras.map(o=>`tp${o.tp} ${esc(o.per)} R$ ${o.val}`).join(' · ')}</div>`:''
 ].join('');
 const t2=document.createElement('tr'); t2.className='det';
 t2.innerHTML=`<td colspan="7">
  <div class="sm" style="margin-bottom:8px">Base mensal de FGTS declarada (R$), ${esc(x.adm)}${x.des?' a '+esc(x.des):''}${x.mtv?' · '+esc(x.mtv):''}</div>
  <table><thead><tr><th>Ano</th>${MESES.map(m=>'<th>'+m+'</th>').join('')}<th>13º</th></tr></thead>
  <tbody>${linhas}</tbody></table>${extra}</td>`;
 tr.after(t2);}
q.addEventListener('input',e=>{termo=e.target.value.trim();pag=1;render();});
document.querySelectorAll('.chip').forEach(b=>b.onclick=()=>{
 document.querySelectorAll('.chip').forEach(c=>c.classList.remove('on'));
 b.classList.add('on');filtro=b.dataset.f;pag=1;render();});
document.querySelectorAll('th[data-s]').forEach(th=>th.onclick=()=>{
 const s=th.dataset.s; asc=(ord===s)?!asc:false; ord=s; pag=1;
 document.querySelectorAll('th .ar').forEach(a=>a.innerHTML='&#9662;');
 th.querySelector('.ar').innerHTML=asc?'&#9652;':'&#9662;'; render();});
render();
</script></body></html>
"""


def gerar(pasta_os: Path, cnpj14: str, empregador: str = "",
          base_sisfgts=None, hoje=None) -> dict:
    hoje = hoje or date.today()
    base = achar_sisfgts(base_sisfgts)
    if not base:
        raise FileNotFoundError(
            "SISFGTS nao encontrado. No Windows esperamos "
            r"C:\SistemasAFT\SisFGTS; no Mac, o disco do Parallels montado "
            "em /Volumes/... Informe a base com --sisfgts se estiver noutro lugar.")
    if not achar_partes_grupo(base, cnpj14, "idA_LRE"):
        raise FileNotFoundError(
            f"Nenhum arquivo LRE para o CNPJ/CPF {cnpj14} em "
            f"{base / 'Arquivos' / 'eSocial' / cnpj14}. "
            "Baixe os dados do eSocial no SISFGTS antes.")
    if not achar_partes_grupo(base, cnpj14, "idM_FOLHA"):
        raise FileNotFoundError(
            f"O CNPJ/CPF {cnpj14} tem o LRE mas NAO tem folha (idM). "
            "No SISFGTS, baixe o eSocial com a opcao 'LRE e demais registros' "
            "- e ela que traz as bases de FGTS de que esta analise precisa.")
    lre = ler_partes(achar_partes_grupo(base, cnpj14, "idA_LRE"))
    folha = ler_partes(achar_partes_grupo(base, cnpj14, "idM_FOLHA"))
    afast = ler_partes(achar_partes_grupo(base, cnpj14, "idK_AFAST"))
    if not lre:
        raise ValueError("O LRE foi lido mas nao ha vinculos (result vazio).")

    jan_ini, jan_fim, trabs = auditar(lre, folha, afast, hoje)
    ag = agregar(trabs, jan_ini, jan_fim, hoje)
    linhas = montar_linhas(trabs)
    meta = {
        "empregador": empregador or cnpj14, "cnpj": fmt_identificador(cnpj14)[0],
        "gerado": hoje.strftime("%d/%m/%Y"), "janela": ag["janela"],
        "vinculos": ag["vinculos"], "trabBuracos": ag["trab_buracos"],
        "mesesBuraco": ag["meses_buraco"], "trabSem13": ag["trab_sem_13"],
        "anosSem13": ag["anos_sem_13"], "trabAbaixo": ag["trab_abaixo"],
        "trabSemResc": ag["trab_sem_rescisoria"],
    }
    destino = Path(pasta_os) / "eSocial"
    destino.mkdir(parents=True, exist_ok=True)
    html = (HTML.replace("__DADOS__", json.dumps(linhas, ensure_ascii=False))
                .replace("__META__", json.dumps(meta, ensure_ascii=False))
                .replace("__EMPREGADOR__", (empregador or cnpj14)
                         .replace("&", "&amp;").replace("<", "&lt;")))
    (destino / "Folha_painel.html").write_text(html, encoding="utf-8")
    gravar_csv(destino / "Folha_analise.csv", trabs)
    gravar_md(destino / "folha.md", meta, ag)
    (destino / "folha_resumo.json").write_text(
        json.dumps(ag, ensure_ascii=False, indent=1), encoding="utf-8")
    meta["destino"] = str(destino)
    meta["arquivos"] = [str(destino / n) for n in
                        ("Folha_painel.html", "Folha_analise.csv",
                         "folha.md", "folha_resumo.json")]
    return meta


def main():
    argv = sys.argv[1:]
    base = None
    hoje = None
    if "--sisfgts" in argv:
        i = argv.index("--sisfgts")
        base = argv[i + 1]
        del argv[i:i + 2]
    if "--hoje" in argv:   # para testes reprodutiveis
        i = argv.index("--hoje")
        hoje = d_iso(argv[i + 1])
        del argv[i:i + 2]

    if len(argv) < 2:
        print(__doc__)
        sys.exit(1)
    pasta_os = Path(argv[0])
    cnpj = re.sub(r"\D", "", argv[1])
    empregador = argv[2] if len(argv) > 2 else pasta_os.name
    if len(cnpj) not in (11, 14):
        print(f"CNPJ/CPF invalido: '{argv[1]}' -> precisa de 14 digitos (CNPJ) "
              "ou 11 digitos (CPF, empregador pessoa fisica).")
        sys.exit(1)
    if not pasta_os.is_dir():
        print(f"Pasta da OS nao existe: {pasta_os}")
        sys.exit(1)

    try:
        m = gerar(pasta_os, cnpj, empregador, base, hoje)
    except (FileNotFoundError, ValueError) as e:
        print(f"ERRO: {e}")
        sys.exit(4)

    print(f"Folha eSocial - {m['empregador']} ({m['cnpj']})")
    print(f"  Folha disponivel .................. {m['janela']}")
    print(f"  Vinculos com folha no periodo ..... {m['vinculos']}")
    print(f"  BURACOS na folha .................. {m['trabBuracos']} trabalhador(es), "
          f"{m['mesesBuraco']} mes(es) sem base e sem afastamento")
    print(f"  Ano sem base de 13o ............... {m['trabSem13']} trabalhador(es), "
          f"{m['anosSem13']} ano(s)")
    print(f"  Ultimos {MESES_RECENTES} meses abaixo do contratual  {m['trabAbaixo']} ativo(s)")
    print(f"  Dispensados sem base rescisoria ... {m['trabSemResc']}")
    print("  Criterio: base declarada (tpValor 11); mes sem base so e buraco se")
    print("  nenhum afastamento cobre >= 20 dias dele. Base declarada nao e")
    print("  recolhimento: FGTS em atraso quem aponta e o SISFGTS. INDICIO,")
    print("  nao prova: confirmar na folha de pagamento antes de autuar.")
    print(f"\nGravado em: {m['destino']}")
    for a in m["arquivos"]:
        print(f"  {Path(a).name}")


if __name__ == "__main__":
    main()
