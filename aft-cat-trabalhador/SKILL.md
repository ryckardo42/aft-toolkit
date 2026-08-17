---
name: aft-cat-trabalhador
model: sonnet
description: >
  Use quando o AFT quiser TODOS os dados das CATs de UM trabalhador específico
  — o dossiê individual de Comunicações de Acidente de Trabalho, buscado pelo
  CPF ou pelo nome completo. Acione com "/aft-cat-trabalhador", "CATs do
  trabalhador", "dossiê do trabalhador", "acidentes desse CPF", "puxa as CATs
  de [nome]", "a CAT do trabalhador X", "histórico de acidentes do
  trabalhador". Varre a base estadual de CATs (as mesmas planilhas .xlsx do
  eSocial da /aft-relatorio-acidentes) e gera um PDF pronto no leiaute do
  formulário CAT do eSocial: capa-resumo + uma ficha completa por CAT. NÃO
  confundir com /aft-relatorio-acidentes (histórico da EMPRESA, por CNPJ) nem
  com /aft-analise-acidente (análise de mérito de UM acidente, IN 2/2022).
compatibility: macOS e Windows (Git Bash). Requer Python 3 com openpyxl (leitura) e reportlab (PDF). Requer a skill aft-relatorio-acidentes instalada (mesma base de CATs).
---

# aft-cat-trabalhador — Dossiê de CATs de um trabalhador
**AFT Toolkit**

> **Onde ficam as pastas das OS.** O AFT pode ter mudado a pasta de trabalho de
> lugar. Nunca presuma `~/Documents/AFT`: resolva **uma vez, no início**, e use
> o que voltar onde este texto disser `<OS_ATIVAS>` ou `<PASTA_AFT>`.
> **Nas mensagens ao AFT, escreva o caminho de verdade.**
>
> ```bash
> python ~/.claude/skills/_scripts/pasta_aft.py --os-ativas   # -> <OS_ATIVAS>
> python ~/.claude/skills/_scripts/pasta_aft.py --path        # -> <PASTA_AFT>
> ```

## Objetivo

Reunir **todas as CATs de um trabalhador** — buscado por **CPF** ou por
**nome** — num **PDF pronto**, no leiaute do formulário CAT do eSocial: uma
capa com a identificação do trabalhador e a relação cronológica das CATs,
seguida de **uma ficha completa por CAT** (identificação, empregador,
acidentado, acidente ou doença, atestado médico). Serve para instruir a
fiscalização quando o caso gira em torno de uma pessoa: acidente grave,
denúncia, reincidência, óbito.

Todo o processamento é do script local `scripts/cat_trabalhador.py` — as
planilhas contêm **nome, CPF e dados de saúde**, e nada disso sai da máquina
nem passa por serviço externo. A fonte é a **mesma base estadual de CATs** da
`/aft-relatorio-acidentes` (`<PASTA_AFT>/CATs`, uma planilha .xlsx por ano).

## Regra dura de privacidade

- **Nunca leia nem ecoe no chat o conteúdo do PDF ou das planilhas.** O script
  imprime só o nome do trabalhador, o **CPF mascarado**, números agregados e o
  caminho do PDF — é isso que aparece na conversa, nada além.
- O CPF **completo** só existe dentro do PDF gravado em disco. Não repita CPF
  completo no chat nem em arquivos de texto da conversa.

## Fluxo de execução

**1. Resolver caminhos.** `pasta_aft.py --os-ativas` para achar `<OS_ATIVAS>`;
`python_path` vem do `aft-config.md`.

**2. Conferir a base estadual** (mesma da `/aft-relatorio-acidentes`):

```bash
python ~/.claude/skills/aft-cat-trabalhador/scripts/cat_trabalhador.py --mostrar-base
```

Se sair `PASTA_CATS_NAO_DEFINIDA`, o próprio script imprime o passo a passo
para montar a base — repasse ao AFT com o caminho real dele (é o mesmo quadro
da `/aft-relatorio-acidentes`).

**3. Decidir onde gravar.** Se o pedido vier no contexto de uma OS (empresa
identificada em `<OS_ATIVAS>`), a saída é `<OS_ATIVAS>/<EMPRESA>/Acidentes`.
Fora de OS, pergunte ao AFT onde gravar (sugira a pasta Downloads).

**4. Gerar o dossiê.**

```bash
# por CPF (com ou sem pontuação):
python ~/.claude/skills/aft-cat-trabalhador/scripts/cat_trabalhador.py --cpf <CPF> --saida "<pasta>"

# por nome (completo ou parte dele; ignora acentos e maiúsculas):
python ~/.claude/skills/aft-cat-trabalhador/scripts/cat_trabalhador.py --nome "<NOME>" --saida "<pasta>"
```

Sai `Dossie-CAT-<cpf>.pdf` na pasta indicada (backup `.bak-<data-hora>` se já
existir). CATs retificadas são substituídas pela retificação; reaberturas e
comunicações de óbito aparecem anotadas.

- **`MULTIPLOS_TRABALHADORES [...]`** — a busca por nome achou mais de uma
  pessoa. Mostre ao AFT a lista (índice, nome, CPF mascarado, nascimento,
  nº de CATs, empregadores) e pergunte qual é. Depois repita o comando com
  `--indice N`. **Nunca tente adivinhar.**
- **`NENHUM_TRABALHADOR`** — não há CAT para o CPF/nome na base. Confira com o
  AFT a grafia do nome (a busca já ignora acentos) e se as planilhas cobrem o
  período; lembre que a base é **estadual** — acidente registrado em outra UF
  não está nela.

**5. Reportar ao AFT.** Em linguagem simples: trabalhador (nome), quantas CATs,
por ano, empregador(es), se há óbito, e o caminho completo do PDF. **CPF só
mascarado.** Se houver óbito ou acidente grave, lembre que a análise de mérito
é a `/aft-analise-acidente`.

**6. Registrar na OS** (só quando a saída foi para uma pasta de OS). Linha na
linha do tempo do `memory.md` (ex.: `| <data> | Dossiê de CATs do trabalhador
[[TRAB_NN]] gerado: N CATs (Acidentes/Dossie-CAT-<cpf>.pdf) | cat-trabalhador |`)
e diário de atividades, letra **D**:

```bash
python ~/.claude/skills/_scripts/diario_registrar.py "<pasta da OS>" --tipos D --detalhe "Dossiê de CATs de trabalhador gerado"
```

## Erros comuns

- `ModuleNotFoundError: openpyxl` ou `reportlab` → instale você mesmo com
  `"<python_path>" -m pip install openpyxl reportlab` e rode de novo.
- `ERRO: a skill aft-relatorio-acidentes não foi encontrada` → o dossiê reusa
  a configuração de base dela; rode `/aft-atualizar`.
- CPF com menos de 11 dígitos → o script recusa; confira a digitação.
