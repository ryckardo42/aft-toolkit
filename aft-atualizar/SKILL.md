---
name: aft-atualizar
model: sonnet
description: >
  Use SEMPRE que o Auditor-Fiscal do Trabalho (AFT) pedir para atualizar o AFT
  Toolkit. Acione com "/aft-atualizar", "atualize o toolkit", "atualize o aft
  toolkit", "atualizar o kit", "tem atualização?", "verificar atualizações",
  "buscar novidades do toolkit", "puxar a última versão". A skill confere DUAS
  fontes — o repositório https://github.com/ryckardo42/aft-toolkit (as skills) e
  o pacote https://github.com/teng-lin/notebooklm-py (o comando `notebooklm`) —,
  atualiza as que estiverem desatualizadas e, ao final, roda o /aft-doctor para
  confirmar que nada quebrou. Diferente do /aft-doctor (só diagnostica, nunca
  instala), esta skill É a que efetivamente baixa e instala as atualizações.
---

# aft-atualizar — Atualizar o AFT Toolkit (skills + notebooklm-py)
**AFT Toolkit**

## Objetivo

Um único comando para manter as duas peças do toolkit em dia: as **skills**
(este repositório) e o **comando `notebooklm`** (pacote de terceiro,
`teng-lin/notebooklm-py`, que as skills usam para consultar ementas). No final,
confirma que tudo continua funcionando com o `/aft-doctor`.

Tom: tranquilizador e direto. O AFT não precisa entender git nem pip — só saber
o que mudou e se precisa fazer algo (normalmente não).

## Passo 1 — Atualizar as skills (repositório do toolkit)

Na pasta das skills (você roda):

```bash
cd ~/.claude/skills
git fetch origin
git log HEAD..origin/main --oneline   # commits novos disponíveis
```

- **Lista vazia** → já está na última versão; informe isso e siga para o Passo 2.
- **Lista com commits** → **antes de baixar**, faça a varredura de segurança (Passo 1a) e
  capture as novidades para o AFT (Passo 1b). Só depois das duas, atualize:
  ```bash
  git pull origin main
  ```
  Use **sempre** fast-forward simples (sem rebase/merge manual). Se o `pull` falhar
  por mudanças locais não commitadas, **não descarte nada**: avise o AFT e pergunte
  como prosseguir (isso não deveria acontecer numa instalação normal, em que o AFT
  nunca edita os arquivos do repositório).

### Passo 1a — Varredura de segurança do que está chegando (antes do pull)

Uma atualização de skills é **código de terceiro** entrando na máquina do AFT: roda com
acesso aos documentos e dados reais da fiscalização. Antes do `git pull`, confira o que
muda e varra o conteúdo que está chegando por sinais de adulteração (Unicode invisível,
cano para shell, `ANTHROPIC_BASE_URL`, exfiltração por rede). Você roda:

```bash
git diff --stat HEAD..origin/main                      # quais arquivos mudam
python ~/.claude/skills/_scripts/checar_diff.py        # varredura das linhas novas
```

- **Saída `✓` (nada suspeito)** → siga para o `git pull` normalmente.
- **Saída `⚠️` (sinais suspeitos)** → **NÃO dê o pull.** Mostre os achados ao AFT em
  linguagem simples, explique que a atualização traz algo fora do padrão e só prossiga
  se ele confirmar que a mudança é legítima (autor/commit conhecido). Na dúvida, não
  atualize: o toolkit antigo funcionando é melhor que um novo adulterado.

O `checar_diff.py` é um alarme: nunca bloqueia nem altera nada, só relata. Quem decide
seguir é sempre o AFT.

### Passo 1b — Capturar as novidades (antes do pull)

O `NOVIDADES.md` na raiz do repositório é o changelog escrito **para o AFT** (sem jargão
de programador) — é o que você vai apresentar no resumo final, não as mensagens de commit
(essas são para quem mantém o código). Capture as entradas que ainda não chegaram nesta
máquina:

```bash
git diff HEAD..origin/main -- NOVIDADES.md
```

- **Diff com linhas `+`** → são as entradas novas. Guarde o texto (ignore linhas `+++` de
  cabeçalho e comentários `<!-- commit: ... -->`, que são só para rastreamento interno) —
  vai direto no resumo do Passo 4, praticamente sem reescrever.
