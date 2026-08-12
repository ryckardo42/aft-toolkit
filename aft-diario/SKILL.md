---
name: aft-diario
model: haiku
allowed-tools: Read, Glob, Grep, Bash, AskUserQuestion
description: >
  Use quando o AFT quiser o DIÁRIO DE ATIVIDADES consolidado do mês: quantos e
  quais dias trabalhou em cada auditoria, e as linhas prontas para a tela
  "2.1 Atividades" do RI (SFIT-WEB). Acione com /aft-diario, "diário de
  atividades", "agenda mensal", "fechar o mês", "dias trabalhados no mês",
  "preencher as atividades do RI", "o que eu fiz esse mês", "diário de julho".
  Aceita 0 ou 1 argumento (mês AAAA-MM ou "julho"); sem argumento, mês
  corrente. Varre OS ATIVAS e OS ARQUIVADAS; read-only sobre as fichas. Para
  REGISTRAR um dia avulso ("trabalhei dia 06 na empresa X"), usa o
  diario_registrar.py na própria conversa — não precisa desta skill.
---

# diario — Fechamento mensal do diário de atividades
**AFT Toolkit**

## Objetivo

No fim do mês o AFT precisa preencher (1) a agenda mensal, descrevendo o que fez em
cada dia útil, e (2) a tela **2.1 Atividades** de cada RI no SFIT-WEB. Esta skill
consolida o que as skills e o gancho automático registraram ao longo do mês no
`## Registro de atividades` de cada OS (letras A-F) e entrega as duas visões prontas.

As letras (as mesmas da tela do RI):
**A** Preparação/planejamento · **B** Início da fiscalização · **C** Inspeção do
ambiente / auditoria de documentos / entrevista de empregados NO estabelecimento ·
**D** Auditoria e análise de documentos FORA do estabelecimento · **E** Elaboração
e/ou emissão de documentos / lançamento de dados em sistemas · **F** Fim da
fiscalização.

## Passo 1 — Resolver o mês e rodar o consolidado

- Argumento `AAAA-MM` → use direto. Nome de mês ("julho") → converta para o
  `AAAA-MM` mais recente que já ocorreu. Sem argumento → mês corrente.
- Rode (o `python` é o `python_path` do `aft-config.md`; a pasta vem do
  `pasta_aft.py`, nunca presuma):

```bash
python ~/.claude/skills/_scripts/diario_mensal.py <AAAA-MM>
```

O script varre OS ATIVAS + OS ARQUIVADAS + as anotações automáticas do gancho,
grava `<pasta AFT>/diario/diario-AAAA-MM.md` e devolve um JSON.

## Passo 2 — Traduzir o resultado

Apresente, nesta ordem e em linguagem simples:

1. **Dias com trabalho registrado** no mês (o número do JSON).
2. **Dias úteis sem registro** (`dias_uteis_sem_registro`) — este é o alerta que
   importa: *"nesses dias não há nada anotado; se você trabalhou em auditoria neles,
   me diga o quê que eu registro"*. Liste as datas.
3. **Empresas do mês** (`empresas_no_mes`), com os dias classificados de cada uma e o
   selo "OS arquivada" quando for o caso.
4. Se `entradas_sem_classificacao` > 0: avise que há dias anotados pelo gancho **sem
   letra** — ofereça classificá-los agora (pergunte o que foi feito em cada um) ou
   pela aba Calendário do painel.
5. O caminho do arquivo gerado e o lembrete: a visão dia a dia também está na **aba
   Calendário do painel** (`/aft-painel`).

## Passo 3 — Registrar o que faltar (a pedido)

Quando o AFT completar um dia ("dia 06/08 fiz análise documental da EMPRESA X"),
registre na hora, sem cerimônia:

```bash
python ~/.claude/skills/_scripts/diario_registrar.py "<pasta da OS>" --tipos <letras> --data <dd/mm/aaaa> --detalhe "<o que foi feito>"
```

O script deduplica por data+letra. Depois de registrar, rode o Passo 1 de novo para
regenerar o consolidado (é derivado, sempre regenerável).

## Passo 4 — Transcrição para o RI

A seção **"Por auditoria — pronto para a tela 2.1 Atividades do RI"** do arquivo
gerado traz, por OS, cada data com o texto oficial das opções do SFIT-WEB. O AFT
transcreve manualmente (data ou período + atividade no dropdown). Avise:

- Os textos de **C** incluem as três opções do estabelecimento (inspeção, auditoria
  de documentos, entrevista) — o AFT corta na tela o que não houve naquele dia.
- A "Competência para Aferição do RI" e o checkbox de sábados/domingos/feriados são
  decisão do AFT — a skill não opina.

Se o AFT quiser o diário em `.docx` (para imprimir ou anexar), gere a partir do
`diario-AAAA-MM.md` seguindo o `/aft-modelo-docx` — só se ele pedir.

## Regras

- **Nunca invente atividade nem dia trabalhado**: só o que está registrado nas
  fichas. Dia vazio é pergunta ao AFT, não lacuna a preencher sozinho.
- Read-only sobre as OS: quem grava é o `diario_registrar.py` (Passo 3), nunca
  edição manual da tabela por esta skill.
- Empresas aparecem por nome; nenhum dado de trabalhador entra no diário.
