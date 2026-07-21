---
name: cipa-nr05-dimensionamento
description: >
  Use este skill SEMPRE que o usuário pedir para dimensionar, calcular, verificar ou
  conferir a composição da CIPA (Quadro I da NR-05). Acione quando mencionar
  "dimensionamento da CIPA", "CIPA", "Quadro I da NR-05", "quantos membros da CIPA",
  "quantos efetivos e suplentes", "composição da comissão", "membros eleitos e
  designados", ou informar um grau de risco e um número de empregados pedindo o
  quantitativo de cipeiros — mesmo sem citar "NR-05". Também acione para verificar, em
  fiscalização, se a CIPA constituída atende ao mínimo legal. Calcula de forma
  determinística (script Python) os efetivos e suplentes POR REPRESENTAÇÃO e o total
  paritário (dobro: metade eleita pelos empregados, metade designada pelo empregador),
  com a regra de grupos de 2.500 acima de 10.000 empregados. NUNCA leia a tabela
  matricial original do Quadro I nem calcule de memória — use o script deste skill.
---

# Dimensionamento da CIPA — Quadro I da NR-05
**AFT Toolkit**

Skill para cálculo da composição mínima da **CIPA** (Comissão Interna de Prevenção de
Acidentes e de Assédio), conforme o **Quadro I da NR-05**, a partir de duas variáveis:
**grau de risco (1 a 4)** e **número de empregados do estabelecimento**.

## Regra de ouro nº 1 — sempre use o script

**NUNCA calcule o dimensionamento "de cabeça" nem leia a tabela matricial original do
Quadro I.** A tabela original tem células vazias e colunas que induzem erro de
alinhamento. Todo cálculo DEVE ser feito pelo script determinístico:

```bash
python3 scripts/dimensionar_cipa.py <grau_de_risco> <num_empregados> [--json]
```

- `<grau_de_risco>`: 1, 2, 3 ou 4 (Anexo I da NR-04, pelo CNAE — o mesmo GR do SESMT);
- `<num_empregados>`: número de empregados do estabelecimento;
- `--json`: saída apenas em JSON (para integração).

## Regra de ouro nº 2 — o Quadro I é POR BANCADA, não o total da CIPA

Os números do Quadro I são o quantitativo exigido para **CADA UMA das duas
representações separadamente**: a dos **empregados** (membros eleitos) e a do
**empregador** (membros designados). Como a CIPA é **paritária**, o total real é o
**DOBRO** — tanto de efetivos quanto de suplentes.

- Total de efetivos = 2 × (efetivos do Quadro I);
- Total de suplentes = 2 × (suplentes do Quadro I).

Se o Quadro I indica 4 efetivos, a CIPA terá **8 efetivos no total** (4 eleitos + 4
designados). Responder apenas "4 efetivos" é o **erro mais grave** neste tema.

> **Obrigatório em toda resposta:** apresente os DOIS níveis — o quantitativo do Quadro I
> por bancada E o total paritário, discriminando eleitos e designados. O script já
> devolve ambos.

## Fluxo de trabalho

1. **Colete as duas variáveis.** Se o usuário informar o CNAE mas não o grau de risco,
   obtenha o GR pelo skill `cnae-grau-risco-nr04` (Anexo I da NR-04) antes de calcular.
2. **Execute o script** com os parâmetros coletados.
3. **Apresente o resultado** no formato padrão abaixo, com a memória de cálculo.
4. Para **verificação fiscal**, escolha o parâmetro de confronto conforme o documento
   analisado — ver a seção "Qual número comparar com qual documento" abaixo. Aponte
   explicitamente o déficit de efetivos e de suplentes, identificando a representação
   em que ocorre.
5. Em caso de dúvida conceitual (faixas, regra de grupos, paridade), consulte
   `references/quadro_i_cipa.md` — quadro completo transposto, algoritmo, exemplos
   resolvidos e erros comuns de leitura.

## Formato padrão de resposta

```
Dimensionamento da CIPA — GR <X>, <N> empregados (faixa <faixa>):

Quadro I (por representação): (<ef>) efetivos e (<su>) suplentes

Composição paritária total:
- Efetivos: <2×ef> — (<ef>) eleitos pelos empregados + (<ef>) designados pelo empregador
- Suplentes: <2×su> — (<su>) eleitos pelos empregados + (<su>) designados pelo empregador
```

