# AFT Toolkit

**Skills de IA para Auditores-Fiscais do Trabalho**, para uso no **Claude Code** (app desktop, Windows).

O toolkit transforma o Claude Code num assistente de fiscalização que trabalha **no seu computador**: organiza as pastas das OS, registra o relato de campo, enquadra NR/ementa, redige autos de infração, gera o TXT importável pelo Sistema Auditor e produz relatórios — tudo com uma política de **anonimização de dados pessoais** embutida.

## Por que Claude Code (e não o chat comum)?

- **Execução local**: os arquivos das suas fiscalizações ficam no seu computador (`Documentos\AFT`). As skills criam pastas, salvam autos, convertem fotos e geram o TXT diretamente no disco.
- **Anonimização (pseudonimização reversível)**: nomes e CPFs de trabalhadores são substituídos por tokens (`[[TRAB_01]]`, `[[CPF_01]]`) nos textos processados pela IA. Os valores reais ficam num mapa local e são re-injetados no TXT final por um **script determinístico** (`rehydrate.py`) — nunca pelo modelo. Um nome ou CPF trocado num documento legal é inaceitável; por isso essa etapa não é feita por IA.
- **Fluxo completo**: do relato ditado pós-inspeção até o arquivo pronto para o botão "imp. txt" do Sistema Auditor.

### O que são esses "scripts" que as skills mencionam?

Você vai ver, em várias skills, referência a arquivos com nome tipo `gerar_painel.py` ou `rehydrate.py` — são **scripts**: pequenos programinhas de computador, parecidos com uma calculadora ou um carimbo automático, que fazem sempre a mesma tarefa mecânica, exatamente igual, toda vez que rodam (gerar o painel, comprimir uma foto, montar o arquivo do Sistema Auditor). A diferença para a IA é essa: a IA "pensa" — lê, interpreta, redige o texto do auto —, enquanto o script só executa uma receita fixa, sem interpretar nada. É por isso que a troca de nome/CPF de um trabalhador no arquivo final, por exemplo, é feita por um script (nunca pela IA): script não erra por criatividade, só faz o que está escrito no código. E é aqui que mora a "mágica" do Claude Code: diferente do chat comum, ele consegue *rodar* esses programinhas no seu próprio computador — criar pastas, salvar arquivos, gerar o TXT — sempre pedindo sua permissão antes. O resultado é um assistente que conversa como uma IA, mas trabalha como um programa instalado na sua máquina.

## Instalação (resumo)

Veja o passo a passo completo em [COMO-INSTALAR.md](COMO-INSTALAR.md) (ou na apostila `Apostila-AFT-Toolkit.pdf` — protegida por senha, distribuída pelo autor no grupo de AFTs). São 4 passos — só os dois primeiros são manuais:

1. **Instale o aplicativo Claude** (claude.com/claude-code).
2. **Instale o Git** (git-scm.com — o app desktop exige o Git para abrir sessões locais no Windows) e reinicie o app pela bandeja.
3. **Cole o prompt de instalação** (está no COMO-INSTALAR.md) numa conversa do `</> Code`: o próprio Claude instala o Python via winget e clona este repositório em `~/.claude/skills`, pedindo sua permissão a cada comando.
4. **Reinicie o app e rode `/aft-setup`** — ele cria as pastas de trabalho, coleta seus dados uma única vez (nome, CIF e a sua lotação — basta dizer a cidade, ex.: "Anápolis", e o toolkit descobre o código de 9 dígitos da UORG) e instala as dependências.

**Conferir:** a qualquer momento, rode **`/aft-doctor`** para checar se está tudo no lugar (Python, Git, skills, configuração) — ele diz, em linguagem simples, o que falta e como resolver.

