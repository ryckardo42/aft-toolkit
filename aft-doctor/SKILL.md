---
name: aft-doctor
model: sonnet
effort: low
allowed-tools: Read, Glob, Grep, Bash, AskUserQuestion
description: >
  Use quando o AFT quiser checar se o AFT Toolkit está instalado e
  funcionando, ou descobrir o que falta quando algo não funciona. Acione com
  "/aft-doctor", "verificar instalacao", "esta tudo certo?", "diagnostico",
  "o toolkit esta funcionando?", "testar instalacao", "checar o toolkit",
  "nao esta funcionando", "as skills nao aparecem". Só diagnostica: não
  instala nem altera arquivos — quem instala é o /aft-atualizar.
---

# aft-doctor — Verificacao pos-instalacao do AFT Toolkit
**AFT Toolkit**

## Objetivo

Dar ao colega, em 10 segundos, a resposta para "esta tudo certo?". E o primeiro
comando a rodar logo depois de instalar (ou sempre que algo der errado). Confere os
pre-requisitos e a configuracao e diz, sem jargao, o que falta e como resolver.

Tom: tranquilizador. O publico pode estar inseguro por ser a primeira vez. Nunca
assuste com termos tecnicos — traduza tudo.

## Passo 1 — Rodar a verificacao

```bash
python ~/.claude/skills/_scripts/aft_doctor.py
```

> Se `python` nao for encontrado, tente `python3`. Se nenhum dos dois rodar, esse ja
> e o primeiro problema: o Python nao esta instalado/no PATH — oriente a rodar
> `/aft-setup` (ele instala o Python) ou a fechar e reabrir o Claude Code se acabou
> de instalar.

O script imprime um relatorio legivel e, na ultima linha, um JSON prefixado com
`JSON:` no formato:

```json
{ "resumo": {"ok": N, "avisos": M, "erros": K},
  "checks": [ {"titulo": "...", "status": "ok|aviso|erro", "detalhe": "...", "dica": "..."} ] }
```

## Passo 2 — Traduzir o resultado para o AFT

A partir do JSON, responda de forma clara e acolhedora. Regra de ouro:

- **Se `erros` = 0 e `avisos` = 0** → diga que esta tudo pronto e relembre o comeco do
  fluxo (`/aft-nova-auditoria` para cadastrar uma OS, `/aft-painel` para ver os prazos).
- **Se houver `erros` (vermelho)** → liste-os PRIMEIRO, com a solucao de cada um (campo
  `dica`). Sao itens que impedem o toolkit de funcionar (ex.: Python ausente, skills
  nao descobertas, config incompleta).
- **Se houver so `avisos` (amarelo)** → explique que o nucleo funciona, mas alguns
  itens opcionais ou de configuracao faltam, e mostre a dica de cada um. O mais comum:
  o AFT ainda nao rodou `/aft-setup` (faltam perfil, pasta de trabalho, aft-config,
  bibliotecas) — nesse caso, sugira rodar `/aft-setup` agora, que resolve vários de
  uma vez.

Use simbolos para leitura rapida: 🟢 (ok), 🟡 (aviso), 🔴 (erro). Exemplo:

```
🩺 Diagnostico do AFT Toolkit — 4 ok, 2 avisos, 0 erros

🟢 Python, Git, skills instaladas, config do toolkit — tudo certo.

🟡 Pendencias (resolvem com 1 comando):
  • Perfil do auditor e pasta de trabalho ainda nao existem.
    -> Rode /aft-setup que eu configuro tudo isso.
  • Biblioteca pypdf faltando (so afeta /aft-autos-lavrados).
    -> O /aft-setup tambem instala.

Quer que eu rode o /aft-setup agora?
```

## Passo 3 — Oferecer a correcao (sem corrigir sozinho)

Esta skill **so diagnostica**. Para resolver, encaminhe para o lugar certo:

- Faltam perfil / pasta / aft-config / bibliotecas → **`/aft-setup`**.
- Skills nao descobertas (estao aninhadas, ex.: `~/.claude/skills/aft-toolkit/...`) →
  explique que o repositorio precisa SER a pasta `~/.claude/skills` e ofereca reinstalar
  com o prompt do COMO-INSTALAR (Passo 3).
- Config do toolkit incompleta → ofereca "Atualize o AFT Toolkit" (`/aft-atualizar`) ou reclone.
- **"Pasta de trabalho fora da Documentos"** (instalacao anterior a 22/07/2026 no Windows:
  os dados foram para `~/Documents/AFT`, mas a Documentos real e a do OneDrive) →
  explique em uma frase que as fiscalizacoes existem e funcionam, so nao aparecem quando
  ele abre "Documentos" no Explorer, e **pergunte** se quer mudar de lugar. Se sim:
  1. peca para **fechar o app do Claude** (o vigia de sessoes e o servidor do painel
     seguram arquivos dentro da pasta e impedem a mudanca no Windows);
  2. rode `python "<python_path>" ~/.claude/skills/_scripts/pasta_aft.py --mover`;
  3. mostre o `pasta_aft` do JSON como o novo lugar. Nada e apagado, e o `path_windows`
     do aft-config.md e atualizado sozinho.
  Se ele preferir deixar como esta, tudo continua funcionando — nao insista.
