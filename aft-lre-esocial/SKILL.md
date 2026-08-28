---
name: aft-lre-esocial
model: sonnet
effort: low
allowed-tools: Read, Glob, Grep, Bash, Write, Edit, AskUserQuestion
description: >
  Use quando o AFT quiser ler o Livro de Registro de Empregados (LRE) que o
  SISFGTS baixou do eSocial e transformá-lo em painel navegável dentro da
  pasta da OS. Dispare com /aft-lre-esocial, "LRE do eSocial", "livro de
  registro de empregados", "vínculos do eSocial", "puxa o LRE dessa
  empresa", "quem está registrado no eSocial", "quadro de empregados",
  "registro tardio", "quem foi admitido sem registro no prazo" — e também
  para as análises derivadas: "férias vencidas", "férias em atraso",
  "auditoria de férias", "quem está sem gozar férias", "buraco na folha",
  "mês sem remuneração declarada", "auditar a remuneração do eSocial".
  Aceita 0 ou 1 argumento (CNPJ ou parte do nome da empresa); sem
  argumento, oferece as OS ATIVAS que já têm dados baixados no SISFGTS.
  Read-only sobre o SISFGTS: nunca escreve nele nem no banco Firebird.
---

# lre-esocial — Livro de Registro de Empregados (eSocial)
**AFT Toolkit** (Windows / Mac com Parallels)

> **Onde ficam as pastas das OS.** O AFT pode ter mudado a pasta de trabalho de
> lugar. Nunca presuma `~/Documents/AFT`: resolva **uma vez, no início**, e use o
> que voltar onde este texto disser `<OS_ATIVAS>`.
>
> **Nas mensagens ao AFT, escreva o caminho de verdade** — nunca ecoe
> `<OS_ATIVAS>` na tela.
>
> ```bash
> python ~/.claude/skills/_scripts/pasta_aft.py --os-ativas
> ```

## Quando usar

Use quando o AFT já baixou os dados do eSocial de uma empresa **dentro do
SISFGTS** e quer trabalhar esses vínculos na auditoria: ver quem está
registrado, quem foi desligado e por quê, e **quais admissões chegaram ao
eSocial fora do prazo**. Se o download incluiu os demais registros
(afastamentos e folha), a skill oferece ainda **duas análises derivadas**:
a auditoria de **férias** (vencidas, gozadas fora do prazo, prazo vencendo)
e a auditoria da **remuneração declarada** (buracos na folha, 13º sem base,
remuneração abaixo do contratual, desligado sem base rescisória).

Cenários típicos:
- Logo depois de baixar o eSocial no SISFGTS, para levar o quadro para a OS.
- Antes da inspeção, para saber o efetivo declarado e os cargos.
- Ao apurar registro em atraso (art. 41 da CLT) — a skill levanta o **indício**.
- Ao apurar férias não concedidas no prazo (arts. 134 e 137 da CLT).
- Para cruzar com a folha, o AFD/AEJ ou a relação de vínculos.

**Não** acione para lavrar auto (é `/aft-auditoria-geral`), para trabalhador sem
registro nenhum (é `/aft-informalidade`) nem para analisar ponto (é
`/aft-jornada-analise`).

## Pré-condições

