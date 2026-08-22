---
name: aft-tn-nco
model: sonnet
effort: medium
description: >
  Use quando o AFT quiser redigir uma Notificação para Correção de
  Irregularidades (TN-NCO) — o texto que vai no DET notificando a empresa a
  corrigir irregularidades de SST. Dispare com /aft-tn-nco, "cria a
  notificação para corrigir", "redige a TN de correção", "notifica a empresa
  para sanar as irregularidades", "monta a notificação dessas
  irregularidades", "notifica tudo o que foi autuado", "uma notificação para
  cada auto lavrado". Puxa sozinha os autos já lavrados (/aft-autos-lavrados)
  e oferece um checklist das ementas para o AFT escolher o que notificar.
  Acione também PROATIVAMENTE logo após identificar
  irregularidade + NR/item + ementa. NÃO é o auto de infração (/aft-
  auditoria-geral → /aft-gera-ai).
---

# tn-nco — Notificação para Correção de Irregularidades
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


Gera o **texto** de uma notificação para a empresa **corrigir** irregularidades de Segurança e Medicina do Trabalho constatadas em inspeção física ou auditoria documental. O AFT cola o resultado no DET (campo Introdução + um Item Solicitado por irregularidade + campo Observações) e o documento fica salvo como `.md` na pasta da OS.

Esta skill **só redige o texto da notificação**. Ela não lavra auto de infração (isso é `/aft-auditoria-geral` → `/aft-gera-ai`). O preenchimento do template no DET é manual (o AFT cola cada bloco) — o toolkit não automatiza o DET.

## Pasta base
`<OS_ATIVAS>/<EMPREGADOR> <CNPJ>/`

---

## FASE 0 — Resolver a OS (para salvar o .md)

A notificação final é salva como `.md` na pasta da OS, então preciso saber qual é.

1. Se um argumento posicional (CNPJ de 14 dígitos ou substring do nome) foi passado, faça match nas pastas de `<OS_ATIVAS>/`.
2. Se a skill foi encadeada na mesma sessão (ex.: depois de `/aft-auditoria-geral`, `/aft-PGR-analise`), herde a OS do contexto.
3. Múltiplos matches → `AskUserQuestion`. Zero matches e nenhum contexto → pergunte ao AFT o empregador (e, se quiser salvar mesmo sem pasta de OS, ofereça a Área de Trabalho como fallback).

Guarde: `PASTA_OS`, `EMPREGADOR`.

> A resolução da OS é leve de propósito — esta skill funciona standalone. Se não houver pasta de OS, ainda gere o texto no chat e só pergunte onde salvar.

---

## FASE 0.5 — Puxar os autos já lavrados (SEMPRE)

Toda execução desta skill começa consultando o que **já foi autuado** naquela OS — o AFT não precisa ter rodado `/aft-autos-lavrados` antes. A ordem é da fonte mais barata para a mais cara; pare na primeira que responder:

1. **Snapshot do dia.** Se existir `<PASTA_OS>/autos-lavrados.md` com a data de geração de **hoje** (linha `_Snapshot gerado em <YYYY-MM-DD>_`), leia-o e siga. Não rode o scan de novo.
2. **Snapshot velho ou ausente → rode a varredura.** Invoque a tool `Agent` com `subagent_type: "aft-autos-lavrados"`, passando **só esta OS** (caminho absoluto da pasta + CNPJ/CPF, ou os 8 primeiros dígitos, conforme o Passo 1 daquela skill), o `python_path` do `aft-config.md` e o caminho do manual `~/.claude/skills/aft-autos-lavrados/SKILL.md`. Avise o AFT em uma linha ("conferindo no Sistema Auditor o que já foi lavrado…"). Ao voltar, leia o `autos-lavrados.md` gravado.
   - Se o tipo de agente não existir, execute a `/aft-autos-lavrados` inline (o fallback previsto nela).
