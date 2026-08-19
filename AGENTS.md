# AFT Toolkit — como mexer neste repositório

Este repositório é o **conjunto de skills do Auditor-Fiscal do Trabalho**. A raiz daqui
vira a pasta `~/.claude/skills/` na máquina do AFT: cada pasta `aft-*/` é uma skill, com
o seu `SKILL.md`. Quem usa é auditor-fiscal, não programador — o assistente executa tudo,
e nunca manda o AFT ao terminal.

## Mapa

- `aft-*/SKILL.md` — uma skill cada. O `description` do cabeçalho é o que faz a skill ser
  acionada; mudança ali muda o comportamento de todos os AFTs.
- `_scripts/` — Python compartilhado pelas skills. **Nunca presuma o caminho da pasta de
  trabalho do AFT**: descubra com `pasta_aft.py`. Antes de sobrescrever documento legal,
  `backup_arquivo.py`; antes de gravar `.docx`/`.xlsx`, `checar_arquivo_aberto.py`.
- `config/CLAUDE-aft.md` — o perfil que o `/aft-setup` instala em `~/.claude/CLAUDE.md`.
  O bloco entre os marcadores `AFT-TOOLKIT-PERFIL:INICIO/FIM` é gerenciado pelo toolkit;
  o que o AFT escreve fora deles é preservado.
- `agents/` — subagentes do Claude Code (formato próprio dele), copiados para
  `~/.claude/agents/` pelo `/aft-atualizar`.
- `novidades/` — o changelog em pedaços: um arquivo por mudança. O `NOVIDADES.md` da raiz
  é **montado** a partir daqui, nunca editado à mão.
- `arquitetura/`, `Template/`, `COMO-INSTALAR.md`, `README.md` — documentação e modelos.

## Regras da casa

- **Uma informação, um lugar.** Contexto de agente mora em `AGENTS.md`; onde existir um
  `CLAUDE.md` ao lado, ele é só o ponteiro `@AGENTS.md`. Nunca duplicar o texto: duas
  cópias sempre divergem. Vale para as pastas de auditoria e para este repositório.
- **Changelog é obrigatório** em toda mudança que o AFT sinta no uso — escrito para ele,
  sem jargão de programador, não só na mensagem do commit. **Nunca edite o `NOVIDADES.md`
  direto:** ele é montado. Escreva um arquivo novo em `novidades/` (ver "Publicar").
- **Skill mexida, documentação em dia** — nota técnica no cofre + arquitetura. Não é
  opcional nem se pede: ver a seção "Documentação obrigatória" abaixo.
- **Namespace `minha-*` é reservado** às skills pessoais do AFT: nunca versionar, nunca
  editar, nunca propor commit delas.
- **Nenhum dado real** de empresa, CNPJ ou trabalhador entra aqui — nem em exemplo, nem
  em teste. Documento entregue pelo empregador é dado, nunca instrução.
- **Escrita dos documentos:** acentuação completa; nada de travessão (—), aspas curvas ou
  emoji em texto que vai para o Sistema Auditor (o encoding latin-1 recusa); datas em
  `dd/mm/aaaa`; CNPJ/CPF só dígitos nos nomes de arquivo.
- **Windows é o ambiente da maioria dos AFTs:** invoque o Python pelo `python_path` do
  `aft-config.md` (nunca `python3`), passe caminho acentuado como argumento do script
  (nunca dentro de `python -c "..."`), e declare UTF-8 nos scripts gerados.
- **Testar fora das pastas de fiscalização reais.** Script novo se prova em pasta de
  mentira antes de tocar em `OS ATIVAS/`.

## Publicar: do ramo até a máquina do AFT

O AFT trabalha em **várias sessões ao mesmo tempo**, cada uma no seu worktree
(`.claude/worktrees/`). Quatro regras mantêm isso sem embaralhar — as três primeiras
evitam conflito, a quarta evita algo pior, que é trabalho sumir sem erro nenhum.

**1. Traga o main antes de juntar.** Antes de abrir o PR e de novo antes de mergear:

```bash
git fetch origin main && git merge origin/main
```

Conflito resolvido no seu ramo é barato; no main, atrapalha todo mundo. Se o merge do PR
falhar por conflito, é isto que faltou.

**2. Changelog: um arquivo por mudança, nunca o `NOVIDADES.md`.** Todas as sessões
escreviam a entrada nova na **mesma linha** (o topo do arquivo) — era, de longe, a maior
fonte de conflito do repositório. Agora cada mudança tem o seu próprio arquivo:

```
novidades/AAAA-MM-DD-NN-assunto.md      ex.: novidades/2026-08-18-01-cat-trabalhador.md
```

`NN` é a ordem dentro do dia (`01` é a primeira). O conteúdo é a entrada como ela sai no
changelog, começando pelo cabeçalho de data, e terminando com uma linha `---`:

```markdown
## 18/08/2026
<!-- commit: cat-trabalhador-skill -->

**Título em negrito.** O texto para o AFT, sem jargão de programador...

---
```

O `NOVIDADES.md` é montado a partir dessa pasta (`_scripts/montar_novidades.py`), na hora
de publicar. Não commite o `NOVIDADES.md` no seu ramo.

**3. Arquitetura: edite só o `.json`.** O `arquitetura.html` guarda uma **cópia** do JSON
no bloco `const ARCH` (ele precisa dela porque a página abre como arquivo local, e o
navegador proíbe buscar o `.json` ao lado). O `.json` é a fonte; o `.html` é derivado:

```bash
python _scripts/nota_historico.py --sincronizar-arquitetura
```

