---
name: modelo-docx
model: sonnet
description: >
  Use este skill SEMPRE que for gerar QUALQUER documento .docx no contexto do AFT Toolkit
  que não tenha template oficial próprio — relatórios avulsos, minutas, resumos, pareceres,
  documentos pedidos fora das skills, ou saídas .docx de outras skills. Acione com
  "/modelo-docx", "documento no padrão do toolkit", "gera um docx", "modelo de documento",
  ou automaticamente sempre que outra skill ou pedido avulso exigir um .docx. É o PADRÃO
  VISUAL de todo .docx do toolkit: template oficial com o cabeçalho da auditoria (AFT/SIT),
  Times New Roman 12, paleta azul institucional (#1F3864/#2E5496), corpo justificado 1,15,
  tabelas com cabeçalho azul e zebra. NÃO substitui os templates oficiais específicos do
  /aft-rt-rgi, /rt-manutencao (RT de interdição) e /autos-lavrados (Relação de autos) —
  esses continuam com seus modelos próprios.
---

# modelo-docx — o padrão de documento .docx do AFT Toolkit
**AFT Toolkit**

## O que é

Todo `.docx` gerado pelo toolkit sai com a mesma identidade visual: o cabeçalho oficial da
auditoria (logos AFT e SIT) e a formatação institucional do modelo "Relatório de
Fiscalização / Indícios". Esta skill fornece a biblioteca Python que implementa esse padrão
(`scripts/modelo_docx.py`) e o template com o cabeçalho (`scripts/template-cabecalho.docx`,
cópia de `Template/Template com cabeçalho.docx` do toolkit).

**Quando usar:** qualquer `.docx` sem template oficial próprio — em especial os documentos
avulsos que o AFT pede fora das skills (regra do perfil do auditor) e as saídas `.docx` de
skills como o `/sfitweb-rel`.

**Quando NÃO usar:** documentos com modelo oficial específico — RT de interdição/embargo
(`/aft-rt-rgi`, `/rt-manutencao`) e Relação de autos (`/autos-lavrados`) mantêm seus
templates.

## Como usar (para o Claude e para outras skills)

Importe a biblioteca — ela resolve o template sozinha e nunca altera o cabeçalho:

```python
import sys
from pathlib import Path
for c in (Path.home() / ".claude" / "skills" / "modelo-docx" / "scripts",
          Path(__file__).resolve().parent.parent.parent / "modelo-docx" / "scripts"):
    if (c / "modelo_docx.py").exists():
        sys.path.insert(0, str(c))
        break
import modelo_docx as m

doc = m.novo_documento()
m.capa(doc, "TÍTULO DO DOCUMENTO",
       subtitulo="descrição breve em itálico",
       unidade="EMPRESA LTDA — CNPJ 00.000.000/0000-00",
       data="Goiânia-GO, 20 de julho de 2026")
m.titulo_secao(doc, "1. Primeira Seção")
m.paragrafo(doc, "Corpo do texto, justificado, Times 12, entrelinhas 1,15.")
m.subtitulo(doc, "1.1 Subtítulo de nível 2")
m.marcador(doc, "item de lista com marcador")
m.tabela_rotulo_valor(doc, [("Empresa", "..."), ("CNPJ", "...")])
t = m.nova_tabela(doc, ["Coluna A", "Coluna B"], larguras_cm=(5, 11.5))
m.linha_subcabecalho(t, "Subgrupo (linha azul-média mesclada)")
m.linha_dados(t, [["Nº 123 em negrito na 1ª linha", "linha 2"],
                  {"rica": [[("Rótulo: ", True), ("valor", False)]]}])
m.assinatura(doc, "Nome do Auditor", "Auditor-Fiscal do Trabalho — CIF 000000")
doc.save("caminho/saida.docx")
```

Para um documento avulso, escreva um script curto assim (no scratchpad), rode e entregue o
`.docx` na pasta da OS (ou onde o AFT indicar). Antes de sobrescrever um `.docx` existente,
rode `_scripts/checar_arquivo_aberto.py` e faça backup com `_scripts/backup_arquivo.py`.

## A especificação (resumo)

| Elemento | Regra |
|---|---|
| Fonte | Times New Roman 12pt em tudo (corpo, títulos, tabelas) |
| Página | A4 · margens: sup/inf/dir 2 cm, esq 2,5 cm |
| Cabeçalho | o do template oficial (logos AFT/SIT) — **nunca alterado** |
| Capa | centralizada: título negrito #1F3864 · subtítulo itálico #444444 · unidade itálico preto · data #555555 · 4pt depois |
| Título de seção ("1. ...") | negrito #1F3864, à esquerda, 18pt antes / 12pt depois |
| Subtítulo ("2.1 ...") | negrito #2E5496, à esquerda, 6pt antes / 6pt depois |
| Corpo | preto, justificado, entrelinhas 1,15, 10pt depois |
| Lista | marcador •, recuo 36pt com deslocamento −18pt, 6pt depois |
| Tabela — cabeçalho | fundo #1F3864, texto branco negrito, centralizado |
| Tabela — subcabeçalho | linha mesclada, fundo #2E5496, branco negrito |
| Tabela — dados | zebra #EBF3FB / #F5F5F5 · rótulos (1ª col.) em negrito · células compactas (2pt) |
| Tabela — bordas | #AAAAAA, linha simples fina (0,125pt) |
| Assinatura | fecho + linha de underscores + nome negrito + cargo, centralizados |

A implementação completa (e canônica) é `scripts/modelo_docx.py` — na dúvida, o código vale.

## Regras

- **Este é o padrão**: skill nova ou documento avulso que gere `.docx` usa esta biblioteca.
  Não reimplemente a formatação manualmente.
- **Cabeçalho intocável**: o template é somente leitura; a biblioteca abre uma cópia e nunca
  grava sobre ele.
- Privacidade: as regras do perfil do auditor valem para o conteúdo (nunca CPF; nome de
  trabalhador só se imprescindível).
- Exemplo real de uso: `sfitweb-rel/scripts/gera_relatorio_docx.py` (Relatório Final
  Simplificado — capa, identificação, tabelas de notificações e de autos por tema,
  assinatura).
