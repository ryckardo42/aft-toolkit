# NR-04 — Anexo II — Dimensionamento do SESMT
## Tabela de composição mínima do SESMT por grau de risco e número de trabalhadores, reestruturada para consulta e cálculo por sistemas de IA (RAG)

| Campo | Conteúdo |
|---|---|
| Tipo normativo | Anexo II da Norma Regulamentadora nº 4 (**NR-04**) — Serviços Especializados em Segurança e em Medicina do Trabalho (**SESMT**) |
| Órgão emissor | Ministério do Trabalho e Emprego (MTE) |
| Tema | Dimensionamento do SESMT: quantidade mínima de profissionais por estabelecimento |
| Variáveis de enquadramento | Grau de Risco (1 a 4, conforme CNAE — Anexo I da NR-04) × nº de trabalhadores do estabelecimento |
| Profissionais dimensionados | Técnico de Segurança do Trabalho; Engenheiro de Segurança do Trabalho; Auxiliar/Técnico de Enfermagem do Trabalho; Enfermeiro do Trabalho; Médico do Trabalho |
| Fonte | Versão oficial publicada (gov.br). Este conteúdo não substitui o publicado na versão certificada. |

---

## Contexto e finalidade

Este documento reproduz integralmente o **Anexo II da NR-04**, que define o dimensionamento mínimo do **SESMT**. Na fiscalização do trabalho, o AFT utiliza esta tabela para verificar se a organização constituiu o SESMT com a quantidade e os tipos de profissionais exigidos, cruzando o **grau de risco** da atividade (Anexo I da NR-04, por CNAE) com o **número de trabalhadores do estabelecimento**. A tabela original é matricial (faixas de trabalhadores em colunas) e frequentemente é lida de forma errada por sistemas automatizados; aqui ela foi **transposta** — cada faixa de trabalhadores é uma linha completa e autônoma — para eliminar erros de alinhamento de coluna.

---

## Algoritmo de enquadramento (procedimento de cálculo)

Para dimensionar o SESMT, siga exatamente estes passos:

1. Identifique o **grau de risco (GR)** da atividade: 1, 2, 3 ou 4 (Anexo I da NR-04, pelo CNAE; vincula-se ao maior grau de risco entre a atividade econômica principal e a preponderante no estabelecimento).
2. Identifique o **número total de trabalhadores (N)** do estabelecimento.
3. Se **N ≤ 5.000**: localize, na seção do GR correspondente, a **linha da faixa** que contém N. A composição indicada nessa linha é o dimensionamento completo. Não some faixas — as faixas **não são cumulativas** entre si.
4. Se **N > 5.000**: o dimensionamento é a **soma** de duas parcelas:
   - a composição integral da faixa **3.501 a 5.000**; MAIS
   - a composição da coluna "grupo de 4.000 ou fração acima de 2.000", **multiplicada pelo número de grupos** calculado sobre o excedente E = N − 5.000, assim: cada 4.000 trabalhadores do excedente forma 1 grupo; a fração restante só conta como grupo adicional se for **superior a 2.000**.
5. Aplique as regras dos marcadores da tabela:
   - **(*)** = profissional em **tempo parcial** (mínimo de três horas). Célula sem asterisco = tempo integral.
   - **(***)** = o empregador **pode optar** por contratar um enfermeiro do trabalho em tempo parcial **em substituição** ao auxiliar ou técnico de enfermagem do trabalho.
6. Se a célula estiver marcada como **0**, o profissional **não é exigido** naquela faixa.
7. Verifique as **Observações A e B** (ao final) para hospitais e estabelecimentos de saúde.

> **Regra crítica:** para N ≤ 5.000, usa-se **apenas a linha da faixa exata** onde N se encontra. O erro mais comum é deslocar a leitura em uma coluna (uma faixa para mais ou para menos) — por isso este documento lista cada faixa como linha completa.

---

## Grau de Risco 1 — Dimensionamento por faixa de trabalhadores

Cada linha abaixo é a composição **completa e final** do SESMT para a faixa indicada (GR 1). "0" = profissional não exigido. "(parcial)" = tempo parcial, mínimo de 3 horas.

| Faixa de trabalhadores | Técnico Seg. Trab. | Engenheiro Seg. Trab. | Aux./Téc. Enferm. Trab. | Enfermeiro Trab. | Médico Trab. |
|---|---|---|---|---|---|
| 50 a 100 | 0 | 0 | 0 | 0 | 0 |
| 101 a 250 | 0 | 0 | 0 | 0 | 0 |
| 251 a 500 | 0 | 0 | 0 | 0 | 0 |
| 501 a 1.000 | 1 | 0 | 0 | 0 | 0 |
| 1.001 a 2.000 | 1 | 0 | 0 | 0 | 1 (parcial) |
| 2.001 a 3.500 | 1 | 1 (parcial) | 1 (***) | 0 | 1 (parcial) |
| 3.501 a 5.000 | 2 | 1 | 1 | 1 (parcial) | 1 |
| Cada grupo de 4.000 ou fração acima de 2.000 (para N > 5.000, somar à faixa 3.501–5.000) | +1 | +1 (parcial) | +1 | 0 | +1 (parcial) |