- **O AFT quer a pasta de trabalho em OUTRO lugar** (HD externo, nuvem, outro disco;
  ex.: "quero minhas OS no HD externo", "posso mudar a pasta AFT de lugar?") → pode:
  1. peca para **fechar o app do Claude** (mesmo motivo do item acima);
  2. rode, com o caminho que ele indicar — **a pasta que vai CONTER `OS ATIVAS`**, nao a
     `OS ATIVAS` em si (o script recusa e explica se ele apontar a subpasta):
     ```bash
     python "<python_path>" ~/.claude/skills/_scripts/pasta_aft.py --definir "<caminho>" --mover
     ```
     Sem `--mover`, so passa a apontar para la (util se ele mesmo ja moveu os arquivos).
     O script **nunca sobrescreve**: se o destino ja tiver dados, recusa e explica.
  3. a escolha fica gravada em `~/.claude/aft-pasta.txt` — **fora** do repositorio das
     skills, entao `/aft-atualizar` nunca a desfaz. Diga isso ao AFT: ele nao vai
     precisar reconfigurar a cada atualizacao.
  4. **Reinstale os servicos** que guardam o caminho antigo por dentro (rotina do painel
     e servidor do painel) — ver "Servicos apontando para a pasta antiga" abaixo.
  Para voltar ao automatico: `pasta_aft.py --soltar`.
- **"Servicos apontando para a pasta antiga"** (aviso do doctor apos uma mudanca de
  pasta) → a rotina e o servidor do painel guardam o caminho de quando foram instalados.
  Ofereca reinstalar os dois com o caminho novo — `<OS_ATIVAS>` abaixo e o campo
  `os_ativas` do JSON do proprio diagnostico, nunca um caminho presumido:
  ```bash
  python "<python_path>" ~/.claude/skills/_scripts/instalar_rotina_painel.py instalar "<python_path>" "<OS_ATIVAS>"
  python "<python_path>" ~/.claude/skills/_scripts/instalar_servidor_painel.py instalar "<python_path>" "<OS_ATIVAS>"
  ```
  O vigia de sessoes nao precisa: ele resolve a pasta a cada execucao.
- **"Painel interativo (servidor)" acusando pasta DIFERENTE** (`o servidor no ar esta
  servindo X, mas a sua pasta de OS agora e Y`) → um servidor antigo sobreviveu a uma
  mudanca de pasta e continua segurando a porta 8347, servindo dados da pasta de antes.
  Ofereca reinstalar o servidor (o comando acima), que derruba o antigo antes de subir
  o novo.
- **"Conversor de PDF" ausente** → nao e defeito: os documentos `.docx` continuam sendo
  gerados. So a versao em PDF sai na mao (abrir o `.docx` e usar Arquivo > Salvar
  como... > PDF). Se o AFT quiser automatizar, o LibreOffice e gratuito e o toolkit
  passa a usa-lo sozinho assim que ele existir. No Windows com Word instalado esse
  check ja aparece como ok.
- Frontmatter de skill quebrado ou modelo pinado indisponivel → ofereca `/aft-atualizar`;
  se ja estiver atualizado e o problema persistir, oriente a avisar o mantenedor
  citando a mensagem do check (pode ser modelo descontinuado ou limitacao do plano).
- **Qualquer defeito que pareca do proprio toolkit** (e nao da maquina do AFT) → ofereca
  a skill `/aft-erro`, que monta o ticket de correcao para ele encaminhar ao mantenedor.

So execute uma correcao se o AFT pedir. Nunca instale nada silenciosamente neste fluxo.

## Regras

- **Nao altera arquivos.** A skill nao instala, nao baixa, nao edita nem apaga nada.
  Isso e garantido tecnicamente pelo `allowed-tools` do frontmatter: as ferramentas de
  escrita (Write/Edit) ficam indisponiveis enquanto a skill roda. **Unica excecao:** o
  proprio `aft_doctor.py` cria a pasta de trabalho (`AFT/OS ATIVAS` e `OS ARQUIVADAS`)
  quando ela falta — criar diretorio vazio e seguro, idempotente, e sem ela nada do
  toolkit funciona. Mover uma pasta que ja tem dados (`--mover`) NUNCA e automatico:
  so com o AFT pedindo. (Unica ressalva: o check "teste dos modelos pinados" faz UMA chamada
  minima ao Claude por modelo datado, para confirmar que a conta do AFT tem acesso —
  gasta uma resposta curta de cota e nao altera nada.)
- O codigo `[ERRO]` (saida != 0) significa que ha pelo menos um item essencial faltando;
  trate sempre os erros antes dos avisos.
- Rodar fora de `~/.claude/skills` (ex.: testando no repositorio clonado em outra pasta)
  gera um aviso de "skills fora do lugar" — isso e esperado nesse caso e nao e problema
  na instalacao real do colega.