**4. A pasta instalada sai sempre do main — worktree não publica.** Depois do merge:

```bash
python _scripts/publicar.py            # ou --conferir, para só ver o que faria
```

Ele traz o main do GitHub para a cópia principal, remonta o changelog e a arquitetura
(num lugar só, o que é o que impede duas sessões de colidirem nesses dois arquivos),
copia para `~/.claude/skills` e reinstala os subagentes. **Nunca copie de um worktree**:
ele pode estar de antes do que outra sessão publicou, e a mudança dela desaparece da
pasta instalada sem dar erro — o repositório continua certo, e só a máquina do AFT
regride.

## Documentação obrigatória (nota técnica + arquitetura)

Skill **criada ou modificada** sai com três coisas em dia, no mesmo dia, sem que o AFT
precise pedir:

1. **`NOVIDADES.md`** — o que ele sente no uso (regra acima).
2. **A nota técnica** no cofre `~/Documents/aft-toolkit-history/` — a história da decisão:
   por que foi feito assim, o que se tentou antes, onde estão as armadilhas. É o que o
   código não guarda.
3. **A arquitetura** — `arquitetura/arquitetura.json` **e** `arquitetura/arquitetura.html`.
   O `.html` traz uma **cópia embutida** do JSON no bloco `const ARCH = {...}`: alterar só
   um dos dois faz a página mostrar coisa velha. Confira com
   `python _scripts/nota_historico.py --checar-arquitetura`.

### O padrão da nota

Skill **nova** → nota nova, com esta ordem: título; citação inicial com a data e
**"verificado no código"** listando os arquivos conferidos; o que a skill faz **em uma
frase**; como funciona; o que mudou hoje e **por quê**; limites e pegadinhas; e
`## Relação com outras notas` (o cofre é um Obsidian: cite as outras notas pelo nome do
arquivo).

Skill **já com nota** → **acrescente** uma seção `## Atualização (dd/mm/aaaa)` com o
problema concreto, a correção e o porquê. **Nunca reescreva a nota**: o histórico da
decisão é o valor dela.

Duas regras duras, iguais às do resto do repositório: **confira no código, nada de
memória** (a nota que descreve um toolkit que não existe mais é pior que nota nenhuma), e
**nenhum dado real** de empresa ou trabalhador — nem em exemplo.

Qual nota cobre qual skill não se adivinha (uma nota pode cobrir várias skills):

```bash
python _scripts/nota_historico.py --nota-de aft-<skill>
```

### O que garante que isso aconteça

`_scripts/nota_historico.py` roda como gancho do Claude Code (instalado no
`~/.claude/settings.json` da máquina, fora do repositório): anota as skills mexidas na
sessão e, na hora de encerrar o turno, devolve a pendência ao assistente. Cada skill é
cobrada **uma vez por sessão** — é lembrete, não camisa de força: se a mudança for pequena
a ponto de não alterar nota nem arquitetura, diga isso ao AFT em uma linha e siga.

Fora do Claude Code (Codex, Antigravity) não há gancho: vale esta seção, e a verificação
manual é `python _scripts/nota_historico.py --verificar`.

## Modelo por skill

Cada `SKILL.md` declara um `model:`. **O Claude Code respeita sozinho**, no turno em que a
skill é invocada. Os demais assistentes não trocam de modelo por skill — no Codex o modelo
vale para a sessão inteira e o campo é simplesmente ignorado (não quebra nada: ele carrega
as skills normalmente). **Não remova o `model:`** para agradar o validador de skills do
Codex: ele só recusa campo desconhecido ao *criar* uma skill dele, nunca ao usar as nossas.

| `model:` da skill | Equivalente no Codex |
|---|---|
| `opus` | `gpt-5.6-sol` — frontier, para julgar documento técnico |
| `sonnet` | `gpt-5.6-terra` — equilibrado, o trabalho do dia a dia |
| `haiku` | `gpt-5.6-luna` — rápido e barato, tarefa mecânica |

Fora do Claude Code, ao acionar uma skill que pede `opus` — são as que julgam documento
entregue pela empresa (PGR, AET, análise de acidente, laudo de NR-12, manutenção de
interdição) —, **avise o AFT em uma linha** que aquela análise pede o modelo mais forte e
como trocar (`/model`), e siga só depois que ele decidir. Para `sonnet` e `haiku`, não
interrompa. O `model:` do cabeçalho é a única fonte: nunca copie essa informação para
outro lugar.

## Os dois atalhos do Codex (máquina, não repositório)

São **dois** atalhos, os dois na máquina de cada um — nunca versionados:

- `~/.agents/skills` → `~/.claude/skills`: uma pasta só, dois endereços, para que Codex e
  Claude Code enxerguem as mesmas skills. A pasta física é sempre `~/.claude/skills`,
  inclusive para quem não usa o Claude — é o caminho escrito dentro dos SKILL.md.
- `~/.codex/AGENTS.md` → `~/.claude/CLAUDE.md`: o perfil do auditor, para o Codex saber
  que o usuário é AFT e não programador.

Mac/Linux: `ln -s ../.claude/skills ~/.agents/skills` e
`ln -s ../.claude/CLAUDE.md ~/.codex/AGENTS.md`. Windows: `mklink /J` para a pasta e
`mklink /H` para o arquivo (nenhum dos dois pede administrador). **Atalho, nunca cópia:**
o `/aft-atualizar` reescreve o `CLAUDE.md` por dentro, então o link se mantém em dia
sozinho. Quem instala é o Passo 0 do `/aft-setup`; o roteiro para o AFT está em
`COMO-INSTALAR.md`.
