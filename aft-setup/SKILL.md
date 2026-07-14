---
name: aft-setup
model: sonnet
description: >
  Use SEMPRE que o Auditor-Fiscal do Trabalho (AFT) acabou de instalar o AFT Toolkit
  e precisa configurá-lo pela primeira vez, ou quando quiser revisar/alterar a
  configuração. Acione com "/aft-setup", "configurar o toolkit", "primeira
  configuração", "configuração inicial", "setup", "mudar minha CIF", "mudar minha
  UORG". A skill verifica os pré-requisitos (Python, pip), cria a estrutura de
  pastas de trabalho em ~/Documents/AFT/, coleta os dados do auditor (nome, CIF,
  UORG, município) uma única vez, grava tudo em aft-config.md, instala as
  bibliotecas Python necessárias e orienta a configuração do NotebookLM. Todas as
  outras skills do toolkit leem essa configuração — sem ela, pedem para rodar
  /aft-setup primeiro.
---

# aft-setup — Configuração inicial do AFT Toolkit

## Objetivo

Deixar o computador do AFT pronto para usar todas as skills do toolkit. Roda uma única
vez (ou quando o auditor quiser mudar algo). Ao final, existe:

- A pasta de trabalho `~/Documents/AFT/` com `OS ATIVAS/` e `OS ARQUIVADAS/`.
- O arquivo `~/Documents/AFT/aft-config.md` com os dados do auditor e da unidade.
- As bibliotecas Python instaladas (`pillow`, `pikepdf`).
- (Opcional, recomendado) O CLI do NotebookLM autenticado.

Tom: acolhedor e paciente — o público é um colega que pode estar usando o Claude Code
pela primeira vez. Explique o que cada passo faz em uma frase, sem jargão.

---

## Passo 1 — Verificar e completar pré-requisitos (você instala, não o AFT)

Rode e interprete:

```bash
python --version || python3 --version
git --version
```

Se algo faltar, **não mande o AFT instalar manualmente — instale você mesmo** via
winget (o AFT só precisa aprovar os comandos):

- **Python ausente**:
  ```bash
  winget install --id Python.Python.3.12 -e --accept-source-agreements --accept-package-agreements
  ```
  Depois confirme com `python --version`. Se o comando ainda não for encontrado, o
  PATH novo só vale em sessão nova: avise que no fim do setup será preciso fechar e
  reabrir o Claude Code, e use o caminho completo do executável (descubra com
  `where python` / `ls "$LOCALAPPDATA/Programs/Python"`) até lá.
- **Git ausente** (improvável: no Windows o app desktop só abre sessão local com o Git instalado, e o toolkit veio via `git clone`. Pode ocorrer no macOS/CLI):
  ```bash
  winget install --id Git.Git -e --accept-source-agreements --accept-package-agreements
  ```
  Avise que, com o Git instalado, o Claude Code passa a usar o Git Bash como
  terminal a partir da próxima reinicialização do aplicativo.
- **winget indisponível ou rede bloqueando** → plano B manual: Python em
  https://www.python.org/downloads/ (marcando **"Add Python to PATH"**) e Git em
  https://git-scm.com. Depois, fechar e reabrir o Claude Code e rodar `/aft-setup`
  de novo.

> Nas demais skills os comandos usam `python`. No Windows isso já funciona; no macOS,
> se só existir `python3`, use `python3`.

## Passo 2 — Criar a estrutura de pastas

```bash
mkdir -p ~/Documents/AFT/"OS ATIVAS" ~/Documents/AFT/"OS ARQUIVADAS"
```

Explique ao AFT, com destaque (essa é a informação mais importante do setup — o AFT
vai voltar a ela toda vez que quiser achar os arquivos de uma fiscalização):

> 📁 **`Documentos\AFT\OS ATIVAS` é onde moram todas as suas empresas fiscalizadas.**
> Cada empresa ganha uma subpasta ali dentro (padrão: `NOME DA EMPRESA <CNPJ 14
> dígitos>`), com todos os arquivos daquela fiscalização: relato de campo, autos,
> anexos e a ficha `memory.md`. Quando a fiscalização termina, a pasta inteira vai
> para `OS ARQUIVADAS` (mesmo nível, ao lado de `OS ATIVAS`). Tudo fica **no seu
> computador** — nada é enviado para fora.

## Passo 3 — Coletar os dados do auditor (uma única vez)

Pergunte, em uma única mensagem, apenas **três coisas** (o resto você descobre na
tabela de UORGs). Explique que esses dados entram automaticamente nos arquivos TXT
importados pelo Sistema Auditor, para nunca mais serem digitados:

| Campo | Exemplo |
|---|---|
| Nome completo | JOÃO DA SILVA |
| CIF (6 dígitos) | 123456 |
| Lotação (cidade ou nome da unidade) | "Anápolis" · "SRT Goiás" · "Gerência de Uberlândia" |

### Resolver a UORG pela tabela (o AFT não precisa saber o código)

O toolkit traz a tabela oficial de UORGs em
`~/.claude/skills/config/uorgs.csv` (UTF-8, separado por `;`, colunas:
`CDUORG;NOME;UF;MUNICIPIO;ENDERECO;BAIRRO;CEP`; ~1.000 unidades; CDUORG tem
sempre 9 dígitos).

1. **Busque** a lotação informada nas colunas `MUNICIPIO` e `NOME`,
   case-insensitive. Tente com e sem acentos (ex.: `ANÁPOLIS` e `ANAPOLIS`) —
   o arquivo está acentuado. Se a cidade for comum a vários estados ou vier
   ambígua, pergunte a UF antes.
2. **Apresente os candidatos numerados** (código + nome + município/UF) e peça
   para o AFT escolher. É normal haver mais de uma unidade na mesma cidade
   (Superintendência, Gerência, Agência) — quem sabe qual é a sua lotação é o AFT.
   > Dica de qualidade: a tabela tem entradas antigas/desativadas (endereço `.`,
   > CEP `99999999`, ou `*** A DESATIVAR` no nome). Liste-as por completude, mas
   > destaque as entradas com endereço real como prováveis.
3. **Preencha automaticamente** a partir da linha escolhida:
   - `uorg` = `CDUORG` (9 dígitos)
   - `local_uorg` = `BAIRRO` (se vazio ou lixo tipo `.`, pergunte ao AFT)
   - `cep_uorg` = `CEP` (se `99999999`, pergunte ao AFT)
   - `municipio` = `MUNICIPIO` · `uf` = `UF`
4. **Eco de confirmação** antes de gravar: mostre código, nome da unidade,
   bairro/local, CEP, município/UF e pergunte se confere.
5. **Fallback**: se a lotação não aparecer na tabela (unidade nova/renomeada),
   peça o código de 9 dígitos diretamente ao AFT — ou aceite deixar em branco
   por enquanto (o Sistema Auditor permite confirmar pela lupa), recomendando
   preencher depois editando o `aft-config.md`.

## Passo 4 — Descobrir o caminho Windows da pasta de trabalho

O Sistema Auditor exige caminhos absolutos no formato Windows (`C:\...`) nas linhas
de anexo do TXT. Descubra o caminho real:

```bash
cygpath -w "$HOME" 2>/dev/null || echo "$HOME"
```

- No Windows (Git Bash), isso retorna algo como `C:\Users\joao`. O prefixo da pasta
  de trabalho fica `C:\Users\joao\Documents\AFT`.
- Pergunte: **"O Sistema Auditor roda neste mesmo computador?"**
  - **Sim** (caso normal no Windows) → use o prefixo calculado acima.
  - **Não** (ex.: roda numa máquina virtual que enxerga este disco por outra letra,
    como `Y:`) → pergunte qual letra/prefixo a VM usa para chegar em
    `Documents\AFT` e use esse valor.

## Passo 5 — Gravar o aft-config.md

Crie `~/Documents/AFT/aft-config.md` no formato abaixo: um título, uma linha de
comentário e um **front-matter YAML entre `---`** com os valores coletados:

````markdown
# Configuração do AFT Toolkit
> Gerado por /aft-setup em [DATA]. Pode editar à mão; rode /aft-setup para refazer.

---
nome_auditor: "JOÃO DA SILVA"
cif: "123456"
uorg: "015000000"          # cod_4 do TXT
local_uorg: "SETOR SUL"    # cod_6 do TXT
cep_uorg: "74080010"       # cod_7 do TXT
municipio: "Goiânia"
uf: "GO"
# Prefixo Windows da pasta de trabalho (para os anexos do Sistema Auditor):
path_windows: "C:\\Users\\joao\\Documents\\AFT"
# Caminho completo do interpretador Python (resolvido no Passo 6; evita o atalho
# vazio "python3" da Microsoft Store). As skills devem invocar este executavel:
python_path: "C:\\Users\\joao\\AppData\\Local\\Programs\\Python\\Python312\\python.exe"
# Navegador que o AFT usa com a conta Google do NotebookLM (chrome | edge):
notebooklm_browser: ""     # perguntado e preenchido pelo Passo 7 / /notebooklm-login
# Dados fixos do TXT (não alterar sem orientação):
cod_1: "8211300"           # CNAE placeholder — o Sistema Auditor corrige pela lupa
cod_2: "1008"              # tipo de ação fiscal
---
````

