---
name: aft-rt-rgi
description: >
  Use este skill SEMPRE que o Auditor-Fiscal do Trabalho (AFT) pedir para criar, gerar, redigir
  ou montar um Relatório Técnico para Interdição e/ou Embargo (RT). Acione quando o usuário
  mencionar "relatório técnico de interdição", "relatório técnico de embargo", "RT de interdição",
  "RT para interdição", "gerar o relatório técnico", "montar o RT", "relatório técnico do termo",
  "AFT-RT-RGI" ou expressões equivalentes. O skill produz um documento .docx completo seguindo
  o modelo oficial (template incluído no toolkit), preenchendo os dados do empregador, ação
  fiscal, objetos interditados, irregularidades, fatores de risco, medidas de proteção,
  documentos solicitados e conclusão, mantendo todo o conteúdo fixo (cabeçalho, seções legais,
  imagens, tabelas NR-3 e instruções de levantamento). Logo após o RT, a skill OBRIGATORIAMENTE
  redige os autos de infração derivados das ementas da seção 4 (um auto por ementa, no formato
  consumido por /gera-ai) e salva tudo na pasta `Autos TE-TI DD-MM/` da OS.
---

# aft-rt-rgi — Relatório Técnico para Interdição e Embargo
**AFT Toolkit**

## Objetivo

Gerar um **Relatório Técnico para Interdição e/ou Embargo** em formato `.docx`, baseado no
modelo oficial incluído no toolkit (`~/.claude/skills/aft-rt-rgi/template.docx`,
modelo da SRTE/GO — adapte cabeçalho/cidade à sua SRTE se necessário). O documento mantém
TODO o conteúdo fixo do modelo (cabeçalho, logotipos, textos legais, citações doutrinárias,
tabelas NR-3, instruções de suspensão, nota sobre SEI) e preenche apenas as partes variáveis
com os dados fornecidos pelo AFT.

---

## Fluxo de execução

### 1. Coletar os dados necessários

Solicite ao usuário (ou extraia do contexto/PDFs anexados/`inspecao-fisica.md`/`memory.md`
da OS) as seguintes informações:

**Identificação (capa):**
- Número do Termo de Interdição (substitui `XXXXX` no título)
- Nome do empregador (substitui `XXXX` em EMPREGADOR)
- CNPJ (substitui `XXXXX` em CNPJ)

**Seção 1 — OBJETIVO (complemento):**
- Data exata da inspeção física. Extraia do contexto disponível (`inspecao-fisica.md`,
  `memory.md`, PDFs anexados). Se não encontrar em lugar algum, **pergunte ao usuário
  antes de continuar**.

**Seção 2 — DA AÇÃO FISCAL:**
O texto é fixo (citações da OIT, Portaria MTE 1.719/2014, etc.). O único ajuste necessário é
adaptar a NR citada ao caso concreto (padrão: NR-12; substituir se for outra). O último
parágrafo da seção 2 menciona o preposto e a análise — ajuste se necessário.

**Seção 3 — OBJETOS INTERDITADO:**
- Número do objeto (ex: 1, 2...)
- Descrição do objeto (ex: ATIVIDADE — Paralisação: TOTAL | ou MÁQUINA: ..., SETOR: ...)

**Seção 4 — IRREGULARIDADES:**

A seção 4 lista as ementas das infrações, uma por linha, no formato:

```
XXXXXX-X - [Descrição completa da ementa]. Capitulação: [fundamento legal].
```

Para montar esse conteúdo, siga o sub-fluxo abaixo **antes de editar o XML**:

**4a. Identificar as irregularidades** a partir do contexto (`inspecao-fisica.md`, PDFs
anexados, descrição do AFT). Liste cada irregularidade de forma objetiva e separada.

**4b. Resolver as ementas (3 camadas):**

1. **NotebookLM** (se configurado pelo `/aft-setup`): leia
   `~/.claude/skills/config/notebooks.json`, identifique a key do notebook
   `ementario-sst` e a key da NR específica do caso (ex: `nr-12`, `nr-13`, `nr-35`).
   Para cada irregularidade, pergunte (uma consulta por irregularidade, em paralelo):
   ```bash
   notebooklm ask "Qual é o código da ementa no formato XXXXXX-X, a descrição completa da ementa e a capitulação legal para a seguinte infração: [descrição objetiva da irregularidade]?" --notebook [notebook_id] --json
   ```
