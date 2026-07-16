---
name: agenda-det
model: sonnet
description: >
  Use SEMPRE que o Auditor-Fiscal do Trabalho (AFT) quiser os prazos de DET no
  Google Calendar. Acione com /agenda-det, "manda os prazos para o calendário",
  "agenda os vencimentos", "sincroniza o google calendar", "põe o DET na
  agenda". Lê a agenda consolidada de vencimentos do gerar_painel.py (campo
  "vencimentos" do JSON) e, pelo conector Google Calendar do Claude, cria um
  evento de DIA INTEIRO por notificação DET com prazo — título
  'DET <código> <12 primeiros caracteres do empregador>' —, atualiza a data
  quando o prazo muda (prorrogação) e renomeia com ✓ quando a notificação é
  marcada como checada no memory.md. Nunca apaga eventos e nunca toca em
  eventos fora do padrão "DET ...". Requer o conector Google Calendar
  conectado na conta Claude do AFT (a skill orienta a conexão se faltar).
  Pendências não vão ao calendário — só notificações DET.
---

# agenda-det — Prazos de DET no Google Calendar
**AFT Toolkit**

## Objetivo

Espelhar no **Google Calendar do AFT** os prazos das notificações DET de todas as OS
ativas, para o vencimento aparecer onde o AFT já olha todo dia (celular, relógio,
notificação do Google). Um evento de **dia inteiro** por notificação, com título na
convenção fixa:

```
DET <código da notificação> <12 primeiros caracteres do empregador>
```

Ex.: `DET RMNHKD5EWIUTJZ THIAGO CASTR`. A fonte da verdade continua sendo o
`memory.md` de cada OS — esta skill só **espelha** (cria/atualiza/renomeia eventos);
nunca escreve nos `memory.md` e nunca apaga eventos.

## Passo 0 — Conector Google Calendar

Esta skill depende do **conector Google Calendar do Claude** (não é API própria — a
autenticação é feita uma única vez, pela interface do Claude, e nenhuma senha ou token
passa por aqui). Verifique se as ferramentas do conector estão disponíveis (tente listar
os calendários). Se não estiverem:

- Explique em uma frase: *"Falta conectar o Google Calendar ao Claude — é um login
  único do Google, feito com segurança pela própria Anthropic."*
- Oriente: no aplicativo do Claude/claude.ai → **Configurações → Conectores → Google
  Calendar → Conectar** (na CLI interativa, `/mcp`). Depois é só rodar `/agenda-det`
  de novo.
