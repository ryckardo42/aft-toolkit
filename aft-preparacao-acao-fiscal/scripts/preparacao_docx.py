#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""preparacao_docx.py — gera o preparacao.docx (resumo da OS para levar a campo).

O documento é uma TRIAGEM: para cada frente da OS, o que dá para constatar no
local e o que, só faltando isso, precisa ser notificado pelo DET. A tese é que a
inspeção física resolva o máximo e a notificação fique com o mínimo — documento
pedido por notificação chega depois e já ajustado.

Divisão de trabalho (padrão do toolkit): o modelo REDIGE o conteúdo da triagem e
o passa num JSON; este script RENDERIZA. Os códigos e as descrições das ementas
nunca vêm do JSON — são lidos literalmente da seção "## Ementas da OS" do
memory.md, agrupados na ordem em que aparecem. Assim nenhuma ementa é
esquecida, inventada ou parafraseada. Pela mesma razão, o grau de risco e o
dimensionamento da CIPA também não vêm do JSON: são calculados aqui, chamando os
scripts determinísticos de /aft-cnae-grau-risco-nr04 e /aft-cipa-nr05-
dimensionamento com o CNAE e o nº de trabalhadores do memory.md.

Uso:
    python preparacao_docx.py "<pasta da OS>" <conteudo.json> [saida.docx]

O JSON tem a forma:
    {
      "empresa": {
        "resumo": ["o que a empresa produz/faz, porte, unidades — um parágrafo
                    por item, redigido a partir da busca da FASE 1.2", "..."],
        "fontes": ["site oficial (empresa.com.br)", "notícia — veículo, data"]
      },
      "frentes": {
        "NR-12": {
          "titulo":    "NR-12 — Máquinas e equipamentos",   (opcional)
          "constatar": ["o que olhar/ouvir em campo", "..."],
          "na_hora":   ["documento a exigir durante a visita", "..."],
          "so_det":    ["o que só então se notifica", "..."]
        },
        "REGISTRO": { ... }
      },
      "minimo_det": ["documento que realisticamente sobra para o DET", "..."]
    }

As chaves de "frentes" são os rótulos que aparecem entre parênteses no
memory.md (REGISTRO, NR-01, NR-12...). Frente presente no memory.md e ausente
do JSON é renderizada assim mesmo, com aviso no lugar do conteúdo — nunca
some do documento.

Sempre UTF-8. Não sobrescreve nada além do .docx de saída.
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
import os
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path.home() / ".claude/skills/aft-modelo-docx/scripts"))
import modelo_docx as m  # noqa: E402

# "- [ ] 312309-0 — Deixar de adotar medidas (...). (NR-12)"
RE_EMENTA = re.compile(
    r"^-\s*\[[ xX]\]\s*(\d{6}-\d)\s*[—–-]\s*(.+?)\s*\(([^()]+)\)\s*$")
RE_FM = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)

TESE = ("Este documento parte de uma premissa: quase tudo o que esta OS manda "
        "fiscalizar pode ser constatado com os próprios olhos, durante a visita. "
        "Documento pedido por notificação chega depois, já ajustado, e adia a ação "
        "fiscal. Por isso, leia da esquerda para a direita: só se passa à última "
        "coluna quando a do meio falhar.")


def fail(msg):
    print(f"ERRO: {msg}", file=sys.stderr)
    sys.exit(1)


# ----------------------------------------------------------------- leitura
def campo_corpo(corpo, rotulo):
    """Valor de uma linha '**Rótulo:** valor' do memory.md ('' se não houver)."""
    m_ = re.search(rf"^\*\*{re.escape(rotulo)}:\*\*\s*(.+)$", corpo, re.M)
    if not m_:
        return ""
    valor = m_.group(1).strip()
    return "" if valor.startswith("_(") else valor


def campo_fm(fm, chave):
    m_ = re.search(rf"^{re.escape(chave)}:\s*(.*)$", fm, re.M)
    return m_.group(1).strip().strip('"').strip("'") if m_ else ""


