---
name: aft-atualizar
model: sonnet
effort: low
description: >
  Use quando o AFT pedir para atualizar o AFT Toolkit. Acione com "/aft-
  atualizar", "atualize o toolkit", "atualizar o kit", "tem atualização?",
  "verificar atualizações", "buscar novidades do toolkit", "puxar a última
  versão". Mostra a versão disponível no portal e o que mudou desde a
  instalada, instala com o OK do AFT, cuida também do pacote notebooklm-py e
  roda o /aft-doctor ao final. Diferente do /aft-doctor, que só diagnostica.
---

# aft-atualizar — Atualizar o AFT Toolkit (skills + notebooklm-py)
**AFT Toolkit**

## Objetivo

Um único comando para manter as duas peças do toolkit em dia: as **skills**
(o pacote versionado que vem do portal) e o **comando `notebooklm`** (pacote de
terceiro, `teng-lin/notebooklm-py`, que as skills usam para consultar ementas).
No final, confirma que tudo continua funcionando com o `/aft-doctor`.

Tom: tranquilizador e direto. O AFT não precisa entender git nem pip — só saber
o que mudou e se precisa fazer algo (normalmente não).

**Esta skill não aplica nada por conta própria.** Ela pergunta, narra e chama o
programa `_scripts/atualizar_toolkit.py`, onde mora toda a lógica da atualização
— conferência do pacote, varredura de segurança, backup, escrita e remoção. Se
você se pegar copiando arquivo, apagando pasta ou rodando comando de git para
atualizar as skills, parou de seguir esta skill.

## Passo 0 — Retrato das skills pessoais (SEMPRE, antes de qualquer coisa)

O AFT pode ter skills próprias em `~/.claude/skills` que o toolkit não conhece. Elas são
dele: nada nosso pode apagá-las. Tire o retrato antes de tocar na pasta (você roda):

```bash
python3 ~/.claude/skills/_scripts/skills_pessoais.py --backup
```

Guarda uma cópia em `~/.claude/skills-pessoais-backup/` (fora da pasta que a atualização
mexe) e mantém os 5 retratos mais recentes. Ao terminar a atualização, confira:

```bash
python3 ~/.claude/skills/_scripts/skills_pessoais.py --conferir
```

Se acusar sumiço, **avise o AFT e reponha** com `--restaurar` (nunca sobrescreve o que
está lá). Foi assim que em 19/08/2026 um AFT perdeu `cowork-ingest`, `cipa-atas`,
`sisos-sync` e outras: elas não usavam o prefixo `minha-`, eram apenas não rastreadas
pelo git, e não rastreado é o que a limpeza remove primeiro. O `.gitignore` do repo passou
a ignorar tudo que não é do toolkit — mas o retrato é a rede que vale mesmo quando a
instalação não é um clone git.

Se o comando falhar porque o programa não está na pasta, **não insista**: siga para o
Passo 1, que é onde essa instalação se explica — e, quando houver instalação de fato, o
programa do Passo 1b tira e confere o retrato sozinho, antes de escrever qualquer coisa.

## Passo 1 — Ver o que há de novo (sem baixar nada ainda)

A atualização inteira é feita por **um programa só**, o `atualizar_toolkit.py`: é ele que
fala com o portal, confere o pacote, guarda a instalação atual e escreve a nova. Você não
executa nenhuma dessas etapas à mão — a sua parte é perguntar, narrar e decidir junto com
o AFT.

Comece perguntando ao portal o que existe de novo. Nesta etapa **nada é baixado e nada é
instalado** (você roda):

```bash
python3 ~/.claude/skills/_scripts/atualizar_toolkit.py --verificar
```

No Windows, troque `python3` pelo caminho completo do `python_path` do `aft-config.md`. A
saída é um JSON: leia `estado`, `versao`, `versao_instalada`, `ha_novidade`, `novidades` e
`detalhe`.

