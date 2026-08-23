#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
lre_ferias.py — AFT Toolkit
Cruza o LRE (vinculos, grupo idA) com os afastamentos (grupo idK) que o
SISFGTS baixa do eSocial e audita as FERIAS de cada vinculo: reconstitui os
periodos aquisitivos e concessivos e aponta indicios de ferias vencidas nao
concedidas (dobra do art. 137 da CLT), gozo fora do prazo, prazo prestes a
vencer e fracionamento irregular.

Grava, dentro da pasta da OS:

  eSocial/Ferias_painel.html   painel interativo por trabalhador
  eSocial/Ferias_analise.csv   um periodo aquisitivo auditado por linha
  eSocial/ferias.md            resumo SEM nome e SEM CPF (para o /aft-painel)
  eSocial/ferias_resumo.json   numeros agregados (sem PII)

Tudo local: nenhuma chamada de rede, nenhuma dependencia externa.
O HTML e autocontido (CSS/JS embutidos, sem CDN) e contem DADOS PESSOAIS.

Uso:
  python lre_ferias.py "<pasta da OS>" <CNPJ14> ["<EMPREGADOR>"] [--sisfgts "<base>"]
  python lre_ferias.py --achar <CNPJ14>

REGRAS APLICADAS (documentadas tambem no SKILL.md da /aft-lre-esocial):

- art. 130 da CLT: a cada periodo aquisitivo (PA) de 12 meses o empregado tem
  direito a ferias. Assumimos 30 dias -- as faltas injustificadas que reduzem
  a escala do art. 130 NAO constam do arquivo, e por isso todo apontamento e
  INDICIO, nunca prova.
- art. 134: as ferias devem ser concedidas nos 12 meses seguintes ao PA
  (periodo concessivo). Prazo estourado sem gozo => indicio de ferias vencidas
  (dobra do art. 137).
- Sumula 81 do TST: dias de ferias gozados APOS o periodo concessivo devem ser
  pagos em dobro -- por isso gozo tardio e apontado mesmo quando as ferias
  foram integralmente gozadas.
- art. 143 (abono pecuniario): ate 10 dias podem ser convertidos em dinheiro e
  NAO aparecem como afastamento. Gozo de 20 a 29 dias com prazo vencido vira
  "conferir abono", nunca dobra firme. Dobra firme so com gozo < 20 dias.
- art. 134 par. 1 (fracionamento): ate 3 periodos, um de pelo menos 14 dias e
  nenhum menor que 5.
- art. 133, IV: afastamento previdenciario por mais de 180 dias dentro do PA
  zera o PA; a contagem recomeca na volta. Como os primeiros 15 dias de cada
  episodio correm por conta do empregador, contamos como previdenciarios os
  dias que EXCEDEM 15 por episodio (simplificacao documentada).

JANELA DE DADOS (a principal protecao contra falso positivo): o arquivo so
tem afastamentos de quando a empresa passou a transmitir ao eSocial. Ferias
de PAs encerrados antes disso podem ter sido gozadas fora da janela (ou no
empregador anterior, em caso de sucessao) sem deixar rastro no arquivo.
Por isso:
  - so PAs INICIADOS dentro da janela sao auditados;
  - PAs encerrados antes da janela ficam fora ate da alocacao FIFO -- mante-los
    na fila faria as ferias recentes "quitarem" PAs antigos e falsearia os
    novos (num teste real isso multiplicava por dez os indicios);
  - vinculo que veio por sucessao/cessao DEPOIS do inicio da janela da empresa
    (sucessaovinc_dttransf) tem janela propria a partir da transferencia: os
    afastamentos dele neste CNPJ so existem dali em diante;
  - bloco de ferias iniciado APOS o prazo concessivo de um PA so completa esse
    PA ate o minimo de 20 dias: se o PA ja tem 20 dias tempestivos, o
    empregador pode ter usado o abono e o bloco tardio pertence ao PA seguinte.
    O que se reporta como "dias apos o prazo" e sempre o MINIMO certo.
