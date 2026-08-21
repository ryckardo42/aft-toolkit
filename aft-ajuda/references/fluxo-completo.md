> Referência da skill /aft-ajuda — leia sob demanda.

Como uma ação fiscal caminha dentro do toolkit, do cadastro ao relatório final, e as três ideias que precisam estar claras antes de qualquer coisa: a pasta, a ficha e a sessão.

## As três ideias que sustentam tudo

Quem entende estas três para de se perder. Quase toda dúvida de AFT novo é, no
fundo, uma delas.

### 1. A pasta da empresa

Toda a fiscalização acontece dentro de **uma pasta por empresa**, guardada em
`OS ATIVAS`, dentro da pasta AFT (criada pelo `/aft-setup`, normalmente em
Documentos). Tudo o que o assistente produz cai ali: autos, notificações,
relatórios, fotos, documentos recebidos.

Consequência prática: quem já fiscalizava antes do toolkit **move as pastas
antigas para dentro de `OS ATIVAS`** e pede para organizar — a
`/aft-organiza-os` lê o conteúdo, classifica cada documento pelo que ele é
(notificação, auto, documento entregue) e monta tudo no padrão, com um plano
que o AFT aprova antes de qualquer arquivo ser mexido. Ela nunca apaga nada.

Onde a pasta está de verdade não se adivinha (no Windows, "Documentos" quase
nunca fica onde parece): o caminho certo vem do
`_scripts/pasta_aft.py --os-ativas`.

### 2. O `memory.md` — a ficha da fiscalização

Dentro da pasta de cada empresa há um arquivo de texto simples chamado
`memory.md`. É a **capa da OS**: identificação do empregador, CNPJ ou CPF,
município, RI, endereço, efetivo, CNAE e grau de risco; número da OS e da
Demanda do SFIT com vencimento; as notificações do DET com seus prazos; as
ementas que a OS mandou fiscalizar; as anotações da inspeção e da análise
documental; os autos redigidos; os que já foram efetivamente transmitidos; e o
registro do que foi feito dia a dia.

**Por que ele existe.** O assistente não guarda lembrança de uma conversa para
a outra. A cada conversa nova ele começa do zero, sem saber quem é a empresa,
o que já foi constatado ou quais autos já foram lavrados. O `memory.md` é a
memória externa da auditoria: ele lê a ficha antes de trabalhar e grava nela o
que apura, e por isso o AFT nunca precisa recontar a história.

É também por ela que as habilidades conversam entre si — o `/aft-painel` mostra
os prazos que estão na ficha, a `/aft-auditoria-geral` transforma em autos as
anotações registradas ali, a `/aft-autos-lavrados` marca o que já foi
transmitido, a `/aft-relatorio` monta o relatório final a partir do que a ficha
acumulou.

É um arquivo comum: o AFT pode abrir, ler e corrigir quando quiser, e ele nunca
sai do computador. Quanto mais fiel a ficha, mais o assistente acerta — e um
dado errado ali sai errado em tudo o que vem depois. Vale conferi-la de vez em
quando.

### 3. A sessão por empresa

No aplicativo do Claude, cada empresa fiscalizada tem a **sua própria sessão de
conversa**, no grupo "OS ATIVAS" da barra lateral, criada automaticamente
assim que a auditoria é cadastrada. Pense em cada sessão como uma aba separada:
ela guarda o histórico daquela fiscalização e carrega o contexto daquela
empresa — dados, prazos, achados, documentos já processados.

**Trabalhe sempre dentro da sessão da empresa.** Pedir um auto, uma análise de
PGR ou uma conferência de prazo numa sessão errada faz o assistente trabalhar
sem o contexto certo, com risco de misturar auditorias. Fora de qualquer sessão
de empresa ficam só as dúvidas gerais do toolkit — como as desta skill.

A criação é automática: o vigia de sessões aplica sozinho quando o aplicativo
fecha, e a sessão nova aparece na abertura seguinte. Não há o que fazer.

No **Codex** as sessões por empresa não existem; lá o AFT organiza as conversas
do jeito dele (a recomendação é um projeto único apontando para `OS ATIVAS` e
um chat fixado por auditoria). Nenhuma habilidade depende disso.

## Você não precisa decorar nome de habilidade

Todas começam com `aft-` e aparecem ao digitar `/aft-` na caixa de texto, mas
**decorar não é necessário**: basta pedir em português. "Cheguei da inspeção e
vou narrar o que vi" aciona a `/aft-inspecao-fisica`; "faça a auditoria do PGR"
aciona a `/aft-PGR-analise`. O assistente escolhe a habilidade pelo que foi
pedido.

## O fluxo, etapa por etapa

Ninguém precisa percorrer tudo: cada habilidade funciona isolada. Esta é a
ordem natural de quem está começando.