**Se o comando não funcionar**, esta é uma instalação **anterior à mudança de
distribuição**. São dois sintomas, e os dois querem dizer a mesma coisa: o programa não
está lá (`No such file or directory`, `can't open file`) ou o programa que está lá é
velho e não conhece o `--verificar` (responde com um `usage:` ou com `unrecognized
arguments`). Em qualquer dos dois, o toolkit deixou de ser atualizado pelo GitHub. Não
tente `git pull`, `git fetch` nem nenhum outro comando de git — o caminho antigo não traz
mais versão nova. Explique ao AFT sem jargão, deixando claro que não foi erro dele:

> O AFT Toolkit mudou de casa: as atualizações não vêm mais do GitHub, e sim do portal
> onde o senhor já tem cadastro. É uma vez só — peça o acesso em
> <https://notebooks-aft.vercel.app/aft-toolkit> com a sua conta Google e me passe o
> código que chegar por e-mail, que eu cuido do resto. Enquanto isso, tudo o que já está
> instalado continua funcionando normalmente.

E **pare por aqui**: sem o programa da atualização nesta máquina não há o que instalar, e
é a página do portal que traz o roteiro. Não copie, não baixe e não improvise instalação
por fora dela. Pule os Passos 2 e 3 e feche pelo Passo 4, com essa orientação e nada mais
— o que está instalado continua funcionando.

Com o JSON na mão:

- **`ok: true` com `estado: "sem_novidade"`** → é o caso comum, e ele é barato: nenhum
  download aconteceu. Diga a frase do `detalhe` em uma linha, sem alarde (ela já traz a
  versão), e siga para o Passo 2.
- **`ok: true` com `ha_novidade: true`** → apresente ao AFT, **antes de baixar qualquer
  coisa**: a versão disponível (`versao`), a que ele tem (`versao_instalada`) e o
  changelog do campo `novidades` — ele já vem escrito para o AFT, em português, e cobre
  só o período dele. Apresente o conteúdo (no máximo agrupando ou encurtando), nunca
  reescrevendo nem acrescentando o que não está lá. Depois **pergunte se ele quer
  instalar agora**. Só com o sim explícito vá ao Passo 1b; um "depois eu vejo" encerra a
  skill aqui, sem insistir.
- **`ok: false`** → o campo `detalhe` já é a explicação pronta para o AFT, em português e
  com o próximo passo (falta o código de acesso, código recusado, e-mail sem liberação,
  portal fora do ar). Repasse-a praticamente como está — não traduza para jargão nem
  invente causa. Se o `estado` for `sem_token` ou `token_invalido`, vá ao Passo 1a; nos
  demais casos nada foi alterado na máquina, então encerre com a orientação do `detalhe`.

### Passo 1a — Guardar o código de acesso (só quando faltar)

O código chega ao AFT uma única vez, no e-mail de liberação do portal, e depois nunca mais
incomoda. Quando ele te passar o código:

- **Nunca ponha o valor dentro do comando** (o que se digita numa linha de comando fica em
  histórico e em registro) e **nunca repita o código no chat**. Grave-o num arquivo
  temporário com a tool Write e mande pelo cano — o programa lê pela entrada padrão:

  ```bash
  python3 ~/.claude/skills/_scripts/atualizar_toolkit.py --gravar-token < "<arquivo temporário>"
  ```

- Apague o arquivo temporário logo em seguida.

O código fica guardado na pasta de trabalho do AFT, **fora** da pasta de skills — assim a
própria atualização não o apaga. Feito isso, repita o Passo 1.

### Passo 1b — Instalar (só depois do sim do AFT)

```bash
python3 ~/.claude/skills/_scripts/atualizar_toolkit.py --aplicar
```

O programa faz sozinho, nesta ordem: confere a soma de verificação do pacote, varre o
conteúdo que está chegando à procura de sinal de adulteração, tira o retrato das skills
pessoais, guarda a instalação atual numa pasta de backup ao lado, escreve a versão nova e
confere que nenhuma skill pessoal sumiu no caminho. **Nada é escrito antes de as
conferências passarem.**

Leia o JSON do resultado:

- **`ok: true`** → instalado. Guarde para o resumo do Passo 4: a versão nova
  (`pacote.versao`), a anterior (`versao_anterior`), a frase do `detalhe` (quantos
  arquivos entraram, quantas skills saíram, quantas pastas do AFT foram preservadas) e o
  caminho do `backup`. As listas `plano.novos` e `plano.alterados` dizem quais arquivos
  mudaram — os Passos 2c e 2h precisam delas.
