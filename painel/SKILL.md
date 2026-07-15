---
name: painel
model: haiku
allowed-tools: Read, Glob, Grep, Bash, AskUserQuestion, Artifact
description: >
  Use SEMPRE que o Auditor-Fiscal do Trabalho (AFT) quiser um panorama das
  auditorias em andamento e os prazos de DET vencendo. Acione com /painel,
  "painel", "minhas auditorias", "minhas OS", "o que vence essa semana",
  "dashboard", "quadro das OS", "painel interativo". Varre os memory.md de
  OS ATIVAS/, detecta notificações DET não cadastradas e gera um painel.html
  autocontido: um CARD por OS colorido por urgência e, ao clicar, o detalhe —
  DETs, TODOS os autos lavrados (nº do AI, ementa, constatação), inspeção
  física, pendências e atividades. Com --scan, puxa os autos ao vivo do
  Sistema Auditor. Tem MODO INTERATIVO opcional (servir_painel.py,
  http://127.0.0.1:8347, 100% local): ações mecânicas nos cards — marcar DET
  respondida, resolver pendência, registrar atividade, status e
  embargo/interdição — gravadas no memory.md com backup, e botões que copiam
  comandos prontos para o Claude Code. Artifact só com consentimento.
  Aberto pelo arquivo (duplo-clique) continua somente leitura.
---

# painel — Dashboard local das auditorias (SISOS-lite)
**AFT Toolkit**

## Objetivo

Dar ao AFT, sem nenhum servidor ou nuvem, um dashboard de fiscalização: **cards das OS em
andamento** (coloridos pela urgência dos prazos de DET — perder um prazo é o erro mais
caro) e, ao clicar num card, **o detalhe completo da auditoria**: notificações DET com
estado, todos os autos de infração lavrados (número do AI, ementa, constatação, data),
autos substituídos, pendências e o registro de atividades. A fonte da verdade são os
arquivos `memory.md` e `autos-lavrados.md` de cada OS — esta skill apenas os lê e gera uma
página HTML. **Nunca escreve nos memory.md** (quem cadastra/atualiza é o `/nova-os` e as
demais skills).

## Passo 0 — Resolver a pasta das OS

- **Windows**: use o padrão do toolkit, `~/Documents/AFT/OS ATIVAS` — não pergunte.
- **macOS**: verifique se `~/Documents/AFT/aft-config.md` tem a linha `pasta_os: <caminho>`.
  - Se tiver, use-a sem perguntar.
  - Se não tiver, pergunte ao AFT qual pasta contém as OS ATIVAS (ofereça o padrão
    `~/Documents/AFT/OS ATIVAS` como sugestão) e **grave a resposta** como linha
    `pasta_os: <caminho>` no `aft-config.md`, para nunca mais perguntar.

## Passo 1 — Gerar o painel

Rode o gerador do toolkit (acrescente `--scan` se o AFT quiser os autos direto do Sistema
Auditor — ver Passo 1.1):

```bash
python ~/.claude/skills/_scripts/gerar_painel.py "<PASTA_OS_ATIVAS>"
```

> Sem argumento, o caminho das OS é `~/Documents/AFT/OS ATIVAS` e a saída é o
> `painel.html` na pasta acima das OS. Argumentos: `[PASTA_OS_ATIVAS] [SAIDA_HTML]
> [SAIDA_ARTIFACT] [--scan]`.

O script lê, de cada OS: o `memory.md` (dados, DETs, pendências, atividades — tolerante
aos dois esquemas em uso), o `autos-lavrados.md` (autos com número de AI e constatação,
gerado pela `/autos-lavrados`) e os PDFs de notificação DET ainda não registrados na
ficha. Imprime no stdout um JSON de resumo:

```json
{ "painel": "...painel.html", "artifact_html": null,
  "os_ativas": N, "os_encerradas_ocultas": E, "dets_vencidos": X, "dets_vencendo_7d": Y,
  "notificacoes_nao_cadastradas": Z, "autos_lavrados": A,
  "scan_ao_vivo": {"pedido": true|false, "os_com_scan_ok": K},
  "novas": [ {"empregador": "...", "arquivo": "....pdf", "codigo": "ABC...",
              "ciencia": "dd/mm/aaaa"|null, "prazo": "dd/mm/aaaa"|null,
              "data_arquivo": "dd/mm/aaaa"} ],
  "vencendo": [ {"empregador": "...", "prazo": "dd/mm/aaaa", "dias": D} ] }
```

### Passo 1.1 — `--scan` (autos ao vivo do Sistema Auditor)

Com `--scan`, o gerador chama o `scan_autos.py` (da `/autos-lavrados`) para cada OS com
CNPJ/CPF e mescla a lista fria de autos transmitidos (nº do AI, ementa, data — já
deduplicada da re-lavratura) com as constatações do `autos-lavrados.md`. Funciona no
Windows (pasta PRO padrão) e no Mac com Parallels (volume `/Volumes/*/SistemasAFT/…`).
**Degrada sozinho**: se a pasta PRO não estiver acessível (VM desligada, volume caído), a
OS usa o último `autos-lavrados.md` — o campo `scan_ao_vivo.os_com_scan_ok` do JSON diz
quantas OS tiveram scan de verdade. Nunca trate a degradação como erro; apenas informe.

## Passo 2 — Responder no chat

A partir do JSON, dê um resumo objetivo, **destacando o que precisa de ação**:

- Se houver `dets_vencidos > 0`: liste primeiro, com ênfase (estão atrasados).
- Depois os que vencem em ≤ 7 dias (`dias` entre 0 e 7).
- Se `notificacoes_nao_cadastradas > 0`: liste cada item de `novas` (empregador, arquivo,
  código e datas) e diga que essas notificações **não estão na ficha** — sugira cadastrar
  com `/nova-os` (ou editar o `memory.md` da OS). **Esta skill não cadastra nada.**
- Informe o total de OS ativas e de autos lavrados (e a fonte: scan ao vivo ou snapshot).
  Se `os_encerradas_ocultas > 0`, mencione em uma frase ("+ N encerrada(s) fora do
  painel — peça `/painel --todas` para ver todas").

Exemplo de resposta:
```
📊 Painel atualizado — N OS ativas · A autos lavrados

🔴 DET vencidos (ação imediata):
  • EMPRESA X — prazo 01/06/2026 (12 dias atrás)

🟠 Vencendo em até 7 dias:
  • EMPRESA Y — prazo 16/06/2026 (em 3 dias)

🔵 Notificação encontrada na pasta mas NÃO cadastrada:
  • EMPRESA Z — Notificação ABC123.pdf — código ABC123..., prazo 20/06/2026
    -> Quer cadastrar? Rode /nova-os (ou me peça para abrir a ficha).

Painel completo: <caminho do painel.html> (clique nos cards para o detalhe)
```

Se `os_ativas = 0`, diga que não há OS cadastradas e sugira `/nova-os`.

## Passo 3 — Oferecer abrir o painel

Ofereça abrir o `painel.html` no navegador (ele é autocontido, abre por duplo-clique):

```bash
# Windows (Git Bash):
start "" "<caminho do painel.html>"
# macOS:
open "<caminho do painel.html>"
```

Se o AFT preferir, ele mesmo abre o arquivo na pasta.

## Passo 3.5 — (Opcional) Modo interativo (servidor local)

Se o AFT pedir o painel **interativo** ("quero marcar direto no painel", "painel ativo",
"abrir o painel com os botões"), suba o servidor local e abra pelo endereço `http` — é o
mesmo painel, mas os cards ganham ações:

```bash
python ~/.claude/skills/_scripts/servir_painel.py "<PASTA_OS_ATIVAS>" --abrir
```

- Endereço: **http://127.0.0.1:8347** (só a máquina do AFT enxerga — nada sai para a
  rede). Consumo ocioso: ~20 MB de RAM, CPU zero. Se já estiver rodando, o script apenas
  informa o endereço e sai — pode chamar de novo sem medo.
- **Ações mecânicas** (gravadas direto no `memory.md` da OS, sempre com backup prévio em
  `.backups/`): marcar notificação DET como checada (e desmarcar), resolver pendência, registrar
  atividade de hoje, mudar o status da OS (`em_andamento` / `aguardando_resposta` /
  `encerrada`) e alternar **embargo/interdição** entre vigente/suspenso (preserva a
  descrição já registrada no campo `embargo_interdicao`).
- **Botões de comando**: copiam para a área de transferência um comando pronto
  (`/inspecao-fisica`, `/inspecao-inicial`, `/gera-ai`, `/autos-lavrados`, `/det-630`,
  `/tn-nco`, `/aft-rt-rgi`, `/sfitweb-rel` — sempre com `— OS <EMPREGADOR>` anexado)
  para o AFT colar no Claude Code; ao passar o mouse, cada botão mostra uma legenda com
  o resumo da skill (texto vindo da arquitetura do toolkit). Ações que exigem julgamento
  nunca rodam pelo servidor.
- O `painel.html` estático continua existindo e é regenerado a cada carregamento da
  página; aberto por duplo-clique (`file://`), os controles somem e ele volta a ser
  somente leitura.
- Para encerrar o servidor: `Ctrl+C` no terminal onde roda (ou reiniciar o computador —
  ele não se instala sozinho, só roda quando chamado).
- **Sempre ligado (opcional):** para não depender de abrir terminal toda vez — necessário
  para a sincronização automática do DET pela extensão Chrome (abaixo) —, instale como
  serviço do sistema (o `/aft-setup`/`/aft-atualizar` já oferecem isso na instalação):
  ```bash
  python ~/.claude/skills/_scripts/instalar_servidor_painel.py instalar "<python_path>" "<PASTA_OS_ATIVAS>"
  ```
  No Windows usa o Agendador de Tarefas (gatilho "ao fazer logon", `pythonw.exe` sem
  janela, reinício automático se cair); no macOS um LaunchAgent com `KeepAlive`. Remover:
  `instalar_servidor_painel.py remover`. Status: `... status`.
- **Sync do DET pela extensão Chrome** ("SisOS — Sync DET", da Chrome Web Store): com o
  servidor no ar e o "Painel local" ativado nas opções da extensão, o botão flutuante
  **Sincronizar** no site do DET envia o token de sessão do próprio AFT para
  `POST /api/det-sync`; o `det_sync.py` consulta a API oficial do DET para cada OS com
  CNPJ/CPF ou RI e atualiza a seção `## Notificações DET` dos memory.md: notificação
  nova → linha `- [ ] <COD> — prazo <data>`; prazo que mudou → data atualizada na linha;
  `ri:` vazio → preenchido. O estado `[ ]`/`[x]` nunca é alterado e o token nunca é
  gravado em disco. Requer estar logado no DET no navegador.

## Passo 4 — (Opcional) Publicar na aba Artefatos

Este passo é **opt-in**: só execute se o AFT pedir ("publica o painel", "atualiza o
artefato") ou responder SIM à oferta. **Nunca publique sem consentimento explícito na
sessão** — publicar hospeda o painel (lista de empresas sob fiscalização, prazos e autos)
na conta claude.ai do AFT, fora do computador dele.

1. Na primeira vez na sessão, ofereça: *"Quer que eu publique/atualize o painel na aba
   Artefatos? Ele fica hospedado na sua conta claude.ai, privado — mas fora do seu
   computador."* Se a resposta não for sim, pare aqui.
2. Gere a versão para artefato (sem caminhos locais):
   ```bash
   python ~/.claude/skills/_scripts/gerar_painel.py "<PASTA_OS_ATIVAS>" "" "<PASTA_OS_ATIVAS>/../painel-artifact.html"
   ```
3. Chame a tool **Artifact** com `action: "list"` e procure um artefato de título
   **"Painel AFT"**.
4. Publique com a tool **Artifact**:
   - Se encontrou → `file_path: <painel-artifact.html>`, `url: <a URL encontrada>`
     (atualiza a MESMA página), `favicon: "📊"`.
   - Se não encontrou → só `file_path` e `favicon: "📊"`, com
     `description: "Painel local das OS e prazos de DET do AFT Toolkit"`.
5. Informe o link e lembre em uma frase: o artefato é **privado** e o link **não deve ser
   compartilhado** (contém a carteira de fiscalização). Nunca sugira compartilhá-lo.

O artefato é um retrato: só muda quando o `/painel` rodar e publicar de novo.

## Passo 5 — (Opcional) Rotina diária da manhã

O `/aft-setup` (Passo 7b) e o `/aft-atualizar` (Passo 2b) já oferecem isso automaticamente
na instalação/primeira atualização. Se o AFT pedir aqui, fora desses fluxos ("quero que o
painel se atualize sozinho todo dia"), use o mesmo script — não reescreva a lógica na mão:

```bash
python "<python_path>" ~/.claude/skills/_scripts/instalar_rotina_painel.py instalar "<python_path>" "<PASTA_OS_ATIVAS>"
```

Detecta macOS (launchd) ou Windows (Agendador de Tarefas) sozinho; padrão 07:00 (`--hora
HH:MM` para outro horário). Leia o JSON de retorno (`ok`, `sistema`, `detalhe`) e traduza
em uma frase. Se ainda não estava registrado no `aft-config.md`, acrescente
`rotina_painel: "07:00"` (ou o horário escolhido) ao front-matter.

Para remover: `python instalar_rotina_painel.py remover`. Para conferir se está ativa:
`python instalar_rotina_painel.py status`.

Roda **inteiramente fora do Claude Code** (não gasta tokens — o gerador é um script
Python determinístico, chamado direto pelo SO com `--scan`). Se o Sistema Auditor não
estiver acessível naquele horário, o gerador degrada sozinho para o último snapshot — a
rotina nunca falha por causa disso.

## O que o painel mostra

- Contadores: OS ativas, DET vencidos, DET vencendo em 7 dias, notificações não
  cadastradas, autos lavrados.
- **Um card por OS**: empregador, CNPJ, município, badge de urgência (vencido / vence em
  Xd / no prazo / sem prazo), chips das NRs autuadas, nº de autos e DETs abertos, "há N
  dias" desde o início.
- **Clique no card → detalhe da auditoria** (modal central amplo): RI em destaque, botão
  para copiar o caminho da pasta, DETs com estado (✔ checada / ◻ aberta) e **selo de
  urgência por notificação** ("vencido há Xd" / "vence HOJE" / "vence em Xd" / "em Xd"),
  notificações sem registro, o **relato da inspeção física** completo (todos os bullets
  do `inspecao-fisica.md`), TODOS os autos lavrados em grade (Nº do AI, ementa,
  descrição, constatação, data), autos substituídos (re-lavratura), pendentes de
  transmissão, pendências da OS e registro de atividades.
- **Datas sempre em dd/mm/aaaa na tela**: as fichas do schema v2 gravam datas ISO nas
  linhas de DET; o painel normaliza só na exibição (os `memory.md` não são tocados).
- Coral é reservado ao que aperta o prazo: DET aberto só fica vermelho se estiver
  vencido ou vencendo em ≤7 dias; os demais ficam neutros. Seções sem conteúdo aparecem
  esmaecidas (informam a ausência sem competir por atenção).
- Cores por urgência: vermelho = vencido, laranja = vence em ≤7 dias, verde = no prazo,
  cinza = sem prazo cadastrado. Tema claro/escuro automático.
- Chip ⛔ no card quando o front-matter tem `embargo_interdicao` preenchido.
- **No modo interativo** (Passo 3.5): controles de status, embargo/interdição, DET,
  pendência e atividade em cada card, além dos botões 📋 de copiar comando.
- **OS com `status: encerrada` somem do painel por padrão** — é um dashboard do que está
  em andamento. Mudar o status para `encerrada` (pelo dropdown do modo interativo, ou
  editando o `memory.md`) já basta para o card sumir na próxima geração — não precisa
  mover a pasta. Para ver todas de novo (conferência pontual), rode com `--todas`. Isso
  é **diferente de arquivar**: a OS encerrada continua em `OS ATIVAS/`, só oculta do
  painel; mover a pasta para `OS ARQUIVADAS/` (convenção do README) é organização de
  disco, feita à parte, quando o AFT quiser.

## Regras

- **A skill é somente leitura.** Ela nunca altera os `memory.md` — as ferramentas de
  escrita (Write/Edit) ficam indisponíveis pelo `allowed-tools`; quem grava o
  `painel.html` é o script Python. (Única exceção: a linha `pasta_os:` no `aft-config.md`
  do Passo 0.) Quem edita `memory.md` no modo interativo é o **servir_painel.py**, por
  clique do próprio AFT no navegador — só as 5 ações mecânicas listadas no Passo 3.5,
  linha a linha, sempre com backup prévio; nada de decisão automática.
- A detecção de notificações novas e a lista de autos são **determinísticas** (scripts
  Python) — o modelo apenas relata o que os scripts acharam; nunca "adivinhe" código,
  data ou número de AI que os scripts não extraíram.
- **Publicar na aba Artefatos é a única saída externa do toolkit** e exige consentimento
  explícito a cada sessão. O artefato é privado por padrão; nunca sugira compartilhar.
- A urgência é calculada com a data de hoje na máquina do AFT (o script usa a data local).
- Regenere o painel sempre que algo mudar — ele é um retrato do momento em que roda (a
  rotina diária do Passo 5 automatiza isso).
- Não exponha dados pessoais de trabalhadores no chat; o painel trata de OS, prazos e
  autos — as constatações exibidas vêm do `autos-lavrados.md`, que já nasce sem nomes/CPF.
- **Relato de campo (`inspecao-fisica.md`) só na versão LOCAL.** Esse arquivo é a memória
  bruta da inspeção e pode ter nome/CPF de trabalhador; por isso o gerador o inclui no
  detalhe do `painel.html` local (a máquina do AFT, como o `memory.md`), mas **nunca** na
  versão publicada como Artifact (o script já corta esse campo na saída de artefato).
