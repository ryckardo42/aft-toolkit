---
name: preparacao-acao-fiscal
model: opus
description: >
  Use SEMPRE que o AFT quiser planejar uma ação fiscal ANTES da visita —
  já sabe a empresa e tem dados preliminares (denúncia, nº de
  trabalhadores, temas prováveis), mas ainda não foi ao local. Acione com
  "/preparacao-acao-fiscal", "vou fiscalizar a empresa X", "estou indo
  numa empresa", "preciso planejar essa ação fiscal". NÃO acionar com
  relatos do PASSADO ("cheguei da inspeção", "constatei") — isso é
  /inspecao-fisica. Resolve/cria a OS (via /nova-os), coleta os insumos
  (denúncia, quadro de trabalhadores, temas), tokeniza qualquer lista
  nominal de trabalhadores antes de processá-la, tira dúvidas técnicas nos
  NotebookLMs pertinentes (com fontes, sem nome de empresa/trabalhador),
  monta um checklist de documentos a solicitar e, com aprovação do AFT,
  encadeia a /NAD. Salva tudo em preparacao.md na pasta da OS. NÃO redige
  auto nem faz o relato de campo (isso é /inspecao-fisica →
  /inspecao-inicial, depois da visita).
---

# preparacao-acao-fiscal — Planejamento pré-visita da ação fiscal
**AFT Toolkit**

## Objetivo

Organizar o que o AFT já sabe **antes de ir a campo**: quem vai fiscalizar, por quê (denúncia, OS, rotina), o que precisa estudar antes (temas técnicos, via NotebookLM) e quais documentos vale a pena já solicitar pelo DET (via `/NAD`). O resultado é um `preparacao.md` na pasta da OS — um roteiro de estudo e ação, não um auto nem um relato de inspeção.

Esta skill trabalha **antes** da visita. Depois de ir ao estabelecimento, o próximo passo é `/inspecao-fisica` (relato do que foi constatado) → `/inspecao-inicial` (autos). Esta skill **não** redige autos e **não** registra achados de campo — ela planeja.

## Pasta base
`~/Documents/AFT/OS ATIVAS/<NOME_DA_AUDITORIA>/` (CNPJ pode ou não estar no nome — ver `/nova-os`)

---

## FASE 1 — Resolver/criar a OS

1. Se a empresa já tem pasta em `OS ATIVAS/`, use-a.
2. Se não existe, **chame o fluxo do `/nova-os`** para coletar o nome da auditoria, município (e DET, se já houver) e criar a pasta + `memory.md`. Não duplique a lógica de `/nova-os` — reaproveite-a. O CNPJ é opcional nessa fase (só se torna obrigatório no `/gera-ai`) — se o AFT já souber, informe; se não, siga sem.

Guarde: `PASTA_OS`, `EMPREGADOR`, `CNPJ` (pode vir vazio).

---

## FASE 2 — Coletar os insumos preliminares

Pergunte (ou aceite o que o AFT já colou/anexou) em uma única rodada:

| Insumo | Obrigatório | Como pode chegar |
|---|---|---|
| Origem da ação | Não | denúncia, OS/projeto, rotina, reincidência — texto livre |
| Teor da denúncia/motivação | Não | texto colado no chat, PDF anexado no chat, ou PDF já salvo na pasta da OS |
| Nº de trabalhadores | Não | número aproximado; se vier lista nominal, trate na FASE 3 |
| Temas prováveis | Não | ex.: "jornada", "NR-12", "PGR desatualizado" — usados para guiar o estudo (FASE 4) |

Se o AFT anexar um PDF (denúncia, extrato de OS, lista do eSocial), leia-o normalmente. Se ele mencionar que salvou algo na pasta da OS, procure lá (`ls "$PASTA_OS"`).

> Nenhum campo é obrigatório para prosseguir — trabalhe com o que houver. Se não houver nada além do nome da empresa, ainda assim é válido pular direto para a FASE 4 (estudo) ou FASE 5 (checklist), sem denúncia.

---

## FASE 3 — Tokenizar a lista de trabalhadores (se houver)

