---
name: aft-nr24-dimensionamento
model: sonnet
effort: medium
description: >
  Use quando o AFT quiser dimensionar, calcular ou conferir as instalações
  exigidas pela NR-24 — instalações sanitárias (bacia sifonada + lavatório),
  mictórios, chuveiros, vestiários (área e armários), bebedouros, local para
  refeições e alojamento. Acione com "dimensionamento da NR-24", "NR-24",
  "quantos banheiros", "quantas bacias sanitárias", "quantos mictórios",
  "quantos lavatórios", "quantos chuveiros", "área do vestiário", "quantos
  armários", "quantos bebedouros", "dimensionar alojamento", "condições
  sanitárias e de conforto", ou ao informar quantos homens e quantas mulheres
  trabalham no estabelecimento pedindo o que a NR-24 exige — mesmo sem citar a
  norma. Cobre também as ÁREAS DE VIVÊNCIA de CANTEIRO DE OBRAS e de FRENTE DE
  TRABALHO pela NR-18 (item 18.5), setorial e prevalente: acione com "canteiro de
  obras", "área de vivência", "banheiros da obra", "frente de trabalho", "banheiro
  químico", "item 18.5.3", ou quando a fiscalizada for da construção (CNAE 41, 42
  ou 43, ou "SPE" no nome). Também para verificar, em fiscalização, se o que existe
  no local atende ao mínimo legal. NUNCA calcule de memória: use o script
  determinístico deste skill.
---

# Dimensionamento da NR-24 (e da NR-18 em obra)
**AFT Toolkit**

Skill para o cálculo das quantidades mínimas de instalações sanitárias e de conforto
a partir de duas variáveis: **número de homens** e **número de mulheres** do turno
com maior contingente — mais os fatos de campo que mudam a proporção (exposição a
agentes, poeira, uniforme, alojamento).

Duas normas, conforme o caso:

- **NR-24** (redação da Portaria SEPRT nº 1.066/2019) — regra geral;
- **NR-18, item 18.5** (áreas de vivência) — em **canteiro de obras** e **frente de
  trabalho**, onde a norma setorial prevalece. Ver a Regra de ouro nº 4.

## Regra de ouro nº 1 — sempre use o script

**NUNCA calcule "de cabeça".** As proporções da NR-24 têm três armadilhas que o
cálculo mental erra: o arredondamento **para cima** de toda fração, a regra
**progressiva** dos mictórios (1:20 até 100 e 1:50 só no excedente) e a separação
**por sexo**, que não é a divisão do total por 20.

```bash
python ~/.claude/skills/aft-nr24-dimensionamento/scripts/dimensionar_nr24.py \
  --homens <H> --mulheres <M> [opções]
```

| Opção | Quando usar | Efeito |
|---|---|---|
| `--construcao ate-23-09-2019` | estabelecimento construído **até 23/09/2019** | muda a regra dos mictórios (ver Regra de ouro nº 3) |
| `--agentes` | exposição e manuseio de material infectante, substâncias tóxicas, irritantes ou aerodispersóides | lavatório 1:10 · chuveiro 1:10 · armário duplo |
| `--poeira` | contato com substâncias que provocam deposição de poeiras que impregnam pele e roupas | lavatório 1:10 · chuveiro 1:20 · armário duplo |
| `--esforco-calor` | esforço físico intenso ou calor intenso | chuveiro 1:20 |
| `--uniforme` / `--sem-uniforme` | há (ou não) troca de vestimenta/uniforme no local | obrigatoriedade do vestiário |
| `--sanitario-individual` | a instalação sanitária masculina é **essencialmente de uso individual** | dispensa o mictório |
| `--higienizacao-diaria` | a organização higieniza as vestimentas diariamente ou fornece descartáveis | dispensa o armário **duplo**, mantido 1 simples (24.4.5.1) |
| `--guarda-volumes` | há serviço de guarda-volumes para roupas e acessórios | dispensa os armários (24.4.7) |
| `--alojados-h N --alojados-m N` | há alojamento | dimensiona o item 24.7 |
| `--beliche` | leito predominante é beliche | área e pé-direito do dormitório |
| `--obra` | **canteiro de obras** | troca a NR-24 pela NR-18 (ver Regra de ouro nº 4) |
| `--frente-trabalho` | **frente de trabalho** da construção | aplica o item 18.5.7 da NR-18 |
| `--json` | integração | saída só em JSON |

