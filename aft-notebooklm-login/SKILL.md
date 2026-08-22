---
name: aft-notebooklm-login
model: sonnet
effort: low
description: >
  Use quando for preciso CONECTAR ou RECONECTAR o NotebookLM (o ementário
  que as skills consultam) à conta Google do AFT, ou quando ele parar de
  responder. Acione com "/aft-notebooklm-login", "conectar o notebooklm",
  "logar no notebooklm", "reconectar o ementário", "o notebooklm parou",
  "authentication expired", "a consulta de ementa falhou". Use TAMBÉM para
  conferir quais notebooks a conta do AFT alcança: "quais notebooks eu
  consulto", "confere meus notebooks", "o Claude não achou a NR-XX no
  ementário". Conecta com a menor intervenção possível e sem mandar o AFT ao
  terminal. Só deixa o comando `notebooklm` pronto — não redige autos nem
  consulta ementas.
---

# notebooklm-login — Conectar o NotebookLM (mínima intervenção, sem terminal)

> **Onde ficam as pastas das OS.** O AFT pode ter mudado a pasta de trabalho de
> lugar (HD externo, nuvem, outro disco). Nunca presuma `~/Documents/AFT`:
> resolva **uma vez, no início**, e use o que voltar onde este texto disser
> `<OS_ATIVAS>` (a pasta que contém as OS) ou `<PASTA_AFT>` (a pasta acima dela).
>
> **Nas mensagens ao AFT, escreva o caminho de verdade** — nunca ecoe
> `<OS_ATIVAS>`/`<PASTA_AFT>` na tela: ele precisa saber onde abrir a pasta.
>
> ```bash
> python ~/.claude/skills/_scripts/pasta_aft.py --os-ativas   # -> <OS_ATIVAS>
> python ~/.claude/skills/_scripts/pasta_aft.py --path        # -> <PASTA_AFT>
> ```


## Objetivo

Deixar o comando `notebooklm` autenticado na conta Google do AFT, para as skills
consultarem os ementários. **Regra de ouro:** o Claude executa TUDO; o AFT nunca
abre terminal. No melhor caso o AFT não faz nada; no pior, faz **um único login no
Google** numa janela que o Claude abre.

> Por que existe esta skill: a sessão do NotebookLM **expira de tempos em tempos**.
> Quando uma consulta de ementa começar a falhar com "Authentication expired" ou
> "Run 'notebooklm login'", rode esta skill — não mande o AFT mexer em nada.

Tom: simples e tranquilizador. Explique cada etapa em uma frase.

---

## Passo 0 - O comando `notebooklm` existe?

Confira (você roda):

```bash
notebooklm --help
```

Se **não** existir, instale você mesmo via pipx (deixa o comando no PATH), com os
dois extras que esta skill usa - `browser` (login por janela) e `cookies` (login
silencioso por cookies):

```bash
pipx install --force "notebooklm-py[browser,cookies] @ git+https://github.com/teng-lin/notebooklm-py@main"
# se não houver pipx: python -m pip install --user pipx && python -m pipx ensurepath
# (depois feche e reabra o app para o PATH novo valer, e rode esta skill de novo)
```

> **Por que do git e não do PyPI:** em 16/07/2026 o Google rebatizou o NotebookLM
> como "Gemini Notebook" e o login passou a pousar em `notebook.google.com`. Toda
> a série 0.7.x publicada no PyPI não reconhece esse endereço e o login por janela
> expira ("Login not detected within 5 minutes") **mesmo com o login feito**. A
> correção está no `main` do projeto. Quando o PyPI publicar a 0.8.0 (ou mais
> nova), pode-se voltar ao `pipx install "notebooklm-py[browser,cookies]"`.

Se o comando **já existir**, confira a versão antes de qualquer login:

```bash
notebooklm --version
```

