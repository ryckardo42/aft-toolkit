---
name: NAD
model: sonnet
description: >
  Use SEMPRE que o AFT quiser redigir uma Notificação para Apresentação de
  Documentos (NAD) — o texto que vai no DET pedindo à empresa documentos que
  se presume existirem. Acione com /NAD, "gera a NAD", "notificação para
  apresentar documentos", "pede o PGR pelo DET", "solicita documentos à
  empresa", "monta a notificação de documentos". Origem natural:
  /preparacao-acao-fiscal, ao final do checklist de documentos aprovado; mas
  funciona standalone, a qualquer momento da fiscalização. Produz: introdução
  fixa (art. 630, §§3º/4º, CLT c/c art. 23 da Lei 8.036/90 c/c art. 18, IV e
  V, do Dec. 4.552/02) + um item por documento no formato "*Subtítulo* - item
  X.X.X da NR-YY: Apresentar [...]. [ementa]" (SST) ou com artigo de
  lei/CLT (não-SST), ementa via NotebookLM só quando existir, apresentado
  BLOCO A BLOCO para colar no DET e salvo como .md na pasta da OS. NÃO é
  auto de infração nem TN de correção (isso é /inspecao-inicial → /gera-ai
  e /tn-nco) — é só o TEXTO da notificação de documentos, pronto para colar.
---

# NAD — Notificação para Apresentação de Documentos
**AFT Toolkit**

Gera o **texto** de uma notificação para a empresa **apresentar** documentos que o AFT presume existirem (PGR, controles de jornada, ASOs, atas da CIPA, folha de pagamento, etc.), via DET. Verbo central: **Apresentar**. O AFT cola o resultado no DET (campo Introdução + um Item Solicitado por documento + campo Observações) e o documento fica salvo como `.md` na pasta da OS.

Esta skill **só redige o texto da notificação**. Não lavra auto de infração (isso é `/inspecao-inicial` → `/gera-ai`) nem notifica correção de irregularidade já constatada (isso é `/tn-nco` — verbo "Corrigir"). O preenchimento do template no DET é manual — o toolkit não automatiza o DET.

## Pasta base
`~/Documents/AFT/OS ATIVAS/<EMPREGADOR> <CNPJ>/`

---

## FASE 0 — Resolver a OS (para salvar o .md)

1. Se um argumento posicional (CNPJ de 14 dígitos ou substring do nome) foi passado, faça match nas pastas de `~/Documents/AFT/OS ATIVAS/`.
2. Se a skill foi encadeada na mesma sessão (ex.: ao final de `/preparacao-acao-fiscal`), herde a OS do contexto.
3. Múltiplos matches → `AskUserQuestion`. Zero matches e nenhum contexto → pergunte ao AFT o empregador (e, se quiser salvar mesmo sem pasta de OS, ofereça a Área de Trabalho como fallback).

Guarde: `PASTA_OS`, `EMPREGADOR`.

> A resolução da OS é leve de propósito — esta skill funciona standalone. Se não houver pasta de OS, ainda gere o texto no chat e só pergunte onde salvar.

---

## FASE 1 — Coletar os documentos a solicitar

A fonte é **contexto da sessão + lista colada** (a skill detecta):

1. **Encadeada:** se a sessão já contém um checklist de documentos aprovado pelo AFT (saída de `/preparacao-acao-fiscal`), reaproveite-o direto.
2. **Colada:** se o AFT colou uma lista de documentos no prompt, use-a.
3. **Standalone sem lista:** pergunte ao AFT quais documentos solicitar. Pode oferecer um catálogo comum como ponto de partida (PGR, PCMSO, ASOs, controles de jornada — AFD/AEJ, atas da CIPA, certificados de treinamento NR-XX, livro/ficha de registro, folha de pagamento, laudo/AET), mas **não presuma** — o AFT decide o que pedir.

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

Estratégia em 3 camadas (mesma de `/tn-nco` e `/inspecao-inicial`):

**Camada 1 — NotebookLM (preferencial):**
1. Resolva o `notebook_id`: leia `~/.claude/skills/config/notebooks.json`.
   - Documento de **SST** (PGR, PCMSO, ASO, laudo, atas CIPA, AET) → key da NR (`nr-01`, `nr-07`, `nr-05`, `nr-17`...). Sem key específica → `ementario-sst`.
   - Documento de **jornada/ponto** → `jornada`. **eSocial** → `esocial`. **FGTS** → `fgts-digital`. **Registro/vínculo** → `informalidade`. Legislação trabalhista geral → `ementario-legis`.
2. Consulte:
   ```bash
   notebooklm ask "Qual ementa do ementário cobre a não apresentação/ausência de [DOCUMENTO] exigido por [BASE_LEGAL]? Retorne o código (formato XXXXXX-X) e a descrição oficial." --notebook [notebook_id] --json
   ```
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

- O verbo central é sempre **Apresentar** — não substitua por "Corrigir", "Elaborar" etc. (isso é `/tn-nco`).
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

> Mesmo boilerplate canônico usado pela `/tn-nco` — é genérico o bastante para se aplicar a pedido de documentos. Reproduza-o verbatim.

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

Em seguida, **salve o documento completo** (introdução + todos os itens em sequência + observações, sem os rótulos "📋 ITEM N") na pasta da OS:

```bash
PATH_MD="$PASTA_OS/nad-$(date +%Y-%m-%d).md"
# Se já existe arquivo do mesmo dia, adicione sufixo -2, -3...
```

Confirme ao AFT: arquivo salvo + nº de itens. Se não houver pasta de OS resolvida, pergunte onde salvar.

---

## FASE 5 — Registro leve no memory.md (opcional)

Se a OS tem `memory.md`, adicione **uma** linha em `## Registro de atividades` (edição cirúrgica via `Edit`):
```
| DD/MM/AAAA | NAD gerada | N documentos solicitados |
```
Não bloqueie o fluxo se o `memory.md` não existir. Não toque em outras seções.

---

## Encadeamento

- **Origem natural:** ao final de `/preparacao-acao-fiscal`, quando o checklist de documentos a solicitar for aprovado pelo AFT.
- **Também standalone**, a qualquer momento: quando o AFT quer pedir mais documentos durante uma fiscalização já em andamento.
- Depois de gerar, o AFT cola os blocos manualmente no DET (o toolkit não automatiza o preenchimento do DET).
- Não confundir com `/tn-nco` (verbo "Corrigir", para irregularidade já constatada).

---

## Regras

- **Nunca** reescreva a introdução ou as observações fixas — são texto canônico do AFT, copiado verbatim para o DET.
- **Nunca** invente código de ementa, item de NR ou base legal. Ementa só entra quando confirmada (Fase 2); na dúvida, item sem `[...]`.
- O verbo central de cada item é sempre **Apresentar** (documento que se presume existir) — se o AFT quiser exigir correção de algo já constatado como irregular, encaminhe para `/tn-nco`.
- **Respeite o teto de 1000 caracteres** por campo do DET (cada item e o campo de observações). Conte e mostre a contagem na apresentação; se estourar, resolva com o AFT antes de entregar.
- Encoding **UTF-8** em todo o pipeline.
- Esta skill **não** lavra auto, **não** clica no DET e **não** define prazos no texto — apenas redige a notificação de documentos.