- **`erro: "conteudo_suspeito"`** → **nada foi instalado**, e assim fica até o AFT
  decidir. Mostre a ele o `varredura.relatorio` em linguagem simples: a atualização traz
  algo fora do padrão. Só repita o comando acrescentando `--confirmado` se ele confirmar
  que a atualização é legítima. Na dúvida, não instale: toolkit antigo funcionando é
  melhor que toolkit novo adulterado.

  > **Atualização grande não é, por si, sinal de adulteração.** Uma renomeação em massa
  > (como a que prefixou `aft-` em todas as skills, em 26/07/2026) mexe em dezenas de
  > arquivos de uma vez. O que importa é o `varredura.relatorio`: se ele não apontou
  > sinal suspeito, o tamanho da lista não quer dizer nada. Explique isso ao AFT em vez
  > de alarmá-lo com números.
- **Qualquer outro `ok: false`** → o `detalhe` traz a explicação pronta e o que fazer; se
  ele mencionar a pasta de backup, repasse o caminho ao AFT. Não tente consertar por fora
  do programa nem repetir o comando às cegas.

## Passo 2 — Atualizar o `notebooklm` (notebooklm-py)

Confira a versão instalada e a versão mais recente publicada (você roda):

```bash
notebooklm --version
```

```bash
curl -s https://pypi.org/pypi/notebooklm-py/json | python3 -c "import json,sys; print(json.load(sys.stdin)['info']['version'])"
```

- Se o `notebooklm --version` falhar ("comando não encontrado"), o pacote não está
  instalado — não é erro desta skill; apenas informe e siga (o `/aft-notebooklm-login`
  ou o `/aft-setup` cuidam da instalação na próxima vez que forem usados).

**Enquanto o PyPI publicar versão anterior à 0.8.0** (rebrand "Gemini Notebook" de
16/07/2026: toda a série 0.7.x tem o login por janela quebrado — ver Passo 0 da
`/aft-notebooklm-login`), o alvo da atualização é o **`main` do git**, não o PyPI:

- Se a versão instalada for `0.7.x` ou anterior, atualize automaticamente, sem
  perguntar:
  ```bash
  pipx install --force "notebooklm-py[browser,cookies] @ git+https://github.com/teng-lin/notebooklm-py@main"
  ```
- Se a versão instalada já vier do git (aparece com o hash, ex.: `0.8.0rc1 (7d0aa42c)`),
  rode o mesmo comando acima — ele é idempotente e só avança para o `main` mais novo.

**Quando o PyPI passar a publicar 0.8.0 ou mais nova**, volte ao fluxo normal:

- Se as duas versões forem **iguais**, informe que já está atualizado.
- Senão, atualize para a versão do PyPI (o `--force` também serve para sair da
  instalação via git e voltar à publicada):
  ```bash
  pipx install --force "notebooklm-py[browser,cookies]"
  ```
  Se o pacote não foi instalado via pipx (comando acima falha ou não muda nada),
  use o equivalente em pip:
  ```bash
  python -m pip install --user --upgrade "notebooklm-py[browser,cookies]"
  ```

Depois confirme com `notebooklm --version` que a versão nova ficou ativa.

## Passo 2b — Oferecer a rotina diária do painel (só na primeira vez)

O toolkit ganhou a opção de o `/aft-painel` se atualizar sozinho toda manhã (agendamento do
próprio sistema operacional — launchd/Agendador de Tarefas, zero tokens, sem abrir o
Claude Code). AFTs que instalaram o toolkit antes dessa novidade nunca foram perguntados.
Confira se já foi oferecida:

```bash
grep -q "rotina_painel" "$(python ~/.claude/skills/_scripts/pasta_aft.py --path)/aft-config.md" && echo "ja_perguntado" || echo "nunca_perguntado"
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
grep -q 'servidor_painel: *"ligado"' "$(python ~/.claude/skills/_scripts/pasta_aft.py --path)/aft-config.md" && echo "ja_ligado" || echo "instalar"
```