def le_memory(pasta: Path):
    """Devolve (dados_da_os, frentes_ordenadas) a partir do memory.md."""
    arq = pasta / "memory.md"
    if not arq.exists():
        fail(f"memory.md não encontrado em {pasta}")
    texto = arq.read_text(encoding="utf-8", errors="replace")
    mfm = RE_FM.match(texto)
    fm, corpo = (mfm.group(1), texto[mfm.end():]) if mfm else ("", texto)

    # Ementas, na ordem do arquivo, agrupadas pela frente entre parênteses.
    frentes, dentro = {}, False
    for linha in corpo.splitlines():
        if linha.startswith("## "):
            dentro = linha.strip().lower().startswith("## ementas da os")
            continue
        if not dentro:
            continue
        mm = RE_EMENTA.match(linha.strip())
        if mm:
            cod, descricao, frente = mm.group(1), mm.group(2).strip(), mm.group(3).strip()
            frentes.setdefault(frente, []).append((cod, descricao))
    if not frentes:
        fail("nenhuma ementa encontrada na seção '## Ementas da OS' do memory.md — "
             "o preparacao.docx é o resumo das ementas da OS e não faz sentido sem elas")

    # "**OS (SFIT):** 123456 · **Demanda:** 789" -> só o nº da OS.
    os_sfit = campo_corpo(corpo, "OS (SFIT)").split("·")[0].strip()

    dados = {
        "empregador": campo_fm(fm, "empregador") or pasta.name,
        "cnpj": campo_corpo(corpo, "CNPJ"),
        "endereco": campo_corpo(corpo, "Endereço"),
        "os": os_sfit,
        "trabalhadores": campo_fm(fm, "trabalhadores"),
        "cnae": campo_fm(fm, "cnae"),
        "grau": campo_fm(fm, "grau_risco"),
        "municipio": campo_fm(fm, "municipio"),
    }
    return dados, frentes


# ------------------------------------------ grau de risco, SESMT e CIPA
def script_de_skill(rel: str):
    """Caminho de um script de outra skill do toolkit — na instalação
    (~/.claude/skills) ou no repositório, quando rodado de lá. None se faltar."""
    for base in (Path(__file__).resolve().parents[2], Path.home() / ".claude/skills"):
        alvo = base / rel
        if alvo.is_file():
            return alvo
    return None


def roda_json(script: Path, args):
    """Roda um script irmão com --json e devolve o dicionário (None se falhar).
    PYTHONIOENCODING garante UTF-8 no cano também no Windows (console cp1252)."""
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    try:
        saida = subprocess.run([sys.executable, str(script), *args, "--json"],
                               capture_output=True, text=True, encoding="utf-8",
                               env=env, timeout=60)
    except (OSError, subprocess.SubprocessError):
        return None
    if saida.returncode != 0:
        return None
    try:
        return json.loads(saida.stdout)
    except json.JSONDecodeError:
        return None


def grau_de_risco(dados):
    """(grau, cnae_info) pelo Anexo I da NR-04. O grau_risco do front-matter só
    entra quando não há CNAE para conferir. Nada aqui é estimado."""
    cnae_info, grau = None, None
    if dados["cnae"]:
        s = script_de_skill("aft-cnae-grau-risco-nr04/scripts/enquadrar_cnae.py")
        if s:
            r = roda_json(s, [dados["cnae"]])
            if r and not r.get("erro"):
                cnae_info, grau = r, r.get("grau_de_risco")
    if grau is None and dados["grau"].strip().isdigit():
        grau = int(dados["grau"].strip())
    return grau, cnae_info


def dimensiona(grau, efetivo, saude=False):
    """(cipa, sesmt) pelos scripts das skills do Quadro I da NR-05 e do Anexo II
    da NR-04 — nunca de cabeça, nunca vindo do JSON de conteúdo."""
    if grau not in (1, 2, 3, 4) or not efetivo:
        return None, None
    cipa = sesmt = None
    s = script_de_skill("aft-cipa-nr05-dimensionamento/scripts/dimensionar_cipa.py")
    if s:
        cipa = roda_json(s, [str(grau), str(efetivo)])
    s = script_de_skill("aft-dimensionamento-sesmt-nr04/scripts/dimensionar_sesmt.py")
    if s:
        sesmt = roda_json(s, [str(grau), str(efetivo)] + (["--saude"] if saude else []))
    return cipa, sesmt


def le_vinculos(caminho):
    """Relação de Empregados do Estabelecimento (SFIT), tratada localmente pelo
    vinculos_ativos.py — mesmo diretório deste script."""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from vinculos_ativos import analisa  # noqa: E402
    return analisa(Path(caminho))


