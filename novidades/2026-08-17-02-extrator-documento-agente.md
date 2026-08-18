## 17/08/2026

<!-- commit: extrator-documento-agente -->

**Analisar PGR, AET e laudo de NR-12 não engole mais o seu limite de uso.** Até agora,
essas três análises carregavam o PDF inteiro na conversa — e o pior: **recarregavam o
documento a cada pergunta sua**. Num PGR real de 163 páginas era como reenviar um
calhamaço a cada frase; por isso o limite estourava no meio do trabalho, justamente na
hora de redigir os autos.

Agora a leitura é feita **fora da conversa**, por um assistente auxiliar que lê o
documento inteiro e devolve um **extrato fiel**, com o trecho transcrito palavra por
palavra e o número da página de cada um. A análise corre sobre esse extrato, que fica
gravado na pasta da OS (`pgr-extrato.md`, `aet-extrato.md` ou `laudo-extrato.md`) e você
pode abrir quando quiser. Vale para `/aft-PGR-analise`, `/aft-aet-auditoria` e
`/aft-auditoria-AR-NR12`, cada uma com o seu roteiro: as 7 ementas do PGR, as 5 da AET,
os 6 blocos do checklist de NR-12.

**Nada de qualidade se perde nisso**, e essa foi a preocupação central:

- O extrato **transcreve, não resume**: cada trecho que sustenta ou afasta um item vai
  literal, entre aspas, com a página — é o que a citação obrigatória do auto exige.
- O extrato **declara o que faltou**. Boa parte dos itens se prova pelo que o documento
  *não* tem, e um resumo comum só contaria o que existe.
- O extrato **não julga**. Ele diz onde o assunto aparece; quem decide se está regular
  continua sendo você.
- Quando um ponto fica limítrofe, a análise **volta ao PDF original** naquelas páginas.

**O documento passa por uma triagem antes, e ela avisa quatro coisas diferentes.** Cada
uma pede uma conduta:

| Aviso | O que significa |
|---|---|
| página **sem texto** | escaneada; será lida como imagem |
| **texto suspeito** | tem texto, mas é lixo de um OCR ruim anterior — o texto é ignorado |
| **ordem embaralhada** | tabela que saiu virada na extração; não se cita sem conferir |
| **conteúdo em imagem** | o texto está bom, mas parte do conteúdo só existe na figura |

O último é o que mais importa na prática: foto de máquina, plaqueta de componente e
tabela colada como figura não aparecem no texto. Num laudo de NR-12 real, 10 das 25
páginas caíram nesse caso — e o assistente é instruído a **não concluir "não localizado"
numa página dessas sem abri-la**.

**Documento escaneado sem OCR é avisado e tratado.** Numa AET real de 33 páginas sem
nenhum texto pesquisável, o aviso aparece em destaque, a leitura é delegada mesmo sendo
documento curto (página sem texto pesa muito mais do que o número de páginas sugere), e o
extrato diz com todas as letras que tudo veio de leitura visual, com a avaliação da
qualidade do escaneamento — se está nítido, torto ou com página faltando. É o que permite
a você decidir se exige o documento de novo.

Uma recomendação prática: **prefira deixar o documento na pasta da OS** a arrastá-lo para
o chat. PDF arrastado para a conversa já entra inteiro no contexto e anula a economia.
<!-- commit: cat-trabalhador-skill -->

**Nova habilidade: o dossiê de CATs de um trabalhador (`/aft-cat-trabalhador`).** Até
agora dava para levantar os acidentes de uma **empresa** (pelo CNPJ). Mas às vezes a
fiscalização gira em torno de uma **pessoa**: um acidente grave, uma denúncia, um óbito
— e você precisa de todos os dados da comunicação de acidente daquele trabalhador.
Agora basta pedir "puxa as CATs do trabalhador" com o **CPF ou o nome**: o assistente
varre as mesmas planilhas estaduais de CAT que você já tem e entrega um **PDF pronto**,
no leiaute do formulário CAT do eSocial — uma ficha completa por CAT, em ordem
cronológica (empregador, acidente, lesão, CID, atestado médico, médico que atendeu).

Se a busca por nome encontrar mais de uma pessoa, o assistente mostra a lista (nome,
nascimento, empregadores) e pergunta qual é — nunca escolhe sozinho. E a privacidade
continua a de sempre: tudo processado no seu computador, nada vai para a internet, e o
CPF aparece na conversa sempre mascarado (completo, só dentro do PDF gravado na pasta).
