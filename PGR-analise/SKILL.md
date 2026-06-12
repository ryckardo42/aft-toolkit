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
  documento, e oferece a redação dos autos de infração (formato 3 subtítulos) no formato
  consumido pelo /gera-ai, que empacota o TXT do Sistema Auditor com o próprio PGR como
  anexo de cada AI.
---

# PGR-analise — Análise de PGR (NR-01)
**AFT Toolkit**

## Objetivo

Analisar um Programa de Gerenciamento de Riscos (PGR) sob a ótica da NR-01, identificando
irregularidades enquadráveis em sete ementas de auto de infração. O resultado é uma análise
ementa por ementa, com citação dos trechos do PGR que sustentam cada conclusão, e a oferta
de redação dos autos de infração (empacotamento via `/gera-ai`) e relatório de recomendação
para a empresa.

---

## Fluxo de execução

### Etapa 1: Receber e registrar o contexto da inspeção física (obrigatório)

> **Princípio:** o PGR não é auditado no vácuo. É um documento que deve refletir a
> realidade do ambiente de trabalho. Todo risco e toda irregularidade que o AFT constatou
> in loco é evidência direta para esta análise: se o PGR não identifica, não avalia ou não
> trata um risco que existe de fato no estabelecimento, isso configura irregularidade nas
> ementas correspondentes. Por isso, **a captura do contexto de campo antecede a leitura do
> PGR.**

**Localize a pasta da OS.** Determine a pasta da empresa em
`~/Documents/AFT/OS ATIVAS/`. Se o AFT já citou a empresa/CNPJ na conversa,
use-a; senão, pergunte qual OS (ou liste as candidatas).

**Procure o `inspecao-fisica.md` antes de perguntar.** Esse arquivo é a fonte primária do
contexto de campo — irregularidades encontradas in loco que influenciam a análise do PGR:

```bash
ls ~/Documents/AFT/"OS ATIVAS"/"<PASTA_EMPRESA>"/inspecao-fisica.md
```

- **Encontrado:** leia-o e use seu conteúdo como a lista de achados de campo (modo
  confronto). Apresente um resumo ao AFT e confirme: *"Carreguei o contexto de campo de
  `inspecao-fisica.md`: [resumo dos achados]. Confirma que uso isso para confrontar o PGR?"*
- **Não encontrado:** caia para a pergunta padrão abaixo.

**Caso contrário, comece perguntando** ao AFT pelo contexto da inspeção física — salvo se ele
já o tiver descrito na conversa. Nesse caso, reaproveite o que já está no contexto e apenas confirme.

Pergunta padrão (se não houver `inspecao-fisica.md` e o contexto ainda não foi fornecido):

> "Antes de analisar o PGR, preciso do contexto da sua inspeção física. Liste os achados e
> irregularidades evidentes constatados in loco — por exemplo: trabalho em altura, uso de
> produtos químicos, máquinas sem proteção, mobiliário/posto de trabalho deficiente
> (NR-17), ausência de CIPA, ausência de SESMT, condição de risco grave e iminente /
> interdição lavrada, etc. Se não houve inspeção física e esta é uma análise puramente
> documental (ex: PGR entregue via DET), me diga apenas 'documental'."

**Registre os achados** numa lista interna de trabalho. Para cada achado anote: (a) o
risco/condição observado, (b) o setor/atividade onde foi visto. Essa lista é a **lente de
confronto** usada na Etapa 4.

**Modo de execução** — defina conforme a resposta:

- **Modo confronto (padrão):** houve inspeção física e o AFT forneceu achados. A análise de
  cada ementa será confrontada com a lista de campo (Etapa 4).
- **Modo documental:** o AFT respondeu "documental" (ou equivalente). Prossiga normalmente,
  mas **marque o relatório** no topo com o aviso: `⚠️ Análise documental apenas — sem
  confronto com inspeção in loco. Riscos reais não declarados no PGR podem não ter sido
  detectados.` Nesse modo a análise se baseia só no que o documento traz.

Não avance para a Etapa 2 sem resolver explicitamente qual é o modo.

---

### Etapa 2: Receber o PGR

**Procure o PGR na pasta da OS antes de pedir.** O PGR costuma ser um PDF com `PGR` no
nome, ou estar dentro de uma pasta com `PGR` no nome. Procure na pasta da OS (e subpastas).