- **Diff vazio, mas havia commits na lista do Passo 1** → essa atualização não teve
  entrada de changelog (pode acontecer: nem toda mudança é relevante o bastante para o
  AFT, ou foi esquecida). Não deixe isso desaparecer: liste os títulos desses commits
  (`git log HEAD..origin/main --oneline`) como "outras alterações desta atualização",
  traduzindo cada título para uma frase simples — é a rede de segurança para quando o
  `NOVIDADES.md` não foi atualizado junto.

## Passo 2 — Atualizar o `notebooklm` (notebooklm-py)

Confira a versão instalada e a versão mais recente publicada (você roda):

```bash
notebooklm --version
```

```bash
curl -s https://pypi.org/pypi/notebooklm-py/json | python3 -c "import json,sys; print(json.load(sys.stdin)['info']['version'])"
```

- Se o `notebooklm --version` falhar ("comando não encontrado"), o pacote não está
  instalado — não é erro desta skill; apenas informe e siga (o `/notebooklm-login`
  ou o `/aft-setup` cuidam da instalação na próxima vez que forem usados).
- Se as duas versões forem **iguais**, informe que já está atualizado.
- Se a versão instalada for **mais antiga**, atualize automaticamente, sem perguntar
  (mantendo os mesmos extras usados na instalação original):
  ```bash
  pipx upgrade notebooklm-py
  ```
  Se o pacote não foi instalado via pipx (comando acima falha ou não muda nada),
  use o equivalente em pip:
  ```bash
  python -m pip install --user --upgrade "notebooklm-py[browser,cookies]"
  ```
  Depois confirme com `notebooklm --version` que a versão nova ficou ativa.

## Passo 2b — Oferecer a rotina diária do painel (só na primeira vez)

O toolkit ganhou a opção de o `/painel` se atualizar sozinho toda manhã (agendamento do
próprio sistema operacional — launchd/Agendador de Tarefas, zero tokens, sem abrir o
Claude Code). AFTs que instalaram o toolkit antes dessa novidade nunca foram perguntados.
Confira se já foi oferecida:

```bash
grep -q "rotina_painel" ~/Documents/AFT/aft-config.md && echo "ja_perguntado" || echo "nunca_perguntado"
```

- **`ja_perguntado`** → não pergunte de novo; siga para o Passo 2c.
- **`nunca_perguntado`** → ofereça **uma única vez**, em uma frase: *"Novidade: o
  painel pode se atualizar sozinho toda manhã, sem você pedir — não gasta nada, é o
  próprio computador rodando um programinha. Quer ativar?"*
  - **Não** → grave `rotina_painel: ""` no front-matter do `aft-config.md` (só para não
    perguntar de novo nas próximas atualizações) e siga.
  - **Sim** → siga exatamente o Passo 7b do `/aft-setup` (mesmo script
    `instalar_rotina_painel.py`, mesmo `python_path`/pasta de OS ATIVAS já configurados)
    e grave `rotina_painel: "07:00"` (ou o horário escolhido) no `aft-config.md`.

## Passo 2c — Garantir o painel interativo sempre ligado

O **servidor interativo** (Passo 7c do `/aft-setup` — controles do painel + sync do DET
pela extensão Chrome) passou a ser **parte padrão** do toolkit, não mais opcional. Se esta
máquina ainda não o tem ligado, instale-o **sem perguntar** (roda só em `127.0.0.1`, nada
sai da máquina). Confira o estado no `aft-config.md`:

```bash
grep -q 'servidor_painel: *"ligado"' ~/Documents/AFT/aft-config.md && echo "ja_ligado" || echo "instalar"
```

- **`ja_ligado`** → nada a fazer; siga para o Passo 2d.
- **`instalar`** → rode o Passo 7c do `/aft-setup` (mesmo script
  `instalar_servidor_painel.py`, mesmo `python_path`/pasta de OS ATIVAS já configurados) e
  grave `servidor_painel: "ligado"` no `aft-config.md` — se a chave já existir com outro
  valor (ex.: `servidor_painel: ""`, de quem recusou quando era opcional), **substitua o
  valor na linha existente**, nunca acrescente uma segunda linha. **Avise no resumo** (Passo 4), em
  uma linha, que o painel interativo agora fica sempre ligado (sobe sozinho no login, só
  na máquina dele) — e que, se ele não quiser, é só pedir para remover
  (`instalar_servidor_painel.py remover`). Isso inclui quem tinha recusado antes: a função
  deixou de ser opcional.