# --------------------------------------------------------------- montagem
def linha_os(dados, grau, efetivo):
    linhas = [("Empregador", f"{dados['empregador']}"
                             + (f" — CNPJ {dados['cnpj']}" if dados["cnpj"] else ""))]
    if dados["os"]:
        linhas.append(("Ordem de Serviço", dados["os"]))
    if dados["endereco"]:
        linhas.append(("Local da fiscalização", dados["endereco"]))
    perfil = " · ".join(x for x in [
        f"{efetivo} trabalhadores" if efetivo else "",
        f"CNAE {dados['cnae']}" if dados["cnae"] else "",
        f"grau de risco {grau}" if grau else "",
    ] if x)
    if perfil:
        linhas.append(("Estabelecimento", perfil))
    return linhas


def secao_empresa(doc, n, empresa):
    """Seção 1 — o que se sabe da empresa antes de bater na porta."""
    m.titulo_secao(doc, f"{n}. A empresa")
    resumo = (empresa or {}).get("resumo") or []
    if not resumo:
        m.paragrafo(doc, "(a preencher)")
    for par in resumo:
        m.paragrafo(doc, par)
    fontes = (empresa or {}).get("fontes") or []
    if fontes:
        m.paragrafo(doc, "Fontes: " + " · ".join(fontes),
                    italico=True, cor=m.CINZA_CAPA2)
    m.paragrafo(doc,
                "Levantamento prévio em fontes abertas, para orientar a visita: é "
                "indício do que procurar, não prova de nada. O que vale é o "
                "constatado no local.", italico=True)


def secao_pessoal(doc, n, vinc):
    """Quadro de pessoal e quem procurar — só quando há Relação de Vínculos."""
    c = vinc["composicao"]
    m.titulo_secao(doc, f"{n}. Quadro de pessoal")
    m.paragrafo(doc,
                f"Relação de Empregados do Estabelecimento"
                + (f", emitida em {vinc['data_emissao']}" if vinc["data_emissao"] else "")
                + f": {vinc['efetivo']} empregados ({c['homens']} homens e "
                f"{c['mulheres']} mulheres). Desses, {c['pcd']} com deficiência, "
                f"{c['aprendizes']} aprendizes e {c['menores_de_18']} menores de 18 "
                "anos — recortes do mesmo efetivo, não parcelas a somar.")

    gente, sobra = [], []
    for d in vinc["sesmt_na_lista"].values():
        for p in d["pessoas"]:
            gente.append(("SESMT", p["nome"], p["ocupacao"]))
    for papel, d in vinc["interlocutores"].items():
        for p in d["pessoas"]:
            gente.append((papel, p["nome"], p["ocupacao"]))
        if d["total"] > len(d["pessoas"]):
            sobra.append(f"{papel}: mais {d['total'] - len(d['pessoas'])} no mesmo nível")
    if gente:
        m.paragrafo(doc,
                    "Quem procurar no estabelecimento — nomes tirados da própria "
                    "Relação de Vínculos, para você chamar pelo nome e ouvir quem "
                    "de fato responde por cada área:")
        t = m.nova_tabela(doc, ["Papel", "Nome", "Ocupação na Relação"],
                          larguras_cm=(3.4, 6.6, 6.5))
        for papel, nome, ocup in gente:
            m.linha_dados(t, [papel, nome, ocup])
        if sobra:
            m.paragrafo(doc, "Na Relação constam ainda — " + " · ".join(sobra)
                             + ". Peça a quem responde pela área no dia da visita.",
                        italico=True)

    for obs in vinc["observacoes"]:
        m.caixa_destaque(doc, "Divergência na Relação de Vínculos", [obs])


