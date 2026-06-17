---
name: det-630
description: >
  Use SEMPRE que o empregador omitir (total ou parcialmente) a entrega de
  documentos notificados via DET (Domicílio Eletrônico Trabalhista). Dispare
  com /det-630, "auto 630", "redigir auto DET", "omissão documental DET",
  "lavrar 630", "ementa 001168-1", "empregador não entregou", "documentos não
  apresentados DET", "auto art 630", "auto omissão documentos". A skill redige
  o auto de infração da Ementa 001168-1 (art. 630, §4º CLT) já no formato
  estruturado consumido por /gera-ai (=== AUTO DE INFRAÇÃO #1 === / 1) DA
  FISCALIZAÇÃO / 2) IRREGULARIDADE / 3) OBSERVAÇÕES / ELEMENTOS DE CONVICÇÃO)
  e prepara o Relatório de Atendimento do DET como anexo do auto.
---

# det-630 — Auto de Infração por omissão documental DET (Ementa 001168-1)
**AFT Toolkit**

## Quando usar

Duas situações:

- **Cenário 1 — Omissão total:** o empregador foi notificado pelo DET e não entregou nenhum documento até o prazo.
- **Cenário 2 — Omissão parcial:** o empregador entregou parte dos documentos, mas deixou itens da notificação sem entrega.

Em ambos os casos a infração é a mesma: **Ementa 001168-1 — Deixar de apresentar documentos sujeitos à inspeção do trabalho no dia e hora previamente fixados pelo AFT** (art. 630, §4º da CLT).

A skill produz o texto do auto já no formato que o `/gera-ai` consome, e prepara o PDF do Relatório de Atendimento (emitido pelo próprio DET) como anexo.

---

## Passo 1 — Localizar a OS e os documentos do DET

1. Identifique a pasta da empresa em `~/Documents/AFT/OS ATIVAS/` (liste e pergunte se ambíguo).
2. Peça ao AFT os dois PDFs do DET, se ainda não estiverem na pasta da OS:
   > "Baixe do DET (det.sit.trabalho.gov.br) e salve na pasta da OS (ou arraste aqui no chat): (1) o **PDF da notificação** e (2) o **Relatório de Atendimento** (ou de Não Atendimento) da notificação."
3. Variáveis a partir daqui:
   - `PASTA_OS` = pasta do empregador
   - `CODIGO` = código da notificação (alfanumérico, ex: `ROCHC716LMJ3KP`) — extraia do PDF ou pergunte
   - `RELATORIO_PDF` = caminho do Relatório de Atendimento

---

## Passo 2 — Identificar o cenário

Pergunte (ou deduza do Relatório de Atendimento, que lista o que foi e não foi entregue):

> "O empregador (1) não entregou **nada**, ou (2) entregou **apenas parte** dos itens?"

Guarde `CENARIO` = `total` ou `parcial`.

**Se `parcial`**: monte a lista `ITENS_NAO_ENTREGUES` — número e descrição **exata** de cada item da notificação que ficou sem entrega (extraia do PDF da notificação + Relatório de Atendimento; confirme com o AFT). Mantenha a numeração original da notificação (se faltam os itens 5 e 7, escreva "5." e "7." — não renumere).

---

## Passo 3 — Coletar os dados da notificação

Extraia do PDF da notificação (ou pergunte UMA pergunta consolidada com o que faltar):

| Variável | O que é |
|---|---|
| `tipo_fiscalizacao` | `mista` ou `indireta` |
| `cnpj` | CNPJ do empregador (14 dígitos) |
| `data_notificacao` | data de lavratura da notificação |
| `data_ciencia` | data em que o empregador teve ciência (marco do prazo) |
| `prazo_entrega` | data-limite de entrega |

**Conversão de datas:** sempre escreva no auto no formato **dd/mm/yyyy**. Nunca invente datas, número de notificação ou tipo de fiscalização — pergunte.

---

## Passo 4 — Redigir o texto no formato /gera-ai

Monte o bloco abaixo. Não use markdown bold (`**…**`) — o parser do `/gera-ai` consome texto puro. Mantenha os subtítulos `1)`, `2)`, `3)` e `ELEMENTOS DE CONVICÇÃO:` exatamente como abaixo.