## Passo 2d — Oferecer os prazos de DET no Google Calendar (só na primeira vez)

Mesma lógica do Passo 2b, para a novidade do **Google Calendar** (Passo 7d do
`/aft-setup` — skill `/agenda-det`). Confira:

```bash
grep -q "agenda_det" ~/Documents/AFT/aft-config.md && echo "ja_perguntado" || echo "nunca_perguntado"
```

- **`ja_perguntado`** → não pergunte de novo; siga para o Passo 2e.
- **`nunca_perguntado`** → ofereça **uma única vez**, em uma frase: *"Novidade: os
  prazos das notificações DET podem aparecer direto no seu Google Calendar — um evento
  por notificação, atualizado quando o prazo muda e marcado com ✓ quando você responde.
  Quer ativar?"*
  - **Não** → grave `agenda_det: ""` no `aft-config.md` e siga (lembre que o painel tem
    o botão "agendar no Google Calendar", sem login).
  - **Sim** → siga exatamente o Passo 7d do `/aft-setup` (conector Google Calendar +
    primeira sincronização pela `/agenda-det`) e grave `agenda_det: "diario"` ou
    `"manual"` conforme a escolha.

## Passo 2e — Re-sincronizar o perfil do auditor (CLAUDE.md)

O perfil `~/.claude/CLAUDE.md` (instalado pelo `/aft-setup`) é uma **cópia** do template
`config/CLAUDE-aft.md` e **não** é atualizado pelo `git pull`. O toolkit cerca a parte
dele do CLAUDE.md com marcadores invisíveis (`<!-- AFT-TOOLKIT-PERFIL:INICIO vN ... -->`
… `<!-- AFT-TOOLKIT-PERFIL:FIM -->`) e uma versão, para poder atualizar **só esse bloco**
sem tocar em nada que o AFT tenha escrito por fora. Sempre confira o estado (você roda):

```bash
python ~/.claude/skills/_scripts/sync_perfil.py --status \
  ~/.claude/skills/config/CLAUDE-aft.md ~/.claude/CLAUDE.md
```

Aja conforme a **única linha** de saída:

- **`EM_DIA v<N>`** → nada a fazer; siga para o Passo 2f.
- **`DESATUALIZADO instalada=v<X> template=v<Y>`** → atualize **automaticamente, sem
  perguntar** (o script faz backup antes e troca só o bloco marcado; o que o AFT
  escreveu fora dos marcadores fica intacto):
  ```bash
  python ~/.claude/skills/_scripts/sync_perfil.py --aplicar \
    ~/.claude/skills/config/CLAUDE-aft.md ~/.claude/CLAUDE.md
  ```
  Mencione no resumo do Passo 4, em uma linha: *"Seu perfil de auditor foi atualizado
  (v\<X\> → v\<Y\>) — só o bloco do toolkit; o que você tinha escrito à parte ficou
  intacto."* (A versão nova do perfil vale a partir da **próxima** conversa.)
- **`SEM_MARCADOR`** → é uma instalação **antiga**, feita antes dos marcadores. Aqui o
  toolkit não tem como distinguir o texto velho dele do que o AFT escreveu, então
  **ofereça UMA vez** (mesma escolha do Passo 5b do `/aft-setup`): *"Seu perfil de
  auditor está numa versão antiga e desde então ganhou regras importantes (proteção
  contra documentos que tentam te dar ordem, robustez no Windows, skills novas). Quer que
  eu (a) substitua o CLAUDE.md pelo perfil novo, (b) acrescente o perfil novo ao final do
  que você já tem, ou (c) deixe como está? Depois de adotado, as próximas atualizações do
  perfil passam a ser automáticas."*
  Antes de executar, pergunte se ele alguma vez **escreveu algo próprio** no CLAUDE.md:
  - **Nunca mexeu** (o arquivo é só o perfil antigo do toolkit) → recomende e execute **(a)**:
    `python ~/.claude/skills/_scripts/sync_perfil.py --adotar-substituir …` — substituir é
    seguro aqui e evita ficar com o texto antigo duplicado.
  - **Personalizou** → recomende **(b)**:
    `python ~/.claude/skills/_scripts/sync_perfil.py --adotar-acrescentar …` — preserva o
    arquivo dele e anexa o bloco novo ao final. **Avise** que o texto antigo do perfil
    (se ainda estiver lá) fica duplicado acima do bloco novo; ofereça-se para apagar só os
    trechos antigos do toolkit, mantendo o que é pessoal dele (com backup antes).
  - **(c)** → não faça nada; o script não grava. (Volta a perguntar na próxima vez.)