3. **Sistema Auditor inalcançável** (pasta `PRO` não encontrada, volume do Parallels não montado, erro no scan) → **não trave a notificação**. Diga ao AFT, em uma frase, que não deu para conferir o Sistema Auditor agora e que a lista vem do `memory.md`; use as linhas `- [x]` de `## Autos lavrados` do `memory.md` como fonte dos autos.
4. **Nenhum auto lavrado** (OS ainda não autuada, ou snapshot vazio) → diga isso em uma linha e siga direto para a FASE 1 pelas fontes normais (contexto da sessão / lista colada / pendências). É o caso da notificação preventiva, dupla visita e ME/EPP — perfeitamente normal.

> **Por que sempre:** o pedido típico é "notifica tudo o que foi autuado". Sem este passo, a skill dependia de o AFT ter rodado `/aft-autos-lavrados` antes e acabava notificando de memória — com risco de deixar auto de fora ou notificar o que não foi lavrado. O que vale é o que está no Sistema Auditor.

Guarde, de cada auto **válido** do snapshot: `numero_ai`, `ementa_num`, `ementa_descricao`, `constatação` e a base legal (NR/item), quando identificável. Autos das seções "Autos substituídos" e "Pendentes de transmissão" **não** entram no checklist (o primeiro foi cancelado; o segundo ainda não existe no mundo jurídico).

### Autos vindos de interdição/embargo

Marque como **origem interdição/embargo** o auto que:

- tiver a ementa citada no Termo/RT dentro de `<PASTA_OS>/interdicao-embargo/` (leia os documentos de lá, se a pasta existir); ou
- cuja constatação mencione máquina, equipamento, setor ou frente de serviço **interditado/embargado**.

Esses autos entram no checklist **desmarcados por padrão**, e você explica ao AFT, antes de perguntar:

> A correção das irregularidades que motivaram a interdição/embargo normalmente **não** segue por notificação NCO no DET: o rito é a empresa apresentar laudo/AR, que o AFT julga (`/aft-auditoria-AR-NR12`) para depois levantar a medida (`/aft-embargo-interdicao-levantamento`). Se a mesma exigência valer para **outras** máquinas ou setores não interditados, aí sim faz sentido notificar — nesse caso, redija a exigência mirando os equipamentos não abrangidos pela interdição, e não o objeto interditado.

Quem decide é o AFT: se ele marcar o item, gere normalmente.

---

## FASE 1 — Coletar as irregularidades a notificar

Junte, numa lista única de candidatas:

1. **Autos lavrados** (FASE 0.5) — um candidato por auto válido.
2. **Contexto da sessão:** irregularidades já enquadradas na sessão (saída de `/aft-auditoria-geral`, `/aft-PGR-analise`, ou o `inspecao-fisica.md` da OS) que **ainda não viraram auto**.
3. **Colada:** lista de irregularidades que o AFT colou no prompt.
4. **`memory.md`:** `## Pendências` e `## Inspeção física`, quando as fontes acima não bastarem. Se nada disso existir, peça a lista ao AFT.

Elimine duplicatas pela ementa: se a irregularidade do contexto já tem auto lavrado, ela aparece **uma vez só**, como auto.

### Checklist de seleção (obrigatório quando houver 2+ candidatas)

Primeiro, mostre **a lista inteira numerada** na tela, para o AFT ver tudo de uma vez:

```
Candidatas a notificar — <EMPREGADOR>

 #  Origem        Ementa      Irregularidade
 1  AI 23.227.251-4  001839-2   papeletas "ponto britânico"
 2  AI 23.284.209-4  312467-3   injetora sem proteção  ⚠ interdição
 3  auditoria        —          extintores sem sinalização (sem auto)
```

Depois, colete a seleção com `AskUserQuestion` em modo **`multiSelect: true`** — é o checklist na tela:

- **No máximo 4 opções por pergunta e 4 perguntas por chamada** (limite da tool): agrupe as candidatas em blocos de 4 (`header`: "Autos 1-4", "Autos 5-8"…). Até 16 candidatas cabem em uma chamada; acima disso, faça rodadas sucessivas e avise quantos lotes vêm.
- **`label`** = identificador curto (`AI 23.227.251-4` ou `Ementa 001839-2`); **`description`** = descrição da ementa + a constatação em meia linha, com o aviso `(interdição — ver rito próprio)` quando for o caso.
- Itens de origem interdição/embargo vão sempre por último no bloco, com o aviso acima já apresentado no chat.
- Se o AFT já disse no prompt o que quer ("faz para todos os autos", "só os de NR-12"), **não pergunte**: aplique e mostre a lista do que entrou.

Só uma candidata → não monte checklist; confirme em uma frase.

Para **cada** irregularidade selecionada, você precisa de três coisas (capture o que faltar perguntando ao AFT). Nas que vêm de auto lavrado, a **base legal** e a **ementa** já estão no snapshot — reaproveite-as e escreva só a exigência:

| Campo | O que é | Exemplo |
|---|---|---|
| **Título** | rótulo curto do assunto, em negrito | `Procedimento de Trabalho` |
| **Base legal** | item da NR (ou artigo da CLT / portaria) violado | `item 12.14.1 da NR-12` |
| **Exigência** | o que a empresa deve **fazer** para sanar (não a descrição da falha) | `Elaborar procedimentos de trabalho e segurança...` |

> **Ponto-chave:** o item de uma notificação descreve a **obrigação a cumprir**, não a violação. No auto de infração se descreve o que está errado; aqui se diz o que **fazer**. Redija a exigência como verbo no infinitivo de ação derivado do requisito da norma: *Elaborar, Instalar, Capacitar, Adequar, Implantar, Sinalizar, Aterrar, Providenciar, Manter, Apresentar*. Use o texto da ementa/requisito da NR como base, reescrevendo no modo imperativo de obrigação.

> **Um item por irregularidade narrada.** Gere **exatamente um** item de notificação para cada irregularidade que o AFT relatou — não fracione uma irregularidade narrada em vários itens normativos, mesmo que ela toque mais de um dispositivo da NR. Ex.: se o AFT narrou "injetora sem proteção, com a polia exposta" como **uma** constatação, isso vira **um** item (a base legal pode citar mais de um dispositivo, e a ementa é a que melhor a cobre), não dois. Manter a correspondência 1:1 com o relato do AFT preserva o controle dele sobre o que está sendo notificado e o que ele vai comprovar depois. Se o AFT quiser desmembrar, ele pede explicitamente.

---

## FASE 2 — Buscar a ementa (só quando existir)

> **Pule esta fase nas irregularidades que vieram de auto lavrado** (FASE 0.5): a ementa é a que o Sistema Auditor registrou — use `ementa_num` como está, sem consultar o NotebookLM. Só as irregularidades **sem auto** passam pelas camadas abaixo.

Para cada irregularidade sem auto, busque o **código da ementa** no formato `XXXXXX-X` (ex.: `312467-3`). A ementa é **opcional**: se não houver ementa correspondente (ex.: orientação ou exigência sem ementa específica), o item sai **sem** o `[...]` no final — não invente código.

Estratégia em 3 camadas (mesma de `/aft-auditoria-geral`):

**Camada 1 — NotebookLM (preferencial, requer o setup do /aft-setup):**
1. Escolha a **key** do notebook: a da NR (`nr-12`, `nr-35`, `nr-06`...) ou, para legislação trabalhista, `ementario-legis` / `jornada` / `informalidade`. O script resolve o ID pela cohort do AFT; nunca leia o `notebooks.json` direto.
   - **Nem toda NR tem notebook próprio.** Quando não houver key específica para a NR, **busque no notebook geral de SST `ementario-sst`** — ele cobre o ementário SST inteiro. Não desista da Camada 1 só porque falta a key da NR.