Se o arquivo já existir, mostre os valores atuais e pergunte o que mudar — edite só o
que o AFT pedir.

## Passo 5b — Instalar o perfil do auditor (CLAUDE.md global)

O toolkit traz um perfil pronto que diz ao Claude, em toda conversa, quem é o usuário
(um AFT, não um programador), como tratar dados sensíveis e quais skills usar. Ele vai
em `~/.claude/CLAUDE.md`:

- **Se `~/.claude/CLAUDE.md` NÃO existe** → copie o template:
  ```bash
  cp ~/.claude/skills/config/CLAUDE-aft.md ~/.claude/CLAUDE.md
  ```
  Explique em uma frase: *"Instalei o seu perfil de auditor — a partir da próxima
  conversa, o Claude já sabe que você é AFT, conhece as skills do toolkit e segue as
  regras de privacidade de dados."*
- **Se JÁ existe** → mostre um resumo do conteúdo atual e pergunte: *"Você já tem um
  CLAUDE.md. Quer (a) substituí-lo pelo perfil do AFT Toolkit, (b) acrescentar o perfil
  ao final do existente, ou (c) deixar como está?"* Execute a escolha. Na opção (b),
  acrescente o conteúdo do template após o existente, separado por `---`.

> Quando o toolkit for atualizado (`git pull`), o template novo fica em
> `config/CLAUDE-aft.md` — o `~/.claude/CLAUDE.md` instalado não muda sozinho. Se o AFT
> quiser a versão nova, basta rodar `/aft-setup` de novo.

## Passo 5c — Instalar a deny-list de segurança (settings.json)

O toolkit traz uma lista de **bloqueios de segurança** que impede o Claude de ler
arquivos de credencial (`~/.ssh`, `~/.aws`, `.env`), de ler os mapas `.depara_*.json`
(dados reais de trabalhador) e de usar comandos de acesso remoto (`ssh`, `scp`, `nc`)
que o AFT nunca precisa. É uma rede de proteção: se algum documento de fiscalização
tentar induzir o assistente a vazar dados, esses bloqueios seguram. O template fica em
`config/settings-aft.json` e vai em `~/.claude/settings.json`:

- **Se `~/.claude/settings.json` NÃO existe** → copie o template:
  ```bash
  cp ~/.claude/skills/config/settings-aft.json ~/.claude/settings.json
  ```
- **Se JÁ existe** → **não sobrescreva** (pode ter ajustes do AFT). Leia os dois,
  acrescente as entradas de `config/settings-aft.json` que faltarem dentro de
  `permissions.deny` (sem duplicar) e regrave o arquivo, preservando tudo que já estava
  lá (outras permissões, `allow`, etc.). Use a tool Write com o JSON resultante.

Explique em uma frase: *"Instalei uma rede de proteção: o Claude agora fica proibido de
ler suas senhas e os dados reais dos trabalhadores, mesmo que algum documento peça."*

> Como o `CLAUDE.md`, esse arquivo não muda sozinho num `git pull`; rode `/aft-setup`
> de novo para reaplicar uma versão nova do template.

## Passo 6 — Resolver o Python e instalar as bibliotecas

**6a. Descobrir e gravar o `python_path`.** No Windows, `python3` às vezes é o atalho
vazio da Microsoft Store (abre a loja em vez de rodar) — por isso o toolkit fixa o
caminho completo do interpretador. Você roda (e grava o resultado no `python_path` do
`aft-config.md`):

```bash
python -c "import sys; print(sys.executable)"
```

Se `python` não existir, tente `py -c "import sys; print(sys.executable)"` ou
`where python`. Grave o caminho retornado (ex.:
`C:\Users\joao\AppData\Local\Programs\Python\Python312\python.exe`) no campo
`python_path`. Daí em diante, as skills invocam **esse** executável.

**6b. Instalar as bibliotecas** (use o `python_path` recém-resolvido, não o `pip` solto):

```bash
"<python_path>" -m pip install pillow pikepdf pypdf python-docx pdfplumber pillow-heif
```

Explique: `pillow` converte fotos de evidência em PDF; `pikepdf` inspeciona assinaturas
e comprime anexos grandes; `pypdf` lê os autos lavrados (`/autos-lavrados`);
`python-docx` gera e edita o Relatório Técnico (.docx) da interdição (`/aft-rt-rgi`);
`pdfplumber` extrai texto de PDFs de fiscalização (termos, autos-modelo);
`pillow-heif` lê fotos HEIC/HEIF do iPhone (opcional, só se houver esse formato).