- **Um único PDF localizado:** use-o (confirme o nome com o AFT em uma linha).
- **Vários candidatos:** liste-os e pergunte qual é o PGR a analisar.
- **Nenhum:** peça ao AFT (anexo no chat ou caminho do arquivo).

O PGR também pode chegar como PDF anexado ou como texto colado. Um anexo/texto fornecido
explicitamente pelo AFT tem **precedência** sobre a busca na pasta.

Faça uma leitura inicial completa antes de começar a análise por ementa. Localize, na
medida do possível, as seções correspondentes a: metodologia de GRO, identificação de
perigos, avaliação de riscos, Inventário de Riscos, Plano de Ação, ergonomia (NR-17),
consulta/comunicação com trabalhadores.

### Etapa 3: Detectar gatilhos contextuais

**Gatilho de interdição (afeta a Ementa 1010603).**

Na lista de contexto de campo capturada na Etapa 1 (ou em qualquer menção do AFT na
conversa), verifique se há indício de interdição: "interdição de máquina", "termo de
interdição lavrado", "máquina interditada", "setor interditado", "risco grave e
iminente", ou termos equivalentes.

Se detectar o gatilho, **pare antes de iniciar a Ementa 1010603 e confirme**:

> "Identifiquei menção de interdição no seu contexto. Confirma que houve interdição
> formal nesta fiscalização? Se sim, aplicarei a regra especial da Ementa 1010603, que
> conclui automaticamente pela infração com texto padronizado."

Só aplique a Regra Especial D.A (descrita abaixo) após confirmação explícita do AFT.

### Etapa 4: Análise sequencial por ementa

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

#### Confronto obrigatório campo × PGR (modo confronto)

No modo confronto, **cada achado de campo da Etapa 1 deve ser rastreado contra o PGR**
antes de fechar cada ementa. Use este mapeamento como roteiro:

| Achado in loco | Pergunta de confronto | Ementa(s) afetada(s) |
|---|---|---|
| Qualquer risco real observado (altura, químico, máquina, físico, biológico) | O risco está identificado no Inventário? Fontes/circunstâncias e grupos expostos descritos? | 1010603, 1010794 |
| Risco observado presente mas sem nível atribuído | O risco foi avaliado e classificado (nível)? | 1010611 |
| Mobiliário/posto deficiente, postura forçada, esforço, repetitividade | O perigo ergonômico foi inventariado e avaliado? Há AEP/AET? | 1010646 |
| Risco que poderia ter sido eliminado/substituído na origem | O PGR tentou evitar o perigo antes de partir para EPI/administrativo? | 1010590 |
| CIPA atuante / ausência de consulta percebida em campo | O PGR documenta consulta aos trabalhadores e uso da CIPA? | 1011154 |
| Risco grave e iminente / interdição lavrada | (aplica a Regra Especial D.A) | 1010603 |

**Regra de ouro:** se um risco existe de fato no estabelecimento (você o viu) e o PGR não
o identifica, não o avalia ou não o trata, a ausência é evidência **positiva** de
irregularidade — mais forte do que uma lacuna meramente documental. Cite o achado de campo
como elemento de convicção ao lado do trecho (ou da ausência) no PGR.

**Achados sem correspondência nas 7 ementas de PGR:** alguns achados de campo são infrações
autônomas de outras NRs e não dizem respeito ao conteúdo do PGR. Esta skill é especialista
em **PGR/NR-01 e permanece estritamente nesse escopo** — não enquadra, não comenta e não
gera autos de outras NRs (para isso, use `/inspecao-inicial`). Use esses achados apenas,
quando couber, como contexto de que o ambiente tem riscos relevantes que o PGR deveria refletir.

### Etapa 5: Pós-análise

Após concluir as sete ementas, pergunte ao AFT se deseja:

1. **Redigir os autos de infração** por ementa (formato `/gera-ai` — ver seção "Redação
   dos autos" abaixo).
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

Se o AFT confirmou interdição na Etapa 3, conclua **automaticamente** pela infração e
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

Confronto com o campo: [achado in loco relevante para esta ementa e como ele sustenta ou afasta a irregularidade; ou "sem achado de campo aplicável" / "modo documental — não aplicável"]

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

Ao final, salve a análise completa em
`~/Documents/AFT/OS ATIVAS/[PASTA_EMPRESA]/analise-PGR.md`.

---

## Pós-análise: ofertas ao AFT

Ao terminar as sete ementas, faça uma pergunta única ao AFT:

> "Deseja que eu (1) redija os autos de infração das ementas presentes (formato pronto
> para o `/gera-ai`, com o PGR como anexo), (2) escreva um relatório de recomendação
> geral para envio à empresa, ou (3) ambos?"

