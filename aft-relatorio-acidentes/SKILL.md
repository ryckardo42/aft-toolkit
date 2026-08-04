---
name: aft-relatorio-acidentes
model: sonnet
description: >
  Use quando o AFT quiser o RELATÓRIO DE ACIDENTES (histórico de CATs) de um
  CNPJ — a listagem cronológica das Comunicações de Acidente de Trabalho da
  empresa, com lesão, parte do corpo, CID, agente causador e óbitos. Acione com
  "/aft-relatorio-acidentes", "relatório de acidentes", "histórico de CATs",
  "levantar as CATs da empresa", "acidentes desse CNPJ", "puxa os acidentes",
  ou quando o AFT anexar um CSV CatsCNPJ_*.csv exportado do Portal AFT. Dois
  modos: A) CSV do Portal AFT anexado; B) varredura da base estadual de CATs
  (planilhas .xlsx do eSocial, uma por ano) filtrando pelo CNPJ. NÃO confundir
  com /aft-analise-acidente (análise aprofundada de UM acidente, IN 2/2022) —
  esta skill LEVANTA o histórico; a análise de mérito é da outra.
compatibility: macOS e Windows (Git Bash). Requer Python 3 com openpyxl (Modo B) e python-docx + a skill aft-modelo-docx (para o .docx).
---

# aft-relatorio-acidentes — Relatório de Acidentes do Trabalho (CATs) de um CNPJ
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

Gerar o **Relatório de Acidentes do Trabalho** de uma empresa: todas as CATs do
CNPJ em ordem cronológica (data, trabalhador, cargo, lesão, parte do corpo, CID,
agente causador, local, tratamento, óbitos), com resumo estatístico no topo.
Sai em **dois formatos, sempre juntos**: `.md` (para consulta rápida) e `.docx`
(padrão visual do toolkit), gravados na subpasta **`Acidentes/`** dentro da
pasta da empresa em `<OS_ATIVAS>`.

Todo o processamento é feito pelo script local
`scripts/relatorio_acidentes.py` — os arquivos de CAT contêm **nome, CPF e
dados de saúde de trabalhadores**, e nada disso sai da máquina nem passa pelo
chat.

## Regra dura de privacidade

- **Nunca leia nem ecoe no chat o conteúdo dos relatórios ou das planilhas**:
  o script já imprime o resumo agregado (totais, período, tipos, caminhos) — é
  só isso que aparece na conversa.