- **Pare aqui**, sem erro. (Alternativa sem login: os botões "agendar no Google
  Calendar" do painel — um clique por evento, sem sincronização automática.)

## Passo 1 — Levantar os vencimentos

Resolva a pasta das OS como no `/painel` (Passo 0 de lá: `pasta_os:` do
`aft-config.md`; padrão `~/Documents/AFT/OS ATIVAS`) e rode o gerador:

```bash
python ~/.claude/skills/_scripts/gerar_painel.py "<PASTA_OS_ATIVAS>"
```

Do JSON impresso, use o campo **`vencimentos`**: a lista já vem pronta e ordenada, um
item por notificação DET com prazo (`tipo: "det"`), com `titulo` (na convenção acima),
`codigo`, `empregador`, `prazo_iso`, `prazo_br` e `checado` (estado `[x]`/`[ ]` no
memory.md). **Ignore os itens `tipo: "pendencia"`** — pendências aparecem no painel,
mas não vão ao calendário. Itens sem `codigo` também não vão (não dá para reconciliar
sem identificador) — apenas relate-os no final.

## Passo 2 — Reconciliar com o calendário

Sempre no **calendário principal** da conta. A **chave é o código da notificação**:
qualquer evento cujo título contenha o código pertence àquela notificação — inclusive
eventos que o AFT criou à mão antes da skill existir (ex.: "📨 Prazo DET <código> —
<nome>"); esses são **adotados** como estão (o título manual não é reescrito — só a
data, se o prazo mudou, e o ✓, se checada). Para cada notificação DET com código,
procure o evento existente (busca por texto pelo código; janela ampla, ex. 6 meses
para trás e 12 para a frente) e aplique UMA das regras:

| Situação no memory.md | Evento no calendário | Ação |
|---|---|---|
| `[ ]` aberta, prazo hoje ou futuro | não existe | **Criar** evento de dia inteiro em `prazo_iso`, título = `titulo` |
| `[ ]` aberta, prazo JÁ VENCIDO | não existe | nada — evento no passado não notifica ninguém; quem grita o vencido é o painel |
| `[ ]` aberta | existe, data diferente | **Atualizar** a data (prorrogação de prazo) |
| `[ ]` aberta | existe, data igual | nada |
| `[x]` checada | existe, sem ✓ | **Renomear** para `✓ <título atual>` (a data fica) |
| `[x]` checada | existe, já com ✓ | nada |
| `[x]` checada | não existe | nada (não criar evento de coisa já resolvida) |

Detalhes do evento criado:
- **Dia inteiro** na data do prazo (sem hora — o Google notifica de manhã).
- Lembretes: popup **1 dia** e **3 dias** antes.
- Descrição: `Notificação DET <código> — <empregador por extenso> (AFT Toolkit)`.
- Nada além disso: **sem CNPJ, sem RI, sem conteúdo da fiscalização** — o evento vai
  para a nuvem do Google; o título+descrição acima é o mínimo necessário e suficiente.

## Passo 3 — Relatório

Uma resposta compacta com o que mudou (e só o que mudou):

```
📅 Google Calendar sincronizado — N notificações conferidas

  + criado    DET S8JHKBXN96R96H MASTER AGROI » 16/07/2026
  ↻ prazo     DET RV0HHWLHKIDFW3 BUENO 28 RES » 29/05 → 29/07/2026
  ✓ checada   DET S8JHJJPG1OZT85 THIAGO CASTR
  (demais sem mudança)
```

Se nada mudou, uma frase basta ("calendário já estava em dia — N eventos conferidos").

## Passo 4 — (Opcional) Rotina diária

Se o AFT quiser que isso rode sozinho ("sincroniza todo dia", oferecido também no
`/aft-setup`/`/aft-atualizar`): use o recurso de **tarefas agendadas do Claude Code**
(se disponível nesta instalação) para rodar `/agenda-det` toda manhã (sugestão: 07:15,
depois da rotina do painel). Grave `agenda_det: "diario"` no front-matter do
`aft-config.md` (ou `agenda_det: "manual"` se preferir só sob demanda) — é o registro
de que a oferta já foi feita. Se o recurso de tarefas agendadas não existir na
instalação, explique que basta pedir `/agenda-det` quando quiser (ex.: junto do
`/painel` da manhã).

## Regras

- **Nunca apague eventos** — nem os ✓, nem órfãos. Quem manda no calendário é o AFT.
- **Nunca toque em evento sem código de notificação no título**: o calendário é
  pessoal; a skill só administra eventos identificáveis pela chave (os que ela criou
  ou os manuais adotados). Evento com código que não está em nenhuma OS ativa
  (fiscalização encerrada, termo avulso) também fica intocado.
- **Sempre busque antes de criar** — rodar a skill duas vezes seguidas não pode
  duplicar nada (o código da notificação é a chave).
- A skill **não escreve em nenhum memory.md** — a direção é só memory.md → calendário.
  (Marcar como checada continua sendo no painel interativo ou pelas skills.)
- Privacidade: o evento carrega só código + 12 caracteres do nome + nome por extenso
  na descrição. Nunca inclua CPF, CNPJ, RI, itens da notificação ou qualquer conteúdo
  da fiscalização em título, descrição ou local do evento.
- Se o conector falhar no meio (token expirado), relate o que já foi feito e oriente
  reconectar — não tente outra via de acesso ao Google.
