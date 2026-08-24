---
name: aft-det-baixar-notificacoes
model: sonnet
effort: low
description: >
  Use quando o AFT quiser baixar do DET SÓ os documentos das notificações de
  uma empresa — o PDF de cada notificação, SEM os arquivos que o empregador
  entregou. Dispare com /aft-det-baixar-notificacoes, "baixa as notificações do
  DET dessa empresa", "só as notificações, não os arquivos enviados", "quero os
  PDFs das notificações da empresa X", "traz o histórico de notificações do
  DET". Aceita CNPJ, nome do empregador ou código de notificação; sem
  argumento, pergunta de qual empresa. Para o pacote COMPLETO (com o Relatório
  de Atendimento, o canal de comunicação e os arquivos entregues), a skill é
  /aft-det-baixar.
---

# aft-det-baixar-notificacoes — só os documentos das notificações
**AFT Toolkit**

> **Onde ficam as pastas das OS.** Nunca presuma o caminho: resolva **uma vez,
> no início**, e use o que voltar onde este texto disser `<OS_ATIVAS>`.
>
> ```bash
> python ~/.claude/skills/_scripts/pasta_aft.py --os-ativas
> ```
>
> No Windows, invoque o Python pelo `python_path` do `aft-config.md`.

## O que esta skill faz (e o que não faz)

Baixa **apenas o PDF de cada notificação** — o documento que o AFT lavrou e o
empregador recebeu. Serve para ler o que foi notificado, montar o histórico de
uma empresa ou conferir o texto de uma notificação antiga, **sem puxar os
anexos** que o empregador enviou (que podem ser centenas de megabytes).

Não baixa: os arquivos entregues, o Relatório de Atendimento, o histórico dos
itens nem o canal de comunicação. Para isso, use a **`/aft-det-baixar`**.

> **Não apaga o alerta amarelo do DET, de propósito.** O download completo faz
> as mesmas leituras que o site faz ao abrir a notificação, e por isso apaga o
> aviso "Existe atualização pendente". Aqui não: o AFT **não olhou** o que a
> empresa entregou, então o alerta continua na tela dele. Apagar o aviso sem ter
> visto o conteúdo seria mentir para o próprio auditor. Diga isso ao AFT quando
> ele perguntar por que o triângulo continua lá.

## Passo 0 — Servidor do painel no ar

```bash
curl -s http://127.0.0.1:8347/api/ping
```

Sem resposta: suba com
`python ~/.claude/skills/_scripts/instalar_servidor_painel.py reiniciar`.

O token do DET chega por uma de duas vias, descritas em
`~/.claude/skills/config/canal-token-det.md` — **leia esse arquivo quando faltar
token**, e não repita o procedimento aqui. O token nunca passa por esta conversa.

> **Faltou token do DET? Não improvise.** Siga o `~/.claude/skills/config/canal-token-det.md`: ele diz como obter o token **nesta sessão** (com ou sem navegador do assistente) e, sobretudo, o que NÃO tentar. Em particular, a página do DET **não** consegue falar com o painel local — quem tenta esse caminho conclui, errado, que a via principal não funciona. Falta de token nunca justifica inventar caminho novo nem dizer ao AFT que o toolkit está quebrado.

## Passo 1 — Resolver (pasta da OS, códigos)

- **CNPJ ou nome do empregador** → ache a pasta em `<OS_ATIVAS>`; os códigos são
  as linhas checkbox da seção `## Notificações DET` do `memory.md`.
- **Código de notificação** (alfanumérico maiúsculo) → ache em qual `memory.md`
  ele aparece.
- **Sem argumento** → pergunte de qual empresa se trata.

**Mostre a lista antes de baixar** e confirme com o AFT, dizendo quantas são.
Notificação marcada `CANCELADA no DET` fica de fora, salvo pedido expresso.
Ausente da ficha: peça uma sincronização com o DET e tente de novo.

## Passo 2 — Baixar (uma chamada por código)

```bash
python ~/.claude/skills/_scripts/det_baixar.py --so-notificacao --via-painel "<pasta da OS>" <CODIGO>
```

Leia o JSON: `baixados`, `ja_existiam`, `pacote`. Cada PDF vai para
`NOTIFICACOES/<CODIGO> <dd-mm-aaaa>/notificacao-<CODIGO>.pdf`, o mesmo pacote que
a `/aft-det-baixar` usa — se depois o AFT quiser o conteúdo completo daquela
notificação, tudo se acumula na mesma pasta, sem duplicar.

- `token_expirado: true` → renove conforme o `canal-token-det.md` e repita.
- `painel_fora: true` → volte ao Passo 0.
- Outro erro → registre e **siga para o próximo código**; nunca trave o lote.

## Passo 3 — Relatório final

Uma mensagem só, com o caminho de verdade da pasta:

```
Notificações DET — <EMPREGADOR>

Baixadas (N): <CODIGO> (X páginas) · ...
Já existiam (N): ...
Falhas (N): <código — erro em linguagem simples>
```

Se o AFT quiser o que a empresa entregou em alguma delas, ofereça a
`/aft-det-baixar` para aquele código.

## Regras

- **Nunca** exponha token ou senha do DET no chat, em log ou em arquivo.
- Pasta da OS sempre via `pasta_aft.py` — nunca presuma o caminho.
- Um código com erro não interrompe os demais.
- Esta skill não julga documento nenhum: baixar é o fim dela. A análise do que
  foi notificado é `/aft-auditoria-geral`.

## Diário de atividades (automático)

Ao concluir, registre o dia trabalhado na OS — sem perguntar nada ao AFT (o
script deduplica por data+letra; repetir é inofensivo):

```bash
python ~/.claude/skills/_scripts/diario_registrar.py "<pasta da OS>" --tipos D --detalhe "notificações do DET baixadas"
```
