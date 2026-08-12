---
name: aft-embargo-interdicao
model: sonnet
description: >
  Use SEMPRE que o AFT pedir para criar, gerar ou redigir um Relatório
  Técnico para Interdição e/ou Embargo (RT). Acione com "relatório técnico
  de interdição/embargo", "RT de interdição", "gerar o relatório técnico",
  "montar o RT", "/aft-embargo-interdicao", "embargar a obra", "interditar
  a máquina". Logo após o RT, redige obrigatoriamente os
  autos derivados das ementas da seção 4. Acione TAMBÉM quando o AFT ANEXAR
  um RT ou Termo de Interdição já pronto e pedir os autos dele: é esta skill
  que os redige, nunca improvisar por fora. Gera o RT em dois formatos: por
  TÓPICO (padrão, seções temáticas) ou por OBJETO ("RT por objeto": cada objeto
  interditado com suas irregularidades, riscos, medidas e documentos); com
  objetos de tipos diferentes, pergunta ao AFT qual usar. Acione AINDA quando o AFT
  descrever uma situação encontrada na inspeção e perguntar se cabe
  interdição/embargo ("isso é grave e iminente?", "devo interditar?"): a
  skill consulta precedentes reais de interdição e sugere — quem decide é
  sempre o AFT.
---

# aft-embargo-interdicao — Relatório Técnico para Interdição e Embargo
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

Gerar um **Relatório Técnico para Interdição e/ou Embargo** em formato `.docx`, baseado no
modelo oficial incluído no toolkit (`~/.claude/skills/aft-embargo-interdicao/template.docx`,
modelo **universal**: cabeçalho, cidade/UF e data já vêm como placeholder genérico,
qualquer AFT de qualquer SRTE pode usar sem adaptação). O documento mantém
TODO o conteúdo fixo do modelo (cabeçalho, logotipos, textos legais, citações doutrinárias,
tabelas NR-3, instruções de suspensão, nota sobre SEI) e preenche apenas as partes variáveis
com os dados fornecidos pelo AFT.

---

## Fluxo de execução

### Modo de entrada (decida primeiro)

- **Modo A — Criar o RT do zero:** o AFT pede o Relatório Técnico de Interdição/Embargo.
  Siga o fluxo completo: passos 0 a 6 (montam e salvam o `.docx`) e depois o passo 7 (autos).
- **Modo B — RT/Termo de Interdição já ANEXADO + pedido de autos:** o AFT anexa um RT ou um
  Termo de Interdição pronto e pede "gere os autos de infração". **Não refaça o RT** (pule os
  passos 0 a 6). Resolva a pasta da OS (passo 1, mínimo: empregador/CNPJ/CPF), **extraia as
  irregularidades/ementas e os objetos interditados do documento anexado** e vá direto ao
  **passo 7** para redigir os autos. Use o `.docx`/PDF anexado como o RT da OS (copie-o para a
  pasta `interdicao-embargo/` como elemento de convicção, fazendo backup/checagem de arquivo
  aberto antes de sobrescrever).
- **Modo C — Dúvida de enquadramento (cabe interditar?):** o AFT descreve uma situação
  encontrada na inspeção e ainda **não decidiu** pela interdição — pergunta se configura
  risco grave e iminente, se "cabe interdição", ou pede sugestão. Rode a
  **consulta a precedentes** (seção abaixo) e apresente o resultado: precedentes análogos
  (nº do termo, ementas usadas, redação do fator de risco) e a sua leitura sobre a
  similaridade com o caso concreto. **Sugira; nunca decida.** Se o AFT decidir interditar,
  siga para o Modo A reaproveitando tudo o que a consulta trouxe.

> Em todos os modos, os autos são redigidos AQUI (nesta skill) — nunca improvisados fora dela.

### Consulta a precedentes de interdição (notebook `interdicoes`)

O toolkit mantém uma base de **precedentes reais**: mais de uma centena de Relatórios
Técnicos de Interdição/Embargo (máquinas NR-12, obras NR-18/NR-35, e outros), cada um com
objetos interditados, ementas, fatores de risco, medidas de proteção e documentos
solicitados. Ela vive no NotebookLM, na key `interdicoes` do
`~/.claude/skills/config/notebooks.json`.

- **Quando consultar:** sempre no **Modo C**; e no **Modo A** quando o AFT não ditar o
  conteúdo das seções 5, 6 ou 7 (fatores de risco, medidas de proteção, documentos) — os
  precedentes viram a minuta proposta, que o AFT revisa.
- **Como consultar** (uma pergunta objetiva por situação):
  ```bash
  notebooklm ask "Situação encontrada: [descrição objetiva]. Há precedentes de interdição para essa situação? Cite os números dos termos, as ementas usadas (código e descrição), como foi redigida a seção de fatores de risco (risco atual x risco de referência, excesso de risco) e quais medidas de proteção e documentos foram exigidos." --notebook [notebook_id de 'interdicoes'] --json
  ```
- **Como apresentar:** cite os termos precedentes pelo número (rastreabilidade), mas deixe
  claro que precedente **não substitui** a avaliação do caso concreto — a decisão de
  interditar é ato do AFT (art. 161 da CLT).
- **Se a key `interdicoes` não existir** no `notebooks.json` (ou o NotebookLM não responder
  mesmo após a reconexão automática), **pule a camada sem alarde**: no Modo C, diga que a
  base de precedentes não está configurada e siga com a análise pelos critérios da NR-03;
  nos demais modos, peça os dados ao AFT como sempre.
- Os precedentes **não dispensam** o sub-fluxo 4b (resolução de ementas): eles servem de
  cheque cruzado ("em casos análogos usou-se a ementa X"), mas o código/capitulação final
  continua vindo do ementário.

### 0. Decidir: INTERDIÇÃO ou EMBARGO (antes de qualquer coisa)

A NR-03 separa as duas medidas **pelo objeto**, não pela gravidade:

| Objeto atingido | Medida | Fundamento |
|---|---|---|
| **Obra** (construção, montagem, instalação, manutenção, reforma) | **EMBARGO** | subitem 3.2.2.1 da NR-03 |
| Atividade, **máquina ou equipamento**, setor de serviço ou estabelecimento | **INTERDIÇÃO** | subitem 3.2.2.2 da NR-03 |

Adote sempre a **menor unidade possível** capaz de afastar o risco (subitem
3.2.2.3.1 da NR-03) — é o que justifica "Paralisação: PARCIAL" restrita a
pavimentos, setores ou máquinas determinadas, em vez de paralisar tudo.

**Quando for EMBARGO, o template exige adaptações** — ele é redigido para
interdição. Basta pôr `"modo": "embargo"` no JSON: o `montar_rt.py` troca sozinho
o título, o cabeçalho do item 3 (`OBJETO(S) EMBARGADO(S):`), as menções do item 1
e, no item 8, "suspensão da interdição" → "do embargo", "Termo de Interdição" →
"de Embargo" e "identificação da(s) máquina(s) ou setor de serviço" →
"identificação da obra ou da frente de trabalho".

> São as **únicas** alterações no texto fixo, e existem porque um embargo de obra
> não pode sair chamado de interdição (NR-03, 3.2.2.1). Todo o resto dos itens
> 1, 2 e 8 permanece literal.

### 0-bis. Escolher o FORMATO do RT: por TÓPICO ou por OBJETO

O conteúdo é o mesmo; muda a organização das seções 4 a 7:

