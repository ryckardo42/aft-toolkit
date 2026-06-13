# AFT Toolkit

**Skills de IA para Auditores-Fiscais do Trabalho**, para uso no **Claude Code** (app desktop, Windows).

O toolkit transforma o Claude Code num assistente de fiscalização que trabalha **no seu computador**: organiza as pastas das OS, registra o relato de campo, enquadra NR/ementa, redige autos de infração, gera o TXT importável pelo Sistema Auditor e produz relatórios — tudo com uma política de **anonimização de dados pessoais** embutida.

## Por que Claude Code (e não o chat comum)?

- **Execução local**: os arquivos das suas fiscalizações ficam no seu computador (`Documentos\AFT`). As skills criam pastas, salvam autos, convertem fotos e geram o TXT diretamente no disco.
- **Anonimização (pseudonimização reversível)**: nomes e CPFs de trabalhadores são substituídos por tokens (`[[TRAB_01]]`, `[[CPF_01]]`) nos textos processados pela IA. Os valores reais ficam num mapa local e são re-injetados no TXT final por um **script determinístico** (`rehydrate.py`) — nunca pelo modelo. Um nome ou CPF trocado num documento legal é inaceitável; por isso essa etapa não é feita por IA.
- **Fluxo completo**: do relato ditado pós-inspeção até o arquivo pronto para o botão "imp. txt" do Sistema Auditor.

## Instalação (resumo)

Veja o passo a passo completo em [COMO-INSTALAR.md](COMO-INSTALAR.md) (ou na apostila `Apostila-AFT-Toolkit.docx`). São 4 passos — só os dois primeiros são manuais:

1. **Instale o aplicativo Claude** (claude.com/claude-code).
2. **Instale o Git** (git-scm.com — o app desktop exige o Git para abrir sessões locais no Windows) e reinicie o app pela bandeja.
3. **Cole o prompt de instalação** (está no COMO-INSTALAR.md) numa conversa do `</> Code`: o próprio Claude instala o Python via winget e clona este repositório em `~/.claude/skills`, pedindo sua permissão a cada comando.
4. **Reinicie o app e rode `/aft-setup`** — ele cria as pastas de trabalho, coleta seus dados uma única vez (nome, CIF e a sua lotação — basta dizer a cidade, ex.: "Anápolis", e o toolkit descobre o código de 9 dígitos da UORG) e instala as dependências.

**Atualização:** peça ao Claude *"Atualize o AFT Toolkit"* (ele roda `git pull` na pasta das skills).

## Skills incluídas

### Configuração
| Skill | O que faz |
|---|---|
| `/aft-setup` | Configuração inicial: pastas de trabalho, dados do auditor (CIF/UORG), perfil do auditor (`CLAUDE.md` global), dependências, NotebookLM |

### Inspeção e lavratura
| Skill | O que faz |
|---|---|
| `/inspecao-fisica` | Transforma a narrativa ditada da visita num relato de campo estruturado (`inspecao-fisica.md`) — fiel, sem enquadramento |
| `/inspecao-inicial` | Lê o relato de campo, identifica NR/ementa (NotebookLM) e redige os autos de infração (todas as NRs + CLT), com gate de dupla visita |
| `/registro` | Autos de falta de registro (art. 41 CLT) + falta de anotação na CTPS (art. 29 CLT) |
| `/PGR-analise` | Auditoria sistemática do PGR (NR-01) nas 7 ementas, com confronto campo × documento e citação de páginas |
| `/det-630` | Auto por omissão de documentos notificados via DET (ementa 001168-1, art. 630 §4º CLT) |
| `/aft-rt-rgi` | Relatório Técnico de Interdição/Embargo em .docx + autos derivados das ementas |

### Jornada / ponto eletrônico (Portaria 671/2021)
| Skill | O que faz |
|---|---|
| `/jornada-analise` | Orquestrador: tria o pacote entregue (AFD/AEJ/atestados) e consolida os pareceres |
| `/jornada-valida-afd-aej` | Validador determinístico (Python) do AEJ: estrutura, trailer, integridade referencial |
| `/jornada-atestado` | Auditoria do Atestado Técnico/Termo de Responsabilidade do REP/PTRP (art. 89), com inspeção de assinatura por código |
| `/jornada-auto-afd-aej` | Autos por AFD/AEJ ausente ou fora do padrão (ementas 002279-9 / 002280-2) |