def secao_risco_cipa(doc, n, dados, grau, cnae_info, cipa, sesmt, vinc):
    """Grau de risco (NR-04), SESMT devido (Anexo II) e CIPA devida (Quadro I)."""
    m.titulo_secao(doc, f"{n}. Grau de risco, SESMT e CIPA")
    if cnae_info:
        m.paragrafo(doc,
                    f"CNAE {cnae_info['classe_cnae']} — {cnae_info['denominacao']}. "
                    f"Grau de risco {cnae_info['grau_de_risco']}, pelo Anexo I da NR-04.")
    else:
        # Por que não se conferiu no Anexo I: faltou o CNAE ou ele não foi
        # localizado lá (código errado). São problemas diferentes.
        motivo = (f"o CNAE {dados['cnae']} não foi localizado nesse anexo — "
                  "confira o código" if dados["cnae"]
                  else "não há CNAE registrado no memory.md")
        if grau:
            m.paragrafo(doc, f"Grau de risco {grau}, informado no memory.md e não "
                             f"conferido no Anexo I da NR-04: {motivo}.")
        else:
            m.paragrafo(doc, "Grau de risco não apurado no Anexo I da NR-04: "
                             f"{motivo}.")

    if not (cipa or sesmt):
        m.paragrafo(doc,
                    "SESMT e CIPA não dimensionados — falta o nº de trabalhadores "
                    "do estabelecimento ou o grau de risco. Levante o efetivo na "
                    "visita e rode /aft-dimensionamento-sesmt-nr04 e "
                    "/aft-cipa-nr05-dimensionamento.")
        return

    # ---- SESMT: devido pelo Anexo II x o que consta da Relação de Vínculos
    if sesmt:
        m.subtitulo(doc, "SESMT — Anexo II da NR-04")
        m.paragrafo(doc,
                    f"Para {sesmt['num_trabalhadores']} trabalhadores e grau de risco "
                    f"{sesmt['grau_de_risco']} (faixa {sesmt['faixa']}), o SESMT "
                    "exigido é:")
        na_lista = (vinc or {}).get("sesmt_na_lista") or {}
        cab = ["Profissional", "Exigido"] + (["Na Relação", "Situação"] if na_lista else [])
        larg = (7.0, 4.0, 2.7, 2.8) if na_lista else (9.5, 7.0)
        t = m.nova_tabela(doc, cab, larguras_cm=larg)
        for rotulo, d in sesmt["dimensionamento"].items():
            exigido = d["quantidade"]
            texto = (f"{exigido}" + (f" ({d['regime']})" if d.get("regime") else "")
                     if exigido else "não exigido")
            linha = [rotulo, texto]
            if na_lista:
                tem = na_lista.get(rotulo, {}).get("quantidade", 0)
                if exigido and tem < exigido:
                    situacao = f"faltam {exigido - tem}"
                elif exigido:
                    situacao = "atende"
                else:
                    situacao = "—"
                linha += [str(tem), situacao]
            m.linha_dados(t, linha)
        for linha in sesmt.get("memoria_de_calculo") or []:
            m.paragrafo(doc, linha, italico=True, depois=4)
        if na_lista:
            m.paragrafo(doc,
                        "A coluna \"Na Relação\" conta as ocupações declaradas na "
                        "Relação de Vínculos deste estabelecimento — é indício, não "
                        "conclusão: o profissional pode estar registrado com outra "
                        "ocupação, lotado em outro estabelecimento ou o serviço pode "
                        "ser comum a mais de uma empresa. Exija em campo os documentos "
                        "do SESMT e confirme antes de concluir por subdimensionamento.")
        else:
            m.paragrafo(doc,
                        "Confronte esses números com os profissionais efetivamente "
                        "lotados no estabelecimento, exigindo a documentação do SESMT "
                        "durante a visita.")
        m.subtitulo(doc, "CIPA — Quadro I da NR-05")

    if not cipa:
        m.paragrafo(doc, "CIPA não dimensionada — falta o nº de trabalhadores ou o "
                         "grau de risco.")
        return

    q = cipa["quadro_i_por_bancada"]
    t = cipa["composicao_paritaria_total"]
    m.paragrafo(doc,
                f"Para {cipa['num_empregados']} trabalhadores e grau de risco "
                f"{cipa['grau_de_risco']} (faixa {cipa['faixa']} do Quadro I da "
                "NR-05), a CIPA devida é:")
    tab = m.nova_tabela(doc, ["", "Efetivos", "Suplentes"],
                        larguras_cm=(7.3, 4.6, 4.6))
    m.linha_dados(tab, ["Quadro I — por representação",
                        [str(q["efetivos"])], [str(q["suplentes"])]])
    m.linha_dados(tab, ["Eleitos pelos empregados",
                        [str(t["efetivos_eleitos_pelos_empregados"])],
                        [str(t["suplentes_eleitos_pelos_empregados"])]])
    m.linha_dados(tab, ["Designados pelo empregador",
                        [str(t["efetivos_designados_pelo_empregador"])],
                        [str(t["suplentes_designados_pelo_empregador"])]])
    m.linha_dados(tab, ["TOTAL (comissão paritária)",
                        [str(t["efetivos_total"])], [str(t["suplentes_total"])]])
    for linha in cipa.get("memoria_de_calculo") or []:
        m.paragrafo(doc, linha, italico=True, depois=4)
    origem = ("da Relação de Vínculos"
              + (f", emitida em {vinc['data_emissao']}" if vinc.get("data_emissao") else "")
              if vinc else "informado antes da visita")
    m.paragrafo(doc,
                f"O nº de trabalhadores usado nos dois dimensionamentos vem {origem} "
                "— confirme o efetivo real no local e refaça o cálculo se ele mudar "
                "de faixa. Compare a CIPA acima com a ata de eleição e a composição "
                "em exercício, apontando o déficit em cada representação.")


