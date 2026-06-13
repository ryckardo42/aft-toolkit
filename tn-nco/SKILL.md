---
name: tn-nco
description: >
  Use SEMPRE que o AFT quiser redigir/gerar uma Notificação para Correção de
  Irregularidades (TN-NCO) — o texto que vai no DET notificando a empresa a
  corrigir irregularidades de Segurança e Medicina do Trabalho constatadas em
  inspeção física ou auditoria de documentos. Dispare com /tn-nco, ou frases
  como "cria a notificação para corrigir", "redige a TN de correção", "notifica
  a empresa para sanar as irregularidades", "como eu notifico essa empresa?",
  "me ajuda a escrever a notificação de correção", "monta a notificação dessas
  irregularidades". Acione também PROATIVAMENTE logo após identificar uma
  irregularidade + NR/item + ementa (em /inspecao-inicial, /PGR-analise ou
  narrativa de campo), oferecendo gerar a notificação. Produz: introdução fixa
  (alínea X do art. 18 do Decreto 4552/2002) + um item por irregularidade no
  formato "*Título* - item X da NR-Y: <exigência> [ementa]" (ementa via
  NotebookLM, só quando existir) + observações fixas, apresentado BLOCO A BLOCO
  para o AFT copiar item por item no DET e salvo como .md na pasta da OS. NÃO é
  o auto de infração (isso é /inspecao-inicial → /gera-ai) — é só o TEXTO da
  notificação de correção, pronto para colar.
---

# tn-nco — Notificação para Correção de Irregularidades
**AFT Toolkit**

Gera o **texto** de uma notificação para a empresa **corrigir** irregularidades de Segurança e Medicina do Trabalho constatadas em inspeção física ou auditoria documental. O AFT cola o resultado no DET (campo Introdução + um Item Solicitado por irregularidade + campo Observações) e o documento fica salvo como `.md` na pasta da OS.

Esta skill **só redige o texto da notificação**. Ela não lavra auto de infração (isso é `/inspecao-inicial` → `/gera-ai`). O preenchimento do template no DET é manual (o AFT cola cada bloco) — o toolkit não automatiza o DET.

## Pasta base
`~/Documents/AFT/OS ATIVAS/<EMPREGADOR> <CNPJ>/`

---

## FASE 0 — Resolver a OS (para salvar o .md)

A notificação final é salva como `.md` na pasta da OS, então preciso saber qual é.

1. Se um argumento posicional (CNPJ de 14 dígitos ou substring do nome) foi passado, faça match nas pastas de `~/Documents/AFT/OS ATIVAS/`.
2. Se a skill foi encadeada na mesma sessão (ex.: depois de `/inspecao-inicial`, `/PGR-analise`), herde a OS do contexto.
3. Múltiplos matches → `AskUserQuestion`. Zero matches e nenhum contexto → pergunte ao AFT o empregador (e, se quiser salvar mesmo sem pasta de OS, ofereça a Área de Trabalho como fallback).

Guarde: `PASTA_OS`, `EMPREGADOR`.

> A resolução da OS é leve de propósito — esta skill funciona standalone. Se não houver pasta de OS, ainda gere o texto no chat e só pergunte onde salvar.

---

## FASE 1 — Coletar as irregularidades a notificar

A fonte é **contexto da sessão + lista colada** (a skill detecta):

1. **Encadeada / contexto da sessão:** se a sessão já contém irregularidades enquadradas (saída de `/inspecao-inicial`, `/PGR-analise`, ou o `inspecao-fisica.md` da OS), reaproveite-as direto. Confirme com o AFT quais entram na notificação (ofereça marcar/desmarcar).
2. **Colada:** se o AFT colou uma lista de irregularidades no prompt, use-a.
3. **Standalone sem lista:** leia `## Pendências` e `## Inspeção física` do `memory.md` da OS (se existir) e liste candidatas; senão, peça ao AFT a lista.

Para **cada** irregularidade, você precisa de três coisas (capture o que faltar perguntando ao AFT):

| Campo | O que é | Exemplo |
|---|---|---|
| **Título** | rótulo curto do assunto, em negrito | `Procedimento de Trabalho` |
| **Base legal** | item da NR (ou artigo da CLT / portaria) violado | `item 12.14.1 da NR-12` |
| **Exigência** | o que a empresa deve **fazer** para sanar (não a descrição da falha) | `Elaborar procedimentos de trabalho e segurança...` |