- **Por TÓPICO (padrão):** o layout do template — seções temáticas
  (4. Irregularidades, 5. Fatores de Risco, 6. Medidas, 7. Documentos), cada uma
  cobrindo todos os objetos de uma vez. É o formato de sempre da skill.
- **Por OBJETO:** as seções 4 a 7 deixam de existir como seções; **cada objeto**
  da seção 3 ganha seus próprios sub-blocos (Irregularidades, Fatores de Risco,
  Medidas de Proteção, Documentos Solicitados), e a Conclusão renumera sozinha
  para o item 4. Alguns AFTs preferem assim no Sistema Auditor quando os objetos
  são de naturezas diferentes — a leitura fica "um objeto, um dossiê".

**Regra de decisão:**

1. Conte os **tipos** de objeto da medida (as 4 hipóteses do subitem 3.2.2.2 da
   NR-03: máquina/equipamento, atividade, setor de serviço, estabelecimento —
   MÁQUINA e EQUIPAMENTO contam como UM tipo só; no embargo, OBRA).
2. **Tipos heterogêneos** (ex.: 1 máquina + 1 setor de serviço; atividade +
   setor; máquina + atividade + estabelecimento): **pergunte OBRIGATORIAMENTE ao
   AFT** — "Os objetos são de tipos diferentes. Prefere o RT por TÓPICO (seções
   temáticas, padrão) ou por OBJETO (cada objeto com suas irregularidades,
   riscos, medidas e documentos)?" — e formate como ele decidir. Não escolha em
   silêncio.
3. **Tipos homogêneos** (só máquinas, só uma obra...): siga no formato por
   tópico **sem perguntar** — a menos que o AFT peça "por objeto".
4. No **Modo B** (RT já anexado) não há o que decidir: o RT não é refeito.

**Consequências práticas do formato por objeto** (o `montar_rt.py` cuida de tudo
ao receber `"formato": "objeto"` no JSON):

- as quatro listas (irregularidades, fatores_risco, medidas_protecao,
  documentos_solicitados) saem do nível de cima do JSON e entram **dentro de
  cada objeto**;
- o bloco fixo da metodologia da NR-3 (com as Tabelas 3.1/3.2/3.3), que no
  template vive na seção 4, **migra para o fim da seção 2** — precisa vir antes
  da análise por objeto;
- a alínea fixa "Requerimento expresso..." do item 6 é **dispensada** neste
  formato: a mesma exigência já consta do bloco fixo DO PEDIDO DE SUSPENSÃO
  (incisos I a III), que permanece intacto;
- irregularidades, medidas e documentos de cada objeto saem como **lista com
  marcador** (sem alíneas A/B/C — elas não reiniciariam a cada objeto).

