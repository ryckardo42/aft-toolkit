---
name: aft-PGRTR-analise
model: opus
description: >
  Use quando o AFT pedir para analisar, auditar ou revisar um Programa de
  Gerenciamento de Riscos do Trabalho Rural (PGRTR) à luz da NR-31. Acione com
  "analisar PGRTR", "auditar PGRTR", "PGRTR da fazenda/empresa", "PGRTR
  apresentado", trabalho rural, fazenda, produtor rural, os códigos de ementa
  231084-8 a 231148-8, ou ao anexar PDF de PGRTR de estabelecimento rural.
  Varre a base fixa de ementas de NR-31 e oferece a redação dos autos. NÃO
  confundir com /aft-PGR-analise (PGR sob a NR-01, ambiente geral/urbano).
---

# PGRTR-analise — Análise de PGRTR (NR-31, trabalho rural)
**AFT Toolkit**

> **Onde ficam as pastas das OS.** O AFT pode ter mudado a pasta de trabalho de
> lugar (HD externo, nuvem, outro disco). Nunca presuma `~/Documents/AFT`:
> resolva **uma vez, no início**, e use o que voltar onde este texto disser
> `<OS_ATIVAS>` (a pasta que contém as OS) ou `<PASTA_AFT>` (a pasta acima dela).
>
> **Nas mensagens ao AFT, escreva o caminho de verdade** — nunca ecoe
> `<OS_ATIVAS>`/`<PASTA_AFT>` na tela: ele precisa saber onde abrir a pasta.
>
> ```bash
> python ~/.claude/skills/_scripts/pasta_aft.py --os-ativas   # -> <OS_ATIVAS>
> python ~/.claude/skills/_scripts/pasta_aft.py --path        # -> <PASTA_AFT>
> ```

## Objetivo

Analisar um Programa de Gerenciamento de Riscos do Trabalho Rural (PGRTR) — e, quando
disponíveis, o PCMSO, os Atestados de Saúde Ocupacional (ASO), as Fichas de Fornecimento
de EPI e a Análise Ergonômica Preliminar/do Trabalho (AEP/AET) — sob a ótica da NR-31,
identificando irregularidades enquadráveis na base fixa de ementas ao final deste skill.
O resultado é uma análise ementa por ementa, com citação de página e confronto com os
achados da inspeção física, e a oferta de redigir os autos de infração (formato
`/aft-gera-ai`) e uma carta de recomendação para o produtor rural.

**Não confundir com `/aft-PGR-analise`** (PGR sob a NR-01, ambiente geral/urbano): são
normas, documentos e ementas completamente diferentes.

---

## Fluxo de execução

### Etapa 1: Receber e registrar o contexto da inspeção física (obrigatório)

> **Princípio:** o PGRTR não é auditado no vácuo. É um documento que deve refletir a
> realidade do estabelecimento rural. Todo risco e toda irregularidade que o AFT
> constatou in loco é evidência direta para esta análise: se o PGRTR não identifica, não
> avalia ou não trata um risco que existe de fato na propriedade, isso configura
> irregularidade nas ementas correspondentes. Por isso, **a captura do contexto de campo
> antecede a leitura do PGRTR.**

**Localize a pasta da OS.** Determine a pasta da empresa/fazenda em `<OS_ATIVAS>/`. Se o
AFT já citou o empregador rural, a fazenda ou o CNPJ/CPF na conversa, use-a; senão,
pergunte qual OS (ou liste as candidatas).

**Procure o `inspecao-fisica.md` antes de perguntar.** Esse arquivo é a fonte primária
do contexto de campo:

```bash
ls "<OS_ATIVAS>"/"<PASTA_EMPRESA>"/inspecao-fisica.md
```

- **Encontrado:** leia-o e use seu conteúdo como a lista de achados de campo (modo
  confronto). Apresente um resumo ao AFT e confirme: *"Carreguei o contexto de campo de
  `inspecao-fisica.md`: [resumo dos achados]. Confirma que uso isso para confrontar o
  PGRTR?"*
- **Não encontrado:** caia para a pergunta padrão abaixo.

**Caso contrário, comece perguntando** ao AFT pelo contexto da inspeção física — salvo
se ele já o tiver descrito na conversa. Nesse caso, reaproveite o que já está no
contexto e apenas confirme.

Pergunta padrão (se não houver `inspecao-fisica.md` e o contexto ainda não foi
fornecido):

> "Antes de analisar o PGRTR, preciso do contexto da sua inspeção física. Liste os
> achados e irregularidades constatados in loco — por exemplo: aplicação de agrotóxicos,
> máquinas e implementos agrícolas sem proteção, trabalho com animais, frentes de
> trabalho sem área de vivência ou sanitários, alojamento precário, trabalho sob calor
> extremo, transporte irregular de trabalhadores, terrenos acidentados, condição de
> risco grave e iminente / interdição lavrada, etc. Se não houve inspeção física e esta
> é uma análise puramente documental (ex: PGRTR entregue via DET), me diga apenas
> 'documental'."

**Registre os achados** numa lista interna de trabalho. Para cada achado anote: (a) o
risco/condição observado, (b) o setor/atividade/frente de trabalho onde foi visto. Essa
lista é a **lente de confronto** usada na Etapa 4.

**Modo de execução** — defina conforme a resposta:

- **Modo confronto (padrão):** houve inspeção física e o AFT forneceu achados. A análise
  de cada ementa será confrontada com a lista de campo (Etapa 4).
- **Modo documental:** o AFT respondeu "documental" (ou equivalente). Prossiga
  normalmente, mas **marque o relatório** no topo com o aviso: `⚠️ Análise documental
  apenas — sem confronto com inspeção in loco. Riscos reais não declarados no PGRTR
  podem não ter sido detectados.` Nesse modo a análise se baseia só no que os documentos
  trazem.

Não avance para a Etapa 2 sem resolver explicitamente qual é o modo.

---

### Etapa 2: Localizar os documentos e coletar os dados do caso

> **Onde esta skill grava.** Tudo o que ela produz mora na subpasta
> `auditoria-PGRTR/` da OS (crie-a na primeira gravação): `analise-PGRTR.md`,
> `pgrtr-extrato.md`, `pcmso-extrato.md`, `autos-pgrtr.md` e
> `recomendacao-geral-PGRTR.md`. **Nunca grave esses arquivos na raiz da OS.**
> Em OS antigas eles podem existir na raiz: use-os normalmente para leitura, mas
> toda gravação nova vai para a subpasta.

**Procure os documentos sozinho antes de perguntar**, na pasta da OS inteira
(`NOTIFICACOES/`, subpastas de resposta ao DET, e raiz), por nome de arquivo
(case-insensitive):

| Documento | Padrões de nome a procurar |
|---|---|
| PGRTR (obrigatório) | contém "PGRTR" ou "PGR" + "rural" |
| PCMSO | contém "PCMSO" |
| Atestados de Saúde Ocupacional (ASO) | contém "ASO" ou "atestado" + "saude"/"ocupacional" |
| Ficha de Fornecimento de EPI | contém "EPI" + "ficha"/"fornecimento" |
| Análise Ergonômica Preliminar / do Trabalho | contém "AEP", "AET" ou "ergonom" |

Um anexo/texto fornecido explicitamente pelo AFT no chat tem **precedência** sobre a
busca na pasta. **Prefira sempre o arquivo na pasta da OS:** documento arrastado para o
chat entra inteiro no contexto da conversa e anula a economia da Etapa 3. Se o AFT
anexar um PGRTR grande, grave-o em `auditoria-PGRTR/` na pasta da OS e siga por lá.

Se o PGRTR não for localizado nem fornecido, **não prossiga** — peça-o ao AFT (é o único
documento obrigatório; os demais são opcionais e enriquecem a análise).

**Notificação (NAD):** não reextraia o código do PDF — leia a seção
`## Notificações DET` do `memory.md` da OS e use o código e a data de lá. Só procure o
PDF diretamente se o `memory.md` não tiver notificação cadastrada.

**Dados a coletar antes de perguntar** (procure no `memory.md`, na capa do PGRTR, ou no
RI/SFIT-WEB antes de perguntar ao AFT; pergunte só o que faltar, numa única mensagem):

- Data de início da fiscalização.
- Atividade desenvolvida no estabelecimento rural.
- Nome da fazenda/propriedade e coordenadas GPS (costumam constar no RI do SFIT-WEB,
  campo "Coordenadas GPS", ou no `memory.md`).
- Se o empregador rural tem CIPATR ou SESTR.
- Se os EPIs e dispositivos de proteção pessoal foram fornecidos (confira também a Ficha
  de Fornecimento de EPI, se localizada).

**Eco de confirmação (uma única mensagem):** antes de iniciar a leitura, mostre o que
foi encontrado/coletado e pergunte se falta algo ou se pode iniciar:

```
Documentos identificados para <EMPREGADOR RURAL>:
  PGRTR: <nome do arquivo ou "não identificado/enviado">
  PCMSO: <nome do arquivo ou "não identificado/enviado">
  Atestados de Saúde (ASO): <nome(s) do(s) arquivo(s) ou "não identificado/enviado">
  Ficha de Fornecimento de EPI: <nome do arquivo ou "não identificado/enviado">
  AEP/AET: <nome do arquivo ou "não identificado/enviado">
  Notificação (NAD): <código, se localizado no memory.md, ou "não localizada">

  Data de início da fiscalização: <data ou "a confirmar">
  Atividade desenvolvida: <atividade ou "a confirmar">
  Fazenda/coordenadas: <dados ou "a confirmar">
  CIPATR/SESTR: <resposta ou "a confirmar">
  EPIs fornecidos: <resposta ou "a confirmar">
  Contexto de campo: <modo confronto (resumo) ou modo documental>

Está correto? Posso iniciar a análise, ou você quer enviar/apontar mais algum arquivo
ou corrigir algum dado?
```

