---
name: aft-autos-lavrados
model: sonnet
effort: medium
allowed-tools: Read, Glob, Grep, Bash, Write, Edit, AskUserQuestion
description: >
  Use quando o AFT quiser checar quais autos de infração já foram
  efetivamente transmitidos no Sistema Auditor. Dispare com /aft-autos-
  lavrados, "autos lavrados", "ver o que transmiti", "autos transmitidos",
  "checar lavratura", "atualizar autos lavrados", "conferir Sistema
  Auditor", "snapshot dos autos". Aceita 0 ou 1 argumento (CNPJ ou parte do
  nome); sem argumento varre todas as OS ATIVAS. Read-only sobre o Sistema
  Auditor.
---

# autos-lavrados — Snapshot do Sistema Auditor
**AFT Toolkit** (Windows)

> **Onde ficam as pastas das OS.** O AFT pode ter mudado a pasta de trabalho de
> lugar (HD externo, nuvem, outro disco). Nunca presuma `~/Documents/AFT`:
> resolva **uma vez, no início**, e use o que voltar onde este texto disser
> `<OS_ATIVAS>` (a pasta que contém as OS) ou `<PASTA_AFT>` (a pasta acima dela).
>
> **Nas mensagens ao AFT, escreva o caminho de verdade** — nunca ecoe
> `<OS_ATIVAS>`/`<PASTA_AFT>` na tela: ele precisa saber onde abrir a pasta.
>
> ```bash
> python ~/.claude/skills/_scripts/pasta_aft.py --os-ativas   # -> <OS_ATIVAS>
> python ~/.claude/skills/_scripts/pasta_aft.py --path        # -> <PASTA_AFT>
> ```


## Quando usar

Use quando o AFT quer um retrato atualizado do que **efetivamente já foi transmitido** no Sistema Auditor — distinto dos rascunhos `.txt` gerados pelo `/aft-gera-ai`, que são apenas o ponto de partida da importação.

Cenários típicos:
- Após uma sessão de lavratura no Sistema Auditor — atualizar a ficha da OS.
- Antes de redigir RT/relatório final — confirmar quais autos contam.
- Periodicamente — sweep de todas as OS ATIVAS para identificar pendências de transmissão.

> **Aviso de calibração (leia na primeira vez).** O extrator e o parser desta skill foram calibrados contra os PDFs do Sistema Auditor lidos com `pdftotext`. No toolkit o extrator padrão é o `pypdf` (puro Python, instalado pelo `/aft-setup`), cujo texto pode sair com espaçamento um pouco diferente. Na **primeira** execução, confira o `autos-lavrados.md` gerado contra o que você vê no Sistema Auditor (número do AI, ementa, data). Se algum campo vier truncado ou trocado, me avise — e, para fidelidade máxima, dá para instalar o `pdftotext` (poppler) no Windows, que a skill usa automaticamente se estiver no PATH.

## Pré-condições

- Sistema Auditor instalado, com a pasta padrão `C:\SistemasAFT\Auditor\Docs\AutosDeInfracao\PRO`.
  - **Windows:** o script usa esse caminho automaticamente.
  - **Mac com Parallels:** o disco C: da máquina virtual precisa estar compartilhado/montado (aparece no Finder como `/Volumes/[C] Windows 11/…`). O script **detecta sozinho** a pasta PRO sob `/Volumes/*/SistemasAFT/…` — não precisa informar caminho. Se o volume não estiver montado, peça ao AFT (em uma frase) para ativar o compartilhamento do disco no Parallels.
  - Instalação em caminho fora do padrão (qualquer SO): passe a pasta `PRO` como 3º argumento ao script (veja Passo 2).
- Pasta da OS em `<OS_ATIVAS>/<NOME_DA_OS>` com `memory.md` (o nome pode ou não conter o CNPJ — ver Passo 1).
- `pypdf` instalado (`pip install pypdf` — o `/aft-setup` já faz). Se ausente, o
  scan reporta o auto como ilegível com a dica de instalação.