Se aparecer `0.7.x` (ou mais antiga), **atualize primeiro** com o mesmo comando
`pipx install --force ... @main` acima - senão o login por janela do Passo 3 vai
falhar por causa do rebrand, por mais que o AFT faça tudo certo.

Não mande o AFT instalar nada à mão. Se o PATH só atualizar na próxima sessão,
avise que será preciso reabrir o app e siga.

## Passo 1 - Já está conectado? (não refaça login à toa)

```bash
notebooklm auth check --test --json
```

- `status: ok` (ou `token_fetch: true`) -> **já conectado.** Não encerre aqui: pule para
  o **Passo 4** (a conferência notebook por notebook) — é ela que diz se o AFT realmente
  consulta o ementário.
- `token_fetch: false` / `status: error` -> a sessão **expirou**; siga para o Passo 2.
- Sem internet -> rode só `notebooklm auth check --json` (validação local). Se houver
  sessão local, assuma conectado e avise que a confirmação online ficou para quando
  houver rede.

## Passo 1b - Descobrir o navegador do AFT (uma vez)

Leia `notebooklm_browser` em `<PASTA_AFT>/aft-config.md`. Se estiver vazio (ou o
arquivo não existir), pergunte ao AFT, em uma frase: *"Você usa o Chrome ou o Edge com
a sua conta do Gmail?"* e grave a resposta nesse campo (`chrome` ou `edge`) para não
perguntar de novo nas próximas reconexões. Chame a escolha de `<NAV>` nos passos abaixo.

> **Nome do navegador nos comandos:** Chrome é sempre `chrome`. O Edge é `edge` nos
> comandos de cookie (`auth inspect`, `--browser-cookies`) e `msedge` no login por
> janela (`--browser`). Se o AFT não souber, use o Edge (`edge`/`msedge`) - sempre
> existe no Windows.

## Passo 2 - Tentativa silenciosa por cookies (zero cliques)

Antes de abrir qualquer janela, tente reaproveitar o login que o AFT já tem no
navegador escolhido (você roda, é só leitura):

```bash
notebooklm auth inspect --browser <NAV> --json
```

- Se aparecer **uma conta** com cookies válidos:
  ```bash
  notebooklm login --browser-cookies <NAV>
  ```
- Se aparecer **mais de uma conta**, passe a do AFT:
  ```bash
  notebooklm login --browser-cookies <NAV> --account email-do-aft@gmail.com
  ```
- Não achou no navegador do AFT? Tente os outros (`chrome`, `edge`, `brave`, `firefox`)
  antes de desistir do atalho.
- Depois valide com `notebooklm auth check --test`. Deu certo -> encerre (o AFT não
  precisou fazer nada).

> **É normal falhar** em Chrome/Edge atualizados: a mensagem "Could not decrypt ...
> cookies" ou "App-Bound Encryption" significa que o navegador moderno bloqueia a
> leitura dos cookies de fora. Não é problema do AFT nem motivo de alarme - apenas
> siga para o Passo 2b sem expor esse erro técnico ao AFT.

## Passo 2b - Reconexão silenciosa pelo perfil salvo (zero cliques, sem janela)

Se o AFT **já se logou por esta skill alguma vez**, o perfil de navegador salvo em
`~/.notebooklm` costuma continuar com a sessão Google viva mesmo depois que os
cookies do NotebookLM expiram. Antes de abrir qualquer janela, renove por ele
(você roda; nenhuma janela aparece, o navegador roda invisível):

```bash
python ~/.claude/skills/_scripts/notebooklm_reauth.py
```

- **Exit 0** -> renovado. Valide com `notebooklm auth check --test` e encerre - o
  AFT não fez nada.
- **Exit 3** -> o notebooklm-py instalado é antigo demais (série 0.7.x, sem esse
  mecanismo): volte ao Passo 0 e atualize, depois tente de novo.
- **Exit 1** -> a sessão do perfil também morreu (ou nunca houve login): siga para
  o Passo 3.

