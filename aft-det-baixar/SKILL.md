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
  painel (token de sessão emprestado pelo navegador do assistente ou pela
  extensão Sync DET): o PDF da notificação, o Relatório de Atendimento e os
  arquivos entregues pelo empregador, organizados por item e por dia de
  download no pacote NOTIFICACOES/<NN> - <CODIGO> <dd-mm-aaaa>/ da OS — em
  segundos, sem navegador automatizado. NÃO cadastra OS (/aft-nova-auditoria) nem julga os documentos
  (/aft-auditoria-geral).
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

O servidor do painel (porta 8347) guarda por cerca de **25 minutos** o token de
sessão do DET. Ele chega por uma de duas vias — **1) o navegador do próprio
assistente** (principal) ou **2) a extensão Chrome "Sync DET"** (alternativa) —
descritas em `~/.claude/skills/config/canal-token-det.md`. **Leia esse arquivo
quando faltar token**; não repita o procedimento aqui. Esta skill só dispara o
download pelo servidor — o token nunca passa por esta conversa.

> **Faltou token do DET? Não improvise.** O `canal-token-det.md` diz como obtê-lo
> **nesta sessão** (com ou sem navegador do assistente) e, sobretudo, o que NÃO
> tentar: a página do DET **não** consegue falar com o painel local, e quem tenta
> esse caminho conclui, errado, que a via principal não funciona. Falta de token
> nunca justifica inventar caminho novo nem dizer ao AFT que o toolkit quebrou.

O que chega vai todo para o pacote da notificação, dentro de `NOTIFICACOES/`
(a raiz da OS fica limpa). O nome do pacote começa pelo **número de ordem de
lavratura** (01 é a primeira notificação emitida na fiscalização) e a data é a
de **lavratura** da notificação — não a do download. Dentro dele, cada dia de
download tem a sua subpasta `baixada em <data>`, para o AFT saber o que a
empresa apresentou em cada data (entrega parcelada tem prazos diversos):

```
<OS>/NOTIFICACOES/<NN> - <CODIGO> <dd-mm-aaaa>/  ← NN = ordem; data = LAVRATURA
├── notificacao-<CODIGO>.pdf              ← o PDF da notificação (estático)
├── canal-comunicacao/                    ← só quando há mensagens (cumulativo)
│   ├── mensagens.md                      ← a conversa, legível (derivado)
│   ├── <anexos das mensagens>
│   └── historico-canal.pdf               ← o histórico oficial do DET
└── baixada em <dd-mm-aaaa>/              ← uma por dia de download
    ├── relatorio-atendimento-<CODIGO>.pdf ← a fotografia DAQUELE dia, com TODOS
    │                                        os itens: o que veio (com MD5/SHA1)
    │                                        e o que faltou — a prova de omissão
    │                                        do art. 630, §4º, da CLT
    ├── historico-itens.md                ← prorrogações, justificativas e status
    │                                        de cada item (derivado)
    └── item<N>_<descrição oficial>/      ← só o que chegou NAQUELE dia
        ├── <arquivos entregues>
        └── invalidados/                  ← o que o AFT rejeitou/dispensou no DET
```

É idempotente: arquivo já baixado em qualquer dia anterior não é baixado de
novo — a pasta do dia só recebe o que chegou nela. Se uma notificação mais
antiga for baixada depois, os pacotes são **renumerados** sozinhos para manter
a ordem de lavratura. Legados migram sozinhos: pacote `notificacao-<COD>` ou
`<COD> <data>` (na raiz ou em NOTIFICACOES/) é renomeado ao padrão, PDF solto
é movido para dentro, e o conteúdo que morava na raiz do pacote desce para a
subpasta do dia em que foi baixado. Cada download entra
sozinho no Registro de atividades do memory.md. O download também REGISTRA A
VISUALIZAÇÃO no DET (as mesmas leituras que o site faz ao abrir a notificação
e cada item), então o triângulo amarelo "Existe atualização pendente" se apaga
na tela do DET como se o AFT tivesse aberto pelo navegador. O mesmo motor
atende o botão "⬇ baixar arquivos" do cartão de notificações do painel.

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

- `ok: true` → anote `pacote` (a pasta da notificação), `dia` (a subpasta
  `baixada em <data>` deste download), `baixados`,
  `ja_existiam`, `movidos`, `itens`, `sem_arquivo`, `invalidados`, `eventos`
  (prorrogações/justificativas no historico-itens.md), `mensagens_canal`,
  `anexos_canal` e `erros`. Notificação sem nenhum arquivo mas com `eventos` >
  0 não é vazia: a história dela está no `historico-itens.md` — diga isso ao
  AFT (é o caso típico de pedidos de prorrogação).
- O canal de comunicação é SOMENTE LEITURA: responder ou registrar ciência é
  ato do AFT, no site do DET.
- `token_expirado: true` → renove o token pela via 1 (o seu navegador) ou peça
  o **Sincronizar** ao AFT, conforme `~/.claude/skills/config/canal-token-det.md`,
  e repita a chamada. Um envio cobre o lote inteiro pelos ~25 min seguintes.
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
- **Só os documentos das notificações**, sem os arquivos que o empregador
  entregou (para ler o que foi notificado sem puxar os anexos): é a
  `/aft-det-baixar-notificacoes`. Ofereça-a quando o AFT disser que não quer as
  entregas, ou quando o lote for grande e ele só quiser o histórico.
