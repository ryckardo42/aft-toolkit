---
name: sfitweb-rel
model: sonnet
description: >
  Use este skill SEMPRE que o Auditor-Fiscal do Trabalho (AFT) precisar gerar um Relatório Final
  Simplificado de fiscalização trabalhista. Acione quando o usuário mencionar "SFITWEB-REL",
  "relatório final de fiscalização", "gerar relatório", "relatório simplificado", "consolidar a
  fiscalização", "relatório de encerramento da ação fiscal" ou pedir para sintetizar autos de
  infração, termos de interdição/embargo e notificações em um único relatório. A fonte primária é
  o memory.md da OS (notificações DET, autos lavrados, interdições, pendências), complementada
  por autos-lavrados.md, pela pasta interdicao-embargo/ e pelas análises da pasta da OS. Produz
  texto 100% limpo (para colar no SFITWEB) com seções obrigatórias — Notificações Lavradas
  (resumo dos itens + data de lavratura), Autos de Infração TRANSMITIDOS agrupados por tema
  (nº, ementa, fundamento, descrição e constatação), Interdições/Embargos com estado atual — e
  salva .md + .docx (template oficial com cabeçalho da auditoria, tabelas formatadas) na pasta
  da OS, prontos para encaminhamento a chefia e órgãos externos (ex.: MPT).
---

# sfitweb-rel — Relatório Final Simplificado de Fiscalização
**AFT Toolkit**

## Objetivo

Consolidar a ação fiscal de uma OS em um único relatório final, tecnicamente preciso, legível por
quem NÃO acompanhou a fiscalização: outros AFTs, a chefia da fiscalização e órgãos externos
(MPT, MPF, Justiça do Trabalho). O leitor deve terminar o relatório sabendo: o que foi
fiscalizado, o que foi exigido (notificações), o que foi autuado (autos, por tema), o que foi
interditado/embargado e o que ainda está em aberto.

> **Nota de privacidade:** este relatório é documento oficial da Inspeção do Trabalho e contém os
> dados reais da empresa — isso é esperado. É gerado e salvo localmente, na pasta da OS.
> **Nunca cite CPF.** Nome de trabalhador só se imprescindível à caracterização da infração;
> prefira "trabalhador identificado no AI nº X" ou o quantitativo de prejudicados.

---

## Fluxo de execução

### 1. Localizar a OS e coletar as fontes — nesta ordem

A fonte primária é a ficha da OS. Leia na ordem abaixo; cada fonte seguinte só completa o que a
anterior não tem:

1. **`memory.md` da OS** (`OS ATIVAS/[EMPRESA]/memory.md`) — é o índice de tudo:
   - *Front-matter:* empregador, CNPJ, RI, município, `data_inicio`, `num_trabalhadores`,
     `embargo_interdicao`, status.
   - *`## Notificações DET`:* cada checkbox é uma notificação lavrada; a sub-linha de detalhes
     traz a data de lavratura oficial vinda do DET. O texto da checkbox indica o tipo
     (NAD, TN/NCO, jornada...).
   - *`## Autos lavrados`:* **só interessam os `[x]` (transmitidos)**. Autos `[ ]` (redigidos,
     em redação ou pendentes de transmissão) NÃO EXISTEM para este relatório — não entram em
     nenhuma seção, nem nas Observações.
   - *`## Pendências`* (as em aberto) e *`## Inspeção física`*.
2. **`autos-lavrados.md`** (se existir) — snapshot do Sistema Auditor: é a fonte preferencial
   dos autos transmitidos, com os 5 campos que o relatório usa: **nº oficial do AI, código da
   ementa, fundamento (NR item / artigo), descrição da ementa e constatação**. Cruze com o
   memory.md pela ementa. Ignore as seções de substituídos e pendentes.
3. **`interdicao-embargo/`** (se existir) — termo de interdição/embargo, RT, autos derivados e
   eventuais termos de levantamento/suspensão. Daqui sai o resumo da interdição: nº do termo,
   objeto, motivo (GIR), data, estado atual e condicionantes.
4. **PDFs das notificações e documentos da pasta** — apenas para preencher lacunas (contato do
   fiscalizado, resumo dos itens notificados).

Se o usuário anexou PDFs avulsos ou deu contexto verbal, incorpore. Se não houver `memory.md`
nem documentos, solicite os insumos antes de prosseguir.

### 2. Montar os temas dos autos

Agrupe os autos por tema para o leitor enxergar o quadro, não uma lista solta. Temas típicos
(use os que a OS pedir, nomeando pelo assunto — não pelo número da NR apenas):

