---
name: aft-bom-dia
model: sonnet
effort: low
description: >
  Use quando o AFT abrir o dia cumprimentando — "bom dia", "boa tarde",
  "boa noite", "/aft-bom-dia", "vamos começar", "o que eu tenho hoje",
  "me põe a par", "resumo do dia", "abre o dia". Roda a rotina da manhã:
  confere se o toolkit está em dia, atualiza os autos lavrados no Sistema
  Auditor, sincroniza as notificações do DET, regenera o painel e entrega
  um briefing na ordem do que arde mais — entrega da empresa ainda não
  vista, DET vencido, DET vencendo, auditoria envelhecendo, pendências e
  diário. Não redige documento nenhum e não transmite nada.
---

# aft-bom-dia — a rotina de abertura do dia
**AFT Toolkit**

> **Onde ficam as pastas das OS.** Nunca presuma `~/Documents/AFT`: resolva **uma
> vez, no início**, e use o que voltar onde este texto disser `<OS_ATIVAS>` (a
> pasta com as OS) ou `<PASTA_AFT>` (a pasta acima dela). Nas mensagens ao AFT,
> escreva o caminho de verdade — nunca ecoe `<OS_ATIVAS>` na tela.
>
> ```bash
> python ~/.claude/skills/_scripts/pasta_aft.py --os-ativas   # -> <OS_ATIVAS>
> python ~/.claude/skills/_scripts/pasta_aft.py --path        # -> <PASTA_AFT>
> ```
>
> No Windows, invoque o Python pelo `python_path` do `aft-config.md`.

## Objetivo

Dar ao AFT, em um cumprimento, o retrato do dia: o que mudou desde ontem e o que
cobra ação hoje. A skill **orquestra** — chama as outras e lê o que elas apuram.
Ela mesma não redige documento, não lavra auto, não notifica ninguém e não
transmite coisa alguma.

Tom: assessor que já chegou antes e leu tudo. Curto, sem jargão de programador,
sem tabela gigante. Quem decide o que fazer com o dia é o AFT.

## Quando NÃO sequestrar a conversa

"Bom dia" no meio de outra coisa é só educação. **Se a sessão já está tratando de
uma auditoria ou de uma tarefa em andamento**, responda ao cumprimento em uma
linha e pergunte, também em uma linha, se ele quer a rotina da manhã. Só rode
sem perguntar quando o cumprimento **abre** a conversa.

## Passo 0 — Saudação, pasta e "já rodei hoje?"

1. **Saudação pelo relógio local** (`date +%H:%M`): até 12h "Bom dia", até 18h
   "Boa tarde", depois "Boa noite". Use o `tratamento` do `aft-config.md` se
   houver (ver a persona do assessor no perfil).
2. Resolva `<OS_ATIVAS>` e `<PASTA_AFT>` com o `pasta_aft.py`.
3. **Rodou hoje?** O marcador é uma linha com a data:
   ```bash
   cat "<PASTA_AFT>/.bom-dia" 2>/dev/null
   ```
   Se a data for a de hoje, diga em uma linha que a rotina já rodou hoje (com a
   hora) e **pergunte** se ele quer rodar de novo. Se ele não quiser, entregue
   só o briefing do Passo 5 a partir do painel — sem sync e sem varredura.
   No fim de uma execução completa, carimbe:
   ```bash
   date "+%d/%m/%Y %H:%M" > "<PASTA_AFT>/.bom-dia"
   ```

## Passo 1 — O toolkit está em dia?

A instalação normal é um clone em `~/.claude/skills`. Quando ela não for git — há
quem instale por cópia, e quem mantenha o clone em `~/Documents/aft-toolkit` e
sincronize dali —, tente o segundo caminho antes de desistir:

```bash
git -C ~/.claude/skills fetch origin --quiet && git -C ~/.claude/skills log HEAD..origin/main --oneline
```

- **Lista vazia** → não diga nada (toolkit em dia não é notícia).
- **Lista com commits** → avise em uma frase quantas novidades há e **proponha**
  o `/aft-atualizar`. **Nunca atualize sozinho**: atualizar mexe na instalação,
  e a decisão é do AFT. Se ele aceitar, chame a `/aft-atualizar` e volte aqui.
- **Nenhum dos dois é repositório git** → siga em silêncio; isso não é defeito e
  não vale interromper a manhã. Se ele perguntar, o diagnóstico é o
  `/aft-doctor`.

## Passo 2 — Autos lavrados (dispare cedo)

O AFT pode ter transmitido autos no Sistema Auditor desde ontem. Chame a
**`/aft-autos-lavrados` sem argumento** — sem argumento ela já varre **todas as
OS ATIVAS** em lote, no agente isolado, em segundo plano. Dispare **antes** dos
Passos 3 e 4, para a varredura correr enquanto o DET sincroniza.

