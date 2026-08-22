# NotebookLM e a origem das ementas

> Referência da skill /aft-ajuda — leia sob demanda.

Este arquivo explica o que é o NotebookLM, por que o toolkit depende dele, de onde vem o código de ementa que o assistente devolve, o que sai (e o que nunca sai) da máquina do AFT numa consulta, como ativar ou reconectar o acesso e o que continua funcionando quando ele está fora do ar.

---

## O que é o NotebookLM

Em uma frase: **é um "caderno de estudos" do Google onde documentos são carregados e depois consultados em linguagem natural — e o assistente responde citando o que está nos documentos, não o que ele "acha"**. O Google rebatizou o produto como *Google Notebooks* (endereço `notebook.google.com`), mas o toolkit continua chamando de NotebookLM.

O toolkit depende dele por um motivo simples: **é lá que moram os ementários completos** — o ementário de SST, o de legislação trabalhista e notebooks por norma (NR-01, NR-03, NR-04, NR-05, NR-10, NR-12, NR-13, NR-18, NR-24, NR-35, informalidade e outros). São esses notebooks, compartilhados pelo mantenedor, que permitem à habilidade **achar sozinha o código da ementa, a capitulação e a gradação** em vez de pedir tudo ao AFT a cada auto.

Nada disso é obrigatório: sem o NotebookLM o toolkit continua funcionando — só que o assistente passa a indicar o ementário do Google Drive ou a pedir o código diretamente ao AFT.

---

## De onde vem a ementa que a IA devolve

O toolkit busca o código de ementa em **três camadas**, da mais barata e imediata para a mais cara:

| # | Camada | O que é |
|---|---|---|
| 1 | **NotebookLM** (recomendado) | Ementários SST e de legislação + notebooks por NR. É a consulta que a `/aft-consulta` e a `/aft-auditoria-geral` fazem por trás dos panos. |
| 2 | **Google Drive compartilhado** | Ementários por NR em Markdown, numa pasta pública. Rede de segurança para quando o NotebookLM falha. |
| 3 | **O AFT informa o código** | Formato `XXXXXX-X`, conferido por ele no ementário oficial. Último recurso, nunca chute do assistente. |

### A ordem se inverte nas consultoras de NR

Três habilidades são **especialistas de uma norma** e carregam, dentro da própria pasta, o texto da norma e um **catálogo curado das ementas mais lavradas** — com descrição oficial, capitulação e os gatilhos que ligam a situação de campo ao código certo:

| Habilidade | Norma | Catálogo interno |
|---|---|---|
| `/aft-NR01` | Disposições gerais, GRO e PGR | 9 ementas |
| `/aft-NR12` | Máquinas e equipamentos | 16 ementas |
| `/aft-NR18` | Construção civil | 29 ementas |

Nessas três, **o catálogo interno vem primeiro e o NotebookLM é a segunda fonte** — só se recorre a ele quando a situação constatada não casa com nenhuma ementa do catálogo, o que acontece nos casos menos comuns. Por isso a resposta é imediata e **não depende de conexão**.

**Fora dessas três, vale a ordem da tabela acima:** o NotebookLM é a fonte principal de consulta — é a ele que recorrem a `/aft-consulta`, a `/aft-auditoria-geral` (para as NRs sem habilidade especialista) e as demais habilidades que precisam localizar código, capitulação ou gradação.

O AFT não precisa saber nomes de habilidade: o sistema chama a consultora certa pelo contexto da conversa (ou basta dizer "analise conforme a NR-12").

---

## A regra dura: não se inventa ementa

> **Nunca se inventa código de ementa, item de norma, capitulação ou gradação.**
> Se a informação não estiver no catálogo interno nem no NotebookLM, a habilidade **diz que não encontrou e devolve a pergunta ao AFT** — em vez de arriscar um palpite.

E a contrapartida, do lado do auditor:

> **Revise sempre.** A IA é apoio à redação e à organização. O conteúdo jurídico de cada auto, termo e relatório é responsabilidade do Auditor-Fiscal. **Confira o código da ementa no ementário oficial antes de transmitir.**

---

## O que sai da máquina numa consulta

Esta é a parte mais importante para quem trabalha com dado sensível.

**Sai apenas a descrição da irregularidade.** Exemplo do que uma consulta envia: *"máquina sem proteção fixa na zona de prensagem, operador exposto"*.

**Nunca saem:**

- nome de trabalhador;
- CPF (nem de trabalhador, nem de empregador pessoa física);
- razão social, nome fantasia ou CNPJ da empresa fiscalizada;
- qualquer trecho de documento entregue pelo empregador.

Se o relato do AFT trouxer nome ou CPF, a habilidade aplica a pseudonimização do toolkit (`[[TRAB_NN]]`, `[[CPF_NN]]`) e leva ao NotebookLM **só o fato**. O arquivo `.depara` — o que liga os códigos aos dados reais — é sensível: não se compartilha, não se envia por e-mail, não sobe para nuvem.