- **Nada de conversor de PDF:** o documento final da Relação de autos é o
  `.docx`. A skill não converte para PDF e não depende de LibreOffice nem de
  automação do Word. Se o AFT quiser um PDF, é abrir o `.docx` no Word e usar
  Arquivo > Salvar como... > PDF.
- **Nada de `zip`/`unzip`:** o `.docx` é montado com a biblioteca padrão do
  Python. Uma instalação limpa do Windows não tem esses comandos (e o Git for
  Windows traz só o `unzip.exe`), então o script nunca depende deles.

## Constantes

- **Pasta PRO (padrão Windows):** `C:\SistemasAFT\Auditor\Docs\AutosDeInfracao\PRO`
- **Padrão de pasta no Sistema Auditor:** `<até 16 chars do nome sanitizado>_<8 primeiros dígitos do CNPJ ou CPF/CAEPF>`. **Toda pasta criada pelo Sistema Auditor termina com esses 8 dígitos** — é a chave de match mais confiável (ex.: `CONSORCIO_SQ_APA_56309119`, do CNPJ `56.309.119/0001-03`). Casos antigos podem aparecer truncados sem o sufixo (ex: `LAVANDERIA_MORAI`).
- **Padrão de PDF lavrado:** `AI_<9 dígitos>.PDF` (ex: `AI_232272514.PDF`).

## Passo a passo

### Passo 1 — Resolver alvo(s)

1. Liste OS ATIVAS:
   ```bash
   ls "<OS_ATIVAS>"/
   ```
2. Para cada pasta, descubra o **identificador** (CNPJ/CPF) do autuado, nesta ordem:
   - regex `^(.+) (\d{11,14})$` sobre o nome da pasta (14 díg. = CNPJ, 11 = CPF/CAEPF);
   - senão, o campo `cnpj:` (ou `**CNPJ:**`/`**CPF:**`) do `memory.md` da OS;
   - **se ainda assim não houver identificador** (OS aberta com nome livre, sem CNPJ — permitido desde a atualização do `/aft-nova-os`), veja o passo 5.
3. **Se o usuário forneceu argumento:**
   - 11 ou 14 dígitos (limpando pontuação) → match exato por CNPJ/CPF.
   - exatamente 8 dígitos → o AFT já informou o prefixo direto; use-o como está.
   - senão → substring case-insensitive do nome.
   - Múltiplos matches → use `AskUserQuestion` para escolher.
   - Zero matches → mensagem clara com a lista das OS e para.
4. **Sem argumento** → processa **todas as OS ATIVAS em lote**.
5. **OS sem CNPJ/CPF identificável** — como toda pasta do Sistema Auditor termina com os **8 primeiros dígitos** do CNPJ/CPF fiscalizado, esse prefixo é suficiente para achar os autos:
   - **Modo OS única** → use `AskUserQuestion` (ou pergunte diretamente) pelos **8 primeiros dígitos do CNPJ ou CPF** da fiscalizada e passe-os ao script no lugar do CNPJ. Explique em uma linha por que precisa deles (é o sufixo da pasta no Sistema Auditor).
   - **Modo lote** → **não** interrompa o lote perguntando: pule essa OS e registre na tabela final o status `sem CNPJ — rode /aft-autos-lavrados "<nome>" e informe os 8 dígitos`.
   - Se o AFT informar só os 8 dígitos, o cross-check de CNPJ do Passo 2 compara apenas esse prefixo (avise que a conferência é parcial).

### Passo 1b — Despachar para o agente isolado (padrão)

> **Se você É o agente `aft-autos-lavrados`** (foi invocado pela tool Agent), pule este
> passo: execute os Passos 2–6 diretamente, seguindo as regras do seu prompt de agente
> (nunca perguntar; pontos de decisão viram a seção "Decisões pendentes do AFT").

Com o(s) alvo(s) resolvido(s) no Passo 1, a varredura pesada (Passos 2–6) roda, por
padrão, no **agente isolado** `aft-autos-lavrados` (instalado em `~/.claude/agents/`):
a leitura dos PDFs acontece fora da conversa principal, e aqui só chega o relatório.

