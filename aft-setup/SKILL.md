---
name: aft-setup
model: sonnet
effort: medium
description: >
  Use quando o AFT acabou de instalar o AFT Toolkit e precisa configurá-lo
  pela primeira vez, ou quando quiser revisar/alterar a configuração. Acione
  com "/aft-setup", "configurar o toolkit", "primeira configuração",
  "configuração inicial", "setup", "mudar minha CIF", "mudar minha UORG".
  Verifica pré-requisitos, cria a pasta de trabalho, coleta os dados do
  auditor (nome, CIF, UORG, município) e grava o aft-config.md. Todas as
  outras skills leem essa configuração.
---

# aft-setup — Configuração inicial do AFT Toolkit

## Objetivo

Deixar o computador do AFT pronto para usar todas as skills do toolkit. Roda uma única
vez (ou quando o auditor quiser mudar algo). Ao final, existe:

- A pasta de trabalho (padrão `~/Documents/AFT/`, mas o AFT pode escolher outro
  lugar no Passo 2) com `OS ATIVAS/` e `OS ARQUIVADAS/`.
- O arquivo `aft-config.md`, dentro dela, com os dados do auditor e da unidade.
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

**Não use `mkdir ~/Documents/AFT` direto** e **não presuma o caminho**. No Windows,
"Documentos" quase nunca fica em `C:\Users\<usuário>\Documents`: o Windows em português
chama a pasta de **Documentos** e o **OneDrive** costuma redirecioná-la para dentro
dele. Um `mkdir` cru cria uma pasta **órfã** que o AFT nunca encontra no Explorer
(aconteceu numa instalação real). Use o resolvedor:

```bash
python "<python_path>" ~/.claude/skills/_scripts/pasta_aft.py --criar
```

Ele devolve um JSON com o caminho real (`pasta_aft`), o que criou (`criadas`) e o que
descobriu do ambiente (`padrao`, `onedrive`, `onedrive_raizes`, `redirecionada`).
**Use esse caminho** — e não o `~/Documents/AFT` presumido — em todos os passos
seguintes (aft-config.md, painel, vigia de sessões). É idempotente: rodar de novo não
recria nada.

> **No Windows com OneDrive, o padrão é dentro do OneDrive.** É o que a maioria dos
> colegas quer: a pasta de trabalho sincronizada, disponível no notebook de campo e
> dentro do backup da instituição. O resolvedor prefere o OneDrive **corporativo** (o do
> trabalho) ao pessoal; quando o OneDrive já faz backup da sua pasta Documentos, os dois
> caminhos são o mesmo. **Uma pasta AFT que já exista com fiscalizações dentro nunca é
> abandonada** — o padrão só decide onde CRIAR numa instalação nova.

> Se o JSON trouxer `duplicadas`, existe outra pasta AFT com arquivos em outro lugar
> (instalação anterior). Avise o AFT: se tiver fiscalizações dentro, mover as subpastas
> para a `OS ATIVAS` correta; se estiver vazia, pode apagar.

### O AFT quer a pasta em outro lugar?

Mostre o caminho resolvido e pergunte, **em uma frase**, se ele quer manter ali ou usar
outro lugar (HD externo, outra nuvem, outro disco). Não insista: o padrão serve para
quase todo mundo — só siga adiante se ele **pedir** a mudança.

Se ele quiser outro lugar, peça a pasta que vai **conter** a `OS ATIVAS` (não a própria
`OS ATIVAS` — o script recusa e explica se ele apontar a subpasta) e rode:

```bash
python "<python_path>" ~/.claude/skills/_scripts/pasta_aft.py --definir "<caminho>" --mover
```

- `--mover` leva junto o que já existir na pasta antiga. **Nunca sobrescreve**: se o
  destino já tiver dados, o script recusa e explica como juntar as duas à mão.
- A escolha fica gravada em `~/.claude/aft-pasta.txt`, **fora** do repositório das skills.
  Diga isso ao AFT: *"atualizar o toolkit nunca vai desfazer essa escolha"*.
- Daí em diante, **use o `pasta_aft` do JSON** em todos os passos seguintes.