**Primeiro passo essencial (quem já fiscaliza):** copie as pastas das suas auditorias em andamento — do jeito que estiverem — para `~/Documents/AFT/OS ATIVAS/` e rode **`/aft-organiza-os`**. Com uma única aprovação, ele organiza tudo no padrão do toolkit, roda o `/aft-autos-lavrados` (busca no Sistema Auditor os autos já transmitidos de cada empresa e os registra no `memory.md`) e as **sessões de chat por empresa** aparecem sozinhas no grupo "OS ATIVAS" do menu lateral na próxima vez que você fechar e reabrir o app (vigia de sessões, automático). Quem começa do zero pula direto para o `/aft-nova-auditoria`.

**Atualização:** peça ao Claude *"Atualize o AFT Toolkit"* (ou `/aft-atualizar`) — ele atualiza as skills (`git pull`) **e** o comando `notebooklm` (`notebooklm-py`), se houver versão nova, e confirma com o `/aft-doctor` que nada quebrou.

## Skills incluídas

### Configuração e visão geral
| Skill | O que faz |
|---|---|
| `/aft-setup` | Configuração inicial: pastas de trabalho, dados do auditor (CIF/UORG), perfil do auditor (`CLAUDE.md` global), dependências, NotebookLM |
| `/aft-doctor` | Verificação pós-instalação: checa Python, Git, descoberta das skills, config, perfil, pasta de trabalho, bibliotecas, o estado do NotebookLM e a saúde das skills (frontmatter e modelos pinados, com teste ao vivo) — e diz, em linguagem simples, o que falta (só leitura) |
| `/aft-atualizar` | Atualiza as skills (`git pull`) e o comando `notebooklm` (notebooklm-py), se houver versão nova, e roda o `/aft-doctor` ao final para confirmar |
| `/aft-nova-skill` | Ajuda o AFT (leigo) a criar uma **habilidade própria**, para uma tarefa que o toolkit não cobre: pergunta objetivo, gatilhos e passos em linguagem simples e grava `~/.claude/skills/minha-<nome>/SKILL.md`. O prefixo reservado `minha-` garante que a skill própria é descoberta pelo Claude Code e **nunca se perde numa atualização** |
| `/aft-notebooklm-login` | Conecta/reconecta o NotebookLM à conta Google com mínima intervenção (cookies do navegador ou um único login em janela do Edge) — o Claude conduz tudo, sem terminal |
| `/aft-nova-auditoria` | Cadastra uma auditoria (nome livre, CNPJ opcional, município e o DET com prazo) — o começo do fluxo |
| `/aft-organiza-os` | Importa uma **pasta bagunçada de fiscalização pré-toolkit** jogada em `OS ATIVAS/`: lê os documentos (notificações DET, relação de autos do Sistema Auditor, resposta do empregador, fotos), extrai empregador/CNPJ-CPF/prazos/autos, mostra o plano antes-e-depois e — com sua aprovação — renomeia a pasta para o padrão, cria o `memory.md` completo e move cada arquivo para onde as demais skills esperam. Nunca apaga nada |
| `/aft-painel` | Gera um `painel.html` local em formato **dashboard de cards**: um card por OS colorido pela urgência do prazo de DET, e um clique abre o **detalhe da auditoria** (DETs, todos os autos de infração lavrados com nº do AI e constatação, pendências, atividades). Detecta PDFs de notificação DET ainda **não cadastrados** na ficha e, com `--scan`, puxa os autos ao vivo do Sistema Auditor (Windows ou Mac+Parallels, degradando para o último snapshot se indisponível) — um SISOS local, sem nuvem. Tem **modo interativo** opcional (mini-servidor local em `http://127.0.0.1:8347`, 100% offline): os cards ganham ações mecânicas — marcar DET respondida, resolver pendência, registrar atividade, mudar status e alternar embargo/interdição vigente/suspenso — gravadas direto no `memory.md` com backup automático, além de botões 📋 que copiam comandos prontos para colar no Claude Code. Aberto pelo arquivo (duplo-clique) continua só leitura. Com a extensão Chrome **"SisOS — Sync DET"** (Web Store) e o modo interativo no ar, o botão Sincronizar no site do DET puxa notificações novas e prazos atualizados direto para os `memory.md` (endpoint local `/api/det-sync` — sem nuvem nenhuma). O modo interativo pode ficar **sempre ligado** (serviço do sistema — LaunchAgent no macOS, Agendador de Tarefas com reinício automático no Windows), oferecido na instalação. Pode instalar também uma rotina diária que regenera o painel estático de manhã e, opcionalmente (com consentimento), publica como Artifact privado. O painel traz ainda o bloco **"Próximos vencimentos"** (agenda consolidada de DETs e pendências datadas de todas as OS), com botão "agendar no Google Calendar" por notificação — sem login nenhum |
| `/aft-agenda-det` | Espelha os prazos das notificações DET no **Google Calendar** do AFT, pelo conector oficial do Claude (login único do Google pela interface do Claude — nenhuma senha passa pelo toolkit): um evento de dia inteiro por notificação (`DET <código> <12 primeiros caracteres do empregador>`), com data atualizada quando o prazo é prorrogado e ✓ no título quando a notificação é respondida. Nunca apaga eventos nem toca no que não é do padrão. Só espelha: a fonte da verdade continua sendo o `memory.md` |