2. Consulte:
   ```bash
   python ~/.claude/skills/_scripts/notebooklm_consulta.py <key> "Qual ementa do ementário cobre a infração ao [BASE_LEGAL] sobre [DESCRICAO]? Retorne o código (formato XXXXXX-X) e a descrição oficial."
   ```
   > **Código 5** (`{"estado": "primeiro-acesso", ...}`): o notebook ainda não está na coleção do
   > AFT — o Google só o registra depois de **uma interação com o chat**. Diga, em uma linha, com
   > o link do campo `url`: *"A base de [título] ainda não está na sua conta. Abra [link], escreva
   > **oi** no chat e me diga 'pronto' — eu repito a consulta."* Depois do "pronto", repita a MESMA
   > consulta. Se o link pedir acesso, o pedido é em https://notebooks-aft.vercel.app.
   > **Código 3** (nada no stdout): não existe para a cohort do AFT; siga sem essa camada.
   > **Reconexão automática:** se a sessão do NotebookLM tiver expirado, ele se reautentica
   > sozinho pelo `NOTEBOOKLM_REFRESH_CMD` (configurado no `/aft-setup`/`/aft-notebooklm-login`).
   > Só passe à Camada 2 se ele ainda assim não responder.
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
Em conformidade com a legislação em vigor, especialmente o previsto na alínea X do art. 18 do Decreto 4552/2002 (Regulamento da Inspeção do Trabalho), fica a empresa NOTIFICADA a cumprir para o cumprimento de obrigações e/ou a correção de irregularidades e adoção de medidas que eliminem os riscos para a saúde e segurança dos trabalhadores, nas instalações ou métodos de trabalho relacionadas nessa notificação:
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

- **Entrada automática:** esta skill sempre consulta antes a `/aft-autos-lavrados` (FASE 0.5) — o AFT não precisa rodá-la à mão.
- **Origem natural:** logo após `/aft-auditoria-geral` ou `/aft-PGR-analise` identificarem irregularidades + ementas, ofereça rodar `/aft-tn-nco` para a empresa corrigir (especialmente em dupla visita / ME-EPP, onde a correção precede a autuação).
- **Interdição/embargo:** para as irregularidades que motivaram a medida, o caminho é `/aft-auditoria-AR-NR12` (julgar o laudo/AR apresentado) e depois `/aft-embargo-interdicao-levantamento` (levantar) ou `/aft-embargo-interdicao-manutencao` (manter) — não a notificação NCO.
- Depois de gerar, o AFT cola os blocos manualmente no DET (o toolkit não automatiza o preenchimento do DET).
- **Depois de lavrada no DET:** ofereça `/aft-email` para redigir o e-mail que avisa a empresa (ou o advogado) da notificação nova.

---

## Regras

- **Nunca** altere o "X" de "alínea X do art. 18" nem reescreva a introdução/observações fixas — são texto canônico do AFT, copiados verbatim para o DET.
- **Nunca** invente código de ementa, item de NR ou base legal. Ementa só entra quando confirmada (vinda do auto lavrado ou da Fase 2); na dúvida, item sem `[...]`.
- **Nunca notifique auto que não existe:** só entram no checklist os autos **válidos** do snapshot. Substituídos (cancelados) e pendentes de transmissão ficam de fora.
- **Nunca decida sozinho** incluir ou excluir irregularidade de interdição/embargo: apresente o rito próprio, deixe desmarcada e siga a escolha do AFT.
- A consulta ao Sistema Auditor **não pode travar a notificação**: se falhar, avise em uma frase e siga pelo `memory.md`.
- Redija cada item como **obrigação a cumprir** (verbo de ação no infinitivo), não como descrição da falha.
- **Respeite o teto de 1000 caracteres** por campo do DET (cada item e o campo de observações). Conte e mostre a contagem na apresentação; se estourar, resolva com o AFT antes de entregar.
- Encoding **UTF-8** em todo o pipeline.
- Esta skill **não** lavra auto, **não** clica no DET e **não** define prazos no texto — apenas redige a notificação de correção.

## Diário de atividades (automático)

Ao concluir o trabalho desta skill numa OS, registre o dia trabalhado no diário —
sem perguntar nada ao AFT (o script deduplica por data+letra; repetir é inofensivo):

```bash
python ~/.claude/skills/_scripts/diario_registrar.py "<pasta da OS>" --tipos E --detalhe "via /aft-tn-nco"
```