def gera(pasta: Path, conteudo: dict, saida: Path, vinculos=None, saude=False):
    dados, frentes = le_memory(pasta)
    cfg_frentes = conteudo.get("frentes") or {}
    vinc = le_vinculos(vinculos) if vinculos else None

    # O efetivo da Relação de Vínculos prevalece sobre o memory.md: é o número
    # que a própria base do SFIT devolveu, e é ele que dimensiona SESMT e CIPA.
    efetivo = (vinc or {}).get("efetivo")
    if not efetivo and dados["trabalhadores"].strip().isdigit():
        efetivo = int(dados["trabalhadores"].strip())
    grau, cnae_info = grau_de_risco(dados)
    cipa, sesmt = dimensiona(grau, efetivo, saude)

    doc = m.novo_documento()
    m.capa(doc, "TRIAGEM DA AÇÃO FISCAL",
           subtitulo="O que constatar no local e o que, só em último caso, notificar",
           unidade=(f"{dados['empregador']}"
                    + (f" — CNPJ {dados['cnpj']}" if dados["cnpj"] else "")))
    m.tabela_rotulo_valor(doc, linha_os(dados, grau, efetivo))
    m.caixa_destaque(doc, "Regra de decisão", [TESE],
                     cor_titulo=m.AZUL_ESCURO, fundo="EBF3FB", borda="9DC3E6")

    n = 1
    secao_empresa(doc, n, conteudo.get("empresa"))
    if vinc:
        n += 1
        secao_pessoal(doc, n, vinc)
    n += 1
    secao_risco_cipa(doc, n, dados, grau, cnae_info, cipa, sesmt, vinc)

    # ---- Quadro de triagem
    total = sum(len(v) for v in frentes.values())
    n += 1
    m.titulo_secao(doc, f"{n}. Quadro de triagem")
    m.paragrafo(doc,
                f"A OS relaciona {total} ementas a fiscalizar, em {len(frentes)} "
                "frentes. A coluna do meio é onde a ação fiscal se resolve.")
    t = m.nova_tabela(doc, ["Ementas", "Constatar no local", "Só notificar se"],
                      larguras_cm=(2.6, 9.4, 4.5))
    for frente, ementas in frentes.items():
        cfg = cfg_frentes.get(frente, {})
        m.linha_subcabecalho(t, cfg.get("titulo") or frente)
        m.linha_dados(t, [
            [c for c, _ in ementas],
            cfg.get("constatar") or ["(a preencher)"],
            cfg.get("so_det") or ["(a preencher)"],
        ])

    # ---- Documentos a exigir ainda na visita
    docs = [(d, cfg_frentes.get(f, {}).get("titulo") or f)
            for f in frentes
            for d in (cfg_frentes.get(f, {}).get("na_hora") or [])]
    if docs:
        n += 1
        m.titulo_secao(doc, f"{n}. Documentos a exigir ainda na visita")
        m.paragrafo(doc,
                    "Peça estes documentos assim que chegar, antes de percorrer o "
                    "estabelecimento: costumam existir no local e, em mãos, permitem "
                    "confrontar documento e realidade no mesmo ato.")
        # A 1ª coluna fica vazia de propósito: impressa, a borda da tabela já é a
        # caixinha onde o AFT marca à caneta (não depende de glifo da fonte).
        td = m.nova_tabela(doc, ["OK", "Documento", "Frente"],
                           larguras_cm=(1.2, 10.8, 4.5))
        for texto, frente in docs:
            m.linha_dados(td, ["", texto, frente])

    # ---- O que só então vai para o DET
    n += 1
    m.titulo_secao(doc, f"{n}. O que só então vai para o DET")
    m.paragrafo(doc,
                "Encerrada a visita, notifique apenas o que efetivamente não foi "
                "possível obter ou verificar no local. A lista abaixo é o teto, "
                "não a meta:")
    for item in conteudo.get("minimo_det") or ["(a preencher)"]:
        m.marcador(doc, item)
    m.paragrafo(doc,
                "A notificação é gerada pela skill /aft-NAD, com a ementa e o prazo "
                "corretos. Tudo o que foi constatado em campo segue para "
                "/aft-inspecao-fisica e /aft-auditoria-geral.")

    doc.save(str(saida))
    return {"arquivo": saida, "ementas": total, "frentes": len(frentes),
            "grau": grau, "efetivo": efetivo, "cipa": cipa, "sesmt": sesmt,
            "vinculos": vinc}


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pasta", help="pasta da OS (com o memory.md)")
    ap.add_argument("conteudo", help="JSON com o conteúdo redigido pelo modelo")
    ap.add_argument("saida", nargs="?", help="destino (padrão: <pasta>/preparacao.docx)")
    ap.add_argument("--vinculos", help="Relação de Empregados do Estabelecimento (PDF "
                                       "do SFIT) — efetivo, SESMT e interlocutores")
    ap.add_argument("--saude", action="store_true",
                    help="estabelecimento de saúde (Observações A e B do Anexo II)")
    a = ap.parse_args()

    pasta = Path(a.pasta)
    if not pasta.is_dir():
        fail(f"pasta da OS não encontrada: {pasta}")
    try:
        conteudo = json.loads(Path(a.conteudo).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        fail(f"não consegui ler o JSON de conteúdo: {e}")
    if a.vinculos and not Path(a.vinculos).is_file():
        fail(f"Relação de Vínculos não encontrada: {a.vinculos}")
    saida = Path(a.saida) if a.saida else pasta / "preparacao.docx"

    r = gera(pasta, conteudo, saida, vinculos=a.vinculos, saude=a.saude)
    arq, total, nfrentes = r["arquivo"], r["ementas"], r["frentes"]
    grau, cipa, sesmt, vinc = r["grau"], r["cipa"], r["sesmt"], r["vinculos"]
    faltando = [f for f in le_memory(pasta)[1]
                if f not in (conteudo.get("frentes") or {})]
    print(f"gravado: {arq}")
    print(f"ementas: {total} · frentes: {nfrentes}")
    if cipa:
        q = cipa["quadro_i_por_bancada"]
        t = cipa["composicao_paritaria_total"]
        print(f"grau de risco: {grau} · CIPA ({cipa['num_empregados']} "
              f"trabalhadores, faixa {cipa['faixa']}): Quadro I "
              f"{q['efetivos']} efetivos / {q['suplentes']} suplentes por "
              f"bancada — total paritário {t['efetivos_total']} efetivos e "
              f"{t['suplentes_total']} suplentes")
    else:
        print(f"grau de risco: {grau or 'não apurado (falta CNAE no memory.md)'} · "
              "CIPA: não calculada (falta nº de trabalhadores ou grau de risco)")
    if sesmt:
        exigido = {k: v["quantidade"] for k, v in sesmt["dimensionamento"].items()
                   if v["quantidade"]}
        print(f"SESMT exigido (faixa {sesmt['faixa']}): "
              + ("; ".join(f"{q} {k}" for k, q in exigido.items()) or "nenhum profissional"))
    if vinc:
        c = vinc["composicao"]
        tem = {k: v["quantidade"] for k, v in vinc["sesmt_na_lista"].items()
               if v["quantidade"]}
        print(f"vínculos: efetivo {vinc['efetivo']} ({c['homens']}H/{c['mulheres']}M · "
              f"PCD {c['pcd']} · aprendizes {c['aprendizes']} · menores {c['menores_de_18']})"
              f" · SESMT na lista: " + ("; ".join(f"{q} {k}" for k, q in tem.items()) or "nenhum"))
        memoria = le_memory(pasta)[0]["trabalhadores"].strip()
        if memoria.isdigit() and int(memoria) != vinc["efetivo"]:
            print(f"AVISO: o memory.md diz {memoria} trabalhadores e a Relação de "
                  f"Vínculos diz {vinc['efetivo']} — o documento usou {vinc['efetivo']}. "
                  "Atualize o memory.md.")
        for obs in vinc["observacoes"]:
            print(f"AVISO: {obs}")
    if not ((conteudo.get("empresa") or {}).get("resumo")):
        print("AVISO: sem 'empresa.resumo' no JSON — a seção 1 saiu com "
              "'(a preencher)'. Faça a busca da FASE 1.2 antes de gerar.")
    if faltando:
        print("AVISO: frentes sem conteúdo de triagem no JSON (saíram com "
              f"'(a preencher)'): {', '.join(faltando)}")


if __name__ == "__main__":
    main()
