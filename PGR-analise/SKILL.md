---
name: PGR-analise
description: >
  Use este skill SEMPRE que o Auditor-Fiscal do Trabalho (AFT) pedir para analisar, auditar,
  revisar ou avaliar um Programa de Gerenciamento de Riscos (PGR) à luz da NR-01. Acione
  quando o usuário mencionar "analisar PGR", "auditar PGR", "revisar PGR", "PGR da empresa",
  "PGR apresentado", "Inventário de Riscos", "Plano de Ação do PGR", "ementas do PGR",
  "1010590", "1010603", "1010611", "1010646", "1010743", "1010794", "1011154", ou anexar PDF
  de PGR/Inventário/Plano de Ação. Também acione quando o contexto envolver lavratura de
  autos de infração por irregularidades no PGR. O skill executa varredura sistemática das
  sete ementas de PGR, identifica irregularidades com citação dos trechos e páginas do
  documento, e oferece geração de autos de infração (formato 3 subtítulos, alinhado à
  skill irmã `inspecao-completa`) com empacotamento na pasta `~/Desktop/autos_<CNPJ>/`
  contendo TXT importável pelo Sistema Auditor (encoding latin-1) e o próprio PGR como
  anexo de cada AI (comprimido se necessário, limite 10 MB).
---

# Skill: Análise de PGR (NR-01)

## Objetivo

Analisar um Programa de Gerenciamento de Riscos (PGR) sob a ótica da NR-01, identificando
irregularidades enquadráveis em sete ementas de auto de infração. O resultado é uma análise
ementa por ementa, com citação dos trechos do PGR que sustentam cada conclusão, e a oferta
de geração de autos de infração e relatório de recomendação para a empresa.

---

## Fluxo de execução

### Etapa 1: Receber o PGR

O PGR pode chegar como PDF anexado ou como texto colado. Aceite os dois formatos.

- **PDF anexado**: leia o conteúdo integral usando as ferramentas de leitura de PDF
  disponíveis (consulte o skill `pdf-reading` se necessário). Localize as seções de
  metodologia, Inventário de Riscos, Plano de Ação e comunicação/consulta.
- **Texto colado**: trabalhe diretamente com o texto fornecido.
- **Nada fornecido**: solicite ao AFT o PGR (anexo ou texto).

Faça uma leitura inicial completa antes de começar a análise por ementa. Localize, na
medida do possível, as seções correspondentes a: metodologia de GRO, identificação de
perigos, avaliação de riscos, Inventário de Riscos, Plano de Ação, ergonomia (NR-17),
consulta/comunicação com trabalhadores.

### Etapa 2: Detectar gatilhos contextuais

**Gatilho de interdição (afeta a Ementa 1010603).**

Verifique se o AFT mencionou, em sua solicitação ou no contexto da conversa, qualquer
indício de interdição: "interdição de máquina", "termo de interdição lavrado", "máquina
interditada", "setor interditado", "risco grave e iminente", ou termos equivalentes.

Se detectar o gatilho, **pare antes de iniciar a Ementa 1010603 e confirme**:

> "Identifiquei menção de interdição no seu contexto. Confirma que houve interdição
> formal nesta fiscalização? Se sim, aplicarei a regra especial da Ementa 1010603, que
> conclui automaticamente pela infração com texto padronizado."

Só aplique a Regra Especial D.A (descrita abaixo) após confirmação explícita do AFT.

### Etapa 3: Análise sequencial por ementa

Execute a análise nas sete ementas, **na ordem listada**, apresentando a conclusão de
cada uma direto no chat antes de passar para a próxima. Para cada ementa, siga as
diretrizes específicas mais adiante neste skill.

Ordem fixa:

1. **1010590** - Não evitar/eliminar riscos na origem
2. **1010603** - Não identificar perigos corretamente
3. **1010611** - Não avaliar riscos ou indicar nível
4. **1010646** - Não considerar condições da NR-17 (ergonomia)
5. **1010743** - Plano de Ação ausente ou deficiente
6. **1010794** - Inventário de Riscos ausente ou em desacordo
7. **1011154** - Falha em consulta e comunicação com trabalhadores

### Etapa 4: Pós-análise

Após concluir as sete ementas, pergunte ao AFT se deseja:

1. **Gerar autos de infração** por ementa (use o modelo da seção "Modelo de Auto de
   Infração" deste skill).
2. **Receber relatório de recomendação geral** para envio à empresa (descrito na seção
   final).

---

## Diretrizes de análise por ementa

### Ementa 1010590 - Não evitar perigos no contexto de evitar riscos

Foco: a organização deve **priorizar a eliminação ou substituição do perigo na origem**
como primeira etapa do GRO, antes de partir para outras camadas da hierarquia de
controle.

Procure no PGR:

- Seção de metodologia ou processo de gerenciamento de riscos.
- Existência de **etapa explícita de evitar/eliminar perigos** antes da identificação e
  avaliação completas, em linha com o item 1.5.4.2.1.1 da NR-01.
- Aderência à **hierarquia de medidas de prevenção**: (1) eliminação/substituição,
  (2) proteção coletiva, (3) administrativas, (4) EPI.
- Postura **proativa**: tentativa de evitar riscos antes da introdução de novas
  atividades, máquinas ou processos.
- Vinculação com **levantamento preliminar de perigos** (item 1.5.4.2.1).

A irregularidade se configura quando o PGR pula a etapa de evitar/eliminar e vai direto
para proteção coletiva, administrativa ou EPI. **Não confundir** com a falta de
identificação (Ementa 1010603) nem com a falha em avaliar (Ementa 1010611): aqui a falha
é em **uma etapa anterior**, a de tentar evitar o risco.

**Saída**:
- Declare se há ou não evidência da irregularidade.
- Se há, cite trechos específicos do PGR que demonstram a falha e explique por que.
- Se não há, declare expressamente que a Ementa 1010590 não parece estar presente.

---

### Ementa 1010603 - Não identificar perigos corretamente

#### Regra Especial D.A: caso haja interdição confirmada

Se o AFT confirmou interdição na Etapa 2, conclua **automaticamente** pela infração e
use **literalmente** o texto a seguir como conteúdo do **subtítulo 2 (IRREGULARIDADE)**
ao gerar o auto:

> O PGR exige um trabalho de Análise Preliminar de Perigos de Acidente, o que não foi
> encontrado no PGR da autuada. Explica-se: em inspeção no ambiente de trabalho,
> encontrou-se irregularidades em maquinários nos setores de serviço inspecionados,
> conforme termo de interdição lavrado, em anexo. Os riscos mecânicos/acidentes
> provenientes do diverso maquinário da empresa foi identificado no PGR de forma
> genérica. Não há, anexo no PGR, nenhuma análise de riscos das máquinas. Consideramos
> que uma análise de risco seria a especificação dos limites das máquinas, identificação
> de perigos existentes e a estimativa dos riscos associados. O PGR deveria indicar
> quais máquinas representam um risco desprezível, baixo, alto, muito alto ou
> inaceitável. Depois, a partir da análise de risco é realizada a avaliação do risco,
> que serve para avaliar quais objetivos de redução foram atingidos, demonstrados no
> cronograma e plano de ação do PGR.
>
> A falta de dispositivos básicos e conhecidos de segurança em maquinário não pode
> passar "em branco" pelo PGR da autuada, mostrando que a organização realizou a
> identificação de perigos em desacordo com o previsto no subitem 1.5.4.3.1 da NR-01.

Após aplicar a regra especial, passe para a Ementa 1010611.

#### Análise padrão D.B: sem interdição

Examine se o PGR descreve, para cada perigo identificado:

- **Descrição clara do perigo** e das possíveis lesões/agravos associados (item
  1.5.3.2(b)).
- **Fontes ou circunstâncias** que geram o perigo (item 1.5.4.3.1).
- **Grupos de trabalhadores** sujeitos ao risco.
- **Perigos externos previsíveis** relacionados ao trabalho (item 1.5.4.3.2): entorno,
  atividades fora do estabelecimento.
- Cobertura de **atividades rotineiras e não rotineiras** e de **todas as pessoas** com
  acesso aos locais de trabalho (contratados, visitantes).

Examine o **Inventário de Riscos Ocupacionais** (item 1.5.7.3.2 alíneas a, b, c):
caracterização de processos e ambientes, caracterização de atividades, descrição de
perigos/danos/fontes/circunstâncias e grupos expostos.

Atenção a Inventário superficial que lista apenas perigos óbvios (físicos, químicos,
biológicos) ignorando outros.

**Saída**:
- Declare se há ou não evidência da irregularidade.
- Cite trechos específicos do PGR e do Inventário que sustentam a conclusão.
- Explique a relação entre o trecho citado e o requisito da NR-01 violado.

---

### Ementa 1010611 - Não avaliar riscos ou indicar nível de risco

A falha aqui é **posterior à identificação**: a organização identificou perigos mas não
avaliou os riscos nem atribuiu níveis (Art. 157, I, CLT c/c item 1.5.3.2(c)).

Examine, em especial no Inventário de Riscos:

- **Avaliação dos riscos**: para cada perigo identificado, há análise de risco
  correspondente?
- **Nível de risco** declarado (Trivial, Tolerável, Médio, Alto, Crítico, Intolerável
  ou outra escala): resultado da combinação severidade × probabilidade.
- **Critérios de avaliação**: matriz de risco, gradações, regras de decisão.

**Distinções importantes** (não confundir):

- Ausência total do PGR → Ementa 101110-3.
- Ausência do Inventário → Ementa 1010794.
- Falta de identificação dos perigos → Ementa 1010603.
- Classificação para fins de Plano de Ação → Ementa 1010719.
- Falhas na metodologia da avaliação (ferramentas inadequadas) → mais perto da Ementa
  1010697; mas ausência total ou falha generalizada na indicação do nível ainda se
  enquadra aqui.

**Saída**:
- Declare se há ou não evidência da irregularidade.
- Cite trechos: por exemplo, Inventário que lista perigos sem nível de risco; metodologia
  que não descreve como o risco é avaliado; ausência de critérios.

---

### Ementa 1010646 - Não considerar condições da NR-17 no PGR

A organização deve integrar as exigências da NR-17 (ergonomia) ao gerenciamento de
riscos.

Verifique:

- **Identificação de perigos ergonômicos** no Inventário: arranjo físico, esforço,
  posturas forçadas, movimentação manual de carga, turno, repetitividade, iluminação,
  desconforto térmico, fatores psicossociais, acústico, alerta constante, monotonia, uso
  da voz.
- **Lesões/agravos** decorrentes desses perigos.
- Inclusão dos **resultados da AEP (Avaliação Ergonômica Preliminar) ou AET (Análise
  Ergonômica do Trabalho)** nos termos da NR-17.
- **Fontes/circunstâncias** dos perigos ergonômicos.
- **Grupos** sujeitos ao risco.
- **Avaliação e classificação** dos riscos ergonômicos.
- **Critérios de gradação da probabilidade** considerando exigências da atividade: norma
  de produção, modo operatório, exigência de tempo, ritmo, conteúdo das tarefas, trabalho
  prescrito vs. real.
- **Integração explícita** entre PGR e NR-17.
- **AET incluída ou referenciada** quando exigida (avaliação aprofundada, inadequação da
  AEP, sugestão do PCMSO, análise de acidentes/doenças).

**Saída**:
- Declare se as condições da NR-17 foram consideradas.
- Indique presença/ausência de AEP e AET.
- Avalie a classificação dos riscos ergonômicos e a aplicação da hierarquia de controle
  para eles.
- Cite trechos textuais que sustentam as conclusões.
- Liste as não conformidades específicas com a Ementa 1010646.

---

### Ementa 1010743 - Plano de Ação ausente ou deficiente

Foco no **conteúdo do Plano de Ação** (itens 1.5.5.2.1 e 1.5.5.2.2 da NR-01). A
ausência total do Plano é coberta pela Ementa 101110-3; aqui a análise é sobre o Plano
existente que falha em algum requisito.

Localize o Plano de Ação no PGR e verifique a presença de:

- **Medidas de prevenção** a introduzir, aprimorar ou manter.
- **Cronograma**.
- **Formas de acompanhamento**.
- **Aferição de resultados**.
- **Data e assinatura** do documento.

**Saída**:
- Liste cada elemento ausente ou inadequado.
- Indique o subitem da NR-01 não atendido (1.5.5.2.1 ou 1.5.5.2.2).
- Explique por que a ausência configura irregularidade sob esta ementa.
- Aponte falta de data/assinatura como irregularidade documental adicional, se for o
  caso.
- Se o Plano estiver completamente ausente, registre isso e note que a ementa adequada
  seria 101110-3.

---

### Ementa 1010794 - Inventário de Riscos ausente ou em desacordo

Aplica-se quando: (1) o Inventário não foi elaborado, (2) foi elaborado mas faltam
requisitos mínimos, ou (3) não foi mantido atualizado.

Localize o Inventário e verifique cada requisito do item 1.5.7.3.2:

- **a)** Caracterização dos **processos e ambientes** de trabalho: mapeamento,
  entradas/saídas, características geográficas, construtivas, ocupação, indicação se o
  ambiente é próprio, de terceiros com cessão de mão de obra ou sem cessão.
