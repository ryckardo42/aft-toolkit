# Novidades do AFT Toolkit

Registro do que muda no toolkit a cada atualização — escrito para você, sem jargão de
programador. O `/aft-atualizar` mostra as entradas novas sempre que você atualiza; para
rever tudo, basta abrir este arquivo.

---

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