1. Invoque a tool `Agent` com `subagent_type: "aft-autos-lavrados"` e um prompt com:
   (a) a **lista de alvos** — caminho absoluto da pasta da OS + CNPJ/CPF ou 8 dígitos,
   um por linha (OS sem identificador ficam de fora, com a linha de status do item 5
   do Passo 1); (b) o `python_path` do `aft-config.md` (macOS: `python3`); (c) a pasta
   PRO alternativa, se a instalação for fora do padrão; (d) o caminho absoluto deste
   manual (`~/.claude/skills/aft-autos-lavrados/SKILL.md`, com o `~` expandido).
   No **modo lote** (todas as OS), rode o agente em segundo plano se a tool permitir
   (`run_in_background`) e avise o AFT que a tabela chega quando a varredura terminar.
2. Ao receber o retorno, apresente o relatório do Passo 7 ao AFT (é o próprio texto
   devolvido pelo agente — confira o formato e repasse).
3. **Decisões pendentes:** se a seção "Decisões pendentes do AFT" vier com itens,
   conduza cada um com `AskUserQuestion` (as mesmas opções que os Passos 1, 2 e 2.5
   definem) e **aplique a resposta você mesmo** — são edições pequenas: promover ou
   rebaixar linhas no `memory.md` e no `autos-lavrados.md`, ou re-despachar o agente
   só para a OS destravada (ex.: pasta ambígua resolvida, 8 dígitos informados).
4. **Fallback (sem agente):** se a invocação falhar porque o tipo `aft-autos-lavrados`
   não existe (agente não instalado ou app não reiniciado após a atualização), execute
   você mesmo os Passos 2–6 abaixo, inline, como esta skill sempre funcionou —
   inclusive as perguntas interativas — e sugira ao AFT rodar `/aft-atualizar` depois.

### Passo 2 — Para cada OS, chamar o scan

```bash
python ~/.claude/skills/aft-autos-lavrados/scripts/scan_autos.py "<EMPRESA>" "<CNPJ_OU_8DIGITOS>"
```

O 2º argumento aceita o CNPJ (14 díg.), o CPF/CAEPF (11 díg.) ou apenas os **8 primeiros dígitos** (Passo 1.5). No Windows e no Mac com Parallels o script acha a pasta `PRO` sozinho (no Mac, sob `/Volumes/*/SistemasAFT/…`).

> Só se a instalação usar um caminho fora do padrão, acrescente a pasta `PRO` como 3º argumento:
> ```bash
> # Windows:
> python ~/.claude/skills/aft-autos-lavrados/scripts/scan_autos.py "<EMPRESA>" "<CNPJ_OU_8DIGITOS>" "D:\OutroCaminho\Auditor\Docs\AutosDeInfracao\PRO"
> # Mac/Parallels, se o volume tiver outro nome:
> python ~/.claude/skills/aft-autos-lavrados/scripts/scan_autos.py "<EMPRESA>" "<CNPJ_OU_8DIGITOS>" "/Volumes/<NOME_DO_VOLUME>/SistemasAFT/Auditor/Docs/AutosDeInfracao/PRO"
> ```

Capture o JSON do stdout. Estrutura:

```json
{
  "empresa": "...", "cnpj": "...",
  "pasta_pro": "C:\\SistemasAFT\\...\\PRO",
  "pasta_auditor": "C:\\...\\EMPRESA_EXEMPLO_11222333" | null,
  "match_estrategia": "cnpj_raiz" | "nome_prefixo" | "nao_encontrado",
  "candidatos_alternativos": ["..."],
  "autos": [
    { "pdf": "...AI_232272514.PDF", "numero_ai": "23.227.251-4",
      "ementa_num": "001839-2", "ementa_descricao": "Deixar de controlar...",
      "historico_raw": "Trata-se de fiscalização...", "data_lavratura": "13/03/2026",
      "cnpj_autuado": "...", "razao_social_autuado": "...",
      "status_duplicidade": "unico", "warnings": [] }
  ],
  "errors": []
}
```

