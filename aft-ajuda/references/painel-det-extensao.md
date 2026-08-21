> Referência da skill /aft-ajuda — leia sob demanda.

Este arquivo cobre o painel de auditorias, a extensão Sync DET para Chrome/Edge, o download de notificações do DET (`/aft-det-baixar`), o espelho dos prazos no Google Calendar (`/aft-agenda-det`) e o que fazer quando alguma dessas coisas não funciona.

---

## 1. O painel (`/aft-painel`)

### O que é

O retrato da carteira de fiscalização do AFT, montado **com o que já está no computador dele**. O painel lê a ficha (`memory.md`) de cada empresa em `OS ATIVAS/` e desenha uma página com um card por auditoria.

### O que mostra

| No card (tela inicial) | No detalhe (ao clicar no card) |
|---|---|
| Empregador, CNPJ, município, RI, nº de trabalhadores, CNAE, grau de risco, início/vencimento, embargo | Notificações DET, com código, rótulo e as datas do sync (lavratura, ciência, entregas) |
| Cor por **urgência do prazo** de DET — perder prazo é o erro mais caro | Pendências em aberto, com botão de registrar e resolver |
| Selo ⚠️ "atualização pendente" e selo ✉️ "mensagem no DET" (a empresa escreveu no canal de comunicação e aguarda resposta) | Auditoria de documentos (as constatações registradas) |
| Notificação cancelada no DET aparece riscada, fora do contador e fora de todo cálculo de prazo | Inspeção física, registro de atividades, autos de infração lavrados, relatórios `.md` da OS |

Além da lista de próximos vencimentos em ordem de data.

### As abas

- **Auditorias** — os cards.
- **Calendário** — o espelho visual do diário de atividades (`/aft-diario`): o mês inteiro num olhar, as empresas trabalhadas em cada dia com as letras A-F, contador de dias trabalhados e os dias úteis sem registro marcados com pontilhado. Inclui OS encerradas e arquivadas: é histórico, não retrato do que está em andamento. No modo interativo há o botão "Registrar dia trabalhado".

### É 100% local

Sem internet, sem servidor na nuvem, sem conta. Junto com o painel roda um **pequeno programa só na máquina do AFT** (o "servidor local"), que escuta no endereço `127.0.0.1:8347` — `127.0.0.1` é o nome técnico da própria máquina, não sai dela. É esse programa que transforma os cards em botões para o trabalho mecânico:

- marcar notificação DET como respondida / reabrir;
- dispensar o alerta ⚠️ de atualização pendente;
- registrar e resolver pendências;
- registrar constatação da auditoria de documentos;
- registrar o dia trabalhado;
- mudar o status da OS; ligar/desligar embargo ou interdição.

**Toda gravação faz backup antes** (cópia do arquivo em `.backups/`) e altera só a linha em questão.

O servidor é instalado pelo `/aft-setup` e **sobe sozinho quando o AFT liga o computador** (Tarefa Agendada no Windows, LaunchAgent no Mac). Se o painel for aberto por duplo clique no arquivo, e não pelo endereço, ele fica **somente leitura** — os botões não funcionam.

### O painel só LÊ as fichas

O `/aft-painel` nunca escreve nos `memory.md`. Quem cadastra a auditoria é a `/aft-nova-auditoria`; quem preenche o resto são as demais skills e os botões do painel.

---

## 2. A extensão Sync DET (Chrome e Edge)

### O que resolve

Copiar, notificação por notificação, o código e o prazo de entrega do DET para a ficha de cada auditoria é uma das tarefas mais repetitivas da fiscalização. Com a extensão isso vira **um clique**: as notificações caem direto na ficha da OS certa e o painel passa a acompanhar os vencimentos sozinho. **Fim da digitação manual de prazo.**

É gratuita, funciona no Chrome e no Edge, e instala em cerca de 15 segundos.

### Pré-requisito

O **servidor do painel precisa estar ligado**. Quem instalou pelo `/aft-setup` já o tem sempre ligado. Na dúvida: `/aft-doctor` confere e explica como resolver.

### Instalando (uma vez só)

