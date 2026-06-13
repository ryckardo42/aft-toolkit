---
name: aft-setup
description: >
  Use SEMPRE que o Auditor-Fiscal do Trabalho (AFT) acabou de instalar o AFT Toolkit
  e precisa configurá-lo pela primeira vez, ou quando quiser revisar/alterar a
  configuração. Acione com "/aft-setup", "configurar o toolkit", "primeira
  configuração", "configuração inicial", "setup", "mudar minha CIF", "mudar minha
  UORG". A skill verifica os pré-requisitos (Python, pip), cria a estrutura de
  pastas de trabalho em ~/Documents/AFT/, coleta os dados do auditor (nome, CIF,
  UORG, município) uma única vez, grava tudo em aft-config.md, instala as
  bibliotecas Python necessárias e orienta a configuração do NotebookLM. Todas as
  outras skills do toolkit leem essa configuração — sem ela, pedem para rodar
  /aft-setup primeiro.
---

# aft-setup — Configuração inicial do AFT Toolkit

## Objetivo

Deixar o computador do AFT pronto para usar todas as skills do toolkit. Roda uma única
vez (ou quando o auditor quiser mudar algo). Ao final, existe:

- A pasta de trabalho `~/Documents/AFT/` com `OS ATIVAS/` e `OS ARQUIVADAS/`.
- O arquivo `~/Documents/AFT/aft-config.md` com os dados do auditor e da unidade.
- As bibliotecas Python instaladas (`pillow`, `pikepdf`).
- (Opcional, recomendado) O CLI do NotebookLM autenticado.

Tom: acolhedor e paciente — o público é um colega que pode estar usando o Claude Code
pela primeira vez. Explique o que cada passo faz em uma frase, sem jargão.

---

## Passo 1 — Verificar e completar pré-requisitos (você instala, não o AFT)

Rode e interprete:

```bash
python --version || python3 --version
git --version
```

Se algo faltar, **não mande o AFT instalar manualmente — instale você mesmo** via
winget (o AFT só precisa aprovar os comandos):

- **Python ausente**:
  ```bash
  winget install --id Python.Python.3.12 -e --accept-source-agreements --accept-package-agreements
  ```
  Depois confirme com `python --version`. Se o comando ainda não for encontrado, o
  PATH novo só vale em sessão nova: avise que no fim do setup será preciso fechar e
  reabrir o Claude Code, e use o caminho completo do executável (descubra com
  `where python` / `ls "$LOCALAPPDATA/Programs/Python"`) até lá.
- **Git ausente** (improvável: no Windows o app desktop só abre sessão local com o Git instalado, e o toolkit veio via `git clone`. Pode ocorrer no macOS/CLI):
  ```bash
  winget install --id Git.Git -e --accept-source-agreements --accept-package-agreements
  ```
  Avise que, com o Git instalado, o Claude Code passa a usar o Git Bash como
  terminal a partir da próxima reinicialização do aplicativo.
- **winget indisponível ou rede bloqueando** → plano B manual: Python em
  https://www.python.org/downloads/ (marcando **"Add Python to PATH"**) e Git em
  https://git-scm.com. Depois, fechar e reabrir o Claude Code e rodar `/aft-setup`
  de novo.

> Nas demais skills os comandos usam `python`. No Windows isso já funciona; no macOS,
> se só existir `python3`, use `python3`.

## Passo 2 — Criar a estrutura de pastas

```bash
mkdir -p ~/Documents/AFT/"OS ATIVAS" ~/Documents/AFT/"OS ARQUIVADAS"
```

Explique ao AFT:

> Sua pasta de trabalho é `Documentos\AFT`. Cada empresa fiscalizada ganha uma
> subpasta dentro de `OS ATIVAS` (padrão: `NOME DA EMPRESA <CNPJ 14 dígitos>`), onde
> ficam todos os arquivos daquela fiscalização: relato de campo, autos, anexos e a
> ficha `memory.md`. Quando a fiscalização termina, a pasta inteira vai para
> `OS ARQUIVADAS`. Tudo fica **no seu computador** — nada é enviado para fora.

## Passo 3 — Coletar os dados do auditor (uma única vez)

Pergunte, em uma única mensagem, apenas **três coisas** (o resto você descobre na
tabela de UORGs). Explique que esses dados entram automaticamente nos arquivos TXT
importados pelo Sistema Auditor, para nunca mais serem digitados:

| Campo | Exemplo |
|---|---|
| Nome completo | JOÃO DA SILVA |
| CIF (6 dígitos) | 123456 |
| Lotação (cidade ou nome da unidade) | "Anápolis" · "SRT Goiás" · "Gerência de Uberlândia" |

### Resolver a UORG pela tabela (o AFT não precisa saber o código)

O toolkit traz a tabela oficial de UORGs em
`~/.claude/skills/config/uorgs.csv` (UTF-8, separado por `;`, colunas:
`CDUORG;NOME;UF;MUNICIPIO;ENDERECO;BAIRRO;CEP`; ~1.000 unidades; CDUORG tem
sempre 9 dígitos).

1. **Busque** a lotação informada nas colunas `MUNICIPIO` e `NOME`,
   case-insensitive. Tente com e sem acentos (ex.: `ANÁPOLIS` e `ANAPOLIS`) —
   o arquivo está acentuado. Se a cidade for comum a vários estados ou vier
   ambígua, pergunte a UF antes.
2. **Apresente os candidatos numerados** (código + nome + município/UF) e peça
   para o AFT escolher. É normal haver mais de uma unidade na mesma cidade
   (Superintendência, Gerência, Agência) — quem sabe qual é a sua lotação é o AFT.
   > Dica de qualidade: a tabela tem entradas antigas/desativadas (endereço `.`,
   > CEP `99999999`, ou `*** A DESATIVAR` no nome). Liste-as por completude, mas
   > destaque as entradas com endereço real como prováveis.
3. **Preencha automaticamente** a partir da linha escolhida:
   - `uorg` = `CDUORG` (9 dígitos)
   - `local_uorg` = `BAIRRO` (se vazio ou lixo tipo `.`, pergunte ao AFT)
   - `cep_uorg` = `CEP` (se `99999999`, pergunte ao AFT)
   - `municipio` = `MUNICIPIO` · `uf` = `UF`
4. **Eco de confirmação** antes de gravar: mostre código, nome da unidade,
   bairro/local, CEP, município/UF e pergunte se confere.
5. **Fallback**: se a lotação não aparecer na tabela (unidade nova/renomeada),
   peça o código de 9 dígitos diretamente ao AFT — ou aceite deixar em branco
   por enquanto (o Sistema Auditor permite confirmar pela lupa), recomendando
   preencher depois editando o `aft-config.md`.

## Passo 4 — Descobrir o caminho Windows da pasta de trabalho

O Sistema Auditor exige caminhos absolutos no formato Windows (`C:\...`) nas linhas
de anexo do TXT. Descubra o caminho real:

```bash
cygpath -w "$HOME" 2>/dev/null || echo "$HOME"
```

- No Windows (Git Bash), isso retorna algo como `C:\Users\joao`. O prefixo da pasta
  de trabalho fica `C:\Users\joao\Documents\AFT`.
- Pergunte: **"O Sistema Auditor roda neste mesmo computador?"**
  - **Sim** (caso normal no Windows) → use o prefixo calculado acima.
  - **Não** (ex.: roda numa máquina virtual que enxerga este disco por outra letra,
    como `Y:`) → pergunte qual letra/prefixo a VM usa para chegar em
    `Documents\AFT` e use esse valor.

## Passo 5 — Gravar o aft-config.md

Crie `~/Documents/AFT/aft-config.md` no formato abaixo: um título, uma linha de
comentário e um **front-matter YAML entre `---`** com os valores coletados:

````markdown
# Configuração do AFT Toolkit
> Gerado por /aft-setup em [DATA]. Pode editar à mão; rode /aft-setup para refazer.

---
nome_auditor: "JOÃO DA SILVA"
cif: "123456"
uorg: "015000000"          # cod_4 do TXT
local_uorg: "SETOR SUL"    # cod_6 do TXT
cep_uorg: "74080010"       # cod_7 do TXT
municipio: "Goiânia"
uf: "GO"
# Prefixo Windows da pasta de trabalho (para os anexos do Sistema Auditor):
path_windows: "C:\\Users\\joao\\Documents\\AFT"
# Dados fixos do TXT (não alterar sem orientação):
cod_1: "8211300"           # CNAE placeholder — o Sistema Auditor corrige pela lupa
cod_2: "1008"              # tipo de ação fiscal
---
````

