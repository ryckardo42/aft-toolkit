# NR-24 — parâmetros de dimensionamento (referência)

Texto de apoio da skill `aft-nr24-dimensionamento`. Base: **NR-24, redação da
Portaria SEPRT nº 1.066, de 23/09/2019** (texto atualizado 2022), consultada no
repositório de NRs vigentes do MTE.

> **Toda fração arredonda para cima.** Onde a norma diz "para cada grupo de N
> trabalhadores **ou fração**", 132/20 = 6,6 vira **7** — nunca 6, nunca 6,6.

---

## 24.1.1 — a base de cálculo

> "Esta norma estabelece as condições mínimas de higiene e de conforto a serem
> observadas pelas organizações, devendo o dimensionamento de todas as
> instalações regulamentadas por esta NR ter como base o **número de
> trabalhadores usuários do turno com maior contingente**."

Consequência prática: o efetivo total do estabelecimento (o que a Relação de
Vínculos Ativos do SFIT traz) **não é** a base legal quando há mais de um turno —
é apenas o **teto**. Dimensionar pelo total superestima a exigência. Antes de
autuar, apure o contingente do maior turno no local.

---

## 24.2 — Instalações sanitárias

| Item | Regra | Fórmula |
|---|---|---|
| 24.2.1 | Todo estabelecimento deve ter instalação sanitária constituída por **bacia sanitária sifonada, dotada de assento com tampo, e por lavatório** | composição, não quantidade |
| 24.2.2 | **1 instalação sanitária para cada 20 trabalhadores ou fração, separadas por sexo** | `teto(H/20)` e `teto(M/20)` |
| 24.2.2.1 | **1 lavatório para cada 10 trabalhadores** nas atividades com exposição e manuseio de material infectante, substâncias tóxicas, irritantes, aerodispersóides **ou que provoquem a deposição de poeiras**, que impregnem a pele e roupas | `teto(N/10)` por sexo |

Atenção ao alcance do 24.2.2.1: ele abrange **as duas** famílias de exposição — a
dos agentes (infectante/tóxico/irritante/aerodispersóide) **e** a das poeiras que
impregnam. Já o item 24.3.5, dos chuveiros, separa as duas em alíneas com
proporções diferentes. É o erro clássico: tratar as duas hipóteses como uma só.

### 24.2.1.1 — mictórios

> "As instalações sanitárias masculinas devem ser dotadas de mictório, **exceto
> quando essencialmente de uso individual**, observando-se que:
> a) os estabelecimentos construídos **até 23/09/2019** devem possuir mictórios
> dimensionados de acordo com o previsto na NR-24, com redação dada pela Portaria
> MTb nº 3.214/1978.
> b) os estabelecimentos construídos **a partir de 24/09/2019** devem possuir
> mictórios na proporção de uma unidade para cada 20 (vinte) trabalhadores ou
> fração, **até 100** (cem) trabalhadores, e de uma unidade para cada 50
> (cinquenta) trabalhadores ou fração, **no que exceder**."

**Alínea b (regra vigente para construções novas)** — progressiva, em duas faixas:

```
H <= 100:  teto(H / 20)
H >  100:  5 + teto((H - 100) / 50)
```

Exemplo com 258 homens: 1ª faixa = 100/20 = **5**; 2ª faixa = 158/50 = 3,16 →
**4**; total **9 mictórios**. Erro comum: aplicar 1:50 sobre os 258 inteiros
(→ 6) em vez de só sobre o excedente.

**Alínea a (construído até 23/09/2019) — obrigação de existência, sem proporção.**

A remissão é à NR-24 na redação de 1978. Lendo o texto revogado inteiro, **não há
item que fixe proporção de mictórios por número de trabalhadores**. O que a redação
de 1978 tinha:

- **24.1.2** — "É considerada satisfatória a metragem de 1,00 m², para cada
  sanitário, por 20 (vinte) operários em atividade" (área, não contagem);