- **b)** Caracterização das **atividades**: duração, frequência, máquinas, equipamentos,
  ferramentas, utilidades, atividades não rotineiras e de contratadas.
- **c)** Descrição de **perigos, danos, fontes, circunstâncias, grupos expostos** e
  **medidas de prevenção implementadas** (controles operacionais existentes).
- **d)** Dados de **análise preliminar/monitoramento** de agentes físicos, químicos e
  biológicos (NR-09) e **resultados da NR-17** (AEP ou AET).
- **e)** **Avaliação dos riscos** com classificação para fins de Plano de Ação.
- **f)** **Critérios** adotados para avaliação e tomada de decisão (matriz, regras,
  gradações).

Verifique também:

- Existência do documento (item 1.5.7.1, alínea "a").
- Consolidação dos dados de identificação e avaliação (item 1.5.7.3.1).
- Indícios de **atualização** e histórico (item 1.5.7.3.3).

**Saída**:
- Se o Inventário está ausente, declare isso como a irregularidade principal.
- Se presente, liste cada requisito (a até f) não atendido, citando o subitem da NR-01 e
  o trecho relevante do documento.

---

### Ementa 1011154 - Falha em consulta e comunicação com trabalhadores

A organização deve demonstrar envolvimento real dos trabalhadores no GRO (itens 1.5.3.3
e 1.5.5.1.3 da NR-01).