## Passo 3 - Login por janela (uma única ação do AFT: entrar no Google)

Este é o caminho confiável no Windows. Usa o `<NAV>` **já instalado** (navegador do
sistema), então **não baixa o Chromium próprio e não precisa do Visual C++**.

**Antes de rodar**, avise o AFT em linguagem simples (cite o navegador escolhido):

> "Vou abrir uma janela do Chrome (ou do Edge). Entre na sua conta Google (a mesma do
> Gmail). Assim que você entrar, eu salvo a conexão sozinho - não precisa digitar
> nada nem fechar a janela."

Então rode o comando **com o sandbox desabilitado** e **timeout generoso** (ele
espera o login por até 5 minutos). Use `chrome` ou `msedge` conforme o `<NAV>`:

```bash
notebooklm login --browser chrome      # ou: notebooklm login --browser msedge
```

- **Sandbox desabilitado é obrigatório:** na ferramenta Bash do Claude Code, ative
  `dangerouslyDisableSandbox`. Sem isso a janela não abre e dá `spawn UNKNOWN` - que
  é limitação do sandbox, NÃO do computador do AFT, e NÃO motivo para mandá-lo ao
  terminal.
- Use `timeout` alto (ex.: 320000 ms) ou rode em segundo plano e aguarde; o comando
  salva a sessão automaticamente quando detecta o login e então retorna.
- **A janela usa um perfil isolado:** o AFT faz o login no Google uma vez aqui, mesmo
  que já esteja logado no navegador do dia a dia (esta etapa não reaproveita a sessão
  do navegador comum - isso é o que o Passo 2 tenta, e que o Chrome/Edge novo bloqueia).

**Fallbacks** (sempre com o sandbox desabilitado), se o navegador escolhido não abrir
ou der erro:
1. O **outro** navegador do sistema: troque para `--browser msedge` (Edge) ou
   `--browser chrome` (Chrome).
2. `notebooklm login` (Chromium próprio do Playwright; baixa ~150 MB sozinho na 1ª
   vez - o próprio comando instala o Chromium se faltar). Use só se Chrome e Edge
   falharem.

Se a janela fechar no meio ou der "Browser closed", recomece acrescentando `--fresh`
(ex.: `notebooklm login --browser chrome --fresh`) para limpar a sessão de navegador
cacheada.

> **"Login not detected within 5 minutes" com o login feito?** Isso NÃO é erro do
> AFT: é o defeito do rebrand (Passo 0) numa versão 0.7.x do notebooklm-py. Não
> insista em mais tentativas de login - atualize o pacote (Passo 0) e rode o login
> de novo.

## Passo 4 - Conferir o que o AFT realmente consulta

```bash
notebooklm auth check --test
python "<python_path>" ~/.claude/skills/_scripts/notebooklm_acesso.py
```

O `auth check` diz se o login está de pé. O segundo comando é o que importa para o
trabalho: percorre um por um os notebooks que existem **para a cohort do AFT** e diz
quais a conta dele alcança **de verdade**. Leva alguns segundos e devolve uma linha
JSON:

- `estado: "sessao-expirada"` -> o login não está valendo; volte ao Passo 2/3.
- `estado: "cli-ausente"` -> Passo 0.
- `cohort` -> 1 (notebooks originais) ou 2 (as cópias, para quem se cadastrou depois de
  19/08/2026). Confira com o AFT **se o número destoar** do que o portal mostra a ele:
  cohort errada faz TUDO cair em `indisponiveis`. Para corrigir, mude o campo
  `notebooklm_cohort:` do `aft-config.md` — ver o Passo 4-B.
- `sem_copia` -> notebooks que não foram duplicados e portanto não existem para esta
  cohort. Não é falha de acesso e não há o que clicar: só mencione se o AFT perguntar.