- **24.1.6 / 24.1.6.1** — material do mictório e equivalência da calha coletiva
  (cada 0,60 m = 1 mictório tipo cuba);
- **24.1.7** — 1 torneira de lavatório para cada 20 trabalhadores;
- **24.1.8** — 1 lavatório para cada 10 nas atividades insalubres;
- **24.1.12** — 1 chuveiro para cada 10 nas atividades insalubres;
- **24.1.14** — privadas e mictórios anexos às seções fabris são computados "para
  efeito das **proporções estabelecidas na presente Norma**" — a norma pressupunha
  proporções, mas o número de mictórios não aparece em item próprio.

Daí o script **não devolver quantidade** nesse caso. O que se exige, e o que se
autua, é o **caput** do item 24.2.1.1: a instalação sanitária masculina deve **ser
dotada de** mictório, salvo quando essencialmente de uso individual.

**Por que o mictório era obrigatório na redação antiga** (a controvérsia é real: no
grupo tripartite, a bancada patronal sustentava que a NR-24 anterior não o exigia
expressamente). A leitura registrada no material didático da ENIT é de que **sim,
era obrigatório**, e o fundamento é interno à própria norma: ela trazia **critério
de dimensionamento do mictório** — item 24.1.6.1, "no mictório do tipo calha, de uso
coletivo, cada segmento, no mínimo de 0,60 m, corresponderá a 1 mictório tipo cuba".
Não se dimensiona o que não é obrigatório. É esse o argumento a sustentar o auto.

> **Nunca apresente um "deveria ter N mictórios" para estabelecimento anterior a
> 24/09/2019** — nem por analogia com a regra nova (1:20 / 1:50), nem com o
> parâmetro de 1:30 que circula em material de apoio e **não existe no texto de
> 1978**. Número sem base normativa dentro de um auto de infração é o que derruba
> o auto. Autue a ausência.

**Antes de concluir pela ausência, converta a calha:** cada segmento de 0,60 m
(com anteparo) ou 0,80 m (sem anteparo) vale uma unidade. Uma calha corrida pode
ser o mictório que se procurava.

**Exceção do caput:** mictório é dispensado quando a instalação sanitária
masculina for **essencialmente de uso individual**. É fato a constatar em campo
(banheiro único, de uso individual), não presunção a partir do número de homens.

### 24.3.2 e 24.3.3 — equivalências que mudam a contagem em campo

- Mictório tipo **calha coletiva com anteparo**: cada segmento de **0,60 m** = 1
  unidade (24.3.2.1).
- Mictório tipo **calha coletiva sem anteparo**: cada segmento de **0,80 m** = 1
  unidade (24.3.2.2).
- **Lavatório** tipo calha ou tampo coletivo com várias cubas: cada segmento de
  **0,60 m** = 1 unidade (24.3.3).

Ao contar o que existe no estabelecimento, meça a calha e converta — não conte
"1 calha = 1 unidade".

---

## 24.3.5 — Chuveiros

> "Será exigido, para cada grupo de trabalhadores ou fração, 1 (um) chuveiro para
> cada:
> a) **10 (dez) trabalhadores**, nas atividades laborais em que haja exposição e
> manuseio de material infectante, substâncias tóxicas, irritantes ou
> aerodispersóides, que impregnem a pele e roupas do trabalhador;
> b) **20 (vinte) trabalhadores**, nas atividades laborais em que haja contato com
> substâncias que provoquem deposição de poeiras que impregnem a pele e as roupas
> do trabalhador, **ou que exijam esforço físico ou submetidas a condições
> ambientais de calor intenso**."

Fora dessas hipóteses, a NR-24 **não exige chuveiro** (mudança de 2019: o chuveiro
deixou de integrar o "conjunto" obrigatório). Isso não afasta exigência de outra
norma — NR-18 (construção), NR-31 (rural), NR-32 (saúde), NR-15 (insalubridade).

**24.3.5.1** — onde há exigência de chuveiro, ele deve **fazer parte ou estar
anexo ao vestiário**.

---

## 24.4 — Vestiários