---

### Etapa 3: Leitura do PGRTR — delegue ao agente extrator

PGRTR costuma passar de cem páginas. Lido direto na conversa, ele consome o contexto e o
limite de uso do AFT, e é **recobrado a cada turno** da análise — o que estoura o plano
no meio do trabalho. Por isso a leitura é feita fora da conversa, por um agente próprio.

**Antes de medir, veja se o extrato já existe.** Se
`<OS_ATIVAS>/[PASTA_EMPRESA]/auditoria-PGRTR/pgrtr-extrato.md` já estiver na pasta (ou,
em OS antigas, `pgrtr-extrato.md` na raiz da OS), a extração já foi
feita — por uma execução anterior deste skill, ou por um fluxo que extraiu os documentos
numa triagem inicial. Confira que ele cobre os blocos do roteiro abaixo e **siga direto
para "Analise sobre o extrato"**: não meça o PDF nem delegue de novo. Extrair duas vezes
o mesmo PGRTR é o desperdício mais caro deste skill. Só refaça a extração se o extrato
estiver vazio, truncado ou visivelmente fora do roteiro e, nesse caso, diga ao AFT em
uma linha por que está refazendo.

Descubra primeiro o tamanho do documento:

```bash
"<python_path>" ~/.claude/skills/_scripts/pdf_texto_paginado.py "<caminho do PGRTR>" --so-resumo
```

- **Mais de 20 páginas** (o caso comum): **delegue ao agente `aft-extrator-documento`**,
  passando no prompt o tipo de documento (PGRTR, NR-31), o caminho do PGRTR, o caminho
  de saída `<OS_ATIVAS>/[PASTA_EMPRESA]/auditoria-PGRTR/pgrtr-extrato.md`, o `python_path` e —
  obrigatoriamente — o **roteiro de extração**, que são os blocos temáticos da base de
  ementas deste skill:

  1. **Existência, estrutura e custeio do PGRTR** (itens 31.3.1 e 31.3.3.2 da NR-31):
     quem elaborou (nome, formação, registro profissional), vigência, se há inventário
     de riscos e Plano de Ação formalizados, responsáveis e prazos das ações, uso da
     ferramenta digital da SEPRT (até 50 empregados), custeio.
  2. **Processo de gerenciamento de riscos** (item 31.3.3 e alíneas): levantamento
     preliminar de perigos, avaliação/classificação dos riscos (matriz, severidade x
     probabilidade, gradação), medidas de prevenção com prioridades e cronograma,
     hierarquia de controle (eliminação, coletiva, administrativa, EPI),
     acompanhamento/verificação dos controles, procedimento de investigação de
     acidentes e doenças.
  3. **Inventário de riscos** (itens 31.3.2 e 31.3.3.2.1): cobertura dos cinco grupos
     de riscos (físicos, químicos, biológicos, ergonômicos, de acidentes), abrangência
     por função/atividade/frente de trabalho, classificação para fins de plano de ação.
  4. **Medidas específicas do meio rural** (item 31.3.5, alíneas a-f): trabalho com
     animais, condições climáticas extremas, organização do trabalho para esforço
     físico e terrenos acidentados, trânsito interno de trabalhadores e veículos,
     eliminação de resíduos, faixas de segurança de linhas elétricas.
  5. **Saúde ocupacional** (itens 31.3.6, 31.3.7 e subitens): planejamento das ações de
     saúde frente às peculiaridades rurais, exames admissional/periódico/retorno/
     mudança de risco/demissional, exames complementares conforme riscos e NR-07,
     exames quando exposição acima do nível de ação, uso dos parâmetros dos Anexos da
     NR-09 nas avaliações de exposição.
  6. **CAT, afastamento e acesso à saúde** (itens 31.3.11 e 31.3.12): procedimentos
     para emissão de CAT, afastamento da exposição e encaminhamento à Previdência
     diante de doença ocupacional ou alteração biológica; acesso a vacinação e
     profilaxia de endemias.
  7. **Comunicação e supervisão** (item 31.2.3 e 31.3.1.3): instruções compreensíveis,
     treinamentos, supervisão do trabalho, cientificação dos trabalhadores sobre os
     riscos do inventário e as medidas do plano de ação.

  O agente lê o documento inteiro no contexto dele e devolve um extrato fiel,
  organizado por esses blocos, com transcrição literal e número de página.
- **Até 20 páginas:** leia direto, sem delegar — o ganho não compensa a ida e volta.
- **Documento sem camada de texto** (escaneado; o script avisa em destaque): **delegue
  mesmo que seja curto.** Sem texto, cada página precisa ser lida como imagem, o que
  pesa na conversa muito mais do que o número de páginas sugere. Avise o AFT em uma
  linha, porque muda o que ele pode esperar do resultado:

  > "Este documento veio escaneado, sem texto pesquisável. Vou lê-lo página por página,
  > o que demora mais; o que ficar ilegível fica sinalizado no extrato para você
  > conferir no original."

Avise o AFT em uma linha antes de delegar (é uma etapa que demora):

> "O PGRTR tem [N] páginas. Vou extraí-lo em segundo plano antes de analisar, para não
> estourar o limite da sua conversa. Um instante."

**Documentos adicionais (PCMSO, ASOs, ficha de EPI, AEP/AET):** aplique a mesma régua de
20 páginas a cada um. Os curtos, leia direto; um PCMSO longo pode ser delegado ao mesmo
agente (saída `auditoria-PGRTR/pcmso-extrato.md`), com roteiro restrito ao bloco 5 acima.

#### Analise sobre o extrato

Feita a extração, **a análise das ementas corre sobre o `pgrtr-extrato.md`**, não sobre
o PDF. O extrato traz a transcrição literal e a página de cada trecho, que é o que a
citação obrigatória exige.

Duas regras ao usar o extrato:

- **O extrato não julga.** "LOCALIZADO" ali significa apenas que o documento trata do
  assunto — nunca que o tratamento é adequado. O juízo de cada ementa continua sendo
  seu, sobre as transcrições.
- **Volte ao original quando for decisivo.** Se um ponto ficar limítrofe, ou se o
  extrato registrar incerteza na seção "Limites desta extração", abra **aquelas
  páginas** do PDF com o Read (parâmetro `pages`) antes de concluir. O extrato é o
  padrão; o original continua ao alcance.

Se o extrato apontar páginas sem texto extraível que sustentem alguma ementa,
confira-as visualmente antes de concluir por infração.

**Citação de página:** cite a página do PDF no formato `(pág. X)`, como vem no extrato.
Se o documento trouxer numeração própria impressa ("Folha X/Y", "Página X") divergente
da página física do PDF, cite as duas na análise (`pág. X do PDF / Folha Y`) — o auto
usará a referência que a empresa consegue localizar. Não pergunte nada ao AFT sobre
paginação: resolva pelo que o documento mostra.

---

### Etapa 4: Análise sequencial pela base de ementas (NR-31)

