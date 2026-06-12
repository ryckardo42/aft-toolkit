# Como instalar o AFT Toolkit no seu Claude Code (Windows)

Instalação em **3 passos** — quem digita comando é o Claude, não você. Tempo total: ~15 minutos.

---

## Passo 1 — Instale o aplicativo Claude

1. Baixe o **Claude para Windows** em https://claude.com/claude-code.
2. Instale e entre com a sua conta Claude (a mesma do claude.ai). É preciso um plano que inclua o Claude Code (Pro ou superior).
3. Dentro do aplicativo, abra a interface de código: o botão **`</> Code`**. É nela que tudo acontece daqui em diante.

---

## Passo 2 — Deixe o Claude instalar o resto

Ao iniciar uma conversa nova no `</> Code`, o Claude pede para você **escolher uma pasta para a sessão** (a pasta do computador em que ele vai trabalhar). Escolha a pasta **Documentos** (`C:\Users\seu-nome\Documents`). Depois da instalação, quando `Documentos\AFT` existir, prefira escolhê-la nas conversas do dia a dia.

O Claude Code é um assistente que executa comandos no seu computador, **sempre pedindo a sua permissão antes**. Então, em vez de instalar programa por programa, cole a mensagem abaixo na conversa e aperte Enter:

```
Prepare este computador para o AFT Toolkit. Faça nesta ordem, me explicando cada passo:
1. Verifique se o Git está instalado; se não estiver, instale com winget (pacote Git.Git).
2. Verifique se o Python 3 está instalado e funcionando no terminal; se não, instale com winget (pacote Python.Python.3.12).
3. Baixe o repositório https://github.com/ryckardo42/aft-toolkit.git para a pasta de skills do Claude Code (~/.claude/skills/aft-toolkit) usando git clone.
4. Confirme que a pasta foi criada, liste as skills instaladas e me diga se preciso reiniciar o aplicativo.
```

Enquanto o Claude trabalha, ele vai pedir permissão para cada comando — basta clicar em **Permitir**. Isso é normal e desejável: nada roda no seu computador sem o seu OK.

**O que ele está instalando?**
- **Git** — a ferramenta que baixa o toolkit e busca as atualizações futuras (nada de programação: é só o "downloader"). De quebra, traz o Git Bash, o terminal que o Claude Code prefere usar.
- **Python** — roda os scripts locais do toolkit: conversão de fotos em PDF, geração do arquivo do Sistema Auditor e validação de arquivos de ponto.

---

## Passo 3 — Reinicie e configure

1. **Feche e reabra** o aplicativo Claude (para ele reconhecer as skills novas e o Git).
2. Numa conversa nova do `</> Code` (pasta da sessão: **Documentos**), digite:
   ```
   /aft-setup
   ```

A skill de configuração cria a pasta `Documentos\AFT`, pergunta seu nome, CIF e os dados da sua UORG, e instala as bibliotecas Python necessárias. Esses dados entram automaticamente nos arquivos do Sistema Auditor — você nunca mais digita.

---

## Recomendado — Ative o NotebookLM

Com o NotebookLM ativo, as skills encontram o **código da ementa sozinhas**.

1. Entre em **https://notebooks-aft.vercel.app** com sua conta Google e solicite acesso.
2. Aguarde a liberação pelo mantenedor.
3. O próprio `/aft-setup` instala e autentica o programa do NotebookLM (o login abre no seu navegador, com a sua conta Google).

Sem o NotebookLM, tudo continua funcionando — as skills pedem o código da ementa ou indicam o ementário no Google Drive.

---

## Pronto! Experimente

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

## Como receber atualizações

Peça ao Claude, numa conversa qualquer: **"Atualize o AFT Toolkit"** (ele roda o `git pull` na pasta das skills e mostra o que mudou).

---

## Plano B — instalação manual

Só se o Passo 2 falhar (computador sem winget, rede corporativa bloqueando):

- **Git**: baixe em https://git-scm.com/download/win e instale com as opções padrão.
- **Python**: baixe em https://www.python.org/downloads/ e, na primeira tela do instalador, **marque "Add Python to PATH"**.
- **Toolkit**: abra o Git Bash (menu Iniciar) e rode:
  ```bash
  git clone https://github.com/ryckardo42/aft-toolkit.git ~/.claude/skills/aft-toolkit
  ```

## Problemas comuns

Regra geral: **descreva o problema ao próprio Claude** no `</> Code` ("o comando X deu este erro: ...") — ele diagnostica e corrige.

| Sintoma | Solução |
|---|---|
| Git ou Python "não encontrado" | Peça ao Claude: "instale o Git e o Python com winget". Se a rede bloquear, plano B manual acima e reinicie o app |
| Skill não aparece com `/` | Feche e reabra o Claude Code; peça a ele para confirmar se `~/.claude/skills/aft-toolkit` existe |
| `notebooklm: command not found` | Peça ao Claude: "instale o notebooklm-py com pip" |
| NotebookLM responde "sem acesso" | Solicite acesso em https://notebooks-aft.vercel.app e aguarde liberação |

Dúvidas? Fale com o Ricardo (SRTE/GO).