**24.4.1 — quando é obrigatório:**
> "a) a atividade exija a utilização de vestimentas de trabalho ou que seja
> imposto o uso de uniforme cuja troca deva ser feita no próprio local de
> trabalho; **ou** b) a atividade exija que o estabelecimento disponibilize
> chuveiro."

**24.4.2 / 24.4.2.1 — área mínima:**

```
N <= 750:  área = N × (1,5 − N/1000)
N >  750:  área = N × 0,75
```

As duas regras se encontram em N = 750 (1,5 − 0,75 = 0,75 → 562,5 m²), então a
curva é contínua. A norma dimensiona pelo "número de trabalhadores que necessitam
utilizá-los": o script calcula **por sexo**, que é a leitura fiscal usual (o
vestiário separado por sexo era exigência expressa da redação de 1978 e segue
sendo a prática); se no caso concreto o vestiário for único e de uso alternado,
recalcule sobre o número real de usuários.

**Outros requisitos do vestiário (24.4.3, alíneas "a" a "d"):** conservação, limpeza
e higiene; piso e parede em material impermeável e lavável; ventilação para o
exterior ou exaustão forçada; assentos laváveis e impermeáveis em número compatível.

**Separação por sexo.** A NR-24 não a diz expressamente para o vestiário (só para a
instalação sanitária, no 24.2.2). O fundamento próprio é o **art. 389 da CLT**, que
obriga a instalação de vestiários com armários individuais privativos das mulheres.
Confirme a capitulação exata pela `/aft-consulta` antes de autuar por esse motivo.

**Chuveiro e vestiário andam juntos (24.3.5.1):** onde há exigência de chuveiro, ele
deve **fazer parte ou estar anexo ao vestiário**. Chuveiro em outro ponto do
estabelecimento não cumpre o item.

### Armários (24.4.3 "e" a 24.4.8)

| Regra | Item |
|---|---|
| Individuais, simples e/ou duplos, **com sistema de trancamento** | 24.4.3 "e" |
| **Uso rotativo** de armários simples é admitido — **exceto** para guarda de EPI e de vestimentas expostas a material infectante, substâncias tóxicas, irritantes ou que provoquem sujidade | 24.4.4 |
| Exposição a agentes **ou** a poeiras que impregnem: **compartimentos duplos ou dois armários simples**, para isolar roupa comum de roupa de trabalho | 24.4.5 |
| **Dispensa do duplo** quando a organização promove **higienização diária** das vestimentas ou fornece **vestimentas descartáveis** — assegurado 1 armário simples para a roupa comum de uso pessoal | **24.4.5.1** |
| Dimensões mínimas do **simples**: 0,40 m (altura) × 0,30 m (largura) × 0,40 m (profundidade) | 24.4.6 |
| Dimensões mínimas do **duplo**: 0,80 × 0,30 × 0,40 m com separação horizontal em 2 compartimentos de 0,40 m de altura; **ou** 0,80 × 0,50 × 0,40 m com divisão vertical em compartimentos de 0,25 m de largura, em isolamento rigoroso | 24.4.6.1 "a" e "b" |
| Empresa que oferece **serviço de guarda-volumes** para roupas e acessórios pessoais está **dispensada de fornecer armários** | **24.4.7** |
| Empresa **desobrigada de manter vestiário** deve garantir **escaninho, gaveta com tranca ou similar** para guarda individual dos pertences, ou serviço de guarda-volumes | **24.4.8** |

**Nenhuma das três dispensas se prova por declaração verbal.** Para a do 24.4.5.1,
exija contrato de lavanderia, registro de coleta e entrega ou nota da vestimenta
descartável; para a do 24.4.7, confirme que o guarda-volumes cobre roupas **e**
acessórios de todos os trabalhadores. E o 24.4.8 fecha o sistema: não há hipótese em
que o trabalhador fique sem lugar seguro para os pertences.

---

## 24.5 — Local para refeições

- **24.5.1** — obrigação de oferecer local em condições de conforto e higiene para
  as refeições nos intervalos.