Quando N > 10.000, apresente também a memória de cálculo dos grupos (excedente, número
de grupos de 2.500, acréscimo aplicado). Quando o resultado for 0/0, informe que o
Quadro I não exige dimensionamento de CIPA naquela combinação de GR e faixa.

## Qual número comparar com qual documento (verificação fiscal)

O quantitativo **por bancada** e o **total paritário** servem a conferências diferentes.
Comparar o documento errado com o número errado gera falso déficit ou falso regular.

| Documento analisado | O que ele contém | Comparar com |
|---|---|---|
| **Ata/edital/resultado da eleição da CIPA, cédulas, lista de votação** | Apenas os representantes **eleitos pelos empregados** | **Quadro I por bancada** (uso principal deste número) |
| Ato de designação/indicação do empregador | Apenas os representantes **designados** | **Quadro I por bancada** |
| Ata de instalação/posse, quadro de composição afixado, organograma da CIPA, registro no eSocial | Ambas as representações reunidas | **Total paritário** (dobro) |

> **Uso principal do `quadro_i_por_bancada`:** conferir a documentação do processo
> eleitoral — verificar se foi eleito o número de efetivos e de suplentes que o Quadro I
> exige. Documento de eleição traz **só a bancada dos empregados**; confrontá-lo com o
> total paritário acusaria, erradamente, déficit de metade dos membros numa CIPA regular.

Na conferência da eleição, verifique efetivos **e** suplentes separadamente: é comum a
eleição atender o número de efetivos e ficar aquém no de suplentes. Quando houver
déficit, identifique em qual representação ele ocorre — a responsabilidade e as
providências diferem conforme seja a bancada eleita (processo eleitoral) ou a designada
(ato do empregador).

## Regras normativas essenciais (resumo)

- As faixas **não são cumulativas**: para N ≤ 10.000 vale apenas a linha da faixa exata.
  Limites inclusivos: 2.500 pertence a "1001 a 2500"; 2.501 pertence a "2501 a 5000";
  10.000 pertence a "5001 a 10.000".
- **N > 10.000**: quantitativo da faixa 5.001–10.000 **mais** o acréscimo por grupo,
  sendo que **cada grupo de 2.500 ou fração** conta como 1 grupo.
- O grau de risco é o do **Anexo I da NR-04** (mesma fonte do SESMT), aplicando-se o
  maior GR entre a atividade econômica principal e a preponderante no estabelecimento.

## Casos de verificação (o script já foi validado contra eles)

| GR | N | Quadro I (por bancada) | Total paritário |
|---|---|---|---|
| 3 | 501 | (6) efetivos, (4) suplentes | 12 efetivos, 8 suplentes |
| 4 | 2.500 | (9) efetivos, (7) suplentes | 18 efetivos, 14 suplentes |
| 1 | 11.000 | (9) efetivos, (7) suplentes (8+1 / 6+1, 1 grupo) | 18 efetivos, 14 suplentes |
| 3 | 15.000 | (16) efetivos, (12) suplentes (12+4 / 8+4, 2 grupos) | 32 efetivos, 24 suplentes |
| 2 | 45 | (0) e (0) — sem exigência pelo Quadro I | — |

## Limitações e distinções

- **Não confundir com o SESMT**: o Quadro I da NR-05 (CIPA) e o Anexo II da NR-04
  (SESMT) usam o mesmo grau de risco, mas têm faixas, quantitativos e regras de
  acréscimo **completamente diferentes** (CIPA: grupos de 2.500 acima de 10.000;
  SESMT: grupos de 4.000 ou fração acima de 2.000, sobre a base de 5.000). Para o
  SESMT, use o skill `dimensionamento-sesmt-nr04`.
- Este skill cobre o **dimensionamento** (Quadro I). Regras de processo eleitoral,
  mandato, estabilidade, treinamento, dispensa de constituição, CIPA por
  estabelecimento/contratante e demais disposições do corpo da NR-05 estão fora do
  escopo do script.
- Saída informativa para apoio à fiscalização; a versão certificada da norma prevalece.