- **SISFGTS instalado e com o eSocial já baixado** para o CNPJ. O download é
  feito no SISFGTS pelo próprio AFT; esta skill **não** acessa a API do SIT nem
  faz login em lugar nenhum: ela só lê o arquivo que o SISFGTS gravou.
  - **Windows:** caminho padrão `C:\SistemasAFT\SisFGTS\Arquivos\eSocial\`.
  - **Mac com Parallels:** o disco C: precisa estar compartilhado/montado (aparece
    como `/Volumes/[C] Windows 11/...`). O script **detecta sozinho** sob
    `/Volumes/*/SistemasAFT/SisFGTS`. Se o volume não estiver montado, peça ao AFT
    **em uma frase** para reativar o compartilhamento do disco no Parallels.
  - Instalação fora do padrão: passe a base com `--sisfgts "<caminho>"`.
- Pasta da OS em `<OS_ATIVAS>/<NOME_DA_OS>`, com CNPJ no nome da pasta ou no
  `memory.md`.
- **Nada além do Python padrão.** Sem pip, sem driver de banco, sem rede.

## Constantes

- **Pasta do eSocial no SISFGTS:** `<SISFGTS>\Arquivos\eSocial\<CNPJ14>\`
  — a pasta é o **CNPJ de 14 dígitos puro** (ex.: `00241190000139`).
- **Padrão do arquivo:** `eSocial_idA_LRE_<n>_<8 primeiros dígitos>.txt`
  (ex.: `eSocial_idA_LRE_1_00241190.txt`).
- **O LRE é multi-parte.** O SISFGTS pagina de **1.000 em 1.000** vínculos: uma
  empresa grande tem `_1_`, `_2_`, ... `_16_`. **Ler só a parte 1 perde os demais
  trabalhadores e falseia todos os números.** O script junta todas — nunca
  contorne isso lendo um arquivo só.
- **Outros grupos na mesma pasta**: `idB`=alterações · `idK`=afastamentos ·
  `idM`=folha · `idR`=rubricas. O painel do LRE usa só o `idA`; a análise de
  férias usa `idA`+`idK`; a análise da folha usa `idA`+`idM`+`idK`. Os grupos
  `idK`/`idM` só existem se o AFT baixou o eSocial no SISFGTS com a opção
  **"LRE e demais registros"** — se faltarem, os scripts avisam com essa frase.
- **Saída:** subpasta `eSocial/` **dentro da pasta da OS**.

## Passo a passo

### Passo 1 — Resolver a OS e o CNPJ

1. Resolva `<OS_ATIVAS>` (bloco do topo).
2. Descubra o **CNPJ** da OS, nesta ordem:
   - regex `^(.+) (\d{14})$` sobre o nome da pasta da OS;
   - senão, o campo `cnpj:` (ou `**CNPJ:**`) do `memory.md`.
3. **Com argumento do AFT:** 14 dígitos (limpando pontuação) → match exato;
   texto → match por parte do nome da pasta. Se casar mais de uma, pergunte
   com `AskUserQuestion`.
4. **Sem argumento:** liste as OS ATIVAS que **já têm** pasta no SISFGTS e
   deixe o AFT escolher. Para descobrir quais têm, rode o `--achar` de cada
   CNPJ (é barato) ou liste a pasta do eSocial do SISFGTS e cruze.

> **CPF/CAEPF não serve.** O LRE do SISFGTS é por CNPJ de 14 dígitos. Numa OS de
> empregador pessoa física, avise que não há LRE a importar.

### Passo 2 — Conferir se há arquivo (antes de prometer resultado)

```bash
python ~/.claude/skills/_scripts/lre_esocial.py --achar <CNPJ14>
```

Ele responde onde achou o SISFGTS e quantas partes do LRE existem. Se responder
`NAO ENCONTRADO`, é volume não montado ou instalação fora do padrão. Se responder
`NENHUM ARQUIVO`, **o AFT ainda não baixou o eSocial daquele CNPJ no SISFGTS** —
diga isso em uma frase, sem rodeios, e pare.

### Passo 3 — Gerar

```bash
python ~/.claude/skills/_scripts/lre_esocial.py "<pasta da OS>" <CNPJ14> "<EMPREGADOR>"
```

Grava dentro da OS:

| Arquivo | O que é |
|---|---|
| `eSocial/LRE_painel.html` | painel interativo: busca dinâmica por nome/CPF/matrícula/cargo, filtros (ativos, desligados, indício, PCD), colunas ordenáveis, paginação e detalhe por trabalhador |
| `eSocial/LRE_vinculos.csv` | planilha dos vínculos, `;` como separador (abre em colunas no Excel pt-BR) |
| `eSocial/lre-esocial.md` | resumo **sem nome e sem CPF** — aparece em "Relatórios da OS" no `/aft-painel` |
| `eSocial/resumo.json` | números agregados que o `/aft-painel` lê para montar o cartão |

### Passo 3b — Oferecer as análises de férias e de folha

O `--achar` do Passo 2 já diz se o CNPJ tem afastamentos (`idK`). Se tiver,
**ofereça as duas análises** logo depois do painel do LRE (não rode sem avisar:
cada uma gera mais quatro arquivos na OS). Se o AFT pediu diretamente
("férias vencidas", "buraco na folha"), rode direto a que ele pediu.

```bash
python ~/.claude/skills/_scripts/lre_ferias.py "<pasta da OS>" <CNPJ14> "<EMPREGADOR>"
python ~/.claude/skills/_scripts/lre_folha.py "<pasta da OS>" <CNPJ14> "<EMPREGADOR>"
```

| Arquivo | O que é |
|---|---|
| `eSocial/Ferias_painel.html` | painel de férias por trabalhador: seção **"Leitura da auditoria"** (os indícios caso a caso, em frases prontas), períodos aquisitivos, prazo concessivo, gozo, indícios (vencidas, fora do prazo, vencendo, abono, fracionamento) |
| `eSocial/Ferias_analise.csv` | um período aquisitivo auditado por linha |
| `eSocial/ferias.md` | resumo **sem nome e sem CPF** |
| `eSocial/ferias_resumo.json` | números agregados (sem PII) |
| `eSocial/Folha_painel.html` | painel da remuneração declarada: grade mês a mês por trabalhador, buracos, 13º, comparação com o salário contratual, bases rescisórias |
| `eSocial/Folha_analise.csv` | um vínculo por linha, com os meses furados |
| `eSocial/folha.md` | resumo **sem nome e sem CPF** |
| `eSocial/folha_resumo.json` | números agregados (sem PII) |

Se os grupos `idK`/`idM` não existirem, o script explica que falta baixar o
eSocial com a opção **"LRE e demais registros"** no SISFGTS — repasse a frase
ao AFT e pare; quem baixa é ele.

### Integração com o `/aft-painel`

Na tela de detalhe da OS aparece um cartão **eSocial** com os agregados do LRE
(*ativos* e *indício de registro tardio*) e, quando as análises derivadas já
rodaram, mais duas linhas de números — férias (*vencidas*, *gozo fora do
prazo*, *prazo vencendo*) e folha (*buracos*, *ano sem 13º*, *sem base
rescisória*) — e até três links: **abrir o painel do LRE**, **painel de
férias** e **painel da folha**, cada um em outra aba.

O cartão é **aditivo e silencioso**: só existe se a OS tiver
`eSocial/resumo.json` **e** `eSocial/LRE_painel.html`; as linhas de férias e
folha só aparecem se o `*_resumo.json` e o painel `.html` correspondentes
existirem. OS que nunca rodaram esta skill não mostram nada — nem todo AFT
baixa esses dados do SISFGTS.

Os links só funcionam no **modo interativo** (painel servido pelo
`servir_painel.py` em `127.0.0.1`), pelas rotas `/lre/<pasta da OS>`,
`/ferias/<pasta da OS>` e `/folha/<pasta da OS>`. Num `painel.html` aberto
direto do disco, o cartão mostra os números e informa que os painéis estão na
pasta `eSocial/` da OS, sem link — navegador não segue `file://` a partir de
`http://`. As rotas validam o nome da pasta contra as OS que existem de fato,
o que impede subir diretório para ler arquivo de fora.

### Passo 4 — Relatar ao AFT

Mostre o resumo em linguagem simples: total de vínculos, ativos, desligados,
PCD e o número de **indícios de registro tardio** — este último **sempre
acompanhado do recorte**: "N indícios entre as X admissões desde 02/01/2026". Informe o caminho real da
pasta `eSocial/` e diga que o painel abre com duplo clique.

Se rodou férias/folha, acrescente os números de cada uma **com a natureza do
achado**: férias vencidas e gozo fora do prazo são indício de **dobra**
(arts. 134 e 137 da CLT; Súmula 81 do TST); buraco na folha é mês sem base
declarada **e sem afastamento que o justifique**. Lembre que gozo de 20 a 29
dias pode ser abono pecuniário regular (art. 143) e que a folha mostra a base
**declarada**, não o recolhimento — FGTS em atraso quem aponta é o SISFGTS.

**Sempre** repita o aviso: *tudo é indício, não prova* — confirmar nos recibos
de férias e na folha de pagamento antes de autuar — e que os arquivos têm
dados pessoais e são locais.

### Passo 4b — Registrar no memory.md

Registre a análise no `memory.md` da OS (backup antes, com `backup_arquivo.py`): na
seção `## Auditoria de documentos` (nas OS anteriores à renomeação ela se chama
`## Anotações da auditoria`: escreva na que existir, sem renomeá-la; se nenhuma existir,
crie `## Auditoria de documentos`), acrescente ao **final da seção** uma subseção
`### eSocial` (se ainda não houver) e, nela, uma linha datada:

```
### eSocial
dd/mm/aaaa — <resumo em até 2 linhas: vínculos, indícios de registro tardio e, se
rodadas, férias/folha — sempre como indício> — painéis: eSocial/
```

Três regras do registro: (1) é **prosa** — nunca comece a linha com `-`: na seção,
bullet é constatação avulsa que a `/aft-auditoria-geral` transforma em auto, e indício
ainda não confirmado não é constatação; (2) **até 2 linhas** por rodada; (3) rodada nova
acrescenta outra linha datada na mesma subseção, mantendo as anteriores.

### Passo 5 — Registrar no diário

```bash
python ~/.claude/skills/_scripts/diario_registrar.py "<pasta da OS>" --tipos D --detalhe "Análise do LRE do eSocial (<n> vínculos)"
```

## Como o indício de registro tardio é apurado

- **Recorte temporal: só admissões a partir de 02/01/2026.** Foi a partir dessa
  data que o registro eletrônico de empregados no LRE do eSocial passou a ser
  obrigatório para **todas** as empresas, sem distinção — antes disso a
  obrigatoriedade era escalonada por grupo de empregador. Apontar "registro
  tardio" para admissão anterior levaria o AFT a perseguir vínculo que talvez
  nem estivesse obrigado ao registro eletrônico.
  > **Frise sempre o recorte ao relatar.** O número de indícios NÃO é do
  > histórico inteiro da empresa: é só de 02/01/2026 em diante. Dizer "12
  > indícios" sem a data engana — o correto é "12 indícios entre as admissões
  > desde 02/01/2026". A constante fica em `MARCO_LRE`, no topo do script.
  >
  > Há outras hipóteses de obrigatoriedade anteriores a essa data, ainda não
  > tratadas pela skill.

- **Campo usado: `dhrecepcao`** — quando o eSocial **recebeu** o evento do
  empregador. **Nunca use `processamento_datahora`**: é processamento interno e
  produz falso positivo grosseiro (evento recebido em 2020 e processado em 2022
  aparece como +792 dias de atraso, quando o atraso real foi de 4 dias).
- **Critério:** recepção **na data da admissão ou depois**. O evento S-2200 é
  devido até o dia **imediatamente anterior** ao início da prestação de serviços.
- **Só admissão nova conta (`tpadmissao = 1`).** Em cessão (`4`), transferência
  de mesmo grupo (`2`) ou por sucessão (`3`), mudança de CPF (`5`) e transferência
  de doméstico (`6`), o `dtadm` é a data de admissão **original**, herdada do
  empregador de origem — a recepção ocorre naturalmente muito depois, e isso
  **não é registro tardio**. Ignorar essa distinção produz falso positivo
  grosseiro: num caso real, 26 de 38 "indícios" eram trabalhadores cedidos.
- **Recepção em massa descontada.** Quando o empregador entrou no eSocial, os
  vínculos preexistentes foram recepcionados em bloco — e o mesmo ocorre em
  retransmissões em lote. Isso **não** é atraso. O script detecta essas datas
  pela assinatura própria de uma carga: **muitos** contratos, com admissões
  espalhadas por um período **longo** (> 1 ano), todos recebidos no **mesmo dia**.
  > **Não basta pegar "a data mais repetida".** Numa empresa que já nasceu no
  > eSocial não há carga alguma, e a data mais repetida é só o dia mais
  > movimentado — tratá-la como carga descarta centenas de vínculos da análise e
  > **esconde atraso real**. Num caso real isso derrubou os indícios de 28 para 9.
- **`evtAdmPrelim` é separado** de `evtAdmissao` no relatório: a admissão
  preliminar tem regime de prazo próprio e não deve ser lida junto.
- **"Mesmo dia" é separado de "depois".** Recepção na própria data da admissão é
  atraso de 1 dia pela letra da regra, mas de gravidade bem diferente de meses de
  atraso. O relatório mostra os dois números para o AFT ponderar.

> **É indício, não prova.** O arquivo mostra que a *transmissão* atrasou; não
> prova que o trabalhador estava sem registro. Pode haver ficha/livro regular com
> transmissão tardia — que é outra infração, de outro enquadramento. **Quem
> decide é o AFT**, conferindo caso a caso. Se for enquadrar, confirme ementa e
> capitulação pelo `/aft-consulta`; **nunca invente código**.

## Como a auditoria de férias é apurada (`lre_ferias.py`)

Reconstitui os **períodos aquisitivos** (PA) de 12 meses a partir da admissão
do LRE e casa cada PA com os afastamentos código 15 (férias) do grupo `idK`.
Regras, todas documentadas no script:

- **art. 134 + art. 137:** PA com prazo concessivo vencido sem gozo suficiente
  = *férias vencidas* (indício de dobra). **Súmula 81 do TST:** dias gozados em
  bloco iniciado após o prazo = *gozo fora do prazo* (dobra devida mesmo tendo
  gozado).
- **Abono pecuniário (art. 143) não aparece no arquivo.** Gozo de 20 a 29 dias
  com prazo vencido vira "conferir abono", nunca dobra firme; dobra firme só
  com gozo **abaixo de 20 dias**. Pela mesma razão, bloco de férias iniciado
  após o prazo de um PA só completa esse PA até os 20 dias mínimos — o
  excedente pertence ao PA seguinte. O que se reporta é o **mínimo certo**.
- **Faltas injustificadas (art. 130) não constam** — assume-se direito a 30
  dias. Mais um motivo de ser indício, não prova.
- **art. 133, IV:** mais de 180 dias previdenciários dentro do PA zeram o PA
  (contam-se os dias que excedem 15 por episódio de afastamento).
- **Fracionamento (art. 134 §1º):** mais de 3 frações, fração menor que 5 dias
  ou nenhuma de pelo menos 14 — apontado só quando a alocação não dividiu
  blocos entre PAs (o corte artificial falsearia).
- **Janela de dados — a proteção principal contra falso positivo:** só são
  auditados PAs **iniciados depois** que a empresa entrou no eSocial (primeira
  recepção no LRE), e vínculo vindo por sucessão/cessão
  (`sucessaovinc_dttransf`) só é auditado a partir da **transferência**:
  férias anteriores podem ter sido gozadas no empregador anterior sem deixar
  rastro no arquivo. Num caso real, ignorar isso multiplicava os indícios por
  dez — todos falsos.

> **É indício, não prova.** Confirmar nos recibos de férias e na folha antes
> de autuar; ementa e capitulação pelo `/aft-consulta` — **nunca invente
> código**.

## Como a folha é auditada (`lre_folha.py`)

Usa a base **declarada** de FGTS por mês (tpValor 11 do S-5003, grupo `idM`),
cruzada com o LRE e os afastamentos:

- **Buraco na folha:** mês dentro do vínculo sem base declarada e sem
  afastamento cobrindo 20 dias ou mais dele (férias não justificam buraco:
  são remuneradas). Vínculo vindo por sucessão/cessão só conta a partir da
  transferência — antes disso a folha era do empregador de origem.
- **13º sem base:** ano fechado, com pelo menos 3 meses de base e sem
  desligamento no ano, sem nenhuma base de 13º (tpValor 12).
- **Abaixo do contratual:** os **últimos 3 meses fechados** abaixo de 90% do
  salário do LRE (só salário mensal e vínculo ativo). Compara-se presente com
  presente: mês antigo abaixo do salário **atual** é normal para quem teve
  aumento.
- **Sem base rescisória:** dispensa por iniciativa do empregador (motivos
  02/03) sem nenhuma base rescisória de FGTS (tpValor 21/22).

> **Base declarada não é recolhimento.** FGTS em atraso quem aponta é o
> próprio SISFGTS — esta análise olha a remuneração e o vínculo, não o débito.

## Tabelas de código

As descrições (motivo de desligamento, raça/cor, grau de instrução, jornada,
unidade salarial, tipo de admissão) estão no script e foram **conferidas contra o
de-para do próprio SISFGTS**. Código que não estiver na tabela **não é
adivinhado**: aparece como *"(código não mapeado - conferir tabela do eSocial)"*.
Se o AFT vir essa marca, é sinal de que vale conferir a tabela oficial — e me
avisar, para incluirmos.

**CBO:** a tabela tem ~2.600 códigos e **não vem no LRE** — o arquivo traz só
`codcbo`. O toolkit embarca `_scripts/cbo.json` com **2.687 ocupações**, e o
painel traduz sozinho. Código fora da tabela aparece como `CBO <número>`, sem
palpite.

> **Procedência:** a tabela foi extraída **uma única vez** do próprio banco do
> SISFGTS (tabela `CBO`, campos `CD_CBO`/`DS_CBO`, em `SISFGTS-DADOS.FDB`) e
> gravada como arquivo estático. Em execução a skill **não** toca no banco: lê
> o `cbo.json`, sem driver Firebird, sem dependência e sem risco de esbarrar no
> arquivo enquanto o SISFGTS estiver aberto.
>
> A extração foi conferida contra o de-para do próprio SISFGTS (19 CBOs de
> gabarito: 19/19 corretos, 0 divergências) e contra o uso real (287 de 288
> códigos distintos em 26.741 vínculos — 99%). O único ausente (`321110`) não
> existe na tabela do SISFGTS. Se a CBO for atualizada, basta regerar o
> `cbo.json`; nada mais muda.

## Privacidade

- O `LRE_painel.html` e o `LRE_vinculos.csv` — e igualmente `Ferias_painel.html`,
  `Ferias_analise.csv`, `Folha_painel.html` e `Folha_analise.csv` — têm **nome,
  salário e afastamentos** de trabalhadores. São arquivos **locais**: não
  publicar, não anexar em e-mail, não subir para nuvem, não gerar como Artifact.
- **CPF completo só no LRE** (que é o livro de registro). Os painéis e CSVs de
  férias e folha mostram o CPF **mascarado** (`***.***.NNN-NN`): matrícula e
  nome bastam para o trabalho, e o dado inteiro não circula à toa.
- Os `.md` (`lre-esocial.md`, `ferias.md`, `folha.md`) são os únicos sem dado
  nominal — por isso são eles que aparecem no `/aft-painel`.
- O HTML é autocontido (CSS/JS embutidos, **sem CDN**): abre offline e não faz
  requisição nenhuma.
- A skill **não** acessa a API do SIT, não faz login e **não lê o banco Firebird**
  do SISFGTS. Só lê o arquivo `.txt` que o SISFGTS já gravou.

## Detalhes do formato (para quem for dar manutenção)

- O arquivo tem extensão `.txt` mas é **JSON**, gravado em **latin-1** — abrir
  com `encoding="latin-1"` (utf-8 quebra em nome acentuado).
- Estrutura: `{"isSucess": true, "isEmptyResult": false, "result": [ ... ]}`,
  um objeto por vínculo, ~60 campos com os nomes do leiaute do eSocial.
- Datas em dois formatos: `dtadm`/`dtdeslig`/`dtnascto` em ISO
  (`1994-03-01T00:00:00`); `dhrecepcao` como `2020-02-19 18:28:06`;
  `processamento_datahora` como **epoch em milissegundos**.
- Campos condicionais (só aparecem quando há): bloco PCD (`def*`, `infocota`),
  CTPS (`seriectps`, `nrctps`), sucessão (`cnpjsucessora`), `nistrab` (PIS).
- **Grupo `idK` (afastamentos):** um registro por afastamento, com `cpftrab`,
  `matricula`, `codmotafast` (tabela 18 do eSocial: `01` acidente/doença do
  trabalho, `03` doença comum, `15` férias, `17` licença maternidade),
  `dtiniafast` e `dttermafast` (último dia afastado; em aberto = sem o campo).
- **Grupo `idM` (folha):** um registro por base de FGTS, com `perapur`
  (`AAAA-MM`, ou `AAAA` no 13º), `remFGTS` (valor) e `tpValor` (S-5003):
  `11` remuneração mensal, `12` 13º salário, `21`/`22` bases rescisórias
  (conferido empiricamente: só aparecem em desligados, e nas dispensas sem
  justa causa). Tipos `13`/`14` existem mas não têm leiaute confirmado —
  os scripts os exibem sem juízo, como "outras bases".
