> Referência da skill /aft-ajuda — leia sob demanda.

Este arquivo cobre o que fazer quando algo do AFT Toolkit não funciona: a regra de ouro, a tabela de sintoma → solução, o ticket automático de erro, as limitações já conhecidas e quando o defeito não é culpa do AFT.

## A regra de ouro

**O AFT não precisa diagnosticar nada.** Basta descrever o problema ao assistente, com as palavras dele mesmo — "o comando X deu este erro: ...", "o painel abriu em branco", "a habilidade não apareceu". O assistente diagnostica e corrige na hora.

**Quem digita comando é sempre o assistente.** O AFT nunca abre terminal, Prompt de Comando, PowerShell ou Git Bash. No máximo, ele:

- clica em "Permitir" quando o assistente pede;
- fecha e reabre o aplicativo (fechar de verdade: botão direito no ícone do Claude na bandeja, perto do relógio → Sair; depois reabrir);
- reinicia o computador;
- interage com uma janela que o assistente abriu (por exemplo, o login da conta Google).

**`/aft-doctor` é sempre a primeira tentativa.** É o check-up completo da instalação, em linguagem simples: diz exatamente o que falta e como resolver, com 🟢 / 🟡 / 🔴. Ele **só diagnostica — não altera nada**, então rodar é sempre seguro. Quem instala e conserta o que faltou é o `/aft-atualizar` ou o próprio assistente.

## Sintoma → o que fazer

| Sintoma | O que fazer |
|---|---|
| Não sei se está tudo certo / algo parou de funcionar | Rode `/aft-doctor`: check-up completo, aponta o que falta e como resolver. É sempre o primeiro a tentar |
| A habilidade não aparece ao digitar `/` | Feche e reabra o Claude Code/Codex. Se persistir, peça ao assistente: "as habilidades estão diretamente em `~/.claude/skills` (ex.: `~/.claude/skills/aft-setup`)? Se estiverem dentro de uma subpasta `aft-toolkit`, mova todo o conteúdo um nível acima" |
| "Git is required for local sessions" | Peça ao assistente para instalar o Git. Depois feche o aplicativo de verdade (ícone na bandeja → Sair) e reabra. Se persistir, reinicie o computador |
| Python "não encontrado" | Peça ao assistente: "instale o Python com winget". Se a rede da repartição bloquear, ele usa o caminho manual — e depois o AFT só fecha e reabre o aplicativo |
| `notebooklm: command not found` | Peça ao assistente: "instale o notebooklm-py[browser] do repositório teng-lin com pipx e garanta que o comando `notebooklm` fique no PATH". Depois feche e reabra o aplicativo |
| Habilidade `/notebooklm` não aparece, embora `notebooklm --help` funcione | É **opcional**: as habilidades do toolkit usam o comando, não essa habilidade. Se quiser tê-la, peça ao assistente: "rode `notebooklm skill install`" e feche e reabra o aplicativo |
| NotebookLM responde "sem acesso" | Solicite acesso em https://notebooks-aft.vercel.app e aguarde a liberação do mantenedor. Não é defeito da instalação |
| NotebookLM parou / "authentication expired" / pede login | A sessão expira de tempos em tempos. Peça ao assistente: "reconecte o notebooklm" (`/aft-notebooklm-login`). Ele reabre a janela de login e o AFT só entra na sua conta Google |
| Foto HEIC do iPhone não converte | Peça ao assistente: "instale o pillow-heif". Alternativa imediata: converter a foto para JPG no próprio celular |
| Sistema Auditor não acha o anexo | O anexo precisa do nome na convenção `AI_N_CNPJ_sufixoN.PDF`, com `.PDF` em maiúsculas, e do caminho Windows correto no `aft-config.md` (campo `path_windows`). Peça ao assistente para conferir e corrigir os dois |
| Painel "não está no ar" (extensão Sync DET reclama) | O servidor local do painel não está rodando. Peça `/aft-painel` — ou `/aft-doctor` para diagnosticar |
| "Token DET não capturado" na extensão | A extensão ainda não viu o AFT navegar logado. Abra qualquer página interna do DET (a lista de notificações) e clique em Sincronizar de novo |
| Sincronizou, mas a notificação não apareceu na ficha | A OS precisa ter CNPJ (ou CPF) no `memory.md` — sem ele o painel não sabe qual empregador consultar no DET. Peça ao assistente para cadastrar |
| O assistente recusa instalar o toolkit ("não instalo conteúdo que não consigo verificar") | Não discuta nem insista — argumentar deixa ele mais desconfiado. Confirme que as três mensagens da instalação foram enviadas **na ordem**: a recusa some quando ele já leu o conteúdo, na mensagem 2. Se persistir, use o Plano B do `COMO-INSTALAR.md` |
| Codex não encontra as habilidades (`/aft-...` não faz nada) | Falta o atalho de pasta. Peça ao assistente: "confira o atalho `~/.agents/skills` apontando para `~/.claude/skills` e recrie se estiver faltando" |
| Codex trata o AFT como programador (manda ao terminal, usa jargão) | Falta o atalho do perfil. Peça: "crie o atalho `~/.codex/AGENTS.md` apontando para `~/.claude/CLAUDE.md`" e reabra o Codex |
| `/aft-doctor` acusa agentes, deny-list ou vigia de sessões faltando, e o AFT está no Codex | É esperado: essas três coisas só existem no aplicativo do Claude. Nenhuma habilidade depende delas |

