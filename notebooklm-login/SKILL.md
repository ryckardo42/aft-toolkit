---
name: notebooklm-login
description: >
  Use SEMPRE que for preciso CONECTAR ou RECONECTAR o NotebookLM (o ementário que
  as skills consultam para achar o código da ementa) à conta Google do AFT, ou
  quando o NotebookLM parar de responder. Acione com "/notebooklm-login",
  "conectar o notebooklm", "ativar o notebooklm", "logar no notebooklm",
  "reconectar o ementário", "o notebooklm parou", "deu erro no notebooklm",
  "authentication expired", "notebooklm pede para logar de novo", "a consulta de
  ementa falhou", "notebooklm list deu erro". A skill conecta com a MENOR
  intervenção possível e SEM nunca mandar o AFT para o terminal: o Claude tenta
  primeiro os cookies do navegador (zero cliques) e, se preciso, abre uma janela
  do navegador do sistema (Edge/Chrome) para um único login no Google, salvando a
  sessão sozinho. NÃO baixa o Chromium próprio nem exige Visual C++ quando usa o
  navegador do sistema. Também detecta sessão já ativa ou expirada. NÃO redige
  autos nem consulta ementas: só deixa o comando `notebooklm` pronto para as
  outras skills usarem (/inspecao-inicial, /NR12, /NR18, /tn-nco, /gera-ai...).
---

# notebooklm-login — Conectar o NotebookLM (mínima intervenção, sem terminal)

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
pipx install "notebooklm-py[browser,cookies]"
# se não houver pipx: python -m pip install --user pipx && python -m pipx ensurepath
# (depois feche e reabra o app para o PATH novo valer, e rode esta skill de novo)
```

Não mande o AFT instalar nada à mão. Se o PATH só atualizar na próxima sessão,
avise que será preciso reabrir o app e siga.

## Passo 1 - Já está conectado? (não refaça login à toa)

```bash
notebooklm auth check --test --json
```

- `status: ok` (ou `token_fetch: true`) -> **já conectado.** Confirme com
  `notebooklm --quiet list` e encerre dizendo que o NotebookLM está ativo.
- `token_fetch: false` / `status: error` -> a sessão **expirou**; siga para o Passo 2.
- Sem internet -> rode só `notebooklm auth check --json` (validação local). Se houver
  sessão local, assuma conectado e avise que a confirmação online ficou para quando
  houver rede.

## Passo 1b - Descobrir o navegador do AFT (uma vez)

Leia `notebooklm_browser` em `~/Documents/AFT/aft-config.md`. Se estiver vazio (ou o
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
> siga para o Passo 3 sem expor esse erro técnico ao AFT.

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

## Passo 4 - Conferir

```bash
notebooklm auth check --test
notebooklm --quiet list
```

Se a **lista de notebooks aparecer**, está pronto - avise o AFT que o NotebookLM
está conectado e as skills já encontram a ementa sozinhas.

## Passo 5 - Lista vazia ou "sem acesso"?

Se autenticou mas `list` vem vazio ou diz que não há acesso, falta **liberação dos
notebooks compartilhados** (não é problema de login):

1. Peça ao AFT para entrar em **https://notebooks-aft.vercel.app** com a conta Google
   e solicitar acesso.
2. O mantenedor (Ricardo, SRTE/GO) libera os notebooks de ementas e NRs.
3. Depois da liberação, rode `notebooklm --quiet list` de novo para confirmar.

## Passo 6 - Se nada funcionar (ambiente sem tela)

O NotebookLM é **opcional**. Se não houver como abrir janela (ex.: máquina sem
interface gráfica), **não pare o trabalho e não mande o AFT ao terminal**: avise que
seguirá sem o NotebookLM e que as skills vão usar o ementário no Google Drive
(link nas próprias skills) ou pedir o código da ementa diretamente.

---

## Regras

- O Claude executa todos os comandos. O AFT só clica "Permitir" e, no máximo, faz o
  login do Google na janela. Nunca peça ao AFT para abrir terminal ou digitar comando.
- Não peça nem armazene a senha do Google. O login acontece na janela do navegador,
  direto com o Google - o Claude só dispara o comando e detecta o sucesso.
- A consulta de ementa envia ao NotebookLM apenas a **descrição da irregularidade** -
  nunca nome de trabalhador ou da empresa (ver privacidade no CLAUDE.md).
- A sessão fica salva em `~/.notebooklm/profiles/default/storage_state.json` (arquivo
  pessoal do AFT): não exibir, não compartilhar.