Se o AFT forneceu uma lista **nominal** de trabalhadores (nome, e opcionalmente CPF — ex.: extrato do eSocial, lista anexada à denúncia), **tokenize antes de processar qualquer coisa com ela.** Nenhum nome ou CPF real de trabalhador deve aparecer no chat a partir deste ponto, nem no `preparacao.md`.

1. **Reaproveite** um `.depara_<CNPJ>.json` (ou `.depara.json`, se o CNPJ ainda não foi informado) existente na **raiz da pasta da OS**, se houver (não confundir com o de uma subpasta `Autos DD-MM/` — a preparação acontece antes de qualquer lavratura). Se existir, acrescente os trabalhadores novos sem renumerar os existentes.
2. Se não existir, crie o arquivo na raiz da OS no mesmo esquema usado pelo `/gera-ai`: `.depara_<CNPJ>.json` se o CNPJ já foi informado (na `/nova-os` desta OS), ou `.depara.json` (sem sufixo) se ainda não — o `/gera-ai` sabe procurar os dois nomes e renomeia para incluir o CNPJ quando ele for coletado.
   ```json
   {
     "cnpj": "[cnpj_14_digitos, ou vazio se ainda não informado]",
     "autuada": { "token": "[[AUTUADA]]", "razao_social": "[RAZAO_SOCIAL]" },
     "trabalhadores": [
       { "token_nome": "[[TRAB_01]]", "nome": "[NOME REAL]",
         "token_cpf": "[[CPF_01]]",  "cpf": "[11_digitos ou vazio]" }
     ]
   }
   ```
3. A partir daqui, refira-se a cada trabalhador só pelo token (`[[TRAB_NN]]`/`[[CPF_NN]]`) no chat e no `preparacao.md`. Guarde só o **quantitativo e o perfil** no texto (ex.: "32 trabalhadores, majoritariamente em produção") — a lista nominal completa fica só no `.depara_<CNPJ>.json`, nunca solta no `preparacao.md`.

> Esse `.depara_<CNPJ>.json` na raiz da OS é o mesmo formato que o `/gera-ai` usa dentro da pasta `Autos DD-MM/`. Quando a fiscalização chegar à lavratura, `/gera-ai` deve procurar e reaproveitar este arquivo (ver nota em `gera-ai/SKILL.md` FASE 2.5) em vez de criar um novo do zero.

---

## FASE 4 — Estudo prévio (NotebookLM)

Para cada tema prévio informado (FASE 2) ou identificado na denúncia, tire as dúvidas técnicas necessárias **antes da visita** — isso evita voltar à empresa por falta de preparo.

1. Resolva o(s) notebook(s) pelo assunto, do mesmo jeito que `/consulta`: leia `~/.claude/skills/config/notebooks.json`, escolha a NR (`nr-12`, `nr-35`...) ou o tema (`jornada`, `esocial`, `informalidade`, `dupla-visita`...); sem NR específica, use `ementario-sst`.
2. Consulte:
   ```bash
   notebooklm ask "O que a fiscalização deve verificar/exigir sobre [TEMA] segundo [NR ou legislação aplicável]? Quais documentos costumam ser necessários para comprovar conformidade?" --notebook [notebook_id] --json
   ```
3. **Nunca envie nome da empresa nem de trabalhador ao NotebookLM** — só o tema/pergunta técnica.
4. Registre cada resposta com a fonte citada (mesmo padrão de `/consulta`), para entrar no `preparacao.md`.

Se o AFT não informou nenhum tema, pule esta fase (ou pergunte se quer estudar algo específico antes de ir).

---

## FASE 5 — Checklist de documentos a solicitar

A partir da denúncia, dos temas e do estudo (FASE 4), monte uma lista de **candidatos** a documentos que fazem sentido pedir pelo DET antes ou durante a visita (ex.: PGR, PCMSO, controles de jornada, atas da CIPA, folha de pagamento).

1. Apresente a lista ao AFT como **sugestão**, nunca como decisão tomada — ele risca, ajusta ou acrescenta itens.
2. **Não invente** exigência documental sem base — cada item candidato deve estar amparado por uma NR/artigo (mesmo que a ementa exata só seja resolvida depois, na `/NAD`).
3. Após aprovação do AFT, pergunte se ele quer **gerar a notificação agora**:
   - **Sim** → encadeie a skill `/NAD` passando a lista aprovada (ela faz a busca de ementa e monta o texto — não duplique essa lógica aqui).
   - **Não/depois** → apenas registre a lista aprovada no `preparacao.md` como pendência, para rodar `/NAD` mais tarde.

