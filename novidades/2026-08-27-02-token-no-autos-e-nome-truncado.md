## 27/08/2026
<!-- commit: token-autos-md-e-nome-truncado -->

**A revisão do auto reprovava exatamente o que as skills mandam escrever.** Antes de
empacotar o auto para o Sistema Auditor, o toolkit passa uma guarda que impede o nosso
ambiente de trabalho de vazar para dentro do documento legal — nome de arquivo interno,
pasta de trabalho, caminho do computador. Essa guarda também reprovava os apelidos de
trabalhador (`[[TRAB_01]]`) no rascunho do auto.

Só que o apelido ali é o certo, e é o que a `/aft-auditoria-geral` e a `/aft-gera-ai`
mandam usar: o nome real do trabalhador só entra no arquivo final, por substituição
automática, para não ficar circulando na conversa. Resultado: todo auto que citava um
trabalhador — praticamente todos — era reprovado, e não havia como consertar sem
desobedecer às outras skills.

Agora a guarda distingue os dois arquivos. No rascunho, o apelido é aceito. No arquivo
final que vai ao Sistema Auditor, continua reprovando — ali o apelido significaria que o
nome do trabalhador não chegou ao autuado, que é falha grave. Todo o resto da guarda segue
igual nos dois.

**Nome de trabalhador cortado não vira mais um segundo trabalhador.** Quando um nome é
informado pela metade — cortado por uma lista que só mostrava os primeiros caracteres, por
exemplo — o toolkit criava um apelido novo, em silêncio, para quem já tinha um. Dois
apelidos da mesma pessoa num auto sugerem dois prejudicados onde há um, e o erro só
apareceria depois da lavratura. Agora o toolkit recusa e avisa, mostrando os dois nomes
abreviados: se for a mesma pessoa, usa-se o apelido que já existe; se forem pessoas
diferentes, informa-se o nome completo de cada uma. Ele não escolhe sozinho de propósito —
pai e filho com o mesmo nome composto existem de verdade.

Achado e corrigido pelo colega Diego, rodando uma fiscalização de ponta a ponta.

---
