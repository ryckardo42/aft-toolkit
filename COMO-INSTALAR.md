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

O Claude Code é um assistente que executa comandos no seu computador, **sempre pedindo a sua permissão antes**. Então, em vez de instalar programa por programa, cole a mensagem abaixo na conversa e aperte Enter:

```
Prepare este computador para o AFT Toolkit. Faça nesta ordem, me explicando cada passo:
1. Confirme que o Git está instalado e funcionando (git --version).
2. Verifique se o Python 3 está instalado e funcionando no terminal; se não, instale com winget (pacote Python.Python.3.12).
3. Instale a ferramenta do NotebookLM a partir do repositório https://github.com/teng-lin/notebooklm-py - pacote notebooklm-py com os extras browser e cookies (use: pipx install "notebooklm-py[browser,cookies]"; se não houver pipx, instale o pipx antes). Ao final, confirme que o comando notebooklm responde (notebooklm --help). Em seguida rode notebooklm skill install para registrar a skill /notebooklm no Claude Code (o pip/pipx só instala o comando de terminal; sem esse passo extra a skill /notebooklm não aparece, mesmo com o comando funcionando). Não é preciso baixar navegador nenhum nem o Visual C++: o login usa o Edge/Chrome que já existe no computador.
4. Baixe o repositório https://github.com/ryckardo42/aft-toolkit.git fazendo dele a própria pasta de skills: git clone https://github.com/ryckardo42/aft-toolkit.git ~/.claude/skills. Se a pasta ~/.claude/skills já existir com conteúdo, clone numa pasta temporária e mova todo o conteúdo do repositório (incluindo a pasta oculta .git) para dentro dela.
5. Confirme que as skills ficaram diretamente em ~/.claude/skills (deve existir, por exemplo, ~/.claude/skills/aft-setup/SKILL.md — e NÃO ~/.claude/skills/aft-toolkit/aft-setup), liste-as e me diga se preciso reiniciar o aplicativo.
```

Enquanto o Claude trabalha, ele vai pedir permissão para cada comando — basta clicar em **Permitir**. Isso é normal e desejável: nada roda no seu computador sem o seu OK.

**O que ele está instalando?**
- **Python** — roda os scripts locais do toolkit: conversão de fotos em PDF, geração do arquivo do Sistema Auditor e validação de arquivos de ponto.
- **notebooklm** — a ferramenta que consulta os ementários no NotebookLM para achar o código da ementa sozinho. Ela já fica instalada aqui (comando de terminal + skill `/notebooklm`); o login (na sua conta Google) o Claude conduz para você no passo "Recomendado — Ative o NotebookLM" abaixo, sem terminal.

---

## Passo 4 — Reinicie e configure

1. **Feche e reabra** o aplicativo Claude (para ele reconhecer as skills novas e o Git).
2. Numa conversa nova do `</> Code` (pasta da sessão: **Documentos**), digite:
   ```
   /aft-setup
   ```

A skill de configuração cria a pasta `Documentos\AFT`, pergunta seu nome, CIF e os dados da sua UORG, e instala as bibliotecas Python necessárias. Esses dados entram automaticamente nos arquivos do Sistema Auditor — você nunca mais digita.

---

## Recomendado — Ative o NotebookLM

Com o NotebookLM ativo, as skills encontram o **código da ementa sozinhas**. A ferramenta `notebooklm` já foi instalada no Passo 3. Você **não precisa do terminal**: o Claude faz a conexão por você.

1. Entre em **https://notebooks-aft.vercel.app** com sua conta Google e solicite acesso; aguarde a liberação pelo mantenedor.
2. Na conversa do `</> Code`, digite **`/notebooklm-login`** (ou peça "conecte o notebooklm"). O Claude tenta conectar sozinho pelos cookies do navegador e, se precisar, **abre uma janela do Edge** onde você só faz login na sua conta Google — ele salva a conexão automaticamente. O `/aft-setup` também conduz esse passo.
3. Se um dia a consulta de ementa parar de funcionar ("authentication expired"), é só pedir "reconecte o notebooklm" — sem mexer em terminal.

Sem o NotebookLM, tudo continua funcionando — as skills pedem o código da ementa ou indicam o ementário no Google Drive.

---

## Pronto! Experimente

| Situação | Digite |
|---|---|
| Cadastrar uma auditoria nova | `/nova-os` |
| Ver suas OS e prazos de DET | `/painel` |
| Voltou de uma inspeção | `/inspecao-fisica` e narre o que viu |
| Quer redigir os autos | `/inspecao-inicial` |
| Trabalhador sem registro | `/registro` |
| Analisar um PGR | `/PGR-analise` |
| Empresa não entregou documentos do DET | `/det-630` |
| Interdição/embargo | `/aft-rt-rgi` |
| Analisar AFD/AEJ/atestado de ponto | `/jornada-analise` |
| Gerar o TXT do Sistema Auditor | `/gera-ai` |
| Relatório final | `/sfitweb-rel` |

## Como receber atualizações

Peça ao Claude, numa conversa qualquer: **"Atualize o AFT Toolkit"** (ou `/aft-atualizar`). Ele atualiza as skills (`git pull`), confere se o comando `notebooklm` tem versão nova e atualiza sozinho se houver, e confirma no final com o `/aft-doctor` que nada quebrou — mostrando o que mudou em cada parte.

---

## Plano B — instalação manual

Só se o Passo 3 falhar (computador sem winget, rede corporativa bloqueando):

- **Python**: baixe em https://www.python.org/downloads/ e, na primeira tela do instalador, **marque "Add Python to PATH"**.
- **Toolkit**: abra o Git Bash (menu Iniciar) e rode:
  ```bash
  git clone https://github.com/ryckardo42/aft-toolkit.git ~/.claude/skills
  ```

## Problemas comuns

Regra geral: **descreva o problema ao próprio Claude** no `</> Code` ("o comando X deu este erro: ...") — ele diagnostica e corrige. **Você nunca precisa abrir um terminal:** quem digita comando é sempre o Claude.

| Sintoma | Solução |
|---|---|
| "Git is required for local sessions" | Instale o Git (Passo 2) e feche o app de verdade: ícone do Claude na bandeja → Sair; reabra. Se persistir, reinicie o computador |
| Python "não encontrado" | Peça ao Claude: "instale o Python com winget". Se a rede bloquear, plano B manual acima e reinicie o app |
| Skill não aparece com `/` | Feche e reabra o Claude Code. Se persistir, peça a ele: "as skills estão diretamente em ~/.claude/skills (ex.: ~/.claude/skills/aft-setup)? Se estiverem dentro de uma subpasta aft-toolkit, mova todo o conteúdo um nível acima" |
| NotebookLM não conecta / "command not found" / pede login | Peça ao Claude: "conecte o notebooklm" (skill `/notebooklm-login`). Ele instala o que faltar e abre a janela de login do Edge — você só entra na sua conta Google |
| Skill `/notebooklm` não aparece (mas o comando `notebooklm --help` funciona) | Peça ao Claude: "rode notebooklm skill install" e depois feche e reabra o app. O pip/pipx instala só o comando de terminal — a skill precisa desse passo extra |
| NotebookLM responde "sem acesso" | Solicite acesso em https://notebooks-aft.vercel.app e aguarde a liberação do mantenedor |
| NotebookLM parou ("authentication expired") | A sessão expira de tempos em tempos. Peça ao Claude "reconecte o notebooklm" — ele reabre o login, sem terminal |

Dúvidas? Fale com o Ricardo (SRTE/GO).
