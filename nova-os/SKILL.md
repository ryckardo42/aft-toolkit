---
name: nova-os
description: >
  Use SEMPRE que o Auditor-Fiscal do Trabalho (AFT) quiser cadastrar/abrir uma nova
  auditoria (OS) no AFT Toolkit — registrar uma empresa que vai fiscalizar e, se já
  houver, a notificação do DET com o prazo. Acione com /nova-os, "nova OS", "cadastrar
  auditoria", "abrir auditoria", "nova empresa", "começar fiscalização", "registrar
  empresa", "abrir OS", "criar pasta da empresa". A skill pergunta empregador, CNPJ,
  município e (opcional) os dados do primeiro DET (código, ciência, prazo), cria a pasta
  `~/Documents/AFT/OS ATIVAS/<NOME> <CNPJ>/` e o `memory.md` da OS no esquema padrão do
  toolkit. É o ponto de entrada do fluxo de fiscalização; depois o AFT usa /inspecao-fisica,
  /gera-ai, etc. O painel (/painel) lê os memory.md criados aqui para mostrar prazos.
---

# nova-os — Cadastrar uma auditoria (OS)
**AFT Toolkit**

## Objetivo

Abrir uma nova fiscalização: criar a pasta da empresa em `~/Documents/AFT/OS ATIVAS/` e a
ficha `memory.md` com os dados básicos e, se já houver, a notificação do DET com o prazo de
entrega. É o "começo do fluxo" — equivale a abrir uma OS. Depois, o `/painel` mostra todas as
OS e seus prazos, e as demais skills (`/inspecao-fisica`, `/inspecao-inicial`, `/gera-ai`...)
trabalham dentro dessa pasta.

Tom: simples e direto, para quem está começando. Pergunte só o necessário, em uma mensagem.

## Pré-requisito

A pasta de trabalho `~/Documents/AFT/OS ATIVAS/` deve existir (criada pelo `/aft-setup`). Se
não existir, crie-a (`mkdir -p`) e siga — mas se faltar o `aft-config.md`, oriente a rodar
`/aft-setup` antes.

## Passo 1 — Coletar os dados

Pergunte em uma única mensagem (deixe claro o que é opcional):

| Campo | Obrigatório | Observação |
|---|---|---|
| Empregador (razão social) | **Sim** | em CAIXA ALTA, padrão das pastas |
| CNPJ (14 díg.) **ou** CPF/CAEPF (11 díg.) | **Sim** | empregador pessoa jurídica usa CNPJ; pessoa física (ex.: produtor rural) usa CPF/CAEPF. Aceite com ou sem pontuação; guarde só dígitos |
| Município | Não | onde fica o estabelecimento |
| Notificação DET — código | Não | ex.: `RMNHIHSH9525MU` (se já notificou pelo DET) |
| DET — data de ciência | Não | dd/mm/aaaa |
| DET — prazo de entrega | Não | dd/mm/aaaa (é o que o painel vigia) |

> Se o AFT ainda não notificou nada pelo DET, deixe a seção de DET vazia — dá para
> acrescentar depois (basta editar o `memory.md` ou rodar `/det-630`/`/nova-os` de novo).

## Passo 2 — Resolver a pasta da OS

Nome da pasta (padrão do toolkit): `<EMPREGADOR> <identificador só dígitos>` — CNPJ (14 díg.) para pessoa jurídica ou CPF/CAEPF (11 díg.) para pessoa física. Grave o mesmo identificador no `memory.md` (`**CNPJ:**` ou `**CPF:**`).

```bash
ls ~/Documents/AFT/"OS ATIVAS"/
```

- Se já existir uma pasta com esse CNPJ (ou nome muito parecido), **não duplique**: avise o
  AFT, mostre a pasta existente e ofereça (a) acrescentar/atualizar o DET nela, ou (b)
  cancelar. Nunca sobrescreva um `memory.md` existente sem confirmação.
- Senão, crie:
  ```bash
  mkdir -p ~/Documents/AFT/"OS ATIVAS"/"<EMPREGADOR> <CNPJ>"/
  ```

## Passo 3 — Escrever o memory.md

Crie `~/Documents/AFT/OS ATIVAS/<EMPREGADOR> <CNPJ>/memory.md` neste esquema (front-matter
leve + seções fixas). É o mesmo esquema que `/gera-ai`, `/inspecao-inicial` e `/det-630`
mantêm, e que o `/painel` lê:

```markdown
---
empregador: <EMPREGADOR>
cnpj: "<14 dígitos>"
municipio: <município ou vazio>
status: em_andamento
---
# <EMPREGADOR>

**CNPJ:** <CNPJ formatado XX.XXX.XXX/XXXX-XX>

## Notificações DET
- [ ] <CÓDIGO> — ciência <dd/mm/aaaa>, prazo <dd/mm/aaaa>

## Autos de Infração
_(vazio)_

## Autos lavrados
_(vazio)_

## Registro de atividades
| Data | Ação | Detalhes |
|------|------|----------|
| <dd/mm/aaaa> | OS cadastrada | via /nova-os |
```

Regras:
- **`prazo <dd/mm/aaaa>`** é a chave que o `/painel` vigia — escreva a palavra `prazo` seguida
  da data. Se o AFT não informou o DET, deixe a seção `## Notificações DET` com `_(vazio)_`.
- Se houver mais de um DET informado, uma linha `- [ ]` por notificação.
- CNPJ no front-matter: só dígitos, entre aspas. No corpo (`**CNPJ:**`): formatado.

## Passo 4 — Confirmar e encadear

Mostre um resumo curto e ofereça o próximo passo:

```
✅ OS cadastrada — <EMPREGADOR>
📁 ~/Documents/AFT/OS ATIVAS/<EMPREGADOR> <CNPJ>/
🗓️  DET: <CÓDIGO> · prazo <dd/mm/aaaa>   (ou "sem DET cadastrado")

Próximos passos:
  • /painel            → ver todas as OS e os prazos
  • /inspecao-fisica   → quando voltar da inspeção, registrar o relato
  • /det-630           → se o empregador não entregar os documentos do DET
```

## Regras

- Nunca duplique uma OS existente (dedup por CNPJ) — atualize a existente.
- Não invente datas nem código de DET; deixe a seção vazia se o AFT não informou.
- Pasta e CNPJ usam o CNPJ real (não tokenizar — é a chave que organiza tudo).
- Idempotente: rodar de novo para a mesma empresa atualiza o DET, não recria a pasta.