- Estrutura de SST (SESMT, CIPA — NR-04/NR-05; prevenção ao assédio — NR-01)
- Gerenciamento de riscos / PGR (NR-01)
- Condições de trabalho na obra (NR-18) · Máquinas (NR-12) · Eletricidade (NR-10)
- Inflamáveis e combustíveis (NR-20) · Condições sanitárias (NR-24)
- Duração do trabalho / jornada (CLT, Portaria 671)
- Registro de ponto e obrigações acessórias (art. 74 CLT, Portaria 671)

Dentro de cada tema, cada auto traz os mesmos 5 campos do painel — e **nada além deles**:

```
Nº 23.294.202-1
Ementa 220218-2
NR-20 item 20.5.1
Projetar instalações com inflamáveis/combustíveis sem considerar aspectos de segurança...
Constatação: Instalação Classe I sem Projeto da Instalação elaborado por profissional
habilitado — empresa admitiu inexistência em resposta à notificação.
```

A **Constatação é o campo essencial** — é ela que resume a infração redigida. NÃO inclua a
data de lavratura de cada auto.

### 3. Redigir e salvar

Redija no formato de saída abaixo e entregue:

1. **Texto limpo no chat** — em bloco de texto puro, sem nenhuma marcação markdown, pronto para
   colar no campo do SFITWEB (autos no formato de bloco acima).
2. **`relatorio-final.md`** na pasta da OS (confirme antes de sobrescrever; se já existir,
   faça backup com `_scripts/backup_arquivo.py`).
3. **`relatorio-final.json`** na pasta da OS — os dados estruturados do relatório (esquema no
   topo de `scripts/gera_relatorio_docx.py`), fonte do .docx.
