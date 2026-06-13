---
name: autos-lavrados
description: >
  Use SEMPRE que o AFT pedir para checar quais autos de infração já foram
  efetivamente lavrados (transmitidos no Sistema Auditor) de uma empresa em
  OS ATIVAS. Dispare com /autos-lavrados, "autos lavrados", "ver o que
  transmiti", "autos transmitidos", "checar lavratura", "estado de lavratura",
  "atualizar autos lavrados", "conferir Sistema Auditor", "snapshot dos autos".
  Aceita 0 ou 1 argumento. Sem argumento varre TODAS as OS ATIVAS e gera
  relatório por empresa. Com argumento (CNPJ 14 dígitos OU substring do nome)
  foca em uma OS. A skill lê os PDFs lavrados na pasta PRO do Sistema Auditor
  (C:\SistemasAFT\Auditor\Docs\AutosDeInfracao\PRO), extrai número do AI,
  ementa e histórico de cada auto, cruza com os rascunhos da pasta
  `Autos DD-MM/` (saídas do /gera-ai) para sinalizar pendências de transmissão,
  gera um `autos-lavrados.md` na pasta da OS e atualiza a seção
  `## Autos lavrados` do memory.md marcando [x] os lavrados e [ ] os pendentes.
  Read-only sobre o Sistema Auditor (nunca toca nos PDFs nem na pasta PRO).
---

# autos-lavrados — Snapshot do Sistema Auditor
**AFT Toolkit** (Windows)

## Quando usar

Use quando o AFT quer um retrato atualizado do que **efetivamente já foi transmitido** no Sistema Auditor — distinto dos rascunhos `.txt` gerados pelo `/gera-ai`, que são apenas o ponto de partida da importação.

Cenários típicos:
- Após uma sessão de lavratura no Sistema Auditor — atualizar a ficha da OS.
- Antes de redigir RT/relatório final — confirmar quais autos contam.
- Periodicamente — sweep de todas as OS ATIVAS para identificar pendências de transmissão.

> **Aviso de calibração (leia na primeira vez).** O extrator e o parser desta skill foram calibrados contra os PDFs do Sistema Auditor lidos com `pdftotext`. No toolkit o extrator padrão é o `pypdf` (puro Python, instalado pelo `/aft-setup`), cujo texto pode sair com espaçamento um pouco diferente. Na **primeira** execução, confira o `autos-lavrados.md` gerado contra o que você vê no Sistema Auditor (número do AI, ementa, data). Se algum campo vier truncado ou trocado, me avise — e, para fidelidade máxima, dá para instalar o `pdftotext` (poppler) no Windows, que a skill usa automaticamente se estiver no PATH.

## Pré-condições

- Sistema Auditor instalado neste computador (Windows), com a pasta padrão
  `C:\SistemasAFT\Auditor\Docs\AutosDeInfracao\PRO`. Se a instalação usar outro
  caminho, passe-o como 3º argumento ao script (veja Passo 2).
- Pasta da OS em `~/Documents/AFT/OS ATIVAS/<EMPREGADOR> <CNPJ>` com `memory.md`.
- `pypdf` instalado (`pip install pypdf` — o `/aft-setup` já faz). Se ausente, o
  scan reporta o auto como ilegível com a dica de instalação.

## Constantes

- **Pasta PRO (padrão Windows):** `C:\SistemasAFT\Auditor\Docs\AutosDeInfracao\PRO`
- **Padrão de pasta no Sistema Auditor:** `<até 16 chars do nome sanitizado>_<8 primeiros dígitos do CNPJ>`. Casos antigos podem aparecer truncados sem o sufixo CNPJ (ex: `LAVANDERIA_MORAI`).
- **Padrão de PDF lavrado:** `AI_<9 dígitos>.PDF` (ex: `AI_232272514.PDF`).

## Passo a passo

### Passo 1 — Resolver alvo(s)

1. Liste OS ATIVAS:
   ```bash
   ls ~/Documents/AFT/"OS ATIVAS"/
   ```
