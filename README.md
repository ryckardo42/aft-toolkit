# aft-toolkit

Skills e ferramentas de IA para Auditores Fiscais do Trabalho (AFT), compatíveis com **Claude Code CLI** e **claude.ai**.

---

## Skills disponíveis

| Skill | Descrição |
|---|---|
| [PGR-analise](PGR-analise/SKILL.md) | Análise de PGR sob a ótica da NR-01 — identifica irregularidades nas 7 ementas e gera autos de infração |

---

## Como instalar (Claude Code CLI)

```bash
git clone https://github.com/ryckardo42/aft-toolkit.git ~/.claude/skills/aft-toolkit
```

> As skills ficam disponíveis automaticamente na próxima conversa. Use `/PGR-analise`, `/nome-da-skill`, etc.

## Como atualizar

```bash
cd ~/.claude/skills/aft-toolkit && git pull
```

---

## Como usar no claude.ai (sem Claude Code)

1. Abra o arquivo `SKILL.md` da skill desejada
2. Copie o conteúdo
3. No claude.ai, crie um **Projeto** e cole nas instruções do projeto

---

## Estrutura do repositório

```
aft-toolkit/
├── README.md
├── PGR-analise/
│   └── SKILL.md
└── (outras skills em breve)
```

---

## Contribuindo

Sugestões de novas skills ou melhorias: abra uma Issue ou entre em contato com o mantenedor.