Verifique cada um destes 12 pontos:

1. Mecanismos documentados para **consultar trabalhadores sobre percepção de riscos**.
2. Consulta sobre percepção de riscos em **atividades rotineiras e não rotineiras**.
3. Consulta sobre percepção de riscos em **mudanças** (novos equipamentos, materiais,
   processos).
4. Uso da **CIPA** (quando existente) ou outros meios para a consulta.
5. Mecanismos documentados para **comunicar os riscos consolidados no Inventário** aos
   trabalhadores.
6. Mecanismos documentados para **comunicar as medidas do Plano de Ação**.
7. Informação aos trabalhadores sobre **procedimentos** durante a implantação das
   medidas.
8. Informação aos trabalhadores sobre **limitações** das medidas implantadas.
9. Evidência de **recebimento, documentação e resposta** às consultas (incluindo atas da
   CIPA).
10. Evidência de **uso das informações** obtidas nas consultas na gestão de riscos.
11. Evidência de que **preocupações e ideias** dos trabalhadores são recebidas,
    consideradas e atendidas.
12. **Evidências documentais**: comunicados, quadros de aviso, boletins, cartazes,
    e-mails, folders, SIPAT, CANPAT.

**Saída**:
- Use marcadores. Liste apenas os pontos (de 1 a 12) com irregularidade.
- Para cada um, explique brevemente por que se enquadra na Ementa 1011154, citando o
  item da NR-01 (1.5.3.3 ou 1.5.5.1.3).
- Se nada foi encontrado, declare explicitamente que não há irregularidades nesta
  ementa.
- **Não comente sobre irregularidades de outras ementas** nesta seção.

---

## Formato da saída da análise

Apresente direto no chat, ementa por ementa, em sequência. Para cada ementa use este
esquema:

```
### Ementa [código] - [descrição curta]

Conclusão: [presente / não presente / fortes indícios]

Evidências:
- [trecho citado do PGR] (pág. X) [ou ausência apontada]
- [explicação técnica vinculando à NR-01]

Dispositivos violados: [itens da NR-01]
```

**Citação de página é obrigatória sempre que possível.** Ao ler um PGR em PDF, registre
a página exata de cada trecho citado no formato `(pág. X)` ou `(págs. X a Y)`. Quando o
trecho vier de seção numerada do PGR (ex: item 5.2 do PGR), cite a seção em vez da
página. Essa rastreabilidade é essencial: o número da página será reaproveitado no texto
do auto de infração, e a empresa pode contestar a autuação se não conseguir localizar a
evidência citada.

Quando o PGR não trouxer informação relevante sobre uma ementa, declare explicitamente
que a irregularidade **não parece estar presente** com base no documento fornecido, sem
forçar enquadramento.

---