- **`ja_ligado`** → se o Passo 1b **instalou uma versão nova**, o servidor precisa
  carregar o código novo — mas **reiniciar o processo apaga
  o token do DET** da memória e obriga o AFT a ir ao Chrome clicar em Sincronizar de
  novo. Então o caminho depende do que a atualização mexeu (procure o arquivo nas listas
  `plano.novos` e `plano.alterados` do JSON do Passo 1b):

  - `_scripts/servir_painel.py` **NÃO está** na lista → recarga a quente, que troca o
    código dos módulos do DET **sem derrubar o processo e sem perder o token**:

    ```bash
    python ~/.claude/skills/_scripts/det_token.py --recarregar
    ```

    Respondeu `"ok": true` → pronto, siga para o Passo 2d (o `gerar_painel.py` nem
    precisa disso: é subprocesso e já pega a versão nova sozinho). O painel não
    respondeu → caia no reinício completo abaixo.
  - `_scripts/servir_painel.py` **está** na lista (ou a recarga falhou) → reinício
    completo:

    ```bash
    python ~/.claude/skills/_scripts/instalar_servidor_painel.py reiniciar
    ```

    (no Windows, com o `python_path` do `aft-config.md`). O reinício apagou o token:
    **avise no resumo** (Passo 4), em uma linha, que antes do próximo download ou sync
    do DET será preciso abrir a aba do DET e clicar em **Sincronizar** uma vez.

  Sem instalação no Passo 1b, nada a fazer. Siga para o Passo 2d.
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
`/aft-setup` — skill `/aft-agenda-det`). Confira:

```bash
grep -q "agenda_det" "$(python ~/.claude/skills/_scripts/pasta_aft.py --path)/aft-config.md" && echo "ja_perguntado" || echo "nunca_perguntado"
```

- **`ja_perguntado`** → não pergunte de novo; siga para o Passo 2e.
- **`nunca_perguntado`** → ofereça **uma única vez**, em uma frase: *"Novidade: os
  prazos das notificações DET podem aparecer direto no seu Google Calendar — um evento
  por notificação, atualizado quando o prazo muda e marcado com ✓ quando você responde.
  Quer ativar?"*
  - **Não** → grave `agenda_det: ""` no `aft-config.md` e siga (lembre que o painel tem
    o botão "agendar no Google Calendar", sem login).
  - **Sim** → siga exatamente o Passo 7d do `/aft-setup` (conector Google Calendar +
    primeira sincronização pela `/aft-agenda-det`). Lá dentro há uma **segunda pergunta**,
    que não pode ser pulada: sob demanda (`agenda_det: "manual"`) ou todo dia
    (`agenda_det: "diario"`, que cria a tarefa agendada pelo Passo 4 da
    `/aft-agenda-det`). Nunca instale a rotina diária sem o AFT pedir.

## Passo 2e — Re-sincronizar o perfil do auditor (CLAUDE.md)

O perfil `~/.claude/CLAUDE.md` (instalado pelo `/aft-setup`) é uma **cópia** do template
`config/CLAUDE-aft.md` e **não** é atualizado pela instalação do pacote. O toolkit cerca a parte
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
- **`DIVERGENTE v<N>`** → mesma versão nos dois lados, mas o conteúdo do bloco difere (o
  template mudou sem trocar de número, ou alguém editou dentro dos marcadores do arquivo
  instalado). Trate como o caso acima: rode o mesmo `--aplicar`, **sem perguntar** (o
  script faz backup e troca só o bloco marcado). No resumo do Passo 4: *"Seu perfil de
  auditor foi ressincronizado com o do toolkit (v\<N\>) — só o bloco do toolkit; o que
  você tinha escrito à parte ficou intacto."*
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

## Passo 2f — Vigia de sessões (garantir instalado, sem perguntar)

> **No Codex, pule os Passos 2f, 2f-bis e 2g** (vigia de sessões, gancho do diário e
> agentes só existem no app do Claude). No lugar deles, confira em uma linha se os dois
> atalhos continuam de pé — `~/.agents/skills` → `~/.claude/skills` e `~/.codex/AGENTS.md`
> → `~/.claude/CLAUDE.md` — e recrie o que faltar (ver Passo 0 do `/aft-setup`).