- **`SEM_ARQUIVO`** → o AFT nunca instalou o perfil. Fora do escopo desta skill: sugira
  rodar `/aft-setup` (Passo 5b) numa próxima vez. Não crie o arquivo aqui.

## Passo 2f — Sessões por auditoria (conferir, oferecer se faltar)

Rode o diagnóstico (não altera nada):

```bash
python ~/.claude/skills/_scripts/sessoes_os.py --status
```

Leia a linha `JSON:` do final:

- **`criar` = 0 e `agrupar` = 0** → nada a fazer; siga para o Passo 3.
- **Há OS sem sessão** → informe em uma frase (*"Você tem N auditorias sem sessão própria
  no menu lateral"*) e ofereça rodar a `/sessoes-os` **depois** que a atualização
  terminar (ela precisa fechar e reabrir o app; não faça isso no meio da atualização).
- **Script falhou / formato não reconhecido** → apenas registre no resumo do Passo 4; não
  é bloqueante.

## Passo 3 — Confirmar que nada quebrou (`/aft-doctor`)

Sempre rode ao final, mesmo se nada tiver sido atualizado no Passo 1/2 (serve
também para confirmar que o ambiente já estava certo):

```bash
python ~/.claude/skills/_scripts/aft_doctor.py
```

Traduza o resultado seguindo as regras do `/aft-doctor` (🟢/🟡/🔴, erros antes de
avisos). Se aparecer algum erro novo causado pela atualização, explique e oriente
a solução — não deixe o AFT com a sensação de que "atualizar" pode ter quebrado
algo sem explicação.

## Passo 4 — Resumo final ao AFT

Uma mensagem só, juntando os passos. As novidades vêm do `NOVIDADES.md` capturado no
Passo 1b — apresente o conteúdo das entradas, não os títulos de commit. Exemplo:

```
🔄 Atualização do AFT Toolkit

✅ Skills atualizadas — novidades para você:

📋 Painel interativo — agora dá para marcar DET como checada, resolver pendência e
   mudar status direto pelo navegador, sem pedir ao Claude.
🔄 Sincronização automática do DET — a extensão do Chrome importa notificações e
   prazos direto nas suas fichas.
🐛 2 correções: notificações de fiscalizações antigas não vazam mais para a OS
   errada; prazo de item de NAD não é mais sobrescrito por engano.

✅ notebooklm: atualizado de 0.6.0 → 0.7.2

🩺 Diagnóstico pós-atualização: tudo certo (4 ok, 0 avisos, 0 erros)
```

Se nada mudou em nenhuma das duas fontes, diga isso em uma frase e confirme o
diagnóstico — não é preciso alarde. Se houve commits sem entrada no `NOVIDADES.md`
(rede de segurança do Passo 1b), inclua-os como "outras alterações desta atualização",
separados das novidades principais.

## Regras

- **Nunca** rode `git reset --hard`, `git checkout -- .` ou qualquer comando que
  descarte alterações locais sem perguntar antes — numa instalação normal isso
  nunca deveria ser necessário.
- A atualização do `notebooklm-py` é automática (sem pedir confirmação a cada
  vez), mas sempre **reporte** a troca de versão — o AFT precisa saber o que
  mudou, mesmo sem precisar agir.
- Esta skill **instala/atualiza**; o `/aft-doctor` (chamado no Passo 3) **só
  diagnostica**. Não pule o Passo 3: é o que garante que a atualização não
  deixou nada quebrado para o AFT descobrir sozinho em campo.
- **Skills próprias do AFT (`minha-*`) são preservadas.** O `git pull` fast-forward
  nunca toca nelas (namespace reservado + `.gitignore`). Se o AFT tiver alguma, o Passo
  3 (`/aft-doctor`) as lista como protegidas — mencione isso no resumo para tranquilizá-lo
  ("suas skills próprias continuam intactas"). Nunca rode comando que possa apagá-las.
