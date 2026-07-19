---
name: organiza-os
model: sonnet
description: >
  Use SEMPRE que o AFT jogar/copiar pastas de fiscalização dentro de OS ATIVAS
  (documentos acumulados antes do toolkit: notificações do DET, relação de
  autos do Sistema Auditor, respostas do empregador, fotos) e quiser colocá-las
  no padrão do AFT Toolkit. Acione com "/organiza-os", "organiza essa pasta",
  "joguei uma pasta na OS ATIVAS", "importar uma auditoria antiga", "arruma a
  pasta da empresa X", "padroniza essa OS", "acabei de copiar os arquivos da
  fiscalização". A skill varre TODA a pasta OS ATIVAS de uma vez (organiza as
  pastas novas e atualiza as já organizadas), lê os arquivos (1ª página dos
  PDFs), classifica cada um, extrai empregador/CNPJ-CPF/códigos e prazos de
  DET, mostra UM plano consolidado e — com uma única aprovação do AFT —
  renomeia as pastas para o padrão, cria/atualiza o memory.md e move os
  arquivos para os lugares que as demais skills esperam. Ao final, encadeia
  /autos-lavrados (para trazer os autos do Sistema Auditor) e abre o painel
  interativo. Nunca apaga nada. NÃO cadastra OS do zero (isso é /nova-os) nem
  baixa nada do DET (isso é det-baixar).
---

# organiza-os — Importar/organizar as pastas de fiscalização de OS ATIVAS
**AFT Toolkit**

## Objetivo

O colega que começa a usar o toolkit já tem fiscalizações em andamento, com os documentos
acumulados em pastas do jeito dele. Esta skill varre **toda a pasta `OS ATIVAS/`** e a
coloca no padrão do toolkit: nome de pasta padronizado, `memory.md` com os dados
extraídos dos próprios documentos (empregador, CNPJ/CPF, notificações DET com prazo),
e os arquivos nos lugares onde as demais skills (`/painel`, `/analise-preliminar`,
`/det-630`, `/autos-lavrados`) esperam encontrá-los. Ao final, encadeia o
`/autos-lavrados` (que traz os autos já transmitidos no Sistema Auditor para o
memory.md e o painel) e abre o painel interativo para o AFT ver o panorama.

Regras de ouro:
- **Inventário e plano primeiro; execução só depois de UMA aprovação** — um único plano
  consolidado para todas as pastas, uma única pergunta.
- **Nunca apagar nada** — só renomear e mover; o que não der para identificar fica onde
  está.
- **Perguntar só o indispensável.** Informação ausente não é pergunta: é campo em branco
  no memory.md, relatado no resumo. Ex.: pasta sem o PDF da notificação DET → processa
  assim mesmo, DET fica "(código não localizado) — prazo (a preencher)". Só pergunte
  quando houver **ambiguidade real** que mude o resultado (ex.: dois empregadores
  diferentes nos documentos da mesma pasta).

## FASE 1 — Varredura completa (sem perguntar o alvo)

Processe **sempre a pasta OS ATIVAS inteira** — não pergunte qual auditoria organizar.
Classifique cada subpasta em três grupos:

```bash
for d in ~/Documents/AFT/"OS ATIVAS"/*/; do [ -f "$d/memory.md" ] || echo "$d"; done
```

(No Mac, use a pasta de OS do `aft-config.md` — campo `pasta_os` — se existir.)

1. **Sem `memory.md` e com conteúdo** → organizar do zero (fluxo completo).
2. **Com `memory.md`** → verificar se precisa de **atualização**: arquivos novos soltos
   na raiz (resposta de DET recém-baixada, notificação nova, fotos), estrutura fora do
   padrão atual, memory.md sem seção obrigatória. Se precisar, entra no plano como
   "atualização" (antes de editar o memory.md, rode
   `python ~/.claude/skills/_scripts/backup_arquivo.py "<memory.md>"`). Se estiver em
   dia, não toque.
3. **Vazia** → apenas relate no resumo final ("pastas vazias: X, Y — nada a organizar")
   e siga. Não pergunte nada sobre elas.

## FASE 2 — Inventário e classificação (somente leitura)

Para cada pasta dos grupos 1 e 2, liste tudo (`ls -la`, recursivo no 1º nível) e, para
cada PDF, extraia a 1ª página:

```bash
pdftotext -layout -f 1 -l 1 "<arquivo.pdf>" - 2>/dev/null | head -40
# sem pdftotext, use pdfplumber via python (o /aft-setup instala)
```