As sessões por empresa (grupo "OS ATIVAS" do menu lateral) são automáticas via **vigia de
sessões** — parte padrão da instalação. Confira e garanta:

```bash
python ~/.claude/skills/_scripts/instalar_vigia_sessoes.py status
```

- **"não instalado"** → instale **sem perguntar** (mesmo espírito do Passo 2c):
  ```bash
  python ~/.claude/skills/_scripts/instalar_vigia_sessoes.py instalar <python_path>
  ```
  e mencione no resumo do Passo 4: *"Sessões por empresa agora são automáticas — cada
  auditoria em OS ATIVAS ganha a própria sessão no grupo 'OS ATIVAS' na próxima vez que
  você fechar e reabrir o app."*
- **Instalado** → nada a fazer. Opcional: rode `sessoes_os.py --status` e, se houver
  pendências (`criar` > 0), informe que serão aplicadas sozinhas no próximo reinício do
  app — sem perguntar nada.
- **Falhou** → registre no resumo do Passo 4; não é bloqueante.

## Passo 2f-bis — Gancho do diário de atividades (garantir instalado, sem perguntar)

O **diário de atividades** (dias trabalhados por auditoria, letras A-F — ver
`/aft-diario`) tem uma rede de segurança: um gancho do Claude Code que anota o dia
trabalhado sempre que um `memory.md` de OS ATIVAS é editado. É parte padrão da
instalação. Confira e garanta:

```bash
python ~/.claude/skills/_scripts/instalar_hook_diario.py status
```

- **"NÃO instalado"** → instale **sem perguntar**:
  ```bash
  python ~/.claude/skills/_scripts/instalar_hook_diario.py instalar <python_path>
  ```
  e mencione no resumo do Passo 4: *"O diário de atividades agora anota sozinho os dias
  trabalhados em cada auditoria — vale a partir da próxima vez que você abrir o app."*
- **Instalado** → nada a fazer.
- **Falhou** → registre no resumo do Passo 4; não é bloqueante (o diário continua
  funcionando pelos registros das skills, só perde a rede de segurança).

## Passo 2g — Sincronizar os agentes do toolkit

Os **agentes** (`agents/*.md` do repositório — hoje o revisor de autos, a varredura do
Sistema Auditor e o extrator de PGR) precisam de uma cópia em `~/.claude/agents/`, e a instalação do pacote sozinha
não a atualiza. Rode **sem perguntar** (idempotente, só copia o que mudou):

```bash
python ~/.claude/skills/_scripts/instalar_agentes.py
```

- `instalados` ou `atualizados` não vazio → mencione no resumo do Passo 4 que os
  agentes novos/atualizados valem a partir do **próximo reinício do app**.
- Tudo em `em_dia` → nada a fazer.
- Falhou → **não é bloqueante** (as skills degradam para o modo inline); registre no
  resumo.

## Passo 2h — Notebooks novos no ementário (só se o mapa mudou)

Quando o toolkit ganha um notebook novo (uma NR que passou a ter ementário próprio), ele
entra no mapa `config/notebooks.json` — mas o Google **não** o coloca na coleção do AFT
sozinho: cada pessoa precisa abri-lo uma vez. Confira se a instalação do Passo 1b mexeu
no mapa: procure `config/notebooks.json` nas listas `plano.novos` e `plano.alterados` do
JSON.

- **Não está em nenhuma das duas** (ou não houve instalação) → pule este passo (não gaste
  tempo sondando o que já funcionava).
- **Está** → rode a conferência de acesso:
  ```bash
  python "<python_path>" ~/.claude/skills/_scripts/notebooklm_acesso.py
  ```
  Se vier algo em `indisponiveis`, dê o recado do **Passo 5 da `/aft-notebooklm-login`**
  (link clicável de cada um + "abra e escreva oi na caixa de chat"), mencionando que são
  os notebooks novos desta atualização. Se `estado` for `cli-ausente` ou
  `sessao-expirada`, apenas registre no resumo e sugira `/aft-notebooklm-login` — não é
  bloqueante.

