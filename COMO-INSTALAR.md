# Como instalar o AFT Toolkit no seu Claude Code (Windows)

Instalação em **4 passos** — você instala manualmente só o aplicativo e o Git; do Python em diante, quem digita comando é o Claude. Tempo total: ~15 minutos.

---

## Passo 1 — Instale o aplicativo Claude

1. Baixe o **Claude para Windows** em https://claude.com/claude-code.
2. Instale e entre com a sua conta Claude (a mesma do claude.ai). É preciso um plano que inclua o Claude Code (Pro ou superior).

---

## Passo 2 — Instale o Git

No Windows, o aplicativo **exige o Git para abrir sessões locais** na aba `</> Code` — sem ele, aparece a mensagem "Git is required for local sessions". Por isso este é o único programa que você instala à mão:

1. Baixe em https://git-scm.com/download/win e instale com as opções padrão (clicar "Next" até o fim).
2. Feche o aplicativo Claude **de verdade**: ele continua rodando na bandeja do sistema (ícones perto do relógio). Botão direito no ícone do Claude → **Sair**. Fechar só a janela no X não basta.
3. Abra o aplicativo de novo.

**Para que serve o Git?** Nada de programação — é a ferramenta que baixa o toolkit e busca as atualizações futuras (o "downloader"), e traz o Git Bash, o terminal que o Claude Code usa no Windows.

---

## Passo 3 — Deixe o Claude instalar o resto

Abra a interface de código (botão **`</> Code`**) e inicie uma conversa nova. O Claude pede para você **escolher uma pasta para a sessão** (a pasta do computador em que ele vai trabalhar). Escolha a pasta **Documentos** (`C:\Users\seu-nome\Documents`). Depois da instalação, quando `Documentos\AFT` existir, prefira escolhê-la nas conversas do dia a dia.

O Claude Code é um assistente que executa comandos no seu computador, **sempre pedindo a sua permissão antes**. Você vai colar **três mensagens**, uma de cada vez, esperando ele terminar cada uma.

**Por que três e não uma só?** Porque a terceira mensagem mexe na pasta de onde o próprio Claude lê as suas skills. Ele é treinado para desconfiar de conteúdo que vem da internet e vai direto para essa pasta — e faz muito bem. As três mensagens fazem **baixar → ele conferir → instalar**: quando chega a hora de instalar, ele já leu o que está instalando. Não é burocracia; é ele conferindo o que vai rodar na sua máquina.

**Mensagem 1 — o básico (Git, Python e a ferramenta de ementas):**

```
Prepare este computador para o AFT Toolkit. Faça nesta ordem, me explicando cada passo em linguagem simples:
1. Confirme que o Git está instalado e funcionando (git --version).
2. Verifique se o Python 3 está instalado e funcionando no terminal; se não, instale com winget (pacote Python.Python.3.12).
3. Instale o pacote notebooklm-py com os extras browser e cookies: pipx install "notebooklm-py[browser,cookies]" (se não houver pipx, instale o pipx antes). Ao final, confirme que o comando notebooklm responde (notebooklm --help). Não é preciso baixar navegador nenhum nem o Visual C++: o login usa o Edge/Chrome que já existe no computador.
```

**Mensagem 2 — baixar o toolkit e deixar ele ler:**

```
Baixe o repositório https://github.com/ryckardo42/aft-toolkit.git para a pasta Documentos\aft-toolkit, usando git clone. Depois liste o que veio, leia o README.md e uns três arquivos SKILL.md e me explique em linguagem simples o que essas skills fazem, se alguma coisa roda sozinha e se você vê algum risco.
```

**Mensagem 3 — instalar (só depois que ele responder a mensagem 2):**

```
Agora mova todo o conteúdo da pasta Documentos\aft-toolkit, inclusive a pasta oculta .git, para ~/.claude/skills. O resultado tem que ser ~/.claude/skills/aft-setup/SKILL.md — e NÃO ~/.claude/skills/aft-toolkit/aft-setup. Se ~/.claude/skills já tiver alguma coisa dentro, preserve o que existe e apenas acrescente. No final, liste as skills e me diga se preciso reiniciar o aplicativo.
```

Enquanto o Claude trabalha, ele vai pedir permissão para cada comando — basta clicar em **Permitir**. Isso é normal e desejável: nada roda no seu computador sem o seu OK.

**O que ele está instalando?**
- **Python** — roda os scripts locais do toolkit: conversão de fotos em PDF, geração do arquivo do Sistema Auditor e validação de arquivos de ponto.
- **notebooklm** — a ferramenta que consulta os ementários no NotebookLM para achar o código da ementa sozinho. Aqui fica instalado o comando de terminal; o login (na sua conta Google) o Claude conduz para você no passo "Recomendado — Ative o NotebookLM" abaixo, sem terminal.

