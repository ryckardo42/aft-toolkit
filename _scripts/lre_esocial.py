#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
lre_esocial.py — AFT Toolkit
Le o Livro de Registro de Empregados (LRE) que o SISFGTS baixa do eSocial e
grava, dentro da pasta da OS, a subpasta eSocial/ com:

  eSocial/LRE_painel.html   painel interativo (busca, filtros, paginacao)
  eSocial/LRE_vinculos.csv  planilha dos vinculos (; para Excel pt-BR)
  eSocial/lre-esocial.md    resumo em markdown (lido pelo /aft-painel)

Tudo local: nenhuma chamada de rede, nenhuma dependencia externa.
O HTML e autocontido (CSS/JS embutidos, sem CDN) e contem DADOS PESSOAIS.

Uso:
  python lre_esocial.py "<pasta da OS>" <CNPJ14_ou_CPF11> [--sisfgts "<base>"]
  python lre_esocial.py --achar <CNPJ14_ou_CPF11>

Empregador pessoa fisica (produtor rural, empregador domestico) e indexado
pelo CPF de 11 digitos, sem pontuacao - aceito nos dois lugares acima onde
normalmente se informa o CNPJ.
"""
import csv
import glob
import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone, date
from pathlib import Path

BASES_WIN = [r"C:\SistemasAFT\SisFGTS", r"C:\SisFGTS"]

# Marco legal: a partir de 02/01/2026 o registro eletronico de empregados no
# LRE do eSocial passou a ser obrigatorio para TODAS as empresas, sem
# distincao. Antes disso a obrigatoriedade era escalonada por grupo de
# empregador, entao apontar "registro tardio" para admissao anterior a essa
# data levaria o AFT a perseguir vinculo que talvez nem estivesse obrigado.
# A lista de indicios cobre, portanto, SO admissoes de 02/01/2026 em diante.
MARCO_LRE = date(2026, 1, 2)


def achar_sisfgts(base_informada=None):
    """Acha a instalacao do SISFGTS. Mesma logica do /aft-autos-lavrados:
    caminho padrao no Windows; no Mac/Parallels, varre /Volumes/*/SistemasAFT."""
    if base_informada:
        p = Path(base_informada)
        return p if (p / "Arquivos" / "eSocial").is_dir() else None
    for b in BASES_WIN:
        p = Path(b)
        if (p / "Arquivos" / "eSocial").is_dir():
            return p
    for padrao in ("/Volumes/*/SistemasAFT/SisFGTS", "/Volumes/*/SisFGTS"):
        for c in sorted(glob.glob(padrao)):
            p = Path(c)
            if (p / "Arquivos" / "eSocial").is_dir():
                return p
    return None


def achar_partes_grupo(base, identificador, grupo):
    """Partes de um grupo de arquivos do eSocial no SISFGTS, ordenadas pela
    sequencia. O SISFGTS pagina os resultados (eSocial_<grupo>_<n>_<sufixo>.txt);
    ler so a parte 1 perde registros. Grupos conhecidos: idA_LRE (vinculos),
    idK_AFAST (afastamentos), idM_FOLHA (bases de FGTS da folha).

    `identificador` e o CNPJ de 14 digitos (empregador pessoa juridica) ou o
    CPF de 11 digitos (empregador pessoa fisica - produtor rural, doméstico):
    o SISFGTS usa o mesmo formato como nome da pasta e como sufixo do arquivo
    nos dois casos, so muda a quantidade de digitos (14 ou 11)."""
    pasta = Path(base) / "Arquivos" / "eSocial" / identificador
    if not pasta.is_dir():
        return []
    partes = []
    for p in pasta.glob(f"eSocial_{grupo}_*.txt"):
        m = re.match(rf"eSocial_{grupo}_(\d+)_(\d+)\.txt$", p.name)
        if m:
            partes.append((int(m.group(1)), p))
    return [p for _, p in sorted(partes)]


def achar_partes_lre(base, identificador):
    """Partes do LRE (grupo idA). O SISFGTS pagina de 1.000 em 1.000 vinculos."""
    return achar_partes_grupo(base, identificador, "idA_LRE")


def ler_partes(partes):
    """Concatena as partes. Extensao .txt mas o conteudo e JSON em latin-1."""
    vinc = []
    for p in partes:
        with open(p, encoding="latin-1") as f:
            doc = json.load(f)
        if not doc.get("isSucess"):
            raise ValueError(f"{p.name}: isSucess != true")
        vinc.extend(doc.get("result", []))
    return vinc


MTV = {
    "01": "Rescisão com justa causa, por iniciativa do empregador",
    "02": "Rescisão sem justa causa, por iniciativa do empregador",
    "03": "Rescisão antecipada do contrato a termo por iniciativa do empregador",
    "04": "Rescisão antecipada do contrato a termo por iniciativa do empregado",
    "06": "Rescisão por término do contrato a termo",
    "10": "Rescisão por falecimento do empregado",
    "11": ("Transferência de empregado para empresa do mesmo grupo empresarial "
           "que tenha assumido os encargos trabalhistas, sem que tenha havido "
           "rescisão do contrato de trabalho"),
}
NAO_MAP = "(código não mapeado - conferir tabela do eSocial)"
# Verificadas no proprio banco do SISFGTS (nao adivinhar as ausentes):
CATEG = {"101": "Empregado - Geral, inclusive o empregado público da "
                "administração direta ou indireta contratado pela CLT",
         "103": "Empregado - Aprendiz"}
CATEG_APRENDIZ = "103"

# Cota de PCD - art. 93 da Lei 8.213/91 (faixas legais; a base e o total de
# empregados). Abaixo de 100 empregados a cota nao se aplica.
def cota_pcd(n):
    if n < 100: return 0, None
    if n <= 200: return round(n*0.02), "2% (100 a 200 empregados)"
    if n <= 500: return round(n*0.03), "3% (201 a 500 empregados)"
    if n <= 1000: return round(n*0.04), "4% (501 a 1.000 empregados)"
    return round(n*0.05), "5% (acima de 1.000 empregados)"
RACA = {"1": "Branca", "2": "Preta", "3": "Parda", "4": "Amarela",
        "5": "Indígena", "6": "Não informado"}
GRAU = {"01": "Analfabeto", "02": "Até 5º ano incompleto do Fundamental",
        "03": "5º ano completo do Fundamental",
        "04": "Do 6º ao 9º ano do Fundamental incompleto",
        "05": "Fundamental completo", "06": "Médio incompleto",
        "07": "Médio completo", "08": "Superior incompleto",
        "09": "Superior completo", "10": "Pós-graduação/especialização",
        "11": "Mestrado", "12": "Doutorado"}
UNID = {1: "por hora", 2: "por dia", 3: "por semana", 4: "por quinzena",
        5: "por mês", 6: "por tarefa", 7: "percentual/comissão"}
JORN = {1: "Horário diário e folga fixos",
        2: "Horário diário fixo e folga variável",
        3: "Escala/turno/revezamento",
        4: "Horário diário fixo e folga fixa (domingo)",
        5: "Jornada 12x36", 6: "Horário diário variável",
        9: "Demais tipos de jornada"}
TPADM = {1: "Admissão", 2: "Transferência mesmo grupo",
         3: "Transferência por sucessão", 4: "Trabalhador cedido",
         5: "Mudança de CPF", 6: "Transferência de doméstico"}


def carregar_cbo():
    """CBO tem ~2.600 codigos e NAO vem no LRE. Se houver um cbo.json ao lado
    deste script ({"848325": "descricao"}), enriquecemos a coluna Cargo; sem
    ele mostramos so o codigo -- nunca um palpite."""
    p = Path(__file__).with_name("cbo.json")
    if p.is_file():
        try:
            with open(p, encoding="utf-8") as f:
                return json.load(f)
        except (OSError, ValueError):
            return {}
    return {}


def d_iso(s):
    if not s:
        return None
    try:
        return datetime.fromisoformat(s).date()
    except (ValueError, TypeError):
        return None


def d_rec(s):
    """dhrecepcao: data em que o eSocial RECEBEU o evento do empregador.
    E este o campo que vale para aferir tempestividade."""
    if not s:
        return None
    try:
        return datetime.strptime(s, "%Y-%m-%d %H:%M:%S").date()
    except (ValueError, TypeError):
        return None


def d_epoch(ms):
    """processamento_datahora: processamento INTERNO, nao a transmissao."""
    if not ms:
        return None
    try:
        return datetime.fromtimestamp(int(ms) / 1000, timezone.utc).date()
    except (ValueError, OSError, TypeError):
        return None


def fmt_d(d):
    return d.strftime("%d/%m/%Y") if d else ""


def fmt_cpf(c):
    c = (c or "").zfill(11)
    return f"{c[:3]}.{c[3:6]}.{c[6:9]}-{c[9:]}" if len(c) == 11 else (c or "")


def fmt_cpf_mascarado(c):
    """CPF mascarado (***.***.NNN-NN) para os paineis derivados (ferias e
    folha): matricula + nome identificam o trabalhador; o CPF completo fica
    so no LRE, que e o livro de registro propriamente dito."""
    if not c:
        return ""
    c = str(c).zfill(11)
    return f"***.***.{c[6:9]}-{c[9:]}" if len(c) == 11 else "***"


def fmt_cnpj(c):
    c = re.sub(r"\D", "", c or "")
    return f"{c[:2]}.{c[2:5]}.{c[5:8]}/{c[8:12]}-{c[12:]}" if len(c) == 14 else c


def fmt_identificador(ident):
    """CNPJ (14 digitos) ou CPF (11 digitos) de empregador pessoa fisica
    (produtor rural, empregador domestico). O SISFGTS indexa o eSocial do
    mesmo jeito nos dois casos - so muda a quantidade de digitos."""
    ident = re.sub(r"\D", "", ident or "")
    if len(ident) == 14:
        return fmt_cnpj(ident), "CNPJ"
    if len(ident) == 11:
        return fmt_cpf(ident), "CPF"
    return ident, "CNPJ/CPF"


def detectar_lotes(vinc, min_reg=5, min_frac=0.02, spread_dias=365):
    """Datas em que houve recepcao EM MASSA (carga inicial do eSocial ou
    retransmissao em lote).

    A assinatura de uma carga e propria: MUITOS contratos, com admissoes
    espalhadas por um periodo LONGO, todos recebidos no MESMO dia. Nao basta
    ser "a data mais repetida": numa empresa que ja nasceu no eSocial, a data
    mais repetida e so o dia mais movimentado, e trata-la como carga descarta
    centenas de vinculos da analise -- escondendo atraso real."""
    por_data = {}
    for x in vinc:
        r, a = d_rec(x.get("dhrecepcao")), d_iso(x.get("dtadm"))
        if r and a:
            por_data.setdefault(r, []).append(a)
    lim = max(min_reg, int(len(vinc) * min_frac))
    return {d for d, adms in por_data.items()
            if len(adms) >= lim and (max(adms) - min(adms)).days > spread_dias}


def resumir(vinc):
    ativos = [v for v in vinc if not v.get("dtdeslig")]
    desl = [v for v in vinc if v.get("dtdeslig")]
    pcd = [v for v in ativos if v.get("tpdeficiencia", "N") != "N"
           or any(v.get(k) == "S" for k in ("deffisica", "defvisual",
                  "defauditiva", "defmental", "defintelectual"))]

    lotes = detectar_lotes(vinc)
    n_lote = n_transf = n_pre_marco = 0
    tardios, regulares, sem_data = [], 0, 0
    for v in vinc:
        adm, rec = d_iso(v.get("dtadm")), d_rec(v.get("dhrecepcao"))
        if not (adm and rec):
            sem_data += 1
            continue
        if rec in lotes:
            n_lote += 1      # recebido em carga/lote: nao e atraso do empregador
            continue
        # Corte do marco legal: so admissoes de 02/01/2026 em diante.
        if adm < MARCO_LRE:
            n_pre_marco += 1
            continue
        # So ADMISSAO NOVA (tpadmissao=1) esta sujeita ao prazo do S-2200.
        # Em cessao, transferencia (mesmo grupo/sucessao), mudanca de CPF e
        # transferencia de domestico, o dtadm e a data de admissao ORIGINAL,
        # herdada do empregador de origem -- a recepcao naturalmente ocorre
        # muito depois, e isso NAO e registro tardio. Comparar as duas datas
        # nesses casos produz falso positivo grosseiro.
        if v.get("tpadmissao") != 1:
            if (rec - adm).days >= 0:
                n_transf += 1
            continue
        if (rec - adm).days >= 0:
            tardios.append((v, (rec - adm).days))
        else:
            regulares += 1
    mesmo_dia = sum(1 for _, d in tardios if d == 0)
    aprendizes = [v for v in ativos if v.get("codcateg") == CATEG_APRENDIZ]
    cbos = Counter(v.get("codcbo") for v in ativos if v.get("codcbo"))
    return {"total": len(vinc), "ativos": len(ativos), "desligados": len(desl),
            "pcd": len(pcd), "aprendizes": len(aprendizes), "cbos": cbos, "lotes": sorted(lotes), "em_lote": n_lote,
            "transf": n_transf, "pre_marco": n_pre_marco,
            "marco": MARCO_LRE, "mesmo_dia": mesmo_dia,
            "apos": len(tardios) - mesmo_dia,
            "tardios": tardios, "regulares": regulares, "sem_data": sem_data,
            "por_tipo": Counter(v.get("tprecepcao") for v, _ in tardios),
            "motivos": Counter(v.get("mtvdeslig", "") for v in desl)}


def montar_linhas(vinc, res, cbo_map):
    ids_tard = {id(v): d for v, d in res["tardios"]}
    out = []
    for v in vinc:
        des = d_iso(v.get("dtdeslig"))
        adm = d_iso(v.get("dtadm"))
        try:
            sal = float(v.get("vrsalfx") or 0)
        except (ValueError, TypeError):
            sal = 0.0
        mt = v.get("mtvdeslig")
        out.append({
            "mat": v.get("matricula", ""), "nome": v.get("nmtrab", ""),
            "cpf": fmt_cpf(v.get("cpftrab")),
            "adm": fmt_d(adm), "admO": (adm or date.min).isoformat(),
            "des": fmt_d(des), "desO": (des or date.min).isoformat(),
            "mtv": (MTV.get(mt, NAO_MAP) if mt else ""),
            "cbo": v.get("codcbo", ""),
            "cargo": cbo_map.get(v.get("codcbo"), ""),
            "sal": sal,
            "salF": f"{sal:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
            "unid": UNID.get(v.get("undsalfixo"), ""),
            "ativo": not des,
            "pcd": (v.get("tpdeficiencia", "N") != "N" or any(
                v.get(k) == "S" for k in ("deffisica", "defvisual",
                "defauditiva", "defmental", "defintelectual"))),
            "tardio": id(v) in ids_tard, "dias": ids_tard.get(id(v)),
            "rec": fmt_d(d_rec(v.get("dhrecepcao"))),
            "evt": v.get("tprecepcao", ""),
            "proc": fmt_d(d_epoch(v.get("processamento_datahora"))),
            "nasc": fmt_d(d_iso(v.get("dtnascto"))),
            "sexo": {"M": "Masculino", "F": "Feminino"}.get(v.get("sexo"), ""),
            "raca": RACA.get(str(v.get("racacor")), ""),
            "grau": GRAU.get(v.get("grauinstr"), ""),
            "hrs": v.get("qtdhrssem", ""),
            "jorn": JORN.get(v.get("tpjornada"), ""),
            "tpadm": TPADM.get(v.get("tpadmissao"), ""),
            "categ": v.get("codcateg", ""),
            "bairro": v.get("bairro", ""), "mun": v.get("codmunic", ""),
            "uf": v.get("uf", ""), "recibo": v.get("meta_nr_recibo", ""),
            "local": v.get("localtabgeral_nrinsc", ""),
        })
    return out


# ------------------------------------------------------------------- saidas
def gravar_csv(destino: Path, linhas: list[dict]):
    cols = ["mat", "nome", "cpf", "adm", "tpadm", "evt", "rec", "proc", "des",
            "mtv", "cbo", "cargo", "sal", "unid", "hrs", "jorn", "categ",
            "sexo", "nasc", "raca", "grau", "bairro", "mun", "uf", "pcd",
            "tardio", "dias", "recibo", "local"]
    rot = {"mat": "MATRICULA", "nome": "NOME", "cpf": "CPF",
           "adm": "ADMISSAO", "tpadm": "TIPO_ADMISSAO", "evt": "EVENTO",
           "rec": "RECEPCAO_ESOCIAL", "proc": "PROCESSAMENTO_INTERNO",
           "des": "DESLIGAMENTO", "mtv": "MOTIVO_DESLIGAMENTO", "cbo": "CBO",
           "cargo": "CARGO", "sal": "SALARIO", "unid": "UNIDADE_SALARIO",
           "hrs": "HORAS_SEMANAIS", "jorn": "JORNADA", "categ": "CATEGORIA",
           "sexo": "SEXO", "nasc": "NASCIMENTO", "raca": "RACA_COR",
           "grau": "GRAU_INSTRUCAO", "bairro": "BAIRRO", "mun": "COD_MUNICIPIO",
           "uf": "UF", "pcd": "PCD", "tardio": "INDICIO_TARDIO",
           "dias": "DIAS_ATRASO", "recibo": "RECIBO_ADMISSAO",
           "local": "LOCAL_DE_TRABALHO"}
    with open(destino, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow([rot[c] for c in cols])
        for l in linhas:
            w.writerow([("S" if l[c] else "N") if c in ("pcd", "tardio")
                        else ("" if l[c] is None else l[c]) for c in cols])


def gravar_md(destino: Path, meta: dict, res: dict):
    """Resumo em markdown -- e este arquivo que o /aft-painel lista como
    documento da OS. NAO contem nome nem CPF: so agregados."""
    L = []
    L.append("# LRE eSocial - Livro de Registro de Empregados\n")
    L.append(f"- **Empregador ({meta.get('tipoDoc','CNPJ')}):** {meta['cnpj']}")
    L.append(f"- **Fonte:** SISFGTS, {meta['partes']} arquivo(s) "
             f"`eSocial_idA_LRE_*_{meta['raiz']}.txt`")
    L.append(f"- **Extraído em:** {meta['gerado']}")
    L.append(f"- **Painel:** [LRE_painel.html](LRE_painel.html) "
             f"· **Planilha:** [LRE_vinculos.csv](LRE_vinculos.csv)\n")
    L.append("## Quadro geral\n")
    L.append("| Indicador | Valor |")
    L.append("|---|---|")
    L.append(f"| Vínculos no LRE | {meta['total']} |")
    L.append(f"| Ativos | {meta['ativos']} |")
    L.append(f"| Desligados | {meta['desligados']} |")
    L.append(f"| PCD (entre os ativos) | {meta['pcd']} |")
    L.append("")
    locais = meta.get("locais") or []
    if len(locais) > 1:
        L.append("## Local de trabalho\n")
        L.append(f"> Este empregador declara **{len(locais)} locais de "
                 "trabalho** distintos (`localtabgeral_nrinsc`) — comum em "
                 "empregador pessoa física com mais de uma propriedade/imóvel. "
                 "A lista completa dos vínculos por local está no painel "
                 "(filtro \"Local de trabalho\") e na coluna "
                 "`LOCAL_DE_TRABALHO` do CSV. Para saber qual código é o "
                 "estabelecimento que você vai fiscalizar, busque no painel "
                 "pelo nome ou CPF de um trabalhador que você já sabe que "
                 "trabalha lá — o código aparece no detalhe do vínculo.\n")
        L.append("| Código do local | Vínculos |")
        L.append("|---|---|")
        for cod, n in locais[:20]:
            L.append(f"| {cod} | {n} |")
        if len(locais) > 20:
            L.append(f"\n_(mostrando 20 de {len(locais)} locais; lista "
                     "completa no painel e no CSV)_")
        L.append("")
    L.append(f"## Registro tardio — admissões a partir de {meta['marco']}\n")
    L.append(f"> A lista de indícios cobre **somente admissões de "
             f"{meta['marco']} em diante** — marco em que o registro "
             f"eletrônico de empregados no LRE do eSocial passou a ser "
             f"obrigatório para **todas** as empresas, sem distinção. Antes "
             f"disso a obrigatoriedade era escalonada por grupo de "
             f"empregador.\n")
    base = meta["regulares"] + meta["tardios"]
    L.append("| Indicador | Valor |")
    L.append("|---|---|")
    L.append(f"| Admissões novas desde {meta['marco']} | {base} |")
    L.append(f"| &nbsp;&nbsp;· transmitidas antes da admissão | {meta['regulares']} |")
    L.append(f"| &nbsp;&nbsp;· **indício de registro tardio** | **{meta['tardios']}** |")
    L.append(f"| &nbsp;&nbsp;&nbsp;&nbsp;— recebido no mesmo dia da admissão | {meta['mesmoDia']} |")
    L.append(f"| &nbsp;&nbsp;&nbsp;&nbsp;— recebido após a admissão | {meta['apos']} |")
    if meta["preMarco"]:
        L.append(f"| Fora do recorte: admitidos antes de {meta['marco']} | {meta['preMarco']} |")
    if meta["transf"]:
        L.append(f"| Fora do critério: transferência/cessão | {meta['transf']} |")
    if meta["carga"]:
        L.append(f"| Recepção em massa (carga/lote) | {meta['carga']} |")
        L.append(f"| Vínculos recebidos nessa(s) carga(s) | {meta['em_lote']} |")
    L.append("")
    if meta["tardios"]:
        L.append(f"### Vínculos com indício (admitidos a partir de "
                 f"{meta['marco']})\n")
        L.append(f"> Critério: admissão a partir de {meta['marco']}; "
                 "data de recepção do evento no eSocial "
                 "(`dhrecepcao`) igual ou posterior à data de admissão, sendo "
                 "o S-2200 devido até o dia imediatamente anterior ao início "
                 "da prestação de serviços. Vínculos recebidos numa carga "
                 "inicial ou retransmissão em lote foram desconsiderados "
                 "(recepção em bloco não é atraso do empregador). "
                 "**É indício, não prova de falta de registro** — "
                 "conferir caso a caso. Eventos `evtAdmPrelim` têm regime de "
                 "prazo próprio.\n\n"
                 "> **Só entram admissões novas** (`tpadmissao = 1`). "
                 "Cessão, transferência (mesmo grupo ou sucessão), mudança "
                 "de CPF e transferência de doméstico ficam de fora: nesses "
                 "casos o `dtadm` é a data de admissão **original**, herdada "
                 "do empregador de origem, e a recepção tardia é da natureza "
                 "do instituto — não é registro em atraso.\n")
        if meta["porTipo"]:
            L.append("Por tipo de evento: " +
                     ", ".join(f"`{k or '?'}` = {v}"
                               for k, v in meta["porTipo"]) + "\n")
        L.append("| Matrícula | Admissão | Recepção | Atraso | Evento |")
        L.append("|---|---|---|---|---|")
        for v, dias in sorted(res["tardios"], key=lambda x: -x[1])[:30]:
            L.append(f"| {v.get('matricula','')} | {fmt_d(d_iso(v.get('dtadm')))} "
                     f"| {fmt_d(d_rec(v.get('dhrecepcao')))} | {dias} d "
                     f"| {v.get('tprecepcao','')} |")
        if len(res["tardios"]) > 30:
            L.append(f"\n_(mostrando 30 de {len(res['tardios'])}; a lista "
                     f"completa está no painel e no CSV)_")
        L.append("")
    if meta["motivos"]:
        L.append("## Motivos de desligamento\n")
        L.append("| Cód. | Descrição | Qtd. |")
        L.append("|---|---|---|")
        for c, n, desc in meta["motivos"]:
            L.append(f"| {c or '-'} | {desc} | {n} |")
        L.append("")
    L.append("---\n")
    L.append("_Gerado pela `/aft-lre-esocial` a partir do arquivo do SISFGTS. "
             "Os dados nominais estão no painel e no CSV desta mesma pasta: "
             "arquivos locais com dados pessoais — não publicar._")
    destino.write_text("\n".join(L), encoding="utf-8")


HTML = r"""<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>LRE eSocial - __EMPREGADOR__</title>
<style>
:root{--bg:#f5f6f8;--card:#fff;--tx:#1c2430;--mut:#6b7684;--bd:#dfe3e8;
 --ac:#1f4e79;--ac2:#e8eef5;--warn:#b3261e;--warnbg:#fdeceb;--ok:#1b6b3a;--okbg:#e8f4ec;}
@media (prefers-color-scheme:dark){:root{--bg:#14181d;--card:#1c2229;--tx:#e6eaef;
 --mut:#98a3b0;--bd:#2d353f;--ac:#6ea8dc;--ac2:#23303d;--warn:#f2837a;
 --warnbg:#37211f;--ok:#7fc79b;--okbg:#1c2b22;}}
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
.card.w .n{color:var(--warn)}.card.g .n{color:var(--ok)}
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
tr.tard td:first-child{box-shadow:inset 3px 0 0 var(--warn)}
.tag{display:inline-block;padding:1px 7px;border-radius:10px;font-size:11px;font-weight:600}
.t-a{background:var(--okbg);color:var(--ok)}
.t-d{background:var(--bg);color:var(--mut);border:1px solid var(--bd)}
.t-t{background:var(--warnbg);color:var(--warn)}
.nm{font-weight:600}.sm{color:var(--mut);font-size:11.5px}.nw{white-space:nowrap}
.det td{background:var(--bg);padding:14px}
.dg{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:10px 20px}
.dg div{font-size:12.5px}.dg b{display:block;color:var(--mut);font-weight:500;font-size:11px}
.note{background:var(--warnbg);border:1px solid var(--warn);color:var(--warn);
 border-radius:8px;padding:11px 13px;margin:14px 0;font-size:12.5px}
.mv{background:var(--card);border:1px solid var(--bd);border-radius:10px;padding:14px;margin-top:14px}
.mv table{font-size:12.5px}.mv th{position:static}
.pg{display:flex;gap:6px;align-items:center;justify-content:center;padding:12px;flex-wrap:wrap}
.pg button{padding:6px 11px;border:1px solid var(--bd);border-radius:7px;background:var(--card);
 color:var(--tx);cursor:pointer;font-size:13px;min-width:36px}
.pg button:hover:not(:disabled){border-color:var(--ac);color:var(--ac)}
.pg button.on{background:var(--ac);color:#fff;border-color:var(--ac)}
.pg button:disabled{opacity:.35;cursor:default}
.pg .info{color:var(--mut);font-size:12.5px;margin:0 8px}
.pg select{padding:6px;border:1px solid var(--bd);border-radius:7px;background:var(--card);color:var(--tx)}
.foot{color:var(--mut);font-size:11.5px;margin:18px 0 40px;text-align:center}
.empty{padding:40px;text-align:center;color:var(--mut)}
mark{background:#ffe38a;color:#000;padding:0 1px;border-radius:2px}
@media (prefers-color-scheme:dark){mark{background:#7a6320;color:#fff}}
</style></head><body><div class="wrap">
<header><h1 id="hEmp"></h1>
<div class="sub"><span id="mDocLbl">CNPJ</span> <b id="mCnpj"></b> &middot; <span id="mFonte"></span>
 &middot; extraído em <span id="mGer"></span></div></header>
<div class="note" id="noteLocais" style="display:none"><b>Vários locais de trabalho declarados</b> —
 este empregador tem <span id="nLocais"></span> locais de trabalho distintos (comum em pessoa física
 com mais de uma propriedade/imóvel). Use o filtro <b>Local de trabalho</b> abaixo para restringir a
 lista a um só local: se você já sabe o nome de um trabalhador daquele estabelecimento, busque por ele
 primeiro, abra o detalhe do vínculo para ver o código do local, e então escolha esse código no filtro.</div>
<div class="cards">
 <div class="card"><div class="n" id="cTot"></div><div class="l">Vínculos no LRE</div></div>
 <div class="card g"><div class="n" id="cAtv"></div><div class="l">Ativos</div></div>
 <div class="card"><div class="n" id="cDes"></div><div class="l">Desligados</div></div>
 <div class="card"><div class="n" id="cPcd"></div><div class="l">PCD entre os ativos<br><span id="cPcdCota" style="font-size:11px"></span></div></div>
 <div class="card"><div class="n" id="cApr"></div><div class="l">Aprendizes<br><span id="cAprCota" style="font-size:11px"></span></div></div>
 <div class="card g"><div class="n" id="cReg"></div><div class="l">Transmitidos antes da admissão<br><span style="font-size:11px">(mesmo recorte)</span></div></div>
 <div class="card w"><div class="n" id="cTar"></div><div class="l">Indício de registro tardio<br><span id="cTarMarco" style="font-size:11px;font-weight:600"></span><br><span id="cTarSub" style="font-size:11px"></span></div></div>
</div>
<div class="note"><b>Indício de registro tardio &mdash; somente admissões a partir de
 <span id="mMarco2"></span></b>, marco em que o registro eletrônico de empregados no LRE do
 eSocial passou a ser obrigatório para <b>todas</b> as empresas, sem distinção (antes disso a
 obrigatoriedade era escalonada por grupo de empregador)<span id="mPre"></span>.<br>
 Critério: data de recepção do
 evento no eSocial (<code>dhrecepcao</code>) igual ou posterior à data de admissão, sendo o
 S-2200 devido até o dia imediatamente anterior ao início da prestação de serviços.
 Vínculos recebidos numa carga inicial ou retransmissão em lote
 (<span id="mCarga"></span>) foram desconsiderados, pois a recepção em bloco não é
 atraso do empregador. <b>É indício, não prova de falta de
 registro</b> &mdash; conferir caso a caso. Eventos <code>evtAdmPrelim</code> têm regime de
 prazo próprio: <span id="mTipos"></span>.<br><b>Só entram admissões novas</b> (<code>tpadmissao&nbsp;=&nbsp;1</code>): cessão, transferência (mesmo grupo ou sucessão), mudança de CPF e transferência de doméstico ficam de fora, porque nesses casos a data de admissão é a <b>original</b>, herdada do empregador de origem &mdash; a recepção tardia é da natureza do instituto, não registro em atraso<span id="mTransf"></span>.</div>
<div class="bar">
 <input id="q" type="search" placeholder="Buscar por nome, CPF, matrícula ou cargo..." autocomplete="off">
 <button class="chip on" data-f="todos">Todos</button>
 <button class="chip" data-f="ativos">Ativos</button>
 <button class="chip" data-f="desligados">Desligados</button>
 <button class="chip" data-f="tardios" title="somente admissões a partir do marco de obrigatoriedade">Indício tardio (desde <span id="chipMarco"></span>)</button>
 <button class="chip" data-f="pcd">PCD</button>
 <select id="fLocal" style="display:none;padding:8px 10px;border:1px solid var(--bd);border-radius:8px;background:var(--bg);color:var(--tx);font-size:13px"></select>
 <span class="cnt" id="cnt"></span></div>
<div class="tw"><table><thead><tr>
 <th data-s="mat">Matríc. <span class="ar">&#9662;</span></th>
 <th data-s="nome">Nome <span class="ar">&#9662;</span></th>
 <th data-s="admO">Admissão <span class="ar">&#9662;</span></th>
 <th data-s="desO">Desligamento <span class="ar">&#9662;</span></th>
 <th data-s="cargo">Cargo (CBO) <span class="ar">&#9662;</span></th>
 <th data-s="sal">Salário <span class="ar">&#9662;</span></th>
 <th data-s="ativo">Situação <span class="ar">&#9662;</span></th>
</tr></thead><tbody id="tb"></tbody></table>
<div class="empty" id="empty" style="display:none">Nenhum vínculo corresponde à busca.</div>
<div class="pg" id="pg"></div></div>
<div class="mv"><b>Perfil ocupacional (ativos)</b>
 <div style="font-size:12px;color:var(--mut);margin:2px 0 8px">O que os CBOs declarados
  dizem que a empresa faz — compare com o CNAE. Divergência forte pode indicar CNAE
  desatualizado ou atividade não declarada.</div>
 <table><thead><tr><th>CBO</th><th>Ocupação</th><th>Ativos</th></tr></thead>
 <tbody id="ptb"></tbody></table></div>
<div class="mv"><b>Cotas — a conferir</b>
 <div style="font-size:12.5px;color:var(--mut);margin-top:6px" id="cotasTxt"></div></div>
<div class="mv"><b>Motivos de desligamento</b>
 <table><thead><tr><th>Cód.</th><th>Descrição</th><th>Qtd.</th></tr></thead>
 <tbody id="mtb"></tbody></table></div>
<div class="foot">Arquivo local com dados pessoais de trabalhadores.
 Não publicar, não anexar em e-mail, não enviar a serviços externos.</div>
</div>
<script>
const D=__DADOS__, M=__META__;
hEmp.textContent='LRE eSocial — '+M.empregador;
mDocLbl.textContent=M.tipoDoc||'CNPJ';
mCnpj.textContent=M.cnpj; mFonte.textContent=M.fonte; mGer.textContent=M.gerado;
if(M.locais && M.locais.length>1){
  noteLocais.style.display='block'; nLocais.textContent=M.locais.length;
  fLocal.style.display='inline-block';
  fLocal.innerHTML='<option value="">Local de trabalho: todos</option>'+
    M.locais.map(l=>`<option value="${esc(l[0])}">${esc(l[0])} (${l[1]})</option>`).join('');
  fLocal.onchange=()=>{filtroLocal=fLocal.value;pag=1;render();};
}
cTot.textContent=M.total; cAtv.textContent=M.ativos; cDes.textContent=M.desligados;
cPcd.textContent=M.pcd; cReg.textContent=M.regulares; cTar.textContent=M.tardios;
cApr.textContent=M.aprendizes;
if(M.cotaPcd){
  cPcdCota.textContent=`cota ${M.cotaPcd} · ${M.cotaPcdFaixa}`;
  if(M.pcd<M.cotaPcd){cPcd.style.color='var(--warn)';
    cPcdCota.textContent+=` — faltam ${M.cotaPcd-M.pcd}`;}
}else{cPcdCota.textContent='cota não se aplica (menos de 100 empregados)';}
cAprCota.textContent=`faixa 5–15%: ${M.aprFaixaMin}–${M.aprFaixaMax} (base a conferir)`;
if(M.aprendizes<M.aprFaixaMin) cApr.style.color='var(--warn)';
cTarSub.textContent=M.tardios?`${M.mesmoDia} no mesmo dia · ${M.apos} depois`:'';
cTarMarco.textContent=`admitidos a partir de ${M.marco}`;
mCarga.textContent=M.carga?(M.carga+' — '+M.em_lote+' vínculos'):'nenhuma recepção em massa detectada';
mTipos.textContent=M.porTipo.map(t=>t[0]+' = '+t[1]).join(', ')||'-';
mTransf.textContent=M.transf?` (${M.transf} vínculo(s) desta empresa nessa situação)`:'';
mMarco2.textContent=M.marco;
chipMarco.textContent=M.marco;
mPre.textContent=M.preMarco?` — ${M.preMarco} vínculo(s) admitido(s) antes dessa data ficaram fora do recorte`:'';
function esc(s){return String(s??'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));}
ptb.innerHTML=(M.perfil||[]).map(x=>`<tr><td>${esc(x[0])}</td><td>${esc(x[2])}</td><td>${x[1]}</td></tr>`).join('');
cotasTxt.innerHTML=
 `<b>PCD</b> — declarados <b>${M.pcd}</b> entre ${M.ativos} ativos. `+
 (M.cotaPcd?`Cota do art. 93 da Lei 8.213/91: <b>${M.cotaPcd}</b> — ${esc(M.cotaPcdFaixa)}.`
           :`Cota não se aplica: menos de 100 empregados.`)+
 `<br><b>Aprendizes</b> — declarados <b>${M.aprendizes}</b>. O art. 429 da CLT exige de 5% a 15%, `+
 `mas <b>a base não é o efetivo total</b>: exclui cargos de direção, gerência e de confiança e as `+
 `funções que exigem nível técnico ou superior. Sobre o total (${M.ativos}) a faixa seria `+
 `${M.aprFaixaMin}–${M.aprFaixaMax} — <b>ordem de grandeza, não a cota devida</b>; o cálculo da base é do AFT.`+
 `<br><span style="color:var(--warn)">Os dois números saem do que o empregador declarou no eSocial: conferir em campo.</span>`;
mtb.innerHTML=M.motivos.map(m=>`<tr><td>${esc(m[0]||'-')}</td><td>${esc(m[2])}</td><td>${m[1]}</td></tr>`).join('');
let filtro='todos',filtroLocal='',termo='',ord='nome',asc=true,pag=1,tam=50;
function norm(s){return String(s??'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();}
function hl(s,t){s=esc(s); if(!t)return s;
 const n=norm(s),q=norm(t); let i=n.indexOf(q); if(i<0)return s;
 return s.slice(0,i)+'<mark>'+s.slice(i,i+t.length)+'</mark>'+s.slice(i+t.length);}
function filtrar(){const t=norm(termo);
 return D.filter(x=>{
  if(filtro==='ativos'&&!x.ativo)return false;
  if(filtro==='desligados'&&x.ativo)return false;
  if(filtro==='tardios'&&!x.tardio)return false;
  if(filtro==='pcd'&&!x.pcd)return false;
  if(filtroLocal&&x.local!==filtroLocal)return false;
  if(!t)return true;
  return norm(x.nome).includes(t)||norm(x.cpf).includes(t)||
         norm(x.mat).includes(t)||norm(x.cargo).includes(t)||norm(x.cbo).includes(t);
 }).sort((a,b)=>{let p=a[ord],q=b[ord];
  if(typeof p==='boolean'){p=p?1:0;q=q?1:0;}
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
  const tar=x.tardio?` <span class="tag t-t">+${x.dias}d</span>`:'';
  const pcd=x.pcd?' <span class="tag t-a">PCD</span>':'';
  return `<tr class="r${x.tardio?' tard':''}" data-i="${i}">
   <td>${esc(x.mat)}</td>
   <td><span class="nm">${hl(x.nome,termo)}</span><div class="sm">${esc(x.cpf)}</div></td>
   <td class="nw">${x.adm}${tar}</td>
   <td>${x.des||'&mdash;'}${x.mtv?`<div class="sm">${esc(x.mtv.slice(0,44))}${x.mtv.length>44?'...':''}</div>`:''}</td>
   <td>${x.cargo?esc(x.cargo)+'<div class="sm">'+esc(x.cbo)+'</div>':'<span class="sm">CBO '+esc(x.cbo)+'</span>'}</td>
   <td class="nw">R$&nbsp;${x.salF}<div class="sm">${esc(x.unid)}</div></td>
   <td>${sit}${pcd}</td></tr>`;}).join('');
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
function detalhe(tr,x){
 const nx=tr.nextElementSibling;
 if(nx&&nx.classList.contains('det')){nx.remove();return;}
 tb.querySelectorAll('tr.det').forEach(e=>e.remove());
 const f=(l,v)=>v?`<div><b>${l}</b>${esc(v)}</div>`:'';
 const t2=document.createElement('tr'); t2.className='det';
 t2.innerHTML=`<td colspan="7"><div class="dg">
  ${f('CPF',x.cpf)}${f('Matrícula',x.mat)}${f('Nascimento',x.nasc)}${f('Sexo',x.sexo)}
  ${f('Raça/cor',x.raca)}${f('Grau de instrução',x.grau)}${f('Tipo de admissão',x.tpadm)}
  ${f('Categoria',x.categ)}${f('Jornada',x.jorn)}${f('Horas semanais',x.hrs)}
  ${f('Bairro',x.bairro)}${f('Município (IBGE)',x.mun?x.mun+' / '+x.uf:'')}
  ${f('Local de trabalho',x.local)}
  ${f('Motivo do desligamento',x.mtv)}${f('Evento',x.evt)}
  ${f('Recepção no eSocial',x.rec)}${f('Processamento interno',x.proc)}
  ${f('Recibo da admissão',x.recibo)}
  ${x.tardio?`<div><b>Indício</b>recebido ${x.dias} dia(s) após a admissão</div>`:''}
 </div></td>`;
 tr.after(t2);}
q.addEventListener('input',e=>{termo=e.target.value.trim();pag=1;render();});
document.querySelectorAll('.chip').forEach(b=>b.onclick=()=>{
 document.querySelectorAll('.chip').forEach(c=>c.classList.remove('on'));
 b.classList.add('on');filtro=b.dataset.f;pag=1;render();});
document.querySelectorAll('th[data-s]').forEach(th=>th.onclick=()=>{
 const s=th.dataset.s; asc=(ord===s)?!asc:true; ord=s; pag=1;
 document.querySelectorAll('th .ar').forEach(a=>a.innerHTML='&#9662;');
 th.querySelector('.ar').innerHTML=asc?'&#9652;':'&#9662;'; render();});
render();
</script></body></html>
"""


def gerar(pasta_os: Path, cnpj14: str, empregador: str = "",
          base_sisfgts=None) -> dict:
    """Le o LRE do SISFGTS e grava <pasta_os>/eSocial/ com painel, CSV e md.

    `cnpj14` aceita tambem CPF de 11 digitos, para empregador pessoa fisica
    (produtor rural, empregador domestico) - o SISFGTS indexa o eSocial da
    mesma forma nos dois casos."""
    base = achar_sisfgts(base_sisfgts)
    if not base:
        raise FileNotFoundError(
            "SISFGTS nao encontrado. No Windows esperamos "
            r"C:\SistemasAFT\SisFGTS; no Mac, o disco do Parallels montado "
            "em /Volumes/... Informe a base com --sisfgts se estiver noutro lugar.")
    partes = achar_partes_lre(base, cnpj14)
    if not partes:
        doc_lbl = "CNPJ" if len(cnpj14) == 14 else "CPF"
        raise FileNotFoundError(
            f"Nenhum arquivo LRE para o {doc_lbl} {cnpj14} em "
            f"{base / 'Arquivos' / 'eSocial' / cnpj14}. "
            "Baixe os dados do eSocial no SISFGTS antes de rodar esta skill.")
    vinc = ler_partes(partes)
    if not vinc:
        raise ValueError("O LRE foi lido mas nao ha vinculos (result vazio).")

    res = resumir(vinc)
    cbo_map = carregar_cbo()
    linhas = montar_linhas(vinc, res, cbo_map)
    raiz = cnpj14[:8] if len(cnpj14) == 14 else cnpj14
    ident_fmt, tipo_doc = fmt_identificador(cnpj14)
    # Local de trabalho (localtabgeral_nrinsc): empregador pessoa fisica rural
    # costuma ter varias propriedades - cada uma com o proprio codigo. Sem
    # isso, o AFT recebe uma lista enorme de trabalhadores sem saber quais
    # pertencem ao estabelecimento que vai fiscalizar.
    locais = Counter(l["local"] for l in linhas if l["local"])
    motivos = [(c, n, (MTV.get(c, NAO_MAP) if c else "-"))
               for c, n in res["motivos"].most_common()]
    meta = {
        "empregador": empregador or cnpj14,
        "cnpj": ident_fmt, "tipoDoc": tipo_doc, "raiz": raiz, "partes": len(partes),
        "fonte": (f"SISFGTS · {len(partes)} arquivo"
                  f"{'s' if len(partes) > 1 else ''} LRE"),
        "gerado": date.today().strftime("%d/%m/%Y"),
        "total": res["total"], "ativos": res["ativos"],
        "desligados": res["desligados"], "pcd": res["pcd"],
        "regulares": res["regulares"], "tardios": len(res["tardios"]),
        "aprendizes": res["aprendizes"],
        # Cota de PCD: art. 93 da Lei 8.213/91, sobre o total de empregados.
        "cotaPcd": cota_pcd(res["ativos"])[0],
        "cotaPcdFaixa": cota_pcd(res["ativos"])[1] or "",
        # Cota de aprendizagem: art. 429 da CLT, 5% a 15%. A BASE LEGAL nao e o
        # efetivo total -- exclui cargos de direcao/gerencia/confianca e as
        # funcoes que exigem nivel tecnico ou superior. Como essa exclusao
        # depende de analise do AFT, a faixa aqui e sobre o total e serve de
        # ORDEM DE GRANDEZA, nunca como a cota devida.
        "aprFaixaMin": round(res["ativos"] * 0.05),
        "aprFaixaMax": round(res["ativos"] * 0.15),
        # Perfil ocupacional: o que os CBOs dizem que a empresa faz.
        "perfil": [[c, n, cbo_map.get(c, f"CBO {c}")]
                   for c, n in res["cbos"].most_common(12)],
        "carga": (", ".join(fmt_d(d) for d in res["lotes"])
                  if res["lotes"] else ""),
        "em_lote": res["em_lote"], "transf": res["transf"],
        "preMarco": res["pre_marco"], "marco": fmt_d(res["marco"]),
        "mesmoDia": res["mesmo_dia"], "apos": res["apos"],
        "porTipo": list(res["por_tipo"].items()), "motivos": motivos,
        "locais": locais.most_common(),
    }

    destino = Path(pasta_os) / "eSocial"
    destino.mkdir(parents=True, exist_ok=True)
    html = (HTML.replace("__DADOS__", json.dumps(linhas, ensure_ascii=False))
                .replace("__META__", json.dumps(meta, ensure_ascii=False))
                .replace("__EMPREGADOR__", (empregador or cnpj14)
                         .replace("&", "&amp;").replace("<", "&lt;")))
    (destino / "LRE_painel.html").write_text(html, encoding="utf-8")
    gravar_csv(destino / "LRE_vinculos.csv", linhas)
    gravar_md(destino / "lre-esocial.md", meta, res)
    # resumo.json: numeros agregados (sem PII) para o /aft-painel montar o
    # cartao da OS sem precisar interpretar o markdown.
    (destino / "resumo.json").write_text(json.dumps({
        "cnpj": meta["cnpj"], "gerado": meta["gerado"],
        "total": meta["total"], "ativos": meta["ativos"],
        "desligados": meta["desligados"], "pcd": meta["pcd"],
        "cota_pcd": meta["cotaPcd"], "cota_pcd_faixa": meta["cotaPcdFaixa"],
        "aprendizes": meta["aprendizes"],
        "apr_faixa": [meta["aprFaixaMin"], meta["aprFaixaMax"]],
        "perfil": meta["perfil"],
        "tardios": meta["tardios"], "marco": meta["marco"],
        "mesmo_dia": meta["mesmoDia"],
        "apos": meta["apos"], "painel": "eSocial/LRE_painel.html",
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    meta["destino"] = str(destino)
    meta["arquivos"] = [str(destino / n) for n in
                        ("LRE_painel.html", "LRE_vinculos.csv", "lre-esocial.md",
                         "resumo.json")]
    return meta


def listar_indicios(pasta_os: Path, limite=25, como_json=False):
    """Lista NOMINAL dos vinculos com indicio de registro tardio.

    Existe para a /aft-preparacao-acao-fiscal: sao as pessoas que o AFT vai
    procurar no estabelecimento para conferir ficha/registro e ASO. Segue a
    mesma regra da FASE 3.1 daquela skill -- nomear so o punhado que o AFT
    precisa chamar pelo nome; os demais viram contagem.

    Le o CSV ja gerado na pasta da OS (nao reprocessa o SISFGTS), entao roda
    mesmo com o disco do SISFGTS desmontado."""
    arq = Path(pasta_os) / "eSocial" / "LRE_vinculos.csv"
    if not arq.is_file():
        return None
    with open(arq, encoding="utf-8-sig", newline="") as f:
        linhas = [r for r in csv.DictReader(f, delimiter=";")
                  if r.get("INDICIO_TARDIO") == "S"]
    linhas.sort(key=lambda r: -int(r.get("DIAS_ATRASO") or 0))
    saida = [{"nome": r["NOME"], "matricula": r["MATRICULA"],
              "admissao": r["ADMISSAO"], "recepcao": r["RECEPCAO_ESOCIAL"],
              "dias": int(r.get("DIAS_ATRASO") or 0),
              "cargo": r["CARGO"] or f"CBO {r['CBO']}",
              "situacao": "ativo" if not r["DESLIGAMENTO"] else "desligado",
              "desligamento": r["DESLIGAMENTO"]}
             for r in linhas]
    if como_json:
        print(json.dumps({"total": len(saida), "limite": limite,
                          "indicios": saida[:limite]},
                         ensure_ascii=False, indent=1))
        return saida
    if not saida:
        print("Nenhum indicio de registro tardio.")
        return saida
    print(f"INDICIOS DE REGISTRO TARDIO - {len(saida)} trabalhador(es)")
    print("(admissao a partir do marco; conferir ficha/registro e ASO no local)\n")
    for i, x in enumerate(saida[:limite], 1):
        atraso = "mesmo dia" if x["dias"] == 0 else f"+{x['dias']} dias"
        print(f" {i:3}. {x['nome']}")
        print(f"      matricula {x['matricula']} | {x['cargo'][:46]}")
        print(f"      admissao {x['admissao']} | recepcao {x['recepcao']} "
              f"| {atraso} | {x['situacao']}")
    if len(saida) > limite:
        print(f"\n ... e mais {len(saida)-limite}. Lista completa no painel "
              f"(filtro 'Indicio tardio') e no LRE_vinculos.csv.")
    return saida


def main():
    argv = sys.argv[1:]
    base = None
    if "--sisfgts" in argv:
        i = argv.index("--sisfgts")
        base = argv[i + 1]
        del argv[i:i + 2]

    if argv and argv[0] == "--perfil":
        if len(argv) < 2:
            print('uso: lre_esocial.py --perfil "<pasta da OS>"'); sys.exit(1)
        arq = Path(argv[1]) / "eSocial" / "resumo.json"
        if not arq.is_file():
            print("Esta OS nao tem eSocial/resumo.json - rode a /aft-lre-esocial antes.")
            sys.exit(3)
        with open(arq, encoding="utf-8") as f:
            d = json.load(f)
        if "--json" in argv:
            print(json.dumps(d, ensure_ascii=False, indent=1)); sys.exit(0)
        print(f"PERFIL OCUPACIONAL - {d['ativos']} ativos "
              f"(o que os CBOs dizem que a empresa faz)\n")
        for c, n, desc in d.get("perfil", []):
            print(f"  {n:5}  {desc[:58]:60} CBO {c}")
        print(f"\nCOTAS (a conferir)")
        print(f"  PCD ......... declarados {d['pcd']} de {d['ativos']} ativos", end="")
        print(f" | cota art. 93 Lei 8.213/91: {d['cota_pcd']} ({d['cota_pcd_faixa']})"
              if d.get("cota_pcd") else " | cota nao se aplica (<100 empregados)")
        fx = d.get("apr_faixa", [0, 0])
        print(f"  Aprendizes .. declarados {d['aprendizes']}"
              f" | art. 429 CLT 5-15%: sobre o total daria {fx[0]}-{fx[1]}")
        print("     ATENCAO: a base do art. 429 NAO e o efetivo total (exclui direcao,")
        print("     gerencia, confianca e funcoes de nivel tecnico/superior) - o calculo")
        print("     da base e do AFT; o numero acima e so ordem de grandeza.")
        sys.exit(0)

    if argv and argv[0] == "--indicios":
        if len(argv) < 2:
            print("uso: lre_esocial.py --indicios \"<pasta da OS>\" [--json] [--limite N]")
            sys.exit(1)
        lim = 25
        if "--limite" in argv:
            i = argv.index("--limite")
            lim = int(argv[i + 1]); del argv[i:i + 2]
        r = listar_indicios(Path(argv[1]), lim, "--json" in argv)
        if r is None:
            print("Esta OS nao tem eSocial/LRE_vinculos.csv - "
                  "rode a /aft-lre-esocial antes.")
            sys.exit(3)
        sys.exit(0)

    if argv and argv[0] == "--achar":
        cnpj = re.sub(r"\D", "", argv[1]) if len(argv) > 1 else ""
        doc_lbl = "CNPJ" if len(cnpj) == 14 else "CPF" if len(cnpj) == 11 else "CNPJ/CPF"
        b = achar_sisfgts(base)
        if not b:
            print("SISFGTS: NAO ENCONTRADO")
            sys.exit(2)
        print(f"SISFGTS: {b}")
        partes = achar_partes_lre(b, cnpj)
        if not partes:
            print(f"LRE do {doc_lbl} {cnpj}: NENHUM ARQUIVO")
            sys.exit(3)
        print(f"LRE do {doc_lbl} {cnpj}: {len(partes)} parte(s)")
        for p in partes:
            print(f"  {p.name}")
        sys.exit(0)

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
        m = gerar(pasta_os, cnpj, empregador, base)
    except (FileNotFoundError, ValueError) as e:
        print(f"ERRO: {e}")
        sys.exit(4)

    print(f"LRE eSocial - {m['empregador']} ({m['cnpj']})")
    print(f"  Fonte ................. {m['partes']} parte(s) do SISFGTS")
    print(f"  Vinculos no LRE ....... {m['total']}")
    print(f"  Ativos ................ {m['ativos']}")
    print(f"  Desligados ............ {m['desligados']}")
    print(f"  PCD (ativos) .......... {m['pcd']}")
    if m["carga"]:
        print(f"  Recepcao em massa ..... {m['carga']} "
              f"({m['em_lote']} vinculos, excluidos do criterio)")
    base = m["regulares"] + m["tardios"]
    print(f"\n  -- Registro tardio: SO admissoes a partir de {m['marco']} --")
    print(f"  (marco em que o registro eletronico no LRE virou obrigatorio")
    print(f"   para todas as empresas; antes a exigencia era escalonada)")
    print(f"  Admissoes novas desde {m['marco']} ... {base}")
    print(f"    transmitidas antes da admissao .. {m['regulares']}")
    print(f"    INDICIO de registro tardio ...... {m['tardios']}"
          f"  (mesmo dia: {m['mesmoDia']} | apos: {m['apos']})")
    if m["porTipo"]:
        print("      por tipo de evento: " +
              ", ".join(f"{t or '?'}={n}" for t, n in m["porTipo"]))
    if m["preMarco"]:
        print(f"  Fora do recorte: {m['preMarco']} admitido(s) antes de "
              f"{m['marco']}")
    if m["transf"]:
        print(f"  Fora do criterio: {m['transf']} transferencia/cessao "
              f"(dtadm e a admissao original, nao ha atraso)")
    print("  criterio: admissao >= marco, tpadmissao=1 e dhrecepcao >= dtadm")
    print("  INDICIO, nao prova de falta de registro; conferir caso a caso")
    print(f"\nGravado em: {m['destino']}")
    for a in m["arquivos"]:
        print(f"  {Path(a).name}")


if __name__ == "__main__":
    main()
