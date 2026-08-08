#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""anexa_pagina_anexos.py — acrescenta ao .docx do relatório (skill /aft-relatorio)
a página final "ANEXOS - Autos de Infração", que apresenta o PDF único gerado pela
skill /aft-autos-pdf-reunidos como anexo do relatório.

Uso:
    python3 anexa_pagina_anexos.py <relatorio.docx> <autos-reunidos.json> [nome-do-pdf-anexo]

  <autos-reunidos.json>: o JSON impresso pelo reune_autos_pdf.py (redirecionado
  para arquivo). Dele saem o modo (paginas_anexo_limite), as páginas cortadas e
  as páginas omitidas por repetição de anexo.

  [nome-do-pdf-anexo]: nome do PDF citado no corpo da página — a via que acompanha
  o relatório, normalmente "RI <ri> - autos e anexos.pdf". Padrão:
  "autos-reunidos.pdf".

A página entra após o fim do relatório, com quebra de página, no padrão visual
do toolkit (biblioteca modelo_docx). Idempotente: se o documento já tem a
página "ANEXOS - Autos de Infração", ela é removida e regravada — rodar duas
vezes não duplica.

ATENÇÃO (quem chama garante): faça backup do .docx antes (backup_arquivo.py) e
confira que ele não está aberto no Word (checar_arquivo_aberto.py).
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

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        try:
            _stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

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
from docx import Document  # noqa: E402

TITULO = "ANEXOS - Autos de Infração"


def montar_textos(dados: dict) -> list[str]:
    """Observações da página, na ordem: corte do modo econômico (se houver),
    Núcleo de Multas (idem), repetidos (sempre) e o total de páginas de fora."""
    limite = dados.get("paginas_anexo_limite")
    cortadas = dados.get("paginas_cortadas") or 0
    repetidas = dados.get("paginas_repetidas_omitidas") or 0

    obs = []
    if limite:
        obs.append("Para reduzir o tamanho do arquivo, os anexos dos autos de "
                   f"infração foram limitados a até {limite} páginas.")
        obs.append("Caso o interessado precise do inteiro teor dos anexos, "
                   "solicitar as informações completas ao Núcleo de Multas.")
    obs.append("Anexos que se repetem em mais de um auto de infração são "
               "apresentados uma única vez, no primeiro auto correspondente.")

    total_fora = cortadas + repetidas
    if total_fora:
        partes = []
        if cortadas:
            partes.append(f"{cortadas} pelo limite de páginas por anexo")
        if repetidas:
            partes.append(f"{repetidas} por repetição de anexo")
        obs.append(f"No total, {total_fora} páginas dos arquivos originais "
                   f"deixaram de ser incluídas ({' e '.join(partes)}).")
    return obs


def remover_pagina_existente(doc) -> bool:
    """Remove a página ANEXOS anterior (do parágrafo do título ao fim do
    documento — a página é sempre a última). Retorna True se removeu."""
    corpo = doc.paragraphs
    idx = next((i for i, p in enumerate(corpo) if p.text.strip() == TITULO), None)
    if idx is None:
        return False
    for p in corpo[idx:]:
        p._element.getparent().remove(p._element)
    return True


def main() -> int:
    if len(sys.argv) not in (3, 4):
        print("Uso: anexa_pagina_anexos.py <relatorio.docx> "
              "<autos-reunidos.json> [nome-do-pdf-anexo]", file=sys.stderr)
        return 2

    docx_path, json_path = Path(sys.argv[1]), Path(sys.argv[2])
    nome_anexo = sys.argv[3] if len(sys.argv) == 4 else "autos-reunidos.pdf"
    if not docx_path.is_file():
        print(f"ERRO: relatório não encontrado: {docx_path}", file=sys.stderr)
        return 1
    if not json_path.is_file():
        print(f"ERRO: JSON da reunião de autos não encontrado: {json_path}",
              file=sys.stderr)
        return 1

    dados = json.loads(json_path.read_text(encoding="utf-8"))
    if dados.get("errors"):
        print("ERRO: o JSON registra falha na reunião dos autos — corrija-a "
              "antes de anexar a página ao relatório.", file=sys.stderr)
        return 1

    doc = Document(str(docx_path))
    substituiu = remover_pagina_existente(doc)

    titulo = m.paragrafo(doc, TITULO, antes=18, depois=12, alinh=m.CENTRO,
                         negrito=True, cor=m.AZUL_ESCURO)
    titulo.paragraph_format.page_break_before = True

    m.paragrafo(doc, "Relação dos autos de infração completos lavrados e "
                     "respectivos anexos.")
    m.paragrafo(doc, f"A relação integra o arquivo {nome_anexo}, que "
                     "acompanha este relatório.")
    for i, texto in enumerate(montar_textos(dados), start=1):
        m.paragrafo(doc, f"Observação {i}: {texto}")

    doc.save(str(docx_path))
    acao = "substituída" if substituiu else "acrescentada"
    print(f"OK: página \"{TITULO}\" {acao} em {docx_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
