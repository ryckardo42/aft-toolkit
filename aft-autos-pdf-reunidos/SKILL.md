---
name: aft-autos-pdf-reunidos
model: sonnet
effort: low
allowed-tools: Read, Glob, Grep, Bash, Write, AskUserQuestion
description: >
  Use quando o AFT quiser reunir todos os PDFs dos autos de infracao lavrados
  de uma empresa em um unico PDF, com os anexos de cada auto logo apos ele.
  Dispare com /aft-autos-pdf-reunidos, "reunir os autos em um PDF", "juntar
  os PDFs dos autos", "PDF unico dos autos", "mesclar autos e anexos",
  "dossie dos autos em PDF", "um PDF so com todos os autos". Aceita 0 ou 1
  argumento (CNPJ ou parte do nome da empresa). Antes de processar, oferece
  o modo Completo (anexos inteiros) ou Economico (10 paginas por anexo).
  Read-only sobre o Sistema Auditor; o PDF final vai para a pasta da OS. NAO
  confundir com /aft-autos-lavrados (snapshot e Relacao de autos em .docx).
---

# autos-pdf-reunidos — Um PDF único com todos os autos + anexos
**AFT Toolkit** (Windows)

> **Onde ficam as pastas das OS.** O AFT pode ter mudado a pasta de trabalho de
> lugar. Nunca presuma `~/Documents/AFT`: resolva **uma vez, no início**, e use o
> que voltar onde este texto disser `<OS_ATIVAS>`.
>
> **Nas mensagens ao AFT, escreva o caminho de verdade** — nunca ecoe
> `<OS_ATIVAS>` na tela.
>
> ```bash
> python ~/.claude/skills/_scripts/pasta_aft.py --os-ativas   # -> <OS_ATIVAS>
> ```

## O que faz

Varre a pasta da empresa no Sistema Auditor (a mesma que o `/aft-autos-lavrados`
usa) e monta **um único PDF** na ordem cronológica de lavratura:

```
AI mais antigo → anexo dele → próximo AI → anexo dele → ... → autos de JORNADA por último
```

- **Auto:** cada `AI_<9 dígitos>.PDF` da raiz entra **completo**. A ordem é o
  número do AI (crescente no tempo).
- **Anexo:** se existir a pasta `AX_<mesmos 9 dígitos>`, os PDFs dela entram
  logo após o auto, em ordem alfabética — inteiros no modo **Completo**,
  limitados a 10 páginas cada no modo **Econômico** (Passo 2.5).
- **Anexo repetido entra uma vez só:** o mesmo documento anexado a vários
  autos (PGR, AET, laudo...) é incluído apenas no **primeiro** auto da ordem
  final; nos demais, o relatório registra "já incluído em AI X". A comparação
  é pelo **conteúdo** do arquivo (hash), então pega o documento igual mesmo
  salvo com nomes diferentes em pastas `AX_` distintas.
- **Jornada por último:** autos cuja ementa é de jornada (excesso diário/semanal,
  interjornada, intrajornada, AFD/AEJ, atestado do REP — a lista exata está no
  script) carregam anexos volumosos de ponto e vão para o **fim** do PDF, na
  ordem cronológica entre si. O script lê a ementa do próprio PDF do auto.
- **Navegação:** o PDF final tem marcadores (índice lateral do leitor de PDF) —
  um por auto, com os anexos aninhados.
- **Compressão:** o arquivo é comprimido ao final (Ghostscript, se instalado;
  senão pikepdf; sem nenhum dos dois, sai sem comprimir — ainda funciona).

É só isso: a skill **não interpreta** os autos (isso é o `/aft-autos-lavrados`)
e **não altera nada** no Sistema Auditor.

## Pré-condições

- Sistema Auditor instalado (`C:\SistemasAFT\Auditor\Docs\AutosDeInfracao\PRO`).
  - **Windows:** o script acha esse caminho sozinho.
  - **Mac com Parallels:** acha sozinho sob `/Volumes/*/SistemasAFT/…` (disco C:
    compartilhado). Se o volume não estiver montado, peça ao AFT (em uma frase)
    para ativar o compartilhamento do disco no Parallels.
  - Instalação fora do padrão: passe `--pasta-pro "<caminho da pasta PRO>"`.
- `pypdf` instalado (o `/aft-setup` já faz; em falta, o script avisa no JSON).
- No Windows, invoque o Python pelo `python_path` do `aft-config.md`.

## Passo a passo

### Passo 1 — Resolver a empresa

Igual ao `/aft-autos-lavrados`: descubra a pasta da OS em `<OS_ATIVAS>` e o
CNPJ/CPF do autuado (nome da pasta ou `memory.md`).

- **Com argumento:** 11/14 dígitos → match por CNPJ/CPF; 8 dígitos → use direto;
  texto → substring case-insensitive do nome. Múltiplos matches →
  `AskUserQuestion`.
- **Sem argumento:** se a conversa já é de uma OS, use-a; senão pergunte qual.
- **OS sem CNPJ/CPF:** pergunte os **8 primeiros dígitos** do CNPJ/CPF (é o
  sufixo da pasta no Sistema Auditor).

### Passo 2 — Definir onde salvar

Padrão: `<pasta-OS>/AUTOS/Autos reunidos/autos-reunidos.pdf` (em OS sem a caixa
`AUTOS/`, use `<pasta-OS>/Autos reunidos/`). Se já existir, será sobrescrito —
avise no chat. Se a empresa **não tem pasta de OS** em `<OS_ATIVAS>`, pergunte ao
AFT onde salvar (sugira a Área de Trabalho).