**Princípio da análise sequencial:** percorra a base de ementas fixa (seção "Base de
ementas NR-31" ao final) **uma a uma, na ordem em que aparecem**. Para cada ementa:

1. Leia o `o_que_verificar`, a `situacao_comum_de_nao_conformidade` e a
   `fundamentacao_tecnica_essencial` daquela ementa.
2. Audite o(s) extrato(s)/documento(s) contra esse guia — considere também as respostas
   coletadas na Etapa 2 (CIPATR/SESTR, EPIs) como evidência complementar, especialmente
   para ementas sobre supervisão, comunicação e fornecimento de EPI.
3. **Confronte com o campo** (modo confronto — ver abaixo).
4. Se encontrar evidência (ou omissão) que corresponda à irregularidade descrita,
   registre a não conformidade no formato da Etapa 5.
5. Senão, siga silenciosamente para a próxima ementa. Ao final, se nenhuma ementa
   apontou irregularidade, declare isso explicitamente — nunca force enquadramento.

#### Confronto obrigatório campo x PGRTR (modo confronto)

No modo confronto, **cada achado de campo da Etapa 1 deve ser rastreado contra o
PGRTR** antes de fechar cada ementa. Use este mapeamento como roteiro:

| Achado in loco | Pergunta de confronto | Ementa(s) afetada(s) |
|---|---|---|
| Qualquer risco real observado (agrotóxico, máquina agrícola, animal, calor, poeira, terreno) | O risco está no inventário, com o grupo correspondente? | 231107-0 |
| Risco observado presente mas sem avaliação/gradação | O risco foi avaliado e classificado (severidade x probabilidade)? | 231109-7, 231121-6 |
| Irregularidade concreta que o plano de ação não trata ou trata sem prazo | Há medida com prioridade e cronograma para isso? | 231110-0, 231116-0 |
| EPI como única resposta a risco que admitia proteção coletiva | A hierarquia de controle foi respeitada/justificada? | 231111-9 |
| Proteção existente removida/degradada, controle abandonado | O PGRTR prevê acompanhamento dos controles? | 231112-7 |
| Condições precárias de vivência, refeição, ferramenta, conforto | O dever geral de condições/higiene/conforto está cumprido? | 231084-8 |
| Trabalhador sem orientação/supervisão perceptível em campo | Há instrução compreensível e supervisão? Trabalhadores conhecem os riscos? | 231086-4, 231106-2 |
| Manejo de animais improvisado, sem contenção/imunização | O PGRTR traz medidas para trabalho com animais? | 231124-0 |
| Trabalho sob intempérie/calor extremo sem regra de parada | Há procedimento para condições climáticas extremas e organização do esforço? | 231125-9, 231126-7 |
| Tráfego interno perigoso, resíduos acumulados, rede elétrica sobre lavoura | O PGRTR trata trânsito interno, resíduos, faixas de linha elétrica? | 231127-5, 231128-3, 231129-1 |
| Acidente/doença ocorrido sem investigação | Há procedimento e registros de análise de acidentes? | 231085-6, 231113-5 |
| ASO vencido/ausente relatado ou constatado | Os exames do 31.3.7 estão em dia? | 231131-3 a 231135-6 |

**Regra de ouro:** se um risco existe de fato no estabelecimento (você o viu) e o PGRTR
não o identifica, não o avalia ou não o trata, a ausência é evidência **positiva** de
irregularidade — mais forte do que uma lacuna meramente documental. Cite o achado de
campo como elemento de convicção ao lado do trecho (ou da ausência) no PGRTR.

**Achados sem correspondência na base de ementas:** alguns achados de campo são
infrações autônomas de outros itens da NR-31 ou de outras NRs e não dizem respeito ao
conteúdo do PGRTR. Esta skill é especialista em **PGRTR/NR-31 (gestão de riscos e saúde
ocupacional rural) e permanece estritamente nesse escopo** — não enquadra, não comenta e
não gera autos fora dele (para isso, use `/aft-auditoria-geral`). Use esses achados
apenas, quando couber, como contexto de que o ambiente tem riscos relevantes que o PGRTR
deveria refletir.

**Análise do PCMSO dentro do PGRTR (item 31.3.7):** se um arquivo de PCMSO for
fornecido, analise-o especificamente em relação às ementas 231131-3 a 231138-0 (exames
admissional, periódico, retorno, mudança de risco, demissional, complementares). Se o
PCMSO não for fornecido, verifique se o próprio PGRTR contempla essa temática antes de
declarar omissão.

**Princípio da análise exaustiva:** a primeira resposta com a auditoria já deve ser o
produto final e completo — nunca entregue um relatório parcial ou preliminar. Percorra
**todas** as ementas da base antes de compilar e apresentar o relatório.

#### Etapa 4.5: Consulta complementar ao ementário oficial

Depois de concluir a análise pela base fixa, faça **uma consulta complementar** ao
ementário oficial para checar se existe alguma ementa de NR-31 relevante ao caso
concreto que não esteja na base fixa. Escreva a pergunta num arquivo (evita problema de
acento no shell), descrevendo em 1-2 frases a situação de fato mais relevante encontrada
na auditoria que não teve correspondência exata na base fixa, e consulte pelo script do
toolkit (nunca fixe ID de notebook):

```bash
python ~/.claude/skills/_scripts/notebooklm_consulta.py nr-31 --prompt-file pergunta.txt
```

Se precisar de cobertura mais ampla, some uma consulta à key `ementario-sst`. Se a
consulta apontar uma ementa fora da base fixa, **nunca a use silenciosamente**:
apresente ao AFT como achado adicional ("A base fixa desta skill não cobre isso, mas o
ementário oficial aponta a ementa <código> para esta situação — confirma o uso?") e só
inclua no relatório após confirmação. Se o NotebookLM não estiver configurado ou não
responder, avise em uma linha e siga só com a base fixa (não é bloqueante).

---

### Etapa 5: Registro, consolidação e salvamento

Cada não conformidade encontrada na Etapa 4 é registrada assim:

```
### Ementa [código] - [descrição da ementa]

Situação: Não Conforme

Confronto com o campo: [achado in loco relevante e como ele sustenta ou afasta a
irregularidade; ou "sem achado de campo aplicável" / "modo documental — não aplicável"]

Evidência (trecho do documento analisado): [cite o trecho exato que comprova a
irregularidade; se for omissão, declare: "Omissão: o documento [nome] não aborda ou
não contém o requisito obrigatório referente a esta ementa"]
Localização no documento: [página(s), no formato da Etapa 3, ou justificativa da
omissão]

Requisito normativo: [item/subitem da NR-31 descumprido, conforme a capitulação legal
da ementa]

Fundamentação técnica: [explicação de por que a evidência/omissão constitui não
conformidade, baseada na fundamentação técnica essencial da ementa]
```

Quando o documento atender ao requisito de uma ementa, **não a inclua no relatório**
(silêncio = conforme).

Compile todas as não conformidades num único relatório, com cabeçalho:

```
# Relatório de Auditoria do PGRTR — <EMPREGADOR RURAL>

CNPJ/CPF: <identificador>
Fazenda/propriedade: <nome> — coordenadas: <se houver>
Atividade desenvolvida: <atividade>
Profissional que elaborou o PGRTR: <nome, formação, registro — conforme consta no documento>
Período de vigência: <datas, se constarem>
Data de início da fiscalização: <data>
Notificação (NAD): <código, se houver>
CIPATR/SESTR: <resposta>
EPIs fornecidos: <resposta>
Modo da análise: <confronto com inspeção física de dd/mm/aaaa | documental>
Documentos analisados: <lista>
```

Se, após percorrer todas as ementas (fixas + eventual complemento do ementário
confirmado), nenhuma não conformidade for encontrada, declare isso claramente no lugar
das seções de ementa.

Salve o relatório completo em `<OS_ATIVAS>/[PASTA_EMPRESA]/auditoria-PGRTR/analise-PGRTR.md`.
Se o arquivo já existir de uma análise anterior, faça backup antes de sobrescrever:

```bash
python ~/.claude/skills/_scripts/backup_arquivo.py "<OS_ATIVAS>/[PASTA_EMPRESA]/auditoria-PGRTR/analise-PGRTR.md"
```

---

## Pós-análise: ofertas ao AFT

Ao terminar, faça uma pergunta única:

> "Deseja que eu (1) redija os autos de infração das ementas não conformes (formato
> pronto para o `/aft-gera-ai`, com o PGRTR como anexo), (2) escreva uma carta de
> recomendação geral para envio ao produtor rural, ou (3) ambos?"

### 1) Redação dos autos de infração (formato /aft-gera-ai)

Para cada ementa não conforme, gere um bloco no formato consumido pelo `/aft-gera-ai`.
A linha `Ementa:` usa o código com hífen exatamente como está na base (ex.: `231105-4`)
— o `/aft-gera-ai` remove o hífen no cod_3.

```
=== AUTO DE INFRAÇÃO #[N] ===
Ementa: [código com hífen, ex: 231105-4] - [descrição curta da ementa]

I - DA FISCALIZAÇÃO:

Trata-se de fiscalização mista, realizada nos termos do art. 30, § 3º,
do Decreto nº 4.552/2002, iniciada em [data_inspecao] no estabelecimento
rural do empregador acima qualificado, localizado na Fazenda
[nome_fazenda][, coordenadas [coordenadas_gps]], que desenvolve a
atividade de [atividade_desenvolvida].

II - IRREGULARIDADE:

[Conteúdo específico da ementa, com base na análise — ver regras abaixo]

ELEMENTOS DE CONVICÇÃO:
Análise documental do PGRTR apresentado pelo AUTUADO[, elaborado por
<nome/profissão/registro do responsável técnico>][; PCMSO apresentado][;
Atestados de Saúde Ocupacional apresentados][; Ficha de Fornecimento de
EPI apresentada]; inspeção in loco.
```

> **Não escreva o Subtítulo 3 (OBSERVAÇÕES).** Ele é único, fixo e injetado pelo
> `/aft-gera-ai` (de `config/blocos_auto.md`) entre o Subtítulo 2 e os ELEMENTOS DE
> CONVICÇÃO. O template termina, de propósito, no Subtítulo 2 + ELEMENTOS DE CONVICÇÃO.

**Regras de redação do subtítulo 2:**

- **Estruture em parágrafos temáticos — nunca em um bloco único.** Separe com linha em
  branco: um parágrafo para o enquadramento normativo (conduta + item da NR-31 violado,
  com a fundamentação técnica essencial da ementa como base), um parágrafo por **grupo
  temático de constatações relacionadas** (incorpore as citações de página da análise e,
  no modo confronto, o achado de campo correspondente), e a conclusão jurídica e o
  parágrafo de dano coletivo sempre isolados, cada um no seu próprio parágrafo, nesta
  ordem: conclusão jurídica logo após o enquadramento; dano coletivo fechando o bloco. A
  linha em branco no `autos-pgrtr.md` é o que o `/aft-gera-ai` converte em quebra de
  linha real (`#13#10`) no Sistema Auditor — um bloco II sem nenhuma quebra interna sai
  como um único parágrafo gigante e ilegível. Alvo prático: 3 a 6 parágrafos.
- Descreva os **fatos concretos** com precisão técnica e tom oficial.
- Cite o **dispositivo da NR-31** violado (item exato e a capitulação da ementa, com o
  art. 18 da Lei nº 5.889/73).
- Cite o **profissional responsável pelo PGRTR** (nome, formação, registro — ex.:
  "Engenheiro de Segurança do Trabalho, CREA/UF 9999") quando constar no documento.
- **Incorpore as citações de página** geradas na análise (`pág. X`). Não economize
  palavras: a empresa precisa localizar cada evidência citada.
- **Conclusão jurídica logo após o enquadramento normativo** (parágrafo próprio):
  *"Sendo assim, incorreu o empregador na infração ementada supracitada."*
- Feche o bloco II com o **parágrafo de dano coletivo** (PGRTR é SST), último parágrafo
  antes de ELEMENTOS DE CONVICÇÃO. Texto canônico:

```
Dano de natureza coletiva. Conforme a Portaria MTP nº 667/2021, a citação
nominal do empregado só é necessária quando imprescindível à
caracterização da infração ou quando a multa se baseia no quantitativo
de trabalhadores prejudicados. Nas infrações que atingem a coletividade,
tais como as relativas ao meio ambiente de trabalho (SST), dispensa-se a
individualização, dado o caráter difuso ou coletivo do bem jurídico
tutelado (Orientação Técnica SIT nº 2/2022). Contudo, citam-se como
exemplos de trabalhadores prejudicados [NOME 1], [função], e [NOME 2],
[função].
```

  **Exemplo de trabalhador prejudicado (frase final "Contudo, ..."):** se o contexto da
  fiscalização (inspeção física, narrativa do AFT) identificar trabalhador exposto, cite
  esse(s). Senão, procure na pasta da OS uma relação de vínculos ativos (ex.:
  `ImprimirVinculosAtivos*.pdf`) e cite **pelo menos dois** empregados com função
  compatível com a exposição. Nome em capitalização normal, podendo abreviar (primeiro
  nome + um sobrenome); função em minúsculas; **nunca cite CPF**. Com um só nome, use o
  singular ("cita-se como exemplo de trabalhador prejudicado..."). Sem nenhum nome
  disponível (exceção), encerre em "...(Orientação Técnica SIT nº 2/2022).", sem a
  frase final.
- **Dado de saúde individualizado nunca entra no auto.** Quando a evidência vier de
  ASO, prontuário ou monitoramento biológico, descreva por função/setor ("operador de
  motosserra do setor de silvicultura"), sem nome, sem CPF e sem dado clínico
  individual — o exemplo nominal do parágrafo de dano coletivo vem da relação de
  vínculos/da exposição, nunca do dado clínico.
- Tom: sóbrio, formal, impessoal, terceira pessoa. Sem travessões.
- **Acentuação completa e obrigatória.** Escreva o subtítulo 2 em português com TODOS
  os acentos (ç ã õ á é í ó ú â ê ô à). O TXT final do Sistema Auditor é gravado em
  ISO-8859-1 (latin-1), que **suporta todos os acentos do português** — acento não é
  problema de encoding e **jamais** deve ser removido. O que o latin-1 não aceita é
  apenas travessão (—), aspas curvas e emojis.
- O subtítulo 3 é **fixo e literal** — não altere. O parágrafo de dano coletivo é
  imutável — reproduza-o literalmente.
- Autos de PGRTR não levam trabalhadores nominados nas **linhas tipo 4** do TXT
  (infração coletiva) — o exemplo de trabalhador prejudicado do parágrafo de dano
  coletivo é só texto do bloco II, não gera linha tipo 4.

**Salvar e handoff:** salve todos os blocos em
`<OS_ATIVAS>/[PASTA_EMPRESA]/auditoria-PGRTR/autos-pgrtr.md` e exiba:

```
✅ N autos de PGRTR redigidos — salvos em auditoria-PGRTR/autos-pgrtr.md

▶ Próximo passo — empacotar no TXT do Sistema Auditor:
  1) Rode /aft-gera-ai e responda que os autos estão (b) na sessão.
  2) Quando ele tratar de anexos, informe o(s) PDF(s) do PGRTR/PCMSO/ASOs como
     documentos prontos.
  3) O limite de 10 MB é por auto (soma dos anexos daquele auto) — se o documento não
     couber em todos, o /aft-gera-ai comprime com o script do toolkit.
```

### 2) Carta de recomendação geral para o produtor rural

Quando solicitado, redija um texto resumido, dirigido ao empregador rural, no formato:

```
RELATÓRIO DE RECOMENDAÇÃO PARA ADEQUAÇÃO DO PGRTR
À [Nome da Empresa/Propriedade]
Assunto: Recomendações para Adequação do Programa de Gerenciamento de Riscos do
Trabalho Rural (PGRTR) à NR-31.

Prezados,

Em recente análise documental do PGRTR deste(a) empregador(a), foram identificadas
oportunidades de melhoria e pontos de não conformidade com a Norma Regulamentadora 31.

Os principais problemas encontrados incluem, mas não se limitam a:
[3 a 5 pontos principais, resumindo as irregularidades de forma geral]

A manutenção de um PGRTR completo e em conformidade com a legislação é fundamental
para a prevenção de acidentes e doenças ocupacionais e para a promoção de um ambiente
de trabalho seguro e saudável.

Diante do exposto, recomenda-se que o empregador busque assessoria técnica
especializada para realizar uma revisão completa do seu Programa de Gerenciamento de
Riscos do Trabalho Rural, a fim de sanar as irregularidades apontadas e garantir o
pleno atendimento aos requisitos da NR-31 e demais normas aplicáveis.

Atenciosamente,
[Nome do Auditor-Fiscal do Trabalho]
```

Tom técnico, direto, sem linguagem jurídica de auto — o destinatário é o empregador
rural. Salve como `auditoria-PGRTR/recomendacao-geral-PGRTR.md` na pasta da OS.

---

## Registro no memory.md e diário

Depois de qualquer etapa que produza resultado (análise concluída, autos redigidos,
recomendação escrita), atualize o `memory.md` da OS:

- Se autos foram redigidos: acrescente uma seção em `## Autos de Infração` (mesmo
  padrão usado pelas demais skills de lavratura — data, arquivo gerado, ementas,
  elementos de convicção).
- Sempre: registre a auditoria na seção `## Auditoria de documentos` (nas OS anteriores
  à renomeação ela se chama `## Anotações da auditoria`: escreva na que existir, sem
  renomeá-la; se nenhuma existir, crie `## Auditoria de documentos`), acrescentando ao
  **final da seção** uma subseção `### PGRTR` (se ainda não houver) e, nela, uma linha
  datada:

  ```
  ### PGRTR
  dd/mm/aaaa — <resumo em até 2 linhas: quantas ementas não conformes, se autos foram
  redigidos> — relatório: auditoria-PGRTR/analise-PGRTR.md
  ```

  Três regras do registro: (1) é **prosa** — nunca comece a linha com `-`: na seção,
  bullet é constatação avulsa que a `/aft-auditoria-geral` transforma em auto, e o
  resumo não é uma constatação; (2) **até 2 linhas** por análise — o detalhe fica no
  relatório e não se repete no memory.md; (3) análise nova do mesmo tema acrescenta
  outra linha datada na mesma subseção, mantendo as anteriores.

Ao final, registre o dia trabalhado no diário — sem perguntar nada ao AFT (o script
deduplica por data+letra; repetir é inofensivo):

```bash
python ~/.claude/skills/_scripts/diario_registrar.py "<pasta da OS>" --tipos D --detalhe "via /aft-PGRTR-analise"
```

---

## Regras gerais

- Texto técnico, oficial, em terceira pessoa. Sem informalidades.
- **Acentuação completa** (ç ã õ á é í ó ú â ê ô à). Nunca remova acentos: o latin-1 do
  TXT final os suporta integralmente.
- **Não usar travessões** (—), aspas curvas nem emojis em texto destinado ao Sistema
  Auditor. Substitua por dois pontos, vírgulas, parênteses ou hífen simples.
- **Não invente dados.** Se uma informação não estiver no documento, declare a
  ausência. Não force enquadramento: se a ementa não estiver presente com base no
  documento, declare isso explicitamente.
- **Nunca use ementa fora da base fixa** sem antes consultar o ementário (Etapa 4.5) e
  confirmar com o AFT.
- **Privacidade de dados de saúde:** PCMSO, ASOs e prontuários contêm dados sensíveis
  de saúde do trabalhador. Nunca ecoe CPF ou dado clínico individualizado no chat, no
  relatório ou no `memory.md` — refira-se por função/setor, ou pelo token `[[TRAB_NN]]`
  se a OS já tiver mapa de-para. Isso vale mesmo quando a evidência vem de um ASO ou
  entrevista específica.
- **Denunciante/entrevista de trabalhador em campo:** se a evidência vier de entrevista
  com trabalhador (ex.: ementa 231086-4, sobre orientação e supervisão), nunca cite o
  nome do entrevistado — refira-se como "trabalhador(es) entrevistado(s) em campo".
- Mantenha a separação entre ementas: não misture irregularidades de uma ementa na
  análise de outra.
- Os textos fixos (parágrafo de dano coletivo, subtítulo 3) são imutáveis. Reproduza-os
  literalmente quando aplicáveis.

---

## Base de ementas NR-31 (fixa)

> Base curada a partir do prompt "Analista de PGRTR" validado em uso real por AFT.
> Códigos, capitulações e gradações conferidos contra o ementário oficial (NotebookLM,
> key nr-31) em 24/08/2026. Os títulos são resumos de trabalho; o texto literal da
> ementa vem sempre do ementário na hora do auto. Percorra a base sequencialmente na
> Etapa 4. Não edite estas ementas sem o AFT pedir.

### 231086-4 — Deixar de assegurar instruções compreensíveis, direitos/deveres e supervisão ao trabalho seguro
**Capitulação legal:** Art. 18 da Lei nº 5.889/73 c/c item 31.2.3, alínea "c", da NR-31, com redação da Portaria SEPRT/ME nº 22.677, de 22/10/2020.
**Gradação:** I3
**O que verificar:**
- Verificar se existem registros de treinamentos, ordens de serviço ou informativos de segurança fornecidos aos trabalhadores em linguagem clara, simples e adaptada ao nível de escolaridade do público-alvo.
- Entrevistar os trabalhadores em campo para confirmar se receberam orientações sobre seus direitos, deveres, riscos ocupacionais específicos e medidas de proteção recomendadas.
- Observar in loco se há supervisores, encarregados ou técnicos orientando e acompanhando diretamente a execução das atividades cotidianas para garantir práticas seguras de trabalho.
**Situação comum de não conformidade:** Trabalhadores safristas são integrados diretamente à colheita manual sem receber qualquer treinamento prévio ou material informativo em linguagem acessível sobre os riscos das ferramentas cortantes e posturas ergonômicas, atuando sem qualquer monitoramento ou supervisão em campo.
**Fundamentação técnica essencial:** O fornecimento de instruções compreensíveis e a supervisão contínua são as bases de uma cultura preventiva eficaz. No meio rural, a ausência de diretrizes claras e o abandono operacional dos trabalhadores potencializam acidentes severos, visto que a percepção do risco individual é insuficiente sem o suporte instrutivo e o monitoramento técnico da chefia.

### 231084-8 — Deixar de cumprir/fazer cumprir disposições de SST rural garantindo condições, higiene e conforto adequados
**Capitulação legal:** Art. 18 da Lei nº 5.889/73 c/c item 31.2.3, alínea "a", da NR-31, com redação da Portaria SEPRT nº 22.677, de 22/10/2020.
**Gradação:** I3
**O que verificar:**
- Inspecionar as frentes de trabalho rurais, verificando se máquinas, tratores e ferramentas manuais apresentam as devidas proteções físicas e condições mecânicas seguras de operação.
- Avaliar as instalações de vivência, sanitários de frente de trabalho e áreas de refeição quanto aos critérios mínimos de higiene, conforto térmico e proteção contra intempéries.
- Analisar se o PGRTR está implementado na prática e se as medidas mitigadoras listadas no cronograma foram efetivamente executadas.
**Situação comum de não conformidade:** O estabelecimento rural mantém trabalhadores em frentes de trabalho distantes realizando suas refeições sentados no chão, sob sol pleno, sem abrigos ou mesas disponíveis, além de permitir o uso de ferramentas desgastadas e sem manutenção protetiva.
**Fundamentação técnica essencial:** Esta alínea constitui o dever geral de prevenção e tutela patronal em SST no ambiente rural. Negligenciar as condições básicas de higiene, conforto e proteção mecânica agride diretamente a integridade física e a dignidade humana do trabalhador, consolidando cenários propícios ao adoecimento crônico e a sinistros graves.

### 231085-6 — Deixar de adotar procedimentos e análise de causas quando da ocorrência de acidentes/doenças do trabalho
**Capitulação legal:** Art. 18 da Lei nº 5.889/73 c/c item 31.2.3, alínea "b", da NR-31, com redação da Portaria SEPRT/ME nº 22.677, de 22/10/2020.
**Gradação:** I4
**O que verificar:**
- Solicitar o livro, sistema ou relatórios formais de investigação e análise de acidentes e doenças ocupacionais ocorridos no estabelecimento rural nos últimos 12 meses.
- Verificar se os relatórios analíticos identificaram detalhadamente os fatores causais (raiz) estruturais, humanos ou de maquinário, indo além da mera descrição do fato.
- Verificar se as recomendações e contramedidas dessas análises foram integradas ao plano de ação do PGRTR e efetivamente colocadas em prática.
**Situação comum de não conformidade:** Após um acidente grave com tombamento de trator agrícola que feriu o operador, a empresa limita-se a emitir a CAT eletrônica e prestar socorro hospitalar, sem realizar qualquer investigação interna ou mapeamento de falhas.
**Fundamentação técnica essencial:** A análise pós-evento de acidentes e agravos à saúde é ferramenta indispensável para retroalimentar o sistema de gestão de riscos. Tratar os sinistros com passividade perpetua falhas latentes e condena o empreendimento à reincidência sob as mesmas causas.

### 231105-4 — Deixar de elaborar/implementar/custear o PGRTR
**Capitulação legal:** Art. 18 da Lei nº 5.889/73 c/c item 31.3.1 da NR-31, com redação da Portaria SEPRT nº 22.677, de 22/10/2020.
**Gradação:** I4
**O que verificar:**
- Solicitar o documento físico ou digital do PGRTR específico para o estabelecimento rural avaliado.
- Verificar se o programa contempla o inventário de riscos completo e o plano de ação com cronograma de execução, cobrando evidências de que as medidas propostas foram implantadas.
- Para estabelecimentos com até 50 empregados, verificar se o empregador optou pela ferramenta digital oficial da SEPRT e se gerou o relatório metodológico correspondente.
- Confirmar se todos os custos de elaboração e execução do programa foram assumidos integralmente pelo empregador.
**Situação comum de não conformidade:** O produtor rural possui fazenda com 65 funcionários registrados e não apresenta nenhum documento de gestão de riscos de SST, alegando usar um PGR geral unificado de outra empresa do grupo ou que os custos inviabilizariam a safra.
**Fundamentação técnica essencial:** O PGRTR é a espinha dorsal da gestão de SST no meio rural. A ausência, falta de implementação ou repasse de custos desse programa deixa o estabelecimento desprovido de política estruturada de prevenção, operando às cegas frente aos riscos biológicos, físicos, químicos e ergonômicos do campo.

### 231106-2 — Deixar de comunicar trabalhadores sobre riscos do inventário e medidas do plano de ação do PGRTR
**Capitulação legal:** Art. 18 da Lei nº 5.889/73 c/c item 31.3.1.3 da NR-31, com redação da Portaria SEPRT nº 22.677, de 22/10/2020.
**Gradação:** I3
**O que verificar:**
- Buscar evidências documentais de que os trabalhadores foram formalmente cientificados sobre os riscos do inventário (atas de integração, listas de presença, termos de ciência assinados).
- Entrevistar amostra de trabalhadores em campo sobre se conhecem os riscos de suas funções e as medidas de prevenção do plano de ação do PGRTR.
- Verificar existência de sinalizações, quadros informativos ou cartilhas acessíveis nas frentes de trabalho expondo as diretrizes do PGRTR.
**Situação comum de não conformidade:** A fazenda possui PGRTR robusto elaborado por consultoria técnica, mas o documento fica arquivado na gaveta da administração e nenhum tratorista/operador foi informado sobre os riscos ergonômicos e químicos mapeados para suas rotinas.
**Fundamentação técnica essencial:** A gestão de riscos só se torna efetiva quando o executor compreende o perigo ao qual está exposto e a utilidade das defesas implementadas. Falhar na transmissão das informações anula o propósito preventivo do programa, transformando-o em burocracia.

### 231145-3 — Deixar de emitir CAT quando constatada doença ocupacional ou alteração biológica com significado clínico
**Capitulação legal:** Art. 18 da Lei nº 5.889/73 c/c item 31.3.11, alínea "a", da NR-31, com redação da Portaria SEPRT nº 22.677, de 22/10/2020.
**Gradação:** I4
**O que verificar:**
- Cruzar relatórios médicos de exames complementares e resultados de monitoramento biológico com o histórico de emissão de CATs da empresa.
- Verificar em prontuários/relatórios do médico coordenador se há diagnósticos, agravos ou indicadores biológicos alterados que não geraram abertura de CAT no prazo legal.
- Avaliar se o monitoramento biológico de expostos a defensivos agrícolas ou poeiras vegetais apresentou desvios críticos reportados via CAT.
**Situação comum de não conformidade:** Exames periódicos de aplicadores de defensivos agrícolas indicam redução severa da colinesterase plasmática; o laboratório alerta a alteração crônica, mas a empresa não emite CAT sob o argumento de os trabalhadores estarem assintomáticos.
**Fundamentação técnica essencial:** A emissão da CAT diante de doenças do trabalho ou alterações biológicas significativas cumpre função de vigilância epidemiológica e proteção jurídica. Sua ausência mascara falhas graves de proteção e retarda a intervenção precoce.

### 231146-1 — Deixar de afastar o trabalhador da exposição quando constatada doença ocupacional ou alteração biológica clínica
**Capitulação legal:** Art. 18 da Lei nº 5.889/73 c/c item 31.3.11, alínea "b", da NR-31, com redação da Portaria SEPRT nº 22.677, de 22/10/2020.
**Gradação:** I4
**O que verificar:**
- Identificar, pelo controle médico, quais colaboradores apresentaram piora em exames clínicos/complementares ou monitoramento de indicadores biológicos.
- Verificar se os trabalhadores identificados continuam exercendo as mesmas atividades ou permanecem expostos ao agente agressor.
- Verificar se há ordens de serviço, relatórios de remanejamento ou laudos médicos que comprovem o afastamento imediato.
**Situação comum de não conformidade:** Um operador de motosserra apresenta agravamento severo de PAIR; apesar da restrição médica recomendando afastamento do ruído, a gerência o mantém na mesma função por falta de mão de obra.
**Fundamentação técnica essencial:** Manter um trabalhador exposto a agente que já demonstrou desestabilizar seus indicadores biológicos acelera a evolução da patologia. O afastamento imediato é bloqueio emergencial obrigatório.

### 231147-0 — Deixar de encaminhar o trabalhador à Previdência Social quando constatada doença ocupacional ou alteração biológica clínica
**Capitulação legal:** Art. 18 da Lei nº 5.889/73 c/c item 31.3.11, alínea "c", da NR-31, com redação da Portaria SEPRT nº 22.677, de 22/10/2020.
**Gradação:** I4
**O que verificar:**
- Verificar comprovantes de agendamento de perícia junto ao INSS e guias de encaminhamento previdenciário.
- Cruzar dados de empregados com agravamentos detectados nos exames com a documentação de suporte pericial enviada ao órgão oficial.
- Analisar se a empresa forneceu tempestivamente laudos, relatórios ambientais e informações exigidas pela Previdência para a avaliação técnica.
**Situação comum de não conformidade:** Um trabalhador rural desenvolve LER/DORT na colheita manual; o serviço médico constata o nexo, mas a administração o afasta só informalmente, sem encaminhá-lo à Previdência Social.
**Fundamentação técnica essencial:** O encaminhamento formal assegura ao trabalhador o direito de ter sua capacidade avaliada oficialmente, com reconhecimento do nexo e acesso aos benefícios. Omitir esse trâmite desampara o indivíduo.

### 231148-8 — Deixar de possibilitar acesso aos órgãos de saúde para profilaxia de doenças endêmicas ou vacinação
**Capitulação legal:** Art. 18 da Lei nº 5.889/73 c/c item 31.3.12, alíneas "a" e "b", da NR-31, com redação da Portaria SEPRT nº 22.677, de 22/10/2020.
**Gradação:** I3
**O que verificar:**
- Verificar se o empregador concede dispensa justificada, flexibilidade de horários ou transporte para comparecimento a postos de saúde para imunização e tratamentos preventivos.
- Verificar cartões de vacinação/prontuários quanto à regularidade de vacinas essenciais ao meio rural (antitetânica, febre amarela, hepatite B).
- Entrevistar trabalhadores para checar se há impedimentos, punições ou descontos salariais quando precisam se afastar para vacinação/profilaxia.
**Situação comum de não conformidade:** Propriedade em região de alta incidência de febre amarela impede que trabalhadores se ausentem durante o expediente para atualizar vacinação contra tétano e endemias, sob ameaça de desconto do dia.
**Fundamentação técnica essencial:** O trabalhador rural está em constante exposição a riscos biológicos agressivos. Facilitar o acesso à imunização e ações preventivas do sistema público de saúde é barreira imunológica elementar contra infecções agudas fatais e endemias.

### 231107-0 — Deixar de contemplar no PGRTR os riscos químicos/físicos/biológicos/de acidentes/ergonômicos
**Capitulação legal:** Art. 18 da Lei nº 5.889/73 c/c item 31.3.2 da NR-31, com redação da Portaria SEPRT nº 22.677, de 22/10/2020.
**Gradação:** I3
**O que verificar:**
- Analisar o inventário de riscos do PGRTR para confirmar se os cinco grupos de perigos (físicos, químicos, biológicos, ergonômicos e de acidentes) foram mapeados.
- Inspecionar rotinas de campo (aplicação de agrotóxicos, operação de tratores, colheita manual) e confrontar se riscos manifestos (calor, poeira orgânica, vibração, posturas forçadas, ferramentas afiadas) foram omitidos.
- Avaliar se a abrangência do PGRTR cobre todas as funções e etapas produtivas, sem lacunas setoriais.
**Situação comum de não conformidade:** O PGRTR de uma fazenda produtora de grãos lista só riscos de acidentes com maquinário, ignorando ruído/vibração (físicos), névoa de defensivos (químicos) e esforço repetitivo na carga de sacarias (ergonômicos).
**Fundamentação técnica essencial:** A ausência de qualquer dimensão de risco invalida a integridade do diagnóstico de segurança. Riscos não catalogados são perigos invisíveis à gestão, impedindo salvaguardas e deixando trabalhadores vulneráveis.

### 231108-9 — Deixar de incluir no PGRTR o levantamento preliminar de perigos ou sua eliminação, quando possível
**Capitulação legal:** Art. 18 da Lei nº 5.889/73 c/c item 31.3.3, alínea "a", da NR-31, com redação da Portaria SEPRT nº 22.677, de 22/10/2020.
**Gradação:** I3
**O que verificar:**
- Verificar no PGRTR a existência de registros, relatórios ou planilhas que evidenciem a fase de levantamento preliminar de perigos.
- Buscar evidências de que a empresa estudou alternativas de engenharia/processo para eliminação imediata de perigos antes da avaliação detalhada.
- Confirmar se o levantamento preliminar considerou histórico de acidentes, quase-acidentes e percepções dos trabalhadores.
**Situação comum de não conformidade:** A consultoria elabora o PGRTR iniciando direto nas medições quantitativas e matrizes de risco, sem documento que ateste o mapeamento macro e triagem inicial para eliminação na fonte.
**Fundamentação técnica essencial:** O levantamento preliminar é a triagem da gestão preventiva. Negligenciá-lo viola a hierarquia fundamental de segurança: eliminar o perigo antecede monitorá-lo ou mitigá-lo.

### 231109-7 — Deixar de incluir no PGRTR a avaliação dos riscos que não puderam ser completamente eliminados
**Capitulação legal:** Art. 18 da Lei nº 5.889/73 c/c item 31.3.3, alínea "b", da NR-31, com redação da Portaria SEPRT nº 22.677, de 22/10/2020.
**Gradação:** I3
**O que verificar:**
- Examinar as matrizes de risco do PGRTR, certificando-se de que os riscos residuais passaram por avaliação estruturada.
- Verificar se a metodologia aplicou critérios claros para cruzar severidade das lesões com probabilidade de ocorrência.
- Checar se os resultados classificaram o nível de criticidade para subsidiar a ordem de urgência das intervenções.
**Situação comum de não conformidade:** O PGRTR enumera perigos inevitáveis na lida com gado bovino (coices, prensamentos), mas omite classificação/gradação, impossibilitando priorizar riscos.
**Fundamentação técnica essencial:** A avaliação dos riscos residuais dimensiona a magnitude real das ameaças. Sem qualificar severidade e probabilidade, a empresa não consegue planejar proteções proporcionais.

### 231110-0 — Deixar de incluir no PGRTR medidas de prevenção com prioridades e cronograma
**Capitulação legal:** Art. 18 da Lei nº 5.889/73 c/c item 31.3.3, alínea "c", da NR-31, com redação da Portaria SEPRT nº 22.677, de 22/10/2020.
**Gradação:** I3
**O que verificar:**
- Inspecionar o Plano de Ação do PGRTR e atestar existência de medidas de engenharia, administrativas ou de EPI propostas.
- Verificar se as medidas estão vinculadas a ordem de prioridade técnica e cronograma físico detalhado.
- Exigir datas explícitas para cada ação preventiva, descartando termos vagos como "contínuo" ou "quando necessário".
**Situação comum de não conformidade:** O PGRTR contém inventário detalhado de riscos ergonômicos na colheita de café, mas o plano de ação traz só orientações teóricas abertas, sem prazos ou prioridades.
**Fundamentação técnica essencial:** O estabelecimento de medidas com cronogramas converte o diagnóstico em ações tangíveis. A falta de prazos anula a evolução dinâmica do programa, tornando-o cartorial.

### 231111-9 — Deixar de incluir no PGRTR a implementação das medidas conforme ordem de prioridade (hierarquia de controle)
**Capitulação legal:** Art. 18 da Lei nº 5.889/73 c/c item 31.3.3, alínea "d", da NR-31, com redação da Portaria SEPRT nº 22.677, de 22/10/2020.
**Gradação:** I3
**O que verificar:**
- Verificar se a implementação segue a ordem de prioridade normativa: eliminação na fonte, proteção coletiva, medidas administrativas, e por último EPI.
- Analisar justificativas técnicas quando a empresa optou diretamente por EPI, checando comprovação de inviabilidade das medidas coletivas.
- Confrontar cronograma de execução com ações de campo para garantir que barreiras coletivas antecedam/justifiquem o EPI.
**Situação comum de não conformidade:** Em vez de isolar acusticamente uma casa de bombas, o produtor adota de imediato protetores auriculares como primeira e única medida.
**Fundamentação técnica essencial:** A hierarquia de controle visa mitigar o perigo na origem, evitando transferir toda responsabilidade ao trabalhador. Barreiras coletivas protegem continuamente; EPI tem maior taxa de falha.

### 231112-7 — Deixar de incluir no PGRTR a etapa de acompanhamento do controle dos riscos
**Capitulação legal:** Art. 18 da Lei nº 5.889/73 c/c item 31.3.3, alínea "e", da NR-31, com redação da Portaria SEPRT nº 22.677, de 22/10/2020.
**Gradação:** I3
**O que verificar:**
- Buscar no PGRTR a descrição do método e periodicidade das inspeções para verificar se as medidas de controle continuam ativas e eficazes.
- Solicitar evidências (relatórios de vistoria, checklists, auditorias internas) de acompanhamento sistemático.
- Verificar gatilhos de revisão quando houver mudanças de processo, novas tecnologias ou agravos à saúde.
**Situação comum de não conformidade:** Proteções são instaladas em colhedoras de cana, mas o PGRTR não prevê rotina de checagem; meses depois as proteções são removidas para manutenção e não recolocadas.
**Fundamentação técnica essencial:** O gerenciamento de riscos é um ciclo dinâmico (PDCA). O acompanhamento certifica que os controles não sofram obsolescência ou degradação pelo uso.

### 231113-5 — Deixar de incluir no PGRTR a investigação e análise de acidentes e doenças ocupacionais
**Capitulação legal:** Art. 18 da Lei nº 5.889/73 c/c item 31.3.3, alínea "f", da NR-31, com redação da Portaria SEPRT nº 22.677, de 22/10/2020.
**Gradação:** I4
**O que verificar:**
- Confirmar a existência de procedimento estruturado para investigação de incidentes, acidentes e doenças do trabalho.
- Verificar se as análises de acidentes passados constam documentadas conforme o procedimento previsto, identificando causas estruturais.
- Verificar se o plano de ação é revisado quando uma investigação aponta falhas nas barreiras pré-existentes.
**Situação comum de não conformidade:** O PGRTR tem inventários e planos preventivos detalhados, mas omite qualquer diretriz sobre como investigar causas raiz em caso de acidente ou adoecimento.
**Fundamentação técnica essencial:** Um acidente demonstra empiricamente que as defesas falharam. A etapa de investigação garante que a empresa aprenda com os desvios e implemente correções definitivas.

### 231114-3 — Deixar de adotar os parâmetros dos Anexos da NR-09 para avaliação de exposição a agentes físicos/químicos/biológicos
**Capitulação legal:** Art. 18 da Lei nº 5.889/73 c/c item 31.3.3.1 da NR-31, com redação da Portaria SEPRT nº 22.677/2020, alterada pela Portaria MTP nº 698/2022.
**Gradação:** I3
**O que verificar:**
- Revisar laudos técnicos e avaliações quantitativas anexados ao PGRTR (ruído, calor, vibração, névoas químicas).
- Confrontar metodologias de amostragem, tempos de medição, limites de tolerância e níveis de ação com os anexos da NR-09 e as NHOs da Fundacentro.
- Verificar se os equipamentos de medição têm certificados de calibração válidos e se os dados foram interpretados conforme as equações normativas.
**Situação comum de não conformidade:** A avaliação do calor na colheita manual de cana é feita com termômetros comuns de parede, desconsiderando o cálculo do IBUTG e a taxa metabólica exigidos.
**Fundamentação técnica essencial:** A adoção dos parâmetros da NR-09 garante rigor científico. Avaliações que ignoram os limites oficiais geram laudos nulos, subdimensionando riscos severos.

### 231116-0 — Deixar de documentar o PGRTR com plano de ação
**Capitulação legal:** Art. 18 da Lei nº 5.889/73 c/c item 31.3.3.2, alínea "b", da NR-31, com redação da Portaria SEPRT/ME nº 22.677/2020.
**Gradação:** I3
**O que verificar:**
- Exigir a apresentação documental integral do PGRTR e atestar a presença do "Plano de Ação" como seção/documento formalizado.
- Verificar se o plano elenca explicitamente medidas de prevenção a introduzir/aprimorar/manter, com base nas inconformidades do inventário.
- Confirmar se as ações têm responsáveis designados e prazos de conclusão inteligíveis.
**Situação comum de não conformidade:** O gestor apresenta só o inventário de riscos, sem Plano de Ação, alegando resolver os problemas verbalmente conforme surgem.
**Fundamentação técnica essencial:** O Plano de Ação é o componente operativo do PGRTR. Sem ele, o programa perde poder de execução, virando listagem estática.

### 231121-6 — Deixar de contemplar no inventário a avaliação/classificação de riscos para fins de plano de ação
**Capitulação legal:** Art. 18 da Lei nº 5.889/73 c/c item 31.3.3.2.1, alínea "e", da NR-31, com redação da Portaria SEPRT nº 22.677, de 22/10/2020.
**Gradação:** I3
**O que verificar:**
- Verificar se o inventário adota matriz de risco ou metodologia que associe severidade e probabilidade.
- Checar se há classificação explícita do nível de risco (baixo, médio, alto, crítico) para cada perigo listado.
- Confirmar se essa gradação foi usada para priorizar a ordem de execução das medidas do plano de ação.
**Situação comum de não conformidade:** O produtor apresenta tabela estática de riscos sem cruzá-los em matriz ou atribuir criticidade, listando correções de forma aleatória.
**Fundamentação técnica essencial:** A classificação dos riscos é a inteligência analítica que direciona investimentos de proteção. Sem hierarquizar, o plano de ação perde o critério técnico de urgência.

### 231124-0 — Deixar de estabelecer no PGRTR medidas para trabalhos com animais
**Capitulação legal:** Art. 18 da Lei nº 5.889/73 c/c item 31.3.5, alínea "a", da NR-31, com redação da Portaria SEPRT nº 22.677, de 22/10/2020.
**Gradação:** I3
**O que verificar:**
- Verificar se o PGRTR possui procedimentos, regras de segurança e treinamentos específicos para manejo de animais.
- Solicitar comprovação da carteira de vacinação dos trabalhadores expostos (raiva, brucelose, tétano).
- Inspecionar se estruturas de contenção (troncos, bretes, mangueiros) são seguras e se há descarte adequado de carcaças/secreções/excreções.
**Situação comum de não conformidade:** Vaqueiros realizam vacinação e contenção de gado de forma improvisada, sem bretes adequados, e o empregador não mantém registro de imunização nem rotina para descarte de dejetos.
**Fundamentação técnica essencial:** O trabalho com animais de grande porte combina risco agudo de trauma físico (coices, chifradas) com risco biológico crônico (zoonoses). Protocolos de aproximação e imunização são barreiras indispensáveis.

### 231125-9 — Deixar de estabelecer no PGRTR medidas para condições climáticas extremas
**Capitulação legal:** Art. 18 da Lei nº 5.889/73 c/c item 31.3.5, alínea "b", da NR-31, com redação da Portaria SEPRT nº 22.677/2020, alterada pela Portaria MTP nº 698/2022.
**Gradação:** I3
**O que verificar:**
- Verificar se o PGRTR formaliza diretrizes especificando quais condições meteorológicas (raios, ventania, calor extremo) justificam paralisação das atividades.
- Exigir registros de treinamento sobre rotas de evacuação e abrigos seguros.
- Entrevistar trabalhadores para atestar se conhecem as regras de interrupção e dispõem de autonomia para o direito de recusa.
**Situação comum de não conformidade:** Trabalhadores permanecem cortando cana manualmente sob forte tempestade elétrica, pois a fazenda não possui procedimento instruindo a parada do trabalho.
**Fundamentação técnica essencial:** O ambiente rural aberto é vulnerável a eventos meteorológicos extremos. Definir critérios de interrupção imediata preserva vidas.

### 231126-7 — Deixar de estabelecer no PGRTR medidas de organização do trabalho para esforço físico e terrenos acidentados
**Capitulação legal:** Art. 18 da Lei nº 5.889/73 c/c item 31.3.5, alínea "c", da NR-31, com redação da Portaria SEPRT nº 22.677, de 22/10/2020.
**Gradação:** I3
**O que verificar:**
- Analisar ordens de serviço/programações diárias no PGRTR quanto à adequação de horários de atividades de alta sobrecarga física.
- Cruzar horários de maior incidência de calor com as tarefas de campo, aferindo se atividades pesadas foram alocadas em períodos mais frescos.
- Verificar se o programa estipula controles para trabalho em terrenos acidentados (pausas, técnicas ergonômicas, calçados antiderrapantes).
**Situação comum de não conformidade:** Fazenda de café em montanha exige colheita e carregamento de sacos entre 11h30 e 14h, sob forte calor, sem escala de revezamento ou pausas.
**Fundamentação técnica essencial:** Esforço físico extremo combinado com estresse térmico eleva a taxa de exaustão e desidratação. Terrenos íngremes ampliam o risco de quedas e lesões na coluna.

### 231127-5 — Deixar de estabelecer no PGRTR condições seguras de trânsito interno de trabalhadores e veículos
**Capitulação legal:** Art. 18 da Lei nº 5.889/73 c/c item 31.3.5, alínea "d", da NR-31, com redação da Portaria SEPRT nº 22.677, de 22/10/2020.
**Gradação:** I3
**O que verificar:**
- Verificar existência de regras explícitas de velocidade, fluxo e segregação segura entre máquinas e transeuntes no plano de tráfego interno.
- Inspecionar visualmente a presença de sinalização visível, advertências e indicações de perigo nas vias internas.
- Mapear áreas com relevo crítico (barrancos, pontes, margens de represas) e atestar defesas físicas contra quedas/capotamentos.
**Situação comum de não conformidade:** Caminhões e tratores circulam em alta velocidade por estradas internas de terra que margeiam canais profundos, sem placa de velocidade máxima nem barreira protetora.
**Fundamentação técnica essencial:** A circulação de maquinário pesado combinada ao transporte de pessoas em estradas sem pavimentação apresenta risco severo de colisão e capotamento. Sinalização e isolamento físico são obrigatórios.

### 231128-3 — Deixar de estabelecer no PGRTR medidas para eliminação de resíduos dos processos produtivos
**Capitulação legal:** Art. 18 da Lei nº 5.889/73 c/c item 31.3.5, alínea "e", da NR-31, com redação da Portaria SEPRT nº 22.677, de 22/10/2020.
**Gradação:** I3
**O que verificar:**
- Verificar no PGRTR o plano de gerenciamento, destinação e descarte de resíduos industriais, biológicos e operacionais.
- Inspecionar postos de trabalho, galpões e vivências quanto ao acúmulo inadequado de sucatas cortantes, arames, madeira ou rejeitos orgânicos.
- Confirmar se depósitos temporários de resíduos têm isolamento, sinalização e estão afastados das rotas de circulação.
**Situação comum de não conformidade:** Oficina e pátio de insumos acumulam peças metálicas cortantes, pneus com água parada e embalagens de óleo jogadas nas vias de passagem.
**Fundamentação técnica essencial:** O acúmulo de resíduos degrada condições de ordem e segurança, obstrui passagens, e serve de foco para animais peçonhentos e vetores de doença.

### 231129-1 — Deixar de estabelecer no PGRTR medidas para trabalho em faixa de segurança de linhas de energia elétrica
**Capitulação legal:** Art. 18 da Lei nº 5.889/73 c/c item 31.3.5, alínea "f", da NR-31, com redação da Portaria SEPRT nº 22.677, de 22/10/2020.
**Gradação:** I3
**O que verificar:**
- Verificar se o PGRTR mapeia as linhas de distribuição de energia que cortam a propriedade e estabelece distâncias mínimas de segurança.
- Checar procedimentos escritos orientando operadores de equipamentos de grande porte sobre risco de indução/contato elétrico.
- Inspecionar sinalização de advertência quanto à altura máxima permitida sob redes elétricas.
**Situação comum de não conformidade:** Propriedade com redes de alta tensão cruzando lavouras permite tráfego de colhedoras diretamente sob os cabos, sem o PGRTR mencionar o risco.
**Fundamentação técnica essencial:** A aproximação de maquinário com redes energizadas representa risco crítico de arcos elétricos e eletrocussão. Medidas específicas normatizam rotas seguras e treinamento.

### 231130-5 — Desconsiderar peculiaridades das atividades rurais no planejamento das ações de saúde ocupacional
**Capitulação legal:** Art. 18 da Lei nº 5.889/73 c/c item 31.3.6 da NR-31, com redação da Portaria SEPRT nº 22.677, de 22/10/2020.
**Gradação:** I3
**O que verificar:**
- Confrontar o planejamento de saúde ocupacional com os riscos identificados no inventário do PGRTR.
- Verificar se o plano médico contempla os agravos específicos do ambiente rural (agrotóxicos, poeiras vegetais, zoonoses, intempéries).
- Checar se os exames complementares obrigatórios para funções específicas (toxicologia, espirometria) estão sendo realizados.
**Situação comum de não conformidade:** O médico do trabalho executa monitoramento padronizado e burocrático, sem solicitar controle de indicadores biológicos (colinesterase) para manuseadores semanais de defensivos.
**Fundamentação técnica essencial:** As ações de saúde no meio rural devem ser responsivas aos perigos de campo. Ignorar peculiaridades anula a eficácia da medicina ocupacional.

### 231131-3 — Deixar de garantir a realização de exame médico admissional antes do início das atividades
**Capitulação legal:** Art. 18 da Lei nº 5.889/73 c/c item 31.3.7, alínea "a", da NR-31, com redação da Portaria SEPRT nº 22.677, de 22/10/2020.
**Gradação:** I3
**O que verificar:**
- Cruzar datas de admissão/início efetivo (contrato ou eSocial) com a data de emissão do ASO admissional.
- Verificar se todos os trabalhadores ativos possuem ASO admissional assinado.
- Confirmar se a data do exame é anterior ou concomitante ao primeiro dia trabalhado.
**Situação comum de não conformidade:** Trabalhadores safristas iniciam o corte de cana numa segunda-feira, com os exames admissionais realizados só no final daquela semana.
**Fundamentação técnica essencial:** O exame admissional atesta a aptidão do trabalhador frente às exigências rurais. Permitir início antes do exame expõe o indivíduo e gera vulnerabilidade jurídica.

### 231132-1 — Deixar de garantir a realização de exame médico periódico
**Capitulação legal:** Art. 18 da Lei nº 5.889/73 c/c item 31.3.7, alínea "b", da NR-31, com redação da Portaria SEPRT nº 22.677, de 22/10/2020.
**Gradação:** I3
**O que verificar:**
- Revisar os ASOs periódicos e rastrear exames com validade vencida (mais de 12 meses ou prazo menor fixado pelo médico/convenção).
- Confrontar a listagem de funcionários ativos com o cronograma de exames clínicos/laboratoriais.
- Verificar se os intervalos foram reduzidos para expostos a riscos críticos elevados, conforme critério médico ou norma coletiva.
**Situação comum de não conformidade:** Vaqueiros e tratoristas trabalham com exames admissionais/periódicos vencidos há mais de um ano e meio, sob alegação de rotina operacional.
**Fundamentação técnica essencial:** O exame periódico é o instrumento de vigilância continuada para identificar precocemente patologias ocupacionais silenciosas. A falha impede intervenções oportunas.

### 231133-0 — Deixar de garantir exame de retorno ao trabalho após afastamento igual/superior a 30 dias
**Capitulação legal:** Art. 18 da Lei nº 5.889/73 c/c item 31.3.7, alínea "c", da NR-31, com redação da Portaria SEPRT nº 22.677, de 22/10/2020.
**Gradação:** I3
**O que verificar:**
- Identificar trabalhadores afastados por 30 dias ou mais por doença ou acidente (ocupacional ou não).
- Exigir o ASO de Retorno ao Trabalho e certificar se a data coincide com o primeiro dia útil de retorno.
- Verificar se restrições/recomendações do ASO de retorno foram cumpridas em campo.
**Situação comum de não conformidade:** Tratorista afastado por 40 dias (fratura no braço) retorna à fazenda e reassume o comando de maquinário pesado sem passar por avaliação médica.
**Fundamentação técnica essencial:** A reintrodução após afastamento prolongado exige validação clínica da recuperação funcional. O exame evita agravamento de condição remanescente e novos acidentes.

### 231134-8 — Deixar de garantir exame de mudança de risco ocupacional antes da mudança
**Capitulação legal:** Art. 18 da Lei nº 5.889/73 c/c item 31.3.7, alínea "d", da NR-31, com redação da Portaria SEPRT nº 22.677, de 22/10/2020.
**Gradação:** I3
**O que verificar:**
- Identificar transferências internas de cargo por registros funcionais/eSocial.
- Cruzar a data efetiva da transferência com a data de emissão do ASO de Mudança de Risco.
- Verificar se o novo risco exigia exames complementares específicos realizados antes do início da nova atividade.
**Situação comum de não conformidade:** Trabalhador da capina manual é promovido a aplicador de defensivos, assumindo o manuseio de tóxicos semanas antes da avaliação médica e exames toxicológicos.
**Fundamentação técnica essencial:** O exame antes da mudança estabelece linha de base clínica e atesta aptidão para o novo perigo. Sem ele, o trabalhador é exposto sem salvaguardas.

### 231135-6 — Deixar de garantir exame demissional em até 10 dias do término do contrato
**Capitulação legal:** Art. 18 da Lei nº 5.889/73 c/c item 31.3.7, alínea "e", da NR-31, com redação da Portaria SEPRT nº 22.677, de 22/10/2020.
**Gradação:** I3
**O que verificar:**
- Cruzar datas de rescisão com as datas de realização do exame demissional.
- Contar o prazo em dias corridos para verificar se o limite de 10 dias foi extrapolado.
- Verificar se a dispensa do exame cumpre o critério normativo (exame clínico recente há menos de 90 dias) e eventuais restrições de convenção coletiva.
**Situação comum de não conformidade:** Empresa dispensa trabalhadores temporários ao fim da safra sem encaminhá-los ao exame demissional no prazo, alegando que o contrato temporário desobrigaria a avaliação.
**Fundamentação técnica essencial:** O exame demissional atesta as condições de saúde no momento da saída. O prazo de 10 dias evita mascaramento de agravos manifestados logo após o desligamento.

### 231136-4 — Deixar de subsidiar exames médicos com exame clínico/complementares conforme os riscos e parâmetros da NR-07
**Capitulação legal:** Art. 18 da Lei nº 5.889/73 c/c item 31.3.7.1 da NR-31, com redação da Portaria SEPRT nº 22.677, de 22/10/2020.
**Gradação:** I3
**O que verificar:**
- Verificar se os exames solicitados estão correlacionados aos riscos físicos, químicos, biológicos e ergonômicos do PGRTR.
- Verificar se as avaliações e exames complementares seguem os parâmetros de periodicidade, amostragem e interpretação técnica dos Anexos da NR-07.
- Garantir que os ASOs detalhem os exames complementares realizados, conforme o perfil de risco da atividade.
**Situação comum de não conformidade:** Trabalhadores expostos a elevada poeira vegetal passam só por anamnese rápida, sem espirometrias ou radiografias de tórax preconizadas.
**Fundamentação técnica essencial:** O exame médico ocupacional deve ser guiado pela matriz de exposição do trabalhador. Ignorar os riscos e a NR-07 anula a capacidade diagnóstica precoce.

### 231138-0 — Deixar de realizar exames complementares quando há exposição acima do nível de ação (Anexos da NR-09/PGRTR)
**Capitulação legal:** Art. 18 da Lei nº 5.889/73 c/c item 31.3.7.1.1, parte final, da NR-31, com redação da Portaria SEPRT nº 22.677, de 22/10/2020.
**Gradação:** I3
**O que verificar:**
- Inspecionar as medições ambientais do PGRTR e identificar postos/funções cujos níveis ultrapassaram o "Nível de Ação".
- Selecionar amostra de prontuários/ASOs de trabalhadores desses postos.
- Verificar se os exames complementares cabíveis foram solicitados, realizados e laudados periodicamente.
**Situação comum de não conformidade:** Operadores de colhedoras de algodão expostos a 82 dB(A) (acima do nível de ação de 80 dB(A)) não são submetidos a audiometrias periódicas.
**Fundamentação técnica essencial:** O nível de ação sinaliza potencial latente de dano. Ativar o monitoramento médico nessa fase é crucial para rastrear disfunções precoces antes de atingir o limite de tolerância.