> **Todo dia, e em todas as OS — não troque isso por heurística nenhuma.** É
> tentador varrer só as OS "defasadas" (o `autos-lavrados.md` mais antigo que N
> dias) ou só as que têm rascunho de auto esperando. **As duas ideias estão
> erradas**, pela mesma razão: o AFT lavra direto no Sistema Auditor, fora do
> toolkit. O `autos-lavrados.md` diz quando a varredura passou, **não** quando
> houve lavratura — a rotina de ontem deixa o arquivo com cara de novo mesmo que
> três autos tenham sido lavrados hoje de manhã. E auto digitado direto no
> Sistema Auditor não deixa rascunho, então a OS não teria sinal nenhum e ficaria
> de fora para sempre. A única fonte da verdade sobre lavratura é o Sistema
> Auditor, e a única forma de saber é olhar. Esta é a parte cara da rotina, e é
> cara por necessidade.

- Não pergunte nada aqui. Se alguma OS ficar sem CNPJ identificável, a própria
  skill devolve a linha de status — repasse no briefing, sem interromper.
- **Sistema Auditor fora de alcance** (Windows desligado, disco C: do Parallels
  não montado no Mac): registre em uma linha no briefing e **siga**. Manhã sem
  Sistema Auditor não é manhã perdida.

## Passo 3 — DET: sincronizar as fichas e baixar o que falta

O DET é a parte que precisa do crachá do AFT logado. **Não repita aqui como o
token chega ao painel** — está em `~/.claude/skills/config/canal-token-det.md`
(via 1: o navegador do assistente; via 2: o botão Sincronizar da extensão).

1. **Servidor do painel no ar:**
   ```bash
   curl -s http://127.0.0.1:8347/api/ping
   ```
   Sem resposta, reerga com
   `python ~/.claude/skills/_scripts/instalar_servidor_painel.py reiniciar`.
2. **Token:** siga o `canal-token-det.md`. Tendo navegador, faça a via 1 sozinho.
   Não tendo — ou dando errado —, peça ao AFT, **em uma frase**, para abrir a aba
   do DET logado no Chrome e clicar em **Sincronizar**.
3. **Varredura:**
   ```bash
   python ~/.claude/skills/_scripts/det_baixar.py --varredura "<OS_ATIVAS>"
   ```
   Ela faz, de uma vez: o sync das fichas (notificação nova entra na seção
   `## Notificações DET` do `memory.md`, prazo alterado é corrigido, o triângulo
   amarelo do DET é espelhado) e o download do que falta nas pastas. **Nunca
   toca em notificação com triângulo amarelo** — o alerta é o aviso de que há
   entrega que o AFT ainda não viu, e apagá-lo por conta própria seria mentir
   para o próprio auditor. Essas voltam em `pendentes` e alimentam o item 1 do
   briefing.
4. **`token_expirado`** no meio: o crachá vale ~30 minutos. Renove (via 1 ou
   Sincronizar) e rode de novo — tudo é idempotente, nada baixa duas vezes.
   **Se não houver token nenhum**, não trave a manhã: diga em uma linha que as
   fichas ficaram sem sincronizar hoje, siga para o Passo 4 e avise que os
   números do briefing são os de ontem.

## Passo 4 — Regenerar o painel e ler o resumo

```bash
python ~/.claude/skills/_scripts/gerar_painel.py "<OS_ATIVAS>" --bom-dia
```

**Use sempre o `--bom-dia`.** O painel é regenerado igual; o que muda é o
stdout, que sai com o bloco do briefing em vez do resumo inteiro — o resumo
completo passa de 16 KB (só a agenda de vencimentos são 5 KB), e tudo o que ele
imprime entra no seu contexto. O briefing usa metade disso.

Tudo que o briefing cita está no bloco **`bom_dia`**, já apurado e já ordenado —
**não reabra `memory.md` para recontar nada**:

| campo | o que é |
|---|---|
| `entregas_nao_vistas` | o que está parado esperando o AFT — triângulo amarelo do DET, pedido de prazo/dispensa aguardando decisão dele, ou mensagem no canal (o campo `motivo` diz qual) |
| `dets_vencidos` | prazo vencido, **do mais antigo para o mais novo** (`dias` negativo) |
| `dets_vencendo_7d` | vence hoje ou nos próximos 7 dias |
| `os_longas` | OS já vencida, a vencer em ≤30 dias, ou aberta há ≥120 dias |
| `pendencias` | as linhas `- [ ]` da seção Pendências, por auditoria |
| `diario` | dias úteis do mês decorridos × com registro no diário (hoje não conta) |

Cada notificação vem com `entregues`, `nao_enviados` e `aguardando` — a contagem
de itens que o próprio DET informa. **Use sempre.** "Venceu" não diz o que houve:
vencido com 5 itens entregues é documento esperando análise; vencido com item não
enviado é a omissão do art. 630, § 4º, da CLT. Nunca escreva "sem entrega" só
porque a data passou — o painel já errou assim uma vez, e a frase seguinte falava
em autuar. Diga o fato; **quem enquadra é o AFT**.