### Preparação da ação fiscal (antes da visita)
| Skill | O que faz |
|---|---|
| `/aft-preparacao-acao-fiscal` | Planeja a fiscalização ANTES de ir a campo: lê a Demanda/Ordem de Serviço do SFIT (anonimizando o denunciante), resolve/cria a OS, tokeniza qualquer lista nominal de trabalhadores, monta o link do endereço no Maps e o checklist de documentos a solicitar — salva tudo em `preparacao.md` e gera o `preparacao.docx`, a triagem "constatar no local x notificar" para levar impressa na visita. Aprofundamento técnico fica com `/aft-consulta` |
| `/aft-NAD` | Redige a Notificação para Apresentação de Documentos — documentos que se presume existir (PGR, controles de jornada, ASOs...), texto pronto para colar no DET, item por item |

### Inspeção e lavratura
| Skill | O que faz |
|---|---|
| `/aft-inspecao-fisica` | Transforma a narrativa ditada da visita num relato de campo estruturado (`inspecao-fisica.md`) — fiel, sem enquadramento |
| `/aft-consulta` | Consulta os ementários/notebooks do NotebookLM: tira dúvidas técnico-jurídicas **ou** enquadra um fato — missão tripla (IDENTIFICAR a ementa, FUNDAMENTAR capitulação/gradação/notas, REDIGIR minuta de Histórico anti-nulidade). Só consulta; não lavra (delega a `/aft-auditoria-geral`/`/aft-gera-ai`) |
| `/aft-auditoria-geral` | Lê o relato de campo, identifica NR/ementa (NotebookLM) e redige os autos de infração (todas as NRs + CLT), com gate de dupla visita |
| `/aft-informalidade` | Autos de falta de registro (art. 41 CLT) + falta de anotação na CTPS (art. 29 CLT) |
| `/aft-PGR-analise` | Auditoria sistemática do PGR (NR-01) nas 7 ementas, com confronto campo × documento e citação de páginas |
| `/aft-aet-auditoria` | Auditoria da Análise Ergonômica do Trabalho (AET) sob a NR-17 nas 5 ementas (17.3.3, 17.3.8, 17.4.1, 17.4.2, 17.4.3), com citação de página/folha e AET anexada a cada auto |
| `/aft-det-630` | Auto por omissão de documentos notificados via DET (ementa 001168-1, art. 630 §4º CLT) |
| `/aft-tn-nco` | Redige a Notificação para Correção de Irregularidades (texto pronto para colar no DET, item por item) |
| `/aft-email` | Redige o **e-mail** que acompanha o ato da fiscalização (notificação lavrada no DET, Termo de Interdição/Embargo encaminhado, adequação de documento analisado): resume o ato, deixa os prazos explícitos, avisa a consequência do descumprimento e empurra o destinatário para o canal oficial (DET / SEI). Entrega sempre **duas versões** — uma direta, para empresário sem jurídico, e uma técnica, para advogado/departamento jurídico — e, com o seu OK, grava no `email.md` da OS, que aparece no painel com botão de copiar. Nunca cita nome da empresa nem CNPJ, e **não envia nada**: quem envia é você |
| `/aft-embargo-interdicao` | Relatório Técnico de Interdição/Embargo em .docx + autos derivados das ementas |
| `/aft-auditoria-AR-NR12` | Julga o laudo de adequação à NR-12 / apreciação de riscos de máquinas (NBR ISO 12100, NBR 14153) apresentado pela empresa — em pedido de suspensão de interdição ou resposta a notificação — em 6 blocos de verificação, com parecer |
| `/aft-embargo-interdicao-manutencao` | Relatório Técnico de MANUTENÇÃO de interdição/embargo em .docx: analisa o requerimento de suspensão do empregador e conclui pela manutenção da medida (encadeia após `/aft-auditoria-AR-NR12` com parecer insuficiente) |
| `/aft-analise-acidente` | Analisa acidente/doença do trabalho (IN GMTP/MTP nº 2/2022): varre CAT, RAI/BO, laudos e PGR, propõe fatores causais (códigos SFIT 251–260) e gera o Relatório de Análise em .docx |

