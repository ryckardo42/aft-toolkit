---
name: aft-relatorio-acidentes
model: sonnet
effort: medium
description: >
  Use quando o AFT quiser o RELATÓRIO DE ACIDENTES (histórico de CATs) de um
  CNPJ — a listagem cronológica das Comunicações de Acidente de Trabalho da
  empresa, com lesão, parte do corpo, CID, agente causador e óbitos. Acione com
  "/aft-relatorio-acidentes", "relatório de acidentes", "histórico de CATs",
  "levantar as CATs da empresa", "acidentes desse CNPJ", "puxa os acidentes",
  ou quando o AFT anexar um CSV CatsCNPJ_*.csv exportado do Portal AFT. Dois
  modos: A) CSV do Portal AFT anexado; B) varredura da base estadual de CATs
  (planilhas .xlsx do eSocial, uma por ano) filtrando pelo CNPJ. Acione TAMBÉM
  para o RELATÓRIO DE DOENÇAS OCUPACIONAIS ("doenças do trabalho da empresa",
  "LER/DORT", "doenças ocupacionais", "CATs de doença"): o modo --doencas lista
  as CATs de doença e caça CATs cadastradas como acidente típico cujo CID
  sugere doença mascarada. NÃO confundir
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
| **B** | **Base estadual de CATs**: as planilhas `.xlsx` do eSocial (uma por ano) em `<PASTA_AFT>/CATs` | O AFT deu só o CNPJ (ou o nome da empresa) |

O Modo B filtra pela coluna *"Número de inscrição do estabelecimento onde o
trabalhador exerce atividades"* e junta os resultados de todos os anos. CATs
retificadas são substituídas pela retificação; reaberturas e comunicações de
óbito aparecem anotadas.

## Modo doenças ocupacionais (`--doencas`)

Quando o AFT quiser focar a fiscalização nas **doenças do trabalho** da empresa
(e não no histórico completo de acidentes), acrescente `--doencas` a qualquer
dos dois modos. Doença ocupacional é categoria própria — e é prática conhecida
a empresa **mascarar a doença como acidente típico** (a crise aguda de LER/DORT
vira "acidente" e a empresa se poupa de rever GRO/PGR e AET). Por isso o modo
classifica as CATs em três categorias:

1. **Doenças declaradas** — CAT com tipo de acidente "Doença";
2. **Suspeitas fortes** — CAT "Típico" com CID fortemente associado a doença
   ocupacional (LER/DORT: G56, M75, M77, M65, M70, M50/M51; PAIR; transtornos
   mentais F32/F33/F41/F43; pneumoconioses; dermatoses de contato; neoplasias
   ocupacionais) **e** reforço no Agente causador ou na Situação geradora
   (esforço excessivo, movimento repetitivo, agente/situação "inexistente");
3. **Suspeitas** — CAT "Típico" com CID da lista acima sem reforço, ou com CID
   musculoesquelético inespecífico (M54, M79, M62, M53, M25) **com** reforço.

CID inespecífico sem reforço não é listado — entra só como contagem de
"indícios fracos" no resumo (senão o relatório afogaria em lombalgias comuns).
A lista de CIDs vem da Lista de Doenças Relacionadas ao Trabalho (Portaria
GM/MS nº 1.999/2023; Anexo II do Decreto nº 3.048/1999) e está no topo do
próprio script (`CID_DOENCA_ALTA` / `CID_DOENCA_MEDIA`).

```bash
# contar primeiro (segundos, nada é gravado):
python ~/.claude/skills/aft-relatorio-acidentes/scripts/relatorio_acidentes.py --cnpj <CNPJ> --doencas --contar
# gerar (sai Relatorio-Doencas-<cnpj>.md e .docx na mesma pasta Acidentes/):
python ~/.claude/skills/aft-relatorio-acidentes/scripts/relatorio_acidentes.py --cnpj <CNPJ> --doencas --saida "<OS_ATIVAS>/<EMPRESA>/Acidentes"
```

`--desde AAAA` funciona igual; `--limite`/`--auto-economico` não se aplicam (o
relatório de doenças já é um recorte, tipicamente pequeno). Se sair
`NENHUMA_DOENCA`, diga ao AFT quantas CATs a empresa tem e que nenhuma é de
doença nem suspeita. **Sempre lembre ao AFT que as suspeitas são indícios** —
a caracterização de doença ocupacional é decisão dele, caso a caso.

## Fluxo de execução

**1. Resolver caminhos.** `pasta_aft.py --os-ativas` para achar `<OS_ATIVAS>`;
`python_path` vem do `aft-config.md`. Identifique a pasta da empresa em
`<OS_ATIVAS>` pelo CNPJ ou nome (confira o `memory.md`). A saída é
`<OS_ATIVAS>/<EMPRESA>/Acidentes`. Se a empresa **não tem pasta de OS**, avise
e pergunte: cadastrar com `/aft-nova-auditoria` primeiro, ou gravar em outra pasta que
o AFT indicar.

**2. Escolher o modo.** CSV informado → Modo A. Só CNPJ → Modo B.

**3. Modo B — conferir a base estadual.** A pasta das planilhas é, por convenção
do toolkit, **`<PASTA_AFT>/CATs`** — ao lado de `OS ATIVAS`. Nada a configurar:

```bash
python ~/.claude/skills/aft-relatorio-acidentes/scripts/relatorio_acidentes.py --mostrar-base
```

- **Devolveu a pasta e o nº de planilhas** → siga para o passo 4.
- **`PASTA_CATS_NAO_DEFINIDA`** → o próprio script imprime o passo a passo para
  montar a base (ver quadro abaixo). Repasse ao AFT com o **caminho real** dele,
  e **não invente outro lugar** para a pasta.
- **Avisou que o `aft-config.md` aponta para pasta inexistente** → é resquício de
  configuração antiga; diga ao AFT que a linha `pasta_cats:` pode ser apagada, e
  siga normalmente (a convenção já assumiu).

### Como o AFT monta a base estadual (uma vez só)

> 📥 **Baixe as planilhas de CAT do seu estado e ponha em `<PASTA_AFT>/CATs`.**
>
> 1. Abra a área do ENIT no SharePoint do MTE, pasta **"CATs eSocial por UF"**:
>    <https://mtegovbr-my.sharepoint.com/shared?id=%2Fpersonal%2Fjoao%5Freis%5Ftrabalho%5Fgov%5Fbr%2FDocuments%2FDados%2FCATs%20eSocial%20por%20UF&listurl=%2Fpersonal%2Fjoao%5Freis%5Ftrabalho%5Fgov%5Fbr%2FDocuments&viewid=68794266%2Df39f%2D4837%2D9e12%2Ddd5cbd44066e&ga=1>
> 2. O link **só abre com a conta institucional (Microsoft) logada** — se pedir
>    login, é isso. Não há como o assistente entrar por você.
> 3. Entre na pasta da **sua UF** e baixe **todas as planilhas** que houver (uma
>    por ano — quanto mais anos, mais fundo vai o histórico).
> 4. Crie a pasta `CATs` dentro da sua pasta AFT (a mesma que contém `OS ATIVAS`)
>    e jogue os `.xlsx` lá dentro. Pronto — nenhuma configuração é necessária.
>
> ⚠️ Sem essas planilhas não há onde procurar: o relatório de acidentes não sai, e a
> `/aft-preparacao-acao-fiscal` monta o dossiê da visita sem os últimos acidentes da
> empresa.

O AFT que preferir manter a base em outro lugar (HD externo, pasta compartilhada)
grava o caminho uma vez, e ele passa a prevalecer sobre a convenção:

```bash
python ~/.claude/skills/aft-relatorio-acidentes/scripts/relatorio_acidentes.py --definir-base "<pasta indicada>"
```

**4. Contar antes de gerar.** Empresa grande pode ter dezenas de CATs — e um
relatório quilométrico. Rode primeiro a contagem (segundos, nada é gravado):

```bash
python ~/.claude/skills/aft-relatorio-acidentes/scripts/relatorio_acidentes.py --cnpj <CNPJ> --contar
# (Modo A: troque --cnpj pelo --csv "<arquivo.csv>")
```

Sai `CONTAGEM {"total": ..., "obitos": ..., "por_ano": {...}, ...}`.

- **Total ≤ 25** → gere direto o relatório completo (passo 5), sem perguntar.
- **Total > 25** → mostre ao AFT os números (total, óbitos, distribuição por
  ano) e pergunte, **uma única vez**, como ele quer o relatório:
  1. **Completo** — todos os acidentes;
  2. **Econômico** — só os **25 mais graves** (óbitos sempre entram; depois,
     maior tempo de afastamento; empate vai para o mais recente). O resumo
     estatístico continua cobrindo todos;
  3. **Recorte temporal** — só os acidentes a partir de um ano que ele escolher
     (a distribuição por ano ajuda: "desde 2024 são 18"). Pode combinar com o
     econômico se ainda ficar grande.

**5. Gerar o relatório.**

```bash
# Modo A (CSV do Portal AFT):
python ~/.claude/skills/aft-relatorio-acidentes/scripts/relatorio_acidentes.py --csv "<arquivo.csv>" --saida "<OS_ATIVAS>/<EMPRESA>/Acidentes"

# Modo B (base estadual):
python ~/.claude/skills/aft-relatorio-acidentes/scripts/relatorio_acidentes.py --cnpj <CNPJ> --saida "<OS_ATIVAS>/<EMPRESA>/Acidentes"
```

Conforme a escolha do passo 4, acrescente `--limite 25` (econômico) e/ou
`--desde <AAAA>` (recorte temporal). O relatório declara o recorte e o modo no
próprio Resumo — quem ler depois sabe que é uma seleção, não o total.

O script grava `Relatorio-Acidentes-<cnpj>.md` e `.docx` (se já existirem, faz
backup `.bak-<data-hora>` antes) e imprime o resumo agregado. No Modo A ele
extrai razão social e CNPJ dos metadados do CSV; se o AFT também informou um
CNPJ e ele divergir do arquivo, o script recusa — mostre o erro ao AFT.

**6. Reportar ao AFT.** Repita o resumo em linguagem simples: total de CATs,
quantas com óbito, período, distribuição por tipo/ano, o recorte/modo aplicado
(se houver) e os dois arquivos gerados (caminho completo). **Sem nomes de
trabalhadores.** Se houver óbito, destaque e lembre que a análise aprofundada é
a `/aft-analise-acidente`.

**7. Registrar na OS.** Acrescente uma linha na linha do tempo do `memory.md`
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