- `disponiveis` -> as skills já consultam esses. Diga o **número**, não a lista inteira.
- `indisponiveis` -> o recado do Passo 5 (com o link pronto de cada um).
- `essenciais_faltando` -> **olhe aqui primeiro**: são os notebooks do dia a dia que
  ainda faltam. Se essa lista estiver vazia, o AFT está pronto para trabalhar mesmo que
  sobrem outros em `indisponiveis`.
- `erros` -> falha de rede ou do CLI, **não** de acesso: ofereça tentar de novo depois.

> **Nunca use `notebooklm list` como prova de que está tudo certo.** Ele mostra só os
> notebooks **vistos recentemente** (o RPC é `ListRecentlyViewedProjects`), então vem
> vazio ou incompleto mesmo com o login perfeito e o acesso já concedido. Foi essa
> checagem enganosa que fez colegas acharem que o toolkit estava quebrado.

## Passo 4-B - A cohort do AFT (só se estiver errada)

Cada notebook do NotebookLM comporta 1.000 leitores. Os originais lotaram em 19/08/2026:
o catálogo foi duplicado, e quem se cadastrou depois enxerga as **cópias** — mesmo
conteúdo, outros endereços. Isso é a "cohort": 1 = originais, 2 = cópias.

O toolkit descobre sozinho e grava o resultado no `aft-config.md`
(`notebooklm_cohort:`), em duas tentativas: primeiro olha os notebooks que já estão na conta
do AFT; se a conta ainda estiver vazia — o caso de quem acabou de se cadastrar e ainda não
abriu nada —, pergunta ao servidor qual dos dois endereços ele alcança. **Não precisa
perguntar nada ao AFT.**

Só há o que fazer aqui se as duas tentativas falharem, e aí a causa é outra: sessão caída
(volte ao Passo 2/3) ou acesso ainda não concedido pelo mantenedor. Se mesmo assim o número
sair errado, confirme com o AFT o que o portal mostra a ele e corrija o campo:

```bash
python ~/.claude/skills/_scripts/notebook_id.py --cohort      # o que o toolkit acha hoje
```

Para forçar, edite `notebooklm_cohort: "2"` no `aft-config.md` — o AFT não precisa abrir o
terminal, você edita o arquivo. Depois repita o Passo 4.

## Passo 5 - Notebooks que precisam do primeiro acesso (o "oi")

O Google só coloca um notebook compartilhado na coleção da conta depois que **a pessoa
o abre uma vez**. Antes disso ele responde "not found" a qualquer consulta - e não há
como o toolkit resolver isso por fora: o `ask` também falha, porque consulta o notebook
antes de chegar ao chat. É **um clique por notebook, uma vez na vida**.

Se `indisponiveis` vier vazio, apenas confirme: *"O Claude consulta todos os N notebooks
do ementário."* Se vier com itens, mande este recado (com os links do JSON):

> ✅ **O Claude já consulta N notebooks** do ementário.
>
> ⚠️ **Faltam M.** O Google só põe um notebook compartilhado na sua coleção depois que
> **você** o abre uma vez - até lá, a consulta a esses temas falha. É rápido: abra o
> notebook, escreva **oi** na caixa de chat e feche. Uma vez só, para sempre.
>
> **Comece por estes - são os do dia a dia:**
> - [Ementário SST](url) · [Ementário Legislação](url) · ...
>
> **Os outros, só se você fiscalizar o tema:**
> - [Título](url) · ...
>
> Se algum pedir acesso, solicite em **https://notebooks-aft.vercel.app** com a sua conta
> Google (o mantenedor libera; nesse caso o "oi" vem depois da liberação).
>
> Quando terminar, me diga **"confere meus notebooks"** que eu confirmo o que entrou.

Regras do recado:
- **Dois blocos, nesta ordem.** Primeiro os que vierem com `essencial` no JSON (o script
  já os devolve na ordem certa: ementários, NR-12, NR-01, NR-03, NR-18, NR-10, NR-04,
  NR-05, NR-24, Informalidade, NR-35, NR-13) - são 13 no máximo e cobrem a maior parte da
  fiscalização. Depois, os demais, deixando claro que são opcionais.
