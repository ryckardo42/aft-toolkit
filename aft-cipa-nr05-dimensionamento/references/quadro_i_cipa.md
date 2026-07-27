# NR-05 — Quadro I — Dimensionamento da CIPA
## Quantitativo de representantes efetivos e suplentes POR BANCADA (empregados e empregador), por grau de risco e número de empregados, reestruturado para consulta e cálculo por sistemas de IA (RAG)

| Campo | Conteúdo |
|---|---|
| Tipo normativo | Quadro I da Norma Regulamentadora nº 5 (**NR-05**) — Comissão Interna de Prevenção de Acidentes e de Assédio (**CIPA**) |
| Órgão emissor | Ministério do Trabalho e Emprego (MTE) |
| Tema | Dimensionamento da CIPA: número de integrantes efetivos e suplentes por representação |
| Variáveis de enquadramento | Grau de Risco (1 a 4) × nº de empregados no estabelecimento |
| Fonte do grau de risco | Conforme nota do próprio Quadro: relação CNAE 2.0 × GR da **NR-04** (nomenclatura atual: **Anexo I da NR-04**), a mesma usada para o dimensionamento do SESMT |
| Fonte | Versão oficial publicada (gov.br). Este conteúdo não substitui o publicado na versão certificada. |

---

## Contexto e finalidade

Este documento reproduz integralmente o **Quadro I da NR-05**, que define o dimensionamento da **CIPA**. Na fiscalização do trabalho, o AFT utiliza este quadro para verificar se o estabelecimento constituiu a CIPA com o número correto de integrantes, cruzando o **grau de risco** da atividade (Anexo I da NR-04, por CNAE) com o **número de empregados do estabelecimento**. A tabela original é matricial e frequentemente é lida de forma errada por sistemas automatizados; aqui ela foi **transposta** — cada faixa de empregados é uma linha completa e autônoma — para eliminar erros de alinhamento de coluna.

---

## ⚠ REGRA FUNDAMENTAL: o Quadro I indica o quantitativo POR REPRESENTAÇÃO, não o total da CIPA

**Os números do Quadro I NÃO representam o total de membros da CIPA.** Eles representam o quantitativo exigido para **CADA UMA das duas representações, separadamente**:

- a **representação dos empregados** (membros **eleitos** pelos empregados); e
- a **representação do empregador** (membros **designados/indicados** pelo empregador).

Como a CIPA é **paritária**, o total real de integrantes é o **DOBRO** do que consta no Quadro I — tanto para efetivos quanto para suplentes.

**Fórmula:**

- Total de efetivos da CIPA = 2 × (efetivos do Quadro I) → metade eleita pelos empregados, metade designada pelo empregador;
- Total de suplentes da CIPA = 2 × (suplentes do Quadro I) → mesma paridade.

**Exemplo da regra:** se o Quadro I estipula **4 efetivos**, a CIPA real e paritária terá **8 membros efetivos** no total (4 representantes eleitos pelos empregados + 4 representantes designados pelo empregador). O mesmo raciocínio de multiplicação por dois se aplica aos suplentes.

> **CRÍTICO para cálculo:** ao responder "quantos membros tem a CIPA", sempre apresente DOIS níveis: (1) o quantitativo do Quadro I por bancada; (2) o total paritário (dobro), discriminando eleitos e designados.

---

## Algoritmo de enquadramento (procedimento de cálculo)

1. Identifique o **grau de risco (GR)** da atividade: 1, 2, 3 ou 4 (Anexo I da NR-04, pelo CNAE).
2. Identifique o **número de empregados (N)** do estabelecimento.
3. Se **N ≤ 10.000**: localize, na seção do GR correspondente, a **linha da faixa** que contém N. Os valores dessa linha são os quantitativos **por bancada**. As faixas **não são cumulativas** — usa-se apenas a linha da faixa exata.
4. Se **N > 10.000**: o quantitativo por bancada é a **soma** de duas parcelas:
   - os valores da faixa **5001 a 10.000**; MAIS
   - o **acréscimo por grupo** (coluna "acima de 10.000, para cada grupo de 2.500 acrescentar"), multiplicado pelo número de grupos calculado sobre o excedente E = N − 10.000: **cada grupo de 2.500 (completo ou fração) conta como 1 grupo**.