Cada auto traz `status_duplicidade` (`unico` · `mantido_ultimo` · `cancelado_presumido` · `manter_todos` · `revisar`) e, quando cancelado, `substituido_por` com o AI do válido — o script já resolve isso; a interpretação está no Passo 2.5.

**Tratamento de casos:**
- `pasta_auditor: null` + `match_estrategia: nao_encontrado` + `candidatos_alternativos: []` → OS sem autos transmitidos. Siga ao Passo 4 com lista vazia.
- `candidatos_alternativos` não vazio → ambiguidade. Use `AskUserQuestion` listando os candidatos (ou "nenhum desses").
- `match_estrategia: nome_prefixo` → **cross-check de CNPJ**: compare `autos[].cnpj_autuado` com o CNPJ da OS (sem formatação):
  - **Todos batem** → prossiga; registre no relatório "Match por prefixo de nome, CNPJ confere".
  - **Algum diverge** → pare e use `AskUserQuestion` mostrando o CNPJ/razão divergentes; o AFT decide.
  - **Mistura** → trate como divergência total (pergunte).
- `errors` não vazio → reporte ao AFT e pare essa OS (em modo batch, siga com as outras).

### Passo 2.5 — Resolver duplicidade de ementa (autos cancelados/re-lavrados)

Em regra, **cada ementa corresponde a um único auto válido**. Quando o AFT erra a lavratura, cancela o auto e re-lavra outro com a mesma ementa — mas o PDF do cancelado continua na pasta do Sistema Auditor. Como a numeração dos autos é crescente (o último dígito é só verificador), o auto de **maior número** é o último lavrado = o válido. O script já classifica cada auto em `status_duplicidade`; interprete assim:

- **`unico`** e **`mantido_ultimo`** → auto **válido**. Segue para o Detalhamento (Passos 3–5).
- **`cancelado_presumido`** → auto antigo **substituído** pelo `substituido_por`. **Não** conta como lavrado: não entra no Detalhamento nem recebe `[x]` no memory.md; vai só na seção "Autos substituídos" do relatório (Passo 5).
- **`manter_todos`** → ementa que legitimamente rende vários autos (ex.: `001960-7`). **Todos válidos**, sem perguntar nada.
- **`revisar`** → ementa das que exigem decisão do AFT (`001775-2`, `001774-4`, `002270-5`, `002269-1`) com duplicata detectada. **Avise e pergunte** com `AskUserQuestion`:
  - mostre a ementa e os AIs em duplicidade;
  - opções: **"Relacionar todos"** (trata todos como válidos) ou **"Só o último lavrado"** (mantém o de maior número; os demais viram `cancelado_presumido`).
  - **Modo lote** (varredura de todas as OS): **não** interrompa perguntando — relacione **todos** os autos `revisar` como válidos e marque a OS com `⚠` para o AFT reabrir em modo OS única e decidir.

> A comparação de "qual é o último" usa o número-base do AI (8 primeiros dígitos, sem o verificador). Nunca descarte um auto sem que o script o tenha marcado `cancelado_presumido` (ou o AFT tenha escolhido "só o último").

### Passo 3 — Resumir cada histórico

Para cada auto **válido** (Passo 2.5 — `unico`, `mantido_ultimo`, `manter_todos` ou `revisar` mantido), produza `resumo_irregularidade` (1–3 frases) a partir de `historico_raw`. Autos `cancelado_presumido` não precisam de resumo (só entram na seção "Autos substituídos" com AI + ementa):

**Manter:** o que foi constatado na inspeção — o fato gerador da autuação.

**Descartar:** parágrafo introdutório ("Trata-se de fiscalização mista…"); listagem nominal de empregados (nomes, CPFs, datas); observações finais ("Lavrado no local…"); base legal e capitulação; frases conectivas.

**Estilo:** seco, descritivo, terceira pessoa. Direto ao fato.

