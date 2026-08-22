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

---
