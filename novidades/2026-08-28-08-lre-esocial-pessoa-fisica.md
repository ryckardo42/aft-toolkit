## 28/08/2026
<!-- commit: lre-esocial-pessoa-fisica -->

**A `/aft-lre-esocial` corrigida: agora funciona com empregador pessoa física, e ganhou
filtro por local de trabalho.** Numa OS de produtor rural ou empregador doméstico — que
não tem CNPJ, é registrado pelo próprio CPF — a skill vinha recusando o pedido, dizendo
que "o SISFGTS não gera o LRE por CAEPF". Estava errado: o SISFGTS indexa o eSocial de
pessoa física pelo CPF do empregador, do mesmo jeito que indexaria por um CNPJ. O bug
nunca tinha aparecido porque a skill nunca tinha sido testada com um caso desses. Agora
aceita o CPF nos três comandos (LRE, férias, folha), com o mesmo painel de sempre.

**E resolvemos um segundo problema que só aparece nesse cenário: várias propriedades no
mesmo CPF.** Produtor rural pessoa física costuma ter mais de um imóvel rural, cada um
com seu próprio trabalhador — mas todos caem no mesmo LRE, porque é o mesmo CPF. Num caso
real testado, 475 vínculos vieram misturados de 3 propriedades diferentes, sem nenhuma
forma de separar quem trabalha em qual. Uma lista desse tamanho, sem filtro, é
inutilizável para preparar uma ação fiscal.

O painel do LRE agora mostra, quando há mais de um local de trabalho declarado, um aviso
e um filtro dedicado. Para usar: se você já sabe o nome de um trabalhador daquela
propriedade (de uma visita anterior, de uma planilha que o empregador entregou), busque
por ele no painel, abra o detalhe do vínculo dele — o código do local aparece ali — e
escolha esse código no filtro. A lista fica só com quem trabalha naquela propriedade. Sem
um nome de partida, o painel mostra a contagem de vínculos por local, para você decidir a
partir do tamanho de cada propriedade ou de outra fonte. Empregador com um só
estabelecimento não vê nada disso — o filtro só aparece quando faz sentido.

---
