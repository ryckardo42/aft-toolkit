## 15/08/2026
<!-- commit: nr24-saida-enxuta-e-vinculos-milhar -->

**A NR-24 na preparação ficou direta: só o que é devido.** Ao planejar a ação fiscal, o
dimensionamento das instalações sanitárias vinha com meia página de cenários hipotéticos
("se houver poeira...", "se houver calor...") e uma lista de conferência de vestiário que
empurrava os números para longe da vista. Agora, tanto na conversa quanto no
`preparacao.docx` que você leva impresso:

- **O quadro do que é devido vem primeiro e sozinho**: bacias, lavatórios, mictórios,
  chuveiros e bebedouros, com o item da norma ao lado — a régua para contar no percurso
  pelo estabelecimento. A memória de cálculo do mictório continua, porque é a conta que
  ninguém faz de cabeça.
- **Os quatro cenários de exposição viraram uma linha.** Antes da visita eles eram só
  hipótese; confirmando em campo poeira, agente químico, esforço ou calor, é só pedir o
  dimensionamento de novo com aquele cenário e o número sai exato, em vez de você
  escolher numa tabela.
- **O bloco de vestiário ficou nas medidas mínimas dos armários e na regra do
  trancamento.** As três dispensas que a empresa costuma invocar (higienização diária,
  guarda-volumes, escaninho) continuam na `/aft-nr24-dimensionamento`, que é onde se
  decide o enquadramento.

**Correção: empresa com mais de mil empregados ficava sem efetivo.** Ao ler a Relação de
Vínculos Ativos do SFIT, o toolkit ignorava o total quando ele vinha com ponto de milhar
("1.151") — justamente nas empresas grandes, onde o dimensionamento de SESMT e CIPA mais
pesa, o número aparecia vazio. Corrigido: agora o efetivo é lido normalmente. Se a lista
nominal vier truncada pelo SFIT ("listagem limitada aos primeiros 200 trabalhadores"), o
aviso continua aparecendo para você confirmar em campo.
