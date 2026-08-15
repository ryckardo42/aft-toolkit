---
name: aft-agenda-det
model: sonnet
effort: low
description: >
  Use quando o AFT quiser os prazos de DET no Google Calendar. Acione com
  /aft-agenda-det, "manda os prazos para o calendário", "agenda os
  vencimentos", "sincroniza o google calendar", "põe o DET na agenda".
  Requer o conector Google Calendar na conta Claude do AFT. Só notificações
  DET vão ao calendário — pendências não.
---

# agenda-det — Prazos de DET no Google Calendar
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
  Calendar → Conectar** (na CLI interativa, `/mcp`). Depois é só rodar `/aft-agenda-det`
  de novo.
- **Pare aqui**, sem erro. (Alternativa sem login: os botões "agendar no Google
  Calendar" do painel — um clique por evento, sem sincronização automática.)

## Passo 1 — Levantar os vencimentos

Resolva a pasta das OS (`<OS_ATIVAS>`, como no bloco acima) e rode o gerador:

```bash
python ~/.claude/skills/_scripts/gerar_painel.py "<OS_ATIVAS>"
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

**Nunca instale a rotina sem o AFT pedir.** A sincronização mexe na agenda pessoal dele;
sob demanda é o padrão, e diária é opção. Só siga este passo se ele responder "sim" à
oferta (feita aqui, no `/aft-setup` Passo 7d ou no `/aft-atualizar` Passo 2d).

A automação depende de **tarefas agendadas do Claude Code** — é o Claude que precisa
acordar, porque o acesso ao calendário é do conector dele, não do toolkit. Não adianta
rotina do sistema (LaunchAgent/Agendador do Windows): ela roda scripts, não o conector.

1. **Diga a limitação antes de criar** (uma frase, sem jargão): *"A tarefa só roda com o
   aplicativo do Claude aberto — se o computador estiver desligado na hora, ela roda na
   próxima vez que você abrir. Serve para quem usa o Claude quase todo dia."*
2. Crie a tarefa agendada com a ferramenta de tarefas agendadas da instalação:
   - identificador: `aft-agenda-det-diaria`
   - horário: **07:15 todo dia** (`15 7 * * *`), depois da rotina do painel — ou o
     horário que o AFT preferir;
   - instrução (a tarefa roda numa sessão nova, sem memória desta conversa, então tem
     que se bastar): *"Rode a skill /aft-agenda-det: espelhe no Google Calendar os prazos
     das notificações DET de todas as OS ativas do AFT Toolkit, pelo conector Google
     Calendar. Siga a skill (Passos 1 a 3). Nunca apague eventos. Se o conector não
     estiver conectado, apenas relate e pare."*
3. **Confira que ficou de pé** (liste as tarefas agendadas) e diga ao AFT o horário.
4. Grave `agenda_det: "diario"` no front-matter do `aft-config.md`.

Se a instalação não tiver tarefas agendadas, explique que a automação não é possível ali
e que basta pedir `/aft-agenda-det` quando quiser (ex.: junto do `/aft-painel` da manhã);
grave `agenda_det: "manual"`.

**Para desligar depois** (o AFT pode mudar de ideia): apague a tarefa `aft-agenda-det-diaria`
e grave `agenda_det: "manual"`. Os eventos já criados **não** são apagados — quem manda
no calendário é o AFT.

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
