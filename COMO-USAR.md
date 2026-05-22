# Como instalar a skill PGR-analise no seu Claude

### O que você vai precisar
- **Claude Code** instalado no seu computador
- **Git** instalado (provavelmente já está — veja abaixo como testar)

---

### Passo 1 — Verifique se o Git está instalado

Abra o terminal do seu computador:
- **Mac**: pressione `Cmd + Espaço`, digite `Terminal` e aperte Enter
- **Windows**: pressione `Win + R`, digite `cmd` e aperte Enter

Cole o comando abaixo e aperte Enter:
```
git --version
```

Se aparecer algo como `git version 2.x.x`, está tudo certo. Se aparecer erro, baixe o Git em [git-scm.com](https://git-scm.com) e instale.

---

### Passo 2 — Instale a skill

Com o terminal aberto, cole o comando abaixo e aperte Enter:

```bash
git clone https://github.com/ryckardo42/aft-toolkit.git ~/.claude/skills/aft-toolkit
```

Aguarde terminar. Vai aparecer algo como `Cloning into...` e depois voltar para a linha normal. Pronto, instalado.

---

### Passo 3 — Use a skill

Abra uma nova conversa no Claude Code e digite:

```
/PGR-analise
```

A skill vai se apresentar e pedir o PGR para analisar.

---

### Como receber atualizações

Sempre que o Ricardo adicionar novas skills ou melhorias, você atualiza com um único comando no terminal:

```bash
cd ~/.claude/skills/aft-toolkit && git pull
```

---

Dúvidas? Fale com Ricardo.