**No formato por tópico com MAIS DE UM objeto**, abra cada item das seções 4, 6
e 7 com a referência ao objeto — `Objeto 1 - ...`, `Objetos 2 e 3 - ...` — e, no
item 5, cite o objeto na `descricao` do fator (ex.: "... na operação do Objeto
1."). Sem isso o leitor não sabe qual irregularidade pertence a qual objeto.
Com objeto único, nada de prefixo.

### 1. Coletar os dados necessários

Os campos são os do **Dicionário de campos do template** (logo abaixo do passo 2).
Extraia do contexto (`inspecao-fisica.md`, `memory.md`, PDFs anexados, descrição do
AFT) ou pergunte. `cidade`, `uf` e `auditor_fiscal` vêm do `aft-config.md`.

**A data da inspeção física** entra no campo `Contexto-da-inspecao-fisica`, no
início do item 2 — **nunca** no item 4. Se não encontrar a data em lugar algum,
**pergunte ao AFT antes de continuar**.

#### 1a. Identificar as irregularidades

A partir do contexto, liste cada irregularidade de forma objetiva e separada. Cada
uma vira um parágrafo do item 4 e precisa ter, no item 5, um fator de risco
correspondente; no item 6, uma medida; e no item 7, um documento comprobatório.

#### 1b. Resolver as ementas (4 camadas)

Mesmo quando a ementa não aparece explicitamente no RT, resolvê-la é o que sustenta
a **capitulação** citada na irregularidade e os **autos derivados** do passo 7.

1. **Catálogos das skills de NR (fonte primária, local, sem rede).** As skills
   `/aft-NR12` e `/aft-NR18` mantêm catálogos curados a partir de autos reais, em
   `~/.claude/skills/aft-NR12/references/ementas-comuns.md` e
   `~/.claude/skills/aft-NR18/references/ementas-comuns.md`. Leia o da NR do caso e
   varra os **"Gatilhos"** de cada bloco contra a narrativa do AFT: é o que eles
   fazem melhor que o NotebookLM — mapear a frase que o AFT escreveu ("sem proteção
   na zona de perigo", "abertura no piso") para a ementa certa. Cada bloco traz
   código, descrição oficial, subitem violado, capitulação e texto-base.
   - **Casando mais de um bloco**, escolha o mais específico e mantenha os outros
     como candidatos — em obra é comum vários fatos distintos coexistirem.
   - **Atenção à notação:** a NR-18 grafa o código com **7 dígitos e sem hífen**
     (`3182746`) e o ementário grafa `318274-6`. É o mesmo código — normalize antes
     de comparar, ou o casamento falha em silêncio.
   - **Atenção à estrutura:** os dois catálogos não são iguais. No da NR-12 cada
     ementa é um bloco `##`; no da NR-18, `##` é a seção da norma (18.4, 18.9...) e
     cada ementa é um `###` dentro dela. Ler só os `##` no da NR-18 devolve uma
     ementa por seção e perde o resto.
   - **Cobertura esperada:** os 45 códigos dos dois catálogos resolvem cerca de
     **36% das ementas** que aparecem em RTs reais, e apenas ~13% dos RTs ficam
     inteiramente cobertos. O catálogo é a primeira camada, **não substitui** o
     NotebookLM — conte com a camada 2 na maioria dos casos.
   - O catálogo da NR-12 traz o campo **"Aplicabilidade a Termo de Interdição"**; o
     da NR-18 **não classifica** a dimensão cautelar, por decisão de projeto — essa
     leitura é desta skill (passo 0 e item 5).
   - **Se o gatilho não casar com nada**, não force: vá à camada 2.
2. **NotebookLM** (se configurado pelo `/aft-setup`): leia
   `~/.claude/skills/config/notebooks.json` e consulte **os dois** notebooks —
   o `ementario-sst` (código, descrição e capitulação) **e o da NR específica**
   do caso (`nr-12`, `nr-18`, `nr-35`...). O da NR não é opcional: é ele que
   confere o texto do subitem contra o fato e costuma apontar **ementa aplicável
   que passou despercebida** (num teste real, a consulta à NR-18 revelou a
   318265-7, ausente na resolução feita só pelo ementário).
   Para cada irregularidade, pergunte (uma consulta por irregularidade, em paralelo):
   ```bash
   notebooklm ask "Qual é o código da ementa no formato XXXXXX-X, a descrição completa da ementa e a capitulação legal para a seguinte infração: [descrição objetiva da irregularidade]?" --notebook [notebook_id] --json
   ```
   > **Reconexão automática:** se a sessão do NotebookLM tiver expirado, ele se reautentica
   > sozinho pelo `NOTEBOOKLM_REFRESH_CMD` (configurado no `/aft-setup`/`/aft-notebooklm-login`).
   > Só passe à camada seguinte se ele ainda assim não responder.
   > **Cheque cruzado obrigatório:** confira a ementa sugerida pelos precedentes contra o
   > ementário. Precedente indica caminho, não capitulação — máquina parecida pode estar
   > em anexo diferente da NR (ex.: sopradora **não** é do Anexo IX da NR-12, que só cobre
   > injetoras).
3. **Ementário no Google Drive** (manual): oriente o AFT a abrir
   https://drive.google.com/drive/folders/1bktX9TkDIoix4iQuca3Yr5aWCfv97GSg?usp=sharing
   (pasta `EMENTAS SST` → `ementasNRXX.md`) e colar o trecho da ementa.
4. **Pedir ao AFT** o código/descrição/capitulação diretamente.

Se nenhuma camada retornar a ementa, cite na irregularidade apenas o dispositivo
violado (NR/subitem + artigo da CLT) e **avise o AFT ao final** que aquela ementa
ficou pendente — ela é necessária no passo 7.

> **Itens 5, 6 e 7 sem dados do AFT?** Consulte os precedentes (seção "Consulta a
> precedentes de interdição") com a descrição da situação e **proponha a minuta**
> baseada nos casos análogos, marcando-a como proposta para o AFT revisar.

### 2. Montar o documento (caminho padrão)

**Use o `montar_rt.py`.** O template traz placeholders `{{chave}}`; o script
substitui cada um, repete os blocos que se repetem, monta as listas do Word e
preserva o texto fixo. Os passos 2-alt a 5 ficam abaixo só como **fallback**.

1. Grave o JSON **com a tool Write** (nunca digite acentos na linha de comando):

```json
{
  "modo": "embargo",
  "formato": "topico",
  "numero_termo": "0012345-6",
  "empregador": "RAZÃO SOCIAL LTDA",
  "cnpj": "00.000.000/0000-00",
  "Contexto-da-inspecao-fisica": "A inspeção física foi realizada em DD/MM/AAAA, ..., acompanhada por ...",

  "objetos": [
    {"numero_objeto": "1", "tipo_objeto": "OBRA",
     "tipo_paralisacao": "PARCIAL", "objetos": "descrição do que ficou paralisado..."}
  ],

  "irregularidades": ["parágrafo 1", "parágrafo 2"],

  "fatores_risco": [
    {"fator_de_risco": "Queda de altura - Extremo (E)",
     "descricao": "...",
     "fundamentacao_risco_atual": "Consequência MORTE e probabilidade PROVÁVEL. ...",
     "fundamentacao_risco_referencia": "Consequência MORTE e probabilidade RARA. ..."}
  ],

  "medidas_protecao": ["medida 1", "medida 2"],
  "documentos_solicitados": ["documento 1", "documento 2"],

  "conclusao": "texto da conclusão (opcional; sem ele a seção fica em branco para o AFT)",

  "cidade": "Goiânia", "uf": "GO", "data": "29/07/2026",
  "auditor_fiscal": "NOME DO AUDITOR"
}
```

`"formato"` é opcional (ausente = `"topico"`). No **formato por objeto**
(`"formato": "objeto"`, decidido no passo 0-bis), as quatro listas saem do nível
de cima e entram **dentro de cada objeto** — os demais campos não mudam:

```json
"objetos": [
  {"numero_objeto": "1", "tipo_objeto": "MÁQUINA",
   "tipo_paralisacao": "TOTAL", "objetos": "descrição...",
   "irregularidades": ["ementa + capitulação do objeto 1"],
   "fatores_risco": [
     {"fator_de_risco": "...", "descricao": "...",
      "fundamentacao_risco_atual": "...", "fundamentacao_risco_referencia": "..."}
   ],
   "medidas_protecao": ["medida do objeto 1"],
   "documentos_solicitados": ["documento do objeto 1"]}
]
```

> No formato por objeto, ementa que atinge mais de um objeto se **repete** no
> bloco de cada objeto atingido — mas continua rendendo **um único auto** no
> passo 7 (regra 7.1).

2. Rode:

```bash
python ~/.claude/skills/_scripts/montar_rt.py "<dados.json>" "<saida.docx>"
```

## Dicionário de campos do template

Formato `{{chave}}`, substituição literal, sem espaços internos. **Não alterar
nenhum outro texto:** os itens 1, 2 e 8, a metodologia da NR-3 e as Tabelas
3.1/3.2/3.3 são texto fixo e juridicamente vinculado.

**Cabeçalho** — `numero_termo` (só dígitos/formato oficial, sem "nº"),
`empregador` (razão social como no CNPJ, sem endereço), `cnpj` (formatado
`00.000.000/0000-00`).

**Item 3 — objetos.** Lista de objetos; o bloco inteiro se repete para cada um:
- `numero_objeto` — ordinal no Termo (1, 2...);
- `tipo_objeto` — caixa alta, pelas hipóteses do subitem 3.2.2.2 da NR-03:
  ATIVIDADE | MÁQUINA | EQUIPAMENTO | SETOR DE SERVIÇO | ESTABELECIMENTO
  (e OBRA, no embargo — subitem 3.2.2.1);
- `tipo_paralisacao` — caixa alta: TOTAL | PARCIAL;
- `objetos` — descrição: identificação física, localização, nº de série/patrimônio
  quando houver, e o que exatamente ficou paralisado. Prosa objetiva, 1 a 3
  parágrafos. **Sem juízo de valor e sem fundamentação legal** (isso é do item 4).

**Item 2 — `Contexto-da-inspecao-fisica`.** É onde entra o **contexto da ação
fiscal**, no início do item 2. Deve trazer **sempre, no mínimo, a data da
inspeção física**; e, quando houver, quem acompanhou (nome e cargo do preposto),
o local percorrido, o que foi examinado e outros dados relevantes — acidente
anterior no mesmo posto, denúncia que originou a ação, documentos não
apresentados na hora. **Nada disso vai no item 4**, que é só das irregularidades.

**Item 4 — `irregularidades`.** Uma por parágrafo, contendo **apenas**: código da
ementa, descrição da irregularidade e capitulação. Nada de narrativa de inspeção
(data, quem acompanhou, percurso) — isso é do item 2. Redação impessoal, no
pretérito, verificável. **Não antecipar as medidas corretivas** (item 6).

**Item 5 — `fatores_risco`.** Lista; o bloco de 4 campos se repete por fator:
- `fator_de_risco` — nome do fator + excesso de risco pela Tabela 3.3. Só cabe
  interdição/embargo com excesso **Extremo (E)** ou **Substancial (S)**. O rótulo
  do template já diz "excesso de risco:" — não repita a expressão no valor;
- `descricao` — como o trabalhador interage com o fator: modo operatório,
  tempo/frequência de exposição, nº de expostos, condições do ambiente;
- `fundamentacao_risco_atual` — justificativa da CONSEQUÊNCIA (Tabela 3.1) e da
  PROBABILIDADE (Tabela 3.2) na situação encontrada, **nomeando as categorias**;
- `fundamentacao_risco_referencia` — a mesma dupla na situação objetivo, após as
  medidas. A distância entre as duas é o excesso de risco declarado acima.

**Item 6 — `medidas_protecao`.** Uma medida por item, no infinitivo, cada uma
vinculada à irregularidade e ao dispositivo correspondentes, verificáveis
documentalmente. A alínea fixa "Requerimento expresso..." do template permanece
como **último item** da lista — o script cuida disso (no formato por objeto ela
é dispensada; ver passo 0-bis).

**Item 7 — `documentos_solicitados`.** Os documentos que comprovarão as medidas do
item 6: ART/laudos, projetos, manuais, ordens de serviço, PGR/PCMSO, certificados
de treinamento, registros fotográficos, notas fiscais. Um por item. **Manter os
nomes idênticos aos citados no item 6** (o inciso III do item 8 os referencia).

#### Como pedir laudo de máquina (regra dura)

O documento que o empregador vai juntar no pedido de suspensão precisa **provar a
adequação de forma verificável**, não apenas afirmar que consertou. Por isso, todo
laudo de máquina pedido no item 7 deve carregar, **sempre**, estes três elementos:

1. **Fotos** da máquina com as proteções instaladas;
2. **Link de acesso à nuvem com vídeos do funcionamento das proteções** — o vídeo é
   o que distingue proteção que funciona de proteção que só está parafusada;
3. **Assinatura de profissional legalmente habilitado (Engenheiro).**

**Máquina com anexo próprio na NR: exigir laudo CONCLUSIVO por aquele anexo.**
Quando a máquina interditada tem anexo específico na NR-12, não basta pedir "laudo
do sistema de segurança": o laudo tem de **concluir pela adequação da máquina ao
anexo próprio**, com citação expressa do anexo e do item. É o anexo que define o
que aquela máquina precisa ter, e é contra ele que o AFT vai julgar o pedido de
suspensão. Sem essa amarração, o empregador junta laudo genérico e o exame vira
discussão sobre o que deveria ter sido pedido.

**Resolva o anexo pela tabela de correlação**, em
`~/.claude/skills/aft-embargo-interdicao/references/anexos-nr12.md` — leia esse arquivo sempre que
o RT interditar máquina. Ele traz o escopo dos 12 anexos, a tabela máquina → anexo →
item a citar (itens conferidos no notebook da NR-12) e, no fim, as **dispensas
expressas** de cada anexo, que limitam o que se pode exigir no item 7. Exemplos:

| Máquina | Anexo da NR-12 | Item a citar |
|---|---|---|
| Moedor de carne (picador) | Anexo VII (Açougue, Mercearia, Bares e Restaurantes) | item 4 (4. Moedor de carne - Picador) |
| Cilindro sovador | Anexo VI (Panificação e Confeitaria) | item 4 (4. Cilindro Sovador) |
| Prensa enfardadeira vertical | Anexo VIII (Prensas e Similares) | item 8 (8. Prensa Enfardadeira Vertical) |

Máquina que **não** estiver na tabela: resolva pelo notebook da NR antes de escrever o
item 7 (mesma consulta do sub-fluxo 1b). Não presuma o anexo pela semelhança física da
máquina, é o erro que a própria skill já adverte no cheque cruzado (sopradora **não** é
do Anexo IX). E a maioria das máquinas **não tem anexo próprio**: nesse caso o item 7
pede ART e laudo do sistema de segurança citando os itens gerais violados, sem inventar
anexo. Um mesmo supermercado costuma ter máquinas do Anexo VI (padaria), do VII
(açougue), do VIII (prensa enfardadeira) e várias sem anexo nenhum.

**Cheque as dispensas antes de exigir.** Cada anexo tem dispensas expressas (extrabaixa
tensão para moedor de carne e amaciador de bife, arranjo físico para ME/EPP,
certificação INMETRO na panificação). Cobrar no item 7 algo que o anexo dispensa entrega
ao empregador um argumento pronto contra o RT. A lista está no arquivo de referência.

**Fórmulas prontas** (adapte máquina, objeto e anexo; mantenha o resto literal):

> Anotação de Responsabilidade Técnica (ART) e laudo técnico do sistema de segurança
> instalado na [MÁQUINA] (Objeto N), com comprovação da categoria de segurança [X] e
> laudo conclusivo que a máquina atende o anexo [NUMERAL] da NR-12 ([ITEM DO ANEXO]),
> assinado por Profissional legalmente habilitado (Engenheiro), com fotos, link de
> acesso à nuvem com vídeos do funcionamento das proteções e interface de segurança
> (relés/CLP de segurança) instalados, com descrição da categoria de segurança
> atingida

> Laudo de adequação [DA/DAS MÁQUINA(S)] concluindo pela adequação [DA/DAS
> MÁQUINA(S)] de acordo com o anexo [NUMERAL] da NR-12 ([ITEM DO ANEXO]), com fotos,
> link de acesso à nuvem com vídeos do funcionamento das proteções. Laudo deve ser
> assinado por Profissional legalmente habilitado (Engenheiro).

**Qual fórmula usar** — decida pelo item 4 do próprio RT, não por impressão: se entre
as irregularidades daquela máquina houver **alguma ementa de interface de segurança,
categoria de segurança, monitoramento ou redundância** (312364-2, 312360-0, 312356-1,
312367-7 e afins), use a **primeira** fórmula, porque há categoria a comprovar. Se as
ementas forem só de proteção mecânica, geometria ou enclausuramento (312358-8, 312377-4,
312603-0, 312604-8 e afins), use a **segunda**. Na dúvida, a primeira: pedir a descrição
da categoria atingida não prejudica ninguém, e a falta dela é o que mais trava o exame
do pedido de suspensão.

**Um laudo por máquina (ou por grupo de máquinas do mesmo anexo), não um por
ementa.** Várias ementas da mesma máquina se provam com um único laudo conclusivo
pelo anexo — desmembrar em um documento por ementa produz item 7 inflado e repetitivo,
e o empregador acaba juntando o mesmo laudo N vezes. Máquinas distintas do mesmo anexo
(ex.: os dois moedores de carne) podem ir num laudo só, desde que ele conclua pela
adequação **de cada uma** delas. O que **não** se agrupa: documento que não é laudo
(procedimento de segurança, certificado de capacitação, ordem de serviço) vai em item
próprio.

**Item 8 — `conclusao`** (opcional). Texto da seção CONCLUSÃO/OBSERVAÇÃO. Sem o
campo, a seção sai em branco para o AFT preencher no Word — antes o script nem
tinha como preenchê-la.

**Fecho** — `cidade`, `uf` (sigla), `data`, `auditor_fiscal` (nome completo, caixa
alta).

### Regras de preenchimento (valem para o JSON inteiro)

- **Não digite numeração nem marcador** — nada de "3.", "A)", "-", "•", "1.": a
  numeração dos itens e das alíneas é automática no Word, e o script insere as
  medidas e os documentos como **lista real**.
- **Coerência obrigatória:** cada irregularidade (item 4) precisa de fator de risco
  (item 5), medida (item 6) e documento comprobatório (item 7) correspondentes. A
  correspondência do item 7 **não é um-para-um**: um único laudo conclusivo pelo anexo
  da máquina cobre todas as ementas daquela máquina (ver "Como pedir laudo de
  máquina"). O que não pode é sobrar irregularidade sem nenhum documento que a prove.
- **Nada de medida ou documento sem irregularidade que o sustente.** Não exigir
  capacitação, PGR, ordem de serviço ou qualquer outro item que não decorra de uma
  irregularidade do item 4 — o pedido de suspensão só pode cobrar o que foi autuado.
- **Nunca afirmar fato que não foi constatado.** Modo operatório, serviço em
  execução, frequência de exposição e número de expostos só entram se estiverem no
  relato do AFT ou no `inspecao-fisica.md`. Faltando o dado, escreva
  `[A CONFIRMAR PELO AFT: ...]` — inventar detalhe verossímil é o defeito mais
  perigoso deste documento, porque passa despercebido na revisão e cai na
  impugnação.
- **Declare o número de expostos** na `descricao` do item 5 — é exigência do
  dicionário.
- **Ao citar a matriz de excesso de risco, escreva "pela tabela da NR-03"**, sem
  numerar. O trecho do template que menciona a Tabela 3.3 começa com "Como
  exemplo": é ilustração de enquadramento, não a matriz do caso concreto. Citar
  "Tabela 3.3" no texto gerado amarra o RT a uma hipótese específica de exposição
  e cria brecha de impugnação sem necessidade. As Tabelas 3.1 (consequência) e
  3.2 (probabilidade) podem ser citadas nominalmente — essas são definitórias.
- **Interdição/embargo não pode inviabilizar a própria correção.** Ao descrever o
  objeto, ressalve os serviços necessários ao cumprimento das medidas (do
  contrário, fechar as aberturas embargadas seria descumprir o embargo).
- **Nenhum campo vazio.** O script aborta se sobrar qualquer `{{...}}` no
  documento final.
- Fonte e recuos vêm do template — o script preserva a formatação de cada
  placeholder, inclusive rótulos em negrito.

**Formatação: o script normaliza, não confia no placeholder.** Os placeholders do
template nem sempre carregam a formatação do corpo (justificação, entrelinha,
recuo), e o texto gerado saía destoando do resto. O `montar_rt.py` agora força o
padrão do corpo — **justificado, entrelinha 1,5** — em objetos, irregularidades,
fatores de risco, medidas e documentos; põe **recuo de primeira linha** no
contexto da inspeção; transforma as **ementas do item 4 em lista com marcador**
(criando a lista, que o template não tem); e remove o parágrafo vazio que o
template deixa antes da alínea fixa do item 6, responsável por uma quebra dupla
antes do último item. Ao reescrever o `<w:pPr>`, respeita a **ordem exigida pelo
schema OOXML** (`pStyle → numPr → tabs → adjustRightInd → spacing → ind → jc →
rPr`): fora de ordem, o Word acusa documento corrompido.

**O que o script resolve sozinho:** placeholder partido entre runs (o Word quebra
`{{chave}}` em pedaços ao editar); numeração automática das listas, com a alínea
fixa no fim do item 6 e o item 7 reiniciando em A); e as trocas do **modo
embargo** no texto fixo. Se um placeholder sumir do template, ele **para com erro**
(exit 3) — sinal de template alterado, não de RT torto.

### 2-alt. Fallback manual — preparar a área de trabalho

> Só use os passos 2-alt a 5 se o `montar_rt.py` não servir (template diferente,
> seção que ele não cobre). Caso contrário, vá do passo 2 direto ao 4-bis.
> O fallback manual cobre apenas o formato por TÓPICO; o formato por objeto
> depende do `montar_rt.py` (a reorganização das seções é cirurgia de XML).

```bash
mkdir -p /tmp/RT_temp
cp ~/.claude/skills/aft-embargo-interdicao/template.docx /tmp/RT_temp/template.docx
```

> No Windows com Git Bash, `/tmp` existe e funciona normalmente.

### 3. Desempacotar o template

```bash
python ~/.claude/skills/_scripts/docx_unpack.py /tmp/RT_temp/template.docx /tmp/RT_temp/unpacked/
```

### 4. Substituir os placeholders no XML

Edite `/tmp/RT_temp/unpacked/word/document.xml` usando a tool Edit para substituir os
seguintes placeholders pelo conteúdo fornecido pelo usuário:

| Placeholder no XML | Campo |
|---|---|
| `TERMO DE INTERDIÇÃO Nº XXXXX` | Nº do Termo |
| `XXXX` (em EMPREGADOR) | Nome do empregador |
| `XXXXX` (em CNPJ) | CNPJ |
| Após o texto fixo da seção 1 (OBJETIVO) | Inserir frase: `"A inspeção física foi realizada em DD/MM/YYYY com subseqüente análise de documentos necessários para elaboração deste relatório técnico."` |
| `OBJETO: 1 – ATIVIDADE - Paralisação: TOTAL` | Descrição do(s) objeto(s) interditado(s) |
| Parágrafo vazio após a metodologia NR-3 (seção 4) | Bloco de ementas montado no sub-fluxo 4a–4c |
| `Fator de Risco : excesso de risco` | Fator de risco |
| `Descrição:` (linha em branco após) | Descrição do risco |
| `Fundamentação do risco atual:` (linha em branco) | Fundamentação do risco atual |
| `Fundamentação do risco de referência` (linha em branco) | Fundamentação do risco de referência |
| Parágrafo `A) Requerimento expresso...` (fim da seção 6) | **Mover para o início da seção 7** — é documento a apresentar, não medida de proteção; o template o deixa preso à seção 6. As medidas então ocupam a seção 6 numeradas a partir de `A)`, e os documentos seguem a partir de `B)` |
| Parágrafos vazios de tabulação em seção 6 | Medidas de proteção |
| Parágrafos vazios de tabulação em seção 7 | Documentos solicitados |
| Parágrafo vazio após "8. CONCLUSÃO/OBSERVAÇÃO:" | Texto de conclusão |
| `XXXXX-GO, XX/XX/2026` | Cidade e data |
| `XXXXXXXX` (linha do nome do auditor) | Nome do AFT |

**IMPORTANTE:** As seções fixas (citações doutrinárias, tabelas NR-3, texto sobre DO PEDIDO DE
SUSPENSÃO, instruções do SEI, assinatura padrão "Auditor-Fiscal do Trabalho") NÃO devem ser
alteradas.

Para adicionar múltiplos objetos na seção 3, replique a estrutura de parágrafo existente.
Para adicionar múltiplas medidas/documentos nas seções 6 e 7, insira novos parágrafos com a
mesma formatação (tabulação).

### 5. Remontar e validar o documento

```bash
python ~/.claude/skills/_scripts/docx_pack.py /tmp/RT_temp/unpacked/ /tmp/RT_temp/RT_Interdicao.docx
```

O `docx_pack.py` valida o XML antes de empacotar — se acusar erro, corrija o
`document.xml` e rode de novo.

### 5-bis. Inserir fotografias no RT (quando houver)

> Vale para os dois caminhos: tanto depois do `montar_rt.py` (passo 2)
> quanto depois do fallback manual.

Fotos da inspeção entram **no corpo do RT**, logo depois da ementa ou do objeto
que ilustram — é o elemento de convicção mais direto do grave e iminente risco.
Não edite o XML da imagem à mão: use o script, que embute o arquivo em
`word/media/`, cria a relação e monta o `<w:drawing>` já dimensionado para a
mancha do texto (máx. 15,5 cm de largura, proporção preservada):

```bash
python ~/.claude/skills/_scripts/inserir_foto_docx.py "<RT.docx>" "<foto.jpg>" "<trecho do parágrafo âncora>" "<legenda>"
```

- O **parágrafo âncora** é um trecho de texto que já existe no documento (ex.: o
  começo da ementa `318264-9 - Utilizar escada portátil`); a foto entra logo
  depois dele. Se o trecho aparecer mais de uma vez, o script usa a última
  ocorrência.
- A **legenda** deve dizer o que se vê, onde e quando (ex.: `Fotografia 1 -
  Pavimento 19: abertura no piso sem fechamento. Inspeção de 29/07/2026.`).
- Rode o script **uma vez por foto**, sempre depois de o `.docx` já estar salvo.
- **A foto precisa existir como arquivo.** Imagem colada no chat não é arquivo:
  peça ao AFT para salvá-la numa pasta (a da OS, de preferência) e use o caminho.

### 6. Salvar na pasta da OS

Salve na pasta **canônica de interdição/embargo** da OS: `interdicao-embargo/` (pasta única
por OS, sem sufixo de data — é onde mora TODA a documentação de interdição/embargo da OS: RT,
autos derivados, termo assinado, requerimento e juntados do empregador e, depois, o RT de
manutenção). **Antes de copiar**: (1) se já existir um RT nessa pasta e ele estiver **aberto
no Word**, a cópia falharia com erro de permissão — cheque e peça para fechar ANTES; (2) faça
backup do RT anterior (o backup é silencioso se não houver arquivo a salvar):

```bash
mkdir -p "<OS_ATIVAS>"/"[PASTA_EMPRESA]"/interdicao-embargo/
DEST="<OS_ATIVAS>"/"[PASTA_EMPRESA]"/interdicao-embargo/RT_Interdicao.docx
python ~/.claude/skills/_scripts/checar_arquivo_aberto.py "$DEST"
python ~/.claude/skills/_scripts/backup_arquivo.py "$DEST"
cp /tmp/RT_temp/RT_Interdicao.docx "$DEST"
```

> Se a pasta `interdicao-embargo/` já tiver RT/autos de OUTRO termo, sufixe os arquivos novos
> com o nº do termo (ex.: `RT_Interdicao_4140033-0.docx`, `autos_4140033-0.md`) para não
> sobrescrever o anterior.

> Se o `checar_arquivo_aberto.py` retornar **ABERTO** (exit 1), **pare** e peça ao AFT, em
> uma frase: *"Feche o arquivo `RT_Interdicao.docx` no Word para eu poder salvar."* Assim
> que ele fechar, rode de novo. Nunca tente o `cp` por cima de um arquivo aberto.

Informe o caminho ao AFT — ele revisa o `.docx` no Word.

---

### 7. Gerar os autos de infração derivados do RT (OBRIGATÓRIO)

Esta fase é parte integrante do fluxo — **não é opcional**, **não perguntar ao usuário se
deseja gerá-los**. O RT acabou de ser produzido e tem todas as informações necessárias: data
da inspeção, objetos interditados (seção 3) e ementas com código + descrição + capitulação
(seção 4 no formato por tópico; blocos de irregularidades de cada objeto no formato por
objeto). Reaproveite esses dados sem nova consulta ao NotebookLM. **O formato do RT não
muda os autos em nada**: as regras 7.1 a 7.6 valem iguais para os dois.

#### 7.1. Regras de agrupamento ementa × objeto

- **1 auto por ementa.** Se a ementa aparece para múltiplos objetos, gere 1 auto único que
  liste todos os objetos atingidos na parte 2 (IRREGULARIDADE).
- **N ementas para 1 objeto.** Gere N autos, cada um referenciando aquele objeto.
- A ordem dos autos segue a ordem em que as ementas aparecem na seção 4 do RT.

#### 7.2. Template de cada auto (formato consumido por /aft-gera-ai)

Para cada ementa, monte um bloco EXATAMENTE neste formato:

```
=== AUTO DE INFRAÇÃO #{N} ===
Ementa: {codigo} - {descricao_curta}

I - DA FISCALIZAÇÃO:
Trata-se de ação fiscal (ainda em curso), na modalidade fiscalização mista (nos termos do § 3º, art. 30, do Regulamento da Inspeção do Trabalho - RIT -, aprovado pelo Decreto nº 4.552/2002), no estabelecimento da empresa qualificada. A inspeção física foi realizada em {data_inspecao}. {enriquecimento_contextual}

II - IRREGULARIDADE:
DA INFRAÇÃO COMETIDA: Constatou-se que o empregador aqui autuado incorreu na ementa supracitada, ao {descricao_ementa_min}, {trecho_objetos}, resultando no termo de embargo/interdição em anexo.

O quadro resultante dessa sistematização e análise de informações levou à caracterização da condição de RISCO GRAVE E IMINENTE à saúde e à integridade física dos trabalhadores expostos, na forma conceituada pelo subitem 3.2.1 da Norma Regulamentadora nº 3 do Ministério do Trabalho e Previdência, com atualização dada pela Portaria nº 1.068, de 23 de setembro de 2019: "Considera-se grave e iminente risco toda condição ou situação de trabalho que possa causar acidente ou doença com lesão grave ao trabalhador.", resultando na lavratura do termo de interdição/embargo em anexo.

Exemplo de empregado prejudicado: dano de natureza coletiva. A Portaria MTP nº 667/2021 esclareceu que a citação do empregado em situação irregular faz-se necessária apenas quando imprescindível à caracterização da infração e quando a lei fixar a multa com base no quantitativo de trabalhadores diretamente prejudicados. Ademais, nas infrações que atingem a coletividade dos trabalhadores, tais como naquelas inerentes ao meio ambiente de trabalho (SST), dispensa-se a individualização do sujeito, pois o bem jurídico tutelado tem natureza difusa ou coletiva. (Orientação técnica SIT/n.2/2022).

ELEMENTOS DE CONVICÇÃO:
Inspeção realizada no estabelecimento e relatório técnico do embargo/interdição em anexo.
```

> **NÃO escreva o Subtítulo 3 (OBSERVAÇÕES).** Ele é único e fixo para todo auto e é
> injetado pelo `/aft-gera-ai` (de `config/blocos_auto.md`) entre o Subtítulo 2 e os
> ELEMENTOS DE CONVICÇÃO. O template acima termina, de propósito, no Subtítulo 2 +
> ELEMENTOS DE CONVICÇÃO.

#### 7.2.1. Enriquecimento contextual do Subtítulo 1

`{enriquecimento_contextual}` não é campo novo a coletar: a informação **já foi levantada**
no item 2 do RT (`Contexto-da-inspecao-fisica`), e antes disso no `inspecao-fisica.md`.
Releia esse contexto e transporte para o auto, em prosa corrida, o que ele trouxer. Sem
isso o auto sai anêmico, dizendo apenas "no estabelecimento da empresa qualificada" quando
o RT sabe que se trata de um supermercado com açougue e padaria, quem acompanhou a
inspeção e quantos trabalhadores há no local. Essas informações situam o fato e sustentam
o auto na impugnação.

A **frase-âncora é fixa** e vem primeiro; o contexto vem depois, na sequência. Acrescente
apenas os itens que o contexto fornecer:

| Informação no contexto | Como inserir |
|---|---|
| Atividade econômica, nome fantasia e setores do estabelecimento | `A atividade econômica desenvolvida, identificada na inspeção, é a [atividade].` — havendo nome fantasia e setores: `A inspeção foi realizada no estabelecimento denominado [NOME FANTASIA], que funciona como [atividade], com [setores].` — **opcional**: omita se o contexto não trouxer. |
| Número de trabalhadores do estabelecimento | `O estabelecimento conta com [N] trabalhadores.` |
| Preposto/acompanhante da inspeção física | `A inspeção foi acompanhada pelo preposto [NOME], [função].` |
| Acompanhante da auditoria documental (quando diverso) | `A auditoria de documentos foi acompanhada por [NOME], [função].` |
| Endereço do local fiscalizado (quando difere do endereço do autuado) | `A inspeção foi realizada no estabelecimento localizado na [endereço], distinto do endereço do autuado.` |
| Obra de construção | `Trata-se de obra ([tipo], ex.: prédio) com [N] pavimentos, localizada na [endereço].` |
| Outro CNPJ/empresa no mesmo estabelecimento | `No mesmo estabelecimento funciona também a empresa [NOME] (CNPJ [...]).` |
| Turnos de trabalho | `O estabelecimento opera em [N] turnos ([descrição]).` |

> Regras: (1) só inclua o que o contexto disser; (2) tom oficial, terceira pessoa; (3)
> frase-âncora primeiro, contexto depois; (4) se não houver contexto além da âncora, o
> subtítulo é só a frase-âncora, sem `{enriquecimento_contextual}`.

**O enriquecimento é idêntico em todos os autos do mesmo RT.** Ele descreve a ação fiscal,
não a irregularidade: escreva uma vez e repita literalmente nos N autos. O que varia de
auto para auto é o Subtítulo 2.

**Não migre para cá o que é do Subtítulo 2.** Acidente anterior, número de expostos e
descrição da máquina pertencem à irregularidade e ao RT; o Subtítulo 1 situa a ação fiscal
(quem, onde, o que é o estabelecimento), não o fato autuado.

**Exemplo** (contexto do RT: supermercado com 81 trabalhadores, acompanhado pelo gerente
da loja e, na fase documental, pela gerente de DP):

```
I - DA FISCALIZAÇÃO:
Trata-se de ação fiscal (ainda em curso), na modalidade fiscalização mista (nos termos do § 3º, art. 30, do Regulamento da Inspeção do Trabalho - RIT -, aprovado pelo Decreto nº 4.552/2002), no estabelecimento da empresa qualificada. A inspeção física foi realizada em 05/08/2026. A inspeção foi realizada no estabelecimento denominado Store Supermercados, que funciona como supermercado, com açougue, padaria, estoque de produtos alimentícios em geral, hortifruti e demais setores. O estabelecimento conta com 81 trabalhadores. A inspeção foi acompanhada pelo preposto Educlenio Alves, gerente da loja. A auditoria de documentos foi acompanhada por Raine Dias, gerente de Departamento Pessoal.
```

#### 7.3. Regras de substituição

- `{N}` — índice sequencial começando em 1.
- `{codigo}` — código da ementa no formato `XXXXXX-X` (vindo direto da seção 4 do RT).
- `{descricao_curta}` — descrição da ementa **sem a capitulação**. Ex: para a entrada de
  seção 4 `312358-8 - Deixar de instalar sistemas de segurança em zonas de perigo de máquinas
  e/ou equipamentos. Capitulação: Art. 157, inciso I, da CLT, c/c item 12.5.1 da NR-12...`,
  use `Deixar de instalar sistemas de segurança em zonas de perigo de máquinas e/ou
  equipamentos`.
- `{data_inspecao}` — data da inspeção física no formato `DD/MM/AAAA` (mesma usada na seção
  1 do RT).
- `{enriquecimento_contextual}` — prosa corrida montada pela tabela do item 7.2.1, a partir
  do contexto que já está no item 2 do RT. Idêntica em todos os autos do mesmo RT. Se o
  contexto nada trouxer, remova o marcador e encerre o Subtítulo 1 na frase-âncora, sem
  deixar espaço duplo.
- `{descricao_ementa_min}` — a descrição curta com **a primeira letra em minúscula** e **sem
  ponto final**. Ex: `deixar de instalar sistemas de segurança em zonas de perigo de máquinas
  e/ou equipamentos`.
- `{trecho_objetos}` — texto que cita o(s) objeto(s) atingido(s):
  - 1 objeto: `para o objeto {n} ({DESCRIÇÃO DO OBJETO EM CAIXA ALTA})`.
  - N objetos: `para os objetos {n1} ({DESCRIÇÃO 1}), {n2} ({DESCRIÇÃO 2})`.
  - A descrição do objeto deve vir literal da seção 3 do RT (linha
    `OBJETO: N – TIPO – Paralisação: ...`).

**NUNCA** mencionar número do termo de interdição/embargo nos autos — sempre referenciar
apenas como "termo de interdição em anexo" / "termo de embargo/interdição em anexo".

#### 7.4. Persistir na pasta dedicada

Na mesma pasta `interdicao-embargo/` criada no passo 6, salve:

1. **`autos.md`** — todos os N blocos `=== AUTO DE INFRAÇÃO #N ===` concatenados em ordem,
   separados por uma linha em branco. Encoding UTF-8. Esse arquivo é o input direto do
   `/aft-gera-ai` (modo "texto colado").
2. A cópia do `.docx` do RT já está lá (passo 6) — serve como elemento de convicção /
   anexo de todos os autos.

#### 7.5. Conferir a coerência RT x autos (obrigatório)

As irregularidades do RT e o `autos.md` precisam bater. Eles podem desalinhar quando o RT é
editado (trocar ementas por itens de NR, tirar/incluir irregularidade — ex.: NR-01/NR-35).
Rode o verificador comparando o `.docx` do RT com o `autos.md` (ele reconhece os dois
formatos do RT e, no formato por objeto, conta uma ementa repetida em vários objetos
uma vez só, como a regra 7.1 manda):

```bash
python ~/.claude/skills/_scripts/checar_rt_autos.py "[caminho do RT .docx]" "[caminho do autos.md]"
```

- **Sem divergência** (exit 0) → siga para 7.6.
- **Com divergência** (exit 1: contagem diferente, ou NR no RT sem auto / auto sem item
  no RT) → relate ao AFT em linguagem simples e pergunte como reconciliar (incluir o auto
  faltante, remover o excedente, ou ajustar o RT). **Não encerre como se estivesse coerente.**

#### 7.6. Apresentar e encerrar

- **Imprima no chat os N blocos `=== AUTO DE INFRAÇÃO #N ===` na íntegra** (para o AFT revisar
  visualmente) e indique o caminho da pasta e os arquivos gerados. Exemplo:

  > RT e autos salvos em `<OS_ATIVAS>/{PASTA_EMPRESA}/interdicao-embargo/`
  > (`autos.md` + RT em .docx).

- **Encerramento conforme o modo de entrada:**
  - **Modo A (criou o RT do zero):** **NÃO pergunte** se quer chamar `/aft-gera-ai` nem o chame
    automaticamente — o AFT dispara `/aft-gera-ai` por conta própria quando estiver pronto para
    transmitir.
  - **Modo B (RT/Termo anexado + pedido de autos):** depois de mostrar os autos, **pergunte
    ao AFT se estão OK** (ex.: *"Os autos acima estão OK para empacotar?"*). **Se ele
    confirmar, chame a skill `/aft-gera-ai`** apontando para o `autos.md` desta pasta (anexando o
    RT/Termo aos autos). Se ele pedir ajustes, corrija e mostre de novo antes do `/aft-gera-ai`.

- **E-mail de encaminhamento (nos dois modos):** ao fechar, ofereça `/aft-email` para redigir o
  e-mail que encaminha o Termo à empresa/advogado — ele já traz o bloco fixo de como pedir a
  suspensão pelo SEI. Só ofereça; quem envia é o AFT.

---

## Estrutura do documento (referência)

```
[CABEÇALHO — fixo: MTE / SIT / SRTE / Setor de Inspeção / logos]

RELATÓRIO TÉCNICO
TERMO DE INTERDIÇÃO Nº [NÚMERO]

EMPREGADOR: [NOME]
CNPJ: [CNPJ]

FORMATO POR TÓPICO (padrão):
1. OBJETIVO — fixo + frase da data da inspeção física
2. DA AÇÃO FISCAL — fixo (adaptar NR citada se necessário)
3. OBJETOS INTERDITADO — OBJETO: N – TIPO — Paralisação: TOTAL/PARCIAL
4. IRREGULARIDADES — metodologia NR-3 fixa + ementas (formato XXXXXX-X)
5. FATORES DE RISCO E/OU RISCOS RELACIONADOS — preencher
6. MEDIDAS DE PROTEÇÃO A ADOTAR — preencher
7. DOCUMENTOS SOLICITADOS — preencher
8. CONCLUSÃO/OBSERVAÇÃO — preencher

FORMATO POR OBJETO:
1. OBJETIVO — fixo
2. DA AÇÃO FISCAL — fixo + metodologia NR-3 fixa (migra da seção 4)
3. OBJETOS INTERDITADO — para CADA objeto:
   OBJETO: N – TIPO — Paralisação: TOTAL/PARCIAL + descrição
   Irregularidade(s) · Fatores de Risco · Medidas de Proteção · Documentos
4. CONCLUSÃO/OBSERVAÇÃO — preencher (renumeração automática do Word)

[DO PEDIDO DE SUSPENSÃO DA INTERDIÇÃO — fixo]
[Instruções SEI — fixas]
[Observação sobre recurso — fixa]

[CIDADE]-[UF], [DATA]

[NOME DO AFT]
Auditor-Fiscal do Trabalho
Competência delegada pela Portaria 1719/2014...
```

---

## Regras de redação

- Linguagem técnica e objetiva, adequada para documentos oficiais.
- Texto limpo: sem colchetes, marcações ou referências de fonte no documento final.
- Não alterar nenhum conteúdo fixo do modelo.
- Se alguma seção não tiver dados do usuário, inserir `[A PREENCHER]` e informar o usuário.
- Manter a formatação (fontes, espaçamentos, tabulações) do modelo original.

---

## Comportamento em casos especiais

| Situação | Ação |
|---|---|
| Múltiplos objetos interditados | Replicar a estrutura da seção 3 para cada objeto |
| Objetos de TIPOS diferentes (máquina + setor, atividade + setor...) | Perguntar OBRIGATORIAMENTE ao AFT: RT por TÓPICO ou por OBJETO (passo 0-bis) — nunca escolher em silêncio |
| Objetos todos do mesmo tipo | Formato por tópico, sem perguntar — a menos que o AFT peça por objeto |
| AFT pede "RT por objeto" | `"formato": "objeto"` no JSON, com as 4 listas dentro de cada objeto (passo 0-bis) |
| Formato por objeto: ementa atinge mais de um objeto | Repetir a ementa no bloco de cada objeto atingido; no passo 7 continua rendendo 1 auto só |
| Formato por tópico com mais de um objeto | Prefixar os itens das seções 4, 6 e 7 com `Objeto N - ...` e citar o objeto na descrição do item 5 |
| NR diferente da NR-12 | Ajustar a referência legal na seção 2 e na seção 4 |
| Paralisação parcial | Indicar "Paralisação: PARCIAL" com especificação do escopo |
| Ausência de algum dado | Inserir `[A PREENCHER]` e listar os campos pendentes ao usuário |
| PDFs de termos/autos anexados | Extrair os dados automaticamente dos documentos antes de preencher |
| Data da inspeção não encontrada no contexto | Perguntar ao usuário antes de continuar |
| Nenhuma camada retorna código de ementa | Inserir `[EMENTA A PREENCHER]` e listar ao AFT ao final |
| Múltiplas irregularidades | Consultar NotebookLM em paralelo, uma pergunta por irregularidade |
| Mesma ementa atinge múltiplos objetos | 1 único auto na Fase 7, listando todos os objetos na parte 2 (não duplicar) |
| Ementa ficou como `[EMENTA A PREENCHER]` no RT | Pular esta ementa na Fase 7 e avisar o AFT no fechamento |
| AFT em dúvida se a situação justifica interdição | Modo C: consultar o notebook `interdicoes` e apresentar precedentes análogos — sugerir, nunca decidir |
| Key `interdicoes` ausente no notebooks.json | Pular a camada de precedentes sem alarde; no Modo C, analisar pelos critérios da NR-03 e avisar que a base não está configurada |
| Pasta `interdicao-embargo/` já existe (mesmo termo) | Reutilizar; sobrescrever `autos.md` e a cópia do `.docx` é idempotente (backup automático antes) |
| Pasta `interdicao-embargo/` já tem RT/autos de OUTRO termo | Sufixar os arquivos novos com o nº do termo (`RT_Interdicao_<termo>.docx`, `autos_<termo>.md`) para não sobrescrever |
| AFT de outra SRTE | Template é universal, nenhum ajuste necessário |
| Medida recai sobre **obra** | É EMBARGO, não interdição (subitem 3.2.2.1 da NR-03) — aplicar as trocas do passo 0 |
| Irregularidade só em parte da obra/estabelecimento | Paralisação PARCIAL delimitando o escopo (pavimentos, setor, máquinas), pela regra da menor unidade possível (3.2.2.3.1 da NR-03) |
| AFT quer foto no RT | Passo 4-bis (`inserir_foto_docx.py`); se a imagem só existir colada no chat, pedir ao AFT para salvá-la como arquivo |
| Máquina interditada tem anexo próprio na NR-12 | Item 7 deve exigir laudo **conclusivo pela adequação ao anexo**, citando anexo e item (ver "Como pedir laudo de máquina") |
| Autos saem sem contexto ("no estabelecimento da empresa qualificada" e nada mais) | Faltou o enriquecimento do item 7.2.1: o contexto já está no item 2 do RT, transporte-o para o Subtítulo 1 |
| Anexo da máquina desconhecido | Consultar `references/anexos-nr12.md`; se a máquina não estiver lá, resolver pelo notebook da NR — nunca presumir pela semelhança física |
| Máquina sem anexo próprio (maioria dos casos) | Item 7 pede ART e laudo do sistema de segurança citando os itens gerais violados, sem inventar anexo |
| Anexo dispensa o que se ia exigir | Conferir a seção "Armadilhas" de `references/anexos-nr12.md` antes de fechar o item 7 |
| Várias ementas da mesma máquina | Um único laudo conclusivo pelo anexo cobre todas; não desmembrar o item 7 em um documento por ementa |
| Placeholder `{{chave}}` não encontrado | Foi apagado do template. Recolocá-lo no Word, exatamente com duas chaves e sem espaços internos, ou usar o fallback manual |
| Sobrou `{{...}}` no documento final | O script aborta antes de gravar: falta o campo no JSON. Conferir o dicionário |
| Medidas ou documentos com "A)", "B)" digitados | Remover: a numeração das alíneas é automática no Word e o script insere os itens como lista real |
| Texto gerado sai em fonte diferente do resto | O estilo `Normal` do template é Verdana e o corpo só fica em Tahoma porque cada run declara a fonte. O `montar_rt.py` detecta a fonte dominante e a aplica no que gera — se ainda assim divergir, conferir se o placeholder novo tem `rFonts` |
| Imagem do template repetida N vezes | Placeholder com figura ancorada no mesmo parágrafo. O script mantém a imagem só na primeira cópia — conferir se a contagem de imagens do RT bate com a do template |