## Pós-análise: ofertas ao AFT

Ao terminar as sete ementas, faça uma pergunta única ao AFT:

> "Deseja que eu (1) gere os autos de infração e empacote tudo (textos + TXT
> importável pelo Sistema Auditor + PGR como anexo) na pasta `~/Desktop/autos_<CNPJ>/`,
> (2) escreva um relatório de recomendação geral para envio à empresa, ou (3) ambos?"

### 1) Geração de autos de infração e empacotamento

Esta etapa usa o **mesmo formato técnico da skill irmã `inspecao-completa`** (linhas
tipo 1, 4, 5, 6; placeholders; encoding latin-1; path Windows via Parallels; `#13#10`
como separador). Sempre que a especificação técnica do TXT for relevante e não estiver
detalhada aqui, consulte a `inspecao-completa` como fonte autoritativa: a PGR-analise é
especialista em **análise**; o formato de exportação fica delegado àquele skill.

#### 1.1. Coleta de dados

Antes de gerar os autos, garanta que tem:

- **CIF do auditor** (6 dígitos): obrigatório, vai na linha tipo 6.
- **CNPJ** da autuada (apenas dígitos): obrigatório, define o nome da pasta.
- **Razão social, endereço**: opcionais. Use placeholders da `inspecao-completa`
  (`CLIQUE NA LUPA E CONFIRA A UORG`, `Ja conferiu a UORG?`, `SN`, `QUADRA`, `BAIRRO`,
  `74911810`, `GO`, `Goiânia`) se não fornecidos.
- **Data de início da fiscalização** e **atividade econômica do estabelecimento**:
  obrigatórios, entram no subtítulo 1 do auto.

O CNPJ e a atividade econômica costumam estar na capa do PGR. Procure antes de
perguntar. Se não localizar, peça em uma única mensagem só o que falta.

#### 1.2. Estrutura do texto de cada auto (3 subtítulos)

Para cada ementa irregular, gere um auto com a estrutura abaixo. Esta é a mesma
estrutura da `inspecao-completa`, compatível com a geração de `#13#10` no TXT.

##### SUBTÍTULO 1: DA FISCALIZAÇÃO (texto fixo)

```
1) DA FISCALIZAÇÃO:

Trata-se de fiscalização mista, realizada nos termos do art. 30, § 3º,
do Decreto nº 4.552/2002, iniciada em [data_inspecao] e ainda em curso
na presente data no empregador acima qualificado, que desenvolve a
atividade econômica de [atividade_economica].
```

##### SUBTÍTULO 2: IRREGULARIDADE (texto contextual)

Aqui entra o conteúdo específico da ementa, com base na análise.

**Regras de redação**:

- Descreva os **fatos concretos** com precisão técnica e tom oficial.
- Cite o **dispositivo da NR-01** violado (item exato, ex: 1.5.4.3.1).
- **Incorpore as citações de página** geradas na análise (`pág. X` ou `págs. X a Y`).
  Não economize palavras: a empresa precisa localizar cada evidência citada.
- Em SST (caso do PGR), inclua o **parágrafo de dano coletivo** (texto fixo abaixo).
- Finalize com a conclusão jurídica: *"Sendo assim, incorreu o empregador na infração
  ementada supracitada."*
- Tom: sóbrio, formal, impessoal, terceira pessoa.

**Parágrafo de dano coletivo (incluir sempre em PGR, que é SST)**:

```
Dano de natureza coletiva. A Portaria MTP nº 667/2021 esclareceu que a
citação do empregado em situação irregular faz-se necessária apenas
quando imprescindível à caracterização da infração e quando a lei fixar
a multa com base no quantitativo de trabalhadores diretamente
prejudicados. Ademais, nas infrações que atingem a coletividade dos
trabalhadores, tais como naquelas inerentes ao meio ambiente de trabalho
(SST), dispensa-se a individualização do sujeito, pois o bem jurídico
tutelado tem natureza difusa ou coletiva. (Orientação técnica
SIT/n.2/2022).
```

**Caso especial: Ementa 1010603 com interdição confirmada**. Use o texto literal da
Regra Especial D.A (definido na seção da Ementa 1010603) como conteúdo deste
subtítulo 2. O texto da regra dispensa citação de página, pois a prova material é o
termo de interdição anexo.

##### SUBTÍTULO 3: OBSERVAÇÕES (texto fixo)