Classifique cada item pelas assinaturas (nome do arquivo + texto da 1ª página):

| Tipo | Assinaturas típicas |
|---|---|
| **Notificação DET** | "NOTIFICAÇÃO Nº" + código alfanumérico 12–16 chars (ex.: `S8JHJEYM2OC4VE`); "NOTIFICAÇÃO PARA A APRESENTAÇÃO DE DOCUMENTOS"/"CORREÇÃO"; cabeçalho MTE/SIT |
| **Relatório de atendimento do DET** | nome `relatorio-atendimento*<CODIGO>*.pdf` ou 1ª página "Relatório de Atendimento" + código — é **evidência de que o DET foi respondido** |
| **Relação de autos lavrados** | "Relação de Autos de Infração Lavrados" (relatório do Sistema Auditor); nome tipo `RR_*.PDF` |
| **Resposta do empregador ao DET** | pasta com subpastas `item1`, `item2`... ou `01 - <descrição>`, `02 - ...` (padrões do download do DET) ou ZIP/pasta com nome `<EMPREGADOR>_<data>` |
| **Fotos de inspeção** | `.jpeg/.jpg/.png/.heic` (soltas ou em subpasta `FOTO`/`fotos`) |
| **Auto de infração (PDF)** | "AUTO DE INFRAÇÃO Nº" — nome `AI_<9 díg>.PDF` |
| **Interdição/embargo** | nome com `interdicao`/`interdição`/`embargo`/`TE-TI`; ou 1ª página com "TERMO DE INTERDIÇÃO"/"TERMO DE EMBARGO"/"TERMO DE MANUTENÇÃO"/"RELATÓRIO TÉCNICO" + interdição/embargo. Inclui o termo assinado, o RT que o fundamenta (`RT_Interdicao.docx`), o RT de manutenção, o requerimento de suspensão e seus juntados |
| **Trabalho do AFT em andamento** | `.docx`/`.md` de análise, minuta de autos, relatório de acidente, relatório final etc. produzidos pelo próprio auditor — **ficam na raiz, intocados**, e são anotados no memory.md ("trabalhos já iniciados") |
| **Lixo temporário do Office** | arquivos `~$*.docx`/`~$*.xlsx` (locks do Word/Excel) — **ignore por completo**: não mova, não liste como "não identificado", não mencione no plano |
| **Não identificado** | sem texto extraível (escaneado) ou sem assinatura conhecida |

Extraia, quando presentes:
- **Empregador** (Nome/Razão Social) e **CNPJ (14 díg.) ou CPF/CAEPF (11 díg.)** — em
  notificações DET vem em "EMPREGADOR / Nome: ... CPF/CNPJ: ...". Empregador pessoa
  física (produtor rural) usa CPF: é normal. Sem notificação na pasta, procure o
  empregador em outros documentos DA EMPRESA (carta de designação, acordo coletivo,
  contrato social) — nunca em documentos de trabalhador.
- **Município/UF** (do endereço de fiscalização).
- Por notificação DET: **código**, **prazo** ("até dd/mm/aaaa" nos itens notificados) e
  **ciência** (se constar). **Código de DET só vale se extraído do PDF da própria
  notificação** (linha "NOTIFICAÇÃO Nº"): números de registro de acordo coletivo,
  protocolo de outros sistemas ou códigos avulsos achados em outros documentos NÃO são
  código de DET — não os cadastre como tal.
- Da relação de autos: para cada auto, **número do AI** (9 dígitos → formate
  `XX.XXX.XXX-X`), **data de lavratura**, **ementa** (7 dígitos → `XXXXXX-X`) e um resumo
  curtíssimo da descrição.

> Privacidade: **não abra nem ecoe** conteúdo de listas de empregados (ex.: "RELAÇÃO DE
> EMPREGADOS.xlsx") nem documentos pessoais de trabalhador (CNH, RG, CAT, certidão de
> óbito...) — classifique pelo nome do arquivo/da subpasta e siga. Nome/CPF de
> trabalhador não aparece no chat nem no memory.md. O CPF/CNPJ **do empregador** é o
> identificador da OS: fica real (nunca tokenizado).

## FASE 3 — Plano consolidado (UMA aprovação para tudo)

Monte **um único plano** cobrindo todas as pastas (novas + atualizações) e peça **uma
única confirmação**. Não pergunte pasta a pasta. Exemplo:

> Exemplo abaixo com dados **fictícios** — nunca use uma fiscalização real como
> exemplo em documentação: este arquivo vai para um repositório público.

```
📦 Plano de organização — 3 pastas novas · 1 atualização · 2 vazias

── 1. "Jose fazenda" (nova) ─────────────────────────────
   Empregador: JOSE DA SILVA SANTOS · CPF 111.222.333-44 · Cidade/UF
   Renomear: Jose fazenda → JOSE DA SILVA SANTOS 11122233344
   DET: ABCDE12345FGHIJ — prazo 19/06/2026 (respondido: há relatório de atendimento)
   Mover: resposta do empregador → notificacao-ABCDE12345FGHIJ/ · fotos → fotos/

── 2. "ACME" (nova) ─────────────────────────────────────
   Empregador: ACME LTDA · CNPJ 11.222.333/0001-44
   ⚠️ Sem o PDF da notificação DET na pasta → DET fica em branco no memory.md
   (preencher depois; sem pergunta)

── 3. ... ───────────────────────────────────────────────

── Atualização: "BETA LTDA 11222333000144" ──────────────
   2 arquivos novos soltos na raiz → mover para notificacao-XYZ.../
   (memory.md será editado com backup antes)

Pastas vazias (nada a fazer): PASTA-A, PASTA-B
Nada será apagado. Confirma a organização completa?
```

Regras do plano:
- **Nome da pasta**: `<EMPREGADOR EM CAIXA ALTA> <identificador só dígitos>` (padrão do
  toolkit). Sem identificador encontrado → só o nome, e avise que o CNPJ/CPF será exigido
  no `/gera-ai`.
- **Notificações**: PDF na **raiz** como `notificacao-<CODIGO>.pdf`; resposta do
  empregador na subpasta `notificacao-<CODIGO>/` (mantendo `item1/`, `item2/`... ou
  `01 - .../`). É onde `/analise-preliminar`, `/det-630` e `/painel` procuram.
- **Nomes de download duplicado**: normalize sufixos do navegador —
  `notificacao-XYZ (1).pdf` → `notificacao-XYZ.pdf` (idem `relatorio-atendimento`). Se o
  nome-alvo já existir com outro conteúdo, mantenha os dois e relate.
- **Relação de autos**: subpasta `Relacao de autos/` (mesma que o `/autos-lavrados` usa
  para a relação .docx).
- **Interdição/embargo**: subpasta `interdicao-embargo/` — pasta **única por OS** (sem sufixo
  de data) onde vai TODO o material da medida: termo assinado, RT que a fundamenta, RT de
  manutenção, requerimento de suspensão e juntados do empregador, e os autos derivados
  (`autos.md` + TXT do `/gera-ai`). É a mesma pasta que o `/aft-rt-rgi` e o `/rt-manutencao`
  escrevem. Se já existir uma pasta antiga `Autos TE-TI DD-MM/`, inclua no plano
  renomeá-la para `interdicao-embargo/` (ou mover o conteúdo dela para lá).
- Fotos: subpasta `fotos/` (crie se estiverem soltas; renomeie `FOTO/` → `fotos/`).
- Trabalho do AFT em andamento (.docx/.md de minutas e análises): **fica na raiz**,
  intocado, anotado no memory.md.
- Ambiguidade real (ex.: dois empregadores diferentes nos documentos) → **pergunte**, não
  escolha em silêncio. Fora isso, nenhuma pergunta além da aprovação do plano.
- Só execute após a confirmação (única) do plano.

## FASE 4 — Executar e registrar

1. Para cada pasta do plano: renomeie a pasta (`mv`), depois mova/renomeie os arquivos.
2. Crie (ou atualize, com backup antes) o `memory.md` no esquema padrão do toolkit (o
   mesmo do `/nova-os`):

```markdown
---
empregador: <EMPREGADOR>
cnpj: "<só dígitos, ou vazio>"
municipio: <município ou vazio>
status: em_andamento
---
# <EMPREGADOR>

**CPF:** <formatado>   (ou **CNPJ:**, conforme o caso)

## Notificações DET
- [ ] <CODIGO> — prazo <dd/mm/aaaa>

## Autos de Infração
_(vazio)_

## Autos lavrados
_(vazio — preenchido a seguir pelo /autos-lavrados)_

## Registro de atividades
| Data | Ação | Detalhes |
|------|------|----------|
| <hoje> | OS importada e organizada | via /organiza-os — <N> notificações, resumo do que foi movido |
```

   - `prazo <dd/mm/aaaa>` literal na linha do DET (é o que o `/painel` vigia).
   - DET **respondido** → marque `[x]`. Evidências de resposta: pasta de resposta do
     empregador presente E/OU `relatorio-atendimento-<CODIGO>.pdf` na pasta. Na dúvida,
     deixe `[ ]` e relate no resumo.
   - Sem notificação DET na pasta → linha
     `- [ ] (código não localizado) — prazo (a preencher)` + observação; **não pergunte**.
   - Registre em observação os trabalhos já iniciados pelo AFT (minutas, análises,
     relatórios .docx encontrados na raiz).
