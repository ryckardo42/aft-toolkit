## 22/08/2026
<!-- commit: notebooks-cohort -->

**O ementário do NotebookLM ganhou uma segunda coleção — e o toolkit agora sabe
qual é a sua.** Cada notebook do NotebookLM aceita no máximo 1.000 leitores, e os
nossos bateram esse teto em 19/08/2026. Não havia como abrir vaga: o catálogo
inteiro foi duplicado. Quem se cadastrou de lá em diante recebe acesso às
**cópias** — o mesmo conteúdo, em endereços diferentes.

Para você isso tinha um efeito prático ruim: as habilidades que consultam o
ementário (`/aft-consulta`, `/aft-auditoria-geral`, `/aft-NR12`, `/aft-NR01`,
`/aft-NR18`, `/aft-NAD`, `/aft-tn-nco`, `/aft-gera-ai`, `/aft-embargo-interdicao`
e a análise de laudo da NR-12) carregavam o endereço dos notebooks originais.
Para um colega da segunda coleção, toda consulta de ementa responderia "não
encontrado" — e a habilidade cairia no modo sem ementário, sem nunca dizer por quê.

Agora existe **um só lugar no toolkit que sabe o endereço de cada notebook**, e é
ele que descobre a qual coleção a sua conta pertence — anotando a resposta na sua
configuração, uma vez. Você não faz nada. Ele tenta por dois caminhos: primeiro
olha os notebooks que você já abriu; se você acabou de se cadastrar e ainda não
abriu nenhum, pergunta direto ao Google qual dos dois endereços a sua conta
alcança. Se as duas tentativas falharem, a causa não é a coleção — é o login
vencido ou o acesso ainda não liberado, e o `/aft-notebooklm-login` diz qual dos
dois.

**Cinco notebooks não precisaram de cópia**, porque têm link público e não têm
teto de leitores: Interdições, Aprendizagem Profissional, FGTS Digital,
Protocolos de Segurança e PCD. Eles são os mesmos para todo mundo.

**Dois notebooks entraram no ementário:** LGPD e Normas ABNT/ISO. A `/aft-consulta`
já sabe quando puxá-los — proteção de dados na fiscalização e norma técnica citada
em laudo.

E o `/aft-notebooklm-login`, ao conferir o seu acesso, passou a olhar só os
notebooks que existem para a sua coleção. Antes ele testaria os endereços originais e
diria "sem acesso" a todos, para quem está na segunda — um susto sem motivo.

## E o "oi" de cada notebook deixou de ser lição de casa

Aproveitando a mexida, mudou também a parte mais chata da configuração. O Google
só põe um notebook do ementário na sua conta depois que **você conversa com o chat
dele uma vez** — abrir o link não basta. Até agora o toolkit te entregava, no dia
da instalação, uma lista de 13 links para você registrar de saída.

Isso estava errado por um motivo que ninguém tinha somado: **esse "oi" gasta uma
consulta**. A conta gratuita do NotebookLM dá por volta de **50 consultas por
dia**, e registrar 13 notebooks queima 13 delas antes de você fiscalizar qualquer
coisa. Nos 47, acabou o dia.

Agora são **dois** no começo — Ementário SST e Ementário Legislação, que respondem
à maior parte do enquadramento. Os outros 45 entram **na hora em que você precisar
deles**: quando uma habilidade for consultar a NR-12 e ela ainda não estiver na sua
conta, o assistente para e diz, em uma linha, com o link pronto — *"abra este link,
escreva oi no chat e me diga pronto"* — e repete a consulta sozinho. Uma
interrupção, uma consulta gasta, no momento em que ela serve para alguma coisa.
Quem fiscaliza máquina registra a NR-12 e nunca precisa da NR-32.

Se você preferir registrar tudo de uma vez — antes de uma viagem, por exemplo —, é
só pedir: a lista completa continua no `/aft-notebooklm-login`, agora com o aviso
da cota junto.

**O limite de 50 por dia entrou na documentação**, na ajuda sobre o NotebookLM. Ele
explica uma confusão comum: consulta de ementa que começa a falhar "sem motivo" no
fim de um dia pesado costuma ser a cota, não defeito do toolkit — no dia seguinte
volta ao normal.

**Um defeito achado no caminho:** a `/aft-analise-acidente` trazia o endereço do
notebook do Guia de Análise de Acidentes **escrito à mão dentro dela**. Para
qualquer colega da segunda coleção, aquela consulta falharia sempre. Agora ela
pergunta pelo nome, como as outras.

---