> Privacidade: o `resumo_irregularidade` **não deve conter nome nem CPF** de trabalhador — descreva a irregularidade em si. Os PDFs do Sistema Auditor trazem dados pessoais; eles ficam na pasta da OS, não no chat nem em ecos.

### Passo 4 — Cruzar com rascunhos da pasta `Autos DD-MM/`

1. Liste as subpastas de lote. No layout de 22/07/2026 elas ficam em `AUTOS/`; OS ainda
   não migradas as têm na raiz — procure **nos dois lugares**:
   ```bash
   ls -d "<OS_ATIVAS>"/"<PASTA_EMPRESA>"/AUTOS/Autos*/ 2>/dev/null
   ls -d "<OS_ATIVAS>"/"<PASTA_EMPRESA>"/Autos*/ 2>/dev/null
   ```
2. Em cada subpasta, leia os `.txt` (saídas do `/aft-gera-ai`) e os `autos*.md` (rascunhos). Extraia números de ementa via regex `(\d{6}-\d)` ou `Ementa:\s*(\d{6,7})`. Normalize removendo hífen (7 dígitos) para comparar.
3. Compare com `ementa_num` dos autos lavrados (também normalizado).
4. Classifique:
   - **Lavrado** = ementa presente entre os autos **válidos** do scan (Passo 2.5).
   - **Pendente de transmissão** = ementa em rascunho, ausente no scan.
   - **Lavrado sem rascunho local** = ementa no scan, ausente nos rascunhos (não é erro — apenas sinalize).

> A chave de cruzamento é o **número da ementa**, não o nome do arquivo. Ignore os autos `cancelado_presumido` aqui — quem representa a ementa é o auto válido que os substituiu.

### Passo 5 — Gerar `autos-lavrados.md` na pasta da OS

Escreva em `<pasta-OS>/autos-lavrados.md` (sobrescreve com aviso no chat se já existir):

```markdown
# Autos lavrados — <empresa>

> _Snapshot gerado em <YYYY-MM-DD>. Fonte: Sistema Auditor._
> _Pasta no auditor: `<basename pasta_auditor>` (match: <match_estrategia>)._

## Resumo

| Estado | Quantidade |
|---|---|
| Lavrados válidos (transmitidos) | <N> |
| Substituídos (presumidamente cancelados) | <C> |
| Pendentes de transmissão | <M> |
| Lavrados sem rascunho local | <K> |

## Detalhamento — autos lavrados

### Nº <numero_ai>
**Ementa <ementa_num> · <NR-XX item Y.Y.Y — quando identificáveis na descrição>**
**Descrição da ementa:** <ementa_descricao>
**Constatação:** <resumo_irregularidade>
**Lavrado em:** <data_lavratura>

(repetir para cada auto VÁLIDO — Passo 2.5)

> **Número do AI é obrigatório** no título de cada auto (`### Nº ...`) — vem do campo `numero_ai` do scan (derivado do nome do arquivo `AI_<9 díg.>.PDF`, ex.: `AI_232842094.PDF` → `23.284.209-4`). Nunca omita nem invente. Como o número do AI é único por auto (a mesma ementa pode se repetir em autos diferentes), ele é a identificação de cada bloco. **Não inclua** no detalhamento caminho de PDF nem de rascunho — só os campos acima.

## Autos substituídos (presumidamente cancelados)
- Ementa <num> — AI <numero_ai> — substituído por AI <substituido_por> (re-lavratura; PDF antigo permanece na pasta)

## Pendentes de transmissão
- Ementa <num> — `<arquivo do rascunho>` — não localizado no Sistema Auditor

## Lavrados sem rascunho local
- Ementa <num> — AI <numero_ai> — sem rascunho correspondente em `Autos */`
```

> A seção "Autos substituídos" só aparece se houver autos `cancelado_presumido`. É informativa (transparência da re-lavratura) e **não** conta como lavrado.

**Se `pasta_auditor` é null** (OS sem autos transmitidos), grave mesmo assim:
```markdown
# Autos lavrados — <empresa>

