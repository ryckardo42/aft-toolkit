## 22/08/2026
<!-- commit: det-opcoes-dependencia -->

**O toolkit aprendeu as regras da tela do DET — e parou de montar item que o
site não deixaria você criar.** As opções de "Retorno Solicitado" não são as
mesmas sempre: elas mudam conforme o tipo do item. **Solicitação de Documento**
só aceita Digital ou Impresso. **Orientação** só aceita Sem Retorno. Só a
**Exigência do Cumprimento de Obrigação** tem as quatro opções. O toolkit não
sabia disso e aceitava combinações impossíveis; agora ele conhece a tabela e a
respeita.

Três consequências que você vai sentir:

- **Item de Orientação nasce certo.** Se você marcar um item como orientação, o
  retorno vira Sem Retorno sozinho — mesmo que o padrão da notificação seja
  digital —, e o item deixa de ter prazo, porque orientação sem retorno é
  verificada em fiscalização futura.
- **Tipos de arquivo só onde fazem sentido.** O DET só aceita anexo na entrega
  **Digital**. Em Impresso, Vistoria in loco ou Sem Retorno, o site descarta a
  seleção — então o toolkit também deixou de mandá-la.
- **Sem Retorno não leva mais prazo**, que é como o próprio site se comporta.

Tudo isso ficou registrado num arquivo de referência com **todas as opções do
DET** e os textos de ajuda do próprio sistema (por exemplo: "Sem Retorno — o
item notificado será inspecionado em fiscalização futura"). É de lá que a skill
tira o que oferecer a você, e é de lá que a conferência tira o que barrar. Se um
dia o DET mudar essa tela, é um arquivo só para atualizar.

---