## Passo 2i — Planilhas de CAT em dia (só se a sincronização estiver configurada)

Quem conectou o espelho de CATs no `/aft-setup` (Passo 2a, caminho automático) tem a
pasta `CATs` mantida em dia por aqui. Rode **sem perguntar** (incremental — só baixa
planilha nova ou atualizada):

```bash
python "<python_path>" ~/.claude/skills/_scripts/sincronizar_cats.py --sync
```

- **`ok` com `novos`/`atualizados` não vazios** → mencione no resumo do Passo 4, em
  linguagem de gente: *"chegou a planilha de CAT de 2027 do seu estado"*.
- **`ok` sem novidade** → nada a dizer.
- **`rclone_ausente` ou `remote_nao_configurado`** → o AFT usa o caminho manual;
  **pule em silêncio** (não ofereça nada — o Passo 2a do `/aft-setup` é o lugar de
  configurar isso).
- **`sem_acesso`** → uma linha no resumo, com a solução: ativar em
  <https://notebooks-aft.vercel.app/aft-toolkit#cats> (digitar o Gmail do cadastro e
  clicar em "Ativar acesso"); a base local continua valendo enquanto isso.
- Qualquer erro → registre no resumo; **não é bloqueante**.

## Passo 2j — Oferecer o aviso semanal de pendências (só na primeira vez)

O toolkit ganhou um aviso semanal: toda segunda-feira de manhã, uma notificação nativa
do computador com o total de pendências em aberto das auditorias (a lista completa fica
na seção "Pendências por auditoria" do painel). Confira se já foi oferecido:

```bash
grep -q "aviso_pendencias" "$(python ~/.claude/skills/_scripts/pasta_aft.py --path)/aft-config.md" && echo "ja_perguntado" || echo "nunca_perguntado"
```

- **`ja_perguntado`** → não pergunte de novo; siga para o Passo 3.
- **`nunca_perguntado`** → ofereça **uma única vez**, em uma frase: *"Novidade: posso
  deixar seu computador te avisar toda segunda de manhã quantas pendências estão em
  aberto nas suas auditorias — notificação do próprio sistema, sem gastar nada. Quer?"*
  - **Não** → grave `aviso_pendencias: ""` no front-matter do `aft-config.md` e siga.
  - **Sim** → siga o Passo 7f do `/aft-setup` (script `instalar_rotina_pendencias.py`,
    mesmo `python_path`/pasta de OS ATIVAS) e grave `aviso_pendencias: "08:00"` (ou o
    horário escolhido) no `aft-config.md`.

## Passo 2k — Lotação no cabeçalho dos documentos (pergunta única)

Todo `.docx` do toolkit passou a sair com o cabeçalho institucional completo — brasão,
"Ministério do Trabalho e Emprego", "Secretaria de Inspeção do Trabalho", **a lotação do
AFT** e os logos SIT/AFT. Quem instalou o toolkit antes disso não tem a linha da lotação
no `aft-config.md`. Confira (você roda):

```bash
python ~/.claude/skills/_scripts/cabecalho.py --status
```

O JSON traz `lotacao` e `origem`:

- **`origem: "config"`** → o AFT já confirmou a redação; nada a perguntar.
- **`origem: "uorg"`** → a linha foi deduzida da tabela oficial de UORGs pelo código que
  ele já tinha. **Pergunte uma única vez**, mostrando a linha exatamente como sairá
  impressa: *"Novidade: seus documentos agora levam a sua unidade no cabeçalho. Ficaria
  assim: '\<lotacao\>'. Confere, ou quer corrigir o texto?"* A tabela de UORGs tem nomes
  antigos (muitas unidades ainda constam como "do Trabalho", sem "e Emprego") e grafias
  com erro, por isso a conferência importa. Grave **o que o AFT responder** no campo
  `lotacao:` do `aft-config.md` — nunca corrija o nome da unidade por conta própria.
- **`origem: "ausente"`** → não há nem código de UORG. Pergunte a lotação por extenso, do
  jeito que deve aparecer no cabeçalho, e grave em `lotacao:`.

