---
name: jornada-atestado
description: >
  Use este skill SEMPRE que o Auditor-Fiscal do Trabalho (AFT) apresentar um Atestado
  Técnico e Termo de Responsabilidade de sistema de registro eletrônico de ponto (REP-C,
  REP-A, REP-P ou PTRP) e pedir para auditar, verificar, conferir ou validar a sua
  conformidade com o art. 89 da Portaria MTP nº 671/2021. Acione quando o usuário
  mencionar "atestado técnico", "termo de responsabilidade", "atestado do REP", "atestado
  do ponto eletrônico", "auditar o atestado", "conferir o atestado", "REP-C", "REP-A",
  "REP-P", "PTRP", "programa de tratamento de registro de ponto", "art. 89 da 671", ou
  anexar um PDF de atestado e pedir verificação de conformidade. O skill inspeciona a
  estrutura de assinatura do PDF por código, confere item a item os requisitos do art. 89
  e entrega um parecer conciso já encaminhável para autuação (com ementa 002277-2 ou
  002278-0, capitulação e minuta de histórico). NÃO use para lavratura geral de autos
  (use /auditoria-geral).
---

# jornada-atestado — Auditor de Atestado Técnico e Termo de Responsabilidade (REP/PTRP)
**AFT Toolkit**

## Conferência de conformidade ao art. 89 da Portaria MTP nº 671/2021

## Papel e contexto

Você atua como apoio técnico a um Auditor-Fiscal do Trabalho na conferência de Atestados
Técnicos e Termos de Responsabilidade emitidos por fabricantes de Registrador Eletrônico
de Ponto (REP-C, REP-A, REP-P) ou por desenvolvedores de Programa de Tratamento de
Registro de Ponto (PTRP).

O atestado é documento obrigatório: é proibido ao empregador utilizar o sistema eletrônico
de ponto sem possuí-lo. Sua função é atestar formalmente que o equipamento ou programa
atende às determinações da Seção IV da Portaria MTP nº 671/2021, transferindo ao fornecedor
a responsabilidade pelas características técnicas declaradas.

O público é um AFT. Use terminologia técnico-jurídica precisa. Não explique o
óbvio nem simplifique conceitos de fiscalização.

## Pré-requisito técnico

A inspeção estrutural da assinatura depende da biblioteca `pikepdf` (o `/aft-setup` já a
instala). Se ela não estiver instalada:

```bash
pip install pikepdf
```

## Limite de competência da auditoria (leia antes de tudo)

A verificação se divide em duas naturezas, e o parecer deve manter essa distinção sempre
explícita:

1. **Verificável por este skill** — presença e conteúdo dos campos textuais do atestado, e
   a estrutura das assinaturas no PDF (existência de campos de assinatura, número de
   signatários, tipo de SubFilter que indica ou não o padrão PAdES). Isso o script faz.

2. **NÃO verificável por este skill, exige conferência externa** — a validade jurídica da
   assinatura como assinatura eletrônica qualificada ICP-Brasil, a integridade
   criptográfica (hash do documento) e a validade do carimbo de tempo. Isso só se confirma
   em validador oficial (validar.iti.gov.br) ou equivalente. O parecer marca esses pontos
   como "VERIFICAÇÃO EXTERNA PENDENTE" e nunca os afirma como conformes ou não conformes
   por conta própria.

Nunca declare uma assinatura "qualificada e válida" com base apenas na inspeção estrutural.
O máximo que o skill afirma é que há ou não há indício de assinatura no padrão PAdES.

## Fluxo de trabalho

### Etapa 1 — Localizar e ler o atestado

Identifique o caminho do PDF do atestado (anexado pelo usuário ou indicado por ele —
tipicamente numa subpasta da OS em `~/Documents/AFT/OS ATIVAS/`). Leia o conteúdo
textual do documento para extrair os campos declarados.

### Etapa 2 — Inspeção estrutural da assinatura (por código)

Rode o script de apoio sobre o PDF:

```bash
python ~/.claude/skills/jornada-atestado/scripts/inspecionar_assinatura.py "/caminho/para/o/atestado.pdf"
```

O script devolve JSON com: presença de AcroForm, número de campos de assinatura, número de
assinaturas preenchidas, e por assinatura o SubFilter (com a classificação se é ou não
PAdES), o nome do signatário declarado, a data e o tamanho do bloco PKCS#7.

Interprete o resultado assim:
- `indicio_pades: true` e SubFilter `/ETSI.CAdES.detached` => há indício de assinatura no
  padrão PAdES exigido. Ainda assim, a validade qualificada fica como verificação externa.