Regra irmã, do mesmo capítulo de segurança: **nada de serviços online com documentos da fiscalização**. Compressão de PDF, conversão de fotos e validação de arquivos são feitas por scripts locais do toolkit — nunca por compressores ou conversores de site.

---

## Como ativar ou reconectar

**Quem executa tudo é o assistente.** O AFT, no máximo, faz **um login na sua conta Google** numa janela que o próprio assistente abre — e nunca digita comando nenhum.

A habilidade é a **`/aft-notebooklm-login`**. Basta dizer, em linguagem normal: *"conecta o notebooklm"*, *"o ementário parou de responder"*, *"a consulta de ementa falhou"*, *"quais notebooks eu consulto"*. O `/aft-setup` também conduz esse passo na instalação.

O que acontece por trás:

1. O assistente confere se já existe sessão válida — muitas vezes não é preciso fazer nada.
2. Tenta reconectar em silêncio, sem abrir janela.
3. Só se isso falhar, abre a janela do Google para o AFT entrar. Assim que ele entra, o assistente salva a conexão sozinho.
4. Ao final, confere **notebook por notebook** quais a conta do AFT realmente alcança.

Na rotina, a reconexão costuma ser **automática**: quando a sessão expira no meio de uma ação fiscal, o próprio comando de consulta se reautentica sozinho.

### Dois obstáculos comuns (e diferentes entre si)

**1. Pedir acesso.** Se o notebook responde "sem acesso" / "não encontrado", solicite o acesso em **https://notebooks-aft.vercel.app**, com a conta Google, e aguarde a liberação do mantenedor.

**2. O "oi" em cada notebook.** Mesmo já liberado, o Google só coloca um notebook compartilhado na coleção da conta depois de **uma conversa com o chat dele** — abrir o link não basta. Antes disso, a consulta àquele tema falha. É **uma vez na vida** por notebook: abra, escreva **oi** na caixa de chat e feche.

Essa etapa não dá para o assistente fazer pelo AFT: quem tem a conta Google no navegador é ele, e o registro só vale feito por ele.

**Não faça isso nos 47 de uma vez.** Registre só os **dois ementários** no começo; os demais entram quando você precisar deles — o assistente avisa na hora, com o link pronto, e repete a consulta depois que você disser "pronto". O motivo é o limite abaixo.

---

## O limite de consultas por dia

A conta gratuita do NotebookLM aceita por volta de **50 consultas por dia**. Isso vale para tudo o que fala com o chat: a consulta de ementa que as habilidades fazem **e o próprio "oi"** do primeiro acesso.

Duas consequências práticas:

- Registrar os 47 notebooks de saída queimaria quase a cota do dia antes de você fiscalizar qualquer coisa. Daí a regra de registrar sob demanda.
- Se, no fim de um dia pesado, a consulta de ementa começar a falhar "sem motivo", pode ser a cota — e não defeito do toolkit. No dia seguinte volta ao normal; enquanto isso, o ementário no Google Drive continua disponível.

---

## A skill `/notebooklm` é outra coisa

Existe também uma habilidade chamada **`/notebooklm`**, que vem de um projeto de terceiro (`teng-lin/notebooklm-py`) e **não faz parte do aft-toolkit**. Ela dá acesso completo ao NotebookLM: criar notebooks, adicionar fontes, organizar material, gerar artefatos.

A diferença:

| | Para quê | Quem usa |
|---|---|---|
| **Consulta de ementa** | Achar código, capitulação e gradação durante a lavratura | As habilidades do toolkit, por trás dos panos — o AFT nem percebe |
| **`/notebooklm`** | Criar e organizar notebooks próprios do AFT | O AFT, quando quiser montar a sua própria base |

Ou seja: para lavrar auto, o AFT não precisa acionar `/notebooklm` — isso já acontece sozinho. A `/notebooklm` serve para quando **ele mesmo** quiser mexer nos notebooks.

---

## Quando o NotebookLM está fora

Nada trava. O que continua funcionando sem conexão com o ementário:

- **As consultoras `/aft-NR01`, `/aft-NR12` e `/aft-NR18`** — o catálogo curado é local, dentro da pasta da habilidade. Cobrem justamente as normas mais presentes na fiscalização.
- **Todo o fluxo de trabalho** — abrir OS, notificar pelo DET, narrar inspeção, redigir, gerar o TXT do Sistema Auditor, relatório final.
- **Os dimensionamentos por script** (grau de risco/CNAE, SESMT, CIPA, instalações da NR-24), que são cálculo determinístico e nunca dependeram do NotebookLM.

O que muda: para as ementas fora dos catálogos locais, o assistente passa a **indicar o ementário do Google Drive** ou a **pedir o código ao AFT** — e diz isso com todas as letras, em vez de inventar.

Se a consulta de ementa começar a falhar, o caminho é sempre o mesmo: peça ao assistente para **reconectar o NotebookLM** (`/aft-notebooklm-login`). Ele diagnostica e resolve; o AFT não vai ao terminal.