```
=== AUTO DE INFRAÇÃO #1 ===
Ementa: 001168-1 - Deixar de apresentar documentos sujeitos à inspeção do trabalho no dia e hora previamente fixados pelo AFT.

1) DA FISCALIZAÇÃO:
Trata-se de ação fiscal em curso, na modalidade fiscalização <TIPO> (nos termos do <PARAGRAFO> do art. 30 do Regulamento da Inspeção do Trabalho - RIT -, aprovado pelo Decreto nº 4.552/2002), no estabelecimento supracitado.

2) IRREGULARIDADE:
O empregador acima identificado foi notificado, nos termos do disposto nos parágrafos 3º e 4º do art. 630 da Consolidação das Leis do Trabalho - CLT, para a apresentação de documentos.

A notificação foi lavrada em <DATA_NOTIFICACAO> por meio do Domicílio Eletrônico Trabalhista - DET, notificação <NUMERO_NOTIFICACAO>, sistema do Governo Federal, administrado pela Secretaria de Inspeção do Trabalho (SIT) do Ministério do Trabalho e Emprego, para facilitar a comunicação eletrônica entre a Inspeção do Trabalho e os empregadores, visando cumprir as disposições do artigo 628-A da CLT. O empregador teve ciência da notificação em <DATA_CIENCIA>.

<PARAGRAFO_OMISSAO>

A recusa na apresentação dos documentos solicitados não apenas impede a verificação do cumprimento das obrigações trabalhistas, mas também configura um dano de natureza coletiva. Tal conduta obstrui a atuação preventiva e fiscalizatória do Estado, prejudicando a efetividade das políticas de proteção aos direitos de todos os trabalhadores, em conformidade com o entendimento do Precedente Administrativo nº 92 da Secretaria de Inspeção do Trabalho (SIT).

Em anexo o Relatório de <ATEND_OU_NAO_ATEND> à notificação emitido pelo DET<COMPLEMENTO_RELATORIO>.

Dano de natureza coletiva. Conforme a Portaria MTP nº 667/2021, a citação nominal do empregado só é necessária quando imprescindível à caracterização da infração ou quando a multa se baseia no quantitativo de trabalhadores prejudicados. Nas infrações que atingem a coletividade, como as relativas ao meio ambiente de trabalho (SST), dispensa-se a individualização, dado o caráter difuso ou coletivo do bem jurídico tutelado (Orientação Técnica SIT nº 2/2022).

ELEMENTOS DE CONVICÇÃO:
- Relatório de <ATEND_OU_NAO_ATEND> à notificação emitido pelo DET (ANEXO).
```

> **Não escreva o rótulo `3) OBSERVAÇÕES`.** As observações específicas deste auto (Precedente nº 92, referência ao Relatório do DET, dano coletivo) ficam como os parágrafos finais do Subtítulo 2. O Subtítulo 3 canônico é injetado automaticamente pelo `/gera-ai` (de `config/blocos_auto.md`) entre o último parágrafo do bloco 2 e os ELEMENTOS DE CONVICÇÃO.

### Tabela de substituições

| Placeholder | Cenário 1 (omissão total) | Cenário 2 (omissão parcial) |
|---|---|---|
| `<TIPO>` | `mista` se `tipo_fiscalizacao=mista`; `indireta` se `=indireta` | idem |
| `<PARAGRAFO>` | `§ 3º` se mista; `§ 1º` se indireta | idem |
| `<DATA_NOTIFICACAO>` | dd/mm/yyyy | idem |
| `<DATA_CIENCIA>` | dd/mm/yyyy | idem |
| `<NUMERO_NOTIFICACAO>` | código (ex: ROCHC716LMJ3KP) | idem |
| `<PARAGRAFO_OMISSAO>` | (ver bloco A abaixo) | (ver bloco B abaixo) |
| `<ATEND_OU_NAO_ATEND>` | `não atendimento` | `atendimento` |
| `<COMPLEMENTO_RELATORIO>` | ` que cita todos os documentos notificados mas não apresentados` | (string vazia) |

**Bloco A — Cenário 1 (omissão total):**
```
O empregador notificado deveria apresentar os documentos notificados até <PRAZO_ENTREGA>, mas não o fez, o que torna imperiosa sua autuação, em face de sua conduta omissiva, por deixar de apresentar documentos sujeitos à inspeção do trabalho no dia e hora previamente fixados pelo AFT.
```

