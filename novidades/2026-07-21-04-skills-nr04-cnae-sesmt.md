## 21/07/2026
<!-- commit: skills-nr04-cnae-sesmt -->

**Duas consultoras novas para a NR-04 (grau de risco e SESMT)** — chegaram duas
skills que respondem, com cálculo exato (nada "de cabeça"), as duas perguntas
clássicas do enquadramento da NR-04:

- **`/cnae-grau-risco-nr04`** diz o **grau de risco (1 a 4)** de uma atividade.
  Você informa o código CNAE em qualquer formato (`01.15-6`, `0115-6/00`,
  `1011201`) ou só descreve a atividade ("frigorífico", "construção de
  rodovias", "cultivo de soja") e ela responde consultando a base validada com
  os 673 códigos do Anexo I. Já lembra a regra do **maior grau de risco** entre
  a atividade principal e a preponderante (item 4.5.1) e emenda no cálculo do
  SESMT.

- **`/dimensionamento-sesmt-nr04`** calcula a **composição mínima do SESMT**
  (Anexo II) a partir do grau de risco e do número de trabalhadores: quantos
  técnicos, engenheiros, médicos etc., com o regime (integral/parcial), a regra
  para mais de 5.000 trabalhadores e as observações para estabelecimentos de
  saúde — sempre com a memória de cálculo. Serve também para **conferir, em
  fiscalização, se o SESMT constituído atende ao mínimo** (subdimensionamento).

As duas conversam entre si: informou o CNAE e o número de empregados, o Claude
enquadra o grau de risco e já dimensiona o SESMT na sequência.