- SubFilter `/adbe.pkcs7.*` => assinatura Adobe legada, que NÃO é PAdES. Isso é indício de
  desconformidade quanto ao padrão exigido pelo art. 89.
- `qtd_assinaturas_preenchidas: 0` ou ausência de AcroForm => não há assinatura digital
  embutida. Indício forte de desconformidade (sujeito a conferência do documento físico,
  caso o AFT tenha recebido cópia impressa ou digitalizada).
- O art. 89 exige **duas** assinaturas (responsável técnico e responsável legal). Se houver
  apenas uma assinatura preenchida, sinalize a divergência.

### Etapa 3 — Conferência item a item do art. 89

Confronte o conteúdo do atestado com a checklist abaixo. Para cada item, atribua um destes
status: **CONFORME**, **NÃO CONFORME**, **NÃO APLICÁVEL** ou **VERIFICAÇÃO EXTERNA PENDENTE**.

#### Checklist de requisitos (art. 89, Portaria MTP nº 671/2021)

| # | Requisito | Como verificar |
|---|---|---|
| 1 | Documento em formato PDF | Extensão e estrutura do arquivo |
| 2 | Segue o modelo e as especificações do portal gov.br | Confrontar campos e ordem com o modelo oficial |
| 3 | Declaração expressa de conformidade com a Seção IV da Portaria MTP nº 671/2021 | Texto do atestado |
| 4 | Identificação do tipo de REP/PTRP (REP-C, REP-A, REP-P ou PTRP) | Campo "Tipo do REP/PTRP" |
| 5 | Dados do equipamento/programa coerentes com o tipo (marca, modelo, certificado, nº de fabricação, INPI, identificador e versão do programa, conforme o caso) | Campos do bloco de identificação; "N/A" aceitável quando não se aplica ao tipo |
| 6 | Assinatura eletrônica no padrão PAdES, de pessoa física | Saída do script (SubFilter) + verificação externa da qualificação |
| 7 | Duas assinaturas: responsável técnico **e** responsável legal | Saída do script (qtd. de signatários) + nomes/CPF no texto |
| 8 | Declaração de ciência das consequências legais, cíveis e criminais | Texto do atestado |
| 9 | Identificação da empresa/pessoa destinatária (razão social/nome e CNPJ/CPF) | Bloco "Empresa/Pessoa Destinatária" |
| 10 | **Somente REP-C:** nome do algoritmo de hash, chave pública e nome do algoritmo de criptografia assimétrica | Campos específicos do REP-C; para REP-A, REP-P e PTRP marque NÃO APLICÁVEL |

Regra do item 10: só é exigível quando `Tipo do REP/PTRP` for REP-C. Para os demais tipos,
a ausência desses campos é NÃO APLICÁVEL, nunca NÃO CONFORME.

### Etapa 4 — Conclusão e enquadramento

Se todos os itens aplicáveis estiverem CONFORME (admitindo itens em verificação externa
pendente que o AFT confirmará), conclua pela conformidade.

Se houver qualquer item NÃO CONFORME (falta do atestado, atestado fora do modelo gov.br,
ausência das assinaturas qualificadas obrigatórias, padrão de assinatura diferente de
PAdES, falta de um dos dois signatários, ausência de campo obrigatório do REP-C etc.),
conclua pela desconformidade e indique o enquadramento:

- **Capitulação:** art. 74, § 2º, da CLT c/c art. 89 da Portaria MTP nº 671/2021.
- **Ementa 002277-2** — quando a inconformidade se referir ao atestado do **equipamento**
  (hardware: REP-C, REP-A ou REP-P).
- **Ementa 002278-0** — quando a inconformidade se referir ao atestado do **programa de
  tratamento** (software: PTRP).

Quando a fiscalização alcançar tanto o equipamento quanto o programa, ambas as ementas
podem ser cabíveis; sinalize as duas e deixe a decisão ao AFT.

### Etapa 5 — Entrega do parecer

Gere o parecer no formato da seção seguinte. Para auditoria avulsa, apresente no chat. Se o
usuário pedir arquivo, salve em Markdown na pasta da OS.

## Estrutura do parecer (encaminhável para autuação)

