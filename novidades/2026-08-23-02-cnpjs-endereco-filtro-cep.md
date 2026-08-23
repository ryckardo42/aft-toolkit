## 23/08/2026
<!-- commit: cnpjs-endereco-filtro-cep -->

**Correção importante na busca de CNPJs por endereço: a lista podia vir errada sem
avisar.** Na descoberta por CEP da `/aft-cnpjs-endereco`, o assistente preenchia o
campo de CEP do site de consulta de um jeito que o site não reconhecia: o CEP
aparecia escrito na tela, mas a busca saía **sem filtro nenhum** e devolvia a base
inteira do país. O resultado era uma lista de vinte CNPJs e razões sociais reais, com
toda a cara de resposta legítima, mas de empresas sem nenhuma relação com o endereço
fiscalizado — e nada na tela indicava o erro. Agora o CEP é digitado com teclado de
verdade, que o site aceita, e a habilidade passou a **conferir o resultado antes de
usá-lo**: contagem na casa dos milhões significa filtro não aplicado, e a lista é
descartada e a busca refeita, nunca repassada ao AFT. Descoberto pelo colega Diego
rodando a habilidade numa fiscalização real, no dia seguinte ao lançamento.

**E uma lição que ficou escrita na habilidade: CEP não é lote.** Em prédio ou
condomínio com CEP exclusivo, a busca por CEP isola o imóvel e funciona muito bem. Em
distrito industrial, bairro ou via longa, um único CEP cobre centenas de empresas —
no caso real foram 645 CNPJs no mesmo CEP, dos quais 170 ativos, e a listagem
gratuita mostra só 20 por página: nem a empresa da Ordem de Serviço nem a que se
procurava apareciam. Nesse cenário a habilidade agora diz com todas as letras que a
descoberta por CEP foi inconclusiva e parte para o cruzamento cadastral com os CNPJs
que o AFT já conhece — que, nesse mesmo caso, encontrou sócio em comum entre as duas
empresas, indício mais forte do que a simples proximidade física.

---
