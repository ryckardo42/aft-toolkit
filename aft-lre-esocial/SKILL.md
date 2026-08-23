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
  "registro tardio", "quem foi admitido sem registro no prazo". Aceita 0 ou
  1 argumento (CNPJ ou parte do nome da empresa); sem argumento, oferece as
  OS ATIVAS que já têm dados baixados no SISFGTS. Read-only sobre o
  SISFGTS: nunca escreve nele nem no banco Firebird.
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
eSocial fora do prazo**.

Cenários típicos:
- Logo depois de baixar o eSocial no SISFGTS, para levar o quadro para a OS.
- Antes da inspeção, para saber o efetivo declarado e os cargos.
- Ao apurar registro em atraso (art. 41 da CLT) — a skill levanta o **indício**.
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
- **Outros grupos na mesma pasta** (esta skill usa apenas o `idA`):
  `idB`=alterações · `idK`=afastamentos · `idM`=folha · `idR`=rubricas.
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

### Integração com o `/aft-painel`

Na tela de detalhe da OS aparece um cartão enxuto **LRE eSocial** com dois
números — *ativos* e *indício de registro tardio* — e o link **abrir o painel do
LRE**, que abre o `LRE_painel.html` em outra aba.

O cartão é **aditivo e silencioso**: só existe se a OS tiver
`eSocial/resumo.json` **e** `eSocial/LRE_painel.html`. OS que nunca rodaram esta
skill não mostram nada — nem todo AFT baixa esses dados do SISFGTS.

O link só funciona no **modo interativo** (painel servido pelo
`servir_painel.py` em `127.0.0.1`), pela rota `/lre/<pasta da OS>`. Num
`painel.html` aberto direto do disco, o cartão mostra os números e informa o
caminho do arquivo, sem link — navegador não segue `file://` a partir de
`http://`. A rota valida o nome da pasta contra as OS que existem de fato, o que
impede subir diretório para ler arquivo de fora.

### Passo 4 — Relatar ao AFT

Mostre o resumo em linguagem simples: total de vínculos, ativos, desligados,
PCD e o número de **indícios de registro tardio** — este último **sempre
acompanhado do recorte**: "N indícios entre as X admissões desde 02/01/2026". Informe o caminho real da
pasta `eSocial/` e diga que o painel abre com duplo clique.

**Sempre** repita o aviso: *registro tardio é indício, não prova* — e que os
arquivos têm dados pessoais e são locais.

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

- O `LRE_painel.html` e o `LRE_vinculos.csv` têm **nome, CPF, endereço e salário**
  de trabalhadores. São arquivos **locais**: não publicar, não anexar em e-mail,
  não subir para nuvem, não gerar como Artifact.
- O `lre-esocial.md` é o único sem dado nominal — por isso é ele que o
  `/aft-painel` exibe.
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