**Bloco B — Cenário 2 (omissão parcial):**
```
O empregador notificado deveria apresentar os documentos notificados até <PRAZO_ENTREGA>. Contudo, apesar de ter apresentado parcialmente os documentos solicitados, deixou de entregar os seguintes itens:

<LISTA_NUMERADA_ITENS>

Tal omissão parcial torna imperiosa sua autuação, em face de sua conduta omissiva, por deixar de apresentar documentos sujeitos à inspeção do trabalho no dia e hora previamente fixados pelo AFT.
```

---

## Passo 5 — Salvar o texto e atualizar memory.md

1. **Salvar o auto redigido** em `$PASTA_OS/auto-det630-<CODIGO>.md`. Se já existir, sobrescreva e avise: "Auto anterior sobrescrito".

2. **Atualizar `memory.md`** da OS (se existir; criar seções se necessário):
   - Em `## Notificações DET`: registre/atualize a notificação com o **prazo** — esta é a
     linha que o `/painel` vigia. Se ainda não houver linha para `<CODIGO>`, acrescente
     (substituindo o `_(vazio)_` se for o caso):
     ```
     - [ ] <CODIGO> — ciência <dd/mm/aaaa>, prazo <dd/mm/aaaa>
     ```
   - Em `## Autos lavrados`: adicionar linha (não duplique se já houver a mesma)
     ```
     - [ ] det630 · ementa 001168-1 · notificação <CODIGO> · cenário <total|parcial> · redigido <DATA_HOJE>
     ```
   - Em `## Registro de atividades`: adicionar linha de tabela
     ```
     | <DATA_HOJE> | Auto det-630 redigido | Notificação <CODIGO> (cenário <total|parcial>) |
     ```

---

## Passo 6 — Preparar o anexo (PDF do Relatório de Atendimento)

> **CONVENÇÃO OBRIGATÓRIA DE NOMES:** todo anexo segue o padrão `AI_[NUM_AUTOS]_[CNPJ]_[sufixo][N].PDF` (extensão `.PDF` MAIÚSCULA). Para o relatório DET, use o sufixo `doc`. Exemplo: `AI_1_56309119000103_doc1.PDF`. O Sistema Auditor não reconhece anexos fora deste padrão.

O anexo será incluído pelo próprio `/gera-ai` (Protocolo para documentos PDF prontos, FASE 2): informe a ele o caminho do `RELATORIO_PDF` quando ele perguntar por anexos.

---

## Passo 7 — Apresentar o resultado e fazer o handoff para /gera-ai

Imprima no chat:

```
✅ Auto da Ementa 001168-1 redigido — notificação <CODIGO>

Cenário: <total|parcial>
Modalidade: <mista|indireta>
Ciência: <DATA_CIENCIA>  ·  Prazo: <PRAZO_ENTREGA>

📄 Texto do auto: <PASTA_OS>/auto-det630-<CODIGO>.md
📎 Anexo a usar no /gera-ai: <RELATORIO_PDF>

▶ Próximo passo — gerar o TXT do Sistema Auditor:
  1) Rode /gera-ai
  2) Quando ele perguntar "Os autos estão (a) colados ou (b) na sessão?", responda (b).
  3) Quando ele tratar de anexos, indique o Relatório de Atendimento como documento PDF pronto.
```

Em seguida, mostre o texto completo do auto em um bloco de código para o usuário revisar antes de seguir.

---

## Regras

- **Nunca invente** datas, número de notificação, tipo de fiscalização ou itens não entregues. Sempre prefira perguntar.
- **Nunca cite o nome do empregador** no corpo do auto — use "empregador acima identificado" / "empregador supracitado". Os dados do empregador entram no cabeçalho do TXT via `/gera-ai`.
- **Datas no formato dd/mm/yyyy** dentro do auto.
- **A data de ciência é o marco jurídico do prazo** — sempre presente no texto da IRREGULARIDADE.
- **Não use markdown formatting** (negrito, itálico) dentro do texto que vai para `/gera-ai` — só texto puro.
- **A extensão do PDF anexo é sempre `.PDF` maiúscula.**
- **Sem travessões** no texto do auto (latin-1).

## Idempotência

- Rodar 2× sobrescreve `auto-det630-<CODIGO>.md` (com aviso).
- A linha em `## Autos lavrados` é checada por código antes de adicionar (não duplica).