> **Ponto-chave:** o item de uma notificação descreve a **obrigação a cumprir**, não a violação. No auto de infração se descreve o que está errado; aqui se diz o que **fazer**. Redija a exigência como verbo no infinitivo de ação derivado do requisito da norma: *Elaborar, Instalar, Capacitar, Adequar, Implantar, Sinalizar, Aterrar, Providenciar, Manter, Apresentar*. Use o texto da ementa/requisito da NR como base, reescrevendo no modo imperativo de obrigação.

> **Um item por irregularidade narrada.** Gere **exatamente um** item de notificação para cada irregularidade que o AFT relatou — não fracione uma irregularidade narrada em vários itens normativos, mesmo que ela toque mais de um dispositivo da NR. Ex.: se o AFT narrou "injetora sem proteção, com a polia exposta" como **uma** constatação, isso vira **um** item (a base legal pode citar mais de um dispositivo, e a ementa é a que melhor a cobre), não dois. Manter a correspondência 1:1 com o relato do AFT preserva o controle dele sobre o que está sendo notificado e o que ele vai comprovar depois. Se o AFT quiser desmembrar, ele pede explicitamente.

---

## FASE 2 — Buscar a ementa (só quando existir)

Para cada irregularidade, busque o **código da ementa** no formato `XXXXXX-X` (ex.: `312467-3`). A ementa é **opcional**: se não houver ementa correspondente (ex.: orientação ou exigência sem ementa específica), o item sai **sem** o `[...]` no final — não invente código.

Estratégia em 3 camadas (mesma de `/inspecao-inicial`):

**Camada 1 — NotebookLM (preferencial, requer o setup do /aft-setup):**
1. Resolva o `notebook_id`: leia `~/.claude/skills/config/notebooks.json` e pegue a key da NR (`nr-12`, `nr-35`, `nr-06`...). Para legislação trabalhista, use `ementario-legis` / `jornada` / `informalidade`.
   - **Nem toda NR tem notebook próprio.** Quando não houver key específica para a NR, **busque no notebook geral de SST `ementario-sst`** — ele cobre o ementário SST inteiro. Não desista da Camada 1 só porque falta a key da NR.
2. Consulte:
   ```bash
   notebooklm ask "Qual ementa do ementário cobre a infração ao [BASE_LEGAL] sobre [DESCRICAO]? Retorne o código (formato XXXXXX-X) e a descrição oficial." --notebook [notebook_id] --json
   ```
3. Extraia o código com regex `\d{6}-\d` do `answer` ou de `references[].cited_text`.

**Camada 2 — Ementário no Google Drive (manual):** oriente o AFT a abrir
https://drive.google.com/drive/folders/1bktX9TkDIoix4iQuca3Yr5aWCfv97GSg?usp=sharing
(pasta `EMENTAS SST` → `ementasNR[XX].md`), localizar o item e colar o trecho da ementa.

**Camada 3 — perguntar ao AFT:** se as camadas 1–2 não retornarem código confiável, pergunte se há ementa. Se o AFT disser que não há, deixe o item sem `[...]`.

Antes de montar, apresente ao AFT a tabela de itens resolvidos para conferência (Título · Base legal · Exigência · Ementa). Ele pode ajustar redação ou códigos.

---

## FASE 3 — Montar a notificação

O texto tem **três partes fixas/variáveis**. Preserve acentuação (UTF-8).

### Introdução (FIXA — copie literalmente)

```
Em conformidade com a legislação em vigor, especialmente o previsto na alínea X do art. 18 do Decreto 4552/2002 (Regulamento da Inspeção do Trabalho), fica a empresa NOTIFICADA a cumprir as exigências de Segurança e Medicina do Trabalho relacionadas nessa notificação:
```

> ⚠️ **O "X" em "alínea X" está CORRETO e é intencional** — designa a décima alínea (alínea 10) do art. 18. **Nunca** substitua o "X" por uma letra, número arábico ou qualquer outro valor, e nunca "corrija" essa frase. Copie a introdução exatamente como está acima.

### Itens (um por irregularidade)

Formato de cada item:

```
*<TÍTULO>* - <BASE_LEGAL>: <EXIGÊNCIA>. [<EMENTA>]
```

- O `[<EMENTA>]` final só aparece **quando existe** ementa (Fase 2). Sem ementa → termine no ponto final da exigência.
- Mantenha o negrito do título com asteriscos (`*Título*`), exatamente como no exemplo.
- **Limite de 1000 caracteres por item.** Cada campo do DET (a descrição de cada item e o campo de observações) aceita no **máximo 1000 caracteres**. Mantenha cada item **dentro desse limite** — a redação da exigência deve ser objetiva e direta ao ponto. Não desmembre uma irregularidade narrada em vários itens só para caber (a regra é 1 item por irregularidade); em vez disso, **enxugue a redação**. Se, mesmo enxuto, um item passar de 1000 caracteres, **avise o AFT** e ofereça duas saídas (encurtar a exigência mantendo a base legal, ou — só se o AFT autorizar — desmembrar em mais de um item).

