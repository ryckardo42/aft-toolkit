#!/usr/bin/env python3
"""gera_relatorio_docx.py — Relatório Final Simplificado (.docx) do /sfitweb-rel.

Uso:
    python3 gera_relatorio_docx.py <relatorio-final.json> [saida.docx]

Constrói o .docx sobre o padrão visual do toolkit (skill modelo-docx: template
oficial com o cabeçalho da auditoria + formatação institucional). Toda a
formatação vem da biblioteca modelo_docx — este script só monta as seções.

Esquema do JSON (listas vazias ou chaves ausentes omitem/ajustam a seção):
{
  "titulo":          "RELATÓRIO FINAL SIMPLIFICADO",
  "subtitulo":       "Relatório de fiscalização trabalhista — consolidação da ação fiscal",
  "unidade":         "EMPRESA LTDA — CNPJ 00.000.000/0000-00",
  "data":            "Goiânia-GO, 20 de julho de 2026",
  "identificacao":   [["Empresa Fiscalizada", "..."], ["CNPJ", "..."], ...],
  "sintese":         ["parágrafo 1", "parágrafo 2"],
  "notificacoes":    [{"codigo": "...", "tipo": "NAD", "itens": "resumo...", "lavrada": "dd/mm/aaaa"}],
  "autos_temas":     [{"tema": "...", "autos": [{"numero": "...", "ementa": "...",
                       "fundamento": "...", "descricao": "...", "constatacao": "..."}]}],
  "autos_total":     "Total: 20 autos de infração transmitidos.",
  "sem_autos":       "frase única quando não há autos transmitidos (autos_temas vazio)",
  "interdicoes":     ["parágrafo 1", ...]  (vazio → frase padrão de inexistência),
  "observacoes":     ["item 1", "item 2"]  (vazio → "Nenhuma pendência identificada."),
  "auditores":       [["Ricardo de Oliveira", "Auditor-Fiscal do Trabalho — CIF 000000"]]
}
"""
import json
import sys
from pathlib import Path

# biblioteca do padrão visual (skill modelo-docx)
for _c in (Path.home() / ".claude" / "skills" / "modelo-docx" / "scripts",
           Path(__file__).resolve().parent.parent.parent / "modelo-docx" / "scripts"):
    if (_c / "modelo_docx.py").exists():
        sys.path.insert(0, str(_c))
        break
else:
    sys.exit("ERRO: skill modelo-docx não encontrada (biblioteca modelo_docx.py). "
             "Rode /aft-atualizar para instalar as skills que faltam.")
import modelo_docx as m  # noqa: E402


def montar(dados: dict, saida: Path):
    doc = m.novo_documento()

    m.capa(doc,
           dados.get("titulo", "RELATÓRIO FINAL SIMPLIFICADO"),
           subtitulo=dados.get("subtitulo"),
           unidade=dados.get("unidade"),
           data=dados.get("data"))

    m.titulo_secao(doc, "1. Identificação da Fiscalização")
    if dados.get("identificacao"):
        m.tabela_rotulo_valor(doc, dados["identificacao"])

    m.titulo_secao(doc, "2. Síntese da Ação Fiscal")
    for par in dados.get("sintese", []):
        m.paragrafo(doc, par)

    m.titulo_secao(doc, "3. Notificações Lavradas")
    notifs = dados.get("notificacoes", [])
    if notifs:
        t = m.nova_tabela(doc, ["Notificação", "Itens notificados (resumo)", "Lavratura"],
                          larguras_cm=(4.0, 9.7, 2.8))
        for n in notifs:
            cod = [(n["codigo"], True)]
            if n.get("tipo"):
                cod.append((n["tipo"], False))
            m.linha_dados(t, [cod, n.get("itens", ""),
                              [(n.get("lavrada", ""), False)]])

    m.titulo_secao(doc, "4. Autos de Infração Lavrados")
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

    m.titulo_secao(doc, "5. Interdições e Embargos")
    inter = dados.get("interdicoes", []) or [
        "Não houve lavratura de termo de interdição ou embargo nesta ação fiscal."]
    for par in inter:
        m.paragrafo(doc, par)

    m.titulo_secao(doc, "6. Observações/Pendências")
    obs = dados.get("observacoes", [])
    if not obs:
        m.paragrafo(doc, "Nenhuma pendência identificada.")
    for item in obs:
        m.marcador(doc, item)

    m.titulo_secao(doc, "7. Auditores-Fiscais do Trabalho Envolvidos")
    auditores = dados.get("auditores", [])
    for i, (nome, cargo) in enumerate(auditores):
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
