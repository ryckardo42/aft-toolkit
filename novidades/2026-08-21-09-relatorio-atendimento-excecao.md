## 21/08/2026
<!-- commit: relatorio-atendimento-excecao -->

**O Relatório de Atendimento baixado do DET lista o que NÃO foi entregue — e isso agora
está dito onde você vai ler.** Quando o `/aft-det-baixar` traz uma notificação, ele grava
o `relatorio-atendimento-<CODIGO>.pdf`, que é o documento oficial do Ministério do Trabalho
e Emprego sobre o atendimento daquela notificação. O detalhe que faltava estar escrito: ele
é um relatório de **exceção**. Lista os itens **não entregues**, e não os entregues. Isso
significa que, numa empresa que atendeu tudo, o PDF sai dizendo "não consta item para o
critério selecionado", com zero itens e zero arquivos — o que parece um download vazio ou
com defeito, mas é o contrário: é a **certidão oficial de que não há omissão**, prova
documental direta para o art. 630, § 4º, da CLT. Quem abrir o arquivo esperando o
inventário do que a empresa mandou vai entender exatamente ao contrário do que ele diz. O
inventário do que veio continua nas pastas `item<N>/` e no `historico-itens.md`. Nada mudou
no comportamento do download: só passou a estar documentado, no script e na skill, o que o
arquivo é e o que ele não é.
