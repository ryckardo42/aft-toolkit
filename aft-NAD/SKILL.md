---
name: aft-NAD
model: sonnet
effort: medium
description: >
  Use quando o AFT quiser redigir a Notificação para Apresentação de
  Documentos (NAD) — o texto que vai no DET pedindo documentos que se
  presume existirem. Acione com /aft-NAD, "gera a NAD", "notificação para
  apresentar documentos", "pede o PGR pelo DET", "solicita documentos à
  empresa", "monta a notificação de documentos". NÃO é auto de infração
  (/aft-auditoria-geral) nem TN de correção (/aft-tn-nco).
---

# NAD — Notificação para Apresentação de Documentos
**AFT Toolkit**

> **Onde ficam as pastas das OS.** O AFT pode ter mudado a pasta de trabalho de
> lugar (HD externo, nuvem, outro disco). Nunca presuma `~/Documents/AFT`:
> resolva **uma vez, no início**, e use o que voltar onde este texto disser
> `<OS_ATIVAS>` (a pasta que contém as OS) ou `<PASTA_AFT>` (a pasta acima dela).
>
> **Nas mensagens ao AFT, escreva o caminho de verdade** — nunca ecoe
> `<OS_ATIVAS>`/`<PASTA_AFT>` na tela: ele precisa saber onde abrir a pasta.
>
> ```bash
> python ~/.claude/skills/_scripts/pasta_aft.py --os-ativas   # -> <OS_ATIVAS>
> python ~/.claude/skills/_scripts/pasta_aft.py --path        # -> <PASTA_AFT>
> ```


Gera o **texto** de uma notificação para a empresa **apresentar** documentos que o AFT presume existirem (PGR, controles de jornada, ASOs, atas da CIPA, folha de pagamento, etc.), via DET. Verbo central: **Apresentar**. O AFT cola o resultado no DET (campo Introdução + um Item Solicitado por documento + campo Observações) e o documento fica salvo como `.md` na pasta da OS.

Esta skill **só redige o texto da notificação**. Não lavra auto de infração (isso é `/aft-auditoria-geral` → `/aft-gera-ai`) nem notifica correção de irregularidade já constatada (isso é `/aft-tn-nco` — verbo "Corrigir"). O preenchimento do template no DET é manual — o toolkit não automatiza o DET.

## Pasta base
`<OS_ATIVAS>/<EMPREGADOR> <CNPJ>/`

---

## FASE 0 — Resolver a OS (para salvar o .md)

1. Se um argumento posicional (CNPJ de 14 dígitos ou substring do nome) foi passado, faça match nas pastas de `<OS_ATIVAS>/`.
2. Se a skill foi encadeada na mesma sessão (ex.: ao final de `/aft-preparacao-acao-fiscal`), herde a OS do contexto.
3. Múltiplos matches → `AskUserQuestion`. Zero matches e nenhum contexto → pergunte ao AFT o empregador (e, se quiser salvar mesmo sem pasta de OS, ofereça a Área de Trabalho como fallback).

Guarde: `PASTA_OS`, `EMPREGADOR`.

> A resolução da OS é leve de propósito — esta skill funciona standalone. Se não houver pasta de OS, ainda gere o texto no chat e só pergunte onde salvar.

---

## FASE 0.5 — O modelo do DET (a lista que o AFT já consagrou)

Quase todo AFT tem, no DET, um **modelo de notificação** com a lista de documentos que ele sempre pede no início da fiscalização — e pode adotar o modelo de um colega. Puxar esses itens evita reescrever o que já está pronto.

1. **Ache o número do modelo**, nesta ordem:
   - o campo `modelo_nad_det` do `aft-config.md` (e `cif_modelo_nad`, a CIF do dono do modelo);
   - **sem esses campos, use o modelo canônico do toolkit: identificação `11301`, CIF `358070`** — a "Primeira notificação", com a lista que serve a qualquer início de fiscalização (contato dos prepostos, relação de prestadores de serviço, PGR com inventário e plano de ação, relação de máquinas do item 12.18.1 da NR-12). Diga ao AFT qual modelo está usando, e que ele pode trocar pelo dele gravando os dois campos no `aft-config.md`.
   - se ele disser que não quer modelo nenhum, siga sem — a skill funciona igual.

