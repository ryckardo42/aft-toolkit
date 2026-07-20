---
name: sessoes-os
model: sonnet
description: >
  Use este skill SEMPRE que o Auditor-Fiscal do Trabalho (AFT) quiser uma sessão do Claude
  Code por empresa fiscalizada na barra lateral do app, organizadas no grupo "OS ATIVAS".
  Acione com "/sessoes-os", "cria as sessões das minhas auditorias", "uma sessão por
  empresa", "organiza as sessões no menu lateral", "sincroniza as sessões com OS ATIVAS",
  "monta o grupo de auditorias". A skill roda o _scripts/sessoes_os.py, que espelha as
  pastas de OS ATIVAS na barra lateral: cria (ou reaproveita) uma sessão por empresa com o
  título da empresa e a pasta da OS como diretório de trabalho, coloca todas no grupo
  "OS ATIVAS" e grava o vínculo sessao_claude no memory.md de cada OS. Como o app regrava
  as preferências enquanto está aberto, a aplicação acontece num modo vigia: o AFT fecha o
  app (Cmd+Q), o script aplica e reabre o app sozinho. Também verifica ("--status") e
  desfaz ("--desfazer"). Acionada pelo /aft-setup, pelo /aft-atualizar e após o /nova-os.
---

# sessoes-os — uma sessão por auditoria, no grupo "OS ATIVAS"
**AFT Toolkit**

## O que faz

Espelha as suas auditorias na barra lateral do app do Claude Code: **cada empresa
fiscalizada ganha a própria sessão de chat**, com o nome da empresa e já apontando para a
pasta da OS, todas dentro do grupo **"OS ATIVAS"**. Tudo que for daquela auditoria passa a
ser tratado na sessão dela — contexto acumulado, histórico num lugar só.

> **Aviso honesto (o AFT deve saber):** o app não oferece uma API oficial para criar
> sessões e grupos; a skill escreve no armazenamento interno do app (o mesmo arquivo em
> que ele guarda essas informações). Por isso: (1) há sempre backup antes e um
> `--desfazer`; (2) a aplicação exige **fechar e reabrir o app** (o script cuida da
> reabertura); (3) se uma atualização do app mudar o formato interno, o script **aborta
> sem tocar em nada** e avisa. Os dados ficam na sua máquina e sobrevivem a atualizações
> do app.

## Fluxo de execução

### 1. Diagnóstico (sempre primeiro, não altera nada)

```
python3 ~/.claude/skills/_scripts/sessoes_os.py --status
```

Mostre ao AFT o resultado em linguagem simples: quantas OS têm sessão, quantas serão
criadas, se o grupo existe. A última linha `JSON:` traz o resumo estruturado. Se tudo já
estiver sincronizado, diga isso e encerre.

### 2. Confirmar e disparar o modo vigia

Explique o que vai acontecer e peça confirmação:

> Vou criar N sessões (uma por empresa) no grupo "OS ATIVAS". Para aplicar, o app precisa
> ser fechado por alguns segundos — eu deixo um assistente aguardando: você fecha o app
> (Cmd+Q), ele aplica e REABRE o app sozinho. Quando o app voltar, o grupo estará montado.
> Posso preparar?

Com o sim, dispare o vigia **desacoplado do app** (sobrevive ao fechamento) e instrua:

```
nohup python3 ~/.claude/skills/_scripts/sessoes_os.py --aplicar >/dev/null 2>&1 & disown
```

> Pronto — agora é só fechar o app do Claude (Cmd+Q). Ele reabre sozinho em alguns
> segundos com o grupo montado. Quando voltar, me chame em qualquer sessão e diga
> "verifica as sessões" que eu confiro se deu tudo certo.

### 3. Conferência (na volta do app)

Quando o AFT voltar, leia `~/Documents/AFT/.sessoes-os.log` (o script registra tudo lá) e
rode `--status` de novo. Relate: sessões criadas, reaproveitadas (as que ele já tinha,
casadas pelo título), vínculos gravados. Se algo falhou, o log diz onde parou — e o
`--desfazer` restaura o backup e remove o que foi criado (também em modo vigia).

## Regras

- **Nunca rode `--aplicar --agora` com o app aberto** — o app sobrescreveria a mudança ao
  fechar. O modo vigia existe exatamente para isso.
- **Reaproveite, não duplique**: sessão existente cujo título case com a empresa é
  vinculada e agrupada, nunca recriada.
- O vínculo fica no front-matter do memory.md (`sessao_claude: "local_..."`) — é ele que
  permite ao Claude rotear conversas para a sessão certa (regra do perfil do auditor).
- OS nova depois disso? Rode a skill de novo — só o delta é aplicado (idempotente).
- OS arquivada: a sessão correspondente NÃO é apagada pela skill; o Claude oferece
  arquivá-la (regra do perfil), e o app pede a confirmação final.

## Solução de problemas

| Sintoma | O que fazer |
|---|---|
| Grupo não apareceu após reabrir | Ler o log; se o script ainda aguardava, o app foi reaberto antes de fechar de fato — feche de novo (o vigia continua ativo) |
| "estrutura do config não reconhecida" | O app mudou o formato interno numa atualização — rode /aft-atualizar; nada foi alterado |
| Sessão criada não abre direito | `--desfazer` restaura tudo; reporte o caso |
| Quero voltar atrás | `python3 ~/.claude/skills/_scripts/sessoes_os.py --desfazer` (modo vigia também) |
