---
name: organiza-os
model: sonnet
description: >
  Use SEMPRE que o AFT jogar/copiar uma pasta bagunçada de fiscalização dentro
  de OS ATIVAS (documentos acumulados antes do toolkit: notificações do DET,
  relação de autos do Sistema Auditor, respostas do empregador, fotos) e quiser
  colocá-la no padrão do AFT Toolkit. Acione com "/organiza-os", "organiza essa
  pasta", "joguei uma pasta na OS ATIVAS", "importar uma auditoria antiga",
  "arruma a pasta da empresa X", "padroniza essa OS", "acabei de copiar os
  arquivos da fiscalização". A skill lê os arquivos (1ª página dos PDFs),
  classifica cada um (notificação DET, relação de autos lavrados, resposta do
  empregador, fotos, não identificado), extrai empregador/CNPJ-CPF/códigos e
  prazos de DET/autos lavrados, mostra um PLANO antes-e-depois e — só com
  aprovação do AFT — renomeia a pasta para o padrão, cria o memory.md completo
  e move os arquivos para os lugares que as demais skills esperam. Nunca apaga
  nada. NÃO cadastra OS do zero (isso é /nova-os) nem baixa nada do DET (isso é
  det-baixar).
---

# organiza-os — Importar/organizar uma pasta de fiscalização pré-toolkit
**AFT Toolkit**

## Objetivo

O colega que começa a usar o toolkit já tem fiscalizações em andamento, com os documentos
acumulados numa pasta do jeito dele. Esta skill pega essa pasta **jogada em `OS ATIVAS/`**
e a coloca no padrão do toolkit: nome de pasta padronizado, `memory.md` com os dados
extraídos dos próprios documentos (empregador, CNPJ/CPF, notificações DET com prazo,
autos já lavrados), e os arquivos nos lugares onde as demais skills (`/painel`,
`/analise-preliminar`, `/det-630`, `/autos-lavrados`) esperam encontrá-los.

Regra de ouro: **inventário e plano primeiro, execução só depois do OK do AFT. Nunca
apagar nada** — só renomear e mover; o que não der para identificar fica onde está.

## FASE 1 — Resolver o alvo

1. Se o AFT indicou a pasta, use-a. Senão, procure candidatas em `OS ATIVAS/`:
   pastas **sem `memory.md`** são as recém-jogadas:
   ```bash
   for d in ~/Documents/AFT/"OS ATIVAS"/*/; do [ -f "$d/memory.md" ] || echo "$d"; done
   ```
   (No Mac, use a pasta de OS do `aft-config.md` — campo `pasta_os` — se existir.)
2. Uma candidata → confirme com o AFT. Várias → apresente numeradas e pergunte.
3. Se a pasta escolhida JÁ tem `memory.md`, avise que ela parece organizada e pergunte
   se é para reprocessar mesmo assim (aí todo cuidado dobra: rode
   `backup_arquivo.py` no memory.md antes de qualquer edição).

## FASE 2 — Inventário e classificação (somente leitura)

Liste tudo (`ls -la`, recursivo no 1º nível) e, para cada PDF, extraia a 1ª página:

```bash
pdftotext -layout -f 1 -l 1 "<arquivo.pdf>" - 2>/dev/null | head -40
# sem pdftotext, use pdfplumber via python (o /aft-setup instala)
```

Classifique cada item pelas assinaturas (nome do arquivo + texto da 1ª página):

| Tipo | Assinaturas típicas |
|---|---|
| **Notificação DET** | "NOTIFICAÇÃO Nº" + código alfanumérico 12–16 chars (ex.: `S8JHJEYM2OC4VE`); "NOTIFICAÇÃO PARA A APRESENTAÇÃO DE DOCUMENTOS"/"CORREÇÃO"; cabeçalho MTE/SIT |
| **Relação de autos lavrados** | "Relação de Autos de Infração Lavrados" (relatório do Sistema Auditor); nome tipo `RR_*.PDF` |
| **Resposta do empregador ao DET** | pasta com subpastas `item1`, `item2`... (padrão do download do DET) ou ZIP/pasta com nome `<EMPREGADOR>_<data>` |
| **Fotos de inspeção** | `.jpeg/.jpg/.png/.heic` (soltas ou em subpasta) |
| **Auto de infração (PDF)** | "AUTO DE INFRAÇÃO Nº" — nome `AI_<9 díg>.PDF` |
| **Interdição/embargo** | nome com `interdicao`/`interdição`/`embargo`/`TE-TI`; ou 1ª página com "TERMO DE INTERDIÇÃO"/"TERMO DE EMBARGO"/"TERMO DE MANUTENÇÃO"/"RELATÓRIO TÉCNICO" + interdição/embargo. Inclui o termo assinado, o RT que o fundamenta (`RT_Interdicao.docx`), o RT de manutenção, o requerimento de suspensão e seus juntados |
| **Não identificado** | sem texto extraível (escaneado) ou sem assinatura conhecida |