`os_longas` usa a data de abertura que o painel deriva sozinho: o
**Vencimento da OS** do SFIT quando a ficha o tem, senão a linha "OS cadastrada"
do Registro de atividades.

## Passo 5 — O briefing

Ordem fixa, do que arde mais para o que arde menos. **Seção sem nada, seção que
não aparece** — silêncio é boa notícia, não precisa de linha dizendo "nada aqui".

1. **Esperando o senhor** (`entregas_nao_vistas`) — uma linha por notificação:
   empregador, código e o `motivo`. É trabalho parado à espera do AFT, e por isso
   vem primeiro. Sendo triângulo amarelo, ofereça a `/aft-det-baixar <código>`
   para abrir o pacote (é ela que apaga o alerta, como ato consciente).
2. **DET vencidos** — do mais antigo primeiro: empregador, código, prazo, **há
   quantos dias venceu** e o que a empresa fez (entregues / não enviados). Se as
   fichas não sincronizaram hoje (Passo 3), diga aqui, em meia linha, que a lista
   é a de ontem.
3. **DET vencendo em até 7 dias** — mesma forma, com os dias que faltam.
4. **Auditorias envelhecendo** — OS vencida primeiro (há quantos dias), depois a
   vencer, depois as abertas há mais de 4 meses. Uma linha cada.
5. **Pendências** — o **total** ("11 pendências em 6 auditorias") e, detalhadas,
   **só as das auditorias que já apareceram acima**. O resto fica no painel; diga
   isso em meia linha, não despeje a lista inteira.
6. **Diário** — só quando houver dia útil do mês sem registro: quantos são e as
   datas. Ofereça a `/aft-diario`.
   **De tarde ou de noite, olhe também o dia de hoje.** Quem cumprimenta com
   "boa tarde" costuma ter passado a manhã fora — em inspeção, em diligência, no
   trânsito. Se o `bom_dia.diario` não contar hoje (ele nunca conta: o dia mal
   começou quando a rotina é de manhã) e a saudação for de tarde ou de noite,
   pergunte em uma linha se ele esteve em campo hoje. Se esteve, ofereça a
   `/aft-inspecao-fisica` para narrar a visita — é ela que registra o dia na OS
   certa, com as letras B e C. Uma pergunta, não um interrogatório: se ele disser
   que não, siga.
7. **Autos lavrados** — quando o agente do Passo 2 voltar: o que apareceu de novo
   desde ontem, e as OS que ele não conseguiu varrer.
8. **Arrumação** (`bom_dia.arrumacao`) — o último e o menos urgente:
   - `pastas_sem_ficha`: pasta dentro de `OS ATIVAS/` **sem `memory.md`**. É o
     caso grave, ainda que raro: o painel só enxerga quem tem ficha, então uma
     auditoria copiada para lá é invisível — não conta prazo, não aparece em
     card nenhum, não entra em briefing nenhum. Ofereça a `/aft-organiza-os`.
   - `fora_do_lugar`: por OS, quantos arquivos volumosos estão soltos na raiz
     (com até três exemplos) e subpastas `item<N>` de download do DET fora de
     `NOTIFICACOES/`. Uma linha por OS, e a oferta da `/aft-organiza-os`
     **naquela OS**, nunca no lote.

> **Não rode a `/aft-organiza-os` por conta própria, e nunca em todas as OS.**
> A FASE 2 dela abre a primeira página de **cada PDF** de cada pasta e classifica
> um a um — é o assistente lendo, não um script. Num acervo real (274 PDFs,
> medidos em 26/08/2026) isso custa duas ordens de grandeza mais que a rotina
> inteira da manhã, e ainda para na FASE 3 pedindo aprovação de um plano de
> movimentação de arquivos. Aqui a regra é **detectar e oferecer**: o custo alto
> só se paga quando há motivo, e só na OS que tem o motivo.

Feche com **até três prioridades** para o dia, na ordem em que você as faria, e
ofereça começar pela primeira. Uma frase cada. Nada de plano do dia com horário:
a agenda é do AFT.

## Regras

- **A skill não decide e não transmite.** Ela lê, mostra e oferece. Quem baixa,
  redige, lavra e transmite é o AFT — pelas skills próprias de cada coisa.
- **Nenhum passo trava a manhã.** Toolkit sem git, Sistema Auditor fora de
  alcance, DET sem token: cada um vira uma linha no briefing, e o resto roda.
- **Privacidade:** o briefing fica na tela. Não escreva relatório, não crie
  arquivo, não mande nada para lugar nenhum. O token do DET nunca aparece no
  chat, em log ou em nome de arquivo.
- **Não registre esta rotina no diário de atividades.** Abrir o dia não é
  trabalho numa auditoria específica; o diário é para o que se fez em cada OS.
- **OS encerrada parada em `OS ATIVAS/`** entra à toa na varredura do Passo 2
  (o painel a esconde, a `/aft-autos-lavrados` não). Aparecendo, sugira ao AFT
  arquivá-la — uma linha, sem insistir.
