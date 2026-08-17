---
name: aft-cnae-grau-risco-nr04
model: haiku
description: >
  Use quando o usuário quiser o grau de risco (GR) de uma atividade
  econômica conforme o Anexo I da NR-04. Acione com "grau de risco",
  "enquadramento CNAE", "qual o GR", "Anexo I da NR-04", ao informar um
  código CNAE em qualquer formato (01.15-6, 0115-6/00, 1011201), ou ao
  descrever a atividade ("frigorífico", "construção de rodovias", "cultivo
  de soja") — mesmo sem citar "CNAE" ou "NR-04". Também como etapa prévia do
  dimensionamento do SESMT. NUNCA responda de memória: use o script deste
  skill.
---

# Enquadramento CNAE → Grau de Risco — Anexo I da NR-04
**AFT Toolkit**

Skill para identificar o **grau de risco (GR, escala 1 a 4)** de uma atividade econômica,
conforme o **Anexo I da NR-04** (relação CNAE 2.0 × GR). O grau de risco é o primeiro dos
dois parâmetros do dimensionamento do SESMT — o segundo é o número de trabalhadores
(Anexo II, coberto pelo skill `aft-dimensionamento-sesmt-nr04`).

## Regra de ouro

**NUNCA informe grau de risco de memória.** Toda consulta DEVE usar o script:

```bash
# Por código CNAE (aceita qualquer formato: 01.15-6, 0115-6/00, 1011-2/01, 01156...)
python ~/.claude/skills/aft-cnae-grau-risco-nr04/scripts/enquadrar_cnae.py <cnae>

# Por descrição da atividade (busca textual, sem acentos, todas as palavras)
python ~/.claude/skills/aft-cnae-grau-risco-nr04/scripts/enquadrar_cnae.py --busca "termo"

# Saída estruturada
python ~/.claude/skills/aft-cnae-grau-risco-nr04/scripts/enquadrar_cnae.py <cnae> --json
```

> O `python` acima é o `python_path` do `aft-config.md` (nunca `python3` solto: no
> Windows costuma ser o atalho vazio da Microsoft Store). Se o interpretador falhar,
> tente outro, mas **nunca** responda sem rodar o script. O caminho é absoluto de
> propósito: funciona a partir de qualquer diretório de trabalho.

A base `scripts/cnae_gr.json` contém os **673 códigos** do Anexo I, validada
integralmente contra o PDF oficial (zero divergências). O Anexo I opera em nível de
**classe** (XX.XX-X); subclasses (XXXX-X/XX) são reduzidas automaticamente à classe.

## Fluxo de trabalho

1. **Se o usuário informou um código CNAE** (qualquer formato): rode o script com o
   código e apresente classe, denominação e GR.
2. **Se o usuário descreveu a atividade** sem código: rode `--busca` com 1–2 palavras
   distintivas da atividade (ex.: "abate", "rodovias", "soja"). Se vierem vários
   resultados, apresente os candidatos com código, denominação e GR e pergunte qual
   corresponde à atividade principal da empresa — não escolha sozinho quando houver
   ambiguidade material (GRs diferentes entre os candidatos).
3. **Sempre acrescente a regra do item 4.5.1 da NR-04**: para dimensionamento do SESMT,
   aplica-se o **maior grau de risco** entre a atividade econômica principal (CNPJ) e a
   atividade preponderante no estabelecimento (a que ocupa o maior número de
   trabalhadores). Se houver indício de que a preponderante difere da principal,
   enquadre as duas e use a de maior GR.
4. **Encadeamento com o SESMT**: se o usuário também informou (ou informar em seguida)
   o número de trabalhadores, passe o GR obtido ao skill
   `aft-dimensionamento-sesmt-nr04` para calcular a composição mínima do SESMT.
5. Para dúvidas conceituais ou navegação por seção/divisão da CNAE, consulte
   `references/anexo_i_cnae_gr.md` (tabela integral estruturada, com seções A–U).

## Formato padrão de resposta (consulta por código)

```
CNAE <classe> — <denominação>
Grau de Risco: <GR> (Anexo I da NR-04)
```

Seguido, quando pertinente, da regra do maior GR (item 4.5.1) e do encadeamento para o
dimensionamento do SESMT.

## Casos de verificação (script já validado contra eles)

| Entrada | Resultado esperado |
|---|---|
| `0115-6/00` (subclasse) | 01.15-6 — Cultivo de soja — GR 3 |
| `1011-2/01` (subclasse) | 10.11-2 — Abate de reses, exceto suínos — GR 3 |
| `42.11-1` | Construção de rodovias e ferrovias — GR 4 |
| `--busca "abate"` | 10.11-2 (GR 3) e 10.12-1 (GR 3) |
| `99.99-9` | Erro: classe não consta no Anexo I |

## Limitações

- A base reflete o Anexo I da NR-04 (CNAE 2.0), incluindo a alteração da Portaria SIT
  nº 128/2009 (23.42-7 → GR 3). A versão certificada publicada no DOU prevalece.
- O skill não consulta o CNPJ da empresa: o código ou a descrição da atividade devem
  ser informados pelo usuário ou obtidos de outra fonte.
- Grau de risco do Anexo I da NR-04 serve ao dimensionamento do SESMT — não confundir
  com o enquadramento de alíquotas RAT/FAP da Previdência.

## Diário de atividades (automático)

Ao concluir o trabalho desta skill numa OS, registre o dia trabalhado no diário —
sem perguntar nada ao AFT (o script deduplica por data+letra; repetir é inofensivo):

```bash
python ~/.claude/skills/_scripts/diario_registrar.py "<pasta da OS>" --tipos D --detalhe "via /aft-cnae-grau-risco-nr04"
```