2. **Ementário no Google Drive** (manual): oriente o AFT a abrir
   https://drive.google.com/drive/folders/1bktX9TkDIoix4iQuca3Yr5aWCfv97GSg?usp=sharing
   (pasta `EMENTAS SST` → `ementasNRXX.md`) e colar o trecho da ementa.
3. **Pedir ao AFT** o código/descrição/capitulação diretamente.

Se nenhuma camada retornar código de ementa para alguma irregularidade, insira
`[EMENTA A PREENCHER]` naquela linha e informe o AFT ao final da execução.

**4c. Montar o bloco** como **parágrafos `<w:p>` separados com bullet**, um por ementa.
Cada ementa deve ser um parágrafo independente — NUNCA um único `<w:t>` com `\n\n`.

Formato visual final (um bullet por ementa, logo abaixo do cabeçalho "4. IRREGULARIDADES:"):

```
• XXXXXX-X - [Descrição da ementa]. Capitulação: [fundamento legal].
• XXXXXX-X - [Descrição da ementa]. Capitulação: [fundamento legal].
```

**XML correto para cada ementa** (substituir o parágrafo vazio `39A36EBD` por N parágrafos):

```xml
<w:p w14:paraId="XXXXXXXX" w14:textId="77777777"
     w:rsidR="00B0080B" w:rsidRDefault="00B0080B" w:rsidP="00CD6010">
  <w:pPr>
    <w:pStyle w:val="Corpodetexto"/>
    <w:numPr>
      <w:ilvl w:val="2"/>
      <w:numId w:val="1"/>
    </w:numPr>
    <w:spacing w:line="360" w:lineRule="auto"/>
    <w:ind w:right="424"/>
    <w:jc w:val="both"/>
    <w:rPr>
      <w:rFonts w:ascii="Tahoma" w:hAnsi="Tahoma" w:cs="Tahoma"/>
      <w:sz w:val="22"/><w:szCs w:val="22"/>
    </w:rPr>
  </w:pPr>
  <w:r>
    <w:rPr>
      <w:rFonts w:ascii="Tahoma" w:hAnsi="Tahoma" w:cs="Tahoma"/>
      <w:sz w:val="22"/><w:szCs w:val="22"/>
    </w:rPr>
    <w:t xml:space="preserve">XXXXXX-X - [Descrição]. Capitulação: [fundamento].</w:t>
  </w:r>
</w:p>
```

**Restrições críticas para `w14:paraId`:**
- Deve ser um hex de 8 dígitos com valor **< 0x80000000** (ex: `03091C72`)
- Nunca usar UUID completo — gerar com `random.randint(1, 0x7FFFFFFE)` formatado como `{n:08X}`
- Valor ≥ 0x80000000 causa falha de validação do DOCX

**Seção 5 — FATORES DE RISCO E/OU RISCOS RELACIONADOS:**
- Fator de Risco e excesso de risco (ex: Extremo/Significativo)
- Descrição do risco
- Fundamentação do risco atual (situação encontrada)
- Fundamentação do risco de referência (situação objetivo)

**Seção 6 — MEDIDAS DE PROTEÇÃO A ADOTAR:**
- Lista das medidas (uma por parágrafo de tabulação)

**Seção 7 — DOCUMENTOS SOLICITADOS:**
- Lista dos documentos (um por parágrafo de tabulação)

**Seção 8 — CONCLUSÃO/OBSERVAÇÃO:**
- Texto de conclusão (breve, objetivo)

**Rodapé:**
- Cidade e data (substitui `XXXXX-GO, XX/XX/2026` — use o município/UF do `aft-config.md`)
- Nome do AFT (substitui `XXXXXXXX` — use `nome_auditor` do `aft-config.md`)

Se algum dado não for fornecido, use um placeholder claro como `[PREENCHER]`.

---

### 2. Preparar a área de trabalho

```bash
mkdir -p /tmp/RT_temp
cp ~/.claude/skills/aft-rt-rgi/template.docx /tmp/RT_temp/template.docx
```

> No Windows com Git Bash, `/tmp` existe e funciona normalmente.

### 3. Desempacotar o template

```bash
python ~/.claude/skills/_scripts/docx_unpack.py /tmp/RT_temp/template.docx /tmp/RT_temp/unpacked/
```

### 4. Substituir os placeholders no XML

