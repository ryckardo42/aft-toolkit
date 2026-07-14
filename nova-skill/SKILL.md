---
name: nova-skill
model: sonnet
description: >
  Use SEMPRE que o Auditor-Fiscal do Trabalho (AFT) quiser criar uma habilidade
  (skill) PRÓPRIA no AFT Toolkit — automatizar uma tarefa da realidade dele que
  as skills oficiais não cobrem. Acione com "/nova-skill", "criar uma skill",
  "quero uma habilidade nova", "criar minha própria skill", "automatizar uma
  tarefa minha", "fazer uma skill pra mim". A skill conversa em linguagem de
  leigo (o AFT não é programador), coleta o objetivo, os gatilhos de ativação e
  o passo a passo, e grava uma skill nova em ~/.claude/skills/minha-<nome>/
  SKILL.md com frontmatter válido e o prefixo reservado "minha-", garantindo
  que ela seja descoberta pelo Claude Code e NUNCA seja perdida numa atualização
  do toolkit (git pull). NÃO edita nem substitui skills oficiais; só cria/edita
  as próprias do AFT (prefixo minha-).
---

# nova-skill — Criar uma habilidade própria do AFT
**AFT Toolkit**

## Objetivo

Deixar o AFT — que **não é programador** — criar uma skill sua, para uma tarefa da
realidade dele que o toolkit oficial não faz (ex.: um modelo de notificação específico da
região, um checklist próprio, um relatório interno). O resultado é uma skill nova em
`~/.claude/skills/minha-<nome>/SKILL.md`, que:

- fica no **primeiro nível** de `~/.claude/skills/` — condição para o Claude Code
  descobri-la (skill em subpasta aninhada fica invisível);
- usa o **prefixo reservado `minha-`** — namespace que nenhuma skill oficial ocupa, então
  ela **nunca colide nem some** quando o toolkit é atualizado (`git pull`); o `.gitignore`
  do toolkit já a protege.

Tom: paciente e concreto. Nada de jargão de programação. Você faz o trabalho técnico
(escrever o arquivo); o AFT só descreve o que quer, em português comum.

## Regra de ouro (inegociável)

Esta skill **só cria ou edita skills próprias do AFT** (pasta começando com `minha-`).
**Nunca** edite, renomeie ou sobrescreva uma skill oficial do toolkit (qualquer pasta sem
o prefixo `minha-`) por meio desta skill — nem que o AFT peça "muda a /gera-ai". Se ele
quiser alterar comportamento de uma skill oficial, explique que isso é mudança no
repositório oficial (mantenedor) e ofereça, no lugar, criar uma `minha-*` que faça o que
ele precisa. Toda pasta que você criar aqui começa com `minha-`.

## FASE 1 — Entender o que o AFT quer automatizar

Pergunte, em linguagem simples e em uma rodada (aceite o que ele já contou):

