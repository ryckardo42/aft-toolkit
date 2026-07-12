---
name: painel
model: haiku
allowed-tools: Read, Glob, Grep, Bash, AskUserQuestion, Artifact
description: >
  Use SEMPRE que o Auditor-Fiscal do Trabalho (AFT) quiser um panorama das
  auditorias em andamento e os prazos de DET vencendo. Acione com /painel,
  "painel", "minhas auditorias", "minhas OS", "o que vence essa semana",
  "quais DET estão vencendo", "dashboard", "quadro das OS". Varre as fichas
  locais (memory.md em ~/Documents/AFT/OS ATIVAS/), detecta PDFs de
  notificação DET ainda NÃO cadastrados nas pastas das OS (com código e
  datas), gera um painel.html autocontido (abre por duplo-clique, sem
  servidor) com prazos coloridos por urgência e responde no chat o que está
  vencido ou vencendo. Opcionalmente — só com consentimento explícito do AFT —
  publica/atualiza o painel como Artifact privado na aba Artefatos do app.
  É SOMENTE LEITURA nas fichas: nunca altera os memory.md; para cadastrar uma
  notificação detectada, encaminha ao /nova-os.
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

O script também **varre as pastas das OS** em busca de PDFs de notificação DET que ainda
não estão registrados na ficha (compara o código da notificação com o memory.md) e imprime
no stdout um JSON com o resumo:

```json
{ "painel": "...painel.html", "artifact_html": null,
  "os_ativas": N, "dets_vencidos": X, "dets_vencendo_7d": Y,
  "notificacoes_nao_cadastradas": Z,
  "novas": [ {"empregador": "...", "arquivo": "....pdf", "codigo": "ABC...",
              "ciencia": "dd/mm/aaaa"|null, "prazo": "dd/mm/aaaa"|null,
              "data_arquivo": "dd/mm/aaaa"} ],
  "vencendo": [ {"empregador": "...", "prazo": "dd/mm/aaaa", "dias": D} ] }
```

## Passo 2 — Responder no chat

A partir do JSON, dê um resumo objetivo, **destacando o que precisa de ação**:

- Se houver `dets_vencidos > 0`: liste primeiro, com ênfase (estão atrasados).
- Depois os que vencem em ≤ 7 dias (`dias` entre 0 e 7).
- Se `notificacoes_nao_cadastradas > 0`: liste cada item de `novas` (empregador, arquivo,
  código e datas) e diga que essas notificações **não estão na ficha** — sugira cadastrar
  com `/nova-os` (ou editar o `memory.md` da OS). **Esta skill não cadastra nada.**
- Informe o total de OS ativas.

Exemplo de resposta:
```
📊 Painel atualizado — N OS ativas

🔴 DET vencidos (ação imediata):
  • EMPRESA X — prazo 01/06/2026 (12 dias atrás)

🟠 Vencendo em até 7 dias:
  • EMPRESA Y — prazo 16/06/2026 (em 3 dias)

🔵 Notificação encontrada na pasta mas NÃO cadastrada:
  • EMPRESA Z — Notificação ABC123.pdf — código ABC123..., prazo 20/06/2026
    -> Quer cadastrar? Rode /nova-os (ou me peça para abrir a ficha).

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

## Passo 4 — (Opcional) Publicar na aba Artefatos

Este passo é **opt-in**: só execute se o AFT pedir ("publica o painel", "atualiza o
artefato") ou responder SIM à oferta. **Nunca publique sem consentimento explícito na
sessão** — publicar hospeda o painel (lista de empresas sob fiscalização e prazos) na
conta claude.ai do AFT, fora do computador dele.

1. Na primeira vez na sessão, ofereça: *"Quer que eu publique/atualize o painel na aba
   Artefatos? Ele fica hospedado na sua conta claude.ai, privado — mas fora do seu
   computador."* Se a resposta não for sim, pare aqui.
2. Gere a versão para artefato (sem a coluna Pasta, que é caminho local):
   ```bash
   python ~/.claude/skills/_scripts/gerar_painel.py "" "" ~/Documents/AFT/painel-artifact.html
   ```
3. Chame a tool **Artifact** com `action: "list"` e procure um artefato de título
   **"Painel AFT"**.
4. Publique com a tool **Artifact**:
   - Se encontrou → `file_path: ~/Documents/AFT/painel-artifact.html`, `url: <a URL
     encontrada>` (atualiza a MESMA página), `favicon: "📊"`.
   - Se não encontrou → só `file_path` e `favicon: "📊"`, com
     `description: "Painel local das OS e prazos de DET do AFT Toolkit"`.
5. Informe o link e lembre em uma frase: o artefato é **privado** e o link **não deve ser
   compartilhado** (contém a carteira de fiscalização). Nunca sugira compartilhá-lo.

O artefato é um retrato: só muda quando o `/painel` rodar e publicar de novo.

## O que o painel mostra

- Contadores: OS ativas, DET vencidos, DET vencendo em 7 dias, notificações não cadastradas.
- Tabela ordenável (clique nos cabeçalhos) com: situação (colorida), empregador, CNPJ,
  município, prazo de DET mais próximo, nº de DET e o caminho da pasta (só na versão local).
- Seção "Notificações DET não cadastradas": PDFs de notificação achados nas pastas das OS
  sem registro no memory.md, com código e datas extraídos do arquivo.
- Cores por urgência: vermelho = vencido, laranja = vence em ≤7 dias, verde = no prazo,
  cinza = sem prazo cadastrado.

## Regras

- **Somente leitura.** Esta skill nunca altera os `memory.md`. Para cadastrar/editar uma OS
  ou um prazo de DET, use `/nova-os` (ou edite o `memory.md` da OS). Isso é garantido
  tecnicamente pelo `allowed-tools` do frontmatter: as ferramentas de escrita (Write/Edit)
  ficam indisponíveis enquanto a skill roda — quem grava o `painel.html` é o script Python.
- A detecção de notificações novas é **determinística** (script Python, regex sobre nome e
  1ª página do PDF) — o modelo apenas relata o que o script achou; nunca "adivinhe" código
  ou data que o script não extraiu.
- **Publicar na aba Artefatos é a única saída externa do toolkit** e exige consentimento
  explícito a cada sessão. O artefato é privado por padrão; nunca sugira compartilhar.
- A urgência é calculada com a data de hoje na máquina do AFT (o script usa a data local).
- Regenere o painel sempre que algo mudar — ele é um retrato do momento em que roda.
- Não exponha dados pessoais de trabalhadores no chat; o painel trata de OS e prazos, não de autos.
