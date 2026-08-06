# Novidades do AFT Toolkit

Registro do que muda no toolkit a cada atualização — escrito para você, sem jargão de
programador. O `/aft-atualizar` mostra as entradas novas sempre que você atualiza; para
rever tudo, basta abrir este arquivo.

---

## 06/08/2026
<!-- commit: skill-email -->

**Nova skill `/aft-email`: o e-mail que acompanha a notificação, o Termo ou a análise —
em duas versões.** Depois de lavrar uma notificação no DET, entregar um Termo de
Interdição ou analisar um PGR, quase sempre vem um e-mail avisando a empresa (ou o
advogado dela). Agora é só pedir: *"faz um e-mail para essa notificação do DET"*.

- **Sempre duas versões do mesmo e-mail.** Uma **direta**, para o empresário ou o RH que
  não conhece a legislação — frases curtas, cada exigência explicada em português comum.
  E uma **técnica**, para empresa com departamento jurídico ou advogado — base normativa
  precisa e o peso da autoridade da inspeção do trabalho. Você escolhe qual usar.
- **Ela lê o documento e resume.** Anexe o PDF da notificação (com o código único) ou do
  Termo de Interdição: o e-mail sai com o resumo do que foi pedido, os prazos em
  dd/mm/aaaa e o aviso, firme e educativo, do que acontece se não cumprir.
- **Os blocos que você sempre usa vêm prontos e literais**: como entrar no DET e enviar os
  documentos (com o aviso de que prorrogação só se pede pelo DET), como pedir a suspensão
  da interdição pelo SEI, a citação da dupla visita (só quando você disser que se aplica)
  e o fechamento sobre dúvidas.
- **Também melhora texto seu.** Cole o seu rascunho e ela devolve as duas versões
  reescritas **e** o retorno sobre o original: ortografia, gramática e estrutura, com o
  porquê de cada mudança.
- **Nome da empresa e CNPJ nunca entram no e-mail** — ela escreve "a empresa", "esse
  estabelecimento". Nem nome de trabalhador, nem denúncia.
- **O e-mail aprovado fica guardado e à mão.** Com o seu OK, ele vai para o `email.md` da
  pasta da OS e aparece no **painel**, no card da auditoria, na seção **E-mails**: dá para
  ver o texto e copiar com um clique (o assunto também).

Ela **não envia nada**. Quem manda o e-mail, do e-mail institucional, é sempre você.
As skills `/aft-NAD`, `/aft-tn-nco` e `/aft-rt-rgi` passam a oferecer o e-mail no fim do
trabalho delas.

---

## 06/08/2026
<!-- commit: preparacao-perfil-empresa-cipa -->

**A preparação da ação fiscal agora chega sabendo o que a empresa faz — e qual CIPA
ela deve ter.** O `preparacao.docx` que você imprime e leva na visita ganhou duas
seções novas, e perdeu o que não servia para nada em campo.

- **Seção 1 — A empresa.** Com o CNPJ (ou o PDF da OS), a skill faz uma busca rápida
  na internet e resume o que a empresa produz, onde opera, o porte e notícias que
  interessam à fiscalização (acidente noticiado, autuação, ação do MPT). Cada
  parágrafo vem com a fonte. É indício para orientar o olhar, nunca prova — o que
  vale continua sendo o constatado no local. Só vão para o buscador razão social,
  CNPJ e município: teor de denúncia e nome de pessoa **nunca** saem da sua máquina.
- **Seção 2 — Grau de risco e CIPA devida.** O nº de trabalhadores virou pergunta
  obrigatória da preparação (se você anexar a lista de empregados, ele sai da lista).
  Com ele e o CNAE, a skill roda a `/aft-cnae-grau-risco-nr04` e a
  `/aft-cipa-nr05-dimensionamento` e põe no documento a CIPA que aquele
  estabelecimento deve ter — Quadro I por representação e o total paritário, para
  você comparar com a ata de eleição ainda na visita. Se você não souber o efetivo,
  a preparação segue sem a seção e deixa a pendência anotada; nada trava.
- **Saiu o que não ajudava.** Sem "Equipe AFT", sem "prazo da fiscalização" e sem a
  linha de assinatura no fim — o documento é seu roteiro de trabalho, não uma peça
  para assinar. Em "Ordem de Serviço" ficou só o número.
- **O vencimento não se perdeu.** O prazo limite para término da fiscalização agora é
  gravado no `memory.md` como `**Vencimento da OS:**`, junto com o número da OS.

Os números da CIPA no documento são calculados pelos scripts na hora de gerar o
arquivo, a partir do `memory.md` — não são digitados pelo Claude. Se algum sair
diferente do que você viu na conversa, é sinal de CNAE ou efetivo desatualizado no
`memory.md`.

---

## 05/08/2026
<!-- commit: instalacao-windows-tres-mensagens -->

**Instalação no Windows: o Passo 3 virou três mensagens, e agora funciona.**
Colegas estavam esbarrando numa recusa do próprio Claude na hora de instalar as
skills. O motivo não era o toolkit: o passo antigo mandava baixar o repositório
**direto** para `~/.claude/skills`, que é a pasta de onde o Claude lê as
instruções dele — e ele é treinado (com razão) para desconfiar de conteúdo da
internet indo direto para lá.

- **Baixar → conferir → instalar.** O `COMO-INSTALAR.md` agora pede três
  mensagens em vez de uma: a primeira instala Git/Python/notebooklm, a segunda
  baixa o toolkit para `Documentos\aft-toolkit` e manda o Claude **ler e
  explicar** o que veio, e só a terceira move para a pasta de skills. Quando
  chega a hora de instalar, ele já conferiu o que está instalando — e a recusa
  não acontece.
- **Saiu o parágrafo de "contexto de confiança".** O texto que afirmava que os
  repositórios eram oficiais e estavam autorizados fazia o efeito contrário:
  insistir que algo é confiável é justamente um sinal de alerta para o Claude.
- **Se ele recusar mesmo assim, não discuta.** Argumentar deixa ele mais
  desconfiado, não menos. O guia explica isso e traz o Plano B (os mesmos
  comandos, colados no PowerShell) já corrigido.
- **`notebooklm skill install` agora é opcional.** As skills do toolkit usam o
  comando de terminal `notebooklm`, não a skill `/notebooklm` — um passo a menos
  na instalação.

Quem já está instalado não precisa fazer nada: a mudança é só no guia de
instalação, para repassar a colegas.

---

## 04/08/2026
<!-- commit: skill-relatorio-acidentes -->

**Nova skill `/aft-relatorio-acidentes`: o histórico de CATs da empresa, em um
comando.** Você informa o CNPJ (ou anexa o CSV do Portal AFT) e sai o Relatório
de Acidentes do Trabalho da fiscalizada: todas as CATs em ordem cronológica,
com lesão, parte do corpo, CID, agente causador, local, duração do tratamento
e óbitos em destaque, mais um resumo estatístico no topo.

- **Dois modos.** Modo A: o CSV `CatsCNPJ_*.csv` exportado do Portal AFT.
  Modo B: a base estadual de CATs (planilhas do eSocial, uma por ano) — no
  primeiro uso a skill pergunta onde está a pasta das planilhas do seu estado
  e grava a escolha no `aft-config.md`; depois basta o CNPJ.
- **Tudo local, nada na nuvem.** As CATs têm nome, CPF e dados de saúde de
  trabalhadores. Quem lê os arquivos e monta o relatório é um script Python na
  sua máquina; no chat aparecem só os números agregados e os caminhos dos
  arquivos — nenhum nome de trabalhador.
- **Dois formatos, na pasta certa.** `Relatorio-Acidentes-<cnpj>.md` e `.docx`
  (padrão visual do toolkit), gravados na subpasta `Acidentes/` da empresa em
  OS ATIVAS. Se já existirem, o script faz backup antes de regravar.
- **Limpeza de dados.** O script conserta sozinho os defeitos de codificação
  típicos dessas bases (acentos virados em `Ã§`/`ø`), descarta CATs
  substituídas por retificação e anota reaberturas e comunicações de óbito.
- **Divisão de trabalho.** Esta skill levanta o histórico; a análise
  aprofundada de um acidente (IN 2/2022) continua com a `/aft-analise-acidente`.
- **Integrada à preparação da ação fiscal.** A `/aft-preparacao-acao-fiscal`
  ganhou a FASE 4.5: quando o CNPJ é conhecido, ela chama a
  `/aft-relatorio-acidentes` e leva o histórico de CATs para o planejamento —
  o `preparacao.md` ganha a seção "Histórico de acidentes (CATs)" com os
  agregados (totais, óbitos, período, principais agentes causadores e partes
  do corpo mais atingidas), e os pontos de atenção da visita passam a apontar
  o setor e o tipo de risco onde a empresa mais se acidenta. O relatório
  completo fica na pasta `Acidentes/` da OS; no chat e no `preparacao.md`
  entram só os números.

---

## 03/08/2026 (tarde)
<!-- commit: skill-levantamento-total -->

**Nova skill `/aft-levantamento-total`: o Relatório Técnico que levanta a
interdição ou o embargo.** Até agora o toolkit cobria a origem da medida
(`/aft-rt-rgi`), o julgamento do laudo (`/aft-auditoria-AR-NR12`) e a negativa
da suspensão (`/aft-rt-manutencao`) — faltava o desfecho feliz: a empresa
cumpriu tudo, o risco grave e iminente foi afastado e o auditor decide
levantar. A nova skill redige esse RT.

- **Documento breve, de propósito.** O levantamento não reabre o mérito: são 7
  seções curtas que registram as datas (requerimento, análise dos documentos no
  SEI e, se houve, a nova inspeção física), o número do processo SEI, o objeto
  liberado e a conclusão pelo levantamento total. Se o auditor quiser destacar
  algo, o registro entra no item 2 ou na conclusão.
