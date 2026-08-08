#!/usr/bin/env python3
"""gera_relatorio_docx.py — Relatório Final Simplificado (.docx) do /aft-relatorio.

Uso:
    python3 gera_relatorio_docx.py <relatorio.json> [saida.docx]

Constrói o .docx sobre o padrão visual do toolkit (skill aft-modelo-docx: template
oficial com o cabeçalho da auditoria + formatação institucional). Toda a
formatação vem da biblioteca modelo_docx — este script só monta as seções.

Esquema do JSON (listas vazias ou chaves ausentes omitem/ajustam a seção):
{
  "subtitulo":       "Relatório de fiscalização trabalhista — consolidação da ação fiscal",
  "unidade":         "EMPRESA LTDA — CNPJ 00.000.000/0000-00",
  "data":            "<Município>-<UF>, 20 de julho de 2026",  # lotação do AFT (aft-config.md:
                                                                # municipio/uf) — NUNCA o município
                                                                # do estabelecimento fiscalizado
  "identificacao":   [["Empresa Fiscalizada", "..."], ["CNPJ", "..."], ...],
  "sintese":         ["parágrafo 1", "parágrafo 2"],
  "embaraco_fraude": ["parágrafo detalhando como o administrado impediu/dificultou/negou..."]
                     ou {"titulo": "...", "paragrafos": [...]}  (ausente/vazio → sem caixa),
  "notificacoes":    [{"codigo": "...", "tipo": "NAD", "itens": "resumo...", "lavrada": "dd/mm/aaaa"}],
  "autos_temas":     [{"tema": "...", "autos": [{"numero": "...", "ementa": "...",
                       "fundamento": "...", "descricao": "...", "constatacao": "..."}]}],
  "autos_total":     "Total: 20 autos de infração transmitidos.",
  "sem_autos":       "frase única quando não há autos transmitidos (autos_temas vazio)",
  "interdicoes":     ["parágrafo 1", ...]  (vazio → frase padrão de inexistência),
  "outras_ocorrencias": ["parágrafo 1", ...]  (info extra do AFT; ausente/vazio → sem seção),
  "observacoes":     ["item 1", "item 2"]  (vazio → "Nenhuma pendência identificada."),
  "auditores":       [["Ricardo de Oliveira", "Auditor-Fiscal do Trabalho — CIF 000000"]]
}

As seções são numeradas dinamicamente: a caixa de embaraço/fraude (destaque, não
numerada) entra logo após a Síntese; "Outras Ocorrências Relevantes" só aparece se
"outras_ocorrencias" tiver conteúdo.
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

import json
import sys
from pathlib import Path

# biblioteca do padrão visual (skill aft-modelo-docx)
for _c in (Path.home() / ".claude" / "skills" / "aft-modelo-docx" / "scripts",
           Path(__file__).resolve().parent.parent.parent / "aft-modelo-docx" / "scripts"):
    if (_c / "modelo_docx.py").exists():
        sys.path.insert(0, str(_c))
        break
else:
    sys.exit("ERRO: skill aft-modelo-docx não encontrada (biblioteca modelo_docx.py). "
             "Rode /aft-atualizar para instalar as skills que faltam.")
import modelo_docx as m  # noqa: E402


EMBARACO_TITULO = "⚠ EMBARAÇO À FISCALIZAÇÃO E FRAUDE (art. 630 da CLT)"

# Título fixo de todo relatório de fiscalização gerado pelo toolkit — não é
# configurável por OS nem por chamada; qualquer "titulo" em `dados` é ignorado.
TITULO_PADRAO = "RELATÓRIO DE AUDITORIA FISCAL DO TRABALHO"


def montar(dados: dict, saida: Path):
    doc = m.novo_documento()

    m.capa(doc,
           TITULO_PADRAO,
           subtitulo=dados.get("subtitulo"),
           unidade=dados.get("unidade"),
           data=dados.get("data"))

    n = [0]

    def secao(titulo):
        n[0] += 1
        m.titulo_secao(doc, f"{n[0]}. {titulo}")

    secao("Identificação da Fiscalização")
    if dados.get("identificacao"):
        m.tabela_rotulo_valor(doc, dados["identificacao"])

    secao("Síntese da Ação Fiscal")
    for par in dados.get("sintese", []):
        m.paragrafo(doc, par)

    # Destaque de embaraço/fraude (não numerado): logo após a síntese, para
    # saltar aos olhos de quem lê. Detalha como o administrado impediu/dificultou.
    ef = dados.get("embaraco_fraude")
    if ef:
        if isinstance(ef, dict):
            titulo = ef.get("titulo") or EMBARACO_TITULO
            pars = ef.get("paragrafos", [])
        else:
            titulo, pars = EMBARACO_TITULO, ef
        if pars:
            m.caixa_destaque(doc, titulo, pars)

    secao("Notificações Lavradas")
    notifs = dados.get("notificacoes", [])
    if notifs:
        t = m.nova_tabela(doc, ["Notificação", "Itens notificados (resumo)", "Lavratura"],
                          larguras_cm=(4.0, 9.7, 2.8))
        for nt in notifs:
            cod = [(nt["codigo"], True)]
            if nt.get("tipo"):
                cod.append((nt["tipo"], False))
            m.linha_dados(t, [cod, nt.get("itens", ""),
                              [(nt.get("lavrada", ""), False)]])

    secao("Autos de Infração Lavrados")
    temas = dados.get("autos_temas", [])
    if not temas:
        m.paragrafo(doc, dados.get(
            "sem_autos",
            "Não há autos de infração transmitidos no Sistema Auditor até a data deste relatório."))
    else:
        t = m.nova_tabela(doc, ["Auto de Infração", "Irregularidade constatada"],
                          larguras_cm=(4.6, 11.9))
        for tema in temas:
            m.linha_subcabecalho(t, tema["tema"])
            for auto in tema["autos"]:
                m.linha_dados(t, [
                    [(f"Nº {auto['numero']}", True),
                     (f"Ementa {auto['ementa']}", False),
                     (auto["fundamento"], False)],
                    {"rica": [[(auto["descricao"], False)],
                              [("Constatação: ", True), (auto["constatacao"], False)]]},
                ])
        if dados.get("autos_total"):
            m.paragrafo(doc, dados["autos_total"], antes=8, negrito=True)

    secao("Interdições e Embargos")
    inter = dados.get("interdicoes", []) or [
        "Não houve lavratura de termo de interdição ou embargo nesta ação fiscal."]
    for par in inter:
        m.paragrafo(doc, par)

    outras = dados.get("outras_ocorrencias", [])
    if outras:
        secao("Outras Ocorrências Relevantes da Fiscalização")
        for par in outras:
            m.paragrafo(doc, par)

    secao("Observações/Pendências")
    obs = dados.get("observacoes", [])
    if not obs:
        m.paragrafo(doc, "Nenhuma pendência identificada.")
    for item in obs:
        m.marcador(doc, item)

    secao("Auditores-Fiscais do Trabalho Envolvidos")
    for i, (nome, cargo) in enumerate(dados.get("auditores", [])):
        m.assinatura(doc, nome, cargo, fecho="É o relatório." if i == 0 else None)

    doc.save(str(saida))
    print(f"OK docx: {saida}")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    entrada = Path(sys.argv[1])
    dados = json.loads(entrada.read_text(encoding="utf-8"))
    saida = Path(sys.argv[2]) if len(sys.argv) > 2 else entrada.with_suffix(".docx")
    montar(dados, saida)
    return 0


if __name__ == "__main__":
    sys.exit(main())