### Consultoras especializadas por NR
| Skill | O que faz |
|---|---|
| `/aft-NR01` | Especialista em disposições gerais e GRO: identifica a ementa (catálogo de 9 + ementário completo local + NotebookLM) e entrega o bloco II - IRREGULARIDADE. Sem linha de RT nem fragmento de interdição (NR-01 não fundamenta a medida cautelar); delega conteúdo de PGR à `/aft-PGR-analise` |
| `/aft-NR12` | Especialista em máquinas e equipamentos: identifica a ementa (catálogo de 16 + NotebookLM) e entrega o bloco II - IRREGULARIDADE, a linha do RT e o fragmento de interdição |
| `/aft-NR18` | Especialista na indústria da construção: separa as ementas de obra (catálogo de 29 + NotebookLM) e entrega o bloco II - IRREGULARIDADE e a linha do RT |
| `/aft-cnae-grau-risco-nr04` | Enquadra a atividade econômica no **grau de risco (1 a 4)** do Anexo I da NR-04 — por código CNAE (qualquer formato, com redução de subclasse a classe) ou por descrição da atividade — de forma determinística (script sobre os 673 códigos validados). Lembra a regra do maior GR (item 4.5.1) e encadeia para o dimensionamento do SESMT |
| `/aft-dimensionamento-sesmt-nr04` | Calcula a composição mínima do **SESMT** (Anexo II da NR-04) a partir do grau de risco e do nº de trabalhadores — quantidade e regime de cada profissional, regra de N > 5.000 e Observações A/B (saúde), com memória de cálculo — por script determinístico. Serve também à verificação de subdimensionamento em fiscalização |
| `/aft-cipa-nr05-dimensionamento` | Dimensiona a **CIPA** (Quadro I da NR-05) a partir do grau de risco e do nº de empregados — por script determinístico. Devolve os dois níveis: o quantitativo **por bancada** (efetivos e suplentes de cada representação) e o **total paritário** (dobro: eleitos pelos empregados + designados pelo empregador), com a regra de grupos de 2.500 acima de 10.000. Orienta qual número comparar com cada documento na verificação fiscal (ata de eleição × total paritário) |
| `/aft-nr24-dimensionamento` | Dimensiona as instalações exigidas pela **NR-24** a partir do nº de homens e mulheres do turno com maior contingente — bacias sanitárias e lavatórios (1:20, separados por sexo), mictórios (regra progressiva 1:20 até 100 e 1:50 no excedente), chuveiros, área do vestiário, armários, bebedouros, local para refeições e alojamento (item 24.7) — por script determinístico, com memória de cálculo. Trata as duas hipóteses de exposição separadamente (agentes × poeira) e sinaliza o ponto em aberto dos mictórios em estabelecimento anterior a 24/09/2019. **Modo obra:** em canteiro (`--obra`) e em frente de trabalho (`--frente-trabalho`) aplica a **NR-18, item 18.5**, setorial e prevalente — conjunto sanitário 1:20 com mictório, chuveiro 1:10, bebedouro 1:25, vestiário sempre obrigatório, deslocamento máximo de 150 m — detectando obra pelo CNAE da seção F ou pela sigla SPE no nome |