## Passo 7 — NotebookLM (recomendado, pode pular)

As skills de lavratura consultam ementários no Google NotebookLM para achar o código
da ementa automaticamente. **Conecte com a menor intervenção possível e sem nunca
mandar o AFT ao terminal** — o fluxo detalhado, com fallbacks, está na skill
`/notebooklm-login`; conduza-o aqui mesmo:

1. **Confirmar/instalar o CLI e a skill** (você roda — instale com os dois extras:
   `browser` para o login por janela e `cookies` para o login silencioso):
   ```bash
   notebooklm --help            # se faltar, instale:
   pipx install "notebooklm-py[browser,cookies]"
   notebooklm skill install     # registra a skill /notebooklm no Claude Code
   ```
   (Pacote publicado em https://github.com/teng-lin/notebooklm-py. Se não houver pipx:
   `python -m pip install --user pipx && python -m pipx ensurepath`, reabrir o app.)
   **Atenção:** o `pip`/`pipx install` só instala o comando de terminal. Sem o
   `notebooklm skill install`, a skill `/notebooklm` (acesso completo à API: criar
   notebooks, adicionar fontes, gerar artefatos) não aparece no Claude Code, mesmo com
   o CLI funcionando — esse é o passo mais fácil de esquecer numa instalação nova. Essa
   skill é independente da `/notebooklm-login` (que só cuida da autenticação, já
   incluída neste toolkit) e não vem pelo `git clone` do aft-toolkit — pertence ao
   projeto teng-lin/notebooklm-py.
2. **Já conectado?** `notebooklm auth check --test --json` — se `status: ok`, pule
   direto para o teste do item 6.
3. **Qual navegador o AFT usa com a conta Google (Gmail/NotebookLM)?** Pergunte uma vez:
   *"Você usa o Chrome ou o Edge com sua conta do Gmail?"* Grave a resposta em
   `aft-config.md` no campo `notebooklm_browser` (`chrome` ou `edge`) — assim não se
   pergunta de novo nas reconexões. Use essa escolha como `<NAV>` abaixo. **Atenção ao
   nome:** nos comandos de cookie (`auth inspect`, `--browser-cookies`) o Edge é `edge`;
   no login por janela (`--browser`) o Edge é `msedge`; o Chrome é `chrome` nos dois.
4. **Tentar cookies primeiro (zero cliques):** `notebooklm auth inspect --browser <NAV>
   --json`. Se achar uma conta válida:
   `notebooklm login --browser-cookies <NAV>` (com `--account email-do-aft` se houver
   mais de uma). Em Chrome/Edge atualizados isso costuma falhar ("Could not decrypt"):
   é esperado, siga ao item 5 sem alarmar o AFT.
5. **Login por janela (um único login do AFT no Google):** avise que vai abrir o `<NAV>`,
   e rode **com o sandbox desabilitado** (`dangerouslyDisableSandbox`) e timeout alto
   (o comando espera o login por até 5 min):
   ```bash
   notebooklm login --browser chrome     # ou: --browser msedge (Edge)
   ```
   Usa o navegador já instalado — **sem baixar o Chromium e sem Visual C++**. A janela
   abre, o AFT faz login no Google e o comando salva sozinho. (A janela usa um perfil
   isolado, então o login é feito uma vez mesmo que o AFT já esteja logado no navegador
   do dia a dia.) Sem o sandbox desabilitado dá `spawn UNKNOWN` (limitação do sandbox,
   não do PC — nunca mande o AFT ao terminal por isso). Fallbacks: o outro navegador
   (`chrome` <-> `msedge`), depois `notebooklm login` (Chromium próprio, baixado sozinho).
6. **Pedir acesso e testar:** se a lista vier vazia ou "sem acesso", o AFT solicita
   acesso em https://notebooks-aft.vercel.app (conta Google); o mantenedor (Ricardo,
   SRTE/GO) libera os notebooks. Confirme com:
   ```bash
   notebooklm --quiet list
   ```
   Se aparecer a lista de notebooks, está pronto.
7. **Reconexão automática (recomendado):** grave a variável `NOTEBOOKLM_REFRESH_CMD` para o
   `notebooklm ask` se reautenticar sozinho quando a sessão expirar — vale para TODAS as
   skills, sem wrapper. Use o `<NAV>` do AFT (`chrome` ou `msedge`):
   ```powershell
   [Environment]::SetEnvironmentVariable('NOTEBOOKLM_REFRESH_CMD','notebooklm login --browser <NAV>','User')
   ```
   Avise o AFT que isso passa a valer ao **reabrir o Claude Code**. (Detalhes na skill
   `/notebooklm-login`.)