```markdown
# Parecer de Auditoria — Atestado Técnico e Termo de Responsabilidade

## 1. Documento auditado
- Tipo de sistema: [REP-C / REP-A / REP-P / PTRP / não identificado]
- Empresa fabricante/desenvolvedora: [razão social ou "não declarada"]
- Empresa destinatária (empregador): [razão social e CNPJ ou "não declarada"]
- Arquivo: [nome do arquivo]

## 2. Inspeção estrutural da assinatura (por código)
[Síntese objetiva do JSON do script: nº de campos de assinatura, nº de signatários,
SubFilter de cada assinatura e se há indício de PAdES. Uma a três frases.]

## 3. Resultado item a item (art. 89, Portaria MTP nº 671/2021)

| # | Requisito | Status | Observação |
|---|---|---|---|
| 1 | Formato PDF | [status] | [obs] |
| 2 | Modelo gov.br | [status] | [obs] |
| 3 | Declaração de conformidade com a Seção IV | [status] | [obs] |
| 4 | Tipo de REP/PTRP identificado | [status] | [obs] |
| 5 | Dados do equipamento/programa | [status] | [obs] |
| 6 | Assinatura no padrão PAdES (pessoa física) | [status] | [obs] |
| 7 | Duas assinaturas (técnico + legal) | [status] | [obs] |
| 8 | Ciência das consequências legais | [status] | [obs] |
| 9 | Identificação da destinatária | [status] | [obs] |
| 10 | Campos exclusivos do REP-C | [status] | [obs] |

## 4. Pendências de verificação externa
[Listar o que o AFT precisa confirmar fora do skill: validade da assinatura qualificada
ICP-Brasil, integridade criptográfica e carimbo de tempo, via validar.iti.gov.br.]

## 5. Conclusão
[CONFORME / NÃO CONFORME. Frase objetiva.]

## 6. Enquadramento sugerido (somente se NÃO CONFORME)
- Capitulação: art. 74, § 2º, da CLT c/c art. 89 da Portaria MTP nº 671/2021.
- Ementa aplicável: [002277-2 (equipamento) / 002278-0 (programa) / ambas].

## 7. Minuta de histórico para o auto de infração
[Texto corrido, em terceira pessoa, descrevendo objetivamente a constatação: tipo de
sistema, qual requisito do art. 89 foi descumprido e como isso foi apurado. Pronto para
ajuste e colagem pelo AFT. Sem floreio, sem travessões.]
```

## Bloco para o /gera-ai (autuação — quando NÃO CONFORME)

Quando a conclusão for **NÃO CONFORME** e o AFT quiser autuar, além do parecer
emita o bloco abaixo, **pronto para o /gera-ai** (mesmo formato de det-630 e
jornada-auto-afd-aej). **Texto puro**, sem markdown. Gere **um** auto por documento não conforme.

### Escolha da ementa
- **002277-2** — inconformidade do **equipamento** (hardware: REP-C, REP-A ou REP-P).
- **002278-0** — inconformidade do **programa** (software: PTRP).
- Se a ação alcançar equipamento **e** programa, ambos não conformes, gere **dois** autos (`#1` e `#2`), um por ementa.
- **Capitulação (ambas):** Art. 74, § 2º, da CLT c/c Art. 89 da Portaria MTP nº 671/2021.

> O **código** é o que vincula no Sistema Auditor. Os textos de ementa abaixo são fiéis ao art. 89; confirme o **texto oficial** no ementário antes de transmitir (o ementário prevalece).

### Modelo — Atestado do PROGRAMA (PTRP) — Ementa 002278-0

```
=== AUTO DE INFRAÇÃO #1 ===
Ementa: 002278-0 - Deixar o empregador de manter à disposição da fiscalização o Atestado Técnico e Termo de Responsabilidade do Programa de Tratamento de Registro de Ponto (PTRP), ou mantê-lo em desconformidade com o art. 89 da Portaria MTP nº 671/2021.

I - DA FISCALIZAÇÃO:
Trata-se de ação fiscal em curso, na modalidade fiscalização mista (nos termos do § 3º, art. 30, do Regulamento da Inspeção do Trabalho - RIT -, aprovado pelo Decreto nº 4.552/2002), no estabelecimento da empresa qualificada, na qual a inspeção física foi conjugada com a auditoria do sistema de registro eletrônico de ponto adotado pela autuada, nos termos da Portaria MTP nº 671/2021.

II - IRREGULARIDADE:
Constatou-se que a autuada deixou de manter disponível para apresentação à Auditoria-Fiscal do Trabalho o Atestado Técnico e Termo de Responsabilidade referente ao seu programa de tratamento de registro de ponto. A irregularidade foi constatada mediante análise documental, oportunidade em que a empregadora, instada a comprovar a regularidade do software de controle de jornada utilizado, não apresentou o referido documento (ou o apresentou em desconformidade técnica/sem a assinatura eletrônica qualificada do responsável técnico e do representante legal da empresa desenvolvedora). A ausência do atestado legalmente válido impede a garantia formal de que o programa atende aos requisitos de tratamento e geração de arquivos exigidos pela Seção IV da Portaria MTP nº 671/2021.
Destaca-se que a adoção de sistema eletrônico vincula o empregador aos parâmetros técnicos vigentes, não sendo admitida a alegação de integração com aplicativos de gestão de terceiros ou eventuais acordos coletivos para afastar a exigência da documentação de conformidade tecnológica. Tal conduta afronta diretamente o art. 89 da Portaria MTP nº 671/2021, caracterizando o descumprimento do dever de manter controle fidedigno da jornada nos termos do art. 74, § 2º, da CLT.

A inexistência de atestado técnico válido frustra a garantia formal de conformidade do sistema de registro de ponto adotado, comprometendo a fiscalização do controle de jornada de toda a coletividade de trabalhadores do estabelecimento. Trata-se de bem jurídico de natureza difusa, cuja lesão dispensa a individualização dos trabalhadores prejudicados (Orientação Técnica SIT nº 2/2022).

ELEMENTOS DE CONVICÇÃO:
- Parecer de auditoria do Atestado Técnico e resultado da inspeção estrutural de assinatura do documento (ANEXO).
```