O inicio da janela e a primeira recepcao de evento no eSocial (dhrecepcao
minimo do LRE), com fallback no primeiro afastamento registrado.
"""
import csv
import json
import re
import sys
from calendar import monthrange
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from lre_esocial import (achar_sisfgts, achar_partes_grupo, ler_partes,
                         d_iso, d_rec, fmt_d, fmt_cpf, fmt_cnpj)

DIAS_FERIAS = 30          # art. 130 (sem as faltas, que o arquivo nao traz)
ABONO_MAX = 10            # art. 143: ate 1/3 de 30 dias
CARENCIA_INSS = 15        # dias por episodio a cargo do empregador
LIMITE_ART133 = 180       # art. 133 IV: > 6 meses zera o PA
JANELA_VENCENDO = 60      # dias: prazo concessivo "prestes a vencer"
COD_FERIAS = "15"         # tabela 18 do eSocial: ferias
COD_INSS = ("01", "03")   # acidente/doenca do trabalho e doenca comum


def add_meses(dt, m):
    y, mo = dt.year + (dt.month - 1 + m) // 12, (dt.month - 1 + m) % 12 + 1
    return date(y, mo, min(dt.day, monthrange(y, mo)[1]))


def carregar(base, cnpj14):
    lre = ler_partes(achar_partes_grupo(base, cnpj14, "idA_LRE"))
    afast = ler_partes(achar_partes_grupo(base, cnpj14, "idK_AFAST"))
    return lre, afast


def janela_dados(lre, afast, hoje):
    """Inicio: primeira recepcao no eSocial (fallback: primeiro afastamento)."""
    recs = [d_rec(v.get("dhrecepcao")) for v in lre]
    recs = [r for r in recs if r]
    inis = [d_iso(a.get("dtiniafast")) for a in afast]
    inis = [i for i in inis if i]
    ini = min(recs) if recs else (min(inis) if inis else hoje)
    return ini


def auditar_vinculo(v, eventos, janela_ini, hoje):
    """Audita as ferias de um vinculo. Devolve o dicionario do trabalhador
    com a lista de PAs e os totais de indicio."""
    dtadm, dtdes = d_iso(v.get("dtadm")), d_iso(v.get("dtdeslig"))
    if not dtadm:
        return None
    fim_vinculo = dtdes or hoje
    # Vinculo que veio por sucessao/cessao DEPOIS do inicio da janela da
    # empresa: os afastamentos dele neste CNPJ so existem a partir da
    # transferencia -- ferias gozadas antes ficaram no empregador anterior.
    # A janela do vinculo e o mais tardio entre a da empresa e a transferencia.
    transf = d_iso(v.get("sucessaovinc_dttransf"))
    if transf and transf > janela_ini:
        janela_ini = transf

    ferias, inss = [], []
    for r in sorted(eventos, key=lambda r: r.get("dtiniafast") or ""):
        i = d_iso(r.get("dtiniafast"))
        if not i:
            continue
        t = d_iso(r.get("dttermafast")) or hoje
        if r.get("codmotafast") == COD_FERIAS:
            ferias.append({"ini": i, "fim": t, "dias": (t - i).days + 1})
        elif r.get("codmotafast") in COD_INSS:
            inss.append((i, t))

    # ---- periodos aquisitivos, com o art. 133 IV
    pas = []
    ini_pa = dtadm
    while ini_pa < fim_vinculo:
        fim_pa = add_meses(ini_pa, 12) - timedelta(days=1)
        dias_prev, volta = 0, None
        for (i, t) in inss:
            ov_i, ov_t = max(i, ini_pa), min(t, fim_pa)
            if ov_i <= ov_t:
                # so os dias que excedem a carencia do empregador no episodio
                dias_prev += max(0, (ov_t - ov_i).days + 1 - CARENCIA_INSS)
                volta = max(volta or t, t)
        if dias_prev > LIMITE_ART133 and volta:
            pas.append({"ini": ini_pa, "fim": fim_pa, "status": "zerado",
                        "obs": f"art. 133 IV: {dias_prev} dias previdenciários "
                               f"no PA; contagem reiniciada em "
                               f"{fmt_d(volta + timedelta(days=1))}"})
            ini_pa = volta + timedelta(days=1)
            continue
        pas.append({"ini": ini_pa, "fim": fim_pa,
                    "completo": fim_pa < fim_vinculo,
                    "prazo": add_meses(fim_pa, 12)})
        ini_pa = fim_pa + timedelta(days=1)

    # ---- alocacao FIFO das ferias aos PAs completos dentro da janela
    fila = [dict(f) for f in ferias]
    for p in pas:
        if p.get("status") == "zerado":
            continue
        if not p.get("completo"):
            p["status"] = "incompleto"
            continue
        if p["fim"] < janela_ini:
            p["status"] = "fora-janela"
            continue
        # Bloco de ferias INICIADO depois do prazo concessivo do PA so
        # completa o PA ate o minimo de 20 dias (30 - abono): se o PA ja tem
        # 20 dias tempestivos, o empregador pode ter usado o abono do art. 143
        # e o bloco tardio pertence ao PA seguinte -- sem esta trava, a
        # alocacao gulosa fabricava "gozo fora do prazo" de 10 dias em quem
        # provavelmente vendeu 10 dias. O que se reporta e o MINIMO certo.
        minimo = DIAS_FERIAS - ABONO_MAX
        gozo, split = [], False
        while fila:
            dias_pa = sum(g["dias"] for g in gozo)
            if dias_pa >= DIAS_FERIAS:
                break
            f = fila[0]
            tardio = f["ini"] > p["prazo"]
            if tardio and dias_pa >= minimo:
                break
            teto = minimo if tardio else DIAS_FERIAS
            usa = min(f["dias"], teto - dias_pa)
            gozo.append({"ini": f["ini"], "fim": f["fim"], "dias": usa,
                         "parcial": usa != (f["fim"] - f["ini"]).days + 1})
            if usa == f["dias"]:
                fila.pop(0)
            else:
                f["dias"] -= usa
                split = True
        p["gozo"], p["split"] = gozo, split
        p["dias"] = sum(g["dias"] for g in gozo)
        p["status"] = "auditar"

    # ---- classificacao dos PAs auditaveis
    tot = {"vencida": 0, "dias_vencidos": 0, "fora_prazo": 0,
           "dias_dobro": 0, "vencendo": 0, "abono": 0, "frac": 0,
           "auditados": 0, "art133": 0}
    for p in pas:
        if p.get("status") == "zerado":
            tot["art133"] += 1
            continue
        if p.get("status") != "auditar":
            continue
        if p["ini"] < janela_ini:
            p["status"] = "fora-janela"
            continue
        tot["auditados"] += 1
        prazo = p["prazo"]
        # dias gozados em blocos INICIADOS apos o prazo concessivo (S. 81 TST)
        p["dias_dobro"] = sum(g["dias"] for g in p["gozo"] if g["ini"] > prazo)
        if dtdes and prazo >= dtdes:
            p["status"] = "rescisao"
            p["obs"] = "prazo concessivo alcança o desligamento: saldo devido na rescisão"
            continue
        if prazo >= hoje:
            if p["dias"] >= DIAS_FERIAS - ABONO_MAX:
                p["status"] = "ok"
            elif (prazo - hoje).days <= JANELA_VENCENDO:
                p["status"] = "vencendo"
                tot["vencendo"] += 1
            else:
                p["status"] = "no-prazo"
        else:
            if p["dias"] < DIAS_FERIAS - ABONO_MAX:
                p["status"] = "vencida"
                tot["vencida"] += 1
                tot["dias_vencidos"] += DIAS_FERIAS - p["dias"]
            elif p["dias_dobro"] > 0:
                p["status"] = "fora-prazo"
                tot["fora_prazo"] += 1
                tot["dias_dobro"] += p["dias_dobro"]
            elif p["dias"] < DIAS_FERIAS:
                p["status"] = "abono"
                tot["abono"] += 1
            else:
                p["status"] = "ok"
        # fracionamento (art. 134 par. 1) -- so quando nenhum bloco foi
        # dividido entre PAs pela alocacao (o corte artificial falsearia)
        if len(p["gozo"]) >= 2 and not p["split"]:
            dias_fr = [g["dias"] for g in p["gozo"]]
            if len(dias_fr) > 3 or max(dias_fr) < 14 or min(dias_fr) < 5:
                p["frac"] = True
                tot["frac"] += 1

    # ---- ha quanto tempo o vinculo esta sem gozar ferias (so ativos)
    meses_sem = None
    if not dtdes:
        marco = max(dtadm, janela_ini)
        ult = max((f["fim"] for f in ferias), default=None)
        ref = ult or marco
        meses_sem = round((hoje - ref).days / 30.44)

    return {"mat": v.get("matricula", ""), "nome": v.get("nmtrab", ""),
            "cpf": fmt_cpf(v.get("cpftrab")), "adm": dtadm, "des": dtdes,
            "ativo": not dtdes, "pas": pas, "tot": tot,
            "meses_sem": meses_sem, "n_ferias": len(ferias)}


def auditar(lre, afast, hoje):
    janela_ini = janela_dados(lre, afast, hoje)
    por_vinc = {}
    for r in afast:
        por_vinc.setdefault((r.get("cpftrab"), r.get("matricula")), []).append(r)
    trabs = []
    for v in lre:
        t = auditar_vinculo(v, por_vinc.get((v.get("cpftrab"),
                                             v.get("matricula")), []),
                            janela_ini, hoje)
        if t:
            trabs.append(t)
    return janela_ini, trabs


# ------------------------------------------------------------------- saidas
STATUS_ROTULO = {
    "vencida": "FÉRIAS VENCIDAS (indício de dobra, art. 137)",
    "fora-prazo": "gozadas FORA do prazo (dobra devida, S. 81 TST)",
    "vencendo": "prazo concessivo prestes a vencer",
    "abono": "conferir abono pecuniário (art. 143)",
    "ok": "regular", "no-prazo": "dentro do prazo concessivo",
    "rescisao": "saldo devido na rescisão", "incompleto": "PA em curso",
    "fora-janela": "anterior aos dados (não auditável)",
    "zerado": "zerado pelo art. 133 IV",
}


def montar_linhas(trabs):
    """Uma linha por trabalhador para o painel (JSON embutido no HTML)."""
    out = []
    for t in trabs:
        tt = t["tot"]
        pas = []
        for p in t["pas"]:
            pas.append({
                "ini": fmt_d(p["ini"]), "fim": fmt_d(p["fim"]),
                "prazo": fmt_d(p.get("prazo")), "st": p.get("status", ""),
                "rot": STATUS_ROTULO.get(p.get("status", ""), p.get("status", "")),
                "dias": p.get("dias"), "dobro": p.get("dias_dobro") or 0,
                "frac": bool(p.get("frac")), "obs": p.get("obs", ""),
                "gozo": [f'{fmt_d(g["ini"])} a {fmt_d(g["fim"])} '
                         f'({g["dias"]} d{"; bloco dividido entre PAs" if g["parcial"] else ""})'
                         for g in p.get("gozo", [])],
            })
        out.append({
            "mat": t["mat"], "nome": t["nome"], "cpf": t["cpf"],
            "adm": fmt_d(t["adm"]), "admO": t["adm"].isoformat(),
            "des": fmt_d(t["des"]), "ativo": t["ativo"],
            "auditados": tt["auditados"], "vencida": tt["vencida"],
            "diasVenc": tt["dias_vencidos"], "foraPrazo": tt["fora_prazo"],
            "diasDobro": tt["dias_dobro"], "vencendo": tt["vencendo"],
            "abono": tt["abono"], "frac": tt["frac"], "art133": tt["art133"],
            "mesesSem": t["meses_sem"], "nFerias": t["n_ferias"],
            "pas": pas,
        })
    # os casos mais graves primeiro
    out.sort(key=lambda x: (-(x["diasVenc"] + x["diasDobro"]),
                            -x["vencendo"], x["nome"]))
    return out


def gravar_csv(destino, trabs):
    cols = ["MATRICULA", "NOME", "CPF", "SITUACAO", "ADMISSAO", "DESLIGAMENTO",
            "PA_INICIO", "PA_FIM", "PRAZO_CONCESSIVO", "DIAS_GOZADOS",
            "DIAS_APOS_PRAZO", "STATUS", "GOZOS"]
    with open(destino, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(cols)
        for t in trabs:
            for p in t["pas"]:
                if p.get("status") in (None, "incompleto", "fora-janela"):
                    continue
                w.writerow([
                    t["mat"], t["nome"], t["cpf"],
                    "ativo" if t["ativo"] else "desligado",
                    fmt_d(t["adm"]), fmt_d(t["des"]),
                    fmt_d(p["ini"]), fmt_d(p["fim"]), fmt_d(p.get("prazo")),
                    p.get("dias", ""), p.get("dias_dobro", ""),
                    STATUS_ROTULO.get(p["status"], p["status"]),
                    " | ".join(f'{fmt_d(g["ini"])} a {fmt_d(g["fim"])} ({g["dias"]} d)'
                               for g in p.get("gozo", []))])


def agregar(trabs, janela_ini, hoje):
    tv = [t for t in trabs if t["tot"]["vencida"]]
    fp = [t for t in trabs if t["tot"]["fora_prazo"]]
    vc = [t for t in trabs if t["tot"]["vencendo"]]
    ab = [t for t in trabs if t["tot"]["abono"]]
    fr = [t for t in trabs if t["tot"]["frac"]]
    return {
        "janela_ini": fmt_d(janela_ini), "hoje": fmt_d(hoje),
        "vinculos": len(trabs),
        "auditados": sum(t["tot"]["auditados"] for t in trabs),
        "trab_auditados": sum(1 for t in trabs if t["tot"]["auditados"]),
        "trab_vencida": len(tv),
        "pa_vencida": sum(t["tot"]["vencida"] for t in trabs),
        "dias_vencidos": sum(t["tot"]["dias_vencidos"] for t in trabs),
        "trab_fora_prazo": len(fp),
        "pa_fora_prazo": sum(t["tot"]["fora_prazo"] for t in trabs),
        "dias_dobro": sum(t["tot"]["dias_dobro"] for t in trabs),
        "trab_vencendo": len(vc),
        "trab_abono": len(ab), "trab_frac": len(fr),
        "art133": sum(t["tot"]["art133"] for t in trabs),
    }


def gravar_md(destino, meta, ag):
    """Resumo em markdown SEM nome e SEM CPF (aparece no /aft-painel)."""
    L = []
    L.append("# Férias - auditoria pelo eSocial (LRE + afastamentos)\n")
    L.append(f"- **Estabelecimento:** {meta['cnpj']}")
    L.append(f"- **Fonte:** SISFGTS, grupos `idA_LRE` e `idK_AFAST`")
    L.append(f"- **Extraído em:** {meta['gerado']} · **janela de dados desde:** {ag['janela_ini']}")
    L.append(f"- **Painel:** [Ferias_painel.html](Ferias_painel.html) "
             f"· **Planilha:** [Ferias_analise.csv](Ferias_analise.csv)\n")
    L.append("## Quadro geral\n")
    L.append("| Indicador | Valor |")
    L.append("|---|---|")
    L.append(f"| Vínculos no LRE | {ag['vinculos']} |")
    L.append(f"| Períodos aquisitivos auditáveis (iniciados desde {ag['janela_ini']}) | {ag['auditados']} |")
    L.append(f"| **Trabalhadores com férias vencidas** (indício de dobra, art. 137) | **{ag['trab_vencida']}** |")
    L.append(f"| &nbsp;&nbsp;· períodos aquisitivos vencidos sem gozo suficiente | {ag['pa_vencida']} |")
    L.append(f"| &nbsp;&nbsp;· dias de férias vencidos e não gozados | {ag['dias_vencidos']} |")
    L.append(f"| **Trabalhadores com férias gozadas fora do prazo** (S. 81 TST) | **{ag['trab_fora_prazo']}** |")
    L.append(f"| &nbsp;&nbsp;· dias gozados após o prazo concessivo | {ag['dias_dobro']} |")
    L.append(f"| Trabalhadores com prazo concessivo vencendo em até {JANELA_VENCENDO} dias | {ag['trab_vencendo']} |")
    L.append(f"| Períodos a conferir abono pecuniário (gozo de 20 a 29 dias) | {ag['trab_abono']} |")
    L.append(f"| Indícios de fracionamento irregular (art. 134 §1º) | {ag['trab_frac']} |")
    if ag["art133"]:
        L.append(f"| Períodos zerados por afastamento previdenciário (art. 133 IV) | {ag['art133']} |")
    L.append("")
    L.append("## Como o indício é apurado\n")
    L.append(f"> Períodos aquisitivos reconstituídos a partir da admissão do LRE; "
             f"férias são os afastamentos código 15 do eSocial. **Só entram na análise "
             f"períodos aquisitivos iniciados a partir de {ag['janela_ini']}** (início da "
             f"janela de dados da empresa no eSocial): férias de períodos anteriores podem "
             f"ter sido gozadas antes da janela — ou no empregador anterior, em caso de "
             f"sucessão — sem deixar rastro no arquivo.\n>\n"
             f"> Assumem-se 30 dias por período (as faltas injustificadas do art. 130 não "
             f"constam do arquivo). Gozo de 20 a 29 dias pode ser regular se houve abono "
             f"pecuniário (art. 143), que também não aparece — por isso dobra firme só é "
             f"apontada com gozo abaixo de 20 dias. **É indício, não prova**: confirmar "
             f"nos recibos de férias e na folha antes de autuar; ementa e capitulação "
             f"pelo `/aft-consulta`.\n")
    L.append("---\n")
    L.append("_Gerado pela `/aft-lre-esocial` a partir dos arquivos do SISFGTS. "
             "Os dados nominais estão no painel e no CSV desta mesma pasta: "
             "arquivos locais com dados pessoais — não publicar._")
    destino.write_text("\n".join(L), encoding="utf-8")


HTML = r"""<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Férias eSocial - __EMPREGADOR__</title>
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
tr.venc td:first-child{box-shadow:inset 3px 0 0 var(--warn)}
.tag{display:inline-block;padding:1px 7px;border-radius:10px;font-size:11px;font-weight:600}
.t-a{background:var(--okbg);color:var(--ok)}
.t-d{background:var(--bg);color:var(--mut);border:1px solid var(--bd)}
.t-w{background:var(--warnbg);color:var(--warn)}
.t-m{background:var(--ambbg);color:var(--amb)}
.nm{font-weight:600}.sm{color:var(--mut);font-size:11.5px}.nw{white-space:nowrap}
.det td{background:var(--bg);padding:14px}
.det table{font-size:12.5px}.det th{position:static;cursor:default}
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
<div class="sub">CNPJ <b id="mCnpj"></b> &middot; LRE + afastamentos do eSocial (SISFGTS)
 &middot; extraído em <span id="mGer"></span> &middot; janela de dados desde <b id="mJan"></b></div></header>