1. **O que essa habilidade deve fazer?** (uma ou duas frases — ex.: "montar um ofício de
   encaminhamento pro MP com os dados da OS").
2. **Quando você vai querer usá-la?** Quais frases/gatilhos — ex.: "gerar ofício MP",
   "encaminhar pro Ministério Público". Isso vira a lista de acionamento.
3. **Passo a passo:** o que ela precisa fazer, na ordem. Aceite bullets tortos; você
   organiza depois. Se ele não souber detalhar, ajude com perguntas ("de onde vêm os
   dados? o resultado é um texto na tela, um arquivo salvo?").
4. **Ela usa algum arquivo ou pasta?** (ex.: lê o `memory.md` da OS, salva um `.md` na
   pasta da empresa). Opcional.

Se algo ficar vago, pergunte antes de escrever — é melhor uma pergunta a mais do que uma
skill que não faz o que ele quis.

## FASE 2 — Propor o desenho e confirmar

Antes de gravar, apresente um resumo curto para o AFT aprovar:

```
Vou criar a skill: /minha-<nome>
  • O que faz: <objetivo em 1 frase>
  • Aciona quando você diz: <gatilhos>
  • Passos: 1) ... 2) ... 3) ...
  • Mexe em arquivos? <não / lê o memory.md / salva em ...>
Confirma? (posso ajustar antes de criar)
```

- **Nome da pasta**: `minha-` + um nome curto em minúsculas, sem espaços nem acento
  (troque espaços por hífen). Ex.: "ofício pro MP" → `minha-oficio-mp`. Mostre o nome
  final e deixe o AFT trocar se quiser. Confira que **não existe** já uma pasta com esse
  nome (`ls ~/.claude/skills/ | grep '^minha-'`); se existir, pergunte se é para
  **editar** a existente ou usar outro nome.
- Só prossiga para a FASE 3 após o "confirma".

## FASE 3 — Gravar a skill

Crie `~/.claude/skills/minha-<nome>/SKILL.md` com a tool Write, neste esqueleto (o
frontmatter é obrigatório e o `name` **tem de ser idêntico** ao nome da pasta):

```markdown
---
name: minha-<nome>
description: >
  <Uma descrição que comece por "Use quando o AFT..." e liste os gatilhos que o
  AFT deu — é isso que faz o Claude Code saber quando acionar a skill. Escreva
  em 3ª pessoa, incluindo as frases-gatilho literais entre aspas.>
---

# minha-<nome> — <título curto>
**Skill própria do AFT**

## Objetivo
<o que faz, em 1–2 frases>

## Passo a passo
1. <passo 1>
2. <passo 2>
3. <passo 3>

## Regras
- <restrições que o AFT pediu, se houver>
- Encoding UTF-8; se gerar texto para o Sistema Auditor, sem travessões nem aspas curvas.
```

Regras ao escrever:
- **`name` = nome da pasta**, sempre (o `/aft-doctor` valida isso; se divergir, a skill
  não é acionada).
- **Não pinar `model`** por padrão — sem o campo `model`, a skill herda o modelo da sessão,
  que é o mais seguro para uma skill do AFT. Só inclua `model:` se o AFT pedir
  explicitamente um modelo, e nesse caso use um apelido (`sonnet`, `opus`, `haiku`).
- A `description` é a parte mais importante: é o que dispara a skill. Capriche nos
  gatilhos que o AFT deu, com as frases literais entre aspas.
- Se a skill precisar de lógica exata e repetitiva (cálculo, formatação rígida, troca de
  dados), lembre que o certo é um **script** determinístico — ofereça criar um `.py` na
  pasta da skill em vez de pedir para a IA "fazer de cabeça" (mesma filosofia do toolkit).
- Se a skill lida com dados de trabalhador, herde a regra de privacidade do toolkit
  (tokens `[[TRAB_NN]]`, nunca ecoar nome/CPF real) — avise o AFT disso.

## FASE 4 — Validar e encerrar

1. Rode o diagnóstico para confirmar que a skill nova está bem formada e protegida:
   ```bash
   python ~/.claude/skills/_scripts/aft_doctor.py
   ```
   Procure a linha **"Skills proprias (minha-*)"** — ela deve listar a skill nova como
   válida e "protegida de atualizacoes". Se acusar frontmatter/name a corrigir, conserte
   o `SKILL.md` e rode de novo.
2. Confirme ao AFT, em linguagem simples:

```
✅ Skill criada: /minha-<nome>
📁 ~/.claude/skills/minha-<nome>/SKILL.md
🔒 É sua e fica protegida: nenhuma atualização do AFT Toolkit vai apagá-la ou mexer nela.

Como usar: comece uma conversa e diga "<um dos gatilhos>" (ou digite /minha-<nome>).
Para mudar algo depois, é só me pedir "edita a minha-<nome>".
```

3. Avise que, para o Claude Code **enxergar** a skill nova, pode ser preciso **reabrir**
   o app (as skills são carregadas no início da sessão).

## Regras

- **Só mexe em skills `minha-*`.** Nunca cria, edita ou apaga skill oficial do toolkit.
- Toda skill criada fica no **primeiro nível** de `~/.claude/skills/` (nunca em subpasta —
  o Claude Code não enxerga skill aninhada) e começa com **`minha-`** (namespace reservado,
  protegido pelo `.gitignore` do toolkit contra atualizações).
- `name` do frontmatter **idêntico** ao nome da pasta; sem isso a skill não é acionada.
- Não invente comportamento que o AFT não pediu; a skill deve fazer só o que foi combinado
  na FASE 2.
- Nunca sugira commitar/enviar a skill própria para o repositório oficial — ela é local e
  pessoal por definição.
