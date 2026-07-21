---
name: dimensionamento-sesmt-nr04
description: >
  Use este skill SEMPRE que o usuário pedir para dimensionar, calcular, verificar ou
  conferir o SESMT de uma empresa ou estabelecimento (Anexo II da NR-04). Acione quando
  mencionar "dimensionamento do SESMT", "SESMT", "Anexo II da NR-04", "quantos técnicos
  de segurança", "quantos médicos do trabalho", "precisa de engenheiro de segurança?",
  "enquadramento NR-4", "composição do SESMT", ou informar um grau de risco e um número
  de empregados pedindo os profissionais exigidos — mesmo sem usar a palavra "SESMT".
  Também acione para verificar, em fiscalização, se o SESMT constituído atende ao mínimo
  legal (subdimensionamento). Calcula de forma determinística (script Python) a
  quantidade mínima de cada profissional, com regime (integral/parcial), regra para mais
  de 5.000 trabalhadores e Observações A/B para estabelecimentos de saúde. NUNCA leia a
  tabela matricial original do Anexo II — use o script deste skill.
---

# Dimensionamento do SESMT — Anexo II da NR-04
**AFT Toolkit**

Skill para cálculo do dimensionamento mínimo do **SESMT** (Serviços Especializados em
Segurança e em Medicina do Trabalho), conforme o **Anexo II da NR-04**, a partir de duas
variáveis: **grau de risco (1 a 4)** e **número de trabalhadores do estabelecimento**.

## Regra de ouro

**NUNCA calcule o dimensionamento "de cabeça" nem leia a tabela matricial original do
Anexo II.** A tabela original tem células vazias e colunas que induzem erro de
alinhamento. Todo cálculo DEVE ser feito pelo script determinístico:

```bash
python3 scripts/dimensionar_sesmt.py <grau_de_risco> <num_trabalhadores> [--saude] [--json]
```

- `<grau_de_risco>`: 1, 2, 3 ou 4 (conforme Anexo I da NR-04, pelo CNAE);
- `<num_trabalhadores>`: número total de trabalhadores do estabelecimento;
- `--saude`: incluir quando for hospital, ambulatório, maternidade, casa de saúde e
  repouso, clínica ou estabelecimento similar (aplica as Observações A e B do Anexo II);
- `--json`: saída apenas em JSON (para integração).

O script imprime a memória de cálculo (faixa aplicada, regra de grupos quando N > 5.000)
e o dimensionamento por profissional com regime de dedicação.

## Fluxo de trabalho

1. **Colete as duas variáveis.** Se o usuário informar o CNAE mas não o grau de risco,
   pergunte o grau de risco (o enquadramento CNAE → GR está no Anexo I da NR-04, que não
   faz parte deste skill). Se informar apenas a atividade, pergunte GR e número de
   trabalhadores. Pergunte também se o estabelecimento é da área de saúde quando houver
   indício (hospital, clínica etc.).
2. **Execute o script** com os parâmetros coletados.
3. **Apresente o resultado** no formato padrão abaixo, reproduzindo a memória de cálculo.
4. Para **verificação fiscal** (a empresa declarou X profissionais): execute o script,
   compare item a item com o quadro declarado e aponte explicitamente cada déficit
   (profissional, quantidade faltante e regime exigido).
5. Em caso de dúvida conceitual (faixas, asteriscos, regra de grupos, observações),
   consulte `references/tabela_anexo_ii.md` — tabela completa transposta, algoritmo,
   exemplos resolvidos e erros comuns de leitura.

## Formato padrão de resposta

```
Dimensionamento do SESMT — GR <X>, <N> trabalhadores (faixa <faixa>):
- (<q>) Técnico de Segurança do Trabalho — <regime>
- (<q>) Engenheiro de Segurança do Trabalho — <regime>
- (<q>) Auxiliar/Técnico de Enfermagem do Trabalho — <regime e opção *** se houver>
- (<q>) Enfermeiro do Trabalho — <regime>
- (<q>) Médico do Trabalho — <regime>
```

Profissionais com quantidade 0 devem aparecer como "não exigido" (não omitir a linha).
Quando N > 5.000, apresente também a memória de cálculo dos grupos (excedente, grupos
de 4.000, fração acima de 2.000).

## Regras normativas essenciais (resumo)

- As faixas **não são cumulativas**: para N ≤ 5.000 vale apenas a linha da faixa exata.
  Limites inclusivos: 2.000 pertence a "1.001 a 2.000"; 2.001 pertence a "2.001 a 3.500".
- **N > 5.000** (regra **): dimensionamento da faixa 3.501–5.000 **mais** o acréscimo da
  coluna de grupo multiplicado pelo número de grupos (cada 4.000 do excedente = 1 grupo;
  fração só conta se **superior** a 2.000).
- **Tempo parcial (*)**: mínimo de 3 horas; pelo item 4.3.7 da NR-04, engenheiro, médico
  e enfermeiro do trabalho dedicam 15h semanais (parcial) ou 30h semanais (integral).
- **Opção (***)**: o empregador pode substituir o auxiliar/técnico de enfermagem do
  trabalho por um enfermeiro do trabalho em tempo parcial.
- **Observação A**: estabelecimento de saúde com mais de 500 trabalhadores → enfermeiro
  do trabalho em **tempo integral**. **Observação B**: só em estabelecimento de saúde o
  técnico de enfermagem do trabalho exige supervisão por enfermeiro do trabalho.
- O dimensionamento vincula-se ao **maior grau de risco** entre a atividade econômica
  principal e a preponderante no estabelecimento.

## Casos de verificação (o script já foi validado contra eles)

| GR | N | Resultado esperado |
|---|---|---|
| 3 | 770 | (3) Técnico; (1) Engenheiro parcial; (1) Médico parcial |
| 3 | 1.500 | (4) Técnico; (1) Engenheiro integral; (1) Aux./Téc. (***); (1) Médico integral |
| 2 | 2.001 | (2) Técnico; (1) Engenheiro integral; (1) Aux./Téc. (***); (1) Médico integral |
| 4 | 12.000 | Faixa 3.501–5.000 + 2 grupos: (16) Técnico; (5) Engenheiro; (3) Aux./Téc.; (1) Enfermeiro; (5) Médico |
| 1 | 300 | Nenhum profissional exigido |

## Limitações

- Este skill **não** faz o enquadramento CNAE → grau de risco (Anexo I da NR-04): o GR
  deve ser informado pelo usuário ou obtido de outra fonte.
- Modalidades especiais (SESMT compartilhado, regionalizado, canteiros de obras,
  ME/EPP com somatório de metade dos trabalhadores) alteram a **base de cálculo de N**,
  não a tabela: defina N conforme o corpo da NR-04 antes de rodar o script.
- Saída informativa para apoio à fiscalização; a versão certificada da norma prevalece.