### 1) Redação dos autos de infração (formato /gera-ai)

Para cada ementa irregular, gere um bloco no formato consumido pelo `/gera-ai`:

```
=== AUTO DE INFRAÇÃO #[N] ===
Ementa: [codigo com hífen, ex: 101059-0] - [descrição curta da ementa]

1) DA FISCALIZAÇÃO:

Trata-se de fiscalização mista, realizada nos termos do art. 30, § 3º,
do Decreto nº 4.552/2002, iniciada em [data_inspecao] e ainda em curso
na presente data no empregador acima qualificado, que desenvolve a
atividade econômica de [atividade_economica].

2) IRREGULARIDADE:

[Conteúdo específico da ementa, com base na análise — ver regras abaixo]

3) OBSERVAÇÕES: a) Lavrado no local da inspeção, conforme parágrafo único do art. 4º da Portaria 667/2021.#13#10b) A auditoria foi iniciada no local de trabalho e continuada em unidade do MTE, com análise documental, pesquisa nos sistemas informatizados e lavratura de documentos (necessidade de acesso a bancos de dados oficiais - eSocial - para confirmação das evidências), o que caracteriza ação fiscal mista, de acordo com o artigo 30, § 3º, do Decreto nº 4.552/2002. Desse modo, a fiscalização ainda se encontra em andamento na data de lavratura deste Auto de Infração.

ELEMENTOS DE CONVICÇÃO:
Análise documental do PGR apresentado pela empresa; inspeção in loco.
```

**Dados a coletar antes** (procure na capa do PGR antes de perguntar; peça em uma única
mensagem só o que faltar): data de início da fiscalização e atividade econômica do
estabelecimento. CNPJ: capa do PGR ou memory.md.

**Regras de redação do subtítulo 2**:

- Descreva os **fatos concretos** com precisão técnica e tom oficial.
- Cite o **dispositivo da NR-01** violado (item exato, ex: 1.5.4.3.1).
- **Incorpore as citações de página** geradas na análise (`pág. X` ou `págs. X a Y`).
  Não economize palavras: a empresa precisa localizar cada evidência citada.
- Inclua o **parágrafo de dano coletivo** (PGR é SST):

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

- Finalize com a conclusão jurídica: *"Sendo assim, incorreu o empregador na infração
  ementada supracitada."*
- Tom: sóbrio, formal, impessoal, terceira pessoa. Sem travessões.
- **Caso especial — Ementa 1010603 com interdição confirmada**: use o texto literal da
  Regra Especial D.A como conteúdo do subtítulo 2 e acrescente aos elementos de
  convicção: `; termo de interdição lavrado, em anexo`.
- O subtítulo 3 é **fixo e literal** (bloco acima) — não altere.
- Não há trabalhadores nominados em autos de PGR (infração coletiva — sem linhas tipo 4).

**Códigos das sete ementas** (formato com hífen, para a linha `Ementa:` — o `/gera-ai`
remove o hífen no cod_3):

| Ementa | Linha `Ementa:` |
|---|---|
| 1010590 | `101059-0` |
| 1010603 | `101060-3` |
| 1010611 | `101061-1` |
| 1010646 | `101064-6` |
| 1010743 | `101074-3` |
| 1010794 | `101079-4` |
| 1011154 | `101115-4` |

**Salvar e handoff**: salve todos os blocos em
`~/Documents/AFT/OS ATIVAS/[PASTA_EMPRESA]/autos-pgr.md` e exiba:

```
✅ N autos de PGR redigidos — salvos em autos-pgr.md

▶ Próximo passo — empacotar no TXT do Sistema Auditor:
  1) Rode /gera-ai e responda que os autos estão (b) na sessão.
  2) Quando ele tratar de anexos, informe o PDF do PGR como documento pronto —
     ele será renomeado para AI_[N]_[CNPJ]_PGR.PDF e vinculado a TODOS os autos
     (cada AI precisa do PGR como evidência).
  3) Se o PGR tiver mais de 10 MB, o /gera-ai comprime com o script do toolkit.
```

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

Salve o relatório como `recomendacao-geral-PGR.md` na pasta da OS.

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
- Os textos fixos (regra especial D.A da Ementa 1010603, subtítulo 3 e parágrafo de dano
  coletivo) são imutáveis. Reproduza-os literalmente quando aplicáveis.
