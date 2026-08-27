---
name: aft-modelo-docx
model: sonnet
effort: low
description: >
  Use SEMPRE que for gerar qualquer documento .docx do AFT Toolkit que não
  tenha template oficial próprio — relatórios avulsos, minutas, resumos,
  pareceres, documentos pedidos fora das skills, ou saídas .docx de outras
  skills. Acione com "/aft-modelo-docx", "documento no padrão do toolkit",
  "gera um docx", "modelo de documento", ou automaticamente sempre que outra
  skill ou pedido avulso exigir um .docx. NÃO substitui os templates
  oficiais de /aft-embargo-interdicao, /aft-embargo-interdicao-manutencao e /aft-autos-lavrados.
---

# modelo-docx — o padrão de documento .docx do AFT Toolkit
**AFT Toolkit**

## O que é

Todo `.docx` gerado pelo toolkit sai com a mesma identidade visual: o cabeçalho
institucional e a formatação do modelo "Relatório de Fiscalização / Indícios". Esta skill
fornece a biblioteca Python que implementa esse padrão (`scripts/modelo_docx.py`) e o
template (`scripts/template-cabecalho.docx`, cópia de `Template/Template com
cabeçalho.docx` do toolkit).

O cabeçalho traz o brasão da República, três linhas de texto e os logos SIT e AFT:

```
Ministério do Trabalho e Emprego
Secretaria de Inspeção do Trabalho
<lotação do AFT>            (ex.: Gerência Regional do Trabalho e Emprego
                             em Nova Iguaçu - RJ)
```

As duas primeiras linhas são fixas; a terceira vem do campo `lotacao` do `aft-config.md`
(perguntado pelo `/aft-setup`). Quem monta esse cabeçalho é o `_scripts/cabecalho.py` —
os templates do repositório são neutros e ganham a lotação numa cópia local, refeita
sozinha quando a lotação muda. Sem lotação configurada, o documento sai com as duas
linhas fixas, nunca com a unidade de outra pessoa.

**Quando usar:** qualquer `.docx` sem template oficial próprio — em especial os documentos
avulsos que o AFT pede fora das skills (regra do perfil do auditor) e as saídas `.docx` de
skills como o `/aft-relatorio`.

**Quando NÃO usar:** documentos com modelo oficial específico — RT de interdição/embargo
(`/aft-embargo-interdicao`, `/aft-embargo-interdicao-manutencao`) e Relação de autos (`/aft-autos-lavrados`) mantêm seus
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
m.caixa_destaque(doc, "⚠ ALERTA", ["parágrafo em caixa vermelha para chamar a atenção"])
m.quadro_citacao(doc, "NR-01, item 1.5.3.2", ["texto do dispositivo legal citado"])
m.assinatura(doc, "Nome do Auditor", "Auditor-Fiscal do Trabalho — CIF 000000")
doc.save("caminho/saida.docx")
```

`caixa_destaque(doc, titulo, paragrafos)` é um *callout* — caixa sombreada com borda
colorida e título em negrito — para realçar algo importante (ex.: embaraço à fiscalização,
fraude). Cores padrão de alerta (vermelho sóbrio); dá para trocar via `cor_titulo`,
`fundo`, `borda`.

`quadro_citacao(doc, titulo, paragrafos)` é a mesma caixa em azul, para **citar lei ou item
de NR**. O vermelho é cor semântica, reservada a embaraço e fraude: dispositivo legal citado
não vai em caixa de alerta.

Para um documento avulso, escreva um script curto assim (no scratchpad), rode e entregue o
`.docx` na pasta da OS (ou onde o AFT indicar). Antes de sobrescrever um `.docx` existente,
rode `_scripts/checar_arquivo_aberto.py` e faça backup com `_scripts/backup_arquivo.py`.

## A especificação (resumo)

| Elemento | Regra |
|---|---|
| Fonte | corpo e tabelas em Times New Roman 12pt; título e subtítulo em Public Sans, a fonte oficial da SIT (sem ela instalada, o Word substitui sozinho) |
| Página | A4 · margens: sup/inf/dir 2 cm, esq 2,5 cm |
| Cabeçalho | institucional: brasão, Ministério do Trabalho e Emprego, Secretaria de Inspeção do Trabalho, lotação do AFT e logos SIT/AFT — montado pelo `_scripts/cabecalho.py`, **nunca escrito à mão** |
| Rodapé | fio fino #B1C0CD e "Página N" à direita, como no Papel Timbrado AFT oficial |
| Capa | centralizada: título negrito #113C5B · fio divisório dourado #F7C548 · subtítulo itálico #444444 · unidade itálico preto · data #555555 · 4pt depois |
| Título de seção ("1. ...") | negrito #113C5B, à esquerda, 18pt antes / 12pt depois |
| Subtítulo ("2.1 ...") | negrito #1266D1, à esquerda, 6pt antes / 6pt depois |
| Corpo | preto, justificado, entrelinhas 1,15, 10pt depois |
| Lista | marcador •, recuo 36pt com deslocamento −18pt, 6pt depois |
| Caixa de destaque | callout sombreado #F8EAE6, borda #D99694, título negrito #A61C1C — para alertas (embaraço, fraude) |
| Quadro de citação | callout sombreado #EAF1F8, borda e título #1266D1 — para citar lei ou item de NR |
| Tabela — cabeçalho | fundo #113C5B, texto branco negrito, centralizado |
| Tabela — subcabeçalho | linha mesclada, fundo #1266D1, branco negrito |
| Tabela — dados | zebra #EAF1F8 / #F5F5F5 · rótulos (1ª col.) em negrito · células compactas (2pt) |
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
- Exemplo real de uso: `aft-relatorio/scripts/gera_relatorio_docx.py` (Relatório Final
  Simplificado — capa, identificação, tabelas de notificações e de autos por tema,
  assinatura).