2. Para cada pasta, extraia `(empresa, cnpj14)` via regex `^(.+) (\d{14})$`. (Se o nome da pasta não terminar em 14 dígitos, leia o CNPJ do `memory.md` da OS.)
3. **Se o usuário forneceu argumento:**
   - 14 dígitos (limpando pontuação) → match exato por CNPJ.
   - Senão → substring case-insensitive do nome.
   - Múltiplos matches → use `AskUserQuestion` para escolher.
   - Zero matches → mensagem clara com a lista das OS e para.
4. **Sem argumento** → processa **todas as OS ATIVAS em lote**.

### Passo 2 — Para cada OS, chamar o scan

```bash
python ~/.claude/skills/autos-lavrados/scripts/scan_autos.py "<EMPRESA>" "<CNPJ14>"
```

> Se o Sistema Auditor estiver instalado em caminho diferente do padrão, acrescente o caminho da pasta `PRO` como 3º argumento:
> ```bash
> python ~/.claude/skills/autos-lavrados/scripts/scan_autos.py "<EMPRESA>" "<CNPJ14>" "D:\OutroCaminho\Auditor\Docs\AutosDeInfracao\PRO"
> ```

Capture o JSON do stdout. Estrutura:

```json
{
  "empresa": "...", "cnpj": "...",
  "pasta_pro": "C:\\SistemasAFT\\...\\PRO",
  "pasta_auditor": "C:\\...\\CHANGAI_SORVETES_00241190" | null,
  "match_estrategia": "cnpj_raiz" | "nome_prefixo" | "nao_encontrado",
  "candidatos_alternativos": ["..."],
  "autos": [
    { "pdf": "...AI_232272514.PDF", "numero_ai": "23.227.251-4",
      "ementa_num": "001839-2", "ementa_descricao": "Deixar de controlar...",
      "historico_raw": "Trata-se de fiscalização...", "data_lavratura": "13/03/2026",
      "cnpj_autuado": "...", "razao_social_autuado": "...", "warnings": [] }
  ],
  "errors": []
}
```

**Tratamento de casos:**
- `pasta_auditor: null` + `match_estrategia: nao_encontrado` + `candidatos_alternativos: []` → OS sem autos transmitidos. Siga ao Passo 4 com lista vazia.
- `candidatos_alternativos` não vazio → ambiguidade. Use `AskUserQuestion` listando os candidatos (ou "nenhum desses").
- `match_estrategia: nome_prefixo` → **cross-check de CNPJ**: compare `autos[].cnpj_autuado` com o CNPJ da OS (sem formatação):
  - **Todos batem** → prossiga; registre no relatório "Match por prefixo de nome, CNPJ confere".
  - **Algum diverge** → pare e use `AskUserQuestion` mostrando o CNPJ/razão divergentes; o AFT decide.
  - **Mistura** → trate como divergência total (pergunte).
- `errors` não vazio → reporte ao AFT e pare essa OS (em modo batch, siga com as outras).

### Passo 3 — Resumir cada histórico

Para cada item em `autos`, produza `resumo_irregularidade` (1–3 frases) a partir de `historico_raw`:

**Manter:** o que foi constatado na inspeção — o fato gerador da autuação.

**Descartar:** parágrafo introdutório ("Trata-se de fiscalização mista…"); listagem nominal de empregados (nomes, CPFs, datas); observações finais ("Lavrado no local…"); base legal e capitulação; frases conectivas.

**Estilo:** seco, descritivo, terceira pessoa. Direto ao fato.

> Privacidade: o `resumo_irregularidade` **não deve conter nome nem CPF** de trabalhador — descreva a irregularidade em si. Os PDFs do Sistema Auditor trazem dados pessoais; eles ficam na pasta da OS, não no chat nem em ecos.

### Passo 4 — Cruzar com rascunhos da pasta `Autos DD-MM/`

1. Liste subpastas `Autos *` na pasta da OS:
   ```bash
   ls -d ~/Documents/AFT/"OS ATIVAS"/"<PASTA_EMPRESA>"/Autos*/ 2>/dev/null
   ```
2. Em cada subpasta, leia os `.txt` (saídas do `/gera-ai`) e os `autos*.md` (rascunhos). Extraia números de ementa via regex `(\d{6}-\d)` ou `Ementa:\s*(\d{6,7})`. Normalize removendo hífen (7 dígitos) para comparar.
3. Compare com `ementa_num` dos autos lavrados (também normalizado).
4. Classifique:
   - **Lavrado** = ementa presente no scan.
   - **Pendente de transmissão** = ementa em rascunho, ausente no scan.
   - **Lavrado sem rascunho local** = ementa no scan, ausente nos rascunhos (não é erro — apenas sinalize).