- **Mesmo visual do RT original.** O `.docx` sai com o cabeçalho institucional,
  a fonte e os espaçamentos do template do `/aft-rt-rgi` — mas sem o bloco de
  instruções de pedido de suspensão no rodapé, que deixa de fazer sentido
  quando a medida se encerra.
- **Quem decide é sempre o auditor.** A skill só redige quando o levantamento
  total já foi decidido; se a intenção for negar, ela aponta para a
  `/aft-rt-manutencao`, e se o laudo ainda precisa ser julgado, para a
  `/aft-auditoria-AR-NR12`.

---

## 03/08/2026
<!-- commit: instalacao-confianca-e-plano-b -->

**O guia de instalação ficou mais robusto contra um tropeço real: o Claude do
colega pode recusar a instalação por precaução de segurança.** Aconteceu com uma
auditora: o assistente dela travou nos dois últimos passos (baixar o `notebooklm`
e o toolkit dos repositórios no GitHub) por considerar fontes "pessoais" um risco
— excesso de zelo, mas deixou a instalação pela metade. Duas mudanças no
COMO-INSTALAR.md resolvem:

- **A mensagem do Passo 3 agora se apresenta.** O texto que o colega cola no
  Claude passou a abrir dizendo que os dois repositórios são as fontes oficiais
  do toolkit, mantidas por Auditor-Fiscal, e que o dono da máquina autoriza a
  instalação — o contexto de confiança que faltou naquele caso.
- **O Plano B ficou completo.** Antes só ensinava a baixar o toolkit à mão;
  agora traz também os comandos manuais do `notebooklm`, prontos para colar no
  PowerShell — na forma que funciona mesmo quando o `pipx` não entrou no PATH e
  com o extra `cookies` (necessário para o login automático pelo navegador), que
  faltava nas instruções antigas. Serve para rede bloqueada, computador sem
  winget ou assistente que recusou.

---

## 02/08/2026 (tarde)
<!-- commit: nr12-capitulacoes-e-ligacao-catalogos -->

**As capitulações do catálogo da NR-12 foram conferidas uma a uma e corrigidas — e o
relatório de interdição passou a consultar os catálogos antes de ir à internet.**

- **Capitulações da NR-12 acertadas.** As 16 ementas do catálogo da `/aft-NR12` citavam
  faixas de itens ("itens 12.5 a 12.5.17") e quase nenhuma mencionava a redação vigente.
  Capitular dezoito subitens quando o fato viola um só enfraquece o enquadramento e abre
  espaço para impugnação. Cada uma foi conferida no caderno da NR-12 e agora traz o
  **subitem exato** e a **Portaria 916/2019**. O catálogo da NR-18 já estava correto.
- **Uma ementa estava trocada.** O bloco "Interface de Segurança (falta de CLP ou relé)"
  apontava para a ementa 312360-0, que na verdade trata de *categoria inadequada* do
  sistema. Para falta de relé ou CLP monitorando, a ementa correta é a **312364-2**.
  Corrigido, com nota explicando a diferença — quem seguisse o catálogo lavraria a
  ementa errada.
- **Relatório de interdição usa os catálogos primeiro.** Antes de consultar o
  NotebookLM, a `/aft-rt-rgi` agora varre os catálogos da NR-12 e da NR-18, que já
  trazem os "gatilhos" que ligam a sua narrativa à ementa certa. Eles resolvem cerca de
  um terço dos casos sem depender de internet; no restante, a consulta continua.

---

## 02/08/2026
<!-- commit: rt-rgi-embargo-fotos-e-montador -->

**O relatório de interdição aprendeu a diferença entre interditar e embargar, passou
a aceitar fotos e ficou muito menos sujeito a erro na montagem.** Tudo isso saiu de
um teste com dois casos completos (máquinas e obra). Você não precisa fazer nada.

- **Embargo x interdição.** A NR-03 separa as duas medidas pelo objeto, não pela
  gravidade: **obra é sempre embargo**; máquina, setor ou atividade é interdição.
  A skill não sabia disso e produzia um "Termo de Interdição" mesmo para obra, com
  o texto todo falando em interdição e o campo pedindo "identificação da máquina".
  Agora ela decide certo e adapta o documento inteiro sozinha. Também passou a
  restringir a paralisação ao menor escopo possível (só os pavimentos com problema,
  por exemplo), como a norma manda.
- **Fotos dentro do RT.** Antes não havia jeito de pôr foto no relatório. Agora a
  foto entra no corpo do documento, logo abaixo da irregularidade que ela ilustra,
  já no tamanho certo da página e com legenda. A única exigência é que a foto
  exista como arquivo: imagem colada no chat não serve, tem que estar salva.
- **Montagem do documento sem edição manual.** O relatório era montado editando o
  "código" do Word à mão, um campo de cada vez — lento e fácil de errar. Um script
  novo preenche tudo de uma vez e confere o resultado. De quebra, ele evita três
  defeitos que já apareciam: numeração interna inválida que corrompia o arquivo,
  ementas sem marcador (que faziam o conferidor acusar erro à toa) e o item
  "Requerimento expresso" aparecendo entre as medidas em vez de entre os documentos.
- **Conferidor de coerência mais confiável.** Ele acusava "NR-03 sem auto
  correspondente" em **todo** relatório, porque a NR-3 é a norma da própria medida e
  aparece no texto fixo. Esse alarme falso acabou.
- **Erros de português no modelo oficial corrigidos:** "preoposto" virou "preposto",
  "da empresa aptos" virou "apto" e "das Norma Regulamentadoras" virou "das Normas
  Regulamentadoras". Saíam em todos os relatórios emitidos.
- **O modelo passou a usar campos `{{nome_do_campo}}`, com um dicionário próprio.**
  Cada lugar do relatório que recebe texto tem agora um campo identificado, e a skill
  sabe o que vai em cada um: o que descrever no objeto, o que citar na irregularidade,
  como fundamentar consequência e probabilidade. A numeração dos itens e das alíneas
  passou a ser automática do Word — nada de "A)" ou "3." digitados. Um mesmo relatório
  pode ter vários objetos e vários fatores de risco, cada um com seu bloco.
  **Atenção a uma mudança de fundo:** os itens 1, 2 e 8 viraram texto fixo. A data
  da inspeção saiu do item 1 e passou a ter campo próprio no item 2 (veja abaixo).
- **Campo próprio para o contexto da inspeção, no item 2.** É onde entra, no mínimo,
  a data da inspeção física — e, quando houver, quem acompanhou, o que foi percorrido
  e o que a empresa não apresentou na hora. Com isso o item 4 ficou **só com as
  ementas, a descrição da irregularidade e a capitulação**, sem narrativa de visita
  no meio.
- **O texto gerado agora sai com a mesma cara do resto do documento.** Antes, o que a
  skill escrevia podia sair em outra fonte, sem justificação e sem recuo, porque cada
  trecho do modelo carrega sua própria formatação e alguns não a traziam. Agora o
  relatório sai todo em Tahoma, justificado e com o mesmo espaçamento; as ementas
  ganharam marcador; e sumiu a linha em branco que separava demais o último item das
  medidas de proteção.
- **A skill não inventa mais detalhe que você não constatou.** Modo operatório, tipo
  de serviço em execução e número de trabalhadores expostos só entram se estiverem no
  seu relato. Faltando o dado, aparece `[A CONFIRMAR PELO AFT: ...]` no documento,
  para você completar — em vez de um detalhe verossímil que passaria despercebido na
  revisão e cairia na impugnação. Pelo mesmo motivo, medidas e documentos exigidos
  agora só podem decorrer de uma irregularidade efetivamente listada.
- **Consulta obrigatória ao caderno da NR do caso.** A skill já consultava o
  ementário; agora consulta também o caderno da norma específica (NR-12, NR-18...).
  Num teste, essa segunda consulta revelou uma ementa aplicável que a primeira não
  tinha apontado.
- **As irregularidades agora aparecem logo abaixo do título "4. IRREGULARIDADE(S)".**
  Antes iam parar no fim da seção, depois de toda a explicação da metodologia e das
  tabelas — longe de onde se procura por elas. O modelo ganhou marcações com "#"
  indicando onde cada bloco de texto entra, e some do documento final a linha de
  exemplo "OBJETO: 1 – ATIVIDADE", que era só um lembrete de formato.

## 01/08/2026
<!-- commit: rt-rgi-precedentes-de-interdicao -->

**O relatório de interdição agora tem memória de casos: a `/aft-rt-rgi` consulta
precedentes reais antes de você decidir.** Reconhecer o risco grave e iminente no calor
da inspeção nem sempre é simples. A skill ganhou uma base de conhecimento com mais de
uma centena de Relatórios Técnicos de Interdição e Embargo reais (máquinas da NR-12,
obras da NR-18, trabalho em altura da NR-35 e outros), guardada num notebook próprio do
NotebookLM chamado "Interdições RGI".