### Jornada / ponto eletrônico (Portaria 671/2021)
| Skill | O que faz |
|---|---|
| `/aft-jornada-analise` | Orquestrador: tria o pacote entregue (AFD/AEJ/atestados) e consolida os pareceres |
| `/aft-jornada-valida-afd-aej` | Validador determinístico (Python) do AEJ: estrutura, trailer, integridade referencial |
| `/aft-jornada-atestado` | Auditoria do Atestado Técnico/Termo de Responsabilidade do REP/PTRP (art. 89), com inspeção de assinatura por código |
| `/aft-jornada-auto-afd-aej` | Autos por AFD/AEJ ausente ou fora do padrão (ementas 002279-9 / 002280-2) |

### Empacotamento, rastreamento e relatórios
| Skill | O que faz |
|---|---|
| `/aft-revisa-auto` | Revisa o rascunho dos autos antes do empacotamento: checklist 5W1H e parágrafo de dano coletivo (SST) — gate automático dentro do `/aft-gera-ai` |
| `/aft-gera-ai` | Empacota autos redigidos no TXT importável pelo Sistema Auditor (latin-1), com anexos em PDF e pseudonimização reversível |
| `/aft-autos-lavrados` | Lê os PDFs já transmitidos no Sistema Auditor (`C:\SistemasAFT\...\PRO`), cruza com os rascunhos e marca no `memory.md` o que está lavrado `[x]` / pendente `[ ]` — read-only sobre o Sistema Auditor |
| `/aft-relatorio` | Relatório Final Simplificado a partir do `memory.md`: notificações lavradas, autos por tema e interdições com estado atual — texto para o SFITWEB + `.docx` para chefia/MPT |
| `/aft-diario` | **Diário de atividades**: cada dia trabalhado numa auditoria fica registrado na ficha da OS com as letras da tela **2.1 Atividades** do RI (A preparação · B início · C inspeção/auditoria/entrevista no estabelecimento · D análise documental fora · E documentos/lançamento em sistemas · F fim). As skills registram sozinhas (com a **data narrada** — "inspecionei dia 11" entra em 11), um gancho automático anota qualquer dia em que a ficha foi mexida, e o painel ganha a aba **Calendário** com o mês inteiro. No fechamento, gera a **agenda mensal** (com os dias úteis sem registro) e, por auditoria, as linhas prontas para transcrever no RI — incluindo OS arquivadas no meio do mês |
| `/aft-modelo-docx` | O **padrão visual** de todo `.docx` do toolkit: cabeçalho institucional com a lotação do AFT (brasão, MTE, SIT, logos), Times 12, títulos em azul institucional e tabelas zebradas — biblioteca `modelo_docx.py` usada pelas demais skills e pelos documentos avulsos |
| `/aft-sessoes-os` | Uma **sessão do Claude Code por empresa fiscalizada**, no grupo "OS ATIVAS" do menu lateral — **automático**: o vigia de sessões (serviço padrão da instalação) cria as sessões sozinho toda vez que o app fecha, com vínculo `sessao_claude` no `memory.md`, backup e `--desfazer`. A skill fica para conferir, aplicar "agora" ou desfazer |

## Modo rápido: cada skill funciona isolada