- **24.5.1.1** — é permitido **dividir os trabalhadores do turno em grupos** para a
  tomada de refeições. Por isso o corte de 30 trabalhadores é o do grupo
  efetivamente **atendido de cada vez**, não necessariamente o do turno inteiro.
- **24.5.2** — local para **até 30** trabalhadores: destinado ou adaptado ao fim,
  arejado, conservado, com assentos e mesas/balcões suficientes. **24.5.2.1**: nas
  proximidades, meios de conservação e aquecimento das refeições, local e material
  para lavagem de utensílios e água potável.
- **24.5.3** — local para **mais de 30** trabalhadores: destinado a este fim e
  **fora da área de trabalho**, com os requisitos das alíneas "a" a "k" (piso e
  paredes laváveis e impermeáveis, circulação, ventilação, lavatórios próximos,
  mesas e assentos para todos, água potável, aquecimento das refeições, recipientes
  com tampa para descarte).

---

## 24.7 — Alojamento

| Parâmetro | Regra | Item |
|---|---|---|
| Capacidade do quarto | máximo **8 trabalhadores** | 24.7.3 "e" |
| Instalações sanitárias | **1 com chuveiro para cada 10 hospedados ou fração** | 24.7.2 "c" |
| Separação por sexo | dormitórios separados | 24.7.2 "d" |
| Área | **3,00 m² por cama simples** ou **4,50 m² por beliche**, incluídas circulação e armário | 24.7.3 "g" |
| Camas | vedado 3 ou mais na mesma vertical | 24.7.3 "a" |
| Armários | individuais, com trancamento, dimensionados para roupas, pertences e enxoval | 24.7.3 "f" e 24.7.3.2 |
| Colchões | certificados pelo INMETRO; roupa de cama limpa e adequada ao clima | 24.7.3 "b" e "c" |
| Pé-direito | mínimo **2,50 m**; **3,00 m** nos quartos com beliche (ausente código de obras local) | 24.9.7.1 |
| Sanitário externo ao dormitório | no máximo **50 m**, ligado por passagem com piso lavável e cobertura | 24.7.2.1 |

**Cuidado com a área:** a relação é **por leito**, e um beliche atende **2**
trabalhadores. Para 8 hospedados em beliche: 4 beliches × 4,50 = **18 m²** (e não
8 × 4,50). Em cama simples: 8 × 3,00 = **24 m²**.

---

## 24.9 — Disposições gerais que entram no dimensionamento

- **24.9.1** — água potável em todos os locais de trabalho; **proibido copo
  coletivo**.
- **24.9.1.1** — **1 bebedouro para cada 50 trabalhadores ou fração**, ou outro
  sistema que ofereça as mesmas condições.
- **24.9.1.2** — sem água corrente potável, fornecimento em recipientes portáteis
  próprios e hermeticamente fechados.

---

## NR-18, item 18.5 — canteiro de obras e frente de trabalho

Na **indústria da construção** (seção F do CNAE — divisões 41, 42 e 43 — e ainda
demolição, reparo, pintura, limpeza e manutenção de edifícios e de obras de
urbanização, item 18.2.1), quem dimensiona as áreas de vivência é a **NR-18**.

**18.5.1** — as áreas de vivência devem contemplar: **a)** instalação sanitária;
**b)** vestiário; **c)** local para refeição; **d)** alojamento, quando houver
trabalhador alojado. As quatro são obrigatórias no canteiro — **vestiário e local
para refeição não dependem de condição alguma**, ao contrário da NR-24 (24.4.1).

**18.5.2** — "As instalações da área de vivência devem atender, **no que for
cabível**, ao disposto na NR-24". É esta a chave de convivência entre as duas: a
NR-18 prevalece no que dispõe; a NR-24 preenche o resto (separação por sexo, área do
vestiário, armários, regime do local de refeições, dimensionamento do alojamento).

