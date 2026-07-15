---
name: aft-atualizar
model: sonnet
description: >
  Use SEMPRE que o Auditor-Fiscal do Trabalho (AFT) pedir para atualizar o AFT
  Toolkit. Acione com "/aft-atualizar", "atualize o toolkit", "atualize o aft
  toolkit", "atualizar o kit", "tem atualização?", "verificar atualizações",
  "buscar novidades do toolkit", "puxar a última versão". A skill confere DUAS
  fontes — o repositório https://github.com/ryckardo42/aft-toolkit (as skills) e
  o pacote https://github.com/teng-lin/notebooklm-py (o comando `notebooklm`) —,
  atualiza as que estiverem desatualizadas e, ao final, roda o /aft-doctor para
  confirmar que nada quebrou. Diferente do /aft-doctor (só diagnostica, nunca
  instala), esta skill É a que efetivamente baixa e instala as atualizações.
---

# aft-atualizar — Atualizar o AFT Toolkit (skills + notebooklm-py)
**AFT Toolkit**

## Objetivo

Um único comando para manter as duas peças do toolkit em dia: as **skills**
(este repositório) e o **comando `notebooklm`** (pacote de terceiro,
`teng-lin/notebooklm-py`, que as skills usam para consultar ementas). No final,
confirma que tudo continua funcionando com o `/aft-doctor`.

Tom: tranquilizador e direto. O AFT não precisa entender git nem pip — só saber
o que mudou e se precisa fazer algo (normalmente não).

## Passo 1 — Atualizar as skills (repositório do toolkit)

Na pasta das skills (você roda):

```bash
cd ~/.claude/skills
git fetch origin
git log HEAD..origin/main --oneline   # commits novos disponíveis
```

- **Lista vazia** → já está na última versão; informe isso e siga para o Passo 2.
- **Lista com commits** → **antes de baixar**, faça a varredura de segurança abaixo
  (Passo 1a). Só depois de ela passar, atualize e guarde as mensagens para o resumo
  final:
  ```bash
  git pull origin main
  ```
  Use **sempre** fast-forward simples (sem rebase/merge manual). Se o `pull` falhar
  por mudanças locais não commitadas, **não descarte nada**: avise o AFT e pergunte
  como prosseguir (isso não deveria acontecer numa instalação normal, em que o AFT
  nunca edita os arquivos do repositório).

### Passo 1a — Varredura de segurança do que está chegando (antes do pull)

Uma atualização de skills é **código de terceiro** entrando na máquina do AFT: roda com
acesso aos documentos e dados reais da fiscalização. Antes do `git pull`, confira o que
muda e varra o conteúdo que está chegando por sinais de adulteração (Unicode invisível,
cano para shell, `ANTHROPIC_BASE_URL`, exfiltração por rede). Você roda:

```bash
git diff --stat HEAD..origin/main                      # quais arquivos mudam
python ~/.claude/skills/_scripts/checar_diff.py        # varredura das linhas novas
```

- **Saída `✓` (nada suspeito)** → siga para o `git pull` normalmente.
- **Saída `⚠️` (sinais suspeitos)** → **NÃO dê o pull.** Mostre os achados ao AFT em
  linguagem simples, explique que a atualização traz algo fora do padrão e só prossiga
  se ele confirmar que a mudança é legítima (autor/commit conhecido). Na dúvida, não
  atualize: o toolkit antigo funcionando é melhor que um novo adulterado.

O `checar_diff.py` é um alarme: nunca bloqueia nem altera nada, só relata. Quem decide
seguir é sempre o AFT.

## Passo 2 — Atualizar o `notebooklm` (notebooklm-py)

Confira a versão instalada e a versão mais recente publicada (você roda):

```bash
notebooklm --version
```

```bash
curl -s https://pypi.org/pypi/notebooklm-py/json | python3 -c "import json,sys; print(json.load(sys.stdin)['info']['version'])"
```

- Se o `notebooklm --version` falhar ("comando não encontrado"), o pacote não está
  instalado — não é erro desta skill; apenas informe e siga (o `/notebooklm-login`
  ou o `/aft-setup` cuidam da instalação na próxima vez que forem usados).
- Se as duas versões forem **iguais**, informe que já está atualizado.
- Se a versão instalada for **mais antiga**, atualize automaticamente, sem perguntar
  (mantendo os mesmos extras usados na instalação original):
  ```bash
  pipx upgrade notebooklm-py
  ```
  Se o pacote não foi instalado via pipx (comando acima falha ou não muda nada),
  use o equivalente em pip:
  ```bash
  python -m pip install --user --upgrade "notebooklm-py[browser,cookies]"
  ```
  Depois confirme com `notebooklm --version` que a versão nova ficou ativa.

## Passo 2b — Oferecer a rotina diária do painel (só na primeira vez)