Edite `/tmp/RT_temp/unpacked/word/document.xml` usando a tool Edit para substituir os
seguintes placeholders pelo conteúdo fornecido pelo usuário:

| Placeholder no XML | Campo |
|---|---|
| `TERMO DE INTERDIÇÃO Nº XXXXX` | Nº do Termo |
| `XXXX` (em EMPREGADOR) | Nome do empregador |
| `XXXXX` (em CNPJ) | CNPJ |
| Após o texto fixo da seção 1 (OBJETIVO) | Inserir frase: `"A inspeção física foi realizada em DD/MM/YYYY com subseqüente análise de documentos necessários para elaboração deste relatório técnico."` |
| `OBJETO: 1 – ATIVIDADE - Paralisação: TOTAL` | Descrição do(s) objeto(s) interditado(s) |
| Parágrafo vazio após a metodologia NR-3 (seção 4) | Bloco de ementas montado no sub-fluxo 4a–4c |
| `Fator de Risco : excesso de risco` | Fator de risco |
| `Descrição:` (linha em branco após) | Descrição do risco |
| `Fundamentação do risco atual:` (linha em branco) | Fundamentação do risco atual |
| `Fundamentação do risco de referência` (linha em branco) | Fundamentação do risco de referência |
| Parágrafos vazios de tabulação em seção 6 | Medidas de proteção |
| Parágrafos vazios de tabulação em seção 7 | Documentos solicitados |
| Parágrafo vazio após "8. CONCLUSÃO/OBSERVAÇÃO:" | Texto de conclusão |
| `XXXXX-GO, XX/XX/2026` | Cidade e data |
| `XXXXXXXX` (linha do nome do auditor) | Nome do AFT |

**IMPORTANTE:** As seções fixas (citações doutrinárias, tabelas NR-3, texto sobre DO PEDIDO DE
SUSPENSÃO, instruções do SEI, assinatura padrão "Auditor-Fiscal do Trabalho") NÃO devem ser
alteradas.

Para adicionar múltiplos objetos na seção 3, replique a estrutura de parágrafo existente.
Para adicionar múltiplas medidas/documentos nas seções 6 e 7, insira novos parágrafos com a
mesma formatação (tabulação).

### 5. Remontar e validar o documento

```bash
python ~/.claude/skills/_scripts/docx_pack.py /tmp/RT_temp/unpacked/ /tmp/RT_temp/RT_Interdicao.docx
```

O `docx_pack.py` valida o XML antes de empacotar — se acusar erro, corrija o
`document.xml` e rode de novo.

### 6. Salvar na pasta da OS

Calcule a data de hoje (`date +%d-%m`) e crie a pasta de saída:

```bash
mkdir -p ~/Documents/AFT/"OS ATIVAS"/"[PASTA_EMPRESA]"/"Autos TE-TI [DD-MM]"/
cp /tmp/RT_temp/RT_Interdicao.docx ~/Documents/AFT/"OS ATIVAS"/"[PASTA_EMPRESA]"/"Autos TE-TI [DD-MM]"/
```

Informe o caminho ao AFT — ele revisa o `.docx` no Word.

---

### 7. Gerar os autos de infração derivados do RT (OBRIGATÓRIO)

Esta fase é parte integrante do fluxo — **não é opcional**, **não perguntar ao usuário se
deseja gerá-los**. O RT acabou de ser produzido e tem todas as informações necessárias: data
da inspeção, objetos interditados (seção 3) e ementas com código + descrição + capitulação
(seção 4). Reaproveite esses dados sem nova consulta ao NotebookLM.

#### 7.1. Regras de agrupamento ementa × objeto

- **1 auto por ementa.** Se a ementa aparece para múltiplos objetos, gere 1 auto único que
  liste todos os objetos atingidos na parte 2 (IRREGULARIDADE).
- **N ementas para 1 objeto.** Gere N autos, cada um referenciando aquele objeto.
- A ordem dos autos segue a ordem em que as ementas aparecem na seção 4 do RT.

#### 7.2. Template de cada auto (formato consumido por /gera-ai)

Para cada ementa, monte um bloco EXATAMENTE neste formato:

```
=== AUTO DE INFRAÇÃO #{N} ===
Ementa: {codigo} - {descricao_curta}

1) DA FISCALIZAÇÃO:
Trata-se de ação fiscal (ainda em curso), na modalidade fiscalização mista (nos termos do § 3º, art. 30, do Regulamento da Inspeção do Trabalho - RIT -, aprovado pelo Decreto nº 4.552/2002), no estabelecimento da empresa qualificada. A inspeção física foi realizada em {data_inspecao}.

2) IRREGULARIDADE:
DA INFRAÇÃO COMETIDA: Constatou-se que o empregador aqui autuado incorreu na ementa supracitada, ao {descricao_ementa_min}, {trecho_objetos}, resultando no termo de embargo/interdição em anexo.

O quadro resultante dessa sistematização e análise de informações levou à caracterização da condição de RISCO GRAVE E IMINENTE à saúde e à integridade física dos trabalhadores expostos, na forma conceituada pelo subitem 3.2.1 da Norma Regulamentadora nº 3 do Ministério do Trabalho e Previdência, com atualização dada pela Portaria nº 1.068, de 23 de setembro de 2019: "Considera-se grave e iminente risco toda condição ou situação de trabalho que possa causar acidente ou doença com lesão grave ao trabalhador.", resultando na lavratura do termo de interdição/embargo em anexo.

Exemplo de empregado prejudicado: dano de natureza coletiva. A Portaria MTP nº 667/2021 esclareceu que a citação do empregado em situação irregular faz-se necessária apenas quando imprescindível à caracterização da infração e quando a lei fixar a multa com base no quantitativo de trabalhadores diretamente prejudicados. Ademais, nas infrações que atingem a coletividade dos trabalhadores, tais como naquelas inerentes ao meio ambiente de trabalho (SST), dispensa-se a individualização do sujeito, pois o bem jurídico tutelado tem natureza difusa ou coletiva. (Orientação técnica SIT/n.2/2022).

ELEMENTOS DE CONVICÇÃO:
Inspeção realizada no estabelecimento e relatório técnico do embargo/interdição em anexo.
```

> **NÃO escreva o Subtítulo 3 (OBSERVAÇÕES).** Ele é único e fixo para todo auto e é
> injetado pelo `/gera-ai` (de `config/blocos_auto.md`) entre o Subtítulo 2 e os
> ELEMENTOS DE CONVICÇÃO. O template acima termina, de propósito, no Subtítulo 2 +
> ELEMENTOS DE CONVICÇÃO.

#### 7.3. Regras de substituição

- `{N}` — índice sequencial começando em 1.
- `{codigo}` — código da ementa no formato `XXXXXX-X` (vindo direto da seção 4 do RT).
- `{descricao_curta}` — descrição da ementa **sem a capitulação**. Ex: para a entrada de
  seção 4 `312358-8 - Deixar de instalar sistemas de segurança em zonas de perigo de máquinas
  e/ou equipamentos. Capitulação: Art. 157, inciso I, da CLT, c/c item 12.5.1 da NR-12...`,
  use `Deixar de instalar sistemas de segurança em zonas de perigo de máquinas e/ou
  equipamentos`.
- `{data_inspecao}` — data da inspeção física no formato `DD/MM/AAAA` (mesma usada na seção
  1 do RT).
- `{descricao_ementa_min}` — a descrição curta com **a primeira letra em minúscula** e **sem
  ponto final**. Ex: `deixar de instalar sistemas de segurança em zonas de perigo de máquinas
  e/ou equipamentos`.
- `{trecho_objetos}` — texto que cita o(s) objeto(s) atingido(s):
  - 1 objeto: `para o objeto {n} ({DESCRIÇÃO DO OBJETO EM CAIXA ALTA})`.
  - N objetos: `para os objetos {n1} ({DESCRIÇÃO 1}), {n2} ({DESCRIÇÃO 2})`.
  - A descrição do objeto deve vir literal da seção 3 do RT (linha
    `OBJETO: N – TIPO – Paralisação: ...`).

**NUNCA** mencionar número do termo de interdição/embargo nos autos — sempre referenciar
apenas como "termo de interdição em anexo" / "termo de embargo/interdição em anexo".

#### 7.4. Persistir na pasta dedicada

Na mesma pasta `Autos TE-TI {DD-MM}/` criada no passo 6, salve:

1. **`autos.md`** — todos os N blocos `=== AUTO DE INFRAÇÃO #N ===` concatenados em ordem,
   separados por uma linha em branco. Encoding UTF-8. Esse arquivo é o input direto do
   `/gera-ai` (modo "texto colado").