> **Modelo de outro auditor funciona, e não precisa ser "público".** A busca usa o filtro "todos os modelos cadastrados"; basta a identificação e a CIF do dono. Nunca peça ao colega para marcar o modelo como público.
2. **Puxe os itens** (precisa do painel no ar e do token — `~/.claude/skills/config/canal-token-det.md`):
   ```bash
   python ~/.claude/skills/_scripts/det_criar.py   # itens_do_modelo(token, id_modelo, cif)
   ```
   Na prática, quem chama é o painel; sem token, ofereça abrir o DET no seu navegador para o AFT logar.
3. **Mostre os itens do modelo ao AFT** e deixe-o riscar o que não quer. Eles entram como estão — texto do modelo é do AFT, não se reescreve.

> **Sem token ou sem modelo, não trave.** Diga em uma linha que a lista virá só da FASE 1 e siga.

---

## FASE 1 — Coletar os documentos a solicitar

A fonte é **os itens do modelo (FASE 0.5) + contexto da sessão + lista colada** (a skill detecta):

0. **Do modelo:** os itens aprovados na FASE 0.5 entram primeiro, na ordem do modelo.
1. **Encadeada:** se a sessão já contém um checklist de documentos aprovado pelo AFT (saída de `/aft-preparacao-acao-fiscal`), reaproveite-o direto.
2. **Colada:** se o AFT colou uma lista de documentos no prompt, use-a.
3. **Standalone sem lista:** pergunte ao AFT quais documentos solicitar. Pode oferecer um catálogo comum como ponto de partida (PGR, PCMSO, ASOs, controles de jornada — AFD/AEJ, atas da CIPA, certificados de treinamento NR-XX, folha de pagamento, contratos de trabalho, laudo/AET), mas **não presuma** — o AFT decide o que pedir. **Nunca** ofereça "livro/ficha de registro de empregados": o registro é feito no eSocial, e livro/ficha não existem mais.

Para **cada** documento, capture:

| Campo | O que é | Exemplo |
|---|---|---|
| **Título** | rótulo curto do documento, em negrito | `Programa de Gerenciamento de Riscos` |
| **Base legal** | item da NR (SST) OU artigo da CLT/lei (não-SST) que ampara a exigência | `item 1.5.3.1 da NR-01` · `art. 74, §2º, da CLT` |
| **Descrição** | o que exatamente apresentar (pode incluir período de referência) | `apresentar o PGR completo, incluindo Inventário de Riscos e Plano de Ação, vigente` |

> **Um item por documento.** Não agrupe documentos distintos num único item, mesmo que venham do mesmo tema (ex.: PGR e PCMSO são dois itens, não um). Se o AFT quiser agrupar, ele pede explicitamente.

---

## FASE 2 — Buscar a ementa (só quando existir)

Para cada documento, busque o **código da ementa** no formato `XXXXXX-X` (ex.: `312467-3`). A ementa é **opcional**: se não houver ementa correspondente à falta de apresentação daquele documento, o item sai **sem** o `[...]` no final — não invente código.

Estratégia em 3 camadas (mesma de `/aft-tn-nco` e `/aft-auditoria-geral`):

**Camada 1 — NotebookLM (preferencial):**
1. Escolha a **key** do notebook (o script resolve o ID pela cohort do AFT; nunca leia o `notebooks.json` direto).
   - Documento de **SST** (PGR, PCMSO, ASO, laudo, atas CIPA, AET) → key da NR (`nr-01`, `nr-07`, `nr-05`, `nr-17`...). Sem key específica → `ementario-sst`.
   - Documento de **jornada/ponto** → `jornada`. **eSocial** → `esocial`. **FGTS** → `fgts-digital`. **Registro/vínculo** → `informalidade`. Legislação trabalhista geral → `ementario-legis`.