```
3) OBSERVAÇÕES: a) Lavrado no local da inspeção, conforme parágrafo único do art. 4º da Portaria 667/2021.#13#10b) A auditoria foi iniciada no local de trabalho e continuada em unidade do MTE, com análise documental, pesquisa nos sistemas informatizados e lavratura de documentos (necessidade de acesso a bancos de dados oficiais - eSocial - para confirmação das evidências), o que caracteriza ação fiscal mista, de acordo com o artigo 30, § 3º, do Decreto nº 4.552/2002. Desse modo, a fiscalização ainda se encontra em andamento na data de lavratura deste Auto de Infração.
```

> Texto fixo. Não altere. **ATENÇÃO: o texto DEVE conter acentuação completa em português.** O encoding ISO-8859-1 (Latin-1) suporta todos os caracteres acentuados do português — o passo `iconv` na geração do TXT trata o encoding automaticamente. Nunca remova acentos.

##### ELEMENTOS DE CONVICÇÃO

Para autuações de PGR, o padrão é:

```
ELEMENTOS DE CONVICÇÃO:
Análise documental do PGR apresentado pela empresa; inspeção in loco.
```

Em casos de interdição, acrescente: `; termo de interdição lavrado, em anexo`.

#### 1.3. Geração do TXT importável

Siga **literalmente** o formato de linhas da `inspecao-completa` (linha tipo 1 com 23
campos / 22 tabs, linhas tipo 5 para anexos, linha tipo 6 com a CIF). Não há linhas
tipo 4 para autos de PGR (a infração é coletiva, sem nominação de trabalhadores).

**Códigos fixos** (idênticos aos da `inspecao-completa`):

| Parâmetro | Valor |
|---|---|
| cod_1 (CNAE) | `8211300` |
| cod_2 (tipo ação) | `1008` |
| cod_3 | código da ementa sem hífen (ex: `1010603` → `1010603`; `101059-0` → `1010590`) |
| cod_4 (UORG) | `015000000` |
| cod_5 | (vazio) |
| cod_6 (local) | `SETOR SUL` |
| cod_7 (CEP UORG) | `74080010` |

**Códigos das sete ementas do PGR para cod_3** (todos sem hífen, 7 dígitos):

| Ementa | cod_3 |
|---|---|
| 1010590 | `1010590` |
| 1010603 | `1010603` |
| 1010611 | `1010611` |
| 1010646 | `1010646` |
| 1010743 | `1010743` |
| 1010794 | `1010794` |
| 1011154 | `1011154` |

**Texto da autuação em linha única**: o conteúdo dos três subtítulos vai concatenado
em uma única linha do TXT, usando `#13#10` para quebras (interpretado pelo Sistema
Auditor):

- Entre subtítulos (1→2 e 2→3): `#13#10 . #13#10` (linha vazia visível).
- Entre parágrafos dentro do mesmo subtítulo: `#13#10`.

**Concatenação de múltiplos autos**: todos os blocos (um por ementa) ficam no **mesmo
arquivo TXT**, um após o outro, sem linhas em branco entre eles.

**Encoding**: gere em UTF-8 e converta para latin-1 (ISO-8859-1) antes de salvar:

```bash
iconv -f utf-8 -t iso-8859-1 "$TXT" > "$TXT.tmp" && mv "$TXT.tmp" "$TXT"
```

**Nome do TXT**: `AI_<NUM_AUTOS>_<CNPJ>.txt`, onde `NUM_AUTOS` é a contagem total de
autos no arquivo. Exemplo com 3 autos para CNPJ `12345678000190`:
`AI_3_12345678000190.txt`.

#### 1.4. Empacotamento em pasta na Desktop

Estrutura padrão (idêntica à `inspecao-completa`):

```
~/Desktop/autos_<CNPJ>/
├── AI_<NUM>_<CNPJ>.txt              (arquivo importável pelo Sistema Auditor)
├── AI_<NUM>_<CNPJ>_legivel.md       (versão legível dos autos, para revisão humana)
└── AI_<NUM>_<CNPJ>_PGR.PDF          (cópia do PGR como anexo, comprimida se > 10 MB)
```

**Criação da pasta**:

```bash
mkdir -p ~/Desktop/autos_<CNPJ>/
```

Se a pasta já existir, pergunte ao AFT: *"Já existe `~/Desktop/autos_<CNPJ>/`. Deseja:
(a) sobrescrever, (b) renomear a antiga para `_backup_<timestamp>`, (c) cancelar?"*