2. A cópia do `.docx` do RT já está lá (passo 6) — serve como elemento de convicção /
   anexo de todos os autos.

#### 7.5. Apresentar e encerrar

- Imprima no chat os N blocos `=== AUTO DE INFRAÇÃO #N ===` na íntegra (para o AFT revisar
  visualmente).
- Feche com uma linha objetiva indicando o caminho da pasta e os arquivos gerados. Exemplo:

  > RT e autos salvos em `~/Documents/AFT/OS ATIVAS/{PASTA_EMPRESA}/Autos TE-TI 26-05/`
  > (`autos.md` + RT em .docx). Quando for transmitir, rode `/gera-ai` apontando para
  > `autos.md` desta pasta — e anexe o RT (convertido em PDF) aos autos.

- **NÃO pergunte** se quer chamar `/gera-ai`. **NÃO chame** `/gera-ai` automaticamente. O AFT
  dispara `/gera-ai` por conta própria quando estiver pronto para transmitir.

---

## Estrutura do documento (referência)

```
[CABEÇALHO — fixo: MTE / SIT / SRTE / Setor de Inspeção / logos]

RELATÓRIO TÉCNICO
TERMO DE INTERDIÇÃO Nº [NÚMERO]

EMPREGADOR: [NOME]
CNPJ: [CNPJ]

1. OBJETIVO — fixo + frase da data da inspeção física
2. DA AÇÃO FISCAL — fixo (adaptar NR citada se necessário)
3. OBJETOS INTERDITADO — OBJETO: N – TIPO — Paralisação: TOTAL/PARCIAL
4. IRREGULARIDADES — metodologia NR-3 fixa + ementas (formato XXXXXX-X)
5. FATORES DE RISCO E/OU RISCOS RELACIONADOS — preencher
6. MEDIDAS DE PROTEÇÃO A ADOTAR — preencher
7. DOCUMENTOS SOLICITADOS — preencher
8. CONCLUSÃO/OBSERVAÇÃO — preencher

[DO PEDIDO DE SUSPENSÃO DA INTERDIÇÃO — fixo]
[Instruções SEI — fixas]
[Observação sobre recurso — fixa]

[CIDADE]-[UF], [DATA]

[NOME DO AFT]
Auditor-Fiscal do Trabalho
Competência delegada pela Portaria 1719/2014...
```

---

## Regras de redação

- Linguagem técnica e objetiva, adequada para documentos oficiais.
- Texto limpo: sem colchetes, marcações ou referências de fonte no documento final.
- Não alterar nenhum conteúdo fixo do modelo.
- Se alguma seção não tiver dados do usuário, inserir `[A PREENCHER]` e informar o usuário.
- Manter a formatação (fontes, espaçamentos, tabulações) do modelo original.

---

## Comportamento em casos especiais

| Situação | Ação |
|---|---|
| Múltiplos objetos interditados | Replicar a estrutura da seção 3 para cada objeto |
| NR diferente da NR-12 | Ajustar a referência legal na seção 2 e na seção 4 |
| Paralisação parcial | Indicar "Paralisação: PARCIAL" com especificação do escopo |
| Ausência de algum dado | Inserir `[A PREENCHER]` e listar os campos pendentes ao usuário |
| PDFs de termos/autos anexados | Extrair os dados automaticamente dos documentos antes de preencher |
| Data da inspeção não encontrada no contexto | Perguntar ao usuário antes de continuar |
| Nenhuma camada retorna código de ementa | Inserir `[EMENTA A PREENCHER]` e listar ao AFT ao final |
| Múltiplas irregularidades | Consultar NotebookLM em paralelo, uma pergunta por irregularidade |
| Mesma ementa atinge múltiplos objetos | 1 único auto na Fase 7, listando todos os objetos na parte 2 (não duplicar) |
| Ementa ficou como `[EMENTA A PREENCHER]` no RT | Pular esta ementa na Fase 7 e avisar o AFT no fechamento |
| Pasta `Autos TE-TI DD-MM/` já existe | Sobrescrever `autos.md` e a cópia do `.docx` (idempotente) |
| AFT de outra SRTE (não GO) | Avisar que o template é da SRTE/GO; preencher cidade/UF do aft-config.md e sugerir ajustar o cabeçalho no Word após gerar |