O fluxo completo abaixo é o caminho recomendado para quem quer rastrear prazos de DET e manter o painel atualizado — mas **nenhuma skill de redação exige esse fluxo**. Você pode chamar `/aft-auditoria-geral`, `/aft-informalidade`, `/aft-embargo-interdicao`, `/aft-PGR-analise` ou `/aft-det-630` direto, colar a narrativa da inspeção e receber o texto do auto pronto, sem nunca ter rodado `/aft-nova-auditoria` e sem precisar do CNPJ real (um nome fantasia basta — o texto do auto nunca embute o CNPJ no corpo, ele é só metadado administrativo). O CNPJ só passa a ser obrigatório no `/aft-gera-ai`, porque é um campo exigido pelo próprio Sistema Auditor (não pelo toolkit) para a importação do TXT — ou seja, dá pra usar o toolkit só para gerar o texto dos autos, sem nunca empacotar nada.

## Fluxo típico de uma fiscalização

```
0. /aft-preparacao-acao-fiscal → (opcional, antes da visita) planeja a ação: lê a Demanda/OS do
                              SFIT, cadastra/usa a OS, monta o checklist de documentos
   /aft-NAD                     → notifica a empresa a apresentar os documentos do checklist
   /aft-painel                  → a qualquer momento, vê todas as OS e os prazos vencendo
1. Visita ao estabelecimento
2. /aft-inspecao-fisica      → narra o que viu; vira relato estruturado na pasta da OS
3. /aft-auditoria-geral     → enquadra NR/ementa e redige os autos
   (desvios automáticos: /aft-informalidade p/ trabalhador sem registro ·
    /aft-embargo-interdicao p/ risco grave e iminente · /aft-PGR-analise p/ auditoria do PGR)
4. /aft-gera-ai              → TXT importável + anexos na pasta Autos DD-MM/
5. Sistema Auditor       → botão "imp. txt" → revisão → transmissão
6. /aft-autos-lavrados       → confere o que foi transmitido e marca no memory.md
7. /aft-relatorio          → relatório final consolidado
```

Sem `/aft-preparacao-acao-fiscal`, o começo do fluxo continua sendo `/aft-nova-auditoria` (cadastro simples, sem checklist de documentos). Dúvida técnica ou pesquisa de ementa, em qualquer ponto do fluxo, é `/aft-consulta`.

## Estrutura de trabalho

