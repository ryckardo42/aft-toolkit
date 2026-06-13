---
name: painel
description: >
  Use SEMPRE que o Auditor-Fiscal do Trabalho (AFT) quiser ver um panorama das suas
  auditorias em andamento e, principalmente, os prazos de DET vencendo. Acione com
  /painel, "painel", "minhas auditorias", "minhas OS", "o que vence", "prazos de DET",
  "o que vence essa semana", "quais DET estão vencendo", "visão geral das fiscalizações",
  "dashboard", "quadro das OS". A skill varre as fichas locais (memory.md de cada OS em
  ~/Documents/AFT/OS ATIVAS/), gera um painel.html autocontido (abre por duplo-clique, sem
  servidor) com a lista de OS e os prazos coloridos por urgência, e responde no chat quais
  prazos estão vencidos ou vencendo. É SOMENTE LEITURA — nunca altera os memory.md.
---

# painel — Painel local das auditorias (SISOS-lite)
**AFT Toolkit**

## Objetivo

Dar ao AFT, sem nenhum servidor, o que mais importa de um painel de fiscalização: **a visão
geral das OS em andamento e os prazos de DET vencendo** (perder um prazo é o erro mais caro).
A fonte da verdade são os arquivos `memory.md` de cada OS — esta skill apenas os lê e gera uma
página HTML para abrir no navegador. **Nunca escreve nos memory.md** (quem cadastra/atualiza é
o `/nova-os` e as demais skills).

## Passo 1 — Gerar o painel

Rode o gerador do toolkit:

```bash
python ~/.claude/skills/_scripts/gerar_painel.py
```

> O caminho padrão das OS é `~/Documents/AFT/OS ATIVAS` e a saída é
> `~/Documents/AFT/painel.html`. Para usar pastas diferentes, passe-as como argumentos:
> `python ~/.claude/skills/_scripts/gerar_painel.py "<PASTA_OS_ATIVAS>" "<SAIDA.html>"`.

O script imprime no stdout um JSON com o resumo:
```json
{ "painel": "...painel.html", "os_ativas": N, "dets_vencidos": X,
  "dets_vencendo_7d": Y, "vencendo": [ {"empregador": "...", "prazo": "dd/mm/aaaa", "dias": D} ] }
```

## Passo 2 — Responder no chat

A partir do JSON, dê um resumo objetivo, **destacando o que precisa de ação**:

- Se houver `dets_vencidos > 0`: liste primeiro, com ênfase (estão atrasados).
- Depois os que vencem em ≤ 7 dias (`dias` entre 0 e 7).
- Informe o total de OS ativas.

Exemplo de resposta:
```
📊 Painel atualizado — N OS ativas

🔴 DET vencidos (ação imediata):
  • EMPRESA X — prazo 01/06/2026 (12 dias atrás)

🟠 Vencendo em até 7 dias:
  • EMPRESA Y — prazo 16/06/2026 (em 3 dias)

Painel completo: ~/Documents/AFT/painel.html
```

Se `os_ativas = 0`, diga que não há OS cadastradas e sugira `/nova-os`.

## Passo 3 — Oferecer abrir o painel

Ofereça abrir o `painel.html` no navegador (ele é autocontido, abre por duplo-clique):

```bash
# Windows (Git Bash):
start "" ~/Documents/AFT/painel.html
# macOS:
open ~/Documents/AFT/painel.html
```

Se o AFT preferir, ele mesmo abre o arquivo na pasta `Documentos\AFT`.

## O que o painel.html mostra

- Contadores: OS ativas, DET vencidos, DET vencendo em 7 dias.
- Tabela ordenável (clique nos cabeçalhos) com: situação (colorida), empregador, CNPJ,
  município, prazo de DET mais próximo, nº de DET e o caminho da pasta.
- Cores por urgência: vermelho = vencido, laranja = vence em ≤7 dias, verde = no prazo,
  cinza = sem prazo cadastrado.

## Regras

- **Somente leitura.** Esta skill nunca altera os `memory.md`. Para cadastrar/editar uma OS
  ou um prazo de DET, use `/nova-os` (ou edite o `memory.md` da OS).
- A urgência é calculada com a data de hoje na máquina do AFT (o script usa a data local).
- Regenere o painel sempre que algo mudar — ele é um retrato do momento em que roda.
- Não exponha dados pessoais de trabalhadores no chat; o painel trata de OS e prazos, não de autos.