### Empacotamento, rastreamento e relatórios
| Skill | O que faz |
|---|---|
| `/gera-ai` | Empacota autos redigidos no TXT importável pelo Sistema Auditor (latin-1), com anexos em PDF e pseudonimização reversível |
| `/autos-lavrados` | Lê os PDFs já transmitidos no Sistema Auditor (`C:\SistemasAFT\...\PRO`), cruza com os rascunhos e marca no `memory.md` o que está lavrado `[x]` / pendente `[ ]` — read-only sobre o Sistema Auditor |
| `/sfitweb-rel` | Relatório Final Simplificado consolidando autos, termos e notificações |

## Fluxo típico de uma fiscalização

```
1. Visita ao estabelecimento
2. /inspecao-fisica      → narra o que viu; vira relato estruturado na pasta da OS
3. /inspecao-inicial     → enquadra NR/ementa e redige os autos
   (desvios automáticos: /registro p/ trabalhador sem registro ·
    /aft-rt-rgi p/ risco grave e iminente · /PGR-analise p/ auditoria do PGR)
4. /gera-ai              → TXT importável + anexos na pasta Autos DD-MM/
5. Sistema Auditor       → botão "imp. txt" → revisão → transmissão
6. /autos-lavrados       → confere o que foi transmitido e marca no memory.md
7. /sfitweb-rel          → relatório final consolidado
```

## Estrutura de trabalho

```
Documentos\AFT\
├── aft-config.md            (seus dados — criado pelo /aft-setup)
├── OS ATIVAS\
│   └── EMPRESA X 12345678000190\
│       ├── memory.md                (ficha da fiscalização)
│       ├── inspecao-fisica.md       (relato de campo)
│       ├── autos.md                 (autos redigidos)
│       └── Autos 19-05\             (TXT importável + anexos PDF)
└── OS ARQUIVADAS\
```

## Segurança dos dados

- Tudo roda e fica **no seu computador**. Nenhuma skill envia arquivos para serviços externos (a compressão de PDF, conversão de fotos e validação de arquivos são scripts Python locais).
- **Nunca** use compressores/conversores online para documentos de fiscalização.
- O arquivo `.depara_<CNPJ>.json` (mapa token↔dados reais) é sensível: não compartilhe, não commite.
- A cópia `*.tokenized.txt` é a única versão segura para compartilhar com colegas.
- Consultas de ementa ao NotebookLM enviam apenas a **descrição da irregularidade** — nunca nomes de trabalhadores ou da empresa.

## Ementários (códigos de ementa)

As skills buscam o código da ementa em 3 camadas:

1. **NotebookLM** (recomendado): peça acesso em https://notebooks-aft.vercel.app e configure o CLI pelo `/aft-setup`. Os notebooks cobrem os ementários SST e de legislação + NRs específicas.
2. **Google Drive compartilhado**: [ementários por NR em Markdown](https://drive.google.com/drive/folders/1bktX9TkDIoix4iQuca3Yr5aWCfv97GSg?usp=sharing).
3. **Você informa o código** (formato `XXXXXX-X`).

## Estrutura do repositório

> O repositório é clonado como a **própria pasta de skills** (`~/.claude/skills`) — o Claude Code só descobre skills no primeiro nível dessa pasta, então cada skill precisa ficar diretamente nela (ex.: `~/.claude/skills/gera-ai/SKILL.md`).

```
~/.claude/skills/   (= este repositório)
├── README.md · COMO-INSTALAR.md · Apostila-AFT-Toolkit.docx
├── config/notebooks.json    (IDs dos notebooks do NotebookLM)
├── config/uorgs.csv         (tabela oficial de UORGs — o /aft-setup resolve o código pela cidade)
├── config/CLAUDE-aft.md     (perfil do auditor — o /aft-setup instala em ~/.claude/CLAUDE.md)
├── _scripts/                (scripts compartilhados: rehydrate, fotos, compressão, docx)
├── aft-setup/ · gera-ai/ · inspecao-fisica/ · inspecao-inicial/
├── registro/ · det-630/ · sfitweb-rel/ · PGR-analise/ · aft-rt-rgi/ · autos-lavrados/
└── jornada-analise/ · jornada-valida-afd-aej/ · jornada-atestado/ · jornada-auto-afd-aej/
```

## Avisos

- As skills são **apoio à redação e organização**. O conteúdo jurídico de cada auto, termo e relatório é de responsabilidade do AFT, que revisa tudo antes de transmitir.
- Nunca aceite código de ementa, item de NR ou capitulação sem conferir no ementário oficial.
- O template do RT (`aft-rt-rgi/template.docx`) segue o modelo da SRTE/GO — auditores de outras SRTEs devem ajustar o cabeçalho.

## Contribuindo

Sugestões de novas skills ou melhorias: abra uma Issue ou fale com o mantenedor (Ricardo de Oliveira, AFT — SRTE/GO).