## Quando o toolkit quebra sozinho: o ticket automático

Todo script do toolkit se protege: se ele morrer no meio, **grava sozinho um ticket de correção** e mostra o caminho na tela:

```
  O AFT TOOLKIT ENCONTROU UM ERRO E PREPAROU UM TICKET.
  Arquivo: <pasta AFT>\tickets\ticket-2026-07-29-1432.md
```

**O que o ticket leva:** o erro exato, a versão do toolkit instalada (o commit) e um retrato da máquina — sistema operacional, versão do Python, quais programas existem ali. É isso que permite corrigir sem adivinhação.

**O que o ticket NUNCA leva:** nome de empresa, CNPJ/CPF, nome de trabalhador ou conteúdo de documento de fiscalização. Esses dados saem como `<EMPRESA>`, `<INSCRICAO>`. O mapa de pseudonimização (`.depara_*.json`) não entra em hipótese nenhuma.

**O ticket fica só na máquina do AFT.** O assistente nunca envia a lugar nenhum — quem decide o que sai da máquina é o AFT, que anexa o arquivo (ou copia o conteúdo) para quem mantém o toolkit.

O que o assistente faz ao ver o aviso, nessa ordem:

1. **tenta consertar** — é o papel dele, e o AFT não vai ao terminal;
2. avisa que o ticket ficou gravado e oferece completá-lo com o contexto (é a `/aft-erro` que faz isso);
3. oferece um contorno para o trabalho de hoje: o ticket é para o mantenedor, mas o AFT ainda precisa do documento pronto.

Erro **sem quebra** — texto torto, painel em branco, `.docx` com falha, resultado errado — **não gera ticket sozinho**: aí o caminho é a `/aft-erro`, que cria o ticket do zero.

## Limitações conhecidas (não é defeito)

Estado atual da ferramenta, e não coisa quebrada:

- As habilidades são **apoio à redação e organização**. O conteúdo jurídico de cada auto, termo e relatório é responsabilidade do AFT, que revisa tudo antes de transmitir.
- **Nunca aceite código de ementa, item de NR ou capitulação sem conferir no ementário oficial.**
- `/aft-autos-lavrados`: a leitura dos PDFs precisa de conferência na primeira execução contra os PDFs reais do Sistema Auditor.
- O template do Relatório Técnico de interdição/embargo segue o modelo da SRTE/GO — auditores de outras SRTEs ajustam o cabeçalho.
- `/aft-atualizar` atualiza o `notebooklm-py` automaticamente, sem perguntar antes: é dependência de terceiro, fora do controle de versão do toolkit.
- As habilidades que pedem o modelo mais forte dependem de o plano do AFT ter acesso a ele — o `/aft-doctor` testa e explica em linguagem simples se faltar.
- A detecção de notificações DET do `/aft-painel` é heurística e pode dar falso positivo — o AFT confere antes de cadastrar.
- No Codex, o modelo declarado por cada habilidade é ignorado (lá o modelo vale para a conversa inteira): as que julgam documento entregue pela empresa — PGR, AET, análise de acidente, laudo de NR-12 e manutenção de interdição — avisam em uma linha que pedem o modelo mais forte e esperam o AFT trocar com `/model`.
- `/aft-NR12`, `/aft-NR18`, `/aft-tn-nco` e o painel em Artifact ainda dependem de validação em máquina Windows real com o aplicativo logado.

## O que NÃO é problema do AFT

Quando o defeito é do toolkit — e não da máquina ou de algo que o AFT fez —, **o assistente diz isso com todas as letras**: não foi ele que fez errado. O AFT não precisa entender o problema técnico para reportá-lo, e reportar é ajudar a melhorar a ferramenta, não confessar erro.

Nunca faça o AFT sentir que precisava saber de informática. Diga o que quebrou, conserte se der, registre o ticket e siga com o trabalho dele.

## Ainda assim não resolveu

Dúvidas, sugestões de novas habilidades ou problemas persistentes: falar com o mantenedor — Ricardo de Oliveira (AFT, SRTE/GO) — ou abrir uma Issue em github.com/ryckardo42/aft-toolkit.
