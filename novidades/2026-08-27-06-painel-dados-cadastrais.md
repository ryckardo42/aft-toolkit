## 27/08/2026
<!-- commit: painel-frontmatter-fallback -->

**O cartão do painel não perde mais o grau de risco, o CNAE e o nº de trabalhadores.**
A ficha de cada empresa (o memory.md) guarda esses dados em dois lugares: o cabeçalho
técnico que os programas leem e as linhas em negrito que você lê. Quando um deles era
preenchido sem o outro, o painel mostrava o cartão sem o dado — e, num caso pior, com
um texto sem sentido no lugar do grau de risco (defeito real, encontrado numa OS ativa:
o campo vazio fazia o painel ler a linha errada da ficha). Três consertos: o painel
agora encontra o dado onde ele estiver na ficha (se o cabeçalho técnico está vazio, ele
lê as linhas em negrito); campo vazio nunca mais vira texto sem sentido; e a habilidade
de grau de risco (/aft-cnae-grau-risco-nr04) passou a preencher os dois lugares da ficha
ao apurar o enquadramento de uma empresa com OS aberta. Nenhuma ficha sua precisa ser
corrigida à mão.

---