Se o AFT pular este passo, as skills continuam funcionando: elas oferecem o ementário
no Google Drive (link nas próprias skills) ou pedem o código da ementa diretamente.
Quando a sessão expirar no futuro, basta pedir "reconectar o notebooklm"
(skill `/notebooklm-login`) — sem mexer em terminal.

## Passo 7b — Rotina diária do painel (opcional)

Ofereça, em uma frase: *"Quer que o painel (visão geral das suas OS e prazos) se
atualize sozinho toda manhã, sem precisar me pedir? Isso não gasta nada — é o próprio
computador rodando um programinha, sem abrir o Claude Code."*

- **Se não** → pule este passo (sem instalar nada); explique que dá para pedir a
  qualquer momento depois, ou rodar `/painel` manualmente quando quiser.
- **Se sim**:
  1. Confirme/pergunte a pasta de OS ATIVAS a usar (a criada no Passo 2, salvo se o AFT
     já apontou outra) e use o `python_path` já resolvido no Passo 6a.
  2. Instale com o script cross-platform do toolkit (detecta macOS/Windows sozinho):
     ```bash
     python "<python_path recém-resolvido>" ~/.claude/skills/_scripts/instalar_rotina_painel.py instalar "<python_path>" "<pasta OS ATIVAS>"
     ```
     (padrão: todas as manhãs às 07:00 — se o AFT preferir outro horário, acrescente
     `--hora HH:MM`.)
  3. Leia o JSON de retorno (`ok`, `sistema`, `detalhe`) e traduza em uma frase. Se
     `ok: false`, explique o erro em linguagem simples — não é bloqueante, o AFT segue
     podendo rodar `/painel` manualmente.
  4. Grave no `aft-config.md` (acrescente ao front-matter) `rotina_painel: "07:00"` (ou
     o horário escolhido) para o `/aft-atualizar` e o `/aft-doctor` saberem que já foi
     oferecida/instalada e não perguntarem de novo.

> A rotina roda **inteiramente fora do Claude Code** (launchd no macOS, Agendador de
> Tarefas no Windows) — chama o `gerar_painel.py` direto, com `--scan`. Se o Sistema
> Auditor não estiver acessível no horário (VM desligada), o script degrada sozinho
> para o último snapshot salvo; nunca falha por isso. Detalhes e como remover:
> `painel/SKILL.md`, Passo 5.

## Passo 8 — Resumo final

Apresente:

```
✅ AFT Toolkit configurado!

📁 Suas empresas fiscalizadas ficam em: ~/Documents/AFT/OS ATIVAS/
   (arquivadas ao final da fiscalização em ~/Documents/AFT/OS ARQUIVADAS/)
📄 Configuração:      ~/Documents/AFT/aft-config.md
👤 Perfil do auditor: ~/.claude/CLAUDE.md [instalado / mantido o existente]
🛡️ Proteção:          ~/.claude/settings.json [deny-list de segurança aplicada]
🐍 Python:            [versão] · pillow/pikepdf instalados
📚 NotebookLM:        [autenticado / pulado — rode /aft-setup depois para ativar]
📊 Painel diário:      [instalado, roda às HH:MM / não instalado — peça a qualquer hora]

Fluxo típico de uma fiscalização:
  1. /nova-os           → cadastra a empresa e o prazo do DET
  2. /painel            → vê todas as OS e os prazos vencendo
  3. /inspecao-fisica   → registra o relato da visita
  4. /inspecao-inicial  → enquadra NR/ementa e redige os autos
  5. /gera-ai           → gera o TXT para importar no Sistema Auditor
  6. /autos-lavrados    → confere o que foi transmitido
Outras: /registro · /PGR-analise · /aft-rt-rgi · /det-630 · /jornada-analise · /sfitweb-rel
```

Feche sugerindo o diagnóstico: *"Sempre que quiser confirmar que está tudo no lugar
(ou se algo parar de funcionar), rode `/aft-doctor` — ele confere a instalação e diz o
que falta."*

---

## Regras

- Nunca grave CIF/UORG de exemplo no config — só valores realmente informados pelo AFT.
- Não peça nem armazene senhas. O login do NotebookLM é feito pelo navegador do próprio AFT.
- Se algum comando falhar, mostre o erro em linguagem simples e o que fazer — não
  abandone o auditor no meio do setup.