<div class="cards">
 <div class="card"><div class="n" id="cAud"></div><div class="l">Períodos aquisitivos auditáveis<br><span id="cAudSub" style="font-size:11px"></span></div></div>
 <div class="card w"><div class="n" id="cVen"></div><div class="l">Trabalhadores com férias vencidas<br><span style="font-size:11px">indício de dobra (art. 137)</span></div></div>
 <div class="card w"><div class="n" id="cDias"></div><div class="l">Dias de férias vencidos sem gozo</div></div>
 <div class="card a"><div class="n" id="cFp"></div><div class="l">Com gozo fora do prazo<br><span id="cFpSub" style="font-size:11px"></span></div></div>
 <div class="card a"><div class="n" id="cVdo"></div><div class="l">Prazo vencendo em até 60 dias</div></div>
 <div class="card"><div class="n" id="cAb"></div><div class="l">Conferir abono pecuniário<br><span style="font-size:11px">gozo de 20 a 29 dias (art. 143)</span></div></div>
</div>
<div class="note"><b>É indício, não prova.</b> Períodos aquisitivos reconstituídos da admissão do LRE;
 férias = afastamentos código 15. Só entram períodos iniciados a partir de <b id="mJan2"></b>
 (início dos dados da empresa no eSocial) — férias anteriores podem ter sido gozadas fora da
 janela, ou no empregador anterior em caso de sucessão, sem deixar rastro no arquivo.
 Assumem-se 30 dias por período: as <b>faltas injustificadas</b> que reduzem a escala do
 art. 130 não constam do arquivo. Gozo de 20 a 29 dias pode ser regular se houve
 <b>abono pecuniário</b> (art. 143), que também não aparece — dobra firme só com gozo abaixo
 de 20 dias. Confirmar nos recibos de férias e na folha antes de autuar.</div>