> _Snapshot gerado em <YYYY-MM-DD>._

Nenhum auto lavrado encontrado no Sistema Auditor para esta empresa.
<linha sobre pendentes de transmissão, se houver rascunho>
```

### Passo 5.5 — Gerar "Relação de autos lavrados" (.docx)

Sempre que o Passo 5 gravar um `autos-lavrados.md` com pelo menos um auto **válido** no Detalhamento, gere também o documento formatado para juntar ao processo:

```bash
python3 ~/.claude/skills/aft-autos-lavrados/scripts/gera_relacao_autos.py "<pasta-OS>/autos-lavrados.md"
```

O script:
- cria (se não existir) a pasta `<pasta-OS>/AUTOS/Relacao de autos/` (em OS ainda não migradas, sem a caixa `AUTOS/`, usa o lugar antigo `<pasta-OS>/Relacao de autos/`);
- gera `relacao-autos.docx` a partir do template oficial (`scripts/template-relacao-autos.docx`) — cabeçalho com os logos SIT/AFT **nunca é alterado**; corpo com EMPREGADOR + INSCRIÇÃO, autos agrupados por data (mais antigo → mais recente, ordem do MD preservada), fonte Times New Roman 12pt, texto sempre justificado.

O `.docx` é o documento final — **a skill não gera PDF** e não depende de LibreOffice nem do Word. Se o AFT pedir um PDF, oriente-o a abrir o `.docx` no Word e usar **Arquivo > Salvar como... > PDF**.

Leia o stdout do script:
- `OK docx: ...` → o documento foi gerado; informe o caminho ao AFT.
- Se o script parar com um **traceback** e o aviso de que um ticket foi gravado em `<pasta AFT>/tickets/` → é defeito do toolkit, não da máquina do AFT. Diagnostique e conserte se der; depois ofereça a skill `/aft-erro` para completar o ticket com o contexto e encaminhá-lo ao mantenedor.
- Se o `autos-lavrados.md` não tiver nenhum auto válido no Detalhamento (OS sem autos lavrados), pule este passo — não há o que relacionar.

> Read-only sobre o template: o script sempre lê `template-relacao-autos.docx` e grava um `.docx` novo em `AUTOS/Relacao de autos/`; o template da skill nunca é sobrescrito.

### Passo 6 — Atualizar `memory.md`

Use a tool `Edit` para modificar **apenas a seção `## Autos lavrados`** do `memory.md` da OS (crie a seção, antes de `## Registro de atividades`, se não existir):

```markdown
## Autos lavrados
- [x] Ementa 001839-2 — papeletas "ponto britânico" — AI 23.227.251-4
- [x] Ementa 001774-4 — empregados sem registro — AI 23.285.483-1
- [ ] Ementa 312358-8 — pendente de transmissão (rascunho em `Autos 18-05/`)
- (cancelado) AI 23.324.627-4 — ementa 101114-6, substituído por AI 23.325.349-1
```

Regras:
- `[x]` = auto **válido** lavrado (Passo 2.5); `[ ]` = ementa só em rascunho (pendente); linha `(cancelado)` sem checkbox = auto substituído (não conta).
- 1 linha por auto, no máximo 1 frase curta (do `resumo_irregularidade`, sem dados pessoais).
- **Chave de dedup das linhas `[x]` e `(cancelado)`: número do AI** (único por auto — permite ementas legitimamente repetidas, ex.: `001960-7`). As linhas `[ ]` pendentes, que ainda não têm AI, seguem sendo chaveadas por ementa.
- **Promoção de pendências:** as skills `/aft-auditoria-geral`, `/aft-det-630` e `/aft-jornada-auto-afd-aej` deixam linhas `- [ ]` (por ementa) aqui. Ao confirmar a transmissão, promova a `- [x]` acrescentando o AI. Se a ementa tem **um** auto válido, promova a própria linha; se tem **vários** (`manter_todos` ou "relacionar todos"), gere **uma linha `[x]` por AI**.
- Se a linha (por AI, ou por ementa nas pendentes) já existe, **substitua** mantendo a ordem; se nova, **append**.