5. Aplique a **regra da paridade**: multiplique por 2 os quantitativos obtidos para chegar ao total de efetivos e de suplentes da CIPA (metade eleita, metade designada).
6. Célula com **0** = não há exigência de integrante naquela faixa pelo Quadro I.

> **Limites inclusivos:** 500 pertence à faixa "301 a 500"; 501 pertence à faixa "501 a 1000"; 2.500 pertence à faixa "1001 a 2500"; 10.000 pertence à faixa "5001 a 10.000".

---

## Grau de Risco 1 — Quantitativos POR BANCADA, por faixa de empregados

Cada linha é o quantitativo **por representação** (empregados eleitos; e, em igual número, designados pelo empregador). Total da CIPA = 2 × valores da linha.

| Faixa de empregados | Efetivos (por bancada) | Suplentes (por bancada) |
|---|---|---|
| 0 a 19 | 0 | 0 |
| 20 a 29 | 0 | 0 |
| 30 a 50 | 0 | 0 |
| 51 a 80 | 0 | 0 |
| 81 a 100 | 1 | 1 |
| 101 a 120 | 1 | 1 |
| 121 a 140 | 1 | 1 |
| 141 a 300 | 1 | 1 |
| 301 a 500 | 2 | 2 |
| 501 a 1000 | 4 | 3 |
| 1001 a 2500 | 5 | 4 |
| 2501 a 5000 | 6 | 5 |
| 5001 a 10.000 | 8 | 6 |
| Acréscimo por grupo de 2.500 ou fração acima de 10.000 | +1 | +1 |

---

## Grau de Risco 2 — Quantitativos POR BANCADA, por faixa de empregados

| Faixa de empregados | Efetivos (por bancada) | Suplentes (por bancada) |
|---|---|---|
| 0 a 19 | 0 | 0 |
| 20 a 29 | 0 | 0 |
| 30 a 50 | 0 | 0 |
| 51 a 80 | 1 | 1 |
| 81 a 100 | 1 | 1 |
| 101 a 120 | 2 | 1 |
| 121 a 140 | 2 | 1 |
| 141 a 300 | 3 | 2 |
| 301 a 500 | 4 | 3 |
| 501 a 1000 | 5 | 4 |
| 1001 a 2500 | 6 | 5 |
| 2501 a 5000 | 8 | 6 |
| 5001 a 10.000 | 10 | 8 |
| Acréscimo por grupo de 2.500 ou fração acima de 10.000 | +1 | +1 |

---

## Grau de Risco 3 — Quantitativos POR BANCADA, por faixa de empregados

| Faixa de empregados | Efetivos (por bancada) | Suplentes (por bancada) |
|---|---|---|
| 0 a 19 | 0 | 0 |
| 20 a 29 | 1 | 1 |
| 30 a 50 | 1 | 1 |
| 51 a 80 | 2 | 1 |
| 81 a 100 | 2 | 1 |
| 101 a 120 | 2 | 1 |
| 121 a 140 | 3 | 2 |
| 141 a 300 | 4 | 2 |
| 301 a 500 | 5 | 4 |
| 501 a 1000 | 6 | 4 |
| 1001 a 2500 | 8 | 6 |
| 2501 a 5000 | 10 | 8 |
| 5001 a 10.000 | 12 | 8 |
| Acréscimo por grupo de 2.500 ou fração acima de 10.000 | +2 | +2 |

---

## Grau de Risco 4 — Quantitativos POR BANCADA, por faixa de empregados

| Faixa de empregados | Efetivos (por bancada) | Suplentes (por bancada) |
|---|---|---|
| 0 a 19 | 0 | 0 |
| 20 a 29 | 1 | 1 |
| 30 a 50 | 2 | 1 |
| 51 a 80 | 3 | 2 |
| 81 a 100 | 3 | 2 |
| 101 a 120 | 4 | 2 |
| 121 a 140 | 4 | 2 |
| 141 a 300 | 4 | 3 |
| 301 a 500 | 5 | 4 |
| 501 a 1000 | 6 | 5 |
| 1001 a 2500 | 9 | 7 |
| 2501 a 5000 | 11 | 8 |
| 5001 a 10.000 | 13 | 10 |
| Acréscimo por grupo de 2.500 ou fração acima de 10.000 | +2 | +2 |