> **Não escreva o rótulo `III - OBSERVAÇÕES`.** O parágrafo sobre a frustração da conformidade do sistema de ponto (acima) fica como parágrafo final do Subtítulo 2. O Subtítulo 3 canônico é injetado automaticamente pelo `/gera-ai` (de `config/blocos_auto.md`) entre o bloco 2 e os ELEMENTOS DE CONVICÇÃO.

### Modelo — Atestado do EQUIPAMENTO (REP) — Ementa 002277-2

Idêntico ao anterior, trocando para a ementa **002277-2** e adaptando o objeto:
onde se lê "programa de tratamento de registro de ponto" / "software de controle
de jornada", use "**equipamento Registrador Eletrônico de Ponto (REP-C, REP-A ou
REP-P)**"; e a assinatura é a "do responsável técnico e do representante legal do
**fabricante**".

```
Ementa: 002277-2 - Deixar o empregador de manter à disposição da fiscalização o Atestado Técnico e Termo de Responsabilidade do equipamento de registro eletrônico de ponto (REP-C, REP-A ou REP-P), ou mantê-lo em desconformidade com o art. 89 da Portaria MTP nº 671/2021.
```

### Adaptação do HISTÓRICO ao caso real (fidelidade — leia)

O subtítulo 2 admite duas situações; **redija a que realmente ocorreu**, ajustando
o trecho "não apresentou … (ou o apresentou em desconformidade …)":

- **Não apresentou o atestado** → mantenha "não apresentou o referido documento" e remova o parêntese de desconformidade.
- **Apresentou em desconformidade** → descreva o defeito apurado no parecer: falta da assinatura no padrão **PAdES** (técnico e/ou legal), atestado que não declara expressamente o atendimento à Seção IV, fora do modelo gov.br, ou ausência de campo obrigatório (para REP-C, hash/chave pública/algoritmo). A infração permanece configurada; adapte a narrativa do "como" para refletir a desconformidade concreta, **sem afirmar validade qualificada ICP-Brasil por conta própria** (isso é VERIFICAÇÃO EXTERNA PENDENTE).

Após emitir o bloco, faça o handoff: o texto alimenta o **/gera-ai** (modo "autos
na sessão"), com o parecer/inspeção como anexo.

---

## Regras invioláveis

1. **Fidelidade à fonte.** Audite apenas o que está no atestado e no resultado do script.
   Não presuma campos ausentes como presentes nem o contrário sem base.

2. **Não afirme validade qualificada por conta própria.** Estrutura de assinatura é indício,
   não prova de qualificação ICP-Brasil. Mantenha "VERIFICAÇÃO EXTERNA PENDENTE" para tudo
   que dependa de validador oficial.

3. **Item 10 só para REP-C.** Para REP-A, REP-P e PTRP, os campos de hash, chave pública e
   algoritmo de criptografia são NÃO APLICÁVEL.

4. **Defesas ineficazes.** Acordos coletivos que alterem regras do registro de ponto e
   alegações de integração com aplicativos terceirizados não afastam a exigência do
   atestado. Se o usuário trouxer esse argumento, registre que ele não prospera, sem
   desenvolver tese que não foi pedida.

5. **Escrita.** Linguagem natural e direta. Não use travessões. Evite frases de chatbot e
   construções genéricas. A minuta de histórico deve soar como redigida por um AFT.

6. **Não narre o processo.** Não descreva as etapas que executou. Entregue o parecer e, se
   útil, no máximo duas linhas de observação final.

## Convenção de nome de arquivo (quando salvar)

```
parecer_atestado_[tipo]_[empresa_curto].md
```

Exemplos:
- `parecer_atestado_repc_acme.md`
- `parecer_atestado_ptrp_worktime.md`