> **Se o Claude recusar a mensagem 3** ("não instalo conteúdo de fonte que não consigo verificar"), **não discuta com ele nem insista** — argumentar costuma deixá-lo mais desconfiado, não menos. Peça primeiro: *"me explique o que exatamente te preocupa nesse conteúdo que você acabou de ler"*. Se ainda assim recusar, use o **Plano B** no fim desta página: os mesmos comandos, executados por você. Não é sinal de que há algo errado com o toolkit — é uma precaução genérica dele sobre o **tipo** de ação, não sobre a origem.

---

## Passo 4 — Reinicie e configure

1. **Feche e reabra** o aplicativo Claude (para ele reconhecer as skills novas e o Git).
2. Numa conversa nova do `</> Code` (pasta da sessão: **Documentos**), digite:
   ```
   /aft-setup
   ```

A skill de configuração cria a pasta `Documentos\AFT`, pergunta seu nome, CIF e os dados da sua UORG, e instala as bibliotecas Python necessárias. Esses dados entram automaticamente nos arquivos do Sistema Auditor — você nunca mais digita.

3. Confira a instalação: digite **`/aft-doctor`** — ele verifica tudo (Python, Git, skills, configuração) e diz, em linguagem simples, o que falta e como resolver.

---

## Passo 5 — Traga as suas fiscalizações (o primeiro passo que importa)

Se você já tem auditorias em andamento, este é o **primeiro passo essencial** depois da
instalação:

1. **Copie as pastas das suas fiscalizações** (do jeito que estiverem, com os documentos
   acumulados) para dentro de `Documentos\AFT\OS ATIVAS\` — uma pasta por empresa.
   (Prefere essa pasta em outro lugar, como um HD externo? Peça ao Claude: *"quero
   minhas fiscalizações no HD externo"*. Ele muda tudo de lugar e a escolha vale para
   sempre — nem a atualização do toolkit desfaz.)
2. Na conversa do `</> Code`, digite **`/aft-organiza-os`**.

Com uma única aprovação sua, ele faz três coisas:

- **organiza tudo** no padrão do toolkit (nomes de pasta, ficha `memory.md` com
  empregador/CNPJ/notificações DET extraídos dos próprios documentos, arquivos nos
  lugares certos — sem apagar nada);
- **busca os autos já lavrados**: roda o `/aft-autos-lavrados`, que vai às pastas do Sistema
  Auditor, encontra os autos transmitidos de cada empresa e os registra no `memory.md`;
- **cria uma sessão de chat por empresa** no menu lateral do app, no grupo "OS ATIVAS" —
  automático: o vigia de sessões (instalado pelo `/aft-setup`) aplica sozinho, e as
  sessões aparecem na próxima vez que você fechar e reabrir o app. Daí em diante, tudo
  daquela auditoria é tratado na sessão dela.

Quem está começando do zero (sem fiscalizações em andamento) pula este passo e usa o
`/aft-nova-auditoria` a cada auditoria nova.

---

## Recomendado — Ative o NotebookLM

Com o NotebookLM ativo, as skills encontram o **código da ementa sozinhas**. A ferramenta `notebooklm` já foi instalada no Passo 3. Você **não precisa do terminal**: o Claude faz a conexão por você.

1. Entre em **https://notebooks-aft.vercel.app** com sua conta Google e solicite acesso; aguarde a liberação pelo mantenedor.
2. Na conversa do `</> Code`, digite **`/aft-notebooklm-login`** (ou peça "conecte o notebooklm"). O Claude tenta conectar sozinho pelos cookies do navegador e, se precisar, **abre uma janela do Edge** onde você só faz login na sua conta Google — ele salva a conexão automaticamente. O `/aft-setup` também conduz esse passo.
3. Se um dia a consulta de ementa parar de funcionar ("authentication expired"), é só pedir "reconecte o notebooklm" — sem mexer em terminal.

Sem o NotebookLM, tudo continua funcionando — as skills pedem o código da ementa ou indicam o ementário no Google Drive.

---

## Pronto! Experimente

| Situação | Digite |
|---|---|
| Importar suas fiscalizações em andamento (1º passo!) | copie as pastas para `OS ATIVAS` e digite `/aft-organiza-os` |
| Cadastrar uma auditoria nova | `/aft-nova-auditoria` |
| Ver suas OS e prazos de DET | `/aft-painel` |
| Voltou de uma inspeção | `/aft-inspecao-fisica` e narre o que viu |
| Quer redigir os autos | `/aft-auditoria-geral` |
| Trabalhador sem registro | `/aft-informalidade` |
| Analisar um PGR | `/aft-PGR-analise` |
| Empresa não entregou documentos do DET | `/aft-det-630` |
| Interdição/embargo | `/aft-embargo-interdicao` |
| Analisar AFD/AEJ/atestado de ponto | `/aft-jornada-analise` |
| Gerar o TXT do Sistema Auditor | `/aft-gera-ai` |
| Relatório final | `/aft-relatorio` |

## Como receber atualizações

Peça ao Claude, numa conversa qualquer: **"Atualize o AFT Toolkit"** (ou `/aft-atualizar`). Ele atualiza as skills (`git pull`), confere se o comando `notebooklm` tem versão nova e atualiza sozinho se houver, e confirma no final com o `/aft-doctor` que nada quebrou — mostrando o que mudou em cada parte.

---

## Plano B — instalação manual

Só se o Passo 3 falhar (computador sem winget, rede corporativa bloqueando, **ou o assistente recusar a instalação por precaução de segurança** — pode acontecer, e não é sinal de problema com o toolkit):

- **Python**: baixe em https://www.python.org/downloads/ e, na primeira tela do instalador, **marque "Add Python to PATH"**.
- **notebooklm**: abra o **PowerShell** (menu Iniciar) e cole, um bloco de cada vez:
  ```powershell
  python -m pip install --user pipx
  python -m pipx install "notebooklm-py[browser,cookies] @ git+https://github.com/teng-lin/notebooklm-py.git"
  python -m pipx ensurepath
  ```
  **Feche e reabra o PowerShell** (para o comando entrar no PATH) e cole:
  ```powershell
  notebooklm --help
  ```
- **Toolkit**: ainda no PowerShell, cole o bloco abaixo. Ele baixa o toolkit para `Documentos\aft-toolkit` e move tudo (inclusive a pasta oculta `.git`, que serve para as atualizações futuras) para a pasta de skills, preservando o que já houver lá:
  ```powershell
  $origem = "$HOME\Documents\aft-toolkit"
  $skillsDir = "$HOME\.claude\skills"
  git clone https://github.com/ryckardo42/aft-toolkit.git $origem
  New-Item -ItemType Directory -Force -Path $skillsDir | Out-Null
  Get-ChildItem -Force $origem | Move-Item -Destination $skillsDir -Force
  Remove-Item $origem -Recurse -Force
  Test-Path "$HOME\.claude\skills\aft-setup\SKILL.md"
  ```
  Se a última linha responder `True`, deu certo — siga para o Passo 4 (reiniciar e `/aft-setup`).

## Problemas comuns

Regra geral: **descreva o problema ao próprio Claude** no `</> Code` ("o comando X deu este erro: ...") — ele diagnostica e corrige. **Você nunca precisa abrir um terminal:** quem digita comando é sempre o Claude.

| Sintoma | Solução |
|---|---|
| "Git is required for local sessions" | Instale o Git (Passo 2) e feche o app de verdade: ícone do Claude na bandeja → Sair; reabra. Se persistir, reinicie o computador |
| Python "não encontrado" | Peça ao Claude: "instale o Python com winget". Se a rede bloquear, plano B manual acima e reinicie o app |
| Skill não aparece com `/` | Feche e reabra o Claude Code. Se persistir, peça a ele: "as skills estão diretamente em ~/.claude/skills (ex.: ~/.claude/skills/aft-setup)? Se estiverem dentro de uma subpasta aft-toolkit, mova todo o conteúdo um nível acima" |
| NotebookLM não conecta / "command not found" / pede login | Peça ao Claude: "conecte o notebooklm" (skill `/aft-notebooklm-login`). Ele instala o que faltar e abre a janela de login do Edge — você só entra na sua conta Google |
| O Claude recusa o Passo 3 ("não instalo conteúdo que não consigo verificar") | Não discuta nem insista — argumentar deixa ele mais desconfiado. Confirme que você mandou as três mensagens **na ordem** (a recusa some quando ele já leu o conteúdo, na mensagem 2). Se persistir, use o **Plano B** acima |
| Skill `/notebooklm` não aparece (mas o comando `notebooklm --help` funciona) | É **opcional** — as skills do toolkit usam o comando de terminal, não essa skill. Se quiser tê-la, peça ao Claude: "rode notebooklm skill install" e feche e reabra o app |
| NotebookLM responde "sem acesso" | Solicite acesso em https://notebooks-aft.vercel.app e aguarde a liberação do mantenedor |
| NotebookLM parou ("authentication expired") | A sessão expira de tempos em tempos. Peça ao Claude "reconecte o notebooklm" — ele reabre o login, sem terminal |

Dúvidas? Fale com o Ricardo (SRTE/GO).
