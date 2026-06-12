# Como instalar o AFT Toolkit no seu Claude Code (Windows)

Guia para quem nunca usou o Claude Code. Tempo total: ~20 minutos.

---

## Passo 0 — Instale o Claude Code (app desktop)

1. Baixe o **Claude Desktop / Claude Code** em https://claude.com/claude-code (versão Windows).
2. Instale e entre com a sua conta Claude (a mesma do claude.ai). É preciso um plano que inclua o Claude Code (Pro ou superior).
3. Abra o aplicativo uma vez para concluir a configuração inicial.

---

## Passo 1 — Instale o Git

O Git é o programa que baixa (e depois atualiza) o toolkit.

1. Baixe em https://git-scm.com/download/win e instale com as opções padrão (só clicar "Next").
2. Para testar: aperte `Win + R`, digite `cmd`, Enter, e digite:
   ```
   git --version
   ```
   Se aparecer `git version 2.x.x`, está pronto.

---

## Passo 2 — Instale o Python

O Python roda os scripts do toolkit (conversão de fotos, geração do arquivo do Sistema Auditor, validação de arquivos de ponto).

1. Baixe em https://www.python.org/downloads/ (botão amarelo "Download Python 3.x").
2. **IMPORTANTE:** na primeira tela do instalador, **marque a caixa "Add Python to PATH"** antes de clicar em Install.
3. Para testar, no `cmd`:
   ```
   python --version
   ```

---

## Passo 3 — Instale o toolkit

Abra o **Git Bash** (foi instalado junto com o Git — procure "Git Bash" no menu Iniciar), cole o comando abaixo e aperte Enter:

```bash
git clone https://github.com/ryckardo42/aft-toolkit.git ~/.claude/skills/aft-toolkit
```

Vai aparecer `Cloning into...` e voltar para a linha normal. Pronto, instalado.

---

## Passo 4 — Configure (uma única vez)

1. Abra o **Claude Code** e inicie uma conversa nova.
2. Digite:
   ```
   /aft-setup
   ```
3. Siga as perguntas: ele cria a pasta `Documentos\AFT`, pede seu nome, CIF e dados da sua UORG, e instala as bibliotecas necessárias. Esses dados entram automaticamente nos arquivos do Sistema Auditor — você nunca mais digita.

---

## Passo 5 (recomendado) — Ative o NotebookLM

Com o NotebookLM ativo, as skills encontram o **código da ementa sozinhas**.

1. Entre em **https://notebooks-aft.vercel.app** com sua conta Google e solicite acesso.
2. Aguarde a liberação (o mantenedor aprova os pedidos).
3. O `/aft-setup` (passo 7 dele) instala e autentica o CLI — ou rode no Git Bash:
   ```bash
   pip install notebooklm-py
   notebooklm login
   ```

Sem o NotebookLM, tudo continua funcionando — as skills pedem o código da ementa ou indicam o ementário no Google Drive.

---

## Passo 6 — Use!

Numa conversa do Claude Code, experimente:

| Situação | Digite |
|---|---|
| Voltou de uma inspeção | `/inspecao-fisica` e narre o que viu |
| Quer redigir os autos | `/inspecao-inicial` |
| Trabalhador sem registro | `/registro` |
| Analisar um PGR | `/PGR-analise` |
| Empresa não entregou documentos do DET | `/det-630` |
| Interdição/embargo | `/aft-rt-rgi` |
| Analisar AFD/AEJ/atestado de ponto | `/jornada-analise` |
| Gerar o TXT do Sistema Auditor | `/gera-ai` |
| Relatório final | `/sfitweb-rel` |

---

## Como receber atualizações

Quando houver novidades no toolkit, abra o Git Bash e rode:

```bash
cd ~/.claude/skills/aft-toolkit && git pull
```

---

## Problemas comuns

| Sintoma | Solução |
|---|---|
| `git: command not found` | Instale o Git (Passo 1) e feche/reabra o terminal |
| `python: command not found` | Reinstale o Python marcando "Add Python to PATH" |
| Skill não aparece com `/` | Feche e reabra o Claude Code; confira se a pasta `~/.claude/skills/aft-toolkit` existe |
| `notebooklm: command not found` | `pip install notebooklm-py` no Git Bash |
| NotebookLM responde "sem acesso" | Solicite acesso em https://notebooks-aft.vercel.app e aguarde liberação |

Dúvidas? Fale com o Ricardo (SRTE/GO).
