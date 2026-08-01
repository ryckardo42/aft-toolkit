---
name: aft-erro
model: sonnet
effort: low
allowed-tools: Read, Write, Edit, Glob, Bash, AskUserQuestion
description: >
  Use quando alguma coisa do AFT Toolkit der errado e o AFT quiser avisar
  quem mantem o toolkit. Acione com "/aft-erro", "deu erro", "isso nao
  funcionou", "reportar um problema", "avisar o mantenedor", "gerar um
  ticket", "abrir um chamado", "reclamar de um bug", "a skill X quebrou",
  "apareceu uma mensagem estranha". Monta um ticket de correcao
  pseudonimizado em <pasta AFT>/tickets/ — sem nome de empresa, CNPJ/CPF nem
  conteudo de documento. Quem encaminha e sempre o AFT.
---

# aft-erro — Ticket de correção do AFT Toolkit
**AFT Toolkit**

## Objetivo

Transformar "não funcionou" em um relato que o mantenedor consegue corrigir.

O AFT não é programador: ele vê uma mensagem estranha na tela e não tem como
saber que a informação decisiva era a versão do Python, a falta de um programa
no PATH ou o commit instalado. Esta skill coleta isso por ele.

**Duas portas de entrada:**

| Situação | O que já existe |
|---|---|
| Um script do toolkit **quebrou** (traceback na tela) | O ticket **já foi gerado sozinho** pelo `_scripts/erro_ticket.py` — falta o contexto |
| Algo saiu **errado sem quebrar** (texto errado, painel em branco, .docx torto) | Nada ainda — o ticket nasce aqui |

Tom: o AFT não errou. Ele está ajudando a melhorar a ferramenta. Nunca o faça
sentir que precisa entender o problema técnico para reportá-lo.

## Passo 1 — Ver se já existe um ticket automático recente

```bash
python "<python_path>" ~/.claude/skills/_scripts/erro_ticket.py --listar --json
```

O JSON traz a pasta e os tickets já gerados, do mais novo para o mais antigo.
O nome carrega a data e a hora (`ticket-2026-07-29-1432.md`).

- **Existe um ticket dos últimos minutos** e ele corresponde ao erro que o AFT
  está relatando → **não gere outro**. Vá para o Passo 3 (completar).
- Não existe, ou é antigo/de outro assunto → Passo 2.

## Passo 2 — Gerar o ticket

Antes, reúna **o que já está na conversa** — não interrogue o AFT. Você
normalmente já sabe: qual skill estava rodando, qual comando falhou e qual foi
a saída. Pergunte no máximo uma coisa, e só se for indispensável: *o que você
esperava que acontecesse?*

A mensagem de erro bruta vai por **arquivo**, nunca digitada dentro do comando
(acento em linha de comando no Windows vira lixo). Grave-a com a tool Write num
arquivo temporário e passe o caminho:

```bash
python "<python_path>" ~/.claude/skills/_scripts/erro_ticket.py \
  --titulo "<resumo em uma linha>" \
  --mensagem "<o que o AFT estava fazendo e o que aconteceu>" \
  --skill "/aft-nome-da-skill" \
  --erro-arquivo "<arquivo com a saída bruta>" \
  --json
```

Todos os campos são opcionais menos `--mensagem`. O script devolve
`{"ok": true, "ticket": "<caminho>"}`.

**O que escrever em `--mensagem`** (3 a 6 linhas, em português corrente):

1. o que o AFT pediu ("gerar a Relação de autos lavrados da OS X");
2. o que a ferramenta fez ("o script parou no meio; o .docx não foi criado");
3. o que se esperava ("o .docx na pasta AUTOS/Relacao de autos/");
4. se já aconteceu antes, e se tem jeito de contornar.

Não escreva nome de empresa, CNPJ/CPF nem nome de trabalhador — use "a
empresa da OS", "o trabalhador". O script ainda passa um filtro por cima, mas
o filtro é a segunda linha de defesa, não a primeira.

## Passo 3 — Completar um ticket que já nasceu sozinho

Quando o ticket veio do crash automático, ele tem o traceback e a máquina, mas
não sabe o que o AFT estava fazendo. Leia o arquivo e acrescente, logo após a
seção `## O que aconteceu`, um bloco assim (tool Edit):

```markdown
## Contexto (relatado depois)

O AFT estava rodando a skill /aft-autos-lavrados, Passo 5.5, para gerar a
Relação de autos de uma OS com 10 autos em 2 datas. O .docx não chegou a ser
criado. Já tinha acontecido na semana passada, na mesma etapa.
```

Não reescreva o resto do arquivo: as seções técnicas são a razão de ele existir.

## Passo 4 — Entregar ao AFT

Mostre, em linguagem simples:

```
🎫 Ticket gerado: ticket-2026-07-29-1432.md
   Pasta: <pasta AFT>/tickets/

O que ele leva: o erro exato, a versão do toolkit que você tem instalada
(commit 374eba1) e um retrato desta máquina — Windows 11, Python 3.12,
quais programas existem aqui. É isso que permite corrigir sem ter que
adivinhar.

O que NÃO leva: nome de empresa, CNPJ, nome de trabalhador ou conteúdo de
documento — tudo isso sai como <EMPRESA>, <INSCRICAO>.

Para enviar: anexe o arquivo (ou copie o conteúdo inteiro) para quem mantém
o AFT Toolkit.
```

Ofereça abrir a pasta dos tickets (`explorer` no Windows, `open` no macOS) e,
se o AFT quiser conferir antes de enviar, mostre o conteúdo na tela.

**Nunca envie o ticket a lugar nenhum sozinho.** Quem decide o que sai da
máquina do AFT é o AFT — a skill grava o arquivo e para por aí.

## Passo 5 — Continuar tentando resolver

Gerar o ticket não encerra o assunto. Se houver contorno possível (fazer a
mesma coisa por outro caminho, gerar o PDF na mão pelo Word, rodar a skill de
novo depois de um `/aft-atualizar`), ofereça-o na mesma resposta. O ticket é
para o mantenedor; o AFT ainda precisa do trabalho dele feito hoje.

## O que acontece sem esta skill (ticket automático)

Todo script do toolkit chama `erro_ticket.ativar()` logo no começo. Se morrer
com um erro não tratado, o AFT vê:

```
==================================================================
  O AFT TOOLKIT ENCONTROU UM ERRO E PREPAROU UM TICKET.
  Arquivo: C:\...\AFT\tickets\ticket-2026-07-29-1432.md
==================================================================
```

O traceback original continua sendo impresso logo abaixo — é dele que **você**
precisa para diagnosticar na hora. Ao ver esse aviso na saída de um comando:

1. diagnostique e, se der, **conserte** (é o seu papel — o AFT não vai ao
   terminal);
2. avise que o ticket ficou gravado, e ofereça completá-lo (Passo 3);
3. se o defeito for do toolkit e não da máquina dele, diga isso com todas as
   letras: não foi ele que fez errado.

## Limites

- A skill **não corrige** o toolkit e não altera nenhuma skill: ela só descreve
  o defeito. Correção é com o mantenedor (ou com você, na sessão, se for algo
  local).
- Não inclua no ticket trechos de documento de fiscalização, mesmo que o erro
  tenha acontecido "por causa daquele PDF". Descreva a característica do
  arquivo (tamanho, quantas páginas, se é digitalizado), nunca o conteúdo.
- Se o erro envolver o mapa `.depara_*.json`, cite apenas que ele existe — o
  arquivo é sensível e não entra no ticket em hipótese nenhuma.
