---
name: aft-det-baixar
model: sonnet
effort: low
description: >
  Use SEMPRE que o AFT pedir para baixar do DET (Domicílio Eletrônico
  Trabalhista) os arquivos de uma notificação ou de um empregador. Dispare com
  /aft-det-baixar, "baixa as notificações do DET da EMPRESA X", "pega o DET da
  empresa Y", "baixa DET para CNPJ ...", "baixa a notificação CÓDIGO do DET",
  "traz os documentos que a empresa entregou no DET". Aceita como argumento:
  código de notificação (alfanumérico maiúsculo, ex.: ABCDE12345FGHIJ), CNPJ
  (14 dígitos) ou nome do empregador. Baixa pela API do DET, via servidor do
  painel (token emprestado pela extensão Sync DET): o PDF da notificação, o
  Relatório de Atendimento e os arquivos entregues pelo empregador, tudo
  organizado por item dentro de notificacao-<CODIGO>/ na pasta da OS — em
  segundos, sem navegador. NÃO cadastra OS (/aft-nova-auditoria) nem julga os
  documentos (/aft-auditoria-geral).
---

# aft-det-baixar — Baixar os arquivos de uma notificação DET
**AFT Toolkit**

> **Onde ficam as pastas das OS.** Nunca presuma o caminho: resolva **uma vez,
> no início**, e use o que voltar onde este texto disser `<OS_ATIVAS>`.
>
> ```bash
> python ~/.claude/skills/_scripts/pasta_aft.py --os-ativas
> ```
>
> No Windows, invoque o Python pelo `python_path` do `aft-config.md`.

## Como funciona

O servidor do painel (porta 8347) guarda por **25 minutos** o token que a
extensão Chrome "Sync DET" entrega quando o AFT clica em **Sincronizar** na
aba do DET. Esta skill só dispara o download por esse servidor — o token nunca
passa por aqui. O que chega, tudo dentro da pasta da notificação (a raiz da OS
fica limpa):

```
<OS>/notificacao-<CODIGO>/
├── notificacao-<CODIGO>.pdf              ← o PDF da notificação
├── relatorio-atendimento-<CODIGO>.pdf    ← o Relatório de Atendimento
└── item<N>_<descrição oficial>/          ← um por item solicitado
    ├── <arquivos entregues>
    └── invalidados/                      ← o que o AFT rejeitou/dispensou no DET
```

É idempotente (arquivo existente não é baixado de novo; PDF que download
antigo deixou na raiz é movido para dentro), e cada download entra sozinho no
Registro de atividades do memory.md. O mesmo motor atende o botão
"⬇ baixar arquivos" do cartão de notificações do painel.

## Passo 0 — Servidor do painel no ar

```bash
curl -s http://127.0.0.1:8347/api/ping
```

Sem resposta: suba com
`python ~/.claude/skills/_scripts/instalar_servidor_painel.py reiniciar`
e confira o ping de novo. Se ainda assim não subir, oriente `/aft-doctor`.

## Passo 1 — Resolver o pedido em (pasta da OS, códigos)

Identifique a entrada do AFT:

- **Código de notificação** (alfanumérico maiúsculo, ≥ 8 caracteres, sem
  espaços): procure em qual `memory.md` de `<OS_ATIVAS>` ele aparece — essa é
  a pasta. Não aparece em nenhuma ficha: peça ao AFT um **Sincronizar** na aba
  do DET (o sync importa a notificação para a ficha) e tente de novo; se a
  empresa não tem OS, oriente `/aft-nova-auditoria` primeiro.
- **CNPJ ou nome do empregador**: localize a pasta da empresa em
  `<OS_ATIVAS>` (CNPJ no nome da pasta ou no front-matter do memory.md). Os
  códigos são as linhas checkbox da seção `## Notificações DET` do memory.md —
  **ignore** as marcadas `CANCELADA no DET`.
- **Sem argumento**: pergunte de qual empresa ou notificação se trata.

## Passo 2 — Baixar (uma chamada por código)

```bash
python ~/.claude/skills/_scripts/det_baixar.py --via-painel "<pasta da OS>" <CODIGO>
```

Leia o JSON devolvido:

- `ok: true` → anote `baixados`, `ja_existiam`, `movidos`, `itens`,
  `sem_arquivo`, `invalidados` e `erros`.
- `token_expirado: true` → peça ao AFT, **em uma frase**: abrir a aba do DET
  no Chrome e clicar no botão flutuante **Sincronizar** (canto inferior
  direito). Aguarde a confirmação e repita a chamada — o token vale 25 min,
  um Sincronizar cobre o lote inteiro.
- `painel_fora: true` → volte ao Passo 0.
- Outro erro → registre e **siga para o próximo código**; nunca trave o lote.

## Passo 3 — Relatório final

Uma mensagem só:

```
Download DET — <EMPREGADOR>

Baixadas (N): <CODIGO> — X arquivos novos (Y já existiam), N itens
Sem novidade (N): ...
Falhas (N): <código — erro em linguagem simples>
```

Se a notificação venceu sem entrega (itens `sem_arquivo` e prazo passado),
lembre o AFT do `/aft-det-630` (auto por omissão). A auditoria do que foi
entregue segue o fluxo normal: constatações em `## Auditoria de documentos`
e, depois, `/aft-auditoria-geral`.

## Regras

- **Nunca** exponha token ou senha do DET no chat, em log ou em arquivo.
- Pasta da OS sempre via `pasta_aft.py` — nunca presuma o caminho.
- Um código com erro não interrompe os demais.
- Esta skill não julga documento nenhum: baixar é o fim dela.