Depois, adicione 1 linha em `## Registro de atividades` (append na tabela; não toque nas existentes):
```markdown
| <YYYY-MM-DD> | Snapshot autos lavrados | <N> lavrados, <M> pendentes |
```

> O `memory.md` do toolkit é um markdown simples (sem schema rígido nem limite de linhas) — basta editar as duas seções com a tool `Edit`, sem validador externo.

### Passo 7 — Reportar ao AFT

**Modo OS única:**
```
✅ Snapshot de autos lavrados — <empresa>

📄 Relatório: <caminho do autos-lavrados.md>
📑 Relação formatada: <caminho do relacao-autos.docx>
🗂️  Pasta auditor: <basename> (match: <estrategia>)

Resumo:
  Lavrados válidos: <N>
  Substituídos (cancelados): <C>  → <lista de AIs, se houver>
  Pendentes de transmissão: <M>  → <lista de ementas>
  Lavrados sem rascunho local: <K>
```
Se houve autos `revisar` (ementas que exigem decisão), registre também a decisão tomada pelo AFT.

**Modo batch (todas OS ATIVAS):** tabela compacta:
```
OS                                  Lavrados  Cancel.  Pendentes  Match           Status
LAVANDERIA MORAIS LTDA              N         C        M          nome_prefixo    ⚠
APARAS XANDAO COMERCIO…             N         0        0          cnpj_raiz       ✓
```
Use `⚠` para linhas com pendentes > 0, com autos `revisar` não decididos, ou match por nome_prefixo; `✓` para `lavrados > 0 && pendentes == 0 && sem revisar pendente && match == cnpj_raiz`. Para OS sem CNPJ/CPF identificável (puladas no lote — Passo 1.5), use `—` na coluna Match e o status `sem CNPJ: rode /aft-autos-lavrados "<nome>" + 8 dígitos`.

## Idempotência

- Rodar 2× sobrescreve `autos-lavrados.md` (aviso no chat).
- `memory.md` é editado por chave (número do AI nas linhas `[x]`/`(cancelado)`; ementa nas `[ ]` pendentes) — não duplica linhas.
- Linha em "Registro de atividades" é append-only.
- A extração é determinística — mesma entrada, mesma saída.

## Erros comuns e tratamento

| Sintoma | Tratamento |
|---|---|
| Pasta PRO não encontrada | Mensagem clara: confirmar se o Sistema Auditor está instalado; oferecer rodar o scan com caminho alternativo (3º argumento) |
| `pypdf` ausente | Auto vem com aviso "extração falhou"; oriente `pip install pypdf` (ou rode `/aft-setup`) |
| Vários candidatos de pasta | `AskUserQuestion` para o AFT escolher |
| PDF corrompido/ilegível | Entra no relatório como "AI <numero> — leitura falhou"; não atualiza o memory.md para essa linha |
| OS sem autos nem rascunhos | Gera `autos-lavrados.md` com "nenhum auto" e registra só o snapshot do dia |
| Ementa duplicada em 2+ autos | Regra do Passo 2.5: mantém o último (maior AI) como válido; anteriores viram "substituídos". Exceção `001960-7` (todos válidos) e `001775-2`/`001774-4`/`002270-5`/`002269-1` (pergunta ao AFT) |

## Regras

- **Read-only no Sistema Auditor.** Nunca tocar nos PDFs nem na pasta `PRO`.
- Em modo batch, falha em uma OS **não trava** as outras — registra o erro na linha e continua.
- Não ecoar no chat nome/CPF de trabalhador extraído dos PDFs — só a descrição da irregularidade.
- **Nunca descarte um auto por conta própria.** Só saem do rol de válidos os que o script marcou `cancelado_presumido` (regra determinística) ou os que o AFT escolheu excluir num caso `revisar`. Na dúvida, mantenha e sinalize.