2. Consulte:
   ```bash
   python ~/.claude/skills/_scripts/notebooklm_consulta.py <key> "Qual ementa do ementário cobre a não apresentação/ausência de [DOCUMENTO] exigido por [BASE_LEGAL]? Retorne o código (formato XXXXXX-X) e a descrição oficial."
   ```
   > **Código 5** (`{"estado": "primeiro-acesso", ...}`): o notebook ainda não está na coleção do
   > AFT — o Google só o registra depois de **uma interação com o chat**. Diga, em uma linha, com
   > o link do campo `url`: *"A base de [título] ainda não está na sua conta. Abra [link], escreva
   > **oi** no chat e me diga 'pronto' — eu repito a consulta."* Depois do "pronto", repita a MESMA
   > consulta. Se o link pedir acesso, o pedido é em https://notebooks-aft.vercel.app.
   > **Código 3** (nada no stdout): não existe para a cohort do AFT; siga sem essa camada.
   > **Reconexão automática:** se a sessão tiver expirado, o `notebooklm` se reautentica sozinho pelo `NOTEBOOKLM_REFRESH_CMD`. Só passe à Camada 2 se ainda assim não responder.
3. Extraia o código com regex `\d{6}-\d` do `answer` ou de `references[].cited_text`.

**Camada 2 — Ementário no Google Drive (manual):** oriente o AFT a abrir
https://drive.google.com/drive/folders/1bktX9TkDIoix4iQuca3Yr5aWCfv97GSg?usp=sharing
(pasta `EMENTAS SST` → `ementasNR[XX].md`), localizar o item e colar o trecho da ementa.

**Camada 3 — perguntar ao AFT:** se as camadas 1–2 não retornarem código confiável, pergunte se há ementa. Se o AFT disser que não há, deixe o item sem `[...]`.

Antes de montar, apresente ao AFT a tabela de itens resolvidos para conferência (Título · Base legal · Descrição · Ementa). Ele pode ajustar redação ou códigos.

---

## FASE 3 — Montar a notificação

O texto tem **três partes fixas/variáveis**. Preserve acentuação (UTF-8).

### Introdução (FIXA — copie literalmente)

```
Nos termos do art. 630, §§ 3º e 4º, da CLT, combinado com o art. 23, da Lei nº 8.036/90, bem como art. 18, IV e V, do Dec. nº 4.552/02, fica a empresa NOTIFICADA PARA APRESENTAR OS DOCUMENTOS relacionados:
```

> Copie exatamente como está acima — não parafraseie nem "corrija" a redação.

### Itens (um por documento)

Formato de cada item — **SST** (item de NR):
```
*<TÍTULO>* - item X.X.X da NR-YY: Apresentar <descrição>. [<EMENTA>]
```

Formato de cada item — **não-SST** (artigo de lei/CLT):
```
*<TÍTULO>* - <BASE_LEGAL>: Apresentar <descrição>. [<EMENTA>]
```

- O verbo central é sempre **Apresentar** — não substitua por "Corrigir", "Elaborar" etc. (isso é `/aft-tn-nco`).
- O `[<EMENTA>]` final só aparece **quando existe** ementa (Fase 2). Sem ementa → termine no ponto final da descrição.
- Mantenha o negrito do título com asteriscos (`*Título*`), exatamente como no exemplo.
- **Limite de 1000 caracteres por item.** Cada campo do DET (a descrição de cada item e o campo de observações) aceita no **máximo 1000 caracteres**. Se, mesmo enxuto, um item passar de 1000 caracteres, **avise o AFT** e ofereça encurtar a descrição mantendo a base legal.

**Exemplo (referência canônica do AFT):**
```
*Procedimento de Trabalho* - item 12.14.1 da NR-12: Apresentar procedimentos de trabalho e segurança para máquinas e equipamentos, específicos e padronizados, a partir da apreciação de riscos. [312467-3]
```

### Observações (FIXAS — copie literalmente)

```
Comprovação de cumprimento e pedido de prorrogação:
> A adoção das  medidas notificadas devem ser comprovadas pelo empregador  nos prazos previstos nos itens. A dificuldade de cumprimento, ou qualquer manifestação deverá ser expressamente manifestada à fiscalização em cada item. A empresa poderá pedir prazo específico, caso deseje, para o item específico;

Dúvidas:
>  Perguntas/esclarecimentos adicionais podem ser feitos no  "Canal de Comunicação" dentro dessa própria notificação, ou pelos e-mails disponíveis na notificação.
```