**Quando o ambiente de execução for um container sem acesso à Desktop do usuário**
(como o claude.ai web), substitua o destino por `/mnt/user-data/outputs/autos_<CNPJ>/`
e chame `present_files` ao final com a lista dos arquivos. Comunique: *"Como estou
rodando em ambiente sem acesso direto à sua MESA, gerei a pasta em outputs. Baixe e
mova para `~/Desktop/autos_<CNPJ>/` antes de importar no Sistema Auditor."*

#### 1.5. Tratamento do PGR como anexo (limite 10 MB)

Se o PGR foi fornecido como PDF, anexe uma cópia dentro da pasta de saída para ser
juntada aos autos no Sistema Auditor.

**Nome do arquivo do anexo**: `AI_<NUM>_<CNPJ>_PGR.PDF` (extensão `.PDF` em maiúsculas,
sistema MTE é case-sensitive).

**Compressão se exceder 10 MB**:

1. Primeira tentativa, ghostscript com `/ebook` (150 dpi):
   ```bash
   gs -sDEVICE=pdfwrite -dCompatibilityLevel=1.4 -dPDFSETTINGS=/ebook \
      -dNOPAUSE -dQUIET -dBATCH \
      -sOutputFile="AI_<NUM>_<CNPJ>_PGR.PDF" PGR_original.pdf
   ```

2. Se ainda > 10 MB, segunda tentativa com `/screen` (72 dpi):
   ```bash
   gs -sDEVICE=pdfwrite -dCompatibilityLevel=1.4 -dPDFSETTINGS=/screen \
      -dNOPAUSE -dQUIET -dBATCH \
      -sOutputFile="AI_<NUM>_<CNPJ>_PGR.PDF" PGR_original.pdf
   ```

3. Se mesmo `/screen` mantiver acima de 10 MB, avise o AFT: *"PGR ficou em <X MB> mesmo
   após compressão máxima. Recomendo dividir o PDF ou anexar manualmente."* Ainda assim,
   inclua o arquivo comprimido na pasta.

**Linha tipo 5 para o anexo**: uma linha tipo 5 por auto, repetindo o mesmo PGR para
todos os autos (cada AI precisa ter o PGR como evidência). O path é absoluto Windows
via drive Parallels:

```
5	Y:\Desktop\autos_<CNPJ>\AI_<NUM>_<CNPJ>_PGR.PDF	Programa de Gerenciamento de Riscos
```

> A descrição do anexo (`Programa de Gerenciamento de Riscos`) é a evidência citada
> dentro do auto. Diferente da `inspecao-completa` que usa "Registro Fotografico" para
> fotos, aqui o anexo é o próprio PGR auditado.

Se o AFT estiver em ambiente diferente do padrão Parallels (drive `Y:`), peça que
ele confirme a letra de drive ou ajuste manualmente antes da importação.

### 2) Relatório de recomendação geral para a empresa

Quando solicitado, redija um relatório técnico **resumido e de fácil entendimento**
dirigido à empresa, com:

- Identificação dos principais problemas encontrados no PGR auditado, agrupados por
  tema (identificação de perigos, avaliação, Inventário, Plano de Ação, ergonomia,
  consulta/comunicação).
- Orientação clara de que a empresa deve **revisar integralmente o PGR**, com foco nos
  pontos críticos apontados.
- Tom técnico, direto, sem linguagem jurídica de auto de infração. O destinatário aqui
  é o empregador, não o processo.

Salve o relatório como `recomendacao_geral.md` dentro da mesma pasta
`~/Desktop/autos_<CNPJ>/` se o AFT pediu também a geração dos autos. Caso contrário,
entregue diretamente no chat ou em arquivo `.md` solto em outputs.

---

## Regras gerais

- Texto técnico, oficial, em terceira pessoa. Sem informalidades.
- **Não usar travessões** (em-dashes). Substituir por dois pontos, vírgulas, parênteses
  ou hífen simples.
- Não invente dados. Se uma informação não estiver no PGR, declare a ausência.
- Não force enquadramento: se a ementa não estiver presente com base no documento,
  declare explicitamente.
- Mantenha a separação entre ementas: não misture irregularidades de uma ementa na
  análise de outra.
- Os textos fixos (regra especial D.A da Ementa 1010603 e modelo do auto de infração)
  são imutáveis. Reproduza-os literalmente quando aplicáveis.