<div class="bar">
 <input id="q" type="search" placeholder="Buscar por nome, CPF ou matrícula..." autocomplete="off">
 <button class="chip on" data-f="todos">Todos</button>
 <button class="chip" data-f="vencida">Férias vencidas</button>
 <button class="chip" data-f="foraPrazo">Gozo fora do prazo</button>
 <button class="chip" data-f="vencendo">Prazo vencendo</button>
 <button class="chip" data-f="abono">Conferir abono</button>
 <button class="chip" data-f="regular">Sem indício</button>
 <span class="cnt" id="cnt"></span></div>
<div class="tw"><table><thead><tr>
 <th data-s="mat">Matríc. <span class="ar">&#9662;</span></th>
 <th data-s="nome">Nome <span class="ar">&#9662;</span></th>
 <th data-s="admO">Admissão <span class="ar">&#9662;</span></th>
 <th data-s="ativo">Situação <span class="ar">&#9662;</span></th>
 <th data-s="auditados">PAs auditados <span class="ar">&#9662;</span></th>
 <th data-s="diasVenc">Dias vencidos <span class="ar">&#9662;</span></th>
 <th data-s="diasDobro">Dias fora do prazo <span class="ar">&#9662;</span></th>
 <th data-s="mesesSem">Sem férias há <span class="ar">&#9662;</span></th>