| # | Etapa | Habilidade | O que sai disso |
|---|---|---|---|
| 1 | Instalar, uma vez só | `/aft-setup` | Pasta AFT, dados do auditor (CIF, UORG), perfil e painel ligado |
| 2 | Conferir se está tudo certo | `/aft-doctor` | Diagnóstico em 🟢 🟡 🔴 — só verifica, não altera |
| 3 | Trazer fiscalizações antigas | `/aft-organiza-os` | Pastas pré-toolkit no padrão, com `memory.md` |
| 4 | Abrir a auditoria | `/aft-nova-auditoria` | A pasta da empresa e a ficha `memory.md` |
| 5 | Planejar antes da visita | `/aft-preparacao-acao-fiscal` · `/aft-NAD` | Dossiê para levar a campo; notificação de documentos no DET |
| 6 | Narrar a visita | `/aft-inspecao-fisica` | `inspecao-fisica.md` — os fatos, sem enquadramento |
| 7 | Analisar os documentos | `/aft-PGR-analise` · `/aft-aet-auditoria` · `/aft-jornada-analise` · `/aft-auditoria-AR-NR12` · `/aft-analise-acidente` · `/aft-consulta` | Constatações na ficha, com página citada |
| 8 | Lavrar os autos | `/aft-auditoria-geral` → `/aft-revisa-auto` → `/aft-gera-ai` | Autos redigidos, revisados e o TXT importável |
| 9 | Risco grave e iminente | `/aft-embargo-interdicao` (e manutenção / levantamento) | Relatório Técnico em `.docx` + autos derivados |
| 10 | Notificar para corrigir | `/aft-tn-nco` · `/aft-email` | Texto pronto para colar no DET; e-mail de aviso |
| 11 | Acompanhar prazos | `/aft-painel` · `/aft-agenda-det` | Painel no navegador; vencimentos no Google Calendar |
| 12 | Fechar a ação | `/aft-autos-lavrados` · `/aft-relatorio` | O que foi mesmo transmitido; o relatório final |
| 13 | Manter em dia | `/aft-atualizar` | Habilidades novas e correções |

Detalhe do passo 6 que costuma gerar dúvida: a `/aft-inspecao-fisica` é
**puramente descritiva**. Ela não cita NR, não indica ementa, não sugere
capitulação. A separação é proposital — primeiro se fixam os fatos, depois se
discute o enquadramento. Quem enquadra é a `/aft-auditoria-geral`, no passo 8,
e ela trabalha a partir de duas fontes que podem coexistir: o
`inspecao-fisica.md` e as constatações da análise documental anotadas na ficha.

Irregularidade flagrada já na primeira visita não precisa esperar resposta de
notificação: pode virar auto na hora, ficando redigida e pronta mesmo que a
lavratura no sistema venha depois.

## Os quatro assessores

A imagem que costuma resolver a confusão sobre a lavratura. Imagine quatro
assessores numa sala, cada um com uma única tarefa:

- **O Escrivão** (`/aft-auditoria-geral`) ouve o que o AFT viu e escreve a
  minuta do auto.
- **O Revisor** (`/aft-revisa-auto`) trabalha numa sala fechada e nunca ouviu a
  conversa: só lê o papel, com olhos de quem vai contestar aquilo no
  julgamento. Confere quem, o quê, quando, onde e como, arruma parágrafos e
  acentos — mas não muda a tese nem inventa nada.
- **O Empacotador** (`/aft-gera-ai`) não escreve uma linha do auto: põe o texto
  no envelope certo, com o carimbo da unidade e os anexos, no formato que o
  Sistema Auditor aceita. E entrega o envelope ao AFT, porque **quem leva ao
  correio é sempre ele**: nenhum assessor transmite auto.
- **O Conferente** (`/aft-autos-lavrados`) abre depois a lista do que foi
  entregue e compara com a do que tinha sido preparado, item por item: este foi
  lavrado, este ficou na gaveta, este chegou sem rascunho.

## Onde cada coisa é gravada

| Arquivo | Onde | O que é |
|---|---|---|
| `memory.md` | raiz da pasta da OS | A ficha da fiscalização |
| `inspecao-fisica.md` | raiz da pasta da OS | O relato de campo, com nomes reais (é prova) |
| `autos.md` | pasta da OS ou `interdicao-embargo/` | Os autos redigidos, entrada do `/aft-gera-ai` |
| TXT do Sistema Auditor + anexos | `AUTOS/Autos DD-MM/` | O que se importa pelo botão "Imp. txt" |
| Relatório Técnico `.docx` | `interdicao-embargo/` | Interdição, embargo, manutenção, levantamento |
| `aft-config.md` | raiz da pasta AFT | Dados do auditor: CIF, UORG, município |

Para a lista completa e sempre atualizada:
`python ~/.claude/skills/_scripts/ajuda_arquitetura.py --bloco dados`.

## O que o toolkit nunca faz sozinho

- **Não transmite nada.** Nem auto, nem notificação do DET, nem termo. Prepara,
  mostra, e quem transmite é o AFT.
- **Não decide enquadramento.** Sugere ementa e fundamentação; a decisão é do
  AFT, que confere o código no ementário oficial antes de transmitir.
- **Não manda documento de fiscalização para fora.** Compressão de PDF,
  conversão de foto e validação de arquivo são feitas por programas que rodam
  na própria máquina.