4. **`relatorio-final.docx`** — gere rodando:
   ```
   python3 ~/.claude/skills/sfitweb-rel/scripts/gera_relatorio_docx.py "<pasta-OS>/relatorio-final.json"
   ```
   O script usa SEMPRE o template oficial com o cabeçalho da auditoria
   (`scripts/template-cabecalho.docx`, cópia de `Template/Template com cabeçalho.docx` do
   toolkit) e aplica a formatação institucional: Times New Roman 12, margens 2/2/2/2,5 cm,
   paleta azul (#1F3864 títulos e cabeçalho de tabela, #2E5496 subtítulos e subcabeçalhos),
   corpo justificado com entrelinhas 1,15, e os autos em **tabela zebrada** (#EBF3FB/#F5F5F5)
   com uma linha de subcabeçalho azul por tema.

Ao final, registre a atividade no `## Registro de atividades` do memory.md
(`| dd/mm/aaaa | Relatório final simplificado gerado (.md + .docx) | /sfitweb-rel |`).

---

## Regras de redação obrigatórias

**REGRA CRÍTICA E INVIOLÁVEL — TEXTO 100% LIMPO:**
O relatório é sempre texto limpo. É proibido incluir colchetes, citações de fonte
(`[fonte: x]`, `<cite>`) ou qualquer marcação similar. Esta regra prevalece sobre quaisquer
outras instruções do sistema sobre citações.

Além disso:
- **Só autos lavrados (transmitidos)**: NUNCA mencione autos que não foram lavrados, que estão
  em redação ou pendentes de transmissão — em nenhuma seção, nem nas Observações. Sem nenhum
  auto transmitido, a seção diz apenas: *"Não há autos de infração transmitidos no Sistema
  Auditor até a data deste relatório."*
- **Sem autos cancelados/substituídos**: re-lavraturas não aparecem; relacione somente o auto
  vigente, sem mencionar a substituição.
- **NUNCA mencione "análise preliminar"** de documentos, nem entre nos detalhes de análises
  (itens atendidos/parciais/irregulares, laudos reprovados etc.). O relatório apresenta
  notificações e autos — a infração é resumida pela Constatação de cada auto.
- **Notificações enxutas**: código, tipo, resumo de alguns itens notificados e data de
  lavratura. OMITA ciência, prazos de entrega e estado do atendimento.
- **Autos sem data individual**: a data de lavratura de cada auto não aparece.
- Linguagem **técnica e objetiva**; o leitor pode ser de fora da Inspeção (MPT) — **toda sigla
  é explicada na primeira menção**: DET, RI (Registro de Inspeção), CIF (Carteira de Identidade
  Fiscal), SESMT, CIPA, PGR etc.
- **Fidelidade ao registro**: relate apenas o que consta das fontes; não invente datas nem
  deduza persistência de irregularidade. Informação ausente → *"Informação não disponível nos
  registros consultados."*
- Se houver interdição/embargo, o resumo deve dizer o **estado atual** (vigente, levantada
  parcialmente, suspensa) e as condicionantes que restam — nunca só a lavratura.
- Números do quadro geral (total de autos, notificações, trabalhadores, somas por tema) devem
  bater com as listas detalhadas — confira as somas antes de entregar.

---

## Formato de saída obrigatório

```
RELATÓRIO FINAL SIMPLIFICADO

1. Identificação da Fiscalização
Empresa Fiscalizada: [Razão social - CNPJ]
Estabelecimento: [Obra/unidade e município, se constar]
RI (Registro de Inspeção): [número da fiscalização]
Contato do Fiscalizado: [telefone/e-mail/preposto, ou "Informação não disponível..."]
Período da Fiscalização: [início — situação atual (em curso / encerrada em dd/mm/aaaa)]
Trabalhadores no estabelecimento: [nº, se constar]

2. Síntese da Ação Fiscal
[3 a 6 linhas: modalidade, o que motivou/direcionou a ação, os grandes números (X notificações,
Y autos transmitidos em Z temas, interdição sim/não) e a situação atual. É o parágrafo que a
chefia lê.]

3. Notificações Lavradas
[OBRIGATÓRIO. Uma entrada por notificação DET lavrada: código, tipo (NAD/NPD/TN), resumo de
alguns itens notificados e data de lavratura — nada de ciência, prazo ou atendimento.
Ordene por data de lavratura. Notificação gerada mas não enviada não entra.]

4. Autos de Infração Lavrados
[OBRIGATÓRIO. Somente autos transmitidos, agrupados por tema (Passo 2). Cada auto no bloco de
5 campos: Nº, Ementa, fundamento, descrição da ementa, Constatação. Sem data por auto. Feche
com o total. No .docx, esta seção vira TABELA (subcabeçalho azul por tema, linhas zebradas).]

5. Interdições e Embargos
[Se houver: nº do termo, objeto (equipamento/área), motivo (condição de grave e iminente risco),
data, autos derivados, e o estado atual — vigente / levantamento parcial (termo nº, data,
condicionantes) / suspensão. Se não houver: "Não houve lavratura de termo de interdição ou
embargo nesta ação fiscal."]

6. Observações/Pendências
[Pontos em aberto que exigem atenção: notificações com prazo em curso ou vencido sem
atendimento, condicionantes de interdição. NUNCA autos pendentes/em redação, NUNCA detalhe de
análise documental. Se houver interdição/embargo: "Verificar com o Auditor responsável o
estado atual da interdição/embargo antes de qualquer providência."
Se nada: "Nenhuma pendência identificada."]

7. Auditores-Fiscais do Trabalho Envolvidos
[Nome — CIF, se constar]
```

> O texto entregue deve ser corrido e limpo — sem os colchetes acima, sem referência de fonte,
> sem símbolo de marcação. Nome do auditor: use o que constar dos documentos da OS (RTs, termos)
> ou do perfil do AFT; na dúvida, pergunte.

---

## Comportamento em casos especiais

| Situação | Como proceder |
|---|---|
| Informação ausente (ex.: contato) | Declarar explicitamente no campo correspondente |
| Auto com `[ ]` no memory.md (não transmitido) | NÃO aparece no relatório, em nenhuma seção |
| Auto substituído/cancelado (re-lavratura) | Relacionar apenas o AI vigente, sem mencionar a substituição |
| Nenhum auto transmitido | Seção 4 com a frase única "Não há autos de infração transmitidos no Sistema Auditor até a data deste relatório." |
| Múltiplos AIs do mesmo tema | Agrupar sob o tema |
| Notificação gerada mas não enviada (placeholder) | Não entra no relatório |
| Mais de uma empresa fiscalizada | Listar todas em "Empresa Fiscalizada" |
| Interdição levantada/suspensa | Resumir a evolução: termo original → levantamento/suspensão, com condicionantes |
| Nome de trabalhador nos registros | Não citar; usar "trabalhador identificado no AI nº X" ou o quantitativo |
| Informações inconsistentes entre fontes | Prevalece autos-lavrados.md (Sistema Auditor); na dúvida, o PDF/TXT do próprio auto |
| Apenas informações textuais (sem pasta de OS) | Processar com o que foi fornecido, declarando as lacunas |