</tr></thead><tbody id="tb"></tbody></table>
<div class="empty" id="empty" style="display:none">Nenhum trabalhador corresponde à busca.</div>
<div class="pg" id="pg"></div></div>
<div class="foot">Arquivo local com dados pessoais de trabalhadores.
 Não publicar, não anexar em e-mail, não enviar a serviços externos.</div>
</div>
<script>
const D=__DADOS__, M=__META__;
hEmp.textContent='Férias eSocial — '+M.empregador;
mCnpj.textContent=M.cnpj; mGer.textContent=M.gerado;
mJan.textContent=M.janelaIni; mJan2.textContent=M.janelaIni;
cAud.textContent=M.auditados; cAudSub.textContent=M.trabAuditados+' trabalhadores';
cVen.textContent=M.trabVencida; cDias.textContent=M.diasVencidos;
cFp.textContent=M.trabForaPrazo; cFpSub.textContent=M.diasDobro+' dias após o prazo (S. 81 TST)';
cVdo.textContent=M.trabVencendo; cAb.textContent=M.trabAbono;
function esc(s){return String(s??'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));}
let filtro='todos',termo='',ord='diasVenc',asc=false,pag=1,tam=50;
function norm(s){return String(s??'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();}
function hl(s,t){s=esc(s); if(!t)return s;
 const n=norm(s),q=norm(t); let i=n.indexOf(q); if(i<0)return s;
 return s.slice(0,i)+'<mark>'+s.slice(i,i+t.length)+'</mark>'+s.slice(i+t.length);}
function filtrar(){const t=norm(termo);
 return D.filter(x=>{
  if(filtro==='vencida'&&!x.vencida)return false;
  if(filtro==='foraPrazo'&&!x.foraPrazo)return false;
  if(filtro==='vencendo'&&!x.vencendo)return false;
  if(filtro==='abono'&&!x.abono)return false;
  if(filtro==='regular'&&(x.vencida||x.foraPrazo||x.vencendo||x.abono||x.frac))return false;
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
  const badges=(x.vencida?` <span class="tag t-w">${x.vencida} PA vencido${x.vencida>1?'s':''}</span>`:'')+
    (x.foraPrazo?' <span class="tag t-m">fora do prazo</span>':'')+
    (x.vencendo?' <span class="tag t-m">vencendo</span>':'')+
    (x.frac?' <span class="tag t-m">fracionamento</span>':'');
  const sem=(x.mesesSem==null)?'&mdash;':(x.mesesSem<=0?'em gozo/recente':x.mesesSem+' m');
  return `<tr class="r${x.vencida?' venc':''}" data-i="${i}">
   <td>${esc(x.mat)}</td>
   <td><span class="nm">${hl(x.nome,termo)}</span><div class="sm">${esc(x.cpf)}</div></td>
   <td class="nw">${x.adm}</td>
   <td>${sit}${badges}</td>
   <td>${x.auditados}</td>
   <td>${x.diasVenc||'&mdash;'}</td>
   <td>${x.diasDobro||'&mdash;'}</td>
   <td class="nw">${sem}</td></tr>`;}).join('');
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
function corSt(st){
 if(st==='vencida')return 't-w';
 if(st==='fora-prazo'||st==='vencendo'||st==='abono')return 't-m';
 if(st==='ok'||st==='no-prazo'||st==='rescisao')return 't-a';
 return 't-d';}
function detalhe(tr,x){
 const nx=tr.nextElementSibling;
 if(nx&&nx.classList.contains('det')){nx.remove();return;}
 tb.querySelectorAll('tr.det').forEach(e=>e.remove());
 const linhas=x.pas.map(p=>{
  const g=p.gozo.length?p.gozo.map(esc).join('<br>'):'&mdash;';
  const fr=p.frac?' <span class="tag t-m">fracionamento a conferir (art. 134 §1º)</span>':'';
  return `<tr><td class="nw">${p.ini} a ${p.fim}</td>
   <td class="nw">${p.prazo||'&mdash;'}</td>
   <td>${p.dias==null?'&mdash;':p.dias}</td>
   <td>${p.dobro||'&mdash;'}</td>
   <td><span class="tag ${corSt(p.st)}">${esc(p.rot)}</span>${fr}${p.obs?`<div class="sm">${esc(p.obs)}</div>`:''}</td>
   <td>${g}</td></tr>`;}).join('');
 const t2=document.createElement('tr'); t2.className='det';
 t2.innerHTML=`<td colspan="8">
  <div class="sm" style="margin-bottom:8px">Períodos aquisitivos do vínculo
   (${x.nFerias} período(s) de férias no arquivo${x.art133?` · ${x.art133} PA zerado(s) pelo art. 133 IV`:''})</div>
  <table><thead><tr><th>Período aquisitivo</th><th>Prazo concessivo</th>
   <th>Dias gozados</th><th>Dias após o prazo</th><th>Situação</th><th>Gozo</th></tr></thead>
  <tbody>${linhas}</tbody></table></td>`;
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
            f"Nenhum arquivo LRE para o CNPJ {cnpj14} em "
            f"{base / 'Arquivos' / 'eSocial' / cnpj14}. "
            "Baixe os dados do eSocial no SISFGTS antes.")
    if not achar_partes_grupo(base, cnpj14, "idK_AFAST"):
        raise FileNotFoundError(
            f"O CNPJ {cnpj14} tem o LRE mas NAO tem afastamentos (idK). "
            "No SISFGTS, baixe o eSocial com a opcao 'LRE e demais registros' "
            "- e ela que traz os afastamentos de que a analise de ferias precisa.")
    lre, afast = carregar(base, cnpj14)
    if not lre:
        raise ValueError("O LRE foi lido mas nao ha vinculos (result vazio).")

    janela_ini, trabs = auditar(lre, afast, hoje)
    ag = agregar(trabs, janela_ini, hoje)
    linhas = montar_linhas(trabs)
    meta = {
        "empregador": empregador or cnpj14, "cnpj": fmt_cnpj(cnpj14),
        "gerado": hoje.strftime("%d/%m/%Y"), "janelaIni": ag["janela_ini"],
        "auditados": ag["auditados"], "trabAuditados": ag["trab_auditados"],
        "trabVencida": ag["trab_vencida"], "paVencida": ag["pa_vencida"],
        "diasVencidos": ag["dias_vencidos"],
        "trabForaPrazo": ag["trab_fora_prazo"], "diasDobro": ag["dias_dobro"],
        "trabVencendo": ag["trab_vencendo"], "trabAbono": ag["trab_abono"],
        "trabFrac": ag["trab_frac"],
    }
    destino = Path(pasta_os) / "eSocial"
    destino.mkdir(parents=True, exist_ok=True)
    html = (HTML.replace("__DADOS__", json.dumps(linhas, ensure_ascii=False))
                .replace("__META__", json.dumps(meta, ensure_ascii=False))
                .replace("__EMPREGADOR__", (empregador or cnpj14)
                         .replace("&", "&amp;").replace("<", "&lt;")))
    (destino / "Ferias_painel.html").write_text(html, encoding="utf-8")
    gravar_csv(destino / "Ferias_analise.csv", trabs)
    gravar_md(destino / "ferias.md", meta, ag)
    (destino / "ferias_resumo.json").write_text(
        json.dumps(ag, ensure_ascii=False, indent=1), encoding="utf-8")
    meta["destino"] = str(destino)
    meta["arquivos"] = [str(destino / n) for n in
                        ("Ferias_painel.html", "Ferias_analise.csv",
                         "ferias.md", "ferias_resumo.json")]
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

    if argv and argv[0] == "--achar":
        cnpj = re.sub(r"\D", "", argv[1]) if len(argv) > 1 else ""
        b = achar_sisfgts(base)
        if not b:
            print("SISFGTS: NAO ENCONTRADO")
            sys.exit(2)
        print(f"SISFGTS: {b}")
        for grupo, rotulo in (("idA_LRE", "LRE"), ("idK_AFAST", "Afastamentos")):
            partes = achar_partes_grupo(b, cnpj, grupo)
            print(f"{rotulo} do CNPJ {cnpj}: "
                  f"{len(partes)} parte(s)" if partes else
                  f"{rotulo} do CNPJ {cnpj}: NENHUM ARQUIVO")
        sys.exit(0)

    if len(argv) < 2:
        print(__doc__)
        sys.exit(1)
    pasta_os = Path(argv[0])
    cnpj = re.sub(r"\D", "", argv[1])
    empregador = argv[2] if len(argv) > 2 else pasta_os.name
    if len(cnpj) != 14:
        print(f"CNPJ invalido: '{argv[1]}' -> precisa de 14 digitos.")
        sys.exit(1)
    if not pasta_os.is_dir():
        print(f"Pasta da OS nao existe: {pasta_os}")
        sys.exit(1)

    try:
        m = gerar(pasta_os, cnpj, empregador, base, hoje)
    except (FileNotFoundError, ValueError) as e:
        print(f"ERRO: {e}")
        sys.exit(4)

    print(f"Ferias eSocial - {m['empregador']} ({m['cnpj']})")
    print(f"  Janela de dados desde ............. {m['janelaIni']}")
    print(f"  PAs auditaveis .................... {m['auditados']} "
          f"({m['trabAuditados']} trabalhadores)")
    print(f"  FERIAS VENCIDAS (dobra, art.137) .. {m['trabVencida']} trabalhador(es), "
          f"{m['paVencida']} PA(s), {m['diasVencidos']} dias sem gozo")
    print(f"  Gozo FORA do prazo (S.81 TST) ..... {m['trabForaPrazo']} trabalhador(es), "
          f"{m['diasDobro']} dias apos o prazo")
    print(f"  Prazo vencendo em ate {JANELA_VENCENDO} dias ..... {m['trabVencendo']} trabalhador(es)")
    print(f"  Conferir abono pecuniario ......... {m['trabAbono']}")
    if m["trabFrac"]:
        print(f"  Fracionamento a conferir .......... {m['trabFrac']}")
    print("  Criterio: PAs iniciados na janela de dados; 30 dias por PA (faltas")
    print("  nao constam); gozo 20-29 dias pode ser abono (art. 143). INDICIO,")
    print("  nao prova: confirmar nos recibos de ferias antes de autuar.")
    print(f"\nGravado em: {m['destino']}")
    for a in m["arquivos"]:
        print(f"  {Path(a).name}")


if __name__ == "__main__":
    main()
