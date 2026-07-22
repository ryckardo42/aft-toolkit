---
name: aft-doctor
model: sonnet
allowed-tools: Read, Glob, Grep, Bash, AskUserQuestion
description: >
  Use SEMPRE que o Auditor-Fiscal do Trabalho (AFT) quiser checar se o AFT Toolkit
  esta instalado e funcionando, ou quando algo nao estiver funcionando e for preciso
  descobrir o que falta. Acione com "/aft-doctor", "verificar instalacao", "esta tudo
  certo?", "diagnostico", "o toolkit esta funcionando?", "testar instalacao", "checar
  o toolkit", "nao esta funcionando", "as skills nao aparecem". A skill roda uma
  verificacao automatica (Python, Git, descoberta das skills, arquivos de config,
  perfil do auditor, pasta de trabalho, bibliotecas Python, NotebookLM e a saude das
  skills - frontmatter e modelos pinados, com teste ao vivo) e relata, em
  linguagem simples, o que esta OK e o que precisa ser resolvido - com a solucao de
  cada item. Nao instala nem altera arquivos - a UNICA coisa que ele conserta sozinho
  e a pasta de trabalho (AFT/OS ATIVAS e OS ARQUIVADAS), criada se faltar, no caminho
  real da pasta Documentos (no Windows ela costuma estar no OneDrive e/ou chamar-se
  "Documentos").
---

# aft-doctor — Verificacao pos-instalacao do AFT Toolkit
**AFT Toolkit**

## Objetivo

Dar ao colega, em 10 segundos, a resposta para "esta tudo certo?". E o primeiro
comando a rodar logo depois de instalar (ou sempre que algo der errado). Confere os
pre-requisitos e a configuracao e diz, sem jargao, o que falta e como resolver.

Tom: tranquilizador. O publico pode estar inseguro por ser a primeira vez. Nunca
assuste com termos tecnicos — traduza tudo.

## Passo 1 — Rodar a verificacao

```bash
python ~/.claude/skills/_scripts/aft_doctor.py
```

> Se `python` nao for encontrado, tente `python3`. Se nenhum dos dois rodar, esse ja
> e o primeiro problema: o Python nao esta instalado/no PATH — oriente a rodar
> `/aft-setup` (ele instala o Python) ou a fechar e reabrir o Claude Code se acabou
> de instalar.

O script imprime um relatorio legivel e, na ultima linha, um JSON prefixado com
`JSON:` no formato:

```json
{ "resumo": {"ok": N, "avisos": M, "erros": K},
  "checks": [ {"titulo": "...", "status": "ok|aviso|erro", "detalhe": "...", "dica": "..."} ] }
```

## Passo 2 — Traduzir o resultado para o AFT

A partir do JSON, responda de forma clara e acolhedora. Regra de ouro:

- **Se `erros` = 0 e `avisos` = 0** → diga que esta tudo pronto e relembre o comeco do
  fluxo (`/nova-os` para cadastrar uma OS, `/painel` para ver os prazos).
- **Se houver `erros` (vermelho)** → liste-os PRIMEIRO, com a solucao de cada um (campo
  `dica`). Sao itens que impedem o toolkit de funcionar (ex.: Python ausente, skills
  nao descobertas, config incompleta).
- **Se houver so `avisos` (amarelo)** → explique que o nucleo funciona, mas alguns
  itens opcionais ou de configuracao faltam, e mostre a dica de cada um. O mais comum:
  o AFT ainda nao rodou `/aft-setup` (faltam perfil, pasta de trabalho, aft-config,
  bibliotecas) — nesse caso, sugira rodar `/aft-setup` agora, que resolve vários de
  uma vez.

Use simbolos para leitura rapida: 🟢 (ok), 🟡 (aviso), 🔴 (erro). Exemplo:

```
🩺 Diagnostico do AFT Toolkit — 4 ok, 2 avisos, 0 erros

🟢 Python, Git, skills instaladas, config do toolkit — tudo certo.

🟡 Pendencias (resolvem com 1 comando):
  • Perfil do auditor e pasta de trabalho ainda nao existem.
    -> Rode /aft-setup que eu configuro tudo isso.
  • Biblioteca pypdf faltando (so afeta /autos-lavrados).
    -> O /aft-setup tambem instala.

Quer que eu rode o /aft-setup agora?
```

## Passo 3 — Oferecer a correcao (sem corrigir sozinho)

Esta skill **so diagnostica**. Para resolver, encaminhe para o lugar certo:

- Faltam perfil / pasta / aft-config / bibliotecas → **`/aft-setup`**.
- Skills nao descobertas (estao aninhadas, ex.: `~/.claude/skills/aft-toolkit/...`) →
  explique que o repositorio precisa SER a pasta `~/.claude/skills` e ofereca reinstalar
  com o prompt do COMO-INSTALAR (Passo 3).
- Config do toolkit incompleta → ofereca "Atualize o AFT Toolkit" (`/aft-atualizar`) ou reclone.
- Frontmatter de skill quebrado ou modelo pinado indisponivel → ofereca `/aft-atualizar`;
  se ja estiver atualizado e o problema persistir, oriente a avisar o mantenedor
  citando a mensagem do check (pode ser modelo descontinuado ou limitacao do plano).

So execute uma correcao se o AFT pedir. Nunca instale nada silenciosamente neste fluxo.

## Regras

- **Somente leitura.** A skill nao instala, nao baixa, nao cria pastas. Diagnostica e
  encaminha. Isso e garantido tecnicamente pelo `allowed-tools` do frontmatter: as
  ferramentas de escrita (Write/Edit) ficam indisponiveis enquanto a skill roda. (Unica ressalva: o check "teste dos modelos pinados" faz UMA chamada
  minima ao Claude por modelo datado, para confirmar que a conta do AFT tem acesso —
  gasta uma resposta curta de cota e nao altera nada.)
- O codigo `[ERRO]` (saida != 0) significa que ha pelo menos um item essencial faltando;
  trate sempre os erros antes dos avisos.
- Rodar fora de `~/.claude/skills` (ex.: testando no repositorio clonado em outra pasta)
  gera um aviso de "skills fora do lugar" — isso e esperado nesse caso e nao e problema
  na instalacao real do colega.