1. Abrir a página da extensão na loja do Chrome e clicar em **Usar no Chrome**:
   `https://chromewebstore.google.com/detail/sync-det-%E2%80%94-sisos-aft-tool/khmecjbidgcndmgmkbpfncjgmmfehiem`
   No **Microsoft Edge** o caminho é o mesmo link — a loja pede só uma confirmação a mais ("Permitir extensões de outras lojas") e o botão vira **Instalar**.
2. **Fixar na barra do navegador**: clicar no ícone de quebra-cabeça (🧩) e depois no alfinete ao lado de "Sync DET". Assim ela fica sempre à vista.
3. Clicar no ícone da extensão. Na primeira abertura aparece a tela de configuração: **marcar a caixa PAINEL LOCAL (AFT TOOLKIT)** e clicar em **Salvar**. É a única configuração necessária.
4. Os campos **URL do SisOS** e **Token de acesso** ficam **em branco** — pertencem a outro modo de uso (o SisOS, um sistema na nuvem), desnecessário com o painel local. O endereço `http://127.0.0.1:8347` que já aparece no campo do painel é o padrão: não mexer.

### Usando no dia a dia

1. Entrar no DET normalmente (`auditor-det.sit.trabalho.gov.br`), com o login **gov.br**. Só de navegar logado, a extensão captura sozinha a **chave de sessão** que o próprio site já usa — pense nela como o crachá que o DET entrega na entrada. O AFT não copia, não cola e **não digita senha nenhuma na extensão**.
2. Clicar no botão flutuante **Sincronizar**, no canto direito, no final da página do DET.

### O que acontece e o que aparece

A extensão entrega a chave ao painel local; o painel consulta a **API oficial do DET** para cada OS de `OS ATIVAS/` que tenha CNPJ (ou CPF) na ficha, e atualiza o `memory.md`:

- notificação nova entra como `- [ ] CÓDIGO — prazo dd/mm/aaaa`, com uma sub-linha de detalhes (lavratura, ciência, última entrega, situação no DET, alertas);
- prazo que mudou no DET é corrigido na linha existente;
- notificação **cancelada** no DET nunca é inserida; a que já estava na ficha passa a dizer "CANCELADA no DET" e deixa de contar prazo (quem apaga a linha é o AFT).

O resultado aparece num aviso na própria página do DET, por exemplo: `✅ Local: 2 importada(s) · 1 prazo(s) atualizado(s)`.

**Notificação de outra fiscalização** do mesmo empregador (de um colega, ou de uma ação antiga) **não entra**: o vínculo é o número do RI declarado na ficha da OS. O aviso conta quantas foram ignoradas, para o AFT saber que existem. Nada é descartado em silêncio.

---

## 3. O que a extensão NUNCA faz

Vale repetir ao AFT, palavra por palavra, quando ele perguntar sobre segurança:

- **Não marca notificação como respondida.** O `[ ]`/`[x]` da ficha é decisão do AFT, no painel.
- **Não altera o que o AFT escreveu** no `memory.md`. As anotações dele ficam intactas; a máquina mexe só na sub-linha que ela mesma escreveu.
- **Faz backup antes de gravar.** Todo `memory.md` alterado tem cópia prévia em `.backups/`.
- **Nada vai para a internet.** A conversa entre extensão e painel acontece inteira dentro do computador (`127.0.0.1` é o endereço da própria máquina). A única saída de rede é a consulta do painel à API do próprio governo.
- **Não vê a senha do AFT.** O login é no gov.br; a extensão só observa a chave de sessão que o site já usa.
- **Não lê a tela do DET nem faz cópia de página.** Os dados vêm da API oficial, consultada pelo painel — a extensão nunca chama essa API.
- **A chave de sessão vive só na memória**, expira sozinha em cerca de 30 minutos e **nunca é gravada em arquivo**.

---

## 4. `/aft-det-baixar` — baixar os arquivos da notificação

Baixa da API oficial do DET, em segundos e sem navegador, tudo o que existe numa notificação. Usa a mesma chave de sessão que a extensão emprestou ao painel (guardada por 25 minutos na memória do servidor) — a chave nunca passa pela conversa com o assistente.