---

## FASE 6 — Gravar o preparacao.md

Salve (ou sobrescreva, avisando o AFT) em `$PASTA_OS/preparacao.md`:

```markdown
# Preparação da ação fiscal — <EMPREGADOR>
> Gerado por /preparacao-acao-fiscal em <DD/MM/AAAA>.

## Origem
<origem informada — denúncia / OS / rotina / reincidência — e resumo objetivo>

## Quadro de trabalhadores
<quantitativo e perfil, SEM nomes/CPFs reais — ex.: "32 trabalhadores, produção e logística">

## Temas a verificar
- <tema 1>
- <tema 2>

## Estudo prévio (NotebookLM)
### <tema 1>
<resposta objetiva>
Fonte: <notebook + trecho citado>

### <tema 2>
...

## Checklist de documentos a solicitar
- [ ] <documento 1> — <base legal> <(NAD gerada em DD/MM, se aplicável)>
- [ ] <documento 2> — <base legal>

## Pontos de atenção para a visita
<riscos identificados no estudo que merecem atenção em campo, se houver>
```

Não inclua nome nem CPF de trabalhador em nenhum campo — só o token, se precisar referenciar algum caso específico da denúncia.

---

## FASE 7 — Checagem de PII

Antes de encerrar, rode o guard-rail sobre o arquivo gerado:

```bash
python ~/.claude/skills/_scripts/checar_pii.py "$PASTA_OS/preparacao.md"
```

Se ele **avisar** CPF/PIS com dígito verificador válido escapando da tokenização, corrija o `preparacao.md` (substitua pelo token correspondente) antes de entregar ao AFT. O script só avisa — não bloqueia nem corrige sozinho.

---

## FASE 8 — Atualizar o memory.md e encerrar

1. Se a OS tem `memory.md`, adicione **uma** linha em `## Registro de atividades`:
   ```
   | DD/MM/AAAA | Preparação da ação fiscal | preparacao.md |
   ```
2. Se restou pendência (checklist aprovado mas `/NAD` ainda não rodada), adicione em `## Pendências` (crie a seção se não existir):
   ```
   - [ ] Gerar NAD com os documentos do checklist de preparacao.md
   ```

Apresente o resumo final:

```
✅ Preparação registrada — <EMPREGADOR>
📄 ~/Documents/AFT/OS ATIVAS/<NOME_DA_AUDITORIA>/preparacao.md

Temas estudados: N   ·   Documentos no checklist: M   ·   NAD gerada: sim/não

Próximos passos:
  • /NAD                → gerar a notificação (se ainda não gerou)
  • Visita ao estabelecimento
  • /inspecao-fisica     → quando voltar, registrar o relato
```

---

## Encadeamento

- Chama `/nova-os` (FASE 1) para resolver/criar a OS — não duplica essa lógica.
- Encadeia `/NAD` (FASE 5) quando o AFT aprova gerar a notificação já na preparação.
- Sucede naturalmente para `/inspecao-fisica` depois da visita (fora do escopo desta skill).
- Não confundir com `/inspecao-fisica` (relato do que já foi constatado, DEPOIS da visita).

---

## Regras

- **Nunca** processe lista nominal de trabalhadores sem tokenizar primeiro (FASE 3) — nome/CPF real não aparece no chat nem no `preparacao.md` a partir do momento em que a lista é fornecida.
- **Nunca** envie nome de empresa ou de trabalhador ao NotebookLM — só o tema técnico.
- **Nunca** invente exigência documental, ementa ou dispositivo legal — o que não vier de fonte confiável, pergunte ao AFT ou deixe em aberto.
- O checklist de documentos é sempre **sugestão para aprovação do AFT** — nunca gere a `/NAD` sem essa aprovação explícita.
- Esta skill **não** redige auto de infração, **não** faz relato de campo e **não** substitui a visita — ela só organiza o que preceder a ida a campo.
- Encoding **UTF-8** em todo o pipeline.