**Sem os flags de exposição, o script devolve o cenário base E o que cada hipótese
mudaria.** É esse o formato certo **antes da visita**, quando o AFT ainda não sabe
o que vai encontrar: ele leva impresso o "se houver poeira, os lavatórios passam de
7 para 14".

## Regra de ouro nº 2 — a base é o TURNO COM MAIOR CONTINGENTE

O item 24.1.1 manda dimensionar pelo **número de trabalhadores usuários do turno
com maior contingente** — não pelo efetivo total do estabelecimento.

Quando os números vierem da Relação de Vínculos Ativos do SFIT (efetivo total),
diga isso com todas as letras: o resultado é **teto**, não a exigência exata, se a
empresa trabalha em mais de um turno. Confirmar o maior turno é tarefa de campo. O
script já imprime esse aviso; **repasse-o**, não o engula.

## Regra de ouro nº 3 — mictório em estabelecimento anterior a 24/09/2019

A alínea "b" do item 24.2.1.1 (construção **a partir de 24/09/2019**) é regra
fechada e o script devolve um número.

A alínea "a" (construção **até 23/09/2019**) remete à NR-24 "com redação dada pela
Portaria MTb nº 3.214/1978" — e o texto revogado **não fixa proporção de mictórios
por número de trabalhadores**. Nesse caso o script **não devolve quantidade
nenhuma**: a exigência que se sustenta é a do **caput** do item 24.2.1.1 — a
instalação sanitária masculina deve **ser dotada de** mictório, salvo quando
essencialmente de uso individual.

> **Em estabelecimento anterior a 24/09/2019, autua-se a AUSÊNCIA de mictório, não
> a insuficiência de quantidade.** Não há proporção a confrontar. Nunca apresente
> ao AFT um "deveria ter N mictórios" nesse caso, nem por analogia com a regra nova
> ou com parâmetro de material didático: seria número sem base normativa dentro de
> um auto de infração.

Antes de concluir pela ausência, **converta a calha**: no mictório tipo calha
coletiva, cada segmento de 0,60 m (com anteparo) ou 0,80 m (sem anteparo) vale uma
unidade — critério que a norma de 1978 já trazia (item 24.1.6.1) e que a atual
manteve (24.3.2.1 e 24.3.2.2). É esse critério, aliás, que sustenta a
obrigatoriedade do mictório na redação antiga: não se dimensiona o que não é
exigido. Detalhe e fontes em `references/nr24_parametros.md`.

## Regra de ouro nº 4 — obra é NR-18, não NR-24

Em **canteiro de obras** e em **frente de trabalho** da construção, quem dimensiona
é a **NR-18** (item 18.5) — norma **setorial**, que prevalece sobre a NR-24 no que
dispõe. No que ela não dispõe, a NR-24 se aplica **por remissão expressa** do item
18.5.2 ("no que for cabível"). Rodar a NR-24 pura numa obra **subdimensiona**.

| | NR-24 (geral) | NR-18 (canteiro, item 18.5.3/18.5.6) |
|---|---|---|
| Instalação sanitária | 1:20, separada por sexo | 1 **conjunto** :20 — bacia sifonada com assento e tampo **+ lavatório + mictório** |
| Mictórios | progressivo 1:20 até 100, 1:50 no excedente; muda com a data de construção | **1 por conjunto masculino** (1:20). Sem regra progressiva, sem data de construção |
| Chuveiros | só nas hipóteses do 24.3.5 (1:10 ou 1:20) | **1:10 sempre** |
| Bebedouros | 1:50 | **1:25**, água potável, filtrada e fresca |
| Vestiário | só se houver uniforme ou chuveiro (24.4.1) | **sempre** (18.5.1 "b") |
| Local para refeições | sempre, com regime por faixa | **sempre** (18.5.1 "c"), regime pela NR-24 |

