---
name: sessoes-os
model: sonnet
description: >
  Use este skill quando o Auditor-Fiscal do Trabalho (AFT) quiser conferir, forçar ou
  desfazer a sincronização das sessões por empresa na barra lateral do app (grupo
  "OS ATIVAS"). Acione com "/sessoes-os", "verifica as sessões", "cria as sessões das
  minhas auditorias", "quero as sessões agora", "desfaz as sessões", "instala/remove o
  vigia de sessões". IMPORTANTE: a criação de sessões é AUTOMÁTICA — o vigia de sessões
  (sessoes_os.py --vigia, serviço instalado por padrão pelo /aft-setup e /aft-atualizar)
  aplica sozinho as pendências toda vez que o app do Claude fecha: cada pasta de OS ATIVAS
  ganha sessão com o nome da empresa no grupo "OS ATIVAS", com vínculo sessao_claude no
  memory.md. As sessões novas simplesmente aparecem na próxima abertura do app — nenhuma
  pergunta, nenhum passo manual. Esta skill serve para os casos à margem do automático:
  conferir o estado (--status), aplicar AGORA sem esperar o próximo fechamento do app
  (modo pontual), desfazer tudo (--desfazer) e instalar/remover o serviço do vigia.
---

# sessoes-os — sessões por auditoria, automáticas, no grupo "OS ATIVAS"
**AFT Toolkit**

## Como funciona (o normal é automático)

Cada empresa fiscalizada tem a própria sessão de chat na barra lateral, no grupo
**"OS ATIVAS"** — e isso acontece **sozinho**. O **vigia de sessões** é um serviço do
sistema (instalado por padrão) que observa as pastas de `OS ATIVAS/` e, toda vez que o
app do Claude é fechado, aplica o que estiver pendente: cria a sessão de quem não tem
(título = empresa, pasta de trabalho = pasta da OS), coloca no grupo e grava o vínculo
`sessao_claude:` no memory.md. **Na próxima abertura do app, as sessões estão lá.**

O AFT não precisa fazer nada: criou OS nova (`/nova-os`), organizou um lote
(`/organiza-os`), copiou uma pasta à mão — o vigia cuida, no próximo ciclo natural de
fechar/abrir o app.

**Briefing automático da sessão:** o vigia também mantém um `CLAUDE.md` de contexto em
cada pasta de OS (esse independe do app estar aberto — é criado em minutos). É ele que
faz a sessão da empresa "saber quem é" já na primeira mensagem: ler o `memory.md` antes
de tudo, usar as skills do toolkit, entender que "atualizar o card/painel/datas" =
registrar na ficha, classificar documentos jogados na conversa e respeitar as regras de
privacidade. Nunca sobrescreve um `CLAUDE.md` que o AFT tenha personalizado.