> **O `--mover` não move só os arquivos.** Ele derruba e reinstala com o caminho novo os
> serviços que guardam a pasta por dentro (servidor do painel, rotina diária, vigia de
> sessões) e realinha as **sessões por empresa** do app — o `cwd` de cada `local_*.json`
> e a pasta de histórico da conversa em `~/.claude/projects`. Leia esses campos do JSON
> (`servicos`, `sessoes`) e traduza o resultado. Se o app do Claude estiver **aberto** na
> hora (o normal, já que você está conversando por ele), a parte das sessões vira uma
> **pendência**: o vigia aplica sozinho no próximo fechamento do app. Diga isso ao AFT em
> uma frase — *"feche e reabra o app uma vez e as suas conversas por empresa acompanham a
> mudança"* — em vez de deixá-lo descobrir com um "Sessão não encontrada no disco".

> Deste ponto em diante, onde este texto disser `<PASTA_AFT>` use o `pasta_aft` do JSON
> (a pasta de trabalho) e onde disser `<OS_ATIVAS>` use `<PASTA_AFT>/OS ATIVAS`. Nunca
> escreva `~/Documents/AFT` nas mensagens ao AFT: mostre sempre o caminho real dele.

> Nuvem (OneDrive/Dropbox/iCloud): funciona, mas avise em uma frase que o sincronismo
> pode segurar arquivos abertos e que os dados de fiscalização passam a ser copiados para
> o servidor do provedor — decisão dele, não sua.

Explique ao AFT, com destaque (essa é a informação mais importante do setup — o AFT
vai voltar a ela toda vez que quiser achar os arquivos de uma fiscalização), usando o
**caminho real que o script devolveu**:

> 📁 **`Documentos\AFT\OS ATIVAS` é onde moram todas as suas empresas fiscalizadas.**
> Cada empresa ganha uma subpasta ali dentro (padrão: `NOME DA EMPRESA <CNPJ 14
> dígitos>`), com todos os arquivos daquela fiscalização: relato de campo, autos,
> anexos e a ficha `memory.md`. Quando a fiscalização termina, a pasta inteira vai
> para `OS ARQUIVADAS` (mesmo nível, ao lado de `OS ATIVAS`). Tudo fica **no seu
> computador** — nada é enviado para fora.

### Passo 2a — A pasta `CATs` (opcional, mas vale a pena)

Ao lado de `OS ATIVAS`, o toolkit procura uma pasta **`CATs`** com as planilhas de
Comunicação de Acidente do estado do AFT (uma `.xlsx` por ano, fonte eSocial). Com
ela montada, a `/aft-relatorio-acidentes` levanta o histórico de acidentes de
qualquer CNPJ, e a `/aft-preparacao-acao-fiscal` leva esse histórico para a visita.
Sem ela, as duas seguem funcionando — só sem essa parte.

Crie a pasta agora (dentro de `<PASTA_AFT>`) e dê o recado, com o caminho real dele:

> 📥 **Para ver o histórico de acidentes das empresas, ponha as planilhas de CAT do
> seu estado em `Documentos\AFT\CATs`.**
>
> 1. Abra a área do ENIT no SharePoint do MTE, pasta **"CATs eSocial por UF"**:
>    <https://mtegovbr-my.sharepoint.com/shared?listurl=https%3A%2F%2Fmtegovbr%2Dmy%2Esharepoint%2Ecom%2Fpersonal%2Fjoao%5Freis%5Ftrabalho%5Fgov%5Fbr%2FDocuments&id=%2Fpersonal%2Fjoao%5Freis%5Ftrabalho%5Fgov%5Fbr%2FDocuments%2FDados%2FCATs%20eSocial%20por%20UF&shareLink=1&ga=1>
> 2. O link **só abre com a sua conta institucional (Microsoft) logada** — é
>    conteúdo interno do Ministério, e eu não tenho como entrar por você.
> 3. Baixe **todas as planilhas da sua UF** (uma por ano; quanto mais anos, mais
>    fundo vai o histórico) e jogue os arquivos nessa pasta.
>
> Não precisa configurar nada depois: o toolkit acha a pasta sozinho.

É um passo que o AFT faz no navegador, na hora que quiser — não trave o setup
esperando por ele.

## Passo 2b — Instalar os agentes do toolkit

