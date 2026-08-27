---
fonte: Apostila-AFT-Toolkit (.docx)
origem: Apostila-AFT-Toolkit 3.docx
gerado_por: minha-apostila-toolkit/converter.py
aviso: NAO EDITE ESTE ARQUIVO. Ele e regerado da apostila a cada atualizacao.
---

AFT-Toolkit 
Inteligência artificial para a Auditoria-Fiscal do Trabalho
*Apostila de instalação e uso — Claude Code/Codex-ChatGPT(Windows)*
github.com/ryckardo42/aft-toolkit
Julho de 2026 · versão 3.0 (15/08/26)

# O AFT-TOOLKIT

INTRODUÇÃO
A arquitetura em passo a passo — para quem está começando.

Até pouco tempo atrás, no curso que gravei de IA para a ENIT,  o jeito principal de usar inteligência artificial era o chat no navegador: você digitava uma pergunta, a IA respondia em texto, e a conversa ficava só nisso. Só que, nos últimos tempos, algo mudou. A IA deixou de ficar presa à caixinha de texto e passou a conseguir operar o computador de verdade: criar arquivos, criar pastas, renomear, organizar, executar tarefas que antes exigiam que você fizesse tudo manualmente. É exatamente nesse novo cenário que o AFT Toolkit se encaixa.
Para entender como isso é possível, precisamos separar duas coisas que costumam ser confundidas: o modelo e o harness. O modelo é a parte que "pensa": é o DeepSeek, o Claude, o Gemini, o ChatGPT. Você manda texto, ele devolve texto, e é só isso que ele sabe fazer sozinho. Um modelo puro não abre arquivo nenhum do seu computador, não roda comando, não lembra do que aconteceu no dia anterior e se perde no meio de uma tarefa mais longa. Quem faz esse trabalho é uma camada que fica em volta do modelo, e o nome dela vem justamente daí: harness.
O Claude Code é um harness. O Codex, da OpenAI, também é. Os dois seguem a mesma lógica: pegam um modelo e dão a ele, digamos, um corpo para trabalhar de verdade, um jeito de controlar a máquina, mexer em pastas, criar e modificar arquivos. O AFT Toolkit é construído em cima desse harness: as habilidades que você vai conhecer nas próximas seções são instruções que ensinam o Claude Code (ou o Codex) a executar, dentro desse corpo, as tarefas específicas da fiscalização do trabalho.

# 1. O que é o AFT Toolkit

Este toolkit nasce de uma ideia simples: transformar o Claude Code/Codex — que você vai entender melhor mais à frente — num verdadeiro sistema operacional do seu trabalho de AFT no dia a dia. Ele pode te ajudar a:
Preparação da ação fiscal antes de ir a campo;
Registro do relato da sua inspeção física e separação de ementas;
Redação do texto de notificações e autos de infração (e já gera o TXT importável pelo Sistema Auditor);
Ajuda no relatório técnico de interdição;
Auditoria de PGR, AET;
Acompanhar os prazos do DET, baixar documentos,  lançando cada vencimento na sua agenda;

O AFT Toolkit é um conjunto de habilidades (roteiros especializados) para o Claude Code, o assistente de IA da Anthropic que roda no seu computador — e também para o Codex, o assistente da OpenAI: as mesmas habilidades servem aos dois. Cada habilidade ensina a IA a executar uma tarefa da fiscalização do trabalho que consideramos repetitiva.
Uma das grandes vantagens é também a conexão com os NotebookLMs do Google, que reúnem uma base de informação muito boa sobre a Auditoria Fiscal do Trabalho — é de lá que várias habilidades consultam ementas e fundamentação.
Você conversa com o Claude/Codex em português, como num chat. A diferença é que, com as habilidades instaladas, ele conhece os modelos oficiais, os textos jurídicos padronizados e as convenções do Sistema Auditor, e trabalha e cria diretamente nas pastas do seu computador.

## 1.1 Por que o Claude Code/Codex, e não um chat comum?

Execução local. Os arquivos das suas fiscalizações ficam no seu computador, na pasta Documentos\AFT. As habilidades criam pastas, salvam autos, convertem fotos de evidência em PDF e geram o TXT diretamente no disco — coisas que um chat de navegador não faz.
Anonimização de dados pessoais. O toolkit usa pseudonimização reversível: nomes e CPFs de trabalhadores são trocados por códigos (tokens) nos textos processados pela IA, e os dados reais só entram no arquivo final por um script local, determinístico, que roda no seu computador. A seção 4 explica em detalhe.
Fluxo completo. Do relato ditado por voz na volta da inspeção até o arquivo pronto para o botão “imp. txt” do Sistema Auditor, passando pela consulta de ementas e pela redação revisável de cada auto.
Você no controle. A IA redige e organiza; quem decide, revisa e transmite é sempre o Auditor. Nenhum documento sai do seu computador sem a sua ação.

## 1.2 Os modelos do Claude: Haiku, Sonnet e Opus

No aplicativo Claude existe um seletor de modelo. Não é outro programa nem outra IA: é o mesmo Claude, em três "tamanhos" diferentes — como escolher entre econômico, completo e turbo num carro. Você não precisa entender de tecnologia para usar o toolkit, mas é útil saber o que cada um faz:
Haiku — o mais rápido. Responde quase na hora. Bom para perguntas curtas e diretas, mas pode entregar algo mais superficial em tarefas longas, como redigir um auto inteiro.
Sonnet — o equilíbrio do dia a dia. É o modelo padrão do AFT Toolkit e dá conta bem da grande maioria das habilidades — redigir autos, analisar um PGR, montar a jornada — com boa velocidade. Na prática, você nem precisa trocar nada.
Opus — o mais cuidadoso. Pensa mais antes de responder e por isso demora um pouco mais. Vale a pena reservar para os casos mais difíceis — um acidente de trabalho complexo, um PGR muito extenso, uma jornada de trabalho com várias inconsistências — quando compensa esperar um pouco mais por uma análise mais cuidadosa.
*Dica:* ***DEIXE COMO PADRÃO O SONNET - ALTO.*** *Só vale procurar o seletor de modelo e trocar para o Opus se sentir que uma tarefa muito complexa saiu rápida demais e superficial — para o uso comum, não é necessário tocar nisso.*

# 2. Instalação em 4 passos (Windows)

Tempo estimado: 15 minutos. Você só faz isso uma vez. Você instala manualmente apenas o aplicativo e o Git (passos 1 e 2); do Python em diante, quem digita comando é o Claude/Codex.

## 2.1 Passo 1 — Instale o aplicativo Claude ou Codex

Baixe o aplicativo para Windows em  ou o ChatGPT https://chatgpt.com/pt-BR/download/
Instale e entre com a sua conta. Par ao Claude, é preciso um plano que inclua o Claude Code (Pro ou superior). Recomendo o de R$100 mensais. Já no ChatGPT o CODEX roda em qualquer plano (mas os limites variam, e vc pode se frustar no gratuito).
É preciso entender que no aplicativo do claude  nós vamos usar majoritariamente a aba “</>Code”, que acessa pastas, documentos, cria arquivos, pastas, processa scripts localmente e etc. É nela que a mágia vai acontecer.

Também recomendo algumas configurações do Claude. Aqui estão:

Descreva seu trabalho como “jurídico” e em ‘Instrucões para qualquer IA, eu gosto dessa (a mesma que uso no Copilot da Microsfot):

***# Sou um  Auditor-Fiscal do Trabalho (AFT), servidor público  federal, cuja principal função é garantir o cumprimento da legislação trabalhista  em empresas e instituições, tanto públicas quanto privadas, em todo o território nacional.***

***Minhas  atividades são multifacetadas e incluem:***

Fiscalização: Realizar inspeções nos locais de trabalho para verificar se estão sendo respeitados os direitos dos trabalhadores, como jornada de trabalho, salário mínimo, registro em carteira, depósitos de FGTS e outros.***

Segurança e Saúde no Trabalho: Fiscalizar o cumprimento das Normas Regulamentadoras (NRs), garantindo que o ambiente de trabalho seja seguro e saudável, e analisar as causas de acidentes de trabalho.***

Combate a Irregularidades: Atuar no combate a formas graves de violação de direitos, como:***
***Trabalho análogo à escravidão.***
***Trabalho infantil.***
***Informalidade.***

O próximo passo é definir a ‘Privacidade’, desmarcando a opção abaixo:

Em ‘Capacidades’ deixe tudo ativado em Memória. Você também consegue importar memória de outroas IA que você usa, como GPT e Gemini:

Já no CODEX:

## 2.2 Passo 2 — Instale o Git

No Windows, o aplicativo exige o Git para abrir sessões locais na aba </> Code — sem ele, aparece a mensagem “Git is required for local sessions”. Por isso este é o único programa que você instala à mão:
Baixe em  e instale com as opções padrão (basta clicar “Next” até o fim).
Feche o aplicativo de verdade: ele continua rodando na bandeja do sistema (ícones perto do relógio). Clique com o botão direito no ícone na bandeja e escolha Sair — fechar só a janela no X não basta.
Abra o aplicativo de novo.
Para que serve o Git? Nada de programação — é a ferramenta que baixa o toolkit e busca as atualizações futuras (o “downloader”), e traz o Git Bash, o ambiente de terminal que o Claude Code usa no Windows.

## 2.3 Passo 3 — Deixe o Claude/CODEX instalar o resto

Abra a interface de código (botão </> Code) e inicie uma conversa nova, ou o CODEX:

O Claude/Codex pede para você escolher uma pasta para a sessão (é a pasta do computador em que ele vai trabalhar). Escolha qualquer pasta “meus documentos” (`C:\Users\seu-nome\Documents`) para esse momento.   Depois da instalação, quando `Documentos\AFT` existir, prefira escolhê-la nas conversas do dia a dia.
É importante deixar o Claude/Codex trabalhar sem interrupções, sem toda hora te pedir confirmação de coisas. Por isso recomendo ativar a opção “ignorar permissões”, aqui:

O Claude Code/Codex é um assistente que executa comandos no seu computador (sempre pedindo a sua permissão antes). Você vai colar três mensagens, uma de cada vez, esperando ele terminar cada uma.

Por que três e não uma só? Porque a terceira mensagem mexe na pasta de onde o próprio Claude/Codex lê as suas habilidades. Ele é treinado para desconfiar de conteúdo que vem da internet e vai direto para essa pasta — e faz muito bem. As três mensagens fazem baixar → ele conferir → instalar: quando chega a hora de instalar, ele já leu o que está instalando. Não é burocracia; é ele conferindo o que vai rodar na sua máquina.
Mensagem 1 — o básico (Git, Python e a ferramenta de ementas):

``` Copie a partir daqui
Prepare este computador para o AFT Toolkit. Faça nesta ordem, me explicando cada passo em linguagem simples:
1. Confirme que o Git está instalado e funcionando (git --version).
2. Verifique se o Python 3 está instalado e funcionando no terminal; se não, instale com winget (pacote Python.Python.3.12).
3. Instale o pacote notebooklm-py com os extras browser e cookies: pipx install "notebooklm-py[browser,cookies]" (se não houver pipx, instale o pipx antes). Ao final, confirme que o comando notebooklm responde (notebooklm --help). Não é preciso baixar navegador nenhum nem o Visual C++: o login usa o Edge/Chrome que já existe no computador.
```

Mensagem 2 — baixar o toolkit e deixar ele ler:

```
Baixe o repositório https://github.com/ryckardo42/aft-toolkit.git para a pasta Documentos\aft-toolkit, usando git clone. Depois liste o que veio, leia o README.md e uns três arquivos SKILL.md e me expliqueem linguagem simples o que essas habilidades fazem, se alguma coisa roda sozinha e se você vê algum risco.
```
Deixe ele processar a mensagem e executar...

Mensagem 3 — instalar (só depois que ele responder a mensagem 2):
Agora mova todo o conteúdo da pasta Documentos\aft-toolkit, inclusive a pasta oculta .git, para ~/.claude/skills. O resultado tem que ser ~/.claude/skills/aft-setup/SKILL.md — e NÃO ~/.claude/skills/aft-toolkit/aft-setup. Se ~/.claude/skills já tiver alguma coisa dentro, preserve o que existe e apenas acrescente. No final, liste as habilidades e me diga se preciso reiniciar o aplicativo.
```
Se você não tiver selecionar logo abaixo da caixa de chato o “Ignorar permissões, o Claude/Codex vai pedir permissão para cada comando — basta clicar em Permitir. Isso é normal e desejável: nada roda no seu computador sem o seu OK. Eu acho chato, e por isso prefiro selecionar “Ignorar permissões” como na imagem acima (seta vermelha de baixo).

O que ele está instalando?
- Python — roda os scripts locais do toolkit: conversão de fotos em PDF, geração do arquivo do Sistema Auditor e validação de arquivos de ponto, dentre tantos outros.
- notebooklm — a ferramenta que consulta os ementários no NotebookLM para achar o código da ementa sozinho. Aqui fica instalado o comando de terminal; o login (na sua conta Google) o Claude/Codex conduz para você no passo "Recomendado — Ative o NotebookLM" abaixo, sem terminal.

Se o Claude/Codex recusar a mensagem 3 ("não instalo conteúdo de fonte que não consigo verificar"), não discuta com ele nem insista — argumentar costuma deixá-lo mais desconfiado, não menos. Peça primeiro: *"***me explique o que exatamente te preocupa nesse conteúdo que você acabou de ler". Se ainda assim recusar, use o Plano B no fim desta página: os mesmos comandos, executados por você. Não é sinal de que há algo errado com o toolkit — é uma precaução genérica dele sobre o tipo de ação, não sobre a origem.

## 2.4 Passo 4 — Reinicie e configure com /aft-setup

Feche e reabra o aplicativo Claude/Codex (para ele reconhecer as habilidades novas e o Git).
Numa conversa nova do </> Code (pasta da sessão: Documentos), digite /aft-setup.
A habilidade de configuração cria a sua pasta de trabalho (Documentos\AFT), pergunta seu nome, sua CIF e a sua lotação, e instala as bibliotecas Python necessárias. Esses dados entram automaticamente em todos os arquivos do Sistema Auditor dali em diante — você nunca mais digita.
Você não precisa saber o código da sua unidade. Basta dizer a cidade (ex.: “Anápolis”) ou o nome da unidade: o toolkit traz a tabela oficial das UORGs do país e descobre sozinho o código de 9 dígitos, o município e o CEP. Como pode haver mais de uma unidade na mesma cidade (Superintendência, Gerência, Agência), o Claude/Codex lista as opções e você só escolhe a sua.
O claude Code vai tomar por padrão, a partir daqui, a pasta Documentos (C:\Users\seu-nome\Documents). Depois da instalação, vai ser criada a pasta Documentos\AFT\OS ATIVAS. É dentro dela que vc vai colocar as pastas das suas empresas em auditoria. Lembre-se: Uma pasta por Empresa (RI).
É essa pasta que vai concentrar todas as suas auditorias!
Confira se está tudo certo: digite /aft-doctor. Ele faz um check-up da instalação (Python, Git, se as habilidades foram reconhecidas, sua configuração e as bibliotecas) e responde, em linguagem simples, o que está OK e o que falta — com a solução de cada item. Rode-o agora, logo após o /aft-setup, e sempre que algo parar de funcionar. É só diagnóstico: não altera nada.

## 2.5 Ative o NotebookLM (essencial)

A ferramenta notebooklm já foi instalada no Passo 3. Falta liberar o acesso e fazer login para as habilidades encontrarem o código da ementa sozinhas, consultando os ementários e NRs em notebooks compartilhados:
Entre em  com a sua conta Google e solicite acesso, caso você ainda não tenha.
Aguarde a liberação pelo mantenedor.
Faça login (abre o navegador, com a sua conta Google): peça ao Claude/Codex para rodar notebooklm login e depois notebooklm list para confirmar que os notebooks aparecem. O /aft-setup também conduz esse passo.
Sem o NotebookLM (agora chamado Google Notebooks) tudo continua funcionando: as habilidades indicam o ementário compartilhado no Google Drive ou pedem o código da ementa a você.
Tem uma coisa importante aqui: Apesar de eu ter liberado os notebooks para você, o Claude/Codex não vai conseguir acessar esses notebooks se você pelo menos não falar um “oi” para cada um deles. Eles só passam a fazer parte do seu repositório de notebooks quando você inicia uma conversa com eles em “https://notebook.google.com/”. Por isso te recomendo já: Abra o portal que eu criei e que centraliza todos os notebooks  >> Abra aqueles que você vai trabalhar >>  digite um “oi” na caixa de chat de cada um deles. Pronto. Agora o google irá adicionar esse notebook na sua base pessoal, em https://notebook.google.com/

## 2.6 Como receber atualizações

Quando houver novidades no toolkit, basta pedir ao Claude/Codex, numa conversa qualquer:
Atualize o AFT Toolkit
(Ele roda o git pull na pasta das habilidades e mostra o que mudou.)

## 2.7 Plano B — instalação manual

Se algo der errado no Passo 3 (ex.: computador sem o winget, rede corporativa bloqueando), instale manualmente e repita o restante:
Python: baixe em  e, na primeira tela do instalador, marque a caixa “Add Python to PATH”.
Toolkit: abra o Git Bash (menu Iniciar) e rode: git clone https://github.com/ryckardo42/aft-toolkit.git ~/.claude/skills (as habilidades precisam ficar diretamente dentro de ~/.claude/skills, ex.: ~/.claude/skills/aft-setup).

## 2.8 Instalando no Codex (em vez do Claude Code)

O AFT Toolkit não é só do Claude. O Codex — o assistente de código da OpenAI — lê as mesmas habilidades e roda os mesmos scripts. Se você prefere o Codex, a instalação é a mesma dos passos 1 a 4 deste capítulo, com três trocas.
A regra que explica tudo: a pasta das habilidades continua sendo ~/.claude/skills, mesmo que você nunca abra o Claude. Esse caminho está escrito dentro de cada habilidade, e por isso não muda. O Codex enxerga essa mesma pasta por um atalho — um segundo endereço para a mesma pasta, nunca uma segunda cópia. Duas cópias sempre acabam diferentes; um atalho, nunca.
Instale o Codex (developers.openai.com/codex) e entre com a sua conta, no lugar do Passo 1.
Instale o Git exatamente como no Passo 2 — é ele que baixa o toolkit e busca as atualizações futuras.
Cole as mesmas três mensagens do Passo 3, uma de cada vez. As duas primeiras são iguais; só a terceira muda, porque ela cria o atalho junto:
Agora mova todo o conteúdo da pasta Documentos\aft-toolkit, inclusive a pasta oculta .git, para ~/.claude/skills. O resultado tem que ser ~/.claude/skills/aft-setup/SKILL.md — e NÃO ~/.claude/skills/aft-toolkit/aft-setup. Se ~/.claude/skills já tiver alguma coisa dentro, preserve o que existe e apenas acrescente. A pasta precisa ser essa mesmo, ~/.claude, ainda que eu não use o Claude: é o caminho que está escrito dentro das habilidades. Em seguida crie o atalho ~/.agents/skills apontando para ~/.claude/skills (no Windows, mklink /J), que é onde você procura habilidades. No final, liste as habilidades e me diga se preciso reiniciar o aplicativo.
Reinicie e configure, avisando qual assistente você usa:
Rode a habilidade aft-setup. Estou no Codex, não no Claude Code.
A configuração faz tudo o que faria no Claude — cria a pasta Documentos\AFT, pergunta seu nome, CIF e UORG, instala as bibliotecas — e, sabendo que você está no Codex, cria também o atalho do seu perfil e pula sozinha as partes que só existem no aplicativo do Claude. Ao final, peça o /aft-doctor: ele reconhece que você está no Codex, confere os atalhos e não cobra o que não existe lá.
O capítulo seguinte — trazer as suas fiscalizações em andamento para a pasta OS ATIVAS — vale igual, sem nenhuma diferença.

## 2.9 Migrando do Claude Code para o Codex (ou usando os dois)

Se você já tem o toolkit funcionando no Claude e quer passar para o Codex (ou poder usar os dois), não desinstale nada. Migrar aqui é criar dois atalhos. Depois deles, os dois assistentes trabalham sobre os mesmos arquivos: as mesmas habilidades, as mesmas pastas de fiscalização, a mesma ficha memory.md de cada empresa. Nada precisa ser copiado de um lado para o outro, e você escolhe em qual trabalhar a cada dia.
Peça isto ao Claude, numa conversa qualquer:
Quero usar o AFT Toolkit também no Codex. Crie os dois atalhos: ~/.agents/skills apontando para ~/.claude/skills, e ~/.codex/AGENTS.md apontando para ~/.claude/CLAUDE.md. No Windows use “mklink /J” para a pasta e “mklink /H” para o arquivo (nenhum dos dois pede administrador). Se eu já tiver um ~/.codex/AGENTS.md escrito, não sobrescreva: me mostre o que tem lá e junte os dois textos. No final, confirme que os atalhos apontam para o lugar certo.
São dois, e cada um resolve uma coisa:
~/.agents/skills — faz o Codex encontrar as suas habilidades. Sem ele, o Codex não acha habilidade nenhuma.
~/.codex/AGENTS.md — faz o Codex saber quem você é. É o seu perfil de Auditor-Fiscal: que você não é programador, que quem digita comando é o assistente, e qual habilidade usar em cada situação. Sem ele, o Codex acha as habilidades mas trata você como desenvolvedor — e te manda ao terminal.
Por que atalho e não cópia: quando o toolkit se atualiza, ele reescreve o seu perfil por dentro. Com o atalho, o Codex recebe a novidade no mesmo instante; com uma cópia, ficaria para trás sem ninguém perceber.
O que muda no dia a dia: o trabalho de fiscalização é o mesmo — autos, TXT do Sistema Auditor, painel, ementário, relatórios, tudo igual. Quatro comodidades continuam existindo só no Claude:
as sessões separadas por empresa no menu lateral. No Codex você organiza as conversas do seu jeito, e nenhuma habilidade depende disso.
a anotação automática do diário quando você edita a ficha da OS fora de uma habilidade. As habilidades continuam registrando sozinhas e o /aft-diario monta o mês igual.
os ajudantes em conversa isolada. A revisão dos autos e a varredura do Sistema Auditor passam a rodar na própria conversa, com o mesmo resultado.
a lista de bloqueios de privacidade que o toolkit instala (impede ler senhas e os dados reais dos trabalhadores). No Codex quem faz esse papel é o modo de aprovação dele — mantenha a aprovação por comando ligada e não use o modo que aprova tudo sozinho.
Esta é a única perda de proteção real da mudança, e vale conhecê-la.
Outra diferença que você vai notar: no Claude, cada habilidade escolhe sozinha o modelo de que precisa. No Codex o modelo vale para a conversa inteira — então, quando a habilidade pedir o modelo mais forte (analisar PGR, AET, acidente, laudo de NR-12 e manutenção de interdição), ela avisa você em uma linha e espera você trocar com /model.
Voltar atrás é simples: os atalhos não atrapalham o Claude em nada. Se você se arrepender, é só continuar abrindo o Claude como sempre — tudo continua no lugar.

# 3. Usando o Claude Code/GPT Codex como um Sistema operacional de fiscalização

# Indrodução

Do jeito que desenhei o ecossistema, a pasta OS ATIVAS, dentro da pasta AFT que foi criada na instalação, é aquela que vai centralizar todas as pastas de suas auditorias. Então, precisamos que cada auditoria, cada RI, seja o nome de uma pasta com uma empresa. Se você provavelmente também mantém uma pasta para cada RI, fica fácil. Nessa pasta pode ter tudo: OS, NADs, etc...
Nesse primeiro, após jogar a pasta de cada fiscalização lá só peça para o claude organizar sua pasta OS ATIVAS. Ou o comando  /aft-organiza-os 

O claude vai organizar sua pasta OS ATIVAS, num formato “nome da empresa CNPJ”. Se fosse o primeiro banco do brasil, ficaria “BANCO DO BRASIL 00000000000191”.
O memory.md é a ficha da fiscalização: um arquivo de texto (markdown)  simples que fica dentro da pasta de cada empresa, em OS ATIVAS. Ele é criado quando você cria uma nova auditoria,  e vai sendo preenchido pelas demais habilidades ao longo do trabalho. Dentro dele ficam os dados de identificação da auditoria (nome do empregador, CNPJ ou CPF, município, RI, endereço, número de trabalhadores, CNAE e grau de risco), o número da OS e da Demanda do SFIT com o prazo de vencimento, as notificações do DET com seus prazos, as ementas que a OS mandou fiscalizar, as anotações feitas durante a inspeção e a análise documental, os autos de infração redigidos, os que já foram efetivamente transmitidos no Sistema Auditor e um registro do que foi feito, dia a dia. É um arquivo comum, que você pode abrir, ler e corrigir a qualquer momento, e que mora e nunca sai do seu computador.

Ele é o cérebro da fiscalização por um motivo simples: o Claude/Codex nem sempre guarda lembrança de uma conversa para outra. E tudo que vai indo para um chat fica enorme, grande para processar.  Cada vez que você abre uma conversa nova, ele começa do zero, sem saber quem é a empresa, o que você já constatou ou quais autos já foram lavrados. O memory.md resolve isso funcionando como a memória externa da auditoria: o Claude/Codex lê essa ficha antes de trabalhar e grava nela tudo o que apura, de modo que você nunca precisa recontar a história da fiscalização. É também por ele que as habilidades conversam entre si: o /aft-painel mostra os prazos que estão no memory.md, a /aft-auditoria-geral transforma em autos as anotações registradas ali, o /aft-autos-lavrados marca o que já foi transmitido e o /aft-relatorio-rel monta o relatório final a partir do que a ficha acumulou. Na prática, quanto mais fiel estiver o memory.md, mais o assistente acerta; se algum dado estiver errado ali, todo o resto sai errado junto, e por isso vale a pena conferi-lo de vez em quando (ele abre no word).

## 3.1 Painel local –  uso ou não uso?

Se você precisa de um pouco mais de organização ou trabalha em dupla e precisa se concentrar mais em fiscalizações que ficam com você, pode achar o SFITWEB e DET poluídos demais. Por isso criei um painel local com a função de reunir em Cards as informações das auditorias que você está trabalhando na sua pasta OS ATIVAS. Veja só:

Link:
https://chromewebstore.google.com/detail/sync-det-%E2%80%94-aft-toolkit/khmecjbidgcndmgmkbpfncjgmmfehiem?authuser=0&hl=pt-BR

O painel, uma website local que só vive no seu computador, é o retrato da sua carteira de fiscalização, montado somente com o que está  no seu computador. Ele lê os dados de cada empresa na pasta  OS ATIVAS e desenha uma página que abre com dois cliques, sem internet: um card por auditoria, colorido pela urgência do prazo, a lista dos próximos vencimentos em ordem de data e, ao clicar no card, o detalhe completo — notificações do DET, autos lavrados, pendências e o que já foi feito. Junto com ele roda um pequeno servidor, só na sua máquina, que transforma os cards em botões para o trabalho mecânico (marcar notificação como checada, resolver pendência, registrar o dia trabalhado), sempre com backup antes de gravar.

Esse painel pode ser alimentado de dos modos. O primeiro será o próprio claude code abrir o navegador dele e pedir pra você logar. O outro jeito, mais fácil, é você usar a extensão para Chrome/Edge que criei, e  Logado no site do DET, você clica em Sincronizar: o Painel consulta a API oficial e atualiza sozinho tudo do painel que faz referência ao DET.
Sobre aExtensão: desenvolvi uma extensão que funciona no Chrome e Edge que faz captura das informações do nosso DET, logado, e joga essas informações para a memória de cada fiscalização, refletindo nesse painel. Coisas como número da notificação, data de lavratura, ciência, entregas. É instalável em 15 segundos. Juro, 15 segundos.

O que é. A Sync DET é uma extensão gratuita para o navegador (Chrome e Edge) que conversa com o painel do toolkit. Ela resolve uma das tarefas mais repetitivas da fiscalização: copiar, notificação por notificação, o código e o prazo de entrega do DET para a ficha de cada auditoria. Com ela, isso vira um clique: as notificações confirmadas caem direto na ficha (memory.md) da OS certa, e o painel passa a acompanhar os vencimentos sozinho.
Antes de começar, um pré-requisito: o servidor do painel precisa estar ligado na sua máquina. Se você fez a instalação pelo /aft-setup, ele já fica sempre ligado (sobe sozinho quando você entra no Windows). Na dúvida, rode /aft-doctor — ele confere e explica como resolver.
Instalando a extensão (uma vez só):
Abra a página da extensão na loja do Chrome — (link abaixo – copie e cole)	 e clique em Usar no Chrome. No Microsoft Edge o caminho é o mesmo: a loja pede só uma confirmação a mais (“Permitir extensões de outras lojas”) e o botão vira “Instalar”.
https://chromewebstore.google.com/detail/sync-det-%E2%80%94-sisos-aft-tool/khmecjbidgcndmgmkbpfncjgmmfehiem

Usando no dia a dia:
Entre no DET normalmente (auditor-det.sit.trabalho.gov.br), com o seu login gov.br. Só de você navegar logado, a extensão captura sozinha a chave de sessão que o próprio site já usa — pense nela como o crachá que o DET te entrega na entrada. Você não copia, não cola e não digita senha nenhuma na extensão.
Clique no botão flutuante Sincronizar, no final da página, no canto direito da sua tela, que a extensão acrescenta no canto da página do DET. É ele que dispara a mágica.

A extensão entrega informações para o painel local na sua máquina para cada OS de OS ATIVAS/ que tenha CNPJ na ficha e atualiza o memory.md — notificação nova entra como “- [ ] CÓDIGO — prazo dd/mm/aaaa”; prazo que mudou no DET é corrigido na linha existente.
O resultado aparece num aviso na própria página: “✅ Local: 2 importada(s) · 1 prazo(s) atualizado(s)”. Se o DET devolver notificações de outra fiscalização do mesmo empregador (de um colega, ou uma ação antiga), elas não entram — e o aviso conta quantas foram ignoradas, para você saber que existem.
O resultado é ótimo no painel é ótimo. Pra quem trabalha em dupla e quer visualizar só suas infos, é interessante essa funcionalidade.

Através das informações que essa extensão entrega para o painel, vindas do DET e só localmente no seu computador, temos conseguido capturar muitas coisas, coo você vê na imagem acima.

O que a extensão nunca faz. Ela não marca notificação como respondida (o checkbox da ficha é decisão sua, no painel), não altera o que você já escreveu no memory.md (cada arquivo alterado recebe backup antes) e não manda nada para a internet: a conversa entre extensão e painel acontece inteira dentro do seu computador (127.0.0.1 é o endereço da própria máquina). A chave de sessão vive só na memória, expira sozinha em cerca de 30 minutos e não é gravada em arquivo.
Se algo não funcionar:
“Painel não está no ar” — o servidor local não está rodando. Peça ao Claude/Codex: /aft-painel (ou rode /aft-doctor para diagnosticar).
“Token DET não capturado” — a extensão ainda não viu você navegar logado. Abra qualquer página interna do DET (a lista de notificações, por exemplo) e clique em Sincronizar de novo.
Sincronizou mas a notificação não apareceu — confira se a OS tem o CNPJ (ou CPF) no memory.md: sem ele o painel não sabe qual empregador consultar no DET.
O mesmo link:
https://chromewebstore.google.com/detail/sync-det-%E2%80%94-aft-toolkit/khmecjbidgcndmgmkbpfncjgmmfehiem?authuser=0&hl=pt-BR
também instala no navegador Edge

Consegui avança tanto nesse painel e no uso do Claude, que agora esse painel local, quando vc tá devidamente  logado no DET e sincronizado, consegue agora até baixar documentos de uma notificação, extrair os documentos, organizar por item, e salvar automaticamente na pasta da auditorai respectiva. Não é feitiçaria, é tecnologia:

Usar o painel também tem agora outra vantagem: Uma habilidade chamada de  /aft-diario cuida do outro lado: anota  sozinha o dia trabalhado na ficha e no fim do mês e  junta tudo — quantos dias você trabalhou, quais dias úteis ficaram sem registro e as linhas prontas para transcrever no RI. A aba Calendário do painel é o espelho visual desse diário: o mês inteiro num olhar, antes de sentar para preencher.

## 3.1 Habilidades = Habilidades

Durante meu uso no dia-a-dia trabalhando, fui criando várias habilidades (habilidades) para o Claude Code/Codex. Todas as habilidades do pacote aft-toolkit começa com ‘aft-‘, como exemplo a ‘aft-nr01’, que é “perita” em NR nas ementas de NR01. Você não precisa saber o nome de cada habilidade, elas são chamadas naturalmente numa conversa com a IA. No Claude Code/Codex, uma habilidade é precedida do ‘/’, exemplo /aft-inspecao-fisica (para registrar achados da inspeção física).



Imagem: *Exemplo de todas as habilidades que aparecem quando vc digita “/aft-“ na caixa de texto do Claude Code/Codex.*
Durante a instalação do toolkit, O Claude Code/Codex vai criar uma pasta ‘AFT’ dentro da pasta ‘documentos’ da sua máquina. É lá onde a mágica vai acontecer. É importante que você saiba que toda a mágica que o Claude/Codex vai fazer é dentro dessa pasta ‘OS ATIVAS’. Tudo que o Claude Code/Codex vai produzir vai ser colocado ali, portanto é muito importante que você transfira todas as pastas das suas fiscalizações, uma pasta para cada empresa, para dentro dessa pasta OS Ativas.

Após mover as pastas das suas fiscalizações para dentro da pasta OS ATIVAS , peça para o Claude/Codex organizar essa pasta OS ativas, com linguagem natural ou com o comando ‘/aft-organiza-os’ .

Ele vai entender o conteúdo das pastas e vai organizar conforme o tipo de documento. Se for auto de infração, vai para dentro de uma pasta de auto de infração. Se for notificação, para dentro da sua pasta respectiva. Se for documento recebido, idem. E assim por diante. Logo logo você vai entender.

Essa habilidade de organizar as pastas também vai criar um arquivo de memória dessa sua fiscalização (memory.md), que detalha tudo que já foi feito nela.

## 3.2 Sessões no Claude Code e GPT CODEX

No grupo "OS ATIVAS" que você vê na lateral, cada empresa fiscalizada tem a sua própria sessão de conversa com o Claude, criada automaticamente pelo toolkit assim que a auditoria é cadastrada. Pense em cada sessão como uma "aba" separada: ela guarda todo o histórico daquela fiscalização especificamente, e mais importante, o Claude carrega automaticamente o contexto daquela empresa (dados, prazos, achados já anotados, documentos já processados) só quando você está dentro da sessão dela. É por isso que uma sessão de chat funciona como uma pasta de trabalho viva: tudo que você conversa ali fica registrado e disponível para as próximas vezes que você voltar a tratar daquele caso.
Por isso é importante sempre usar a sessão da empresa específica ao trabalhar numa fiscalização: se você pedir para redigir um auto, analisar um PGR ou conferir prazos de DET numa sessão errada (ou numa sessão genérica), o Claude não vai ter o contexto daquela empresa carregado e pode misturar informações de auditorias diferentes, além de você perder o histórico organizado por caso. Trabalhar solto, fora de qualquer sessão de empresa, deve ficar reservado para dúvidas gerais do toolkit ou consultas que não pertencem a nenhuma fiscalização específica — assim que o assunto vira "essa empresa X", o ideal é migrar para a sessão dela (o próprio Claude costuma avisar e oferecer para encaminhar, se perceber que você começou a tratar de uma empresa fora da sessão certa).
Atenção: as sessões por empresa são um recurso do aplicativo do Claude. No Codex elas não existem — lá você organiza as conversas do seu jeito, e nenhuma habilidade depende disso (veja a seção 2.9).

No CODEX é igual. Cada pasta de empresa dentro de OS ATIVAS corresponde a uma auditoria (OS).
Para consumir menos tokens  e evitar misturar dados, o melhor é:
manter um único projeto: OS ATIVAS;
usar um chat/tarefa separado para cada auditoria.
Portanto, faça assim: Crie um projeto e selecione a pasta OS ATIVAS que foi criada:

Nesse mesmo projeto, selecione todas as pastas das empresas que você jogou dentro da pasta ‘OS ATIVAS’

Dê o nome ao projeto de ‘OS ATIVAS’:

E agora você precisa abrir um chat para cada empresa. Exemplo:

Agora que iniciei um chat para uma auditoria, renomeie o chat para o nome que deseja:

Recomendo fixar esse chat. Assim ele não some dessa barra lateral, e você sempre pode voltar para ele para continuar sua auditoria.

## 3.3 Preparação de ação fiscal / Nova OS

A /aft-preparacao-acao-fiscal é a habilidade usada antes da inspeção: ela reúne tudo o que dá para descobrir sem sair do lugar e devolve um roteiro impresso para levar a campo.
Ela lê até três PDFs do SFIT-WEB e sabe o que fazer com cada um. Da Demanda tira a denúncia, os dados do acidente, o histórico e os RIs; o denunciante nunca é nomeado, vira [[DENUNCIANTE_01]], e o contato dele fica só no PDF arquivado. Da Ordem de Serviço tira o número da OS, o vencimento e a tabela de ementas a fiscalizar. Da Relação de Vínculos Ativos tira o efetivo exato, a composição do quadro e quem procurar no estabelecimento. Fora isso, aceita o que você colar: a denúncia em texto, um número aproximado de trabalhadores, os temas prováveis. Se a empresa ainda não tem pasta, ela mesma chama a /aft-nova-auditoria.
Ao todo, aciona seis habilidades e três scripts. As habilidades: /aft-nova-auditoria (cria a OS), /aft-cnae-grau-risco-nr04 (grau de risco, Anexo I), /aft-dimensionamento-sesmt-nr04 (SESMT, Anexo II), /aft-cipa-nr05-dimensionamento (CIPA, Quadro I), /aft-nr24-dimensionamento (banheiros, mictórios, lavatórios e bebedouros devidos, a partir dos homens e mulheres da Relação de Vínculos) e /aft-relatorio-acidentes (histórico de CATs). Se você aprovar, ela encadeia a /aft-NAD e gera a notificação ali mesmo.
Os três scripts rodam na sua máquina, sem gastar tokens e sem nada sair dali: o vinculos_ativos.py lê a Relação de Vínculos inteira (o PDF nunca entra no contexto), o relatorio_acidentes.py processa as CATs e o preparacao_docx.py monta o dossiê, recalculando grau de risco, SESMT, CIPA e NR-24 pelos scripts oficiais. Os números do documento nunca são digitados pelo modelo. A única consulta externa é a busca sobre a empresa na internet, e só com razão social, CNPJ e município: denúncia e nome de pessoa, jamais.
No memory.md ficam os dados duráveis da OS: números da OS e da demanda, vencimento, endereço, telefone, CNAE, grau de risco, efetivo e o quadro de pessoal (homens, mulheres, PCD, aprendizes, menores de 18), a seção ## Ementas da OS com código e descrição literais, o registro de atividade e as pendências

Particularmente, em SST, gosto de fazer inspeção orientada ao histórico de acidentes. Por isso, chego na empresa já com a relação dos últimos acidentes e os dados básicos de cada um. E tem um agente no toolkit que faz justamente isso, e pode fazer já na fase de preparação. A habilidade /aft-relatorio-acidentes monta o histórico de acidentes de trabalho de qualquer empresa que você for fiscalizar: você informa só o CNPJ e ela devolve, em um documento Word salvo na pasta da empresa, todas as CATs registradas contra aquele estabelecimento, em ordem cronológica, com tipo de acidente, lesão, parte do corpo atingida, agente causador e óbitos em destaque. Todo o processamento acontece no seu computador, sem enviar dados de trabalhadores para lugar nenhum. E você quase nunca precisa chamá-la diretamente: a /aft-preparacao-acao-fiscal a aciona sozinha ao montar o dossiê da preparação, para que você chegue ao estabelecimento já sabendo onde, como e com que frequência aquela empresa machuca gente. Isso muda o rumo da inspeção: uma concentração de acidentes com máquinas, por exemplo, indica que a NR-12 merece atenção especial na sua inspeção, e em qual setor (gosto até de entrevistar o acidentado caso sele ainda esteja ativo e pedir a análise desse acidente para a empresa que está sob auditoria. 

Para que isso funcione, uma pasta “CAT” precisará ser alimentada  com as planilhas de acidentes do trabalho da sua UF. Essas planilhas são adquiridas no link do OneDrive institucional, onde estão separadas por Estado:

Pasta no onedrive com CATs separadas por UF

Para funcionar, a habilidade precisa das planilhas de CAT do eSocial do seu Estado, guardadas na pasta CATs, dentro da sua pasta AFT (ao lado de OS ATIVAS). Há dois caminhos para obtê-las:
O automático, recomendado: se você tem cadastro aprovado nos Notebooks-AFT, abra notebooks-aft.vercel.app/aft-toolkit, digite o Gmail do seu cadastro na seção "Planilhas de CAT" e clique em Ativar acesso; depois disso o /aft-setup conecta sua conta Google uma única vez (você só clica em Permitir) e o toolkit baixa (clona)  as planilhas da sua UF e as mantém atualizadas sozinho a cada /aft-atualizar.
Imagem de: https://notebooks-aft.vercel.app/aft-toolkit
O manual, alternativo: entrar na área da ENIT (ou no link que já postei acima)  no SharePoint do MTE (pasta "CATs eSocial por UF", que só abre com a sua conta institucional logada), baixar todas as planilhas da sua UF e copiá-las para a pasta CATs. Nos dois casos a configuração termina aí: o toolkit encontra a pasta sozinho, e sem ela nada quebra, apenas o dossiê da visita sai sem o histórico de acidentes.
Caso você usufruir desse poderoso agente, precisará baixar todas essas planilhas e colocar dentro da pasta “CAT” criada dentro da pasta “AFT” originada na instalação do toolkit. Na minha máquina ficou assim:

Com isso, o agente que faz o relatório de acidentes conseguirá consultar o CNPJ nessas planilhas e vai gerar  um relatório com dados dos acidentes da empresa, que vai pra pasta “Acidentes” da auditada. E o melhor: tudo local feito na sua máquina por scripts, nada vai pra internet.

## 3.4 Inspeção Física

A habilidade (habilidade) /aft-inspecao-fisica existe para resolver o momento mais frágil de toda ação fiscal: o retorno dainspeção presencial. O Auditor-Fiscal volta do estabelecimento com tudo fresco na cabeça e narra, em texto corrido ou por voz ditada, o que encontrou. Basta abrir a sessão da empresa e falar:
"*cheguei da inspeção e vou narrar o que vi".* A habilidade recebe essa narrativa bruta, com toda a pontuação irregular do ditado, e a converte em uma lista de bullet points fiéis, agrupando num único item todos os fatos referentes ao mesmo trabalhador (nome, função, jornada, salário, situação de registro, ASO, data de início) ainda que tenham sido narrados de forma dispersa. Antes de gravar qualquer coisa, ela devolve os bullets na tela e pede a conferência do AFT: "confere se não perdi nem troquei nenhum fato antes de eu salvar". Só depois do aceite o arquivo é gravado. Exemplo:

*. Obs: particularmente gosto de ditar com voz. A IA consegue até pontuar e os erros são mínimos*

O que ela escreve é um único arquivo, inspecao-fisica.md, na raiz da pasta da OS em ~/Documents/AFT/OS ATIVAS/, com um cabeçalho mínimo (empresa e data da inspeção) e o corpo em bullets. Se o arquivo já existir, por exemplo numa segunda visita à mesma empresa, a habilidade pergunta se deve acrescentar ao final, substituir ou cancelar; ela nunca sobrescreve sem autorização. O relato permanece integralmente local, com os nomes reais, porque ele é fonte de prova do Auditor. É importante entender o que a habilidade deliberadamente NÃO faz: ela é puramente descritiva. Não cita Norma Regulamentadora, não indica ementa, não sugere capitulação, não emite juízo de infração. Essa inteligência jurídica pertence às habilidades seguintes, e a separação é proposital: primeiro se fixam os fatos, depois se discute o enquadramento. Eis um exemplo:

No exemplo acima, cheguei de uma inspeção em uma indústria frigorífica, e narrei do meu jeito, a minha parte  inspeção em grupo.  Nem foi no chat, foi numa nota mesmo do celular. Depois só copiei na sessão/chat da fiscalização. O print acima foi o resultado transformado pelo Claude.
É a partir dessa “inspeção física” que o Claude/Codex pode levantar todas as ementas e me sugerir autos. Claro que eu posso orientar ainda mais essa parte da auditoria: quanto mais informação der, melhor será. Mas será desse contexto acima que será usado para o texto dos autos de infração, como a data da inspeção física, quem acompanhou e etc.
Muitas irregularidades já são constatadas nessa primeira inspeção física e elas podem desde já virar autos de infração. Se eu flagro falta de CIPA, máquina sem proteção e trabalhador sem capacitação, dentre outros, não preciso esperar retorno de notificação entregue. Eu já faço (peço para a IA fazer) esses autos de infração logo após narrar a inspeção física. Mesmo que não os lavre no sistema, eles já ficam redigidos e prontos.  Para que a IA consiga associar irregularidades com ementas e redigir os autos, precisamos falar da habilidade seguinte, ‘auditoria-geral’.

## 3.5 A habilidade  ‘/auditoria-geral’

Lembre-se que você  não precisa “decorar” o nome das habilidades. O sistema entende o que você quer e chama. Se a /aft-inspecao-fisica é a que descreve, a /aft-auditoria-geral é a que enquadra. Ela é o coração jurídico do toolkit: pega os fatos já registrados e, ao final, os transforma em autos de infração prontos, com ementa, capitulação e texto no modelo oficial. Aciona-se com /aft-auditoria-geral ou com frases naturais como "faça a auditoria", "emente as irregularidades", "lavrar auto", "enquadrar as constatações". Ela trabalha a partir de duas fontes de achados, que podem coexistir: o arquivo inspecao-fisica.md, com o relato de campo, e a seção "Auditoria de documentos" do memory.md (nas OS mais antigas ela se chama "Anotações da auditoria" — a skill lê as duas), onde ficam as constatações lançadas durante a análise documental (SESMT subdimensionado, ASO faltando, programa vencido). Se nenhuma das duas existir, ela aceita a narrativa colada na hora, ou sugere rodar antes a /aft-inspecao-fisica.

A /aft-auditoria-geral é a skill que transforma fato em auto de infração. Ela pega o que o Auditor constatou — na visita ao estabelecimento, na análise dos documentos, ou nos dois — e devolve os autos redigidos, prontos para revisão. É o passo do meio do fluxo: alguém já descreveu os fatos antes, e alguém vai empacotar o arquivo depois. O trabalho acontece em seis fases encadeadas (0 a 5), e o Auditor confirma cada uma antes que a seguinte comece. Nada avança no silêncio.
Fase 0 — o que a pasta já sabe. A skill abre a pasta da OS e lê o memory.md para recuperar razão social, CNPJ, município e o que mais estiver anotado. É por isso que ela não repergunta o que você já cadastrou na /aft-nova-auditoria. Aqui também se resolve a dupla visita, e a regra é de silêncio: a skill nunca pergunta sobre ela. Quando você pede os autos, ela assume que não há dupla visita e autua.

Fase 1 — de onde vêm os achados. A skill busca em duas fontes, que podem coexistir: o arquivo inspecao-fisica.md (o relato de campo produzido pela /aft-inspecao-fisica) e a seção "## Auditoria de documentos" do memory.md (as constatações que você foi lançando durante a análise dos documentos: SESMT subdimensionado, ASO faltando, PGR inexistente; nas OS mais antigas a seção se chama "## Anotações da auditoria", e a skill lê as duas). Se não houver nenhuma das duas, ela pede que você cole os achados.
O interessante é,  que se a habilidade ler menção de  trabalhador sem registro, aciona uma habilidade específica, a  /aft-informalidade para os autos do     art. 41 (registro) e do art. 29 (CTPS), que correm em paralelo.

Em seguida ela apresenta a lista numerada das irregularidades e pergunta se confere — nem todo bullet do relato vira auto: contexto da visita (quem acompanhou, que setor foi inspecionado) é aproveitado como cenário, não como infração. É também aqui que ela completa o que falta sobre o estabelecimento: número de trabalhadores e CNAE, se não estiverem no memory.md nem nos documentos da OS, perguntados de uma vez só. O grau de risco ela nunca pergunta: deriva do CNAE pelo Quadro I da NR-04.

Fase 2 — achar a ementa certa. A busca é em camadas, da mais barata para a mais cara. Primeiro a lista curada de ementas frequentes que acompanha a própria skill (o arquivo ementas-frequentes.md, com uma coluna "Quando usar" que casa situação com código); depois o NotebookLM (agora google notebooks do ementário da NR aplicável; depois o ementário compartilhado no Google Drive; e, em último caso, uma pergunta direta a você. O resultado vem sempre em tabela — irregularidade, NR, item violado, código da ementa, descrição e gradação — para confirmação. E vale a regra dura de toda a caixa de ferramentas: nunca se inventa código de ementa nem item de norma. Se não achou, ela diz que não achou.

Fase 3 — a redação. Cada ementa aprovada vira um auto separado, conforme veremos logo mais.
Fase 4 — a ficha da empresa. A habilidade  atualiza o memory.md com edição cirúrgica, linha a linha, sem sobrescrever nada do que já estava lá: acrescenta uma linha por auto em "Autos lavrados", marcada como pendente de empacotamento; registra a data e o resumo em "Inspeção física"; No exemplo abaixo, o registro na memória de uma ME/EPP que teve várias interdições, e cujos autos já estão com texto prontos esperando para serem devidamente empacotados para o  módulo auto de infração do Sistema Auditor:

Fase 5 — o que vem depois. A skill fecha com um resumo do que foi feito e aponta o próximo passo: /aft-gera-ai para empacotar os autos, lavratura da TN quando houver lista de notificação, /aft-embargo-interdicao se o risco grave só ficou evidente durante a redação. Ela também registra sozinha o dia trabalhado no diário de atividades da OS, com as letras D (análise de documentos) e E (elaboração de documentos), sem perguntar nada, como veremos no futuro.

## 3.6 Habilidade de gerar Autos de Infração

É tudo integrado. Tudo funciona em harmonia. Imagine que você tem quatro assessores numa sala, cada um com uma única tarefa.

O Escrivão (/aft-auditoria-geral) ouve o que você viu na empresa e escreve a minuta do auto. Pronta a minuta, ela vai para o Revisor (/aft-revisa-auto), que é um sub agente que trabalha numa sala fechada e nunca ouviu a conversa: ele só lê o papel, com olhos de quem vai contestar aquilo no julgamento. Confere se está lá o quem, o quê, quando, onde e como, arruma os parágrafos e os acentos, mas não muda a sua tese nem inventa nada. Depois entra o Empacotador (/aft-gera-ai), que não escreve uma linha do auto: ele só põe o texto dentro do envelope certo, com o carimbo da sua unidade e os anexos, no formato que o Sistema Auditor aceita. Aí ele te entrega o envelope, porque quem leva ao correio é sempre você: nenhum assessor transmite auto.
Por fim, quando você volta de lá, o Conferente (/aft-autos-lavrados) abre a lista do que foi entregue e compara com a lista do que tinha sido preparado, item por item. Ele diz: este foi lavrado, este ficou na gaveta, este chegou sem rascunho. Se o mesmo auto foi refeito, ele fica com o mais novo. E se você trocou a ementa na hora da lavratura, mantendo o mesmo fato, ele percebe que é o mesmo assunto com outra etiqueta e junta as duas linhas numa só, sem te perguntar, porque você já decidiu isso quando lavrou. Só isso ele resolve sozinho; qualquer outra dúvida ele anota num bilhete e traz para você decidir***. Obs: Um script(programinha)vai lá na pasta do sistema auditor e checa os autos lavrados. Tudo localmente. Nada sai para fora.***
Exemplo:

No exemplo acima, joguei o mensagem/instrução no chat/contexto da empresa que estou trabalhando.

Em cada um desses chats (sessões) é que você deve trabalhar em cada empresa. Olha só o resultado:

O Claude Code foi lá no notebookLM da NR-36, pegou ementa, capitulação, voltou, lembrou do histórico da fiscalização e redigiu o AI. Dei ok, forneci a uma foto e pedi para usar como anexo do AI. Agora trataremos do próximo ponto: como o Claude Code/Codex faz os autos de infração.

Continuando do exemplo 1 lá atrás,  o Claude foi lá na NR36, pegou ementa, voltou, lembrou do histórico e me perguntou se eu queria rodar os agentes que geram o AI. Minha reposta:

O auto de infração, um TXT importável pelo sistema auditor, foi gerado e enviado para a pasta da fiscalizada, dentro da subpasta “autos”, com pasta com o nome do dia da geração, e com o anexo (.PDF).
Se você estiver familiarizado com o sistema Khronos, aqui é a mesma coisa: você vai conseguir importar os autos apenas apontando o TXT gerado. No sistema auditor, é só ir em “Imp.txt”

Apontar o local do auto (TXT), que o sistema auditor vai importar tudo, inclusive o anexo, a foto que eu forneci para o chat, já como PDF.

## 3.7 Habilidades específicas e gerais

Dentro do toolkit existem, além das habilidades de fluxo, algumas habilidades que funcionam como especialistas de uma norma específica: a /aft-NR01 (disposições gerais, gerenciamento de riscos ocupacionais e PGR), a /aft-NR12 (máquinas e equipamentos) e a /aft-NR18 (construção civil). Elas são as consultoras das Normas mais presentes na fiscalização, e a diferença está na fonte: cada uma carrega, dentro da própria pasta, o texto da norma e um catálogo curado das ementas mais lavradas naquela NR, com a descrição oficial, a capitulação e os gatilhos que ligam a situação de campo ao código correto. Por isso a consulta é imediata e não depende de conexão. Elas podem ser chamadas diretamente pelo Auditor (/aft-NR12, por exemplo, quando a narrativa fala de proteção fixa, intertravamento ou zona de perigo) ou serem acionadas de dentro da /aft-auditoria-geral e da /aft-embargo-interdicao, quando a norma identificada for justamente a especialidade delas. OBS: Mais uma vez, não precisa saber o nome das habilidades. O sistema chama automático pelo contexto, conversa, ou você falando “analise conforme a NR-12, etc”. O que devolvem é material já formatado para as três pontas do trabalho: o código da ementa, o bloco II do auto de infração, a linha da Seção 4 do Relatório Técnico e o fragmento de fundamentação do Termo de Interdição.

Nessas três habilidades, o NotebookLM é a segunda fonte, não a primeira: só se recorre a ele quando a situação constatada não casa com nenhuma ementa do catálogo interno, o que acontece nos casos menos comuns. Para todo o resto do toolkit a lógica se inverte, e o NotebookLM é a fonte principal de consulta e busca. É nele que estão os ementários completos de SST e de legislação trabalhista, e é a ele que recorrem a /aft-consulta, a /aft-auditoria-geral (para as NRs sem habilidade especialista) e as demais habilidades que precisam localizar código de ementa, capitulação ou gradação. Vale sempre a mesma regra de segurança, em qualquer das duas situações: nada de ementa, item de norma ou capitulação inventados. Se a informação não estiver no catálogo interno nem no NotebookLM, a habilidade diz que não encontrou e devolve a pergunta ao Auditor, em vez de arriscar um palpite.
Exemplo: você recebeu o PGR da empresa que quer fazer auditoria. Basta você falar na sessão da empresa “Faça auditoria do PGR da empresa” O próprio Claude Code/Codex vai achar onde está o PGR (se dentro da pasta da fiscalizada), o PDF do programa. Vai fazer a análise conforme o seu contexto, aquilo que você relatou, o que você viu de irregularidade na empresa, e vai te trazer as prováveis infrações em relação a este programa. Você confirmando, o Claude Code vai gerar os autos de infração.

Ele analisa o PGR conforme várias ementas, cruzando o documento com o contexto fornecido: relatos da inspeção física e autos de infração lavrados por irregularidades.

Conferido tudo (ele cita até as páginas dos achados), é só mandar gerar os autos. O Claude/Codex entende que o PGR é anexo para todos e, caso o PDF passar de 10MB, compacta automaticamente. Agora é só mandar gerar os autos, e importar pelo sistema auditor, como no exemplo 1.

## 3.8 Habilidade com  Embargo e Interdição

Nesse tema, é muito importante que você compreenda que o módulo de embargo/ interdição é feito com a intenção básica de registrar o ato, mas também com a intenção de servir como uma ferramenta para gerar o relatório técnico nos termos da Instrução Normativa correlata. Mas ele não é uma amarra para o auditor.  Por isso há a possibilidade do AFT anexar em PDF o seu próprio relatório técnico:

Isso acontece porque há muito mais liberdade para o AFT redigir e montar  um relatório técnico em um  processador de texto como o MS Word: Anexar fotos,  formatar do jeito preferido, cabeçalhos, etc... O  relatório técnico é o coração do termo, certo? Você consegueo número do termo antes, conforme foto abaixo, assim você pode fazer redigir seu Relatório à vontade no Word, à mão, do jeito que quiser!

Essa habilidade /aft-embargo-interdicao produz o Relatório Técnico que fundamenta a interdição ou o embargo, a medida cautelar do art. 161 da CLT e da NR-03, com todos requisitos da portaria correlata. Você aciona digitando /aft-embargo-interdicao ou pedindo em português mesmo: "relatório técnico de interdição", "montar o RT". A /aft-auditoria-geral pode chamar sozinha quando o relato de campo traz sinais de risco grave, como as palavras interditar, embargo ou GIR. Em uma fiscalização em usina, fiz o teste real: abri o notebook, o claude, na sala de reuniões da empresa, e fiz todo Termo de Interdição e relatório técnico de 6 máquinas em recorde 25 minutos, com PDF gerado, assinado e enviado ao e-mail da empresa na hora, que viu, tomou ciência, e me devolveu o mesmo PDF assinado digitalmente.
Nos campos do módulo embargo e interdição do sistema Auditor, eu só registro fielmente os objetos. Para o resto, faço sempre menção ao relatório Técnico, que é o que de fato a empresa recebe e o que é protocolado no SEI, repetindo o mesmo texto em todos os campos possíveis (fatores de risco, medidas, documentos, etc...). Em irregularidades lanço algumas ementas também.

Nessa habilidade, antes de escrever qualquer coisa, ela decide entre interdição ou embargo. A NR-03 separa as duas medidas pelo objeto atingido, não pela gravidade: obra é sempre embargo (subitem 3.2.2.1); máquina, equipamento, setor de serviço ou atividade é interdição (subitem 3.2.2.2). Feita a escolha, a habilidade adapta o documento inteiro, porque um embargo de obra não pode sair chamado de interdição. Ela também delimita a paralisação ao menor escopo capaz de afastar o risco, como manda o subitem 3.2.2.3.1: só os pavimentos com problema, só as máquinas irregulares, e não a obra ou a fábrica toda.
Depois disso, ela trabalha em três modos. No modo A cria o relatório do zero. O modelo oficial em .docx já vem no toolkit com os campos marcados, e a habilidade preenche apenas as partes variáveis: número do termo, empregador, CNPJ, objetos interditados, irregularidades com suas ementas e capitulações, fatores de risco, medidas de proteção e documentos solicitados. Nada do conteúdo fixo é tocado, nem cabeçalho, nem logotipos, nem citações legais, nem tabelas da NR-03, nem as instruções de peticionamento no SEI. A data da inspeção física entra no item 2, junto com quem acompanhou a visita e o que foi examinado. Exemplo de relato, simples, de teste que eu fiz:

O resultado foi um relatório técnico de interdição completo, em docx, pronto para ser revisado, gerado o PDF e anexado no módulo embargo/interdição. Aqui um trecho (100% pela IA):

Caso você ache o texto padrão desse modelo muito verborrágico, você pode editar o modelo com alguns textos que você ache mais apropriado. Só peça para o claude/codex te mostrar onde está o “template” da habilidade ‘embargo/inderdição’. Ele vai te mostrar o caminho, e você pode editar o .DOCX à vontade. No próximo uso a habilidade vai gerar mais próximo do texto que você gosta.

No modo B você anexa um relatório ou um Termo de Interdição já pronto e pede só os autos. A habilidade não refaz o documento: lê dele as ementas e os objetos interditados e vai direto para a lavratura.

O modo C é para a dúvida. Você descreve o que encontrou e pergunta se cabe interditar. A habilidade consulta uma base de 113 relatórios técnicos reais e mostra os casos parecidos: o número do termo, as ementas que foram usadas e como o fator de risco foi redigido naquela ocasião. Ela sugere e fundamenta. Quem decide é você.

Para achar a ementa certa, a habilidade olha primeiro os catálogos das habilidades /aft-NR12 e /aft-NR18, que trazem os gatilhos ligando a sua narrativa ao código correto. O que não estiver lá, ela busca no NotebookLM, no ementário e no caderno da norma específica. Fotos da inspeção também podem entrar no corpo do relatório, logo abaixo da irregularidade que ilustram, já no tamanho da página e com legenda. A única exigência é que a foto esteja salva como arquivo, porque imagem colada no chat não serve.

Em qualquer modo, os autos de infração derivados são obrigatórios e a habilidade não pergunta se você quer. É um auto por ementa da seção 4, com o texto já trazendo a caracterização do risco grave e iminente pelo subitem 3.2.1 da NR-03 e o parágrafo de dano coletivo.
Tudo é salvo na pasta interdicao-embargo/ da OS: o relatório em .docx e o arquivo autos.md, que é entrada direta do /aft-gera-ai. Antes de gravar, a habilidade confere se o arquivo está aberto no Word e faz backup do anterior. Depois, roda um verificador que compara o relatório com os autos, para garantir que as ementas de um batem com as do outro.

Relatório Técnico de Levantamento Total de Interdição/Embargo em Word (.docx): o contrário da habilidade anterior. Quando a empresa pede a suspensão no processo SEI e você decide LEVANTAR a medida, esta habilidade redige o relatório que registra o cumprimento das exigências e o afastamento do risco grave e iminente. É um documento curto de propósito, em sete itens: ela pergunta a data do requerimento, o número do processo SEI e se você voltou ao estabelecimento (guardando a data da inspeção física) ou decidiu só pela análise dos documentos, copia do termo original o objeto que estava interditado e conclui pelo levantamento total. Se você quiser destacar alguma coisa, ela põe o registro na análise (item 2) ou na conclusão (item 7). Só redige depois que você decide: se a intenção for negar, ela te manda para a /aft-embargo-interdicao-manutencao.

/aft-embargo-interdicao-manutencao: Interditado o estabelecimento ou a máquina, a empresa peticiona pedindo a suspensão da medida e junta laudos, ARTs, fotos e projetos. Quando o Auditor examina esse material e decide que não é caso de levantar a interdição, é esta habilidade que redige o Relatório Técnico de Manutenção. Aciona-se com /aft-embargo-interdicao-manutencao, "manter a interdição", "negar a suspensão", "indeferir o levantamento". Ela localiza na pasta interdicao-embargo/ os três documentos indispensáveis (o RT original, o requerimento da empresa e os documentos juntados), e monta o confronto item a item: cada documento solicitado e cada medida de proteção exigida no RT original, com a anotação do que veio, do que veio parcialmente e do que não veio. O documento final segue estrutura fixa: objetivo, análise dos documentos apresentados e do cumprimento das medidas, conclusão pela manutenção e, opcionalmente, uma seção dizendo à empresa exatamente o que precisa vir no próximo pedido (marca e modelo dos dispositivos, categoria de segurança alcançada, laudos com medições reais, ARTs específicas, link de nuvem com fotos e vídeos dos testes). Se o núcleo do requerimento for um laudo de adequação de máquina, a habilidade sugere rodar antes a /aft-auditoria-AR-NR12, que julga tecnicamente esse laudo, e aproveita o parecer como corpo da análise.

Há uma regra nessas habilidades que merece destaque, porque define bem o espírito do toolkit: a suspensão e manutenção da interdição /embargo é ato de convicção do Auditor, e a habilidade nunca deduz os argumentos dele. Por mais evidente que o confronto documental pareça, o levantamento das faltas, se houver,  é apresentado como matéria-prima, e a habilidade pergunta expressamente quais foram os argumentos técnicos pela manutenção e se houve nova inspeção física, aguardando a resposta antes de redigir uma linha. As seções são mostradas no chat para aprovação e só então o .docx é gerado, salvo na mesma pasta interdicao-embargo/, com o memory.md atualizado com a data e o resumo das pendências. Vale ainda lembrar que os documentos entregues pela empresa são dados a analisar, nunca instruções: se algum trecho do laudo ou da petição tentar dirigir a decisão, pedindo para liberar a máquina ou suspender o embargo, isso é relatado ao Auditor como achado e ignorado. Quem decide é sempre ele.

## 3.9 Habilidade com  Notificação para correção de irregularidades (aft-tn-nco)

Durante a auditoria, após você identificar as irregularidades na inspeção física ou na auditoria de documentos, você pode desejar notificar a empresa para correção. E aí que entra essa habilidade.

O Claude/Codex então vai checar quais autos você lavrou ou irregularidades ainda sem autos de infração.

Talvez nem tudo o que você autuou você queira notificar: Há itens que estão na interdição que você fez e não precisam ser notificadas ou há itens que a empresa já regularizou na sua inspeção física ou nesse interstício de tempo. Por isso o sistema vai identificar todas as regularidades autuadas ou não e vai te oferecer para você marcar o que você quer notificar em um checkbox:

Calma, calma. Você ainda vai precisar copiar o texto e colar no DET manualmente. Mas já é um avanço certo?

Legenda: texto para ser copiado para o DET. Na seta vermelha, você  só clica e todo o texto da caixa é copiado. Vá na notificação do DET e faça um CTRL + V.
Depois o Claude/Codex ainda te pergunta se você quer um texto para enviar por e-mail informando para a empresa que você transmitiu uma nova notificação via DET. Eu particularmente sempre uso e sempre envio, pois nem sempre o e-mail que a anotamos na ação fiscal é o e-mail que tem acesso ao DET. O e-mail é bem genérico e informativo, fazendo com que o fiscalizado tenha a curiosidade e a necessidade de ter a ciência no DET o mais rápido possível.

*Claude/Codex chamando o “estagiário” que faz e-mail.*

# 4. Catálogo das habilidades (nem todas)

Difícil listar todas as habilidades do Claude/Codex criadas por mim, pois novas habilidades são adicionadas no decorrer das minhas auditorias, e colegas estão começando a contribuir também.

## 4.1 Configuração e visão geral (apenas algumas. Todo dia entram novas habilidades)

| Habilidade | O que faz |
|---|---|
| /aft-setup | Configuração inicial: cria as pastas de trabalho, registra seus dados (nome, CIF, lotação) e instala as dependências. Roda uma única vez. |
| /aft-doctor | Check-up da instalação: confere se Python, Git, as habilidades, a configuração, o seu perfil, a pasta de trabalho e as bibliotecas estão no lugar — e diz, em linguagem simples, o que falta e como resolver. Rode logo após o /aft-setup e sempre que algo não funcionar. Só diagnostica; não altera nada. |
| /aft-atualizar | Atualiza as habilidades (git pull no repositório do toolkit) e o comando notebooklm (notebooklm-py), se houver versão nova, e roda o /aft-doctor ao final para confirmar que nada quebrou. Diferente do /aft-doctor (só diagnostica), esta habilidade é a que baixa e instala as atualizações de fato. |
| /aft-nova-auditoria | Cadastra uma auditoria: empregador, CNPJ, município e, se já houver, a notificação do DET com o prazo. É o começo do fluxo — cria a pasta da empresa e a ficha dela. |
| /aft-painel | Gera um painel (página que abre no navegador) com todas as suas auditorias em andamento e os prazos de DET coloridos por urgência (vencido, vencendo, no prazo). É um “SISOS local”: roda no seu computador, sem internet nem servidor. Só mostra; quem cadastra é o /aft-nova-auditoria. |
| /notebooklm | Acesso completo à API do NotebookLM: criar notebooks, adicionar fontes (PDF, URL, YouTube, áudio), gerar resumos/podcasts/relatórios e baixar os artefatos — recursos que nem a interface web do NotebookLM oferece. É diferente do que as habilidades de lavratura já fazem por trás dos panos (apenas consulta de ementa, autenticada pela /notebooklm-login): use o /notebooklm quando você mesmo quiser criar ou organizar notebooks e fontes, não para autuar. Habilidade do projeto teng-lin/notebooklm-py, fora do aft-toolkit — depois de instalar o pacote (seção 2.3), é preciso rodar notebooklm skill install (uma única vez) para ela aparecer. |

## 4.2 Inspeção e lavratura

| Habilidade | O que faz |
|---|---|
| /aft-inspecao-fisica | Transforma a narrativa ditada da visita (por voz ou texto corrido) num relato de campo estruturado e fiel, salvo na pasta da OS. Puramente descritivo: sem NR, sem ementa. É a memória de campo que alimenta as outras habilidades. |
| /aft-consulta | Consulta os ementarios/notebooks para tirar uma duvida tecnico-juridica ou enquadrar um fato: identifica a ementa (codigo e descricao), apresenta a capitulacao e a gradacao (e notas tecnicas), e ainda sugere o texto do campo Historico do auto, com metodologia que evita nulidades. So consulta - nao lavra (isso e com /aft-inspecao-inicial e /aft-gera-ai). |
| /aft-inspecao-inicial | Lê o relato de campo, identifica a NR e a ementa de cada irregularidade (consultando o NotebookLM), e redige os autos de infração no modelo de 3 subtítulos. Cobre todas as NRs e a CLT. Aplica automaticamente o critério de dupla visita (ME/EPP) e desvia para /aft-registro e /aft-embargo-interdicao quando detecta os gatilhos. |
| /aft-registro | Trabalhador sem registro: gera os dois autos (art. 41 e art. 29 da CLT), com a fundamentação completa do vínculo empregatício (pessoalidade, não eventualidade, onerosidade, subordinação) e a verificação no eSocial. |
| /aft-PGR-analise | Auditoria sistemática do PGR à luz da NR-01: varre as 7 ementas de PGR, confronta o documento com o que você viu em campo, cita os trechos e as páginas que sustentam cada conclusão e redige os autos das ementas presentes. |
| /aft-det-630 | Empregador não entregou (ou entregou só parte) dos documentos notificados via DET: redige o auto da ementa 001168-1 (art. 630, §4º da CLT), com o Relatório de Atendimento do DET como anexo. |
| /aft-tn-nco | Redige a Notificação para Correção de Irregularidades — o texto que você cola no DET para a empresa sanar as irregularidades (introdução fixa + um item por irregularidade + observações), pronto bloco a bloco. Não é o auto de infração; é a notificação para corrigir. |
| /aft-embargo-interdicao | Risco grave e iminente: gera o Relatório Técnico de Interdição/Embargo em Word (.docx) a partir do modelo oficial e, em seguida, redige os autos derivados das ementas do RT. |
| /aft-auditoria-AR-NR12 | Julga o laudo de adequação à NR-12 ou a apreciação de riscos que a empresa apresentou — seja num pedido de suspensão de interdição, seja em resposta a uma notificação. Confere o método de estimativa de risco, a categoria de segurança (S/F/P → B, 1, 2, 3, 4 da NBR 14153), a interface de segurança (relé ou CLP), os requisitos da NR-12 que dependem da apreciação e a habilitação de quem assinou, e entrega um parecer: apto, apto com ressalvas ou insuficiente. Salva um arquivo numerado (auditoria-1-AR-NR12.md, auditoria-2-AR-NR12.md…) na pasta da OS. Exemplos do que dizer: “analisa esse laudo de conformidade NR-12 que a empresa juntou no pedido de suspensão”; “a metalúrgica respondeu minha notificação com uma apreciação de riscos feita com HRN, dá teu julgamento técnico”; “esse laudo sustenta o levantamento da interdição?”; “o laudo fala em categoria 2 mas não vi relé de segurança em lugar nenhum, dá uma auditada”; “auditar a apreciação de riscos que veio na resposta do DET”; “a empresa mandou fotos e um documento de 3 páginas feito por TST, confere se sustenta o levantamento”. |
| /aft-embargo-interdicao-manutencao | Relatório Técnico de Manutenção de Interdição/Embargo em Word (.docx): quando a empresa pede a suspensão (levantamento) e você decide MANTER a medida, esta habilidade confronta o que foi exigido no relatório original com o que a empresa apresentou, incorpora os seus argumentos e o resultado da nova inspeção (se houve) e conclui pela manutenção. Nunca inventa os seus argumentos: pergunta a você. Exemplos do que dizer: “vou manter o embargo da obra, redige o relatório técnico da manutenção”; “a empresa pediu suspensão da interdição mas não vou levantar, faz o RT negando”; “mantém a interdição das serras do frigorífico e monta o termo de manutenção”; “fiz nova inspeção e as proteções continuam faltando, mantém o embargo”; “relatório técnico de manutenção ref. ao termo 4.145.884-2, com os requisitos para novo requerimento”; “o pedido de suspensão veio sem o laudo que eu exigi, vou indeferir”. |
| /aft-embargo-interdicao-levantamento | Relatório Técnico de Levantamento Total de Interdição/Embargo em Word (.docx): o contrário da habilidade anterior. Quando a empresa pede a suspensão no processo SEI e você decide LEVANTAR a medida, esta habilidade redige o relatório que registra o cumprimento das exigências e o afastamento do risco grave e iminente. É um documento curto de propósito, em sete itens: ela pergunta a data do requerimento, o número do processo SEI e se você voltou ao estabelecimento (guardando a data da inspeção física) ou decidiu só pela análise dos documentos, copia do termo original o objeto que estava interditado e conclui pelo levantamento total. Se você quiser destacar alguma coisa, ela põe o registro na análise (item 2) ou na conclusão (item 7). Só redige depois que você decide: se a intenção for negar, ela te manda para a /aft-embargo-interdicao-manutencao. Exemplos do que dizer: “a empresa cumpriu tudo, redige o levantamento da interdição”; “vou liberar as máquinas do frigorífico, faz o RT de levantamento”; “levanta o embargo da obra, processo SEI 10162.204455/2026-41”; “voltei lá hoje e as proteções estão instaladas, monta o relatório de levantamento”. |
| /aft-analise-acidente | Analise de acidente do trabalho: analise o contexto e gera texto para Relatorio de Analise na estrutura da IN GMTP/MTP n. 2/2022, propoe os fatores causais com os codigos oficiais do SFIT para confirmacao do AFT e entrega o relatorio em Word. Ao final, pergunta se deve encadear a lavratura de autos (/aft-inspecao-inicial + /aft-gera-ai). |

## 4.3 Consultoras especializadas por NR

Quando a irregularidade é de máquinas ou de obra, estas consultoras conhecem as ementas mais lavradas e entregam o texto pronto para a /aft-inspecao-inicial e o /aft-embargo-interdicao. A /aft-inspecao-inicial as aciona sozinha quando identifica a NR; você também pode chamá-las direto.

| Habilidade | O que faz |
|---|---|
| /aft-NR12 | Máquinas e equipamentos: a partir da sua descrição (ex.: “injetora sem proteção e sem parada de emergência”), identifica a ementa (catálogo das 16 mais comuns + NotebookLM) e entrega o bloco da irregularidade, a linha do Relatório Técnico e o fragmento para o Termo de Interdição. |
| /aft-NR18 | Indústria da construção: separa as várias ementas de uma inspeção de obra (catálogo das 29 mais comuns + NotebookLM) — periferia sem guarda-corpo, elevador sem cancela, andaime, instalações elétricas, área de vivência — e entrega o bloco da irregularidade e a linha do RT de cada uma. |

## 4.4 Jornada e ponto eletrônico (Portaria MTP 671/2021) – Rodam localmente em scripts

| Habilidade | O que faz |
|---|---|
| /aft-jornada-analise | Recebeu o pacote de ponto da empresa (AFD, AEJ, atestados)? Esta habilidade tria os arquivos, aciona os especialistas e consolida tudo num único relatório. |
| /aft-jornada-valida-afd-aej | Valida tecnicamente o arquivo AEJ com um script Python local: estrutura, formatos, trailer e integridade referencial. Detecta arquivo editado ou montado à mão. |
| /aft-jornada-atestado | Confere o Atestado Técnico e Termo de Responsabilidade do REP/PTRP item a item contra o art. 89, inclusive a estrutura da assinatura digital do PDF (padrão PAdES). |
| /aft-jornada-auto-afd-aej | Redige os autos por AFD/AEJ ausente ou fora do padrão (ementas 002279-9 e 002280-2), descrevendo o defeito tecnicamente constatado. |

## 4.5 Empacotamento, rastreamento e relatórios

| Habilidade | O que faz |
|---|---|
| /aft-gera-ai | O empacotador: pega os autos já redigidos (por qualquer habilidade ou colados por você), coleta os dados administrativos, converte fotos de evidência em PDF e gera o arquivo TXT no formato e encoding exatos do Sistema Auditor. É aqui que a anonimização é aplicada e revertida com segurança. Roda localmente |
| /aft-revisa-auto | Revisor de qualidade que roda automaticamente dentro do /aft-gera-ai, antes do empacotamento: confere o checklist 5W1H (O Quê, Quando, Onde, Como, Por Quê) em cada auto e, em autos de SST, garante o parágrafo de dano coletivo (Portaria MTP 667/2021). Também pode ser chamado isoladamente sobre um rascunho de auto. |
| /aft-autos-lavrados | Depois de transmitir, lê os PDFs dos autos já lavrados na pasta do Sistema Auditor (C:\SistemasAFT\...\PRO), cruza com os rascunhos e marca na ficha da empresa o que foi transmitido e o que ainda está pendente. Só lê o Sistema Auditor, nunca altera nada nele. |
| /aft-relatorio | Consolida autos, termos e notificações num Relatório Final Simplificado, limpo e objetivo, para leitura por outros Auditores. |

4.6Scripts que vão rodar locamente na sua máquina: Scripts locais (Python)– Alguns deles.
Em várias habilidades você vai ver nomes de arquivo esquisitos, como gerar_painel.py ou rehydrate.py. Esses arquivos são chamados de scripts. Um script é um programinha bem pequeno, feito para fazer uma única tarefa mecânica, sempre do mesmo jeito.
Pense numa calculadora, ou num carimbo. A calculadora não tem opinião sobre a conta: você digita 2 + 2 e ela responde 4, hoje, amanhã e daqui a dez anos. O carimbo não decide onde quer bater: ele deixa a mesma marca todas as vezes. O script é assim. Ele não pensa, não interpreta, não muda de ideia e não erra de distração.
Essa é justamente a diferença para a inteligência artificial. A IA lê, entende, compara e escreve — e por isso ela é ótima para redigir um auto ou analisar um documento. Mas justamente porque ela pensa, ela pode se confundir numa conta ou trocar um número. Por isso o toolkit divide o trabalho: pensar é com a IA, contar é com o script. Dimensionamento de SESMT, de CIPA e de NR-24, por exemplo, nunca sai da cabeça da IA. Sai sempre de um script, que faz a conta pela tabela oficial da norma.
E aqui está a parte mais importante para você. O Claude Code (e o Codex) não é um chat comum de internet. Ele consegue rodar esses programinhas dentro do seu próprio computador, como se fosse você mesmo abrindo um programa. Isso quer dizer três coisas boas:
ele sempre pede sua permissão antes de rodar qualquer coisa — quem autoriza é você;
os documentos da fiscalização ficam na sua máquina, não são enviados para servidores lá fora;
o que o script faz não gasta o "raciocínio" da IA, então é rápido e barato.
Um exemplo do dia a dia: quando você entrega a Relação de Vínculos Ativos, o PDF inteiro, com o nome de todos os trabalhadores, é lido por um script na sua máquina. A IA nem chega a ver essa lista. Ela recebe só o resultado da contagem: tantos homens, tantas mulheres, tantos aprendizes. Os nomes ficam onde sempre estiveram, no seu computador.
Somente a título de informação, alguns dos scripts executados localmente (na sua máquina):
dimensionar_sesmt.py — calcula o SESMT devido pelo Anexo II da NR-04
dimensionar_cipa.py — calcula a CIPA devida pelo Quadro I da NR-05
dimensionar_nr24.py — calcula banheiros, mictórios, lavatórios e bebedouros
enquadrar_cnae.py — acha o grau de risco do CNAE no Anexo I da NR-04
vinculos_ativos.py — lê a Relação de Vínculos e devolve só os números
relatorio_acidentes.py — monta o histórico de acidentes (CATs) da empresa
preparacao_docx.py — monta o dossiê que você imprime e leva na visita
gerar_painel.py — monta o painel com os prazos das suas auditorias
rehydrate.py — devolve os nomes reais dos trabalhadores no documento final
backup_arquivo.py — guarda uma cópia antes de regravar um arquivo
checar_pii.py — confere se escapou algum dado pessoal onde não devia

## 4.6 Avisos e limitações

As habilidades são apoio à redação e organização; o conteúdo jurídico de cada auto, termo e relatório é responsabilidade do AFT, que revisa tudo antes de transmitir.
/aft-autos-lavrados: a extração por pypdf precisa de calibração/verificação na 1ª execução contra os PDFs reais do Sistema Auditor.
O template do RT (aft-embargo-interdicao/template.docx) segue um modelo geral — você pode ajustar o template do cabeçalho.
/aft-atualizar atualiza o notebooklm-py automaticamente, sem perguntar antes — é uma dependência de terceiro (teng-lin/notebooklm-py) fora do controle de versão do toolkit.
As habilidades com model: claude-opus-4-8[1m] dependem do plano do AFT ter acesso ao modelo — o /aft-doctor testa e explica em linguagem simples se faltar.
A detecção de notificações DET do /aft-painel é heurística (pode dar falso positivo) — o AFT confere antes de cadastrar.
Validação end-to-end de /aft-NR12, /aft-NR18, /aft-tn-nco e do fluxo de Artifact do /aft-painel depende de interação e de máquina real com o app logado; testar no Windows real.

# 5. Como funciona a anonimização

Um dos motivos para usar o Claude Code/Codex é o controle sobre dados pessoais. O toolkit adota a pseudonimização reversível:
Quando um trabalhador entra na conversa (no relato de campo ou na lista de autuados), ele é registrado num mapa local (arquivo .depara na pasta da OS) que associa um código a cada dado real: [[TRAB_01]] para o nome, [[CPF_01]] para o CPF, [[AUTUADA]] para a razão social.
Dali em diante, os textos dos autos e os ecos no chat usam apenas os códigos. É assim que o texto circula durante a redação e revisão.
Na hora de gerar o TXT do Sistema Auditor, um script Python local (rehydrate.py) substitui os códigos pelos dados reais, por correspondência exata. A IA nunca digita um CPF no documento final — quem o faz é o script, que confere o formato e aborta se algo estiver errado. Num documento legal, um nome ou CPF trocado é inaceitável; por isso essa etapa não é feita pelo modelo.
Ficam na pasta da lavratura: o TXT real (para importar), a cópia tokenizada (segura para compartilhar com colegas) e o mapa de-para (sensível — nunca compartilhe).
O CNPJ da empresa não é tokenizado: ele é a chave que organiza as pastas, os anexos e a importação no Sistema Auditor.

# Para os desorganizados como meu: Painel e extensão Chrome/Edge — as notificações do DET direto na sua ficha

# 7. Boas práticas e segurança

Revise sempre. A IA é apoio à redação e organização. O conteúdo jurídico de cada auto, termo e relatório é responsabilidade do Auditor. Confira o código da ementa no ementário oficial antes de transmitir.
Nada de serviços online com documentos da fiscalização. Compressão de PDF, conversão de fotos e validação de arquivos são feitas por scripts locais do toolkit. Nunca use compressores ou conversores de site.
O arquivo .depara é sensível. Ele liga os códigos aos dados reais. Não compartilhe, não envie por e-mail, não suba para nuvem.
A cópia .tokenized.txt é a versão segura para compartilhar com colegas (não contém nome nem CPF de trabalhador).
Consultas ao NotebookLM enviam apenas a descrição da irregularidade (ex.: “máquina sem proteção fixa”) — nunca nomes de trabalhadores ou da empresa.
Acentuação: os textos dos autos usam português completo (ç, ã, é...). O que não pode aparecer são travessões (—), aspas curvas e emojis, que o encoding do Sistema Auditor não aceita — as habilidades já cuidam disso.

# 8. Problemas comuns

Regra geral: descreva o problema ao próprio Claude/Codex no </> Code (“o comando X deu este erro: ...”) — ele diagnostica e corrige na hora. A tabela abaixo cobre os casos mais comuns:

| Sintoma | Solução |
|---|---|
| Não sei se está tudo certo / algo parou de funcionar | Rode /aft-doctor: ele faz o check-up completo da instalação e aponta exatamente o que falta e como resolver. É sempre o primeiro a tentar. |
| “Git is required for local sessions” | Instale o Git (seção 2.2) e feche o aplicativo de verdade: botão direito no ícone do Claude na bandeja (perto do relógio) → Sair; reabra. Se persistir, reinicie o computador. |
| Python “não encontrado” | Peça ao Claude/Codex: “instale o Python com winget”. Se a rede bloquear, use o plano B manual (seção 2.7) e reinicie o aplicativo. |
| A habilidade não aparece ao digitar / | Feche e reabra o Claude Code/Codex. Se persistir, peça a ele: “as habilidades estão diretamente em ~/.claude/skills (ex.: ~/.claude/skills/aft-setup)? Se estiverem dentro de uma subpasta aft-toolkit, mova todo o conteúdo um nível acima”. |
| notebooklm: command not found | Peça ao Claude/Codex: “instale o notebooklm-py[browser] do repositório teng-lin com pipx e garanta que o comando notebooklm fique no PATH”; reinicie o terminal/app. |
| Habilidade /notebooklm não aparece (mas notebooklm --help funciona) | Peça ao Claude/Codex: “rode notebooklm skill install” e depois feche e reabra o app. O pip/pipx instala só o comando de terminal — a habilidade precisa desse passo extra (seção 3.1). |
| NotebookLM responde “sem acesso” | Solicite acesso em notebooks-aft.vercel.app e aguarde a liberação. |
| Foto HEIC (iPhone) não converte | Peça ao Claude/Codex: “instale o pillow-heif” (ou converta a foto para JPG). |
| Sistema Auditor não acha o anexo | O anexo precisa do nome na convenção AI_N_CNPJ_sufixoN.PDF, com .PDF em maiúsculas, e do caminho Windows correto no aft-config.md (campo path_windows). |

# 9. Suporte

Dúvidas, sugestões de novas habilidades ou problemas: fale com o mantenedor — Ricardo de Oliveira (AFT, SRTE/GO) — ou abra uma Issue em .
Bom proveito — e bem-vindo(a) à fiscalização assistida por IA, com os dados sob o seu controle.

# 10. Guia de Referência do AFT Toolkit v3.0 - Contribuição de Diego Negrão

Documento anexo em PDF, juntado ao final desta apostila.

## Passo a passo da instalação ao relatório final

A ordem natural de quem nunca usou: instale uma vez, cadastre a auditoria e siga o fluxo.
1

### Instale uma vez

Cria sua pasta de trabalho (~/Documents/AFT), grava seus dados de auditor (CIF, UORG), instala o seu perfil no Claude/Codex, as proteções de privacidade e deixa o painel sempre ligado na sua máquina. Guiado, do início ao fim.
/aft-setup
2

### Confira se está tudo certo

Diagnóstico completo em linguagem simples (🟢 🟡 🔴). Não altera nada — só verifica e explica como resolver. Rode sempre que algo parecer estranho.
/aft-doctor
3

### Já fiscalizava antes do toolkit?

Jogue a pasta antiga da fiscalização dentro de OS ATIVAS/ e peça para organizar: ela monta tudo no padrão do toolkit, com um plano que você aprova antes de qualquer arquivo ser mexido.
/aft-organiza-os
4

### Abra a auditoria

Uma pasta por empresa fiscalizada, com a ficha memory.md — a "capa da OS" onde ficam status, notificações DET, pendências e autos. O CNPJ é opcional aqui (só vira obrigatório na hora de gerar os autos).
/aft-nova-auditoria
5

### Prepare a ação fiscal

Antes de ir a campo: planeje a visita (denúncia, dados prévios, checklist) e, se for o caso, notifique a empresa pelo DET para apresentar documentos.
/aft-preparacao-acao-fiscal/aft-NAD
6

### Voltou da inspeção? Narre

Conte o que viu — por voz ou texto corrido. O relato vira uma lista organizada de achados, fiel ao que você disse, pronta para embasar autos e análises.
/aft-inspecao-fisica
7

### Analise os documentos da empresa

Cada tipo de documento tem uma especialista: PGR, ergonomia (AET), pacote de ponto eletrônico (AFD/AEJ/atestados), laudos de máquinas (NR-12) e acidentes de trabalho. Dúvida de enquadramento? A consulta busca ementa e fundamentação na base NotebookLM.
/aft-PGR-analise/aft-aet-auditoria/aft-jornada-analise/aft-auditoria-AR-NR12/aft-analise-acidente/aft-consulta
8

### Lavre os autos

A redação parte do seu relato e das análises; casos comuns têm habilidade própria (falta de registro, omissão de documentos do DET). Tudo passa pela revisão 5W1H e termina no TXT importável pelo Sistema Auditor — com anexos e com os dados pessoais protegidos. Você revisa e você transmite: o toolkit prepara, quem decide é o AFT.
/aft-inspecao-inicial/aft-registro/aft-det-630/aft-revisa-auto/aft-gera-ai

Consultoras de NR:
/aft-NR12 (máquinas) e /aft-NR18 (obras) ajudam no enquadramento durante a redação.
9

### Risco grave e iminente

Interdição ou embargo: o relatório técnico sai em .docx no modelo oficial, já com os autos derivados. Se a empresa pedir a suspensão com um laudo, a auditoria do laudo alimenta o RT de manutenção (quando você mantém a medida) ou o RT de levantamento (quando ela cumpriu tudo e você libera).
/aft-embargo-interdicao/aft-embargo-interdicao-manutencao/aft-auditoria-AR-NR12/aft-embargo-interdicao-levantamento
10

### Acompanhe prazos sem esforço

O painel mostra todas as auditorias em cards, com notificações DET, pendências e vencimentos — direto no navegador, só na sua máquina. Os prazos podem ir para o seu Google Calendar (evento por notificação, ✓ quando você responde).
/aft-painel/aft-agenda-det
11

### Feche a ação fiscal

Confira o que já foi efetivamente transmitido no Sistema Auditor e gere o relatório final da ação.
/aft-autos-lavrados/aft-relatorio-rel
12

### Mantenha o toolkit em dia

Uma frase e pronto: baixa a versão nova, confere a segurança do que chegou, atualiza seu perfil e te conta as novidades em português, sem jargão. Suas habilidades pessoais (minha-*) nunca são tocadas.
/aft-atualizar