Resumo GR 1: o SESMT só passa a ser exigido a partir de **501 trabalhadores**.

---

## Grau de Risco 2 — Dimensionamento por faixa de trabalhadores

Cada linha abaixo é a composição **completa e final** do SESMT para a faixa indicada (GR 2).

| Faixa de trabalhadores | Técnico Seg. Trab. | Engenheiro Seg. Trab. | Aux./Téc. Enferm. Trab. | Enfermeiro Trab. | Médico Trab. |
|---|---|---|---|---|---|
| 50 a 100 | 0 | 0 | 0 | 0 | 0 |
| 101 a 250 | 0 | 0 | 0 | 0 | 0 |
| 251 a 500 | 0 | 0 | 0 | 0 | 0 |
| 501 a 1.000 | 1 | 0 | 0 | 0 | 0 |
| 1.001 a 2.000 | 1 | 1 (parcial) | 1 (***) | 0 | 1 (parcial) |
| 2.001 a 3.500 | 2 | 1 | 1 (***) | 0 | 1 |
| 3.501 a 5.000 | 5 | 1 | 1 | 1 | 1 |
| Cada grupo de 4.000 ou fração acima de 2.000 (para N > 5.000, somar à faixa 3.501–5.000) | +1 | +1 (parcial) | +1 | 0 | +1 |

Resumo GR 2: o SESMT só passa a ser exigido a partir de **501 trabalhadores**; o Enfermeiro do Trabalho só é exigido na faixa de 3.501 a 5.000.

---

## Grau de Risco 3 — Dimensionamento por faixa de trabalhadores

Cada linha abaixo é a composição **completa e final** do SESMT para a faixa indicada (GR 3).

| Faixa de trabalhadores | Técnico Seg. Trab. | Engenheiro Seg. Trab. | Aux./Téc. Enferm. Trab. | Enfermeiro Trab. | Médico Trab. |
|---|---|---|---|---|---|
| 50 a 100 | 0 | 0 | 0 | 0 | 0 |
| 101 a 250 | 1 | 0 | 0 | 0 | 0 |
| 251 a 500 | 2 | 0 | 0 | 0 | 0 |
| 501 a 1.000 | 3 | 1 (parcial) | 0 | 0 | 1 (parcial) |
| 1.001 a 2.000 | 4 | 1 | 1 (***) | 0 | 1 |
| 2.001 a 3.500 | 6 | 1 | 1 | 1 | 1 |
| 3.501 a 5.000 | 8 | 2 | 1 | 1 | 2 |
| Cada grupo de 4.000 ou fração acima de 2.000 (para N > 5.000, somar à faixa 3.501–5.000) | +3 | +1 | +1 | 0 | +1 |

Resumo GR 3: o SESMT passa a ser exigido a partir de **101 trabalhadores** (1 Técnico de Segurança do Trabalho).

---

## Grau de Risco 4 — Dimensionamento por faixa de trabalhadores

Cada linha abaixo é a composição **completa e final** do SESMT para a faixa indicada (GR 4).

| Faixa de trabalhadores | Técnico Seg. Trab. | Engenheiro Seg. Trab. | Aux./Téc. Enferm. Trab. | Enfermeiro Trab. | Médico Trab. |
|---|---|---|---|---|---|
| 50 a 100 | 1 | 0 | 0 | 0 | 0 |
| 101 a 250 | 2 | 1 (parcial) | 0 | 0 | 1 (parcial) |
| 251 a 500 | 3 | 1 (parcial) | 0 | 0 | 1 (parcial) |
| 501 a 1.000 | 4 | 1 | 1 (***) | 0 | 1 |
| 1.001 a 2.000 | 5 | 1 | 1 (***) | 0 | 1 |
| 2.001 a 3.500 | 8 | 2 | 1 | 1 | 2 |
| 3.501 a 5.000 | 10 | 3 | 1 | 1 | 3 |
| Cada grupo de 4.000 ou fração acima de 2.000 (para N > 5.000, somar à faixa 3.501–5.000) | +3 | +1 | +1 | 0 | +1 |

Resumo GR 4: o SESMT passa a ser exigido a partir de **50 trabalhadores** (1 Técnico de Segurança do Trabalho).

---

## Legenda dos marcadores da tabela original

- **(*) Tempo parcial** — profissional com dedicação mínima de três horas. Neste documento, indicado como "(parcial)". Células sem essa indicação correspondem a tempo integral. Conforme o item 4.3.7 da NR-04, engenheiro de segurança do trabalho, médico do trabalho e enfermeiro do trabalho dedicam no mínimo 15 horas semanais (tempo parcial) ou 30 horas semanais (tempo integral).
- **(**) Regra para mais de 5.000 trabalhadores** — o dimensionamento total deverá ser feito levando-se em consideração o dimensionamento da faixa de 3.501 a 5.000, **acrescido** do dimensionamento do(s) grupo(s) de 4.000 ou fração acima de 2.000.
- **(***) Opção de substituição** — o empregador pode optar pela contratação de um **enfermeiro do trabalho em tempo parcial**, em substituição ao auxiliar ou técnico de enfermagem do trabalho. Neste documento, indicado como "(***)" ao lado do quantitativo de Aux./Téc. de Enfermagem.

