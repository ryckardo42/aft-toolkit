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
esquecida, inventada ou parafraseada.

Uso:
    python preparacao_docx.py "<pasta da OS>" <conteudo.json> [saida.docx]

O JSON tem a forma:
    {
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
import json
import re
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

    dados = {
        "empregador": campo_fm(fm, "empregador") or pasta.name,
        "cnpj": campo_corpo(corpo, "CNPJ"),
        "endereco": campo_corpo(corpo, "Endereço"),
        "os": campo_corpo(corpo, "OS (SFIT)"),
        "prazos": campo_corpo(corpo, "Prazo da fiscalização"),
        "equipe": campo_corpo(corpo, "Equipe AFT"),
        "trabalhadores": campo_fm(fm, "trabalhadores"),
        "cnae": campo_fm(fm, "cnae"),
        "grau": campo_fm(fm, "grau_risco"),
        "municipio": campo_fm(fm, "municipio"),
    }
    return dados, frentes


def caminho_config() -> Path:
    """aft-config.md dentro da pasta de trabalho do AFT — que pode ter sido
    movida (HD externo, nuvem). Resolve pelo pasta_aft.py; só cai no caminho
    canônico se ele não estiver disponível."""
    try:
        sys.path.insert(0, str(Path.home() / ".claude/skills/_scripts"))
        from pasta_aft import pasta_aft  # type: ignore
        return Path(pasta_aft()) / "aft-config.md"
    except Exception:
        return Path.home() / "Documents/AFT/aft-config.md"


def le_config():
    """Nome e CIF do auditor, do aft-config.md (silencioso se faltar)."""
    cfg = caminho_config()
    if not cfg.exists():
        return "", ""
    txt = cfg.read_text(encoding="utf-8", errors="replace")
    nome = re.search(r'^nome_auditor:\s*"?([^"\n]+)"?', txt, re.M)
    cif = re.search(r'^cif:\s*"?([^"\n]+)"?', txt, re.M)
    return (nome.group(1).strip() if nome else "",
            cif.group(1).strip() if cif else "")


# --------------------------------------------------------------- montagem
def linha_os(dados):
    linhas = [("Empregador", f"{dados['empregador']}"
                             + (f" — CNPJ {dados['cnpj']}" if dados["cnpj"] else ""))]
    if dados["os"]:
        linhas.append(("Ordem de Serviço", dados["os"]))
    if dados["endereco"]:
        linhas.append(("Local da fiscalização", dados["endereco"]))
    if dados["prazos"]:
        linhas.append(("Prazo da fiscalização", dados["prazos"]))
    perfil = " · ".join(x for x in [
        f"{dados['trabalhadores']} trabalhadores" if dados["trabalhadores"] else "",
        f"CNAE {dados['cnae']}" if dados["cnae"] else "",
        f"grau de risco {dados['grau']}" if dados["grau"] else "",
    ] if x)
    if perfil:
        linhas.append(("Estabelecimento", perfil))
    if dados["equipe"]:
        linhas.append(("Equipe AFT", dados["equipe"]))
    return linhas


def gera(pasta: Path, conteudo: dict, saida: Path):
    dados, frentes = le_memory(pasta)
    cfg_frentes = conteudo.get("frentes") or {}
    nome_aft, cif_aft = le_config()

    doc = m.novo_documento()
    m.capa(doc, "TRIAGEM DA AÇÃO FISCAL",
           subtitulo="O que constatar no local e o que, só em último caso, notificar",
           unidade=(f"{dados['empregador']}"
                    + (f" — CNPJ {dados['cnpj']}" if dados["cnpj"] else "")))
    m.tabela_rotulo_valor(doc, linha_os(dados))
    m.caixa_destaque(doc, "Regra de decisão", [TESE],
                     cor_titulo=m.AZUL_ESCURO, fundo="EBF3FB", borda="9DC3E6")

    # ---- 1. Quadro de triagem
    total = sum(len(v) for v in frentes.values())
    m.titulo_secao(doc, "1. Quadro de triagem")
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

    # ---- 2. Documentos a exigir ainda na visita
    docs = [(d, cfg_frentes.get(f, {}).get("titulo") or f)
            for f in frentes
            for d in (cfg_frentes.get(f, {}).get("na_hora") or [])]
    if docs:
        m.titulo_secao(doc, "2. Documentos a exigir ainda na visita")
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

    # ---- 3. O que só então vai para o DET
    m.titulo_secao(doc, "3. O que só então vai para o DET")
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

    if nome_aft:
        m.assinatura(doc, nome_aft,
                     f"Auditor-Fiscal do Trabalho — CIF {cif_aft}" if cif_aft
                     else "Auditor-Fiscal do Trabalho", fecho="")
    doc.save(str(saida))
    return saida, total, len(frentes)


def main():
    args = sys.argv[1:]
    if len(args) not in (2, 3):
        print(__doc__.strip())
        sys.exit(1)
    pasta = Path(args[0])
    if not pasta.is_dir():
        fail(f"pasta da OS não encontrada: {pasta}")
    try:
        conteudo = json.loads(Path(args[1]).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        fail(f"não consegui ler o JSON de conteúdo: {e}")
    saida = Path(args[2]) if len(args) == 3 else pasta / "preparacao.docx"

    arq, total, nfrentes = gera(pasta, conteudo, saida)
    faltando = [f for f in le_memory(pasta)[1]
                if f not in (conteudo.get("frentes") or {})]
    print(f"gravado: {arq}")
    print(f"ementas: {total} · frentes: {nfrentes}")
    if faltando:
        print("AVISO: frentes sem conteúdo de triagem no JSON (saíram com "
              f"'(a preencher)'): {', '.join(faltando)}")


if __name__ == "__main__":
    main()