- Link clicável sempre (o campo `url`). Se o segundo bloco passar de 15 itens, resuma-o
  ("os outros N estão no portal") em vez de despejar a lista inteira.
- **Não afirme que falta liberação** de acesso: "not found" é a mesma resposta para
  "tem acesso e nunca abriu" e para "não tem acesso". O recado acima cobre os dois.
- Não ofereça abrir os notebooks você mesmo: quem tem a conta Google no navegador é o
  AFT, e o registro do primeiro acesso só vale feito por ele.

## Passo 6 - Se nada funcionar (ambiente sem tela)

O NotebookLM é **opcional**. Se não houver como abrir janela (ex.: máquina sem
interface gráfica), **não pare o trabalho e não mande o AFT ao terminal**: avise que
seguirá sem o NotebookLM e que as skills vão usar o ementário no Google Drive
(link nas próprias skills) ou pedir o código da ementa diretamente.

---

## Auto-reautenticação nativa (NOTEBOOKLM_REFRESH_CMD)

A sessão do NotebookLM **expira de tempos em tempos**, inclusive no meio de uma ação fiscal.
Em vez de cada skill tratar isso, o toolkit usa o **gancho nativo da CLI**: a variável de
ambiente `NOTEBOOKLM_REFRESH_CMD`. Quando ela aponta para um comando de reconexão, o próprio
`notebooklm ask` **se reautentica sozinho** ao detectar a sessão expirada — sem wrapper, e
valendo para TODAS as skills que usam `notebooklm ask`.

O comando de reconexão é o **script silencioso** do Passo 2b (`notebooklm_reauth.py`):
renova pelo perfil salvo, **sem abrir janela nenhuma** — funciona até em sessão de agente
sem tela, e cabe no timeout de 60 s do gancho. (O valor antigo, `notebooklm login
--browser <NAV>`, abria janela e estourava esse timeout: se encontrar uma máquina ainda
configurada assim, atualize a variável.)

**Deixe a variável configurada** (você roda; é persistente — vale para as próximas sessões).
No Windows, monte o valor com caminhos completos — o `python.exe` do `python_path` do
`aft-config.md` e a pasta do usuário — usando **barras normais** (`/`) e aspas, e o `<NAV>`
do AFT (`chrome` ou `msedge`):

```powershell
[Environment]::SetEnvironmentVariable('NOTEBOOKLM_REFRESH_CMD','"C:/caminho/do/python.exe" "C:/Users/FULANO/.claude/skills/_scripts/notebooklm_reauth.py" <NAV>','User')
[Environment]::GetEnvironmentVariable('NOTEBOOKLM_REFRESH_CMD','User')   # conferir
```

> A variável só passa a valer em **processos novos** — avise o AFT que pode ser preciso
> **reabrir o Claude Code uma vez** para o gancho entrar em vigor nas skills. Esta skill
> continua sendo o caminho **manual** de reconexão quando o gancho não basta (ex.: sem
> rede, primeiro login do navegador, ou a sessão do perfil também expirada).

## Regras

- O Claude executa todos os comandos. O AFT só clica "Permitir" e, no máximo, faz o
  login do Google na janela. Nunca peça ao AFT para abrir terminal ou digitar comando.
- Não peça nem armazene a senha do Google. O login acontece na janela do navegador,
  direto com o Google - o Claude só dispara o comando e detecta o sucesso.
- A consulta de ementa envia ao NotebookLM apenas a **descrição da irregularidade** -
  nunca nome de trabalhador ou da empresa (ver privacidade no CLAUDE.md).
- A sessão fica salva em `~/.notebooklm/profiles/default/storage_state.json` (arquivo
  pessoal do AFT): não exibir, não compartilhar.