---

## Exemplos resolvidos (casos de verificação)

### Exemplo 1 — GR 3, 501 empregados

Faixa aplicável: **501 a 1000** (linha única, não cumulativa). Quadro I (por bancada): **(6) efetivos** e **(4) suplentes**.

Composição paritária da CIPA:

- **Efetivos: 12 no total** — (6) eleitos pelos empregados + (6) designados pelo empregador;
- **Suplentes: 8 no total** — (4) eleitos pelos empregados + (4) designados pelo empregador.

### Exemplo 2 — GR 4, 2.500 empregados

Faixa aplicável: **1001 a 2500** (2.500 é o último valor desta faixa — atenção para não usar a faixa seguinte). Quadro I (por bancada): **(9) efetivos** e **(7) suplentes**.

Composição paritária da CIPA:

- **Efetivos: 18 no total** — (9) eleitos + (9) designados;
- **Suplentes: 14 no total** — (7) eleitos + (7) designados.

### Exemplo 3 — GR 1, 11.000 empregados (aplicação da regra de grupos)

N = 11.000 > 10.000. Excedente E = 11.000 − 10.000 = 1.000 → fração de um grupo de 2.500 → conta como **1 grupo**.

Quadro I (por bancada) = faixa 5001 a 10.000 do GR 1 **+ 1 ×** acréscimo por grupo:

- Efetivos: 8 + (1 × 1) = **(9) efetivos por bancada**;
- Suplentes: 6 + (1 × 1) = **(7) suplentes por bancada**.

Composição paritária da CIPA:

- **Efetivos: 18 no total** — (9) eleitos + (9) designados;
- **Suplentes: 14 no total** — (7) eleitos + (7) designados.

### Exemplo 4 — GR 2, 45 empregados

Faixa aplicável: **30 a 50**. Quadro I (por bancada): **0 efetivos e 0 suplentes** — não há exigência de dimensionamento de CIPA pelo Quadro I nessa combinação de GR e faixa.

---

## Erros comuns de leitura e de cálculo (evitar)

- **Tratar o Quadro I como total da CIPA:** este é o erro mais grave. Os valores são **por bancada**; o total paritário é sempre o dobro. Responder "a CIPA terá 6 efetivos" para o Exemplo 1 está **errado** — são 6 por representação, 12 no total.
- **Deslocamento de coluna:** na tabela matricial original, células vazias fazem leitores automáticos atribuírem à faixa N o valor da faixa vizinha. Neste documento não há células vazias: toda ausência de exigência está grafada como **0**.
- **Somar faixas:** para N ≤ 10.000 as faixas **não são cumulativas** — usa-se apenas a linha da faixa exata. A única soma prevista é a da regra de grupos para N > 10.000.
- **Confundir limites de faixa:** os limites são inclusivos — 2.500 pertence a "1001 a 2500"; 2.501 pertence a "2501 a 5000"; 10.000 pertence a "5001 a 10.000".
- **Confundir com o dimensionamento do SESMT:** o Quadro I da NR-05 (CIPA) e o Anexo II da NR-04 (SESMT) usam o **mesmo grau de risco** (Anexo I da NR-04), mas têm faixas de empregados, quantitativos e regras de acréscimo **completamente diferentes** (CIPA: grupos de 2.500 acima de 10.000; SESMT: grupos de 4.000 ou fração acima de 2.000, sobre a base de 5.000). Não misturar as duas tabelas.

---

## Referências normativas

| Norma | Dispositivo | Conteúdo relevante |
|---|---|---|
| NR-05 | Quadro I | Dimensionamento da CIPA (grau de risco × nº de empregados), por representação |
| NR-04 | Anexo I (referido no Quadro como "Quadro I da NR-04") | Relação CNAE 2.0 × grau de risco, usada como fonte do GR |