**Exemplo (referência canônica do AFT):**
```
*Procedimento de Trabalho* - item 12.14.1 da NR-12: Elaborar procedimentos de trabalho e segurança para máquinas e equipamentos, específicos e padronizados, a partir da apreciação de riscos. [312467-3]
```

### Observações (FIXAS — copie literalmente)

```
Comprovação de cumprimento e pedido de prorrogação:
> A adoção das  medidas notificadas devem ser comprovadas pelo empregador  nos prazos previstos nos itens. A dificuldade de cumprimento, ou qualquer manifestação deverá ser expressamente manifestada à fiscalização em cada item. A empresa poderá pedir prazo específico, caso deseje, para o item específico;

Dúvidas:
>  Perguntas/esclarecimentos adicionais podem ser feitos no  "Canal de Comunicação" dentro dessa própria notificação, ou pelos e-mails disponíveis na notificação.
```

> Esse texto de observações é o boilerplate canônico do AFT — reproduza-o verbatim, sem reescrever ou "consertar" a redação.

---

## FASE 4 — Apresentar no chat (bloco a bloco) + salvar .md

O AFT **copia cada parte individualmente** para os campos correspondentes do DET (Introdução · um Item Solicitado por irregularidade · Observações). Por isso, apresente cada parte em seu **próprio bloco de código copiável**, com rótulo claro.

**Cheque o limite de 1000 caracteres antes de apresentar.** Cada campo do DET aceita no máximo 1000 caracteres. Conte os caracteres de **cada item** e do **bloco de observações**, e mostre a contagem ao lado do rótulo (ex.: `ITEM 1 (308/1000)`). Se algum item passar de 1000, **pare e resolva com o AFT** (enxugar a redação ou, com autorização, desmembrar) antes de entregar — nunca entregue um item que o AFT não conseguiria colar inteiro no DET.

Estrutura da apresentação no chat:

````
📋 **INTRODUÇÃO** — cole no campo *Introdução* do DET
```
<texto fixo da introdução>
```

📋 **ITEM 1** — novo *Item Solicitado*
```
*Procedimento de Trabalho* - item 12.14.1 da NR-12: Elaborar... [312467-3]
```

📋 **ITEM 2** — novo *Item Solicitado*
```
*<Título>* - <base legal>: <exigência>. [<ementa>]
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
PATH_MD="$PASTA_OS/tn-nco-$(date +%Y-%m-%d).md"
# Se já existe arquivo do mesmo dia, adicione sufixo -2, -3...
```

Confirme ao AFT: arquivo salvo + nº de itens. Se não houver pasta de OS resolvida, pergunte onde salvar (ou ofereça a Área de Trabalho).

---

## FASE 5 — Registro leve no memory.md (opcional)

Se a OS tem `memory.md`, adicione **uma** linha em `## Registro de atividades` (edição cirúrgica via `Edit`):
```
| DD/MM/AAAA | TN-NCO de correção gerada | N itens |
```
Não bloqueie o fluxo se o `memory.md` não existir. Não toque em outras seções.

---

## Encadeamento

- **Origem natural:** logo após `/inspecao-inicial` ou `/PGR-analise` identificarem irregularidades + ementas, ofereça rodar `/tn-nco` para a empresa corrigir (especialmente em dupla visita / ME-EPP, onde a correção precede a autuação).
- Depois de gerar, o AFT cola os blocos manualmente no DET (o toolkit não automatiza o preenchimento do DET).

---

## Regras

- **Nunca** altere o "X" de "alínea X do art. 18" nem reescreva a introdução/observações fixas — são texto canônico do AFT, copiados verbatim para o DET.
- **Nunca** invente código de ementa, item de NR ou base legal. Ementa só entra quando confirmada (Fase 2); na dúvida, item sem `[...]`.
- Redija cada item como **obrigação a cumprir** (verbo de ação no infinitivo), não como descrição da falha.
- **Respeite o teto de 1000 caracteres** por campo do DET (cada item e o campo de observações). Conte e mostre a contagem na apresentação; se estourar, resolva com o AFT antes de entregar.
- Encoding **UTF-8** em todo o pipeline.
- Esta skill **não** lavra auto, **não** clica no DET e **não** define prazos no texto — apenas redige a notificação de correção.