**18.5.3** — "A instalação sanitária deve ser constituída de **lavatório, bacia
sanitária sifonada, dotada de assento com tampo, e mictório**, na proporção de **1
conjunto para cada grupo de 20 trabalhadores ou fração**, bem como de **chuveiro**,
na proporção de **1 unidade para cada grupo de 10 trabalhadores ou fração**."

**18.5.5** — deslocamento do posto de trabalho até a instalação sanitária mais
próxima: **no máximo 150 m**.

**18.5.6** — água potável, filtrada e fresca, no canteiro, nas frentes de trabalho e
nos alojamentos, por bebedouro ou dispositivo equivalente, **1 para cada 25
trabalhadores ou fração**; vedado o copo coletivo. **18.5.6.1** — do posto de
trabalho ao bebedouro, no máximo **100 m no plano horizontal e 15 m no vertical**;
**18.5.6.2** — fora disso, água em recipientes portáteis herméticos nos postos.

**18.5.7 — frentes de trabalho** — devem ser disponibilizados: **a)** instalação
sanitária composta de **bacia sanitária sifonada, dotada de assento com tampo, e
lavatório para cada grupo de 20 trabalhadores ou fração**, podendo ser **banheiro
com tratamento químico** dotado de mecanismo de descarga ou de isolamento dos
dejetos, com respiro e ventilação, material para lavagem e enxugo das mãos (proibida
toalha coletiva) e higienização diária dos módulos; **b)** local para refeição com
conforto, higiene e proteção contra intempéries. **18.5.7.1** — admite convênio
formal com estabelecimento próximo, garantido o transporte dos trabalhadores.

### O que muda em relação à NR-24

| | NR-24 (geral) | NR-18 (canteiro) |
|---|---|---|
| Instalação sanitária | 1:20 | 1 **conjunto** :20 (bacia + lavatório + mictório) |
| Mictórios | progressivo 1:20 até 100, 1:50 no excedente; distinção por data de construção | **1 por conjunto masculino** (1:20), sem progressão e sem data |
| Chuveiros | só nas hipóteses do 24.3.5 | **1:10 sempre** |
| Bebedouros | 1:50 | **1:25** |
| Vestiário | condicionado (24.4.1) | **sempre** (18.5.1 "b") |
| Local para refeições | sempre | **sempre** (18.5.1 "c") |

**Onde a NR-24 ainda é mais rigorosa e prevalece por ser mais protetiva:** o
lavatório 1:10 do item 24.2.2.1, havendo exposição a material infectante,
substâncias tóxicas, irritantes, aerodispersóides ou poeiras que impregnem — a
NR-18 fixa só 1 lavatório por conjunto (1:20). O script aplica o mais rigoroso.

### Três armadilhas do modo obra

1. **Mictório no conjunto feminino.** O item 18.5.3 descreve o conjunto com
   mictório, mas o mictório é da instalação **masculina** (24.2.1.1). Conjunto
   feminino = bacia + lavatório.
2. **Separação por sexo.** Não está no 18.5.3 — vem do item **24.2.2** da NR-24,
   por remissão do 18.5.2. É esse o caminho da capitulação.
3. **Água quente.** A NR-18 vigente **não** exige água quente nos chuveiros do
   canteiro; a exigência era do item 18.4.2.7.1 da redação anterior, **revogada**.
   Não a leve ao auto pela NR-18.

O que fica **fora** deste script na NR-18: proteção contra quedas, andaimes,
elevadores, instalações elétricas, etapas de obra e capacitação — isso é
`/aft-NR18`.

---

## Anexos da NR-24 — proporções próprias

O script cobre o **corpo** da norma. Se o caso se enquadrar num Anexo, o Anexo
prevalece no que dispuser:

| Anexo | Alcance | Proporção própria |
|---|---|---|
| **I** | Shopping centers e similares | trabalhadores de lanchonetes, restaurantes e similares: vestiários e instalações sanitárias **com chuveiros**, 1 conjunto para cada **20** trabalhadores ou fração (item 4); **1 para cada 10** havendo exposição a material infectante, substâncias tóxicas, irritantes ou que provoquem sujidade (item 4.1). Demais lojistas podem usar as instalações e a praça de alimentação do shopping |
| **II** | Trabalho externo de prestação de serviços (executado no estabelecimento do cliente ou em logradouro público) — excluídas construção, leituristas, vendedores, entregadores, carteiros e similares e o que é regido pelo Anexo III | regras próprias de acesso a instalações sanitárias, alimentação e hidratação |
| **III** | Transporte público rodoviário coletivo de passageiros | em linhas sem ponto inicial/final em terminal: instalações sanitárias, local para refeição e hidratação a no máximo **250 m** a pé de um dos pontos; instalações compostas de bacia e lavatório na proporção de **1 para cada 20** trabalhadores ou fração, dispensada a separação por sexo para grupos de até 10, garantidas privacidade e higiene; admitido banheiro químico nas condições do item 4.1.2 |

---

## Códigos de ementa (mapa de busca, não capitulação)

Códigos que o AFT vinha usando na planilha própria de dimensionamento. Servem
para **localizar** a ementa no ementário; **a capitulação e a gradação vêm da
`/aft-consulta`**, nunca daqui.

| Código | Item | Assunto |
|---|---|---|
| 124250-4 | 24.2.1 | estabelecimento sem instalação sanitária / sem bacia sifonada com assento e tampo ou sem lavatório |
| 124251-2 | 24.2.1.1 | instalação sanitária masculina sem mictório ou fora da proporção |
| 124252-0 | 24.2.2 | instalação sanitária fora da proporção 1:20, separadas por sexo |
| 124253-9 | 24.2.2.1 | lavatório 1:10 nas atividades com exposição/manuseio |
| 124254-7 | 24.2.3 | características das instalações sanitárias |
| 124258-0 | 24.3.5 | chuveiro fora da proporção |
| 124260-1 | 24.4.1 | estabelecimento sem vestiário quando exigido |
| 124261-0 | 24.4.2 | vestiário fora do cálculo de área |
| 124264-4 | 24.4.5 | falta de armário duplo (ou dois simples) na exposição |
| 124265-2 | 24.4.6 | dimensões de armários fora do mínimo |
| 124267-9 | 24.5.1 | sem local em condições de conforto e higiene para refeições |
| 124268-7 | 24.5.2 | local de refeições fora das características |
| 124272-5 | 24.7.2 | dormitório do alojamento fora das características |
| 124273-3 | 24.7.3 | quarto do dormitório fora das características |
| 124285-7 | 24.9.1 | água potável / copo coletivo / bebedouros |

---

## Erros de cálculo mais comuns

1. **Somar homens + mulheres e dividir por 20.** O item 24.2.2 exige separação por
   sexo: 258 + 132 = 390/20 = 20 dá menos do que 13 + 7 = 20 por acaso, mas em
   outros números a conta muda (ex.: 25 H e 25 M → 2 + 2 = 4, e não 3).
2. **Arredondar para baixo ou deixar decimal.** "Ou fração" sempre sobe.
3. **Aplicar 1:50 sobre o total de homens** no cálculo de mictórios pós-2019, em
   vez de só sobre o que excede 100.
4. **Usar o efetivo total do estabelecimento** onde a norma manda usar o turno com
   maior contingente (24.1.1).
5. **Tratar poeira e agentes como a mesma hipótese.** Para lavatório (24.2.2.1) são
   equivalentes (1:10); para chuveiro (24.3.5) não são: agentes = 1:10, poeira =
   1:20.
6. **Contar calha coletiva como uma unidade** em vez de converter por segmento
   (0,60 m / 0,80 m).
7. **Multiplicar 4,50 m² pelo número de trabalhadores alojados em beliche** — a
   relação é por beliche, que atende 2.
8. **Exigir quantidade de mictórios em estabelecimento anterior a 24/09/2019** —
   por analogia com a regra nova ou com o parâmetro de 1:30, que não existe no
   texto de 1978. Ali só a ausência é autuável (ver 24.2.1.1 acima).