Extraia, quando presentes:
- **Empregador** (Nome/Razão Social) e **CNPJ (14 díg.) ou CPF/CAEPF (11 díg.)** — em
  notificações DET vem em "EMPREGADOR / Nome: ... CPF/CNPJ: ...". Empregador pessoa
  física (produtor rural) usa CPF: é normal.
- **Município/UF** (do endereço de fiscalização).
- Por notificação DET: **código**, **prazo** ("até dd/mm/aaaa" nos itens notificados) e
  **ciência** (se constar).
- Da relação de autos: para cada auto, **número do AI** (9 dígitos → formate
  `XX.XXX.XXX-X`), **data de lavratura**, **ementa** (7 dígitos → `XXXXXX-X`) e um resumo
  curtíssimo da descrição.

> Privacidade: **não abra nem ecoe** conteúdo de listas de empregados (ex.: "RELAÇÃO DE
> EMPREGADOS.xlsx") — classifique pelo nome do arquivo e siga. Nome/CPF de trabalhador
> não aparece no chat nem no memory.md. O CPF/CNPJ **do empregador** é o identificador
> da OS: fica real (nunca tokenizado).

## FASE 3 — Plano antes-e-depois (aprovação obrigatória)

Monte e apresente o plano completo. Exemplo:

> Exemplo abaixo com dados **fictícios** — nunca use uma fiscalização real como
> exemplo em documentação: este arquivo vai para um repositório público.

```
📦 Organização proposta — pasta "Jose fazenda"

Empregador identificado: JOSE DA SILVA SANTOS · CPF 111.222.333-44 · Cidade/UF

1. Renomear a pasta:
   Jose fazenda  →  JOSE DA SILVA SANTOS 11122233344

2. Criar memory.md com:
   • Notificações DET: ABCDE12345FGHIJ — prazo 19/06/2026
   • Autos lavrados: 14 autos (23.324.310-1 ... de 22/06/2026, NR-33)

3. Renomear/mover arquivos:
   notificacao-ABCDE12345FGHIJ.pdf       → (já no padrão, fica na raiz)
   JOSE_DA_SILVA_SANTOS_2026-07-13_*/    → notificacao-ABCDE12345FGHIJ/   (resposta do empregador, item1..4)
   relacao autos jose RR_*.PDF           → Relacao de autos/relacao-autos-2026-07-13.PDF
   TERMO_interdicao_assinado.pdf         → interdicao-embargo/   (termo/RT/embargo)
   RT_Interdicao.docx                    → interdicao-embargo/
   fotos/ (16 imagens)                   → fotos/   (fica como está)

4. Não identificados (ficam onde estão — me diga o que são, se quiser):
   • FC AGRO.pdf (PDF escaneado, sem texto)

Nada será apagado. Confirma a organização?
```

Regras do plano:
- **Nome da pasta**: `<EMPREGADOR EM CAIXA ALTA> <identificador só dígitos>` (padrão do
  toolkit). Sem identificador encontrado → só o nome, e avise que o CNPJ/CPF será exigido
  no `/gera-ai`.
- **Notificações**: PDF na **raiz** como `notificacao-<CODIGO>.pdf`; resposta do
  empregador na subpasta `notificacao-<CODIGO>/` (mantendo `item1/`, `item2/`...). É onde
  `/analise-preliminar`, `/det-630` e `/painel` procuram.
- **Relação de autos**: subpasta `Relacao de autos/` (mesma que o `/autos-lavrados` usa
  para a relação .docx).
- **Interdição/embargo**: subpasta `interdicao-embargo/` — pasta **única por OS** (sem sufixo
  de data) onde vai TODO o material da medida: termo assinado, RT que a fundamenta, RT de
  manutenção, requerimento de suspensão e juntados do empregador, e os autos derivados
  (`autos.md` + TXT do `/gera-ai`). É a mesma pasta que o `/aft-rt-rgi` e o `/rt-manutencao`
  escrevem. Se já existir uma pasta antiga `Autos TE-TI DD-MM/`, proponha renomeá-la para
  `interdicao-embargo/` (ou mover o conteúdo dela para lá).
- Fotos: subpasta `fotos/` (crie se estiverem soltas).
- Ambiguidade real (ex.: dois empregadores diferentes nos documentos) → **pergunte**, não
  escolha em silêncio.
- Só execute após confirmação explícita.

## FASE 4 — Executar e registrar

1. Renomeie a pasta (`mv`), depois mova/renomeie os arquivos conforme o plano.
2. Crie o `memory.md` no esquema padrão do toolkit (o mesmo do `/nova-os`):

```markdown
---
empregador: <EMPREGADOR>
cnpj: "<só dígitos, ou vazio>"
municipio: <município ou vazio>
status: em_andamento
---
# <EMPREGADOR>

**CPF:** <formatado>   (ou **CNPJ:**, conforme o caso)

## Notificações DET
- [ ] <CODIGO> — prazo <dd/mm/aaaa>

## Autos de Infração
_(vazio)_

## Autos lavrados
- [x] Ementa <XXXXXX-X> — <resumo curtíssimo> — AI <XX.XXX.XXX-X> (lavrado em <dd/mm/aaaa>)
...uma linha por auto da relação...

## Registro de atividades
| Data | Ação | Detalhes |
|------|------|----------|
| <hoje> | OS importada e organizada | via /organiza-os — <N> notificações, <M> autos lavrados |
```

   - `prazo <dd/mm/aaaa>` literal na linha do DET (é o que o `/painel` vigia). DET cujo
     prazo já passou e foi respondido (há pasta de resposta) → marque `[x]`; na dúvida,
     deixe `[ ]` e avise.
   - Linhas de autos lavrados chaveadas pelo **número do AI** (única por auto).
3. Rode o guarda de PII no que você escreveu:
   ```bash
   python ~/.claude/skills/_scripts/checar_pii.py "<pasta da OS>/memory.md"
   ```
4. Confirme com o painel (a OS nova deve aparecer):
   ```bash
   python ~/.claude/skills/_scripts/gerar_painel.py "<pasta OS ATIVAS>"
   ```
5. Resumo final:

```
✅ OS organizada — <EMPREGADOR>
📁 <caminho novo da pasta>
🗂️  <N> notificação(ões) DET no padrão · <M> autos lavrados registrados no memory.md
❓ Não identificados (intocados): <lista ou "nenhum">

Próximos passos:
  • /painel               → a OS já aparece no dashboard
  • /analise-preliminar   → analisar a resposta do empregador ao DET
  • /autos-lavrados       → conferir os autos direto no Sistema Auditor
```

## Encadeamento

- Não substitui `/nova-os` (cadastro do zero, sem documentos) — esta skill parte de
  documentos existentes.
- A resposta do empregador organizada alimenta `/analise-preliminar`; os autos do
  memory.md são refinados depois pelo `/autos-lavrados` (que lê o Sistema Auditor).

## Regras

- **Nunca apague arquivo nenhum** — só renomear e mover dentro da própria pasta da OS.
  Não identificado = fica onde está, listado para o AFT.
- **Nunca execute nada antes da aprovação do plano** (FASE 3).
- Se já existir pasta organizada com o mesmo CNPJ/CPF em OS ATIVAS, **não duplique**:
  proponha fundir (mover os arquivos novos para lá) e pergunte antes.
- Dados extraídos vêm **dos documentos** — não invente empregador, código, prazo ou
  número de AI que não estejam escritos neles. Campo não encontrado fica vazio.
- Nome/CPF de trabalhador: nunca no chat nem no memory.md (só quantitativos).
- Encoding UTF-8; datas dd/mm/aaaa no corpo do memory.md.