3. Rode o guarda de PII em cada memory.md escrito — **sempre com a saída em UTF-8**, para
   o console Windows (cp1252) não derrubar o script:
   ```bash
   PYTHONIOENCODING=utf-8 python ~/.claude/skills/_scripts/checar_pii.py "<pasta da OS>/memory.md"
   ```

## FASE 5 — Encadeamento obrigatório: /autos-lavrados + painel

Depois de organizar tudo:

1. **Rode a skill `/autos-lavrados`** (varredura completa, sem argumento) — é ela que
   cruza as OS com os PDFs transmitidos no Sistema Auditor e preenche a seção
   `## Autos lavrados` de cada memory.md (e, por consequência, o painel). Se o Sistema
   Auditor não estiver acessível nesta máquina (pasta PRO inexistente), relate em uma
   linha e siga — não é bloqueante.
2. Regenere o painel:
   ```bash
   PYTHONIOENCODING=utf-8 python ~/.claude/skills/_scripts/gerar_painel.py "<pasta OS ATIVAS>"
   ```
3. **Abra o painel interativo automaticamente** para o AFT ver o panorama — sem
   perguntar:
   ```bash
   start "" "http://127.0.0.1:8347"     # Windows (macOS: open "http://127.0.0.1:8347")
   ```
   Se o servidor interativo não responder (instalação sem ele), abra o arquivo estático
   como reserva: `start "" "<pasta AFT>/painel.html"` — e lembre que o `/aft-atualizar`
   instala/repara o servidor.

4. Resumo final (uma mensagem só, com a tabela de tudo):

```
✅ OS ATIVAS organizada — <N> pastas novas · <M> atualizadas · <V> vazias

| OS (pasta nova) | Empregador · CNPJ | DET | Prazo | Respondido |
|---|---|---|---|---|
| ... | ... | ... | ... | ... |

🧾 Autos lavrados: <resultado do /autos-lavrados em uma linha>
❓ Não identificados (intocados): <lista ou "nenhum">
📊 Painel interativo aberto: http://127.0.0.1:8347

Próximos passos sugeridos: /analise-preliminar (respostas de DET) · /det-630 (omissões) ·
/analise-acidente (OS de acidente)
```

## Encadeamento

- Não substitui `/nova-os` (cadastro do zero, sem documentos) — esta skill parte de
  documentos existentes.
- A resposta do empregador organizada alimenta `/analise-preliminar`; a seção de autos
  do memory.md é preenchida/refinada pelo `/autos-lavrados` (FASE 5, automático).

## Regras

- **Nunca apague arquivo nenhum** — só renomear e mover dentro da própria pasta da OS.
  Não identificado = fica onde está, listado para o AFT. (Exceção de silêncio: locks
  `~$*` do Office não são nem mencionados.)
- **Nunca execute nada antes da aprovação do plano consolidado** (FASE 3) — mas é UMA
  aprovação para o lote inteiro, não uma por pasta.
- **Não pergunte o que dá para resolver sozinho**: pasta sem notificação → DET em
  branco; pasta vazia → relatar e seguir; nome de arquivo fora do padrão → normalizar
  no plano. Perguntas só para ambiguidade real.
- Se já existir pasta organizada com o mesmo CNPJ/CPF em OS ATIVAS, **não duplique**:
  proponha fundir (mover os arquivos novos para lá) dentro do próprio plano.
- Dados extraídos vêm **dos documentos** — não invente empregador, código, prazo ou
  número de AI que não estejam escritos neles. Campo não encontrado fica vazio.
- Código de DET: **só** o que está na linha "NOTIFICAÇÃO Nº" do PDF da notificação.
- Nome/CPF de trabalhador: nunca no chat nem no memory.md (só quantitativos).
- Encoding UTF-8; datas dd/mm/aaaa no corpo do memory.md.