`Documentos\AFT\OS ATIVAS\` é onde moram as pastas de todas as empresas fiscalizadas — é criada pelo `/aft-setup` e cada empresa nova entra ali via `/aft-nova-auditoria`. Quando a fiscalização termina, a pasta da empresa vai para `OS ARQUIVADAS\` (mesmo nível).

```
Documentos\AFT\
├── aft-config.md            (seus dados — criado pelo /aft-setup)
├── painel.html              (visão geral das OS — gerado pelo /aft-painel)
├── OS ATIVAS\
│   └── EMPRESA X 12345678000190\
│       ├── memory.md                (ficha da fiscalização — criada pelo /aft-nova-auditoria)
│       ├── inspecao-fisica.md       (relato de campo)
│       ├── autos.md                 (autos redigidos)
│       ├── autos-lavrados.md        (o que já foi transmitido — fica na raiz)
│       ├── NOTIFICACOES\            (PDFs do DET + respostas do empregador)
│       │   └── ABC123 21-08-2026\   (tudo daquela notificação; data do download)
│       │       ├── notificacao-ABC123.pdf
│       │       ├── relatorio-atendimento-ABC123.pdf
│       │       └── item1_...\       (itens entregues pela empresa)
│       ├── AUTOS\
│       │   ├── Autos 19-05\         (TXT importável + anexos PDF)
│       │   └── Relacao de autos\    (relação .docx)
│       └── interdicao-embargo\      (termo, RT, laudos)
└── OS ARQUIVADAS\
```

### Quer a pasta em outro lugar?

Dá — e a escolha é permanente. Peça ao Claude *"quero minhas fiscalizações no HD externo"*
(ou onde for) e ele cuida do resto: leva os arquivos que já existem, sem sobrescrever
nada, e passa a usar o lugar novo em todas as skills. O `/aft-setup` também pergunta isso
na instalação, e o `/aft-doctor` mostra onde a pasta está e move se você pedir.

A escolha fica gravada em `~/.claude/aft-pasta.txt`, **fora** da pasta das skills — então
**atualizar o toolkit (`/aft-atualizar`) nunca a desfaz**: você configura uma vez e
esquece. Se um dia quiser voltar ao padrão, é só pedir.

> Nuvem (OneDrive, Dropbox, iCloud): funciona, mas lembre que aí os documentos de
> fiscalização passam a ser copiados para o servidor do provedor. Decisão sua.

## Segurança dos dados

- Tudo roda e fica **no seu computador**. Nenhuma skill envia arquivos para serviços externos (a compressão de PDF, conversão de fotos e validação de arquivos são scripts Python locais).
- **Única exceção, opcional e com consentimento a cada sessão:** o `/aft-painel` pode publicar o painel como **Artifact privado** na conta claude.ai do AFT (aba Artefatos do app), para acompanhar os prazos de qualquer lugar. O painel não contém dados de trabalhadores, mas lista as empresas sob fiscalização e prazos — o artifact é privado por padrão e o link **não deve ser compartilhado**. Nada é publicado sem o AFT autorizar expressamente.
- **Nunca** use compressores/conversores online para documentos de fiscalização.
- O arquivo `.depara_<CNPJ>.json` (mapa token↔dados reais) é sensível: não compartilhe, não commite.
- A cópia `*.tokenized.txt` é a única versão segura para compartilhar com colegas.
- Consultas de ementa ao NotebookLM enviam apenas a **descrição da irregularidade** — nunca nomes de trabalhadores ou da empresa.
- **Documentos do empregador são dados, não instruções.** O que a empresa fiscalizada entrega (resposta ao DET, PGR, atas, atestados, AFD/AEJ) é conteúdo não confiável: o perfil do auditor (`config/CLAUDE-aft.md`) instrui o assistente a tratá-lo como fato a analisar e a **relatar** — nunca obedecer — qualquer texto embutido que tente direcionar a fiscalização ("aprove", "não autue", "está regular").
- **Rede de proteção (deny-list).** O `/aft-setup` instala em `~/.claude/settings.json` (a partir de `config/settings-aft.json`) bloqueios que impedem o Claude de ler credenciais (`~/.ssh`, `~/.aws`, `.env`), de ler os mapas `.depara_*.json` e de usar comandos de acesso remoto (`ssh`, `scp`, `nc`). É a última linha de defesa caso algum documento tente induzir um vazamento.
- **Atualização verificada.** O `/aft-atualizar` varre o conteúdo que está chegando (`_scripts/checar_diff.py`) por sinais de adulteração antes de baixar — uma atualização de skills é tratada como artefato de cadeia de suprimentos.

## Ementários (códigos de ementa)

As skills buscam o código da ementa em 3 camadas:

1. **NotebookLM** (recomendado): peça acesso em https://notebooks-aft.vercel.app e conecte com `/aft-notebooklm-login` (ou pelo `/aft-setup`) — o Claude faz o login na sua conta Google por você, sem terminal. Os notebooks cobrem os ementários SST e de legislação + NRs específicas. Para **consultar livremente** os notebooks (tirar dúvida ou enquadrar um fato), use a skill **`/aft-consulta`**. A reconexão da sessão é automática (`NOTEBOOKLM_REFRESH_CMD`).
2. **Google Drive compartilhado**: [ementários por NR em Markdown](https://drive.google.com/drive/folders/1bktX9TkDIoix4iQuca3Yr5aWCfv97GSg?usp=sharing).
3. **Você informa o código** (formato `XXXXXX-X`).

## Estrutura do repositório

> O repositório é clonado como a **própria pasta de skills** (`~/.claude/skills`) — o Claude Code só descobre skills no primeiro nível dessa pasta, então cada skill precisa ficar diretamente nela (ex.: `~/.claude/skills/aft-gera-ai/SKILL.md`).

```
~/.claude/skills/   (= este repositório)
├── README.md · COMO-INSTALAR.md · Apostila-AFT-Toolkit.pdf
├── config/notebooks.json    (IDs dos notebooks do NotebookLM)
├── config/uorgs.csv         (tabela oficial de UORGs — o /aft-setup resolve o código pela cidade)
├── config/CLAUDE-aft.md     (perfil do auditor — o /aft-setup instala em ~/.claude/CLAUDE.md)
├── _scripts/                (scripts compartilhados: rehydrate, checar_pii, fotos, compressão, docx, gerar_painel, servir_painel, det_sync, instalar_rotina_painel, instalar_servidor_painel)
├── aft-setup/ · aft-doctor/ · aft-atualizar/ · aft-nova-skill/ · aft-notebooklm-login/ · aft-nova-auditoria/ · aft-organiza-os/ · aft-painel/ · aft-agenda-det/ · aft-gera-ai/ · aft-inspecao-fisica/ · aft-auditoria-geral/
├── aft-preparacao-acao-fiscal/ · aft-NAD/   (planejamento pré-visita e notificação de documentos)
├── aft-consulta/ · aft-informalidade/ · aft-det-630/ · aft-tn-nco/ · aft-email/ · aft-relatorio/ · aft-diario/ · aft-PGR-analise/ · aft-aet-auditoria/ · aft-embargo-interdicao/ · aft-auditoria-AR-NR12/ · aft-embargo-interdicao-manutencao/ · aft-analise-acidente/ · aft-autos-lavrados/ · aft-revisa-auto/ · aft-modelo-docx/ · aft-sessoes-os/
├── aft-NR01/ · aft-NR12/ · aft-NR18/   (consultoras por NR, com references/ementas-comuns.md)
├── aft-cnae-grau-risco-nr04/ · aft-dimensionamento-sesmt-nr04/ · aft-cipa-nr05-dimensionamento/ · aft-nr24-dimensionamento/   (enquadramento CNAE→GR, SESMT da NR-04, CIPA da NR-05 e instalações da NR-24, por script determinístico)
├── aft-jornada-analise/ · aft-jornada-valida-afd-aej/ · aft-jornada-atestado/ · aft-jornada-auto-afd-aej/
└── minha-*/   (SUAS skills próprias — criadas pelo /aft-nova-skill; git-ignoradas, sobrevivem a toda atualização)
```

> **Skills próprias, à prova de atualização.** Você (ou qualquer colega) pode criar skills
> suas para tarefas que o toolkit oficial não cobre. Basta que o nome comece com `minha-`
> (o `/aft-nova-skill` faz isso por você). Esse prefixo é um **namespace reservado**: nenhuma
> skill oficial o usa, o `.gitignore` protege essas pastas, e o `git pull` do
> `/aft-atualizar` **nunca as toca** — elas ficam no seu computador, suas, para sempre.

## Avisos

- As skills são **apoio à redação e organização**. O conteúdo jurídico de cada auto, termo e relatório é de responsabilidade do AFT, que revisa tudo antes de transmitir.
- Nunca aceite código de ementa, item de NR ou capitulação sem conferir no ementário oficial.
- O template do RT (`aft-embargo-interdicao/template.docx`) segue o modelo da SRTE/GO — auditores de outras SRTEs devem ajustar o cabeçalho.
- Guard-rail de PII: `_scripts/checar_pii.py` varre um relato/pasta e **avisa** se houver CPF ou PIS/PASEP com dígito verificador válido (o único dado de alto dano que pode entrar por engano). Não troca nem bloqueia nada — a anonimização real continua determinística (`rehydrate.py`).
- Guard-rail de supply-chain: `_scripts/checar_diff.py` varre o diff de uma atualização (linhas que estão chegando) por Unicode invisível e padrões de exfiltração/execução remota, e **avisa** antes do `git pull` (chamado pelo `/aft-atualizar`). Também é só um alarme — quem decide atualizar é o AFT.

## Contribuindo

Sugestões de novas skills ou melhorias: abra uma Issue ou fale com o mantenedor (Ricardo de Oliveira, AFT — SRTE/GO).
