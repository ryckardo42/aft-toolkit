---
name: aft-atualizar
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
- **Lista com commits** → atualize e guarde as mensagens para o resumo final:
  ```bash
  git pull origin main
  ```
  Use **sempre** fast-forward simples (sem rebase/merge manual). Se o `pull` falhar
  por mudanças locais não commitadas, **não descarte nada**: avise o AFT e pergunte
  como prosseguir (isso não deveria acontecer numa instalação normal, em que o AFT
  nunca edita os arquivos do repositório).

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