> Mesmo boilerplate canônico usado pela `/aft-tn-nco` — é genérico o bastante para se aplicar a pedido de documentos. Reproduza-o verbatim.

---

## FASE 4 — Apresentar no chat (bloco a bloco) + salvar .md

O AFT **copia cada parte individualmente** para os campos correspondentes do DET (Introdução · um Item Solicitado por documento · Observações). Apresente cada parte em seu **próprio bloco de código copiável**, com rótulo claro.

**Cheque o limite de 1000 caracteres antes de apresentar.** Conte os caracteres de **cada item** e do **bloco de observações**, mostre a contagem ao lado do rótulo (ex.: `ITEM 1 (312/1000)`). Se algum item estourar, resolva com o AFT antes de entregar.

Estrutura da apresentação no chat:

````
📋 **INTRODUÇÃO** — cole no campo *Introdução* do DET
```
Nos termos do art. 630, §§ 3º e 4º, da CLT...
```

📋 **ITEM 1** — novo *Item Solicitado*
```
*Programa de Gerenciamento de Riscos* - item 1.5.3.1 da NR-01: Apresentar... [XXXXXX-X]
```

📋 **ITEM 2** — novo *Item Solicitado*
```
*<Título>* - <base legal>: Apresentar <descrição>. [<ementa>]
```

(…um bloco por item…)

📋 **OBSERVAÇÕES** — cole no campo *Observações* do DET
```
Comprovação de cumprimento e pedido de prorrogação:
> ...
Dúvidas:
> ...
```
````

Em seguida, **salve o documento completo** na pasta da OS:

```bash
PATH_MD="$PASTA_OS/nad-$(date +%Y-%m-%d).md"
# Se já existe arquivo do mesmo dia, adicione sufixo -2, -3...
```

O arquivo tem **quatro partes**, nesta ordem — é o formato que permite criar a notificação no DET depois, sem depender da conversa:

````markdown
---
det:
  titulo: Notificação para Apresentação de Documentos
  prazo_dias: 16          # ou prazo: dd/mm/aaaa
  tipo: solicitacao       # a NAD é Solicitação de Documento
  retorno: digital        # a empresa anexa pelo DET
  preassinalado: sim
  arquivos: todos
  modelo: 11301           # só se veio de modelo (FASE 0.5)
  cif: 358070             # a CIF do DONO do modelo
---

# Notificação para Apresentação de Documentos

<introdução, copiada literalmente>

## Itens

<um parágrafo por item — os do modelo entram com o texto do modelo,
 os redigidos aqui entram no formato *Título* - base legal: Apresentar... [ementa]>

## Observações

<os blocos "Rótulo:" + linhas ">">
````

> **Por que a seção `## Itens` existe.** Item vindo de modelo do DET é frase corrida, sem título nem ementa — não casa com o formato canônico. Com a seção declarada, o motor lê **cada parágrafo** dela como um item, venha do modelo ou da sua redação. Arquivos antigos, sem a seção, continuam valendo pela regra de sempre.

Confirme ao AFT, em uma linha cada: arquivo salvo + nº de itens (dizendo quantos vieram do modelo); **a data de prazo que ficou**, e que ela pode ser alterada direto no DET. Se não houver pasta de OS resolvida, pergunte onde salvar.

---

## FASE 4.5 — Criar o rascunho no DET (ofereça)

Com o painel local no ar e o **RI** no `memory.md`, ofereça criar o rascunho da notificação no DET a partir do `.md` — em segundos, sem digitar item por item no site.

1. **Token:** siga `~/.claude/skills/config/canal-token-det.md`. Sem token, **ofereça abrir o DET no navegador do assistente** para o AFT logar (via principal) ou peça o Sincronizar da extensão.
2. **Prévia primeiro:** `POST /api/det-criar` sem `confirmar` — devolve o que seria gravado, com a conferência automática já aplicada.
3. **Revisor:** chame a tool `Agent` com `subagent_type: "aft-revisor-notificacao"`, passando o caminho do `.md` e o JSON da prévia. Mostre o parecer.
4. **Só com o "sim" do AFT**, repita com `confirmar: true`.
5. **Sem RI no `memory.md`**, diga isso em uma linha e não ofereça — OS recém-criada pode ainda não ter o número.