**Como identificar que é obra** (nesta ordem, e diga em que se baseou):

1. o AFT afirmar que é obra, canteiro ou frente de trabalho;
2. **CNAE da seção F** — divisões **41, 42 ou 43** (campo de aplicação do item 18.2.1);
3. **"SPE"** no nome do empregador (Sociedade de Propósito Específico) — na prática,
   sociedade constituída para tocar uma obra. Case por **palavra inteira**: "ESPECIAL"
   e "SPEED" não valem.

Sinal forte não é certeza: **declare a premissa** ("tratei como canteiro de obras
porque o CNAE é 4120-4/00") para o AFT corrigir numa frase. Também se aplica a
demolição, reparo, pintura, limpeza e manutenção de edifícios e de obras de
urbanização (item 18.2.1), mesmo sem CNAE de construção.

**Canteiro e frente de trabalho não são a mesma coisa.** A frente (18.5.7) exige
menos: bacia sifonada com assento e tampo + lavatório 1:20, **sem mictório e sem
chuveiro**, admitido banheiro químico com descarga ou isolamento dos dejetos,
respiro, ventilação, material para lavagem e enxugo das mãos e higienização diária.
Havendo as duas coisas na mesma fiscalização, rode as duas vezes.

> **Água quente não entra.** A NR-18 vigente (2022) **não** exige água quente nos
> chuveiros do canteiro — isso era do item 18.4.2.7.1 da redação anterior,
> revogada. Nunca leve essa exigência ao auto pela NR-18.

## Regra de ouro nº 5 — vestiário e armário se conferem, não se calculam

A quantidade de armários é trivial (1 por trabalhador usuário) e a área sai da
fórmula. O que reprova em campo é o resto do item 24.4, e o script devolve isso
como **lista de verificação**, não como número — reproduza-a inteira:

- **trancamento** em todos os armários (24.4.3 "e") — armário individual sem tranca
  não atende;
- **uso rotativo** de armário simples é admitido (24.4.4), **exceto** para EPI e
  vestimenta exposta a material infectante, substância tóxica, irritante ou que
  provoque sujidade. Pergunte a quem usa se o armário é dele ou roda por turno;
- **medidas mínimas** (24.4.6 e 24.4.6.1) — irregularidade frequente, só aparece
  com trena. O script imprime as três configurações admitidas;
- **chuveiro anexo ao vestiário** (24.3.5.1), quando houver exigência de chuveiro;
- **separação por sexo** — fundamento próprio no **art. 389 da CLT** (vestiários com
  armários individuais privativos das mulheres); confirme a capitulação pela
  `/aft-consulta`;
- demais requisitos do 24.4.3: piso e parede impermeáveis e laváveis, ventilação ou
  exaustão, assentos laváveis suficientes, conservação e higiene.

**As três dispensas que a empresa invoca** — e nenhuma se prova por declaração
verbal:

| Dispensa | Alcance | Item |
|---|---|---|
| Higienização diária das vestimentas ou vestimenta descartável | dispensa o armário **duplo**; permanece 1 simples para a roupa comum | 24.4.5.1 |
| Serviço de guarda-volumes | dispensa **os armários** | 24.4.7 |
| Estabelecimento desobrigado de vestiário | ainda deve ter **escaninho, gaveta com tranca ou similar**, ou guarda-volumes | 24.4.8 |

O 24.4.8 fecha o sistema: **não existe hipótese** em que o trabalhador fique sem
lugar seguro para guardar os pertences. Sem vestiário exigido, o script zera a
contagem de armários e devolve a obrigação do 24.4.8 no lugar.

## Fluxo de trabalho

1. **Colete homens e mulheres.** Se o AFT der só o total, peça a divisão por sexo:
   sem ela o item 24.2.2 não se aplica corretamente. Se houver Relação de Vínculos
   Ativos do SFIT, os números saem dela (ver "Uso dentro da preparação" abaixo).
1b. **Verifique se é obra** pelos sinais da Regra de ouro nº 4 (CNAE 41/42/43,
   "SPE" no nome, ou o AFT dizendo). Sendo, use `--obra` — ou `--frente-trabalho`,
   se o que se fiscaliza é a frente e não o canteiro.
2. **Pergunte só o que muda o cálculo**, numa rodada só, e apenas quando o AFT
   estiver conferindo o que existe (uso fiscal): data de construção, exposição a
   agentes ou poeira, esforço/calor, uniforme, alojamento. **Antes da visita, não
   pergunte nada disso** — rode sem os flags e entregue os cenários.
3. **Execute o script.**
4. **Apresente o resultado** no formato padrão abaixo, com a memória de cálculo.
5. **Verificação fiscal** (o AFT conta o que existe no local): confronte item a
   item e aponte cada déficit com a quantidade faltante. Antes de comparar, aplique
   as **equivalências de calha** (mictório coletivo: cada 0,60 m com anteparo ou
   0,80 m sem anteparo = 1 unidade; lavatório calha/tampo coletivo: cada 0,60 m =
   1 unidade — itens 24.3.2.1, 24.3.2.2 e 24.3.3). Contar "1 calha = 1 unidade"
   subdimensiona o que a empresa tem e gera falso déficit.
6. **Verifique se incide algum Anexo** (I: shopping center; II: trabalho externo;
   III: transporte público rodoviário) — têm proporções próprias, no
   `references/nr24_parametros.md`. O script cobre o corpo da norma.
7. Em dúvida conceitual, consulte `references/nr24_parametros.md` — texto dos
   itens, fórmulas, anexos, mapa de códigos de ementa e erros comuns.

## Formato padrão de resposta

```
NR-24 — <H> homens e <M> mulheres (turno com maior contingente):

Instalações sanitárias (bacia sifonada com assento e tampo + lavatório) — item 24.2.2
- Feminino: <M>/20 = <x,xx> -> (<n>) instalações
- Masculino: <H>/20 = <x,xx> -> (<n>) instalações

Mictórios (instalação sanitária masculina) — item 24.2.1.1
- <memória de cálculo das duas faixas>
- Total: (<n>) mictórios

Lavatórios: (<n>) feminino · (<n>) masculino — <regra aplicada>
Chuveiros: (<n>) feminino · (<n>) masculino — <regra aplicada, ou "não exigido">
Vestiário: <exigido/a verificar> — área mínima <x> m² (F) e <x> m² (M); <n> armários (F) e <n> (M), <tipo>
Bebedouros: (<n>) — item 24.9.1.1
Local para refeições: <item 24.5.2 ou 24.5.3>
```

Reproduza sempre a **memória de cálculo** (a divisão e o arredondamento) — é ela
que sustenta o auto e permite ao AFT conferir. Itens com quantidade 0 aparecem como
"não exigido", com o motivo; não omita a linha.

Havendo alojamento, acrescente o bloco do item 24.7 (quartos, sanitários com
chuveiro, armários, área e pé-direito).

## Uso dentro da preparação da ação fiscal

A `/aft-preparacao-acao-fiscal` chama esta skill na FASE 3.6, com os **homens e
mulheres que o `vinculos_ativos.py` extraiu da Relação de Vínculos Ativos** — é
exatamente a divisão por sexo que a NR-24 exige, e ela já vem pronta do SFIT.

Nesse uso:

- rode **sem os flags de exposição** e entregue o cenário base + os cenários
  condicionais: antes da visita ninguém sabe se há poeira ou troca de uniforme;
- deixe explícito que o número da Relação é o **efetivo total**, não o maior turno;
- o resultado vai para o `preparacao.docx`, que o AFT leva impresso — o documento
  vira a régua para contar bacias, mictórios e bebedouros no percurso pelo
  estabelecimento;
- **não registre déficit como constatação antes da visita.** É indício.

## Constatação de auditoria, não auto automático

Dimensionamento insuficiente apurado em campo **não vira auto na hora**: registre
em `## Anotações da auditoria` do `memory.md` da OS, com os números apurados (o que
é devido, o que existe, a diferença, o item da NR-24). Quem transforma em auto é a
`/aft-auditoria-geral`, e a ementa e a capitulação vêm da `/aft-consulta` — os
códigos do `references/nr24_parametros.md` servem só para **localizar** a ementa,
nunca como capitulação final.

## Casos de verificação (o script já foi validado contra eles)

| Entrada | Resultado esperado |
|---|---|
| 258 H, 132 M, pós-2019 | IS: 13 M / 7 F · mictórios: 5 + 4 = **9** · bebedouros: 8 |
| 800 H, pós-2019 | IS: 40 · mictórios: 5 + 14 = **19** · vestiário: 600,00 m² (regra dos 0,75 m²) |
| 749 / 750 / 751 usuários | vestiário: 562,50 / 562,50 / 563,25 m² (curva contínua em 750) |
| 45 H, 12 M, até 23/09/2019 | mictórios: **sem quantidade** — exigível apenas a existência, com alerta |
| 8 hospedados em beliche | 1 quarto · 1 sanitário com chuveiro · **18,00 m²** (4 beliches × 4,50), não 36 |
| 12 trabalhadores | local de refeições pelo item 24.5.2 (até 30) |
| 170 H, 10 M, `--obra` | conjuntos: 9 M / 1 F · mictórios: **9** · chuveiros: **17 M / 1 F** · bebedouros: **8** |
| 170 H, 10 M, `--frente-trabalho` | conjuntos (bacia + lavatório): 9 M / 1 F · mictórios: 0 · chuveiros: 0 · bebedouros: 8 |
| `--agentes --uniforme` | armários **duplos** (ou dois simples), 1 por trabalhador |
| `--agentes --uniforme --higienizacao-diaria` | volta a **1 armário simples**, com a exigência de prova da higienização |
| `--uniforme --guarda-volumes` | **0 armários** — dispensa do 24.4.7 |
| `--sem-uniforme` (sem chuveiro) | vestiário não exigido · **0 armários** · obrigação de escaninho/gaveta com tranca (24.4.8) |

## Limitações e distinções

- **Não confundir com o SESMT (`/aft-dimensionamento-sesmt-nr04`) nem com a CIPA
  (`/aft-cipa-nr05-dimensionamento`)**: aquelas dimensionam pessoas a partir do
  grau de risco; esta dimensiona **instalações físicas** a partir de homens e
  mulheres. A NR-24 não usa grau de risco.
- O script cobre o **corpo** da NR-24 e o **item 18.5** da NR-18. Os **Anexos I, II
  e III** da NR-24 têm proporções próprias e ficam na referência — identificados
  pelo AFT, não presumidos.
- No modo obra, o script dimensiona as **áreas de vivência** (item 18.5). O resto da
  NR-18 — proteção contra quedas, andaimes, elevadores, instalações elétricas,
  etapas de obra — está fora do escopo: é `/aft-NR18`.
- Requisitos **qualitativos** (revestimento, ventilação, portas, indevassabilidade,
  conservação, colchão certificado) não são dimensionamento: entram como itens de
  inspeção, e a referência lista os principais.
- A NR-24 não exigir chuveiro **não afasta** exigência de NR-18, NR-31, NR-32 ou
  NR-15 no mesmo local.
- Saída informativa para apoio à fiscalização; a versão certificada da norma
  prevalece.