- Se o AFT pedir para **analisar** os acidentes no chat (padrões, gravidade,
  reincidência), trate os trabalhadores por referência posicional ("Acidente
  7", "o trabalhador do acidente 12") ou pelos tokens `[[TRAB_NN]]` — nunca
  pelo nome. A análise de mérito de UM acidente é a `/aft-analise-acidente`.

## Os dois modos

| Modo | Fonte | Quando usar |
|---|---|---|
| **A** | CSV `CatsCNPJ_<cnpj>.csv` exportado do **Portal AFT** | O AFT anexou/indicou o arquivo CSV |
| **B** | **Base estadual de CATs**: pasta com planilhas `.xlsx` do eSocial, uma por ano | O AFT deu só o CNPJ (ou o nome da empresa) |

O Modo B filtra pela coluna *"Número de inscrição do estabelecimento onde o
trabalhador exerce atividades"* e junta os resultados de todos os anos. CATs
retificadas são substituídas pela retificação; reaberturas e comunicações de
óbito aparecem anotadas.

## Fluxo de execução

**1. Resolver caminhos.** `pasta_aft.py --os-ativas` para achar `<OS_ATIVAS>`;
`python_path` vem do `aft-config.md`. Identifique a pasta da empresa em
`<OS_ATIVAS>` pelo CNPJ ou nome (confira o `memory.md`). A saída é
`<OS_ATIVAS>/<EMPRESA>/Acidentes`. Se a empresa **não tem pasta de OS**, avise
e pergunte: cadastrar com `/aft-nova-os` primeiro, ou gravar em outra pasta que
o AFT indicar.

**2. Escolher o modo.** CSV informado → Modo A. Só CNPJ → Modo B.

**3. Modo B — primeiro uso.** Confira a configuração:

```bash
python ~/.claude/skills/aft-relatorio-acidentes/scripts/relatorio_acidentes.py --mostrar-base
```

Se voltar `PASTA_CATS_NAO_DEFINIDA`, **pergunte ao AFT onde estão as planilhas
de CAT do estado dele** (uma pasta com um `.xlsx` por ano) e grave:

```bash
python ~/.claude/skills/aft-relatorio-acidentes/scripts/relatorio_acidentes.py --definir-base "<pasta indicada>"
```

Fica salvo no campo `pasta_cats:` do `aft-config.md` — nas próximas vezes não
se pergunta mais.

**4. Gerar o relatório.**

```bash
# Modo A (CSV do Portal AFT):
python ~/.claude/skills/aft-relatorio-acidentes/scripts/relatorio_acidentes.py --csv "<arquivo.csv>" --saida "<OS_ATIVAS>/<EMPRESA>/Acidentes"

# Modo B (base estadual):
python ~/.claude/skills/aft-relatorio-acidentes/scripts/relatorio_acidentes.py --cnpj <CNPJ> --saida "<OS_ATIVAS>/<EMPRESA>/Acidentes"
```

O script grava `Relatorio-Acidentes-<cnpj>.md` e `.docx` (se já existirem, faz
backup `.bak-<data-hora>` antes) e imprime o resumo agregado. No Modo A ele
extrai razão social e CNPJ dos metadados do CSV; se o AFT também informou um
CNPJ e ele divergir do arquivo, o script recusa — mostre o erro ao AFT.

**5. Reportar ao AFT.** Repita o resumo em linguagem simples: total de CATs,
quantas com óbito, período, distribuição por tipo/ano e os dois arquivos
gerados (caminho completo). **Sem nomes de trabalhadores.** Se houver óbito,
destaque e lembre que a análise aprofundada é a `/aft-analise-acidente`.

**6. Registrar na OS.** Acrescente uma linha na linha do tempo do `memory.md`
da empresa (ex.: `| <data> | Relatório de acidentes gerado: N CATs, X óbitos,
período A-B (Acidentes/Relatorio-Acidentes-<cnpj>.md) | relatorio-acidentes |`).

## Erros comuns

- `ModuleNotFoundError: openpyxl` → instale você mesmo com
  `"<python_path>" -m pip install openpyxl` e rode de novo.
- `DOCX_FALHOU` → a skill `aft-modelo-docx` não está instalada ou falta
  `python-docx` (`"<python_path>" -m pip install python-docx`). O `.md` já
  saiu; conserte e rode de novo para sair o `.docx`.
- `NENHUMA_CAT` → não há CAT do CNPJ na fonte. No Modo B, confira com o AFT se
  o CNPJ é do **estabelecimento** certo (matriz × filial mudam o final do
  CNPJ) e se as planilhas cobrem o período procurado.
- Planilha ignorada com aviso → o arquivo não tem a coluna de inscrição do
  estabelecimento; confirme com o AFT se aquele `.xlsx` é mesmo da base de CATs.

## Encadeamento

- A `/aft-preparacao-acao-fiscal` chama esta skill (FASE 4.5 dela) para levar o
  histórico de CATs ao planejamento pré-visita — mesma mecânica, mesma pasta
  `Acidentes/`, e só os agregados vão para o `preparacao.md`.
- Havendo óbito ou acidente que mereça mérito, o passo seguinte é a
  `/aft-analise-acidente`.

## Limites

- A skill **lista e resume**; não classifica infração, não emente, não decide.
  Enquadramento é com `/aft-auditoria-geral`; análise de acidente (IN 2/2022)
  é com `/aft-analise-acidente`.
- Os dados reproduzem o que foi declarado nas CATs — erros de digitação e
  campos vazios da fonte aparecem como estão (ou como `Não informado`).