> **Aviso honesto:** o app não tem API oficial para sessões/grupos; o vigia escreve no
> armazenamento interno do app, sempre com o app FECHADO (por isso o "próximo
> fechamento"), com backup automático antes e `--desfazer` completo. Se uma atualização
> do app mudar o formato interno, ele aborta sem tocar em nada e registra no log.

## Quando esta skill entra (exceções ao automático)

### "Verifica as sessões" — conferência

```
python3 ~/.claude/skills/_scripts/sessoes_os.py --status
```

Mostre o resultado em linguagem simples (a linha `JSON:` tem o resumo). Se houver
pendências, explique: *"serão aplicadas sozinhas na próxima vez que você fechar o app"*.
Confira também o serviço: `python3 ~/.claude/skills/_scripts/instalar_vigia_sessoes.py
status` — se não estiver instalado, instale sem perguntar (`instalar <python_path>`).
O histórico do vigia fica em `~/Documents/AFT/.sessoes-os.log`.

### "Quero as sessões AGORA" — sem esperar o próximo fechamento

Dispare o aplicador pontual desacoplado e avise que é só fechar o app:

```
python3 -c "import subprocess,os; subprocess.Popen(['python3', os.path.expanduser('~/.claude/skills/_scripts/sessoes_os.py'), '--aplicar'], start_new_session=True, stdout=open(os.devnull,'wb'), stderr=subprocess.STDOUT)"
```

> Feche o app do Claude (Cmd+Q no Mac) — ele aplica e REABRE o app sozinho com tudo
> montado.

(É o mesmo motor do vigia; a diferença é que o modo pontual reabre o app para o AFT.)

### "Desfaz tudo"

```
python3 ~/.claude/skills/_scripts/sessoes_os.py --desfazer
```

Restaura o backup do config e remove TODAS as sessões que o toolkit criou (o manifesto é
acumulativo). Também espera o app fechar. Para desligar o automático de vez:
`instalar_vigia_sessoes.py remover`.

## Regras

- **Reaproveitar, nunca duplicar**: sessão existente cujo título case com a empresa é
  vinculada e agrupada.
- O vínculo `sessao_claude:` no memory.md é o que permite ao Claude rotear conversas para
  a sessão certa (regra do perfil do auditor).
- OS arquivada: o vigia NÃO apaga a sessão; o Claude oferece arquivá-la (regra do
  perfil), e o app pede a confirmação final.
- Windows: o vigia roda como Tarefa Agendada ("AFT Sessoes - Vigia"); macOS: LaunchAgent
  (`br.aft.sessoes-vigia`).
- **O grupo é sincronizado pela CONTA claude.ai (servidor), não é local.** Um grupo
  criado num Mac aparece no Windows e vice-versa. **Descoberta de campo (2026-07-21):** ao
  iniciar, o app baixa a lista de grupos do servidor e SOBRESCREVE qualquer gravação
  local — testado e confirmado que ele reescreve até o **Local Storage (leveldb)** poucos
  segundos após abrir, apagando o grupo que o script tinha gravado com o app fechado.
  Conclusão: **criar o grupo por arquivo NÃO persiste nesta versão** (nem via
  `claude_desktop_config.json`, nem via leveldb). O grupo só gruda se for criado pela
  **interface do app** (que envia ao servidor). As SESSÕES, por serem arquivos locais,
  persistem sem problema — o que falha é só a caixa visual do grupo.
- **Interruptor do agrupamento:** se existir o arquivo `~/Documents/AFT/.sessoes-sem-grupo`,
  o vigia CRIA sessões + contexto + vínculo mas NÃO tenta montar/gravar o grupo (evita
  backups e ruído inúteis, dado o parágrafo acima). Para religar, apague o arquivo. O
  `--status` mostra "agrupamento DESLIGADO" e o JSON traz `agrupamento_ligado: false`.
  Nesse modo, o AFT monta o grupo "OS ATIVAS" uma vez pela interface (arrastando as
  sessões) e aí sincroniza para sempre, inclusive para as outras máquinas.

## Windows — particularidades (aprendidas em campo)

- **App da Microsoft Store (MSIX)**: o `%APPDATA%\Claude` que o app (e processos filhos
  dele) enxerga é **virtualizado**; no disco real os dados ficam em
  `%LOCALAPPDATA%\Packages\Claude_<id>\LocalCache\Roaming\Claude`. O script detecta e
  prefere o caminho real — obrigatório para o vigia/Tarefa Agendada, que roda fora do
  contêiner e nem vê o caminho virtual.
- **Nome de processo**: tanto o app desktop quanto o CLI se chamam `claude.exe`
  (minúsculo). O script distingue o app pelo caminho do executável
  (`WindowsApps\Claude_...` na Store; `AnthropicClaude` no instalador clássico).
- **Reabertura**: app da Store não tem `.exe` fixo para `os.startfile`; lança-se pelo
  AUMID derivado do próprio caminho do pacote (`Packages\<família>\...` →
  `shell:AppsFolder\<família>!Claude`), sem depender de `Get-StartApps` (que falha em
  contexto não interativo, como a Tarefa Agendada do vigia).
- **Janela piscando**: todo `subprocess` de console (`powershell`, `tasklist`, `pip`) usa
  `creationflags=CREATE_NO_WINDOW`. Sem isso, cada ciclo do vigia (a cada 20-60s) fazia
  piscar uma janela de terminal — muito visível rodando em loop permanente.
- **Console cp1252**: o script reconfigura o stdout para UTF-8 com `errors=replace`
  (senão acentos/setas derrubam o script com `UnicodeEncodeError`); sob `pythonw.exe`
  (como o vigia roda) `sys.stdout` é `None`, então todo `print`/log está em `try/except`.

## Solução de problemas

| Sintoma | O que fazer |
|---|---|
| "Sessão não encontrada no disco" ao abrir uma sessão nova | **Normal e esperado** para empresa que nunca teve conversa: a sessão nasce vazia e o histórico só é criado na primeira mensagem. Basta enviar a primeira mensagem. NÃO clique em "Apagar" (o vigia a recriaria) |
| Criei uma OS e a sessão "não apareceu" | Ela aparece na próxima vez que o app for fechado e reaberto (o vigia só escreve com o app fechado). Sem paciência? Fluxo "quero AGORA" acima |
| A sessão da empresa "não sabia de nada" na 1ª mensagem | Falta o `CLAUDE.md` de contexto na pasta da OS (o vigia cria em minutos; force com `sessoes_os.py --contexto`). Conversas JÁ iniciadas não recarregam o contexto — peça "leia o memory.md desta pasta" ou comece conversa nova na mesma sessão |
| Grupo/sessões nunca aparecem | `instalar_vigia_sessoes.py status` — se não instalado, instale; leia `~/Documents/AFT/.sessoes-os.log` |
| "estrutura do config não reconhecida" no log | O app mudou o formato interno numa atualização — rode /aft-atualizar; nada foi alterado |
| Quero voltar atrás | `--desfazer` (restaura backup e remove o que foi criado) + `instalar_vigia_sessoes.py remover` se quiser desligar o automático |
| Grupo "OS ATIVAS" some toda vez que o app reabre | Comportamento ESPERADO desta versão: os grupos vêm do servidor da conta e o app sobrescreve o estado local (JSON e leveldb) ao abrir. Não há como criar o grupo por arquivo. Solução: criar o grupo uma vez pela interface do app (arrastar as sessões), OU desligar o agrupamento (arquivo `.sessoes-sem-grupo`) e conviver com as sessões soltas |
| (Windows) `UnicodeEncodeError ... cp1252` no log | Script desatualizado sem o reconfigure de stdout — rode `/aft-atualizar` |
