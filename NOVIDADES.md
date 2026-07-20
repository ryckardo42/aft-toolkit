# Novidades do AFT Toolkit

Registro do que muda no toolkit a cada atualização — escrito para você, sem jargão de
programador. O `/aft-atualizar` mostra as entradas novas sempre que você atualiza; para
rever tudo, basta abrir este arquivo.

---

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