> O toolkit **nunca lavra**. O rascunho fica "Em Elaboração" no DET; conferir, lavrar e transmitir são atos do AFT, no site.

### O PDF para levar impresso (só na NAD preliminar)

Quando a notificação vai ser **entregue em mãos na empresa** — o caso da NAD preliminar, gerada na preparação, antes da visita —, acrescente `"pdf": true` à chamada de criação. O PDF do **rascunho** é baixado para o pacote da OS, em `NOTIFICACOES/<CODIGO> <dd-mm-aaaa>/notificacao-<CODIGO>-rascunho.pdf`.

- **5 linhas em branco** ao final, o padrão do próprio DET (`pdf_linhas`, de 0 a 100): são para o AFT completar itens à mão, no local.
- O PDF sai **sem número de notificação** ("NOTIFICAÇÃO Nº." em branco) — é rascunho, o número só existe depois da lavratura. **É o esperado neste fluxo**: o AFT entrega o papel na empresa e colhe a assinatura durante a inspeção física.
- **Só neste caso.** Nas demais NADs, a notificação é transmitida pelo DET e não há o que imprimir; o PDF definitivo vem depois, pela `/aft-det-baixar`.
- O sufixo `-rascunho` no nome **não é enfeite**: a `/aft-det-baixar` grava a versão lavrada como `notificacao-<CODIGO>.pdf` e pula o download se o arquivo já existir. Mesmo nome faria o rascunho tomar o lugar do documento definitivo, em silêncio.

---

## FASE 5 — Registro leve no memory.md (opcional)

Se a OS tem `memory.md`, adicione **uma** linha em `## Registro de atividades` (edição cirúrgica via `Edit`):
```
| DD/MM/AAAA | NAD gerada | N documentos solicitados |
```
Não bloqueie o fluxo se o `memory.md` não existir. Não toque em outras seções.

---

## Encadeamento

- **Origem natural:** ao final de `/aft-preparacao-acao-fiscal`, quando o checklist de documentos a solicitar for aprovado pelo AFT.
- **Também standalone**, a qualquer momento: quando o AFT quer pedir mais documentos durante uma fiscalização já em andamento.
- **Criar o rascunho no DET** (FASE 4.5): com o painel no ar e o RI conhecido, o toolkit monta a notificação a partir do `.md`, sempre com o `aft-revisor-notificacao` passando antes e com a lavratura ficando para o AFT. Sem painel, ele cola os blocos à mão — por isso a FASE 4 continua entregando cada bloco pronto para copiar.
- **Depois de lavrada no DET:** ofereça `/aft-email` para redigir o e-mail que avisa a empresa (ou o advogado) da notificação nova.
- Não confundir com `/aft-tn-nco` (verbo "Corrigir", para irregularidade já constatada).

---

## Regras

- **Nunca** reescreva a introdução ou as observações fixas — são texto canônico do AFT, copiado verbatim para o DET.
- **Nunca** invente código de ementa, item de NR ou base legal. Ementa só entra quando confirmada (Fase 2); na dúvida, item sem `[...]`.
- O verbo central de cada item é sempre **Apresentar** (documento que se presume existir) — se o AFT quiser exigir correção de algo já constatado como irregular, encaminhe para `/aft-tn-nco`.
- **Respeite o teto de 1000 caracteres** por campo do DET (cada item e o campo de observações). Conte e mostre a contagem na apresentação; se estourar, resolva com o AFT antes de entregar.
- Encoding **UTF-8** em todo o pipeline.
- Esta skill **não** lavra auto, **não** clica no DET e **não** define prazos no texto — apenas redige a notificação de documentos.

## Diário de atividades (automático)

Ao concluir o trabalho desta skill numa OS, registre o dia trabalhado no diário —
sem perguntar nada ao AFT (o script deduplica por data+letra; repetir é inofensivo):

```bash
python ~/.claude/skills/_scripts/diario_registrar.py "<pasta da OS>" --tipos E --detalhe "via /aft-NAD"
```