Se o AFT preferir **não** ter a unidade no cabeçalho, grave `lotacao: ""` (campo vazio):
os documentos saem só com as duas linhas fixas e ninguém pergunta de novo.

Depois de gravar (ou se já estava em dia), prepare as cópias personalizadas dos templates:

```bash
python ~/.claude/skills/_scripts/cabecalho.py --preparar
```

Mencione no resumo do Passo 4, em uma linha: *"Seus documentos agora saem com o cabeçalho
da sua unidade; deixei também um 'Template com cabeçalho.docx' na sua pasta AFT."* Se o
JSON trouxer `template_avulso: "preservado"`, é porque já existe um arquivo com esse nome
**com texto escrito dentro** — o script não sobrescreve documento do AFT; diga isso a ele
e ofereça gravar o modelo novo com outro nome. Falha aqui **não é bloqueante**: os
documentos continuam saindo, só sem a linha da lotação.

## Passo 3 — Confirmar que nada quebrou (`/aft-doctor`)

Sempre rode ao final, mesmo se nada tiver sido instalado nos Passos 1/2 (serve
também para confirmar que o ambiente já estava certo):

```bash
python ~/.claude/skills/_scripts/aft_doctor.py
```

Traduza o resultado seguindo as regras do `/aft-doctor` (🟢/🟡/🔴, erros antes de
avisos). Se aparecer algum erro novo causado pela atualização, explique e oriente
a solução — não deixe o AFT com a sensação de que "atualizar" pode ter quebrado
algo sem explicação.

Se o programa do diagnóstico não estiver na pasta, não há o que diagnosticar: diga isso
em uma linha e siga para o Passo 4.

## Passo 4 — Resumo final ao AFT

Uma mensagem só, juntando os passos. As novidades são as do campo `novidades` mostrado no
Passo 1 — já escritas para o AFT; apresente o conteúdo delas, sem reescrever. Diga sempre
a versão que ficou instalada: é ela que o AFT vai citar quando pedir ajuda. Exemplo:

```
🔄 Atualização do AFT Toolkit

✅ Skills atualizadas — versão 2026.08.31 (a anterior era 2026.08.12).
   A versão de antes ficou guardada em ~/.claude/skills-backup-2026.08.12,
   caso algo saia errado. Novidades para você:

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
diagnóstico — não é preciso alarde: o comando barato que não achou novidade não merece
relatório. Se algum passo falhou sem ser bloqueante (agentes, CATs, cabeçalho), registre
em uma linha cada um, ao final, com o que fazer.

## Regras

- **Nada é instalado sem o sim do AFT.** O changelog vem antes do download, e o download
  antes de qualquer escrita. Perguntar duas vezes é melhor do que instalar sem perguntar.
- **A atualização das skills não usa git.** Nunca rode `git pull`, `git fetch`,
  `git reset --hard`, `git checkout -- .` nem qualquer coisa parecida na pasta de skills:
  o toolkit vem do portal, em pacote versionado, e quem o aplica é o
  `_scripts/atualizar_toolkit.py`.
- **O código de acesso nunca aparece.** Não o escreva em comando, não o repita no chat,
  não o guarde no `aft-config.md` e não o inclua em ticket de erro. Se precisar saber se
  ele existe, pergunte ao programa (`--estado-token`), que responde sim ou não.
- A atualização do `notebooklm-py` é automática (sem pedir confirmação a cada
  vez), mas sempre **reporte** a troca de versão — o AFT precisa saber o que
  mudou, mesmo sem precisar agir.
- Esta skill **instala/atualiza**; o `/aft-doctor` (chamado no Passo 3) **só
  diagnostica**. Não pule o Passo 3: é o que garante que a atualização não
  deixou nada quebrado para o AFT descobrir sozinho em campo.
- **Skills próprias do AFT são preservadas** — as `minha-*` e também as sem prefixo
  nenhum. O programa só remove pasta que o toolkit instalou e deixou de instalar; o que
  nunca foi dele não é tocado, e no fim ele confere o retrato para garantir que nenhuma
  sumiu. Se o AFT tiver alguma, mencione no resumo para tranquilizá-lo ("suas skills
  próprias continuam intactas"). Nunca rode comando que possa apagá-las.