O toolkit ganhou a opção de o `/painel` se atualizar sozinho toda manhã (agendamento do
próprio sistema operacional — launchd/Agendador de Tarefas, zero tokens, sem abrir o
Claude Code). AFTs que instalaram o toolkit antes dessa novidade nunca foram perguntados.
Confira se já foi oferecida:

```bash
grep -q "rotina_painel" ~/Documents/AFT/aft-config.md && echo "ja_perguntado" || echo "nunca_perguntado"
```

- **`ja_perguntado`** → não pergunte de novo; siga para o Passo 3.
- **`nunca_perguntado`** → ofereça **uma única vez**, em uma frase: *"Novidade: o
  painel pode se atualizar sozinho toda manhã, sem você pedir — não gasta nada, é o
  próprio computador rodando um programinha. Quer ativar?"*
  - **Não** → grave `rotina_painel: ""` no front-matter do `aft-config.md` (só para não
    perguntar de novo nas próximas atualizações) e siga.
  - **Sim** → siga exatamente o Passo 7b do `/aft-setup` (mesmo script
    `instalar_rotina_painel.py`, mesmo `python_path`/pasta de OS ATIVAS já configurados)
    e grave `rotina_painel: "07:00"` (ou o horário escolhido) no `aft-config.md`.

## Passo 2c — Oferecer o painel interativo sempre ligado (só na primeira vez)

Mesma lógica do Passo 2b, para a novidade do **servidor interativo** (Passo 7c do
`/aft-setup` — controles do painel + sync do DET pela extensão Chrome). Confira:

```bash
grep -q "servidor_painel" ~/Documents/AFT/aft-config.md && echo "ja_perguntado" || echo "nunca_perguntado"
```

- **`ja_perguntado`** → não pergunte de novo; siga para o Passo 3.
- **`nunca_perguntado`** → ofereça **uma única vez**, em uma frase: *"Novidade: o painel
  agora pode ficar sempre ligado no seu computador (sobe sozinho ao ligar a máquina) — é
  o que permite marcar DET/pendência direto no painel e sincronizar notificações do DET
  automaticamente pela extensão do Chrome. Quer ativar?"*
  - **Não** → grave `servidor_painel: ""` no `aft-config.md` e siga.
  - **Sim** → siga exatamente o Passo 7c do `/aft-setup` (mesmo script
    `instalar_servidor_painel.py`, mesmo `python_path`/pasta de OS ATIVAS já
    configurados) e grave `servidor_painel: "ligado"` no `aft-config.md`.

## Passo 3 — Confirmar que nada quebrou (`/aft-doctor`)

Sempre rode ao final, mesmo se nada tiver sido atualizado no Passo 1/2 (serve
também para confirmar que o ambiente já estava certo):

```bash
python ~/.claude/skills/_scripts/aft_doctor.py
```

Traduza o resultado seguindo as regras do `/aft-doctor` (🟢/🟡/🔴, erros antes de
avisos). Se aparecer algum erro novo causado pela atualização, explique e oriente
a solução — não deixe o AFT com a sensação de que "atualizar" pode ter quebrado
algo sem explicação.

## Passo 4 — Resumo final ao AFT

Uma mensagem só, juntando os três passos, por exemplo:

```
🔄 Atualização do AFT Toolkit

✅ Skills: 3 novidades baixadas
   • Nova skill /analise-acidente
   • Apostila: nova seção sobre os modelos do Claude
   • Guard-rail de PII (checar_pii.py)

✅ notebooklm: atualizado de 0.6.0 → 0.7.2

🩺 Diagnóstico pós-atualização: tudo certo (4 ok, 0 avisos, 0 erros)
```

Se nada mudou em nenhuma das duas fontes, diga isso em uma frase e confirme o
diagnóstico — não é preciso alarde.

## Regras

- **Nunca** rode `git reset --hard`, `git checkout -- .` ou qualquer comando que
  descarte alterações locais sem perguntar antes — numa instalação normal isso
  nunca deveria ser necessário.
- A atualização do `notebooklm-py` é automática (sem pedir confirmação a cada
  vez), mas sempre **reporte** a troca de versão — o AFT precisa saber o que
  mudou, mesmo sem precisar agir.
- Esta skill **instala/atualiza**; o `/aft-doctor` (chamado no Passo 3) **só
  diagnostica**. Não pule o Passo 3: é o que garante que a atualização não
  deixou nada quebrado para o AFT descobrir sozinho em campo.
- **Skills próprias do AFT (`minha-*`) são preservadas.** O `git pull` fast-forward
  nunca toca nelas (namespace reservado + `.gitignore`). Se o AFT tiver alguma, o Passo
  3 (`/aft-doctor`) as lista como protegidas — mencione isso no resumo para tranquilizá-lo
  ("suas skills próprias continuam intactas"). Nunca rode comando que possa apagá-las.