## Observações do Anexo II (estabelecimentos de saúde)

- **Observação A:** hospitais, ambulatórios, maternidades, casas de saúde e repouso, clínicas e estabelecimentos similares deverão contratar um **enfermeiro do trabalho em tempo integral** quando possuírem **mais de quinhentos trabalhadores**.
- **Observação B:** em virtude das características das atribuições do SESMT, **não** se faz necessária a supervisão do técnico de enfermagem do trabalho por enfermeiro do trabalho, **salvo** quando a atividade for executada em hospitais, ambulatórios, maternidades, casas de saúde e repouso, clínicas e estabelecimentos similares.

---

## Exemplos resolvidos (casos de verificação)

### Exemplo 1 — GR 3, 770 trabalhadores

Faixa aplicável: **501 a 1.000** (linha única, não cumulativa). Dimensionamento:

- (3) Técnico de Segurança do Trabalho;
- (1) Engenheiro de Segurança do Trabalho, em tempo parcial (mínimo de 3 horas);
- (0) Auxiliar/Técnico de Enfermagem do Trabalho;
- (0) Enfermeiro do Trabalho;
- (1) Médico do Trabalho, em tempo parcial (mínimo de 3 horas).

### Exemplo 2 — GR 2, 2.001 trabalhadores

Faixa aplicável: **2.001 a 3.500** (2.001 é o primeiro valor desta faixa — atenção para não usar a faixa seguinte). Dimensionamento:

- (2) Técnico de Segurança do Trabalho;
- (1) Engenheiro de Segurança do Trabalho, em tempo integral;
- (1) Auxiliar/Técnico de Enfermagem do Trabalho (com a opção *** de substituição por enfermeiro do trabalho em tempo parcial);
- (0) Enfermeiro do Trabalho;
- (1) Médico do Trabalho, em tempo integral.

### Exemplo 3 — GR 3, 1.500 trabalhadores

Faixa aplicável: **1.001 a 2.000**. Dimensionamento:

- (4) Técnico de Segurança do Trabalho;
- (1) Engenheiro de Segurança do Trabalho, em tempo integral;
- (1) Auxiliar/Técnico de Enfermagem do Trabalho (com a opção *** de substituição por enfermeiro do trabalho em tempo parcial);
- (0) Enfermeiro do Trabalho;
- (1) Médico do Trabalho, em tempo integral.

### Exemplo 4 — GR 4, 12.000 trabalhadores (aplicação da regra **)

N = 12.000 > 5.000. Excedente E = 12.000 − 5.000 = 7.000. Grupos: 1 grupo completo de 4.000 + fração de 3.000 (superior a 2.000, portanto conta como grupo) = **2 grupos**.

Dimensionamento = faixa 3.501 a 5.000 do GR 4 **+ 2 ×** coluna de grupo do GR 4:

- Técnico de Segurança do Trabalho: 10 + (2 × 3) = **16**;
- Engenheiro de Segurança do Trabalho: 3 + (2 × 1) = **5**;
- Auxiliar/Técnico de Enfermagem do Trabalho: 1 + (2 × 1) = **3**;
- Enfermeiro do Trabalho: 1 + (2 × 0) = **1**;
- Médico do Trabalho: 3 + (2 × 1) = **5**.

---

## Erros comuns de leitura da tabela original (evitar)

- **Deslocamento de coluna:** na tabela matricial original, células vazias fazem leitores automáticos "puxarem" valores para a coluna errada, atribuindo à faixa N o quantitativo da faixa vizinha (ex.: atribuir os 5 Técnicos de GR 2/3.501–5.000 à faixa 2.001–3.500). Neste documento não há células vazias: toda ausência de exigência está grafada como **0**.
- **Somar faixas:** para N ≤ 5.000 as faixas **não são cumulativas** — usa-se apenas a linha da faixa exata. A única soma prevista é a da regra (**) para N > 5.000.
- **Ignorar os asteriscos:** o quantitativo pode estar correto e o enquadramento ainda assim errado se não se distinguir tempo parcial (*) de integral, ou se se ignorar a opção de substituição (***).
- **Confundir limites de faixa:** os limites são inclusivos — 2.001 pertence à faixa "2.001 a 3.500"; 2.000 pertence à faixa "1.001 a 2.000".

---

## Referências normativas

| Norma | Dispositivo | Conteúdo relevante |
|---|---|---|
| NR-04 | Anexo II | Tabela de dimensionamento do SESMT (grau de risco × nº de trabalhadores) |
| NR-04 | Anexo I | Enquadramento do grau de risco por CNAE |
| NR-04 | Item 4.3.7 | Carga horária mínima de engenheiro, médico e enfermeiro do trabalho (15h parcial / 30h integral semanais) |
