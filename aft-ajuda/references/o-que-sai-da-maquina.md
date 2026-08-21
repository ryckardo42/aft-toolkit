> Referência da skill /aft-ajuda — leia sob demanda.

A resposta honesta a "meus dados vão para a internet?": depende de qual dos três regimes de processamento a habilidade usa. Este arquivo explica os três, diz como reconhecer cada um e quando o AFT precisa decidir antes de rodar.

## Por que a resposta não é um "não" seco

O toolkit é local: as pastas, as fichas, os documentos e os autos ficam no
computador do AFT, e não há servidor nem nuvem no meio. Mas **"o toolkit é
local" não significa que todo processamento seja local**, e responder que sim
seria mentira — com consequência real para quem trabalha com atestado médico e
lista nominal.

São três regimes. Saber em qual você está é o que permite decidir.

## Regime 1 — Script local: nada sai

Um pequeno programa (script) roda no próprio computador, lê o arquivo e devolve
o resultado. **O conteúdo do documento nunca entra na conversa** e nunca chega
a modelo nenhum.

Isto não é um detalhe de implementação: **é o caminho desenhado justamente para
o dado pessoal.** Onde há nome, CPF, PIS, salário ou jornada de trabalhador, o
toolkit resolve por script de propósito — e é por isso que o número que aparece
na sua tela veio de um cálculo, e não de uma leitura do modelo. Quando houver
escolha entre uma habilidade que calcula por script e uma que lê o documento,
**para dado de pessoa física a de script é a preferível**.

É assim que o toolkit faz o trabalho pesado e o trabalho com dado pessoal:

- a leitura da Relação de Vínculos Ativos (o PDF inteiro, com a lista nominal);
- a validação do ponto eletrônico (AFD/AEJ);
- os dimensionamentos — grau de risco pelo CNAE, SESMT, CIPA, instalações da
  NR-24;
- a varredura das planilhas de CAT;
- a leitura dos PDFs dos autos já transmitidos no Sistema Auditor;
- a troca dos códigos pelos dados reais na hora de gerar o TXT (`rehydrate.py`)
  — de propósito: um nome ou CPF trocado num documento legal é inaceitável, e
  por isso essa etapa **nunca** é feita pelo modelo;
- compressão de PDF e conversão de foto.

**Como reconhecer:** a habilidade diz que roda um script, ou o assistente pede
permissão para executar um comando `python`. Se o número apareceu de um
cálculo, foi script.

## Regime 2 — O assistente lê o documento: o conteúdo vai para o modelo

Quando a habilidade precisa **compreender** o documento — julgar um PGR, ler
um laudo, entender um atestado escaneado —, não há script que resolva: o
assistente abre o arquivo, e aí o conteúdo dele passa pelo modelo de IA.

É legítimo e é o que dá valor à ferramenta. Mas é o regime em que **o documento
sai da máquina**, e o AFT precisa saber disso antes, não depois.

Vale para qualquer habilidade que analise documento entregue pela empresa.

**Como reconhecer:** a habilidade lê e opina sobre o conteúdo, cita páginas,
interpreta o que está escrito. Nenhum script faz isso.

### O que é dado protegido, e o que não é

Aqui o critério é **jurídico**, e é o que evita tanto o descuido quanto a
paranoia inútil. A LGPD (Lei nº 13.709/2018) protege **dados de pessoa
natural** — art. 1º, e a definição de dado pessoal do art. 5º, I. Ela **não
protege pessoa jurídica**.

Consequência prática, que separa as habilidades em dois grupos:

| Documento | Contém dado pessoal? |
|---|---|
| PGR, Inventário de Riscos, Plano de Ação | **Não.** É documento técnico da empresa sobre a própria gestão de riscos |
| AET (Análise Ergonômica do Trabalho) | **Não**, como regra: descreve posto de trabalho e organização, não pessoas |
| Laudo de adequação à NR-12, apreciação de risco de máquina | **Não.** Trata de máquina |
| ASO, atestado médico, laudo com CID, encaminhamento | **Sim — dado sensível de saúde** (art. 5º, II) |
| CAT e o que a acompanha | **Sim.** Acidente é sempre de uma pessoa |
| Lista nominal, ficha de registro, folha de ponto, holerite, CTPS | **Sim** — nome, CPF, PIS, endereço, salário |

Por isso **auditar um PGR, uma AET ou um laudo de máquina não levanta questão
de dado pessoal**: não há pessoa natural identificada ali. Dizer ao AFT que
precisa "ter cuidado" para analisar o PGR da empresa é errado e só atrapalha o
trabalho dele.

### A decisão que é do AFT

O cuidado é com **o conteúdo, não com o tipo do documento** — e o tipo é só um
bom palpite inicial. Um PGR pode trazer anexa a lista nominal dos exames; um
pacote de resposta ao DET costuma misturar tudo, do programa técnico ao
atestado.

Por isso, ao rodar uma habilidade deste regime sobre um **lote** de documentos
(tipicamente a resposta da empresa a uma notificação), o que vale é **olhar o
que tem ali antes**. Havendo documento de pessoa física no meio, os caminhos
são: separar os arquivos e rodar só sobre os da empresa; pedir a
pseudonimização antes; ou analisar à mão. **Quem decide é o AFT** — a
habilidade não tem como saber, pelo nome do arquivo, que aquele PDF é um
atestado.

Se o AFT perguntar e você não souber em que regime a habilidade está, **leia o
`SKILL.md` dela antes de responder**. Não deduza.

## Regime 3 — Consulta externa deliberada: só o fato, nunca a pessoa

A consulta de ementa ao NotebookLM. Sai **apenas a descrição da
irregularidade** ("máquina sem proteção fixa na zona de prensagem"). Nunca nome
de trabalhador, CPF, razão social ou CNPJ — e se o relato do AFT trouxer, a
pseudonimização entra antes (`[[TRAB_NN]]`, `[[CPF_NN]]`).

Detalhes em `notebooklm-e-ementas.md`.

## Triagem não é auditoria

Assunto vizinho, e fonte de erro caro. Algumas habilidades fazem **varredura
rápida** de um lote de documentos, para dizer o que parece atendido e o que
parece faltar. Elas costumam **amostrar** — ler alguns arquivos da pasta, não
todos — e marcar o resto como "precisa auditoria do AFT".

Isso é ponto de partida, **não conclusão**:

- o que ela chamou de atendido pode não estar;
- o que ela não leu não foi avaliado, e o relatório diz isso;
- nada dali vira auto sem o AFT ter olhado o documento.

Ao explicar uma habilidade dessas, **diga que é triagem** na mesma frase em que
diz o que ela faz. Um AFT que a tome por auditoria completa deixa de lavrar
auto que era devido — e o erro só aparece muito depois.

## A regra que não muda em nenhum regime

**Nada de fiscalização em serviço online de terceiro.** Compressor de PDF de
site, conversor de foto, validador online: nunca. Isso é diferente dos três
regimes acima, que são o funcionamento do toolkit; aqui o documento iria parar
num serviço qualquer, sem contrato e sem controle.

Uma única exceção documentada, e ela é opt-in, com consentimento pedido a cada
sessão: o `/aft-painel` pode publicar o painel como página privada na conta do
AFT — e mesmo assim só com empresas e prazos, **sem dado de trabalhador**.

O mapa `.depara_<CNPJ>.json`, que liga os códigos aos dados reais, é sensível:
não se exibe, não se compartilha, não sobe para lugar nenhum.