Se o arquivo já existir, mostre os valores atuais e pergunte o que mudar — edite só o
que o AFT pedir.

## Passo 5b — Instalar o perfil do auditor (CLAUDE.md global)

O toolkit traz um perfil pronto que diz ao Claude, em toda conversa, quem é o usuário
(um AFT, não um programador), como tratar dados sensíveis e quais skills usar. Ele vai
em `~/.claude/CLAUDE.md`:

- **Se `~/.claude/CLAUDE.md` NÃO existe** → copie o template:
  ```bash
  cp ~/.claude/skills/config/CLAUDE-aft.md ~/.claude/CLAUDE.md
  ```
  Explique em uma frase: *"Instalei o seu perfil de auditor — a partir da próxima
  conversa, o Claude já sabe que você é AFT, conhece as skills do toolkit e segue as
  regras de privacidade de dados."*
- **Se JÁ existe** → mostre um resumo do conteúdo atual e pergunte: *"Você já tem um
  CLAUDE.md. Quer (a) substituí-lo pelo perfil do AFT Toolkit, (b) acrescentar o perfil
  ao final do existente, ou (c) deixar como está?"* Execute a escolha. Na opção (b),
  acrescente o conteúdo do template após o existente, separado por `---`.

> Quando o toolkit for atualizado (`git pull`), o template novo fica em
> `config/CLAUDE-aft.md` — o `~/.claude/CLAUDE.md` instalado não muda sozinho. Se o AFT
> quiser a versão nova, basta rodar `/aft-setup` de novo.

## Passo 6 — Instalar as bibliotecas Python

```bash
pip install pillow pikepdf pypdf || pip3 install pillow pikepdf pypdf
```

Explique: `pillow` converte fotos de evidência em PDF para anexar aos autos;
`pikepdf` inspeciona assinaturas de PDF e comprime anexos grandes; `pypdf` lê o
texto dos autos lavrados no Sistema Auditor (skill `/autos-lavrados`).

## Passo 7 — NotebookLM (recomendado, pode pular)

As skills de lavratura consultam ementários no Google NotebookLM para achar o código
da ementa automaticamente. Para habilitar:

1. **Pedir acesso aos notebooks**: entrar em https://notebooks-aft.vercel.app com a
   conta Google (Gmail) e solicitar acesso. O mantenedor (Ricardo, SRTE/GO) libera os
   notebooks de ementas e NRs.
2. **Instalar o CLI**:
   ```bash
   pip install notebooklm-py || pip3 install notebooklm-py
   ```
3. **Autenticar** (abre o navegador para login Google):
   ```bash
   notebooklm login
   ```
4. **Testar**:
   ```bash
   notebooklm list
   ```
   Se aparecer a lista de notebooks compartilhados, está pronto.

Se o AFT pular este passo, as skills continuam funcionando: elas oferecem o ementário
no Google Drive (link nas próprias skills) ou pedem o código da ementa diretamente.

## Passo 8 — Resumo final

Apresente:

```
✅ AFT Toolkit configurado!

📁 Pasta de trabalho: ~/Documents/AFT/  (OS ATIVAS · OS ARQUIVADAS)
📄 Configuração:      ~/Documents/AFT/aft-config.md
👤 Perfil do auditor: ~/.claude/CLAUDE.md [instalado / mantido o existente]
🐍 Python:            [versão] · pillow/pikepdf instalados
📚 NotebookLM:        [autenticado / pulado — rode /aft-setup depois para ativar]

Fluxo típico de uma fiscalização:
  1. /nova-os           → cadastra a empresa e o prazo do DET
  2. /painel            → vê todas as OS e os prazos vencendo
  3. /inspecao-fisica   → registra o relato da visita
  4. /inspecao-inicial  → enquadra NR/ementa e redige os autos
  5. /gera-ai           → gera o TXT para importar no Sistema Auditor
  6. /autos-lavrados    → confere o que foi transmitido
Outras: /registro · /PGR-analise · /aft-rt-rgi · /det-630 · /jornada-analise · /sfitweb-rel
```

---

## Regras

- Nunca grave CIF/UORG de exemplo no config — só valores realmente informados pelo AFT.
- Não peça nem armazene senhas. O login do NotebookLM é feito pelo navegador do próprio AFT.
- Se algum comando falhar, mostre o erro em linguagem simples e o que fazer — não
  abandone o auditor no meio do setup.