Além das skills, o toolkit traz **agentes** — ajudantes que trabalham numa conversa
isolada, sem entulhar a principal (hoje: o revisor de autos `aft-revisor-autos` e a
varredura do Sistema Auditor `aft-autos-lavrados`). Eles vêm no repositório em
`~/.claude/skills/agents/`, mas o Claude Code só os descobre em `~/.claude/agents/`.
Instale (idempotente, você roda):

```bash
python ~/.claude/skills/_scripts/instalar_agentes.py
```

Leia o JSON (`instalados`/`atualizados`/`em_dia`). Os agentes passam a valer quando o
app for reiniciado — o mesmo reinício que o fim do setup já pede. Se falhar, **não é
bloqueante**: as skills funcionam sem os agentes (modo inline); registre no resumo.

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
de anexo do TXT. Converta **a pasta que o Passo 2 devolveu** (nunca um caminho
presumido) para o formato Windows:

```bash
cygpath -w "<pasta_aft do Passo 2>" 2>/dev/null || echo "<pasta_aft do Passo 2>"
```

- No Windows (Git Bash) isso retorna o caminho real — que pode ser
  `C:\Users\joao\Documents\AFT` **ou** `C:\Users\joao\OneDrive\Documentos\AFT` se o
  OneDrive fizer backup das pastas. Use o que vier; é ele que vai no `path_windows`.
- Pergunte: **"O Sistema Auditor roda neste mesmo computador?"**
  - **Sim** (caso normal no Windows) → use o prefixo calculado acima.
  - **Não** (ex.: roda numa máquina virtual que enxerga este disco por outra letra,
    como `Y:`) → pergunte qual letra/prefixo a VM usa para chegar em
    `Documents\AFT` e use esse valor.

## Passo 5 — Gravar o aft-config.md

Crie o `aft-config.md` **dentro da pasta que o Passo 2 devolveu** (não presuma
`~/Documents/AFT`), no formato abaixo: um título, uma linha de comentário e um
**front-matter YAML entre `---`** com os valores coletados:

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
notebooklm_browser: ""     # perguntado e preenchido pelo Passo 7 / /aft-notebooklm-login
# Dados fixos do TXT (não alterar sem orientação):
cod_1: "8211300"           # CNAE placeholder — o Sistema Auditor corrige pela lupa
cod_2: "0"                 # nº de empregados da empresa no TXT (0 = não informado)
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

> O template é um **bloco gerenciado**: cercado por marcadores invisíveis
> (`<!-- AFT-TOOLKIT-PERFIL:INICIO vN ... -->` … `:FIM -->`) com número de versão. Tanto
> o `cp` quanto a opção (b) já carregam os marcadores. Graças a eles, o `/aft-atualizar`
> mantém o perfil em dia **sozinho** dali em diante — substitui só o miolo entre os
> marcadores quando sai uma versão nova, sem tocar no que o AFT escreveu por fora (não é
> mais preciso rodar `/aft-setup` de novo só para atualizar o CLAUDE.md).

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
  **Também acrescente a chave `effortLevel` — mas SÓ se ela ainda não existir** no
  arquivo do AFT. Se já existir com qualquer valor, deixe como está: significa que ele
  escolheu o próprio nível (pelo `/effort` ou à mão) e essa escolha manda.

Explique em duas frases: *"Instalei uma rede de proteção: o Claude agora fica proibido de
ler suas senhas e os dados reais dos trabalhadores, mesmo que algum documento peça. E
deixei o nível de esforço em 'alto', que é o certo para enquadramento e redação de auto —
as tarefas mecânicas do toolkit já baixam isso sozinhas."*

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
e comprime anexos grandes; `pypdf` lê os autos lavrados (`/aft-autos-lavrados`);
`python-docx` gera e edita o Relatório Técnico (.docx) da interdição (`/aft-rt-rgi`);
`pdfplumber` extrai texto de PDFs de fiscalização (termos, autos-modelo);
`pillow-heif` lê fotos HEIC/HEIF do iPhone (opcional, só se houver esse formato).

## Passo 7 — NotebookLM (recomendado, pode pular)

As skills de lavratura consultam ementários no Google NotebookLM para achar o código
da ementa automaticamente. **Conecte com a menor intervenção possível e sem nunca
mandar o AFT ao terminal** — o fluxo detalhado, com fallbacks, está na skill
`/aft-notebooklm-login`; conduza-o aqui mesmo:

1. **Confirmar/instalar o CLI e a skill** (você roda — instale com os dois extras:
   `browser` para o login por janela e `cookies` para o login silencioso):
   ```bash
   notebooklm --help            # se faltar, instale:
   pipx install --force "notebooklm-py[browser,cookies] @ git+https://github.com/teng-lin/notebooklm-py@main"
   notebooklm skill install     # registra a skill /notebooklm no Claude Code
   ```
   (Pacote de https://github.com/teng-lin/notebooklm-py — **instale do git, não do
   PyPI**: o rebrand "Gemini Notebook" de 16/07/2026 quebrou o login de toda a série
   0.7.x publicada, e a correção por ora só está no `main`; detalhes no Passo 0 da
   `/aft-notebooklm-login`. Se não houver pipx:
   `python -m pip install --user pipx && python -m pipx ensurepath`, reabrir o app.)
   Se o comando já existir mas `notebooklm --version` mostrar `0.7.x`, atualize com o
   mesmo comando acima antes de qualquer login.
   **Atenção:** o `pip`/`pipx install` só instala o comando de terminal. Sem o
   `notebooklm skill install`, a skill `/notebooklm` (acesso completo à API: criar
   notebooks, adicionar fontes, gerar artefatos) não aparece no Claude Code, mesmo com
   o CLI funcionando — esse é o passo mais fácil de esquecer numa instalação nova. Essa
   skill é independente da `/aft-notebooklm-login` (que só cuida da autenticação, já
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
6. **Conferir o que o AFT realmente consulta** (e não o `notebooklm list`):
   ```bash
   python "<python_path>" ~/.claude/skills/_scripts/notebooklm_acesso.py
   ```
   Percorre os notebooks do ementário um por um e devolve `disponiveis` /
   `indisponiveis` / `erros`. **Não use `notebooklm list` como prova de sucesso**: ele
   lista só os notebooks vistos recentemente, então vem vazio mesmo com tudo certo.

   O que vier em `indisponiveis` precisa de **um primeiro acesso feito pelo AFT** — o
   Google só põe um notebook compartilhado na coleção da conta depois que a pessoa o
   abre uma vez, e nenhum comando faz isso por ela. Dê o recado do **Passo 5 da
   `/aft-notebooklm-login`** (links clicáveis + "escreva oi na caixa de chat" + o portal
   https://notebooks-aft.vercel.app para quem ainda não tem acesso). Deixe claro que é
   uma vez por notebook, para sempre, e que ele só precisa abrir os temas que fiscaliza.
7. **Reconexão automática (recomendado):** grave a variável `NOTEBOOKLM_REFRESH_CMD` para o
   `notebooklm ask` se reautenticar sozinho quando a sessão expirar — vale para TODAS as
   skills, sem wrapper. O valor é o script **silencioso** do toolkit (renova sem abrir
   janela, pelo perfil salvo). Monte-o com caminhos completos — o `python_path` do
   `aft-config.md` e a pasta do usuário — com **barras normais** (`/`) e aspas, e o
   `<NAV>` do AFT (`chrome` ou `msedge`):
   ```powershell
   [Environment]::SetEnvironmentVariable('NOTEBOOKLM_REFRESH_CMD','"C:/caminho/do/python.exe" "C:/Users/FULANO/.claude/skills/_scripts/notebooklm_reauth.py" <NAV>','User')
   ```
   Avise o AFT que isso passa a valer ao **reabrir o Claude Code**. (Detalhes e o valor
   antigo a substituir na skill `/aft-notebooklm-login`.)

Se o AFT pular este passo, as skills continuam funcionando: elas oferecem o ementário
no Google Drive (link nas próprias skills) ou pedem o código da ementa diretamente.
Quando a sessão expirar no futuro, basta pedir "reconectar o notebooklm"
(skill `/aft-notebooklm-login`) — sem mexer em terminal.

## Passo 7b — Rotina diária do painel (opcional)

Ofereça, em uma frase: *"Quer que o painel (visão geral das suas OS e prazos) se
atualize sozinho toda manhã, sem precisar me pedir? Isso não gasta nada — é o próprio
computador rodando um programinha, sem abrir o Claude Code."*

- **Se não** → pule este passo (sem instalar nada); explique que dá para pedir a
  qualquer momento depois, ou rodar `/aft-painel` manualmente quando quiser.
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
     podendo rodar `/aft-painel` manualmente.
  4. Grave no `aft-config.md` (acrescente ao front-matter) `rotina_painel: "07:00"` (ou
     o horário escolhido) para o `/aft-atualizar` e o `/aft-doctor` saberem que já foi
     oferecida/instalada e não perguntarem de novo.

> A rotina roda **inteiramente fora do Claude Code** (launchd no macOS, Agendador de
> Tarefas no Windows) — chama o `gerar_painel.py` direto, com `--scan`. Se o Sistema
> Auditor não estiver acessível no horário (VM desligada), o script degrada sozinho
> para o último snapshot salvo; nunca falha por isso. Detalhes e como remover:
> `aft-painel/SKILL.md`, Passo 5.

## Passo 7c — Painel interativo sempre ligado (parte padrão da instalação)

Isso é **diferente** do Passo 7b: aquele só regenera o `painel.html` (arquivo estático) uma
vez por dia; este mantém o **servidor interativo** (`http://127.0.0.1:8347`) sempre no ar,
subindo sozinho a cada login. É o que os controles do painel (marcar DET, pendência,
atividade, status, embargo) e a **sincronização automática do DET pela extensão Chrome**
("SisOS — Sync DET") precisam para funcionar sem o AFT ter que abrir um terminal.

Isso faz parte da instalação padrão — **instale sem perguntar**. Avise em uma frase o que
foi feito: *"Deixei o painel interativo sempre ligado no seu computador — sobe sozinho
quando você liga a máquina, sem terminal. Ele roda só na sua máquina; nada sai para a
internet."*

1. Use a pasta de OS ATIVAS e o `python_path` já resolvidos nos passos anteriores.
2. Instale:
   ```bash
   python "<python_path>" ~/.claude/skills/_scripts/instalar_servidor_painel.py instalar "<python_path>" "<pasta OS ATIVAS>"
   ```
3. Leia o JSON de retorno (`ok`, `sistema`, `detalhe`) e traduza em uma frase — no
   Windows isso usa o Agendador de Tarefas com gatilho "ao fazer logon" e reinício
   automático (`pythonw.exe`, sem janela); no macOS um LaunchAgent com `KeepAlive`. Se
   `ok: false`, explique o erro em linguagem simples — não é bloqueante.
4. Grave `servidor_painel: "ligado"` no front-matter do `aft-config.md`.

> Não é uma prisão: se depois o AFT **não** quiser mais o servidor sempre ligado, dá para
> remover com `python instalar_servidor_painel.py remover` (é só pedir). Detalhes:
> `aft-painel/SKILL.md`, Passo 3.5.

## Passo 7d — Prazos de DET no Google Calendar (opcional)

Ofereça, em uma frase: *"Quer que os prazos das notificações DET apareçam também no seu
Google Calendar (um evento por notificação, com atualização quando o prazo muda)? É um
login único do Google, feito com segurança pela interface do Claude."*

- **Se não** → grave `agenda_det: ""` no `aft-config.md` (para não perguntar de novo) e
  siga. Mencione que os botões "agendar no Google Calendar" do painel funcionam sem
  login nenhum (um clique por evento).
- **Se sim**:
  1. Verifique se o **conector Google Calendar** do Claude já está conectado (tente
     listar os calendários). Se não estiver, oriente: aplicativo do Claude/claude.ai →
     **Configurações → Conectores → Google Calendar → Conectar** (na CLI, `/mcp`) —
     nenhuma senha passa pelo toolkit.
  2. Rode a primeira sincronização seguindo a skill `/aft-agenda-det` (Passos 1–3).
  3. Ofereça a rotina diária do Passo 4 da `/aft-agenda-det` (tarefas agendadas do Claude
     Code, se disponíveis) e grave `agenda_det: "diario"` ou `agenda_det: "manual"` no
     `aft-config.md`, conforme a escolha.

## Passo 7e — Vigia de sessões (parte padrão da instalação)

As sessões por empresa no menu lateral (grupo "OS ATIVAS") são **automáticas**: um
serviço em segundo plano — o **vigia de sessões** — observa as pastas de `OS ATIVAS/` e,
toda vez que o app do Claude é fechado, cria as sessões que faltam (título = empresa,
pasta = pasta da OS, vínculo no memory.md). **Instale sem perguntar**:

```bash
python ~/.claude/skills/_scripts/instalar_vigia_sessoes.py instalar <python_path>
```

Confira o JSON de saída (`"ok": true`). Informe em uma linha: *"Sessões por empresa são
automáticas: cada auditoria em OS ATIVAS ganha a própria sessão no grupo 'OS ATIVAS' na
próxima vez que você fechar e reabrir o app."* Se falhar, não é bloqueante — registre no
resumo e siga (o `/aft-atualizar` tenta de novo). Quem não quiser o automático pede
"remover o vigia de sessões" a qualquer momento.

## Passo 8 — Resumo final

Apresente:

```
✅ AFT Toolkit configurado!

📁 Suas empresas fiscalizadas ficam em: <OS_ATIVAS>/
   (arquivadas ao final da fiscalização em <PASTA_AFT>/OS ARQUIVADAS/)
📄 Configuração:      <PASTA_AFT>/aft-config.md
👤 Perfil do auditor: ~/.claude/CLAUDE.md [instalado / mantido o existente]
🤖 Agentes:           [N instalados em ~/.claude/agents (revisor de autos + varredura
                       do Sistema Auditor) / falhou — skills seguem no modo inline]
🛡️ Proteção:          ~/.claude/settings.json [deny-list de segurança aplicada]
🐍 Python:            [versão] · pillow/pikepdf instalados
📚 NotebookLM:        [autenticado · N de M notebooks já consultáveis (M-N esperando o
                       seu primeiro "oi") / pulado — rode /aft-setup depois para ativar]
📊 Painel diário:      [instalado, roda às HH:MM / não instalado — peça a qualquer hora]
🖥️ Painel interativo:  sempre ligado (sobe sozinho no login; só na sua máquina — peça
                       "remover o painel sempre ligado" se não quiser)
📅 Google Calendar:    [prazos de DET sincronizando via /aft-agenda-det / não ativado —
                       peça a qualquer hora]

➡️ JÁ FISCALIZAVA ANTES DO TOOLKIT? Primeiro passo essencial:
   copie as pastas das suas auditorias (do jeito que estiverem) para
   <OS_ATIVAS>/ e me peça /aft-organiza-os — eu organizo tudo e
   trago os autos do Sistema Auditor (/aft-autos-lavrados). As sessões por
   empresa (grupo "OS ATIVAS" do menu lateral) são automáticas: aparecem
   na próxima vez que você fechar e reabrir o app.

Fluxo típico de uma fiscalização:
  1. /aft-nova-os           → cadastra a empresa e o prazo do DET
  2. /aft-painel            → vê todas as OS e os prazos vencendo
  3. /aft-inspecao-fisica   → registra o relato da visita
  4. /aft-auditoria-geral  → enquadra NR/ementa e redige os autos
  5. /aft-gera-ai           → gera o TXT para importar no Sistema Auditor
  6. /aft-autos-lavrados    → confere o que foi transmitido
Outras: /aft-registro · /aft-PGR-analise · /aft-rt-rgi · /aft-det-630 · /aft-jornada-analise · /aft-sfitweb-rel
```

Se a pasta `OS ATIVAS/` estiver vazia, pergunte ativamente: *"Você já tem fiscalizações
em andamento? Copie as pastas delas para <OS_ATIVAS>/ (do jeito que
estiverem) e me avise — eu rodo o /aft-organiza-os, que organiza tudo e busca os autos já
transmitidos no Sistema Auditor. As sessões por empresa aparecem sozinhas no grupo
'OS ATIVAS' quando você fechar e reabrir o app."*

Feche sugerindo o diagnóstico: *"Sempre que quiser confirmar que está tudo no lugar
(ou se algo parar de funcionar), rode `/aft-doctor` — ele confere a instalação e diz o
que falta."*

---

## Regras

- Nunca grave CIF/UORG de exemplo no config — só valores realmente informados pelo AFT.
- Não peça nem armazene senhas. O login do NotebookLM é feito pelo navegador do próprio AFT.
- Se algum comando falhar, mostre o erro em linguagem simples e o que fazer — não
  abandone o auditor no meio do setup.