> **Encadeada pelo `/aft-relatorio` (Passo 6 de lá):** o original continua **aqui**,
> no destino padrão, com o JSON gravado ao lado (`autos-reunidos.json`) — ele alimenta
> a página "ANEXOS - Autos de Infração" do .docx do relatório. Depois, aquela skill
> **copia** o PDF para a pasta do relatório com o nome do RI
> (`RI <ri> - autos e anexos.pdf`); a cópia é responsabilidade dela, não desta.

### Passo 2.5 — Oferecer o modo (obrigatório, antes de processar)

Use `AskUserQuestion` explicando os dois modos em linguagem simples:

- **Completo** — cada auto seguido do anexo **inteiro**. Fiel ao que está no
  Sistema Auditor; arquivo maior (um PGR de centenas de páginas entra todo).
- **Econômico** — cada arquivo de anexo entra com **até 10 páginas**; o resto é
  cortado e listado no relatório. Dossiê muito menor, bom para leitura rápida
  ou envio.

Diga também que, nos dois modos, anexo repetido entra só na primeira menção e
os autos de jornada vão para o fim. Se o AFT pedir outro limite de páginas
(via "Other"), use o número que ele der em `--paginas-anexo`.

### Passo 3 — Rodar o script

```bash
python ~/.claude/skills/aft-autos-pdf-reunidos/scripts/reune_autos_pdf.py "<EMPRESA>" "<CNPJ_OU_8DIGITOS>" "<SAIDA.pdf>"
```

Modo **Completo** → sem `--paginas-anexo`. Modo **Econômico** →
`--paginas-anexo 10` (ou o limite que o AFT escolheu). Instalação fora do
padrão → `--pasta-pro "<PRO alternativa>"`.

Capture o JSON do stdout. Campos que importam:

- `pasta_auditor` + `match_estrategia` — como a pasta foi achada. Se vier
  `null` com `candidatos_alternativos`, pergunte qual é (`AskUserQuestion`) e
  rode de novo com os 8 dígitos certos. Se `nome_prefixo`, diga ao AFT que o
  match foi pelo nome (conferência parcial).
- `autos[]` — por auto (já na ordem final do PDF): `numero_ai`, `ementa_num`,
  `jornada`, `paginas_auto`, `anexos[]` (com `paginas_total` ×
  `paginas_incluidas`, e `repetido_de` quando omitido por repetição),
  `anexo_cortado`, `warnings`.
- `autos_jornada_no_fim` — os AIs de jornada deslocados para o fim.
- `anexos_repetidos_omitidos` — anexos que entraram só na primeira menção.
- `anexos_orfaos` — pastas `AX_` sem auto correspondente (não entram no PDF).
- `total_autos`, `total_paginas`, `tamanho_mb`, `compressao`.
- `errors` — reporte e pare.

### Passo 4 — Reportar ao AFT

```
✅ Autos reunidos em um só PDF — <empresa>

📄 Arquivo: <caminho do PDF>  (<total_paginas> páginas, <tamanho_mb> MB, modo <Completo|Econômico>)
🗂️  Fonte: <basename pasta_auditor> (<total_autos> autos, match: <estrategia>)

Autos de jornada deslocados para o fim: <lista de AIs, ou "nenhum">
Anexos repetidos incluídos só na primeira menção: <N> (<resumo: "PGR em 5 autos → só no AI X", ...>)
```

- No modo **Econômico**, liste **todos** os cortes (`anexo_cortado`):
  `AI <numero_ai> — <arquivo> (<paginas_total> pág. → <paginas_incluidas>)`.
- Se houver `warnings` (PDF ilegível pulado) ou `anexos_orfaos`, relate.
- Lembre em uma linha: os PDFs originais continuam intactos no Sistema Auditor.

## Erros comuns e tratamento

| Sintoma | Tratamento |
|---|---|
| Pasta PRO não encontrada | Confirmar instalação do Sistema Auditor; no Mac, conferir se o disco do Parallels está montado; ou `--pasta-pro` |
| `pypdf` ausente | `pip install pypdf` (ou rode `/aft-setup`) e repita |
| Vários candidatos de pasta | `AskUserQuestion` para o AFT escolher |
| PDF corrompido/protegido | O script pula e registra em `warnings` — relate ao AFT, não trava o resto |
| Sem compressor (gs/pikepdf) | O PDF sai sem comprimir; sugira `pip install pikepdf` se o tamanho incomodar |
| Traceback + aviso de ticket em `<pasta AFT>/tickets/` | Defeito do toolkit, não do AFT: diagnostique, conserte se der e ofereça o `/aft-erro` |

## Regras

- **Read-only no Sistema Auditor.** O PDF final nunca é gravado na pasta `PRO`.
- **Nenhum auto fica de fora.** Todos os `AI_*.PDF` da pasta entram — inclusive
  eventuais autos cancelados/re-lavrados (quem julga validade é o
  `/aft-autos-lavrados`). Auto com ementa ilegível não vira jornada: fica na
  posição cronológica normal.
- **Nunca invente ementa de jornada.** A lista `EMENTAS_JORNADA` do script é a
  única fonte da classificação; para incluir outra ementa, o AFT pede e o
  mantenedor atualiza o script.
- Não ecoar no chat nome/CPF de trabalhador que apareça em nome de arquivo de
  anexo — cite só o AI e a contagem de páginas nesses casos.
- Nunca enviar o PDF (nem os autos) a serviço externo — compressão é sempre
  local.