Pode ser disparada de dois jeitos, que fazem exatamente a mesma coisa:
- o botão **⬇ baixar arquivos** no cartão de notificações do painel;
- a skill `/aft-det-baixar` no chat, aceitando código da notificação, CNPJ ou nome do empregador.

**O que baixa e para onde** — tudo vai para o pacote da notificação, dentro de `NOTIFICACOES/` na pasta da OS (a raiz da OS fica limpa):

```
<OS>/NOTIFICACOES/<CODIGO> <dd-mm-aaaa>/
├── notificacao-<CODIGO>.pdf              o PDF da notificação
├── relatorio-atendimento-<CODIGO>.pdf    sempre atualizado a cada download
├── historico-itens.md                    prorrogações, justificativas e status de cada item
├── canal-comunicacao/                    só quando há mensagens
│   ├── mensagens.md, anexos, historico-canal.pdf
└── item<N>_<descrição oficial>/          um por item solicitado
    ├── <arquivos entregues pela empresa>
    └── invalidados/                      o que o AFT rejeitou ou dispensou no DET
```

Detalhes úteis:
- **Não baixa duas vezes** o mesmo arquivo; entrega parcelada ou prorrogação acumula no mesmo pacote.
- Cada download entra sozinho no **Registro de atividades** do `memory.md`.
- O download **registra a visualização no DET**: o triângulo amarelo "Existe atualização pendente" se apaga na tela do site, como se o AFT tivesse aberto a notificação pelo navegador.
- Encadeia naturalmente com a análise dos documentos entregues — que é outra skill.

---

## 5. `/aft-agenda-det` — os prazos no Google Calendar

Espelha no Google Calendar do AFT os prazos das notificações DET de todas as OS ativas, para o vencimento aparecer onde ele já olha todo dia: celular, relógio, notificação do Google.

- Um **evento de dia inteiro** por notificação, com título fixo: `DET <código da notificação> <12 primeiros caracteres do empregador>`.
- A fonte da verdade continua sendo o `memory.md`. A skill só espelha: **cria, atualiza e renomeia** eventos; nunca escreve nas fichas e **nunca apaga** evento.
- Só **notificações DET** vão ao calendário — pendências não.
- **Requer o conector Google Calendar** na conta Claude do AFT: um login único do Google, feito com segurança pela própria Anthropic, em Configurações → Conectores → Google Calendar → Conectar.
- **Alternativa sem login:** os botões "agendar no Google Calendar" do próprio painel — um clique por evento, sem sincronização automática.

---

## 6. Quando não funciona

| Sintoma | O que significa | O que fazer |
|---|---|---|
| **"Painel não está no ar"** | O servidor local não está rodando. | O AFT pede `/aft-painel` ao assistente (ou `/aft-doctor`, que diagnostica). Quem executa qualquer comando é sempre o assistente — o AFT nunca abre terminal. |
| **"Token DET não capturado"** | A extensão ainda não viu o AFT navegar logado. | Abrir qualquer página interna do DET (a lista de notificações, por exemplo) e clicar em **Sincronizar** de novo. |
| **Sincronizou, mas a notificação não apareceu** | A OS não tem como ser ligada ao empregador, ou a notificação é de outro RI. | Conferir se a ficha (`memory.md`) da OS tem o **CNPJ ou CPF**: sem ele o painel não sabe qual empregador consultar no DET. Se o aviso disse que houve notificações **ignoradas**, é o caso de RI de outra fiscalização — conferir o campo `ri:` da ficha. |
| **Botões do painel não respondem** | O painel foi aberto por duplo clique no arquivo, e não pelo endereço do servidor — nesse modo ele é somente leitura. | Abrir pelo endereço `http://127.0.0.1:8347`, com o servidor ligado. |
| **`/aft-det-baixar` diz que o token expirou** | A chave de sessão vale ~25 minutos. | Voltar à aba do DET, logado, e clicar em **Sincronizar**; depois repetir o download. |

---

## Skills relacionadas

`/aft-painel` · `/aft-doctor` · `/aft-setup` · `/aft-nova-auditoria` · `/aft-det-baixar` · `/aft-agenda-det` · `/aft-diario`