- **Novo modo de dúvida.** Descreva a situação que encontrou ("prensa sem proteção na
  zona de prensagem, cabe interdição?") e a skill busca casos análogos: mostra o número
  dos termos precedentes, as ementas que foram usadas e como o fator de risco foi
  redigido. A sugestão vem fundamentada — e a decisão continua sendo sua.
- **Menos digitação no RT.** Se você não ditar os fatores de risco, as medidas de
  proteção ou os documentos a solicitar, a skill propõe uma minuta dessas seções a
  partir dos precedentes, em vez de deixar `[A PREENCHER]`.
- **Sem a base, nada quebra.** Quem ainda não tem acesso ao notebook "Interdições RGI"
  continua usando a skill exatamente como antes.

## 01/08/2026
<!-- commit: consumo-de-tokens-modelos-e-descricoes -->

**O toolkit ficou bem mais econômico — e nenhuma skill depende mais do modelo que
estiver escolhido na caixa do chat.** Alguns colegas relataram gasto excessivo de
uso. Fomos atrás e achamos três causas. Você não precisa fazer nada: tudo chega pelo
`/aft-atualizar`.

- **Menos texto carregado o tempo todo.** O app precisa manter em memória um resumo de
  cada uma das 40 skills, mesmo as que você não usa naquele dia. Esses resumos estavam
  longos demais e foram enxugados pela metade — só isso já corta cerca de 5 mil
  "palavras de contexto" de toda conversa, antes mesmo de você pedir qualquer coisa.
  O arquivo de perfil (o CLAUDE.md do toolkit) também foi apertado.
- **Cada skill agora diz qual modelo usar.** Dez skills não diziam e acabavam herdando
  o que estivesse selecionado na caixa — inclusive as que redigem auto de infração e
  relatório de interdição, que podiam cair num modelo rápido demais para a tarefa, e as
  calculadoras de CNAE, SESMT e CIPA, que só rodam uma conta e estavam consumindo um
  modelo caro à toa. Todas foram acertadas.
- **Fim de uma cobrança extra silenciosa.** Cinco skills pediam uma variante do modelo
  com "memória estendida" (o sufixo `[1m]`). Nos planos Max, Team e Enterprise isso não
  fazia diferença nenhuma; **no plano Pro, essa variante é paga à parte e vinha
  consumindo créditos avulsos sem necessidade**. O pedido foi retirado, e de quebra as
  skills passaram a usar a geração mais recente do modelo, pelo mesmo preço.
- **Raciocínio proporcional à tarefa.** Skills mecânicas (conferir instalação, gerar
  documento, agendar prazo) passaram a trabalhar em modo econômico. As que exigem
  análise — PGR, AET, acidente, interdição, laudo de máquina — continuam no modo mais
  caprichado.
- **Conversa longa perde menos coisa importante.** Quando o app precisa resumir uma
  conversa que ficou muito longa, agora ele sabe o que preservar: a pasta da OS em uso,
  CNPJ, códigos de DET, ementas e enquadramentos já decididos, e o que já foi gravado
  em disco. Os apelidos de trabalhador (`[[TRAB_01]]`) continuam protegidos no resumo.

**E uma recomendação simples, que vale mais que todas as outras juntas: deixe a caixa de
modelo do app em Sonnet.** Depois desta atualização, 31 das 40 skills usam Sonnet — com a
caixa nele, o toolkit inteiro trabalha sem ficar trocando de modelo no meio da conversa
(cada troca faz o app reler tudo o que já foi dito, e é isso que mais consome). Duas
observações:

- **Ponha a caixa em Opus só quando a sessão for julgar um documento técnico que a
  empresa entregou** — análise de PGR, de AET, de acidente, de laudo de máquina, ou RT de
  manutenção de interdição. Nesses casos o Claude passa a te lembrar sozinho no começo da
  conversa. Nas demais, Sonnet.
- **O nível de esforço fica em "alto"** — o `/aft-setup` já configura isso para quem
  ainda não escolheu um nível (se você já escolheu o seu, ele não mexe). As tarefas
  mecânicas do toolkit baixam esse nível sozinhas quando é o caso; o que continua no alto
  é justamente enquadrar irregularidade, consultar ementa e redigir auto ou RT.

## 30/07/2026
<!-- commit: notebooklm-rebrand-e-reconexao-silenciosa -->

**A conexão com o NotebookLM ficou imune ao rebrand do Google — e se renova sozinha,
sem janela.** Em 16/07/2026 o Google rebatizou o NotebookLM como "Gemini Notebook" e
mudou o endereço da página. Resultado: em muitas máquinas o login por janela passou a
falhar com "Login not detected within 5 minutes" **mesmo com o login feito
corretamente** — não era erro seu, nem do seu computador. O que muda:

- **Instalação corrigida.** O toolkit passa a instalar o comando `notebooklm` da
  versão que já entende o endereço novo (por enquanto, direto do projeto no GitHub;
  quando sair a versão oficial corrigida, o `/aft-atualizar` volta ao canal normal
  sozinho).
- **Reconexão sem janela.** Quando a sessão do NotebookLM expira (isso é normal e
  vai continuar acontecendo), o toolkit agora renova pelo login que ficou salvo da
  primeira vez — **sem abrir janela e sem você fazer nada**. Só quando esse login
  salvo também vence é que a janela do Google aparece de novo.
- **O `/aft-doctor` avisa.** Se a sua máquina estiver com a versão antiga do
  `notebooklm` (a que quebrou com o rebrand) ou com a reconexão automática no modo
  antigo (que abria janela), o doctor aponta e diz o que pedir ao Claude.
- **Ticket de correção mais preciso.** Corrigido um detalhe que fazia o campo
  "Skill" do ticket sair como um caminho estranho (`C:/Program Files/Git/...`) em
  vez do nome da skill.

## 30/07/2026
<!-- commit: pasta-padrao-no-onedrive-e-mudanca-de-pasta-completa -->

**No Windows, a pasta de trabalho agora nasce dentro do OneDrive.** Era o que a maioria
dos colegas fazia à mão depois de instalar: as fiscalizações ficavam numa pasta local,
fora do backup da instituição e invisíveis no notebook levado a campo. Numa **instalação
nova**, o toolkit passa a criar a pasta `AFT` dentro do seu OneDrive — o **corporativo**
(o do trabalho) na frente do pessoal —, mesmo quando o OneDrive não faz backup da sua
pasta Documentos.

- **Quem já usa o toolkit não tem nada mudado de lugar.** Uma pasta AFT que já existe com
  fiscalizações dentro nunca é abandonada. O `/aft-doctor` passa a **sugerir** a mudança
  (uma linha, não é defeito) e mover só acontece se você pedir. Se preferir manter onde
  está, é só me dizer: eu fixo a escolha e o aviso não volta.

**Mudar a pasta de lugar agora leva TUDO junto.** Antes, o `--mover` levava os arquivos
com segurança mas deixava para trás duas coisas que guardam o caminho por dentro — e o
colega só descobria depois, sem entender:

- **As suas conversas por empresa.** Cada sessão do menu lateral guarda a pasta da OS
  dentro dela; sem realinhar, o app mostrava **"Sessão não encontrada no disco"** (foi o
  que aconteceu com 2 de 8 empresas numa mudança real). Agora o `cwd` de cada sessão e o
  histórico da conversa acompanham a mudança. Como isso não pode ser feito com o app
  aberto, fica uma pendência que se aplica sozinha **no próximo fechamento do app** —
  feche e reabra uma vez e está pronto.
- **Os serviços que rodam sozinhos** (painel sempre ligado, rotina das 07:00, vigia de
  sessões). Eles guardavam a pasta congelada na instalação e continuavam varrendo o lugar
  antigo — o painel chegava a **recriar a pasta velha** ao se salvar. Agora são derrubados
  antes da mudança e reinstalados depois, já apontando para o lugar novo.

**O que você precisa fazer: nada.** Se um dia mudar a pasta de lugar (OneDrive, HD
externo, outro disco), peça a mudança normalmente e feche o app uma vez ao final.

---

## 29/07/2026 (3)
<!-- commit: relacao-de-autos-so-em-docx-sem-exigir-conversor-de-pdf -->

**Sumiu o aviso "nem LibreOffice nem Word encontrados nesta máquina".** Vários colegas
no Windows viram esse alerta no `/aft-doctor` — inclusive em computador **com o Word
instalado e funcionando**. Era falso alarme: a checagem procurava o Word num único lugar
do sistema e não o encontrava quando o Office é de 32 bits e o Python de 64 (combinação
comum). O susto era gratuito, e a conversão que ele cobrava era dispensável.

- **A Relação de autos lavrados agora sai só em `.docx`** — e é esse o documento que vai
  ao processo. O toolkit não tenta mais convertê-la para PDF sozinho.
- **Se você quiser um PDF**, é o caminho de sempre: abra o `.docx` no Word e use
  **Arquivo > Salvar como... > PDF**. Nada mudou aí.
- **Uma dependência a menos.** A skill `/aft-autos-lavrados` não precisa de LibreOffice
  nem de permissão para o toolkit dirigir o Word por trás. Menos coisa para dar errado
  na sua máquina.
- **O `/aft-doctor` deixou de conferir conversor de PDF** — a checagem inteira saiu, junto
  com o aviso.

**O que você precisa fazer: nada.** Se o aviso te incomodava, ele não volta.

---

## 29/07/2026 (2)
<!-- commit: ticket-de-correcao-quando-o-toolkit-quebra -->

**Quando o toolkit quebrar, ele agora escreve o chamado por você.** Até hoje, um defeito
aparecia na sua tela como um monte de linhas em inglês — e não havia como saber o que
dessa bagunça o mantenedor precisava para corrigir. Agora todo script do toolkit, ao
quebrar, grava sozinho um **ticket de correção**:

```
==================================================================
  O AFT TOOLKIT ENCONTROU UM ERRO E PREPAROU UM TICKET.
  Arquivo: ...\AFT\tickets\ticket-2026-07-29-1432.md
==================================================================
```

- **O que vai no ticket:** o erro exato, a versão do toolkit que você tem instalada, e o
  retrato da máquina — sistema, Python, quais programas existem aí, bibliotecas,
  serviços do painel. É a informação que o mantenedor precisaria pedir por mensagem, uma
  a uma.
- **O que NÃO vai, nunca:** nome de empresa, CNPJ/CPF, e-mail, conteúdo de documento de
  fiscalização. Tudo isso sai trocado por `<EMPRESA>`, `<INSCRICAO>`, `<PASTA AFT>`.
  Dê uma lida antes de enviar mesmo assim — quem decide o que sai da sua máquina é você.
- **Nova skill `/aft-erro`.** Para o que dá errado *sem* quebrar — a skill devolveu texto
  torto, o painel abriu em branco, o documento saiu estranho —, peça "/aft-erro" ou
  simplesmente diga "deu erro": o assistente monta o mesmo ticket com o contexto do que
  você estava fazendo. Ele também serve para completar um ticket que nasceu sozinho.
- Os tickets ficam em `tickets/`, dentro da sua pasta de trabalho. Nada é enviado a lugar
  nenhum: o arquivo fica na sua máquina até você encaminhá-lo.

**O que você precisa fazer: nada.** Se aparecer o aviso, peça ao assistente para
resolver — e mande o arquivo para quem mantém o toolkit.

---

## 29/07/2026 (1)
<!-- commit: relacao-de-autos-funciona-no-windows-sem-instalar-nada -->

**A Relação de autos lavrados voltou a funcionar no Windows.** Um colega reportou que o
Passo 5.5 da `/aft-autos-lavrados` nunca gerava o documento na máquina dele. O defeito
era real e atingia **todo Windows**: o script pedia ao sistema dois programas de
compactação (`zip` e `unzip`) que o Windows não tem. Ele quebrava no meio, deixando a
Relação por fazer.

- **O documento agora é montado pelo próprio Python**, que já sabe fazer isso sozinho.
  Nada para instalar, nada para configurar. O cabeçalho oficial com os logos SIT/AFT
  continua idêntico.
- **O PDF passou a sair pelo Word.** Antes, a versão em PDF só era gerada se você tivesse
  o LibreOffice instalado — que quase ninguém tem. Agora, quando falta o LibreOffice, o
  toolkit usa o **Microsoft Word que você já tem**, sem abrir janela e sem instalar
  biblioteca nenhuma. Se não houver nem um nem outro, o `.docx` sai normalmente e o
  assistente orienta a exportar o PDF na mão.
- **O `/aft-doctor` passou a conferir** se existe um conversor de PDF nesta máquina, para
  você saber disso antes de precisar.

**O painel também ficou muito mais rápido.** Ele era refeito do zero a cada vez que a
página era aberta — com uma dezena de auditorias, isso passava de 10 segundos, e chegava
a fazer o `/aft-doctor` acusar como "fora do ar" um painel perfeitamente saudável. Agora
o painel só é refeito quando alguma coisa muda de verdade: abrir a página de novo é
instantâneo. E o diagnóstico ganhou uma checagem nova, que percebe quando o servidor no
ar está lendo a pasta **errada** (sintoma de um servidor antigo que sobreviveu a uma
mudança de pasta de lugar).

**O que você precisa fazer: nada.**

---

## 28/07/2026 (6)
<!-- commit: painel-atualiza-sozinho-e-mostra-nad-sem-ciencia -->

**O painel se atualiza sozinho e passou a mostrar a NAD recém-lavrada.** Duas melhorias
no quadro das auditorias, as duas pensadas para o painel deixar de mentir por omissão
enquanto você trabalha.

- **Atualização automática.** Com o painel aberto no navegador, ele percebe sozinho
  quando uma ficha muda — inclusive quando o sync da extensão do Chrome acaba de trazer
  notificações do DET — e recarrega a página, mantendo aberto o card que você estava
  lendo. Não recarrega no meio de uma digitação: se você estiver escrevendo num campo,
  ele espera. Vale só no painel interativo (aberto pelo endereço local); o painel aberto
  por duplo-clique no arquivo continua como era.
- **Selo "⏳ aguardando ciência".** Uma notificação recém-lavrada some do painel até o
  empregador tomar ciência, o que pode levar até 15 dias (ciência tácita). Você lavrava a
  NAD e ela simplesmente não aparecia — dando a impressão de que nada havia sido feito.
  Agora toda notificação lavrada entra no painel desde o primeiro dia, marcada com o selo
  de aguardando ciência, e o selo cai sozinho quando a ciência chega.

**O que você precisa fazer: nada.**

---

## 28/07/2026 (5)
<!-- commit: mudanca-de-pasta-a-prova-de-caminho-longo -->

**Mudar a pasta de lugar ficou seguro de verdade.** A função lançada hoje mais cedo foi
testada de ponta a ponta numa máquina real, com 9 auditorias e 444 arquivos, e falhou:
seis PDFs de uma análise de acidente fatal (um ASO, um PCMSO, documentos CAF/CEF)
**ficaram para trás sem nenhum aviso**, e uma cópia pela metade dos documentos sigilosos
foi abandonada no destino. A causa é uma armadilha antiga do Windows, e ela agora está
resolvida.

- **Caminhos longos deixaram de sumir.** As pastas que o DET baixa aninham muito
  (`OS ATIVAS › EMPRESA › notificacao-XXXX › NOTIFICACAO_XXXX › NOTIFICACAO_XXXX ›
  ITEM_NN › arquivo.pdf`) e passam dos 260 caracteres que o Windows aceita por padrão.
  Acima desse limite, o computador se comporta como se o arquivo **não existisse** — e a
  cópia o pulava calada. A mudança de pasta agora usa o modo de caminho estendido do
  Windows e enxerga todos eles.
- **Conferência antes de apagar.** A pasta antiga só é removida depois que a nova é
  conferida arquivo a arquivo e byte a byte. Se algo não fechar, a cópia incompleta é
  desfeita sozinha e **os seus dados continuam onde estavam** — nunca fica um duplicado
  parcial de documento sigiloso largado por aí.
- **Nada de meio-termo perigoso.** Se a cópia conferiu mas algum arquivo da pasta antiga
  não pôde ser apagado (o caso comum: um `.docx` aberto no Word), a mudança se completa
  normalmente e isso vira apenas um aviso. Antes, esse caso era tratado como erro e o
  toolkit continuava apontando para a pasta já esvaziada.
- **Voltar atrás funciona.** Uma pasta de destino que contenha só diretórios vazios
  deixou de bloquear a operação — é o esqueleto que o Windows deixa para trás quando um
  programa está com a pasta aberta, não dado seu.
- **O painel não fica mais servindo a pasta errada.** Ao reinstalar o servidor do painel
  depois de mudar a pasta, a instância antiga era mantida viva segurando o endereço, e o
  `/aft-doctor` dizia "no ar" enquanto o painel lia o lugar de antes — chegando a recriar
  a pasta antiga sozinho. Agora o servidor velho é encerrado antes de o novo subir.

**O que você precisa fazer: nada.** Quem não mudou a pasta de lugar não é afetado.

**Uma ressalva honesta:** a pasta não pode ser renomeada enquanto estiver aberta em algum
programa — e a própria conversa do Claude Code aberta na auditoria conta como um deles.
Por isso a mudança quase sempre copia (mais lento que renomear) e costuma deixar para
trás a casca vazia da pasta antiga, que você pode apagar pelo Explorer depois de fechar o
aplicativo. Feche também os documentos abertos no Word antes de mudar a pasta: além de
travarem a limpeza, eles continuam apontando para o caminho velho.

---

## 28/07/2026 (3)
<!-- commit: pasta-de-trabalho-onde-o-aft-quiser -->

**Suas fiscalizações podem morar onde você quiser — e a atualização não desfaz mais
isso.** Até agora a pasta de trabalho era sempre `Documentos\AFT`. Quem precisava dela
em outro lugar (um **HD externo**, uma pasta sincronizada na **nuvem**, um segundo
disco) não tinha como: mesmo mudando à força, as skills continuavam procurando no
caminho antigo. Agora é só pedir — *"quero minhas fiscalizações no HD externo"* — e o
assistente muda tudo de lugar.

- **Ele leva os arquivos junto** e **nunca sobrescreve**: se já houver dados no destino,
  ele para e explica como juntar as duas pastas, em vez de misturar.
- **A escolha é permanente.** Ela fica guardada fora da pasta das skills, então
  **`/aft-atualizar` nunca mais a desfaz** — configure uma vez e esqueça. Era esse o
  risco real: atualizar o toolkit e ver o assistente voltar a procurar no lugar errado.
- **O painel acompanha.** O `/aft-painel` e o painel automático passam a ler a pasta
  nova. Como os dois serviços de fundo guardam o caminho por dentro, o `/aft-doctor`
  agora **avisa se algum deles ficou apontando para a pasta antiga** e reinstala com o
  caminho certo se você pedir.
- **O `/aft-setup` pergunta** onde você quer a pasta na hora da instalação, e o
  `/aft-doctor` sempre mostra onde ela está — dizendo, quando for o caso, que aquele
  lugar foi **escolhido por você** (e não um defeito a consertar).
- **Skills suas já nascem preparadas.** As habilidades que você cria com
  `/aft-nova-skill` (as `minha-*`) passam a procurar a pasta do jeito certo desde o
  primeiro dia. E se você já tinha alguma com o caminho antigo escrito por dentro, o
  `/aft-doctor` avisa — elas são suas, o toolkit nunca as edita sozinho.

**O que você precisa fazer: nada.** Quem está satisfeito com `Documentos\AFT` continua
exatamente como está — nada muda. A mudança só acontece se você pedir.

---

## 28/07/2026 (2)
<!-- commit: preparacao-le-a-os-do-sfit -->

**Anexou a Ordem de Serviço ou a Demanda? O toolkit lê sozinho — e protege o
denunciante.** A `/aft-preparacao-acao-fiscal` e a `/aft-nova-os` agora entendem os dois
PDFs que o SFIT-WEB gera: a **Demanda** ("Detalhar Demanda", com a denúncia e os dados
do demandante) e a **Ordem de Serviço** (mais resumida, com os prazos da fiscalização e
a equipe de AFTs). Basta anexar um deles — ou os dois — e dizer que vai fiscalizar
aquela empresa. A pasta da OS é criada com tudo preenchido — razão social, CNPJ,
endereço completo, telefone, CNAE (já com o grau de risco), número da OS e da demanda,
prazos para iniciar e terminar a fiscalização, equipe — sem redigitar nada; a sessão da
empresa no menu lateral continua aparecendo sozinha, como sempre.

- **Ementas da OS no dossiê** — a tabela de irregularidades "a fiscalizar" da demanda
  vira a seção `## Ementas da OS` no memory.md, com caixinhas para marcar o que já foi
  verificado; ela também guia o estudo prévio e o checklist de documentos da preparação.
- **Denunciante protegido** — nome, telefone e e-mail de quem denunciou **nunca**
  aparecem no chat nem nos arquivos de trabalho: o assistente se refere a ele como
  `[[DENUNCIANTE_01]]` e reescreve o resumo da denúncia sem os traços que o identificam
  (parentesco, tempo de casa, função). A única cópia do contato é o próprio PDF da
  demanda, arquivado dentro da pasta da OS — quem precisar ligar, abre o PDF.
- **Chegada planejada (Google Maps)** — a preparação grava no `preparacao.md` o link do
  endereço no Maps (montado no seu computador, sem consultar ninguém) e, se você quiser,
  abre o mapa para confirmar o local e anotar observações de acesso antes da visita.
- **Alarme de contato esquecido** — o guarda de privacidade (`checar_pii.py`), que já
  apontava CPF/PIS, agora avisa também e-mails e telefones que escapem para um arquivo
  de trabalho; as skills já mandam ignorar o telefone da própria empresa, então o alarme
  que sobrar merece atenção (pode ser o contato do denunciante).
- **`preparacao.docx`: a triagem para levar impressa na visita** — além da ficha em
  markdown, a preparação passa a gerar um documento no padrão do toolkit (cabeçalho
  oficial, pronto para imprimir) montado sobre uma única pergunta: *o que dá para
  constatar no local e o que, só faltando isso, precisa ser notificado?* São três
  seções — o quadro de triagem (ementas da OS de um lado, o que verificar em campo do
  outro), os documentos a exigir logo na chegada e, por último, o mínimo que sobra para
  o DET. A ideia é que a inspeção física resolva a maior parte: documento pedido por
  notificação chega depois e já ajustado.
- **Fim do "estudo prévio"** — a preparação não pergunta mais quais temas você quer
  estudar nos NotebookLMs antes da visita. Ela ficou focada no que é dela: organizar a
  OS, as ementas, o endereço e o checklist de documentos. Para tirar dúvida técnica,
  achar a ementa certa ou entender o que exigir sobre um tema, use a `/aft-consulta` —
  antes, durante ou depois da preparação, quantas vezes precisar.

**O que você precisa fazer: nada.** Anexe o PDF da OS na conversa e diga que vai
fiscalizar a empresa — o resto do fluxo segue como sempre.

---

## 28/07/2026
<!-- commit: agentes-revisor-e-autos-lavrados -->

**O toolkit ganhou seus dois primeiros agentes: ajudantes que trabalham numa "sala
separada".** Um agente é como um colega para quem o Claude delega uma tarefa pesada: ele
recebe a missão, trabalha isolado e volta só com o resultado — sem entulhar a sua
conversa com o conteúdo de dezenas de arquivos.

- **Revisor de autos (`aft-revisor-autos`)** — quando o `/aft-revisa-auto` roda (também
  como etapa automática do `/aft-gera-ai`), a revisão 5W1H agora acontece com **olhos
  frescos**: o revisor enxerga só o texto dos autos, sem ver a conversa que os redigiu —
  exatamente como o julgador do auto vai ler. Revisão mais dura, autos mais sólidos.
- **Varredura do Sistema Auditor (`aft-autos-lavrados`)** — o snapshot dos autos
  lavrados (leitura de dezenas de PDFs) agora roda fora da sua conversa; de volta, só o
  relatório. Na varredura de todas as OS, pode rodar **em segundo plano** enquanto você
  continua trabalhando. E qualquer decisão que seja sua (pasta ambígua, CNPJ divergente,
  ementa em duplicidade) volta como pergunta — o agente nunca decide por você.

**O que você precisa fazer: nada.** O `/aft-atualizar` instala os agentes sozinho
(ficam em `~/.claude/agents/`) e eles passam a valer no próximo reinício do app. Se por
algum motivo não estiverem instalados, as skills continuam funcionando do jeito antigo
— nada trava. O `/aft-doctor` agora confere isso também.

---

## 26/07/2026 (2)
<!-- commit: prefixo-aft-em-todas-as-skills -->

**Agora TODAS as skills do toolkit começam com `aft-`.** Antes, os nomes eram um
sortimento: algumas já tinham o prefixo (`/aft-setup`, `/aft-doctor`), a maioria não
(`/nova-os`, `/gera-ai`, `/painel`). Isso fazia com que, ao digitar `/` no Claude Code,
as skills do toolkit ficassem espalhadas no meio de tudo que você tem instalado — sem
como saber, olhando, o que era do AFT Toolkit e o que era outra coisa.

A partir desta atualização, **basta digitar `/aft` para ver todas as suas ferramentas de
fiscalização juntas, em bloco**. `/NR12` virou `/aft-NR12`, `/gera-ai` virou
`/aft-gera-ai`, `/painel` virou `/aft-painel`, e assim por diante. As quatro que já
tinham o prefixo (`/aft-setup`, `/aft-doctor`, `/aft-atualizar`, `/aft-rt-rgi`) não
mudaram.

**O que você precisa fazer: nada.** A atualização renomeia tudo sozinha e o seu perfil
(`CLAUDE.md`) é re-sincronizado no mesmo `/aft-atualizar`. Só há uma consequência
prática: **o nome antigo deixa de funcionar**. Se você digitar `/gera-ai`, não vai achar
— é `/aft-gera-ai` agora. Pedir em português continua funcionando igual ("empacota os
autos", "monta o painel", "qual a ementa para máquina sem proteção") — as skills
continuam sendo encontradas pelo que você descreve, não só pelo comando.

Suas skills próprias (as que começam com `minha-`) **não foram tocadas** — continuam com
o nome que você deu.

Tabela de-para, para consulta:

| Antes | Agora | Antes | Agora |
|---|---|---|---|
| `/nova-os` | `/aft-nova-os` | `/jornada-analise` | `/aft-jornada-analise` |
| `/organiza-os` | `/aft-organiza-os` | `/jornada-atestado` | `/aft-jornada-atestado` |
| `/painel` | `/aft-painel` | `/jornada-auto-afd-aej` | `/aft-jornada-auto-afd-aej` |
| `/agenda-det` | `/aft-agenda-det` | `/jornada-valida-afd-aej` | `/aft-jornada-valida-afd-aej` |
| `/sessoes-os` | `/aft-sessoes-os` | `/registro` | `/aft-registro` |
| `/nova-skill` | `/aft-nova-skill` | `/det-630` | `/aft-det-630` |
| `/notebooklm-login` | `/aft-notebooklm-login` | `/tn-nco` | `/aft-tn-nco` |
| `/preparacao-acao-fiscal` | `/aft-preparacao-acao-fiscal` | `/NAD` | `/aft-NAD` |
| `/inspecao-fisica` | `/aft-inspecao-fisica` | `/consulta` | `/aft-consulta` |
| `/auditoria-geral` | `/aft-auditoria-geral` | `/PGR-analise` | `/aft-PGR-analise` |
| `/gera-ai` | `/aft-gera-ai` | `/aet-auditoria` | `/aft-aet-auditoria` |
| `/revisa-auto` | `/aft-revisa-auto` | `/analise-acidente` | `/aft-analise-acidente` |
| `/autos-lavrados` | `/aft-autos-lavrados` | `/auditoria-AR-NR12` | `/aft-auditoria-AR-NR12` |
| `/sfitweb-rel` | `/aft-sfitweb-rel` | `/rt-manutencao` | `/aft-rt-manutencao` |
| `/modelo-docx` | `/aft-modelo-docx` | `/NR01` `/NR12` `/NR18` | `/aft-NR01` `/aft-NR12` `/aft-NR18` |
| `/cnae-grau-risco-nr04` | `/aft-cnae-grau-risco-nr04` | `/dimensionamento-sesmt-nr04` | `/aft-dimensionamento-sesmt-nr04` |
| `/cipa-nr05-dimensionamento` | `/aft-cipa-nr05-dimensionamento` | | |

> Detalhe técnico, para quem tiver curiosidade: esta atualização mexe em muitos arquivos
> de uma vez (é uma renomeação em massa). Se o `/aft-atualizar` mostrar uma lista grande
> de mudanças, é isso — e é esperado.

---

## 26/07/2026
<!-- commit: nr01-consultora -->

**Nova consultora: `/aft-NR01`, para as infrações de disposições gerais e gerenciamento de
riscos.** Funciona como a `/aft-NR12` e a `/aft-NR18`, mas para a NR-01: você descreve a
irregularidade (empresa sem PGR, sem ordens de serviço, documentos negados à
fiscalização, acidente que a empresa não analisou, treinamento sem certificado...) e
ela devolve a ementa certa — código, capitulação, gradação — e o bloco
II - IRREGULARIDADE pronto para o auto.

O que ela tem por dentro: um catálogo curado com as 9 ementas mais lavradas de NR-01
(conferidas uma a uma contra o ementário oficial e o NotebookLM da NR-01), o ementário
COMPLETO da norma (~79 ementas) e o texto integral da NR-01 — tudo dentro da própria
skill, no seu computador. Na prática isso significa resposta imediata e sem depender
de internet ou de login no NotebookLM para o dia a dia; o NotebookLM continua lá, mas
só como último recurso, para dúvida interpretativa que os arquivos locais não
resolvem.

Duas regras que ela respeita sozinha: NR-01 nunca vira interdição ou embargo (por isso
ela não gera linha de RT nem fragmento de interdição — se o caso tiver risco grave, ela
te encaminha para a consultora da NR certa e o `/aft-rt-rgi`); e PGR que EXISTE mas
está ruim continua sendo assunto da `/aft-PGR-analise` — a `/aft-NR01` cuida do PGR que
não existe, não foi apresentado ou está sem data e assinatura.

---

## 25/07/2026
<!-- commit: revisa-auto-paragrafacao-bloco-2 -->

**O bloco II dos autos não sai mais como um parágrafo gigante e ilegível no Sistema
Auditor.** Você notou isso num auto de PGR: o "II - IRREGULARIDADE" inteiro (a
identificação de perigos, as páginas citadas, o dano coletivo, a conclusão) tinha saído
como uma única linha corrida, sem nenhuma quebra. A causa: a skill que redige o texto
(no caso, a `/PGR-analise`) escrevia o bloco II como um parágrafo só, e ninguém depois
dividia isso.

Agora a `/revisa-auto` (o revisor de qualidade que já roda sozinho antes de todo
`/gera-ai`) ganhou um passo novo: ela olha o bloco II de cada auto e, se estiver tudo
em um parágrafo só, divide em vários — um para o enquadramento normativo, um por grupo
de constatações relacionadas, um para o dano coletivo, um para a conclusão. Só insere
linhas em branco onde o texto já muda de assunto; não muda, resume nem acrescenta uma
palavra sequer. Essas linhas em branco são exatamente o que já virava quebra de linha
de verdade no TXT do Sistema Auditor (com o recuo de 8 espaços que já corrigimos na
atualização anterior) - só que antes não existiam para o bloco II ser dividido.

Também reforcei as skills que mais geram bloco II em parágrafo único (`/PGR-analise`,
`/auditoria-geral`, `/aet-auditoria`) para já escreverem em parágrafos separados na
origem — a `/revisa-auto` continua sendo a rede de segurança para qualquer auto que
escapar disso.

---

## 22/07/2026 (4)
<!-- commit: painel-det-rotulo-notas -->

**O card de Notificações DET agora mostra o que você escreveu na ficha.** Antes,
quando a notificação tinha as datas do sync, o painel mostrava só isso — código
e datas — e jogava fora o que você tinha anotado à mão na linha do memory.md.
Agora cada notificação exibe:

- o **rótulo** ao lado do código — o tipo que você deu à notificação
  ("NAD jornada/ponto", "Termo de Notificação (Dupla Visita)");
- as **datas em uma linha só** (Lavratura · Ciência · entregas), em vez de
  empilhadas uma por linha — sobra espaço para o que interessa;
- as **suas notas** logo abaixo — "itens 3 (banco de horas), 4 (intervalo >2h)
  e 9 (ponto manual) não entregues — condicionais, verificar antes de cobrar".

Os fragmentos de data que já aparecem como campos (ex.: "lavrada 01/06/2026")
saem das notas para não duplicar; todo o resto é preservado exatamente como você
escreveu. Notificações registradas só pelo sync (sem texto seu) ficam como eram.

---

## 22/07/2026 (3)
<!-- commit: extensao-popup-ri-nuvem -->

**Duas correções na extensão Sync DET** (a do botão "Sincronizar" na tela do DET).

**O indicador de token voltou a dizer a verdade.** Ao clicar no ícone da
extensão, o status dizia "Token DET não encontrado" mesmo quando a sincronização
estava funcionando perfeitamente — ele procurava o crachá do DET numa gaveta
errada. Agora ele olha no lugar certo e usa o mesmo critério do botão (crachá com
menos de 25 minutos), então o que o indicador mostra é exatamente o que vai
acontecer se você clicar em Sincronizar.

**O destino na nuvem (SisOS) passou a respeitar o RI da auditoria.** Ele
importava *todas* as notificações do CNPJ — inclusive as de fiscalizações
antigas ou de outros auditores — e, ao preencher sozinho o RI, adotava a
notificação mais antiga da lista, podendo até trocar um RI que você já tinha
declarado. Agora vale a mesma regra que já corrigimos no painel local: **o RI que
você declarou manda**; auditoria ainda sem RI adota o da notificação **mais
recente**; e notificação de outra fiscalização não entra nem some em silêncio —
volta na resposta da sincronização para você decidir.

Isso só afeta quem usa o SisOS na nuvem. No uso local (painel em
`127.0.0.1:8347`), nada muda — a regra já era essa.

---

## 22/07/2026 (3)
<!-- commit: layout-notificacoes-autos -->

**A pasta de cada fiscalização ficou muito mais limpa** — antes, tudo se
acumulava solto na raiz: os PDFs de cada notificação do DET, as pastas com os
documentos que a empresa entregou, cada lote de autos lavrados, a relação de
autos... Numa auditoria com várias notificações isso passava de **30 itens
soltos** na mesma tela.

Agora existem duas caixas:

- **`NOTIFICACOES/`** — todos os PDFs de notificação, os relatórios de
  atendimento e as pastas com os documentos entregues pela empresa.
- **`AUTOS/`** — os lotes de autos (`Autos 25-05/` etc.) e a `Relacao de autos/`.

**O que continua na raiz** (e por um bom motivo): o `memory.md` e todos os
relatórios `.md` — `autos-lavrados.md`, as análises preliminares, as análises de
jornada. É de lá que o **painel** os lê e monta os links; se descessem para uma
subpasta, sumiriam do painel.

Você não precisa fazer nada: rode **`/organiza-os`** e ele migra as pastas
antigas sozinho — só criando as caixas e movendo o que já existe. **Nada é
renomeado nem apagado**, e as fiscalizações que ainda não foram migradas
continuam funcionando normalmente. O `/det-baixar-empregador` já baixa direto
para `NOTIFICACOES/`, e o `/gera-ai` já cria os lotes novos dentro de `AUTOS/`.

## 22/07/2026 (2)
<!-- commit: pasta-aft-onedrive -->

**Correção importante para quem usa Windows com OneDrive** — a pasta de
trabalho (`AFT` com `OS ATIVAS` e `OS ARQUIVADAS`) podia ser criada num lugar
que você nunca encontrava. Motivo: o toolkit presumia
`C:\Users\<você>\Documents`, mas quando o **OneDrive faz backup das suas
pastas**, "Documentos" passa a ser `C:\Users\<você>\OneDrive\Documentos` — e no
Windows em português ela se chama **Documentos**, não *Documents*. Resultado: o
`/aft-setup` criava uma pasta invisível no caminho errado e o AFT ficava sem
saber onde ficaram as fiscalizações.

Agora o toolkit descobre a sua pasta Documentos **de verdade** (lendo o registro
do Windows, que já sabe do OneDrive e do idioma) — e o **`/aft-doctor` passa a
criar a pasta se ela faltar**, dizendo o caminho exato onde criou. Basta rodar:

```
/aft-doctor
```

**Se você já instalou antes e a pasta ficou no lugar errado**, o toolkit **não
abandona os seus dados**: continua usando a pasta onde as suas fiscalizações
estão (elas funcionam normalmente ali). O `/aft-doctor` agora **avisa** que essa
pasta não é a sua "Documentos" de verdade — que é por isso que você não a acha
pelo Explorer — e **oferece mudar tudo de lugar**, com os dados. Se aceitar, ele
fecha o app (para soltar os arquivos), move a pasta inteira para a Documentos
correta e ainda atualiza o `path_windows` do seu `aft-config.md`. Nada é apagado,
e nada é sobrescrito: se já houver uma pasta com conteúdo no destino, ele recusa
e explica. Se preferir deixar como está, também tudo bem — continua funcionando.

O painel, o servidor e o vigia de sessões passam a usar o mesmo caminho
resolvido.

## 22/07/2026
<!-- commit: det-sync-ri-estrito-alerta-visto -->

**Sync DET: o RI do front-matter agora manda sozinho** — a pesquisa no DET é
por CNPJ do empregador, e vinha acontecendo de o sync puxar notificações de
OUTRA fiscalização do mesmo empregador (outro RI, às vezes de outro auditor).
Agora o campo `ri:` da ficha (`memory.md`) é **o** identificador da auditoria:
só entra notificação daquele RI. Se a sua OS acompanha duas fiscalizações
(ex.: ação fiscal + acidente), declare os dois RIs no próprio campo, separados
por vírgula (`ri: "320038432, 320199999"`). Notificação de RI alheio continua
aparecendo no relatório do sync como "ignorada" — nunca some em silêncio.

**Alerta "⚠️ atualização pendente" agora é dispensável** — constatamos que a
API do DET pode continuar marcando a notificação como "atualização pendente"
mesmo depois de o triângulo amarelo sumir da tela (a tela apaga quando você
abre a notificação; o campo da API, não necessariamente). Então o alerta no
painel ficava aceso para sempre. Agora ele é **clicável**: clicou = "já vi", o
alerta some da ficha e do painel — e **volta sozinho** se a empresa fizer uma
entrega nova naquela notificação (novidade de verdade).

## 21/07/2026 (4)
<!-- commit: auditoria-geral-anotacoes -->

**A `/inspecao-inicial` virou `/auditoria-geral`** — o nome antigo dava a
entender que ela só servia para a primeira visita, mas ela sempre foi a skill
que **enquadra e redige os autos**, seja a partir do relato de campo, seja da
auditoria documental (análise do PGR, dos ASOs, das respostas ao DET). Os
gatilhos antigos continuam funcionando ("inspeção inicial", "lavrar auto",
"ementa", "faça a auditoria", "emente as irregularidades"…) — é só o nome que
mudou.

**Nova seção `## Anotações da auditoria` na ficha da empresa** — antes, quando
você constatava algo durante a análise (o SESMT está subdimensionado, faltou o
ASO admissional de um trabalhador, o PGR está vencido), essa informação não
tinha para onde ir. Agora tem: é a **memória da auditoria**. Você anota — no
chat da auditoria ("registra que o SESMT está subdimensionado") ou direto no
painel, que ganhou um campo para **anotar** e um botão para marcar como
**tratada**. Depois, a `/auditoria-geral` lê as anotações em aberto e as
transforma em autos de infração (marcando cada uma como tratada quando vira
auto). Nada de constatação se perder no meio do caminho.

**Trabalhadores, CNAE e grau de risco na ficha** — a `/nova-os` passou a aceitar
(opcionalmente) o número de trabalhadores, o CNAE e o grau de risco, e a
`/auditoria-geral` os coleta dos documentos ou pergunta uma vez, sem repetir. O
grau de risco é derivado sozinho do CNAE (Quadro I da NR-04). Esses dados
alimentam o dimensionamento de CIPA/SESMT e agora aparecem no cabeçalho do card
no painel.

## 21/07/2026 (3)
<!-- commit: sessoes-vigia-automatico -->

**Sessões por empresa agora são 100% automáticas** — ontem as sessões do grupo
"OS ATIVAS" ainda dependiam de você aceitar uma oferta e fechar o app na hora.
Agora existe o **vigia de sessões**: um serviço em segundo plano (instalado por
padrão pelo `/aft-setup` e garantido pelo `/aft-atualizar`, como o servidor do
painel) que observa as suas pastas de OS ATIVAS e, toda vez que o app do Claude
é fechado, cria sozinho as sessões que faltam — com o nome da empresa, apontando
para a pasta da OS, dentro do grupo "OS ATIVAS". Você não responde mais nada:
criou uma auditoria (`/nova-os`), organizou um lote (`/organiza-os`) ou copiou
uma pasta à mão, e as sessões simplesmente **aparecem na próxima vez que você
abrir o app**. O `/aft-doctor` ganhou a checagem do vigia, e a `/sessoes-os`
vira a skill das exceções: conferir ("verifica as sessões"), aplicar AGORA sem
esperar o próximo reinício, desfazer tudo ou desligar o automático.

E cada sessão de empresa agora **nasce sabendo quem é**: o vigia mantém um
arquivo de contexto (`CLAUDE.md`) na pasta de cada OS, que o app carrega ao
abrir a sessão. Na primeira mensagem — "fiz essa notificação hoje, atualiza o
card e as datas" — o Claude já sabe que deve ler a ficha `memory.md`, que
"card/painel" é o painel do toolkit, quais skills usar e as regras de
privacidade. Sem esse briefing, a sessão nova respondia como um chat genérico.

## 21/07/2026 (2)
<!-- commit: skill-nr05-cipa -->

**Dimensionamento da CIPA (NR-05)** — nova skill `/cipa-nr05-dimensionamento`,
irmã das duas consultoras da NR-04. Você informa o **grau de risco** (o mesmo do
Anexo I da NR-04, que o `/cnae-grau-risco-nr04` descobre pelo CNAE) e o **número
de empregados** do estabelecimento, e ela calcula a composição mínima da CIPA
pelo Quadro I — sempre com a memória de cálculo.

O cuidado principal desta skill é não cair na **pegadinha da paridade**: os
números do Quadro I são **por bancada** (cada representação separada), e a CIPA
é paritária, então o total real é o **dobro** — metade eleita pelos empregados,
metade designada pelo empregador. A skill mostra os dois níveis (por bancada e
total) e ainda te diz **qual número comparar com qual documento** na
fiscalização: uma ata de eleição traz só a bancada dos empregados (compare com o
Quadro I por bancada); uma ata de instalação/posse traz as duas (compare com o
total paritário). Também trata a regra dos grupos de 2.500 acima de 10.000
empregados.

## 21/07/2026
<!-- commit: skills-nr04-cnae-sesmt -->

**Duas consultoras novas para a NR-04 (grau de risco e SESMT)** — chegaram duas
skills que respondem, com cálculo exato (nada "de cabeça"), as duas perguntas
clássicas do enquadramento da NR-04:

- **`/cnae-grau-risco-nr04`** diz o **grau de risco (1 a 4)** de uma atividade.
  Você informa o código CNAE em qualquer formato (`01.15-6`, `0115-6/00`,
  `1011201`) ou só descreve a atividade ("frigorífico", "construção de
  rodovias", "cultivo de soja") e ela responde consultando a base validada com
  os 673 códigos do Anexo I. Já lembra a regra do **maior grau de risco** entre
  a atividade principal e a preponderante (item 4.5.1) e emenda no cálculo do
  SESMT.

- **`/dimensionamento-sesmt-nr04`** calcula a **composição mínima do SESMT**
  (Anexo II) a partir do grau de risco e do número de trabalhadores: quantos
  técnicos, engenheiros, médicos etc., com o regime (integral/parcial), a regra
  para mais de 5.000 trabalhadores e as observações para estabelecimentos de
  saúde — sempre com a memória de cálculo. Serve também para **conferir, em
  fiscalização, se o SESMT constituído atende ao mínimo** (subdimensionamento).

As duas conversam entre si: informou o CNAE e o número de empregados, o Claude
enquadra o grau de risco e já dimensiona o SESMT na sequência.

## 20/07/2026 (3)
<!-- commit: sessoes-os -->

**Uma sessão de chat por empresa fiscalizada, organizada no menu lateral** — nova
skill `/sessoes-os`: ela espelha as suas pastas de OS ATIVAS na barra lateral do
app do Claude Code, criando uma sessão por empresa (com o nome da empresa e já
apontando para a pasta da OS) dentro do grupo "OS ATIVAS". Sessões que você já
tinha criado à mão são reconhecidas pelo nome e reaproveitadas, nunca
duplicadas. Como o app só relê essas informações ao abrir, a skill aplica num
"modo vigia": você fecha o app, ela aplica e o app reabre sozinho — com backup
automático e um "desfazer" completo. O perfil do auditor (v4) aprendeu as
regras de convivência: se você tratar de uma empresa fora da sessão dela, o
Claude avisa e oferece encaminhar para a sessão certa; quando uma OS é
arquivada, ele oferece arquivar a sessão junto. O `/nova-os` passa a oferecer a
criação da sessão de cada auditoria nova; o `/organiza-os` confere as sessões ao
final do lote (organizou empresas novas → oferece criar as sessões delas); e o
`/aft-setup` e o `/aft-atualizar` conferem se está tudo sincronizado.

Com isso, o **caminho de chegada** de quem já fiscaliza ficou oficial e está
documentado na instalação: depois do `/aft-setup` e do `/aft-doctor`, copie as
pastas das suas auditorias em andamento para `Documentos/AFT/OS ATIVAS/` e rode
o `/organiza-os` — com uma aprovação só, ele organiza tudo, roda o
`/autos-lavrados` (busca no Sistema Auditor os autos já transmitidos e registra
na ficha de cada empresa) e cria as sessões no grupo "OS ATIVAS".

## 20/07/2026 (2)
<!-- commit: sfitweb-rel-embaraco-extras-pasta -->

**Relatório final mais completo e melhor guardado** — três melhorias no
`/sfitweb-rel`:

- **Ele te pergunta o que mais incluir.** Antes de gerar o documento, o Claude
  lê e entende a ficha da OS e pergunta se você quer acrescentar outras
  ocorrências da fiscalização além das notificações, autos e interdições — por
  exemplo, empregados que continuaram sem registro após a NCRE, itens não
  regularizados ou qualquer fato relevante. O que você informar entra numa
  seção própria, "Outras Ocorrências Relevantes da Fiscalização".
- **Embaraço e fraude ganham destaque.** Toda situação de embaraço à
  fiscalização ou fraude (art. 630 da CLT) relatada num auto aparece numa caixa
  vermelha logo no início do relatório, detalhando exatamente como o
  administrado impediu, dificultou ou se negou a apresentar o que foi exigido —
  bem visível para a chefia e para o MPT.
- **Cada empresa tem sua pasta de relatórios.** O documento final passa a ser
  salvo em uma subpasta dedicada, "Relatórios de Fiscalização/", dentro da
  pasta da OS, e o Claude te avisa o caminho onde salvou.

## 20/07/2026
<!-- commit: modelo-docx-padrao -->

**Todo documento .docx do toolkit agora tem a mesma cara** — nova skill
`/modelo-docx`: o padrão visual oficial dos documentos gerados pelo toolkit.
Qualquer `.docx` — um relatório avulso que você pedir, o Relatório Final do
`/sfitweb-rel`, saídas de skills futuras — sai sobre o template com o cabeçalho
da auditoria (logos AFT e SIT), em Times New Roman 12, com títulos em azul
institucional, corpo justificado e tabelas com cabeçalho azul e linhas
zebradas. A skill traz a biblioteca pronta (`modelo_docx.py`) com as peças do
documento (capa, seções, listas, tabelas, assinatura), então tudo o que for
gerado daqui em diante segue o mesmo modelo sem esforço. Documentos com modelo
oficial próprio — RT de interdição/embargo e Relação de autos — continuam nos
templates deles. O perfil do auditor foi atualizado (v3) para aplicar o padrão
automaticamente também aos documentos pedidos fora das skills.

## 19/07/2026 (4)
<!-- commit: sfitweb-rel-v2 -->

**Relatório final de fiscalização muito mais completo** — o `/sfitweb-rel` foi
reescrito para acompanhar tudo o que o toolkit passou a registrar desde que ele
nasceu. Agora ele lê a ficha da OS (memory.md), o espelho do Sistema Auditor
(autos-lavrados.md, com os números oficiais dos AIs) e a pasta de
interdição/embargo, e monta o relatório com seções obrigatórias: notificações
lavradas (resumo dos itens notificados + data de lavratura), autos de infração
agrupados por tema (SESMT/CIPA, obra, inflamáveis, jornada...) e interdições
com o estado atual e as condicionantes — não só a lavratura. Cada auto sai com
os mesmos campos do painel: número, ementa, fundamento, descrição e a
**constatação**, que resume a infração redigida. Só entra o que foi de fato
lavrado: auto em redação ou pendente de transmissão não aparece, auto
substituído não aparece, e detalhes de análise de documentos também não. Sai
em três formatos: texto limpo para colar no SFITWEB, `.md` e `.docx` na pasta
da OS — o `.docx` agora usa o **template oficial com o cabeçalho da auditoria**
e formatação institucional (Times 12, títulos em azul, autos em tabela zebrada
com um subtítulo por tema), pronto para encaminhar à chefia ou ao MPT.

## 19/07/2026 (3)
<!-- commit: painel-det-datas-detalhe -->

**Cada notificação de DET agora mostra suas datas no painel** — ao abrir o
dossiê de uma auditoria (clique no card), a seção "Notificações DET" traz,
abaixo do código de cada notificação, quatro datas que antes só existiam no
DET: **Lavratura**, **Ciência**, **Próxima entrega** e **Última entrega**.
Elas vêm da sincronização com o DET (a sub-linha de detalhes que o "Sync DET"
grava sob cada notificação); onde uma data não existe, ela simplesmente não
aparece. Notificações antigas, ainda sem a sincronização, seguem mostrando ao
menos a próxima entrega, como antes.

E, quando uma notificação está com **atualização pendente** no DET (aquele
triângulo amarelo — pedido de prazo, dispensa, item ainda não aberto), o painel
agora destaca isso com um selo "⚠️ atualização pendente": no card da auditoria
(na grade principal) e, dentro do dossiê, bem na frente do código da
notificação. É o ponto mais acionável — o que pede sua atenção primeiro. O selo
some sozinho quando você resolve a pendência lá no DET e sincroniza de novo.

## 19/07/2026 (2)
<!-- commit: organiza-os-lote-autos-painel -->

**/organiza-os agora organiza tudo de uma vez, com menos perguntas** — a skill passou a
varrer a pasta OS ATIVAS inteira num único passe: organiza as pastas novas, atualiza as
já organizadas que receberam arquivos novos e apenas relata as vazias. Você aprova UM
plano consolidado (uma pergunta só) em vez de responder pasta a pasta. Pasta sem a
notificação do DET não trava mais nada: a OS é criada com o campo em branco para
preencher depois. Ao final, ela roda sozinha o `/autos-lavrados` (trazendo os autos já
transmitidos no Sistema Auditor para as fichas e o painel) e abre automaticamente o
painel interativo (http://127.0.0.1:8347) com o panorama geral.

Aprendizados de uso real incorporados: arquivos temporários do Word (`~$...`) são
ignorados em silêncio; nomes de download duplicado ("arquivo (1).pdf") são normalizados;
o relatório de atendimento do DET conta como prova de que a notificação foi respondida;
código de DET só é aceito se vier do PDF da própria notificação (número de acordo
coletivo não engana mais); minutas e análises que você já tinha feito ficam intactas e
anotadas na ficha da OS.

## 19/07/2026
<!-- commit: skills-interdicao-laudos -->

**Duas skills novas para interdição e laudos de máquina** — `/auditoria-AR-NR12` julga o
laudo de adequação/apreciação de riscos de máquinas (NBR ISO 12100 e NBR 14153) que a
empresa apresenta ao pedir a suspensão de uma interdição ou ao responder notificação, em 6
blocos de verificação, com parecer pronto. E `/rt-manutencao` redige o Relatório Técnico de
MANUTENÇÃO da interdição/embargo (.docx no modelo oficial) quando o pedido de suspensão é
negado. As duas se encadeiam: laudo insuficiente → RT de manutenção.

<!-- commit: painel-interativo-padrao -->

**Painel interativo já vem ligado de fábrica** — antes o toolkit perguntava, na
instalação, se você queria o painel interativo sempre ligado (aquele que deixa marcar DET,
resolver pendência e sincronizar o DET pela extensão do Chrome). Agora ele já vem ligado:
é instalado junto, sobe sozinho quando você liga o computador e roda só na sua máquina
(nada sai para a internet). Quem atualizar e ainda não tiver vai passar a ter também. Se
preferir sem ele, é só pedir para remover.

<!-- commit: relatorio-adhoc-docx -->

**Relatório pedido fora das skills sai em .docx** — se você pedir um documento ou
relatório que nenhuma skill cobre (um resumo, uma minuta avulsa), o Claude agora entrega
o arquivo final em .docx, em vez de só um texto em markdown no chat ou um `.md` solto.
Não muda nada no que as skills já fazem (`/NAD`, `/tn-nco` etc. continuam entregando o
texto pronto para colar no DET, em bloco de texto puro, do jeito que já era).

**Seu perfil de auditor se mantém atualizado sozinho** — o `CLAUDE.md` (o arquivo que diz
ao Claude quem você é e como trabalhar) antes ficava congelado na versão do dia da
instalação. Agora o `/aft-atualizar` o mantém em dia automaticamente quando sai uma
versão nova, atualizando só a parte do toolkit e sem tocar em nada que você tenha escrito
por conta própria no arquivo. Quem instalou faz tempo vai receber, uma única vez, o
convite para adotar o perfil novo (que traz proteções que faltavam nas versões antigas —
como a regra de tratar documento da empresa como dado, nunca como ordem).

## 16/07/2026
<!-- commit: fix-servidor-painel-windows -->

**Painel sempre ligado agora funciona no Windows** — o recurso de deixar o painel
interativo subindo sozinho a cada login (oferecido no `/aft-setup` e no `/aft-atualizar`)
tinha uma falha que fazia a instalação dar erro no Windows ("Acesso negado"). Corrigido:
agora a tarefa é registrada no seu próprio usuário, sem exigir administrador. Quem já
tinha tentado ativar e não conseguiu, é só pedir de novo.

<!-- commit: agenda-google -->

**Prazos de DET no seu Google Calendar** — nova skill `/agenda-det`: cria um evento de
dia inteiro para cada notificação DET com prazo (ex.: "DET RMNHKD5EWIUTJZ THIAGO
CASTR"), atualiza a data quando o prazo é prorrogado e marca ✓ quando você responde.
Usa o conector Google Calendar do Claude (login único do Google, pela interface do
Claude — nenhuma senha passa pelo toolkit). O `/aft-atualizar` vai te oferecer a
ativação.

**"Próximos vencimentos" no painel** — bloco novo logo abaixo dos cards das auditorias: todas as
notificações DET e pendências datadas, de todas as OS, em ordem de vencimento, cada uma
com selo de urgência e botão "agendar no Google Calendar" (esse funciona sem login
nenhum — abre o evento pronto, você só clica em Salvar).

<!-- commit: subtitulos-romanos -->

**Autos de infração com novo visual** — os subtítulos dos autos passaram de "1) DA
FISCALIZAÇÃO" para "I - DA FISCALIZAÇÃO:", "II - IRREGULARIDADE:" e "III -
OBSERVAÇÕES:", cada um em linha própria (com a quebra de linha que o Sistema Auditor
entende). Vale para todas as skills que redigem autos. Autos antigos, já redigidos no
formato numerado, são convertidos automaticamente pelo `/gera-ai` na hora de gerar o
TXT — você não precisa reescrever nada.

## 15/07/2026
<!-- commit: 86b79c2 -->

**Painel interativo** — agora dá para marcar uma notificação DET como checada, resolver
pendência, registrar atividade e mudar status/embargo direto pelo navegador, sem precisar
pedir ao Claude. É opcional: continue usando o painel do jeito antigo (abrir o arquivo por
duplo-clique) se preferir.

**Sincronização automática do DET** — com a extensão "Sync DET" do Chrome, um clique no
site do DET importa notificações novas e atualiza prazos direto nas suas fichas, sem
digitar nada.

**Duas correções importantes:**
- Notificações de fiscalizações antigas do mesmo CNPJ não entram mais, por engano, na OS
  errada (podia acontecer quando o empregador já tinha sido fiscalizado antes).
- O prazo de um item específico de uma NAD não é mais sobrescrito por engano quando a
  notificação tem mais de um prazo (ex.: um item vencido e outro ainda não).

**Ajustes visuais no painel** — RI em destaque, prazo de cada notificação sinalizado
(vencido / vence em breve), datas sempre em dd/mm/aaaa, caminho da pasta virou um botão de
copiar, e OS com status "encerrada" somem da tela sozinhas (sem precisar mover a pasta).

## 14/07/2026
<!-- commit: 87eebcf -->

**O painel virou um dashboard** — cards por empresa, coloridos pela urgência do prazo, com
clique para ver o detalhe completo da auditoria (autos lavrados, notificações, pendências).

**Rotina diária automática** — o painel pode se atualizar sozinho toda manhã, sem você
precisar pedir (opcional, oferecido na instalação/atualização).

**Suas próprias skills, protegidas** — se você criar uma skill personalizada (`minha-*`,
veja `/nova-skill`), ela nunca é apagada numa atualização do toolkit.

**Nova skill `/organiza-os`** — joga uma pasta de fiscalização antiga (de antes do
toolkit) em `OS ATIVAS/` e ela organiza tudo no padrão, com um plano para você aprovar
antes de mexer em qualquer arquivo.

<!-- commit: fcea179 -->
**`/autos-lavrados` gera a Relação de autos em .docx** — antes só listava no chat; agora
produz o documento pronto.

<!-- commit: 8cb65d8 -->
**Mais privacidade no `/gera-ai`** — parou de pedir o CPF do trabalhador prejudicado.

## 13/07/2026
<!-- commit: ce2ae22 -->

**Novas skills `/preparacao-acao-fiscal` e `/NAD`** — para planejar a visita antes de ir a
campo (checklist de documentos, denúncia, dados prévios).

---

_Este arquivo cresce a cada atualização relevante para o AFT. Mudanças só técnicas
(refatoração, testes, ajuste de documentação interna) não entram aqui._