> A chave de cruzamento é o **número da ementa**, não o nome do arquivo.

### Passo 5 — Gerar `autos-lavrados.md` na pasta da OS

Escreva em `<pasta-OS>/autos-lavrados.md` (sobrescreve com aviso no chat se já existir):

```markdown
# Autos lavrados — <empresa>

> _Snapshot gerado em <YYYY-MM-DD>. Fonte: Sistema Auditor._
> _Pasta no auditor: `<basename pasta_auditor>` (match: <match_estrategia>)._

## Resumo

| Estado | Quantidade |
|---|---|
| Lavrados (transmitidos) | <N> |
| Pendentes de transmissão | <M> |
| Lavrados sem rascunho local | <K> |

## Detalhamento — autos lavrados

### AI <numero_ai> · Ementa <ementa_num>
**Descrição da ementa:** <ementa_descricao>
**Constatação:** <resumo_irregularidade>
**Lavrado em:** <data_lavratura>
**PDF:** `<pdf path completo>`

(repetir para cada auto)

## Pendentes de transmissão
- Ementa <num> — `<arquivo do rascunho>` — não localizado no Sistema Auditor

## Lavrados sem rascunho local
- Ementa <num> — AI <numero_ai> — sem rascunho correspondente em `Autos */`
```

**Se `pasta_auditor` é null** (OS sem autos transmitidos), grave mesmo assim:
```markdown
# Autos lavrados — <empresa>

> _Snapshot gerado em <YYYY-MM-DD>._

Nenhum auto lavrado encontrado no Sistema Auditor para esta empresa.
<linha sobre pendentes de transmissão, se houver rascunho>
```

### Passo 6 — Atualizar `memory.md`

Use a tool `Edit` para modificar **apenas a seção `## Autos lavrados`** do `memory.md` da OS (crie a seção, antes de `## Registro de atividades`, se não existir):

```markdown
## Autos lavrados
- [x] Ementa 001839-2 — papeletas "ponto britânico" — AI 23.227.251-4
- [x] Ementa 001774-4 — empregados sem registro — AI 23.285.483-1
- [ ] Ementa 312358-8 — pendente de transmissão (rascunho em `Autos 18-05/`)
```

Regras:
- `[x]` = ementa lavrada (presente no scan); `[ ]` = ementa só em rascunho.
- 1 linha por auto, no máximo 1 frase curta (do `resumo_irregularidade`, sem dados pessoais).
- **Chave de dedup: número da ementa.** Se a linha já existe, **substitua** (mantém a ordem); se nova, **append**. As skills `/inspecao-inicial`, `/det-630` e `/jornada-auto-afd-aej` deixam linhas `- [ ]` aqui — esta skill as promove a `- [x]` quando confirma a transmissão.

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
🗂️  Pasta auditor: <basename> (match: <estrategia>)

Resumo:
  Lavrados: <N>
  Pendentes de transmissão: <M>  → <lista de ementas>
  Lavrados sem rascunho local: <K>
```

**Modo batch (todas OS ATIVAS):** tabela compacta:
```
OS                                  Lavrados  Pendentes  Match           Status
LAVANDERIA MORAIS LTDA              N         M          nome_prefixo    ⚠
APARAS XANDAO COMERCIO…             N         0          cnpj_raiz       ✓
```
Use `⚠` para linhas com pendentes > 0 ou match por nome_prefixo; `✓` para `lavrados > 0 && pendentes == 0 && match == cnpj_raiz`.

## Idempotência

- Rodar 2× sobrescreve `autos-lavrados.md` (aviso no chat).
- `memory.md` é editado por chave (número da ementa) — não duplica linhas.
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

## Regras

- **Read-only no Sistema Auditor.** Nunca tocar nos PDFs nem na pasta `PRO`.
- Em modo batch, falha em uma OS **não trava** as outras — registra o erro na linha e continua.
- Não ecoar no chat nome/CPF de trabalhador extraído dos PDFs — só a descrição da irregularidade.
