> Referência da skill /aft-ajuda — leia sob demanda.

O roteiro de estreia: conduzir um AFT que acabou de instalar (ou que instalou e travou) até a primeira auditoria cadastrada e o painel aberto na tela dele.

## Para que serve este tour

Não é para ensinar o toolkit. É para atravessar o ponto em que as pessoas
desistem — aquele em que a ferramenta ainda é abstrata, nada na tela parece
seu, e voltar ao método antigo é mais confortável.

O tour acaba quando o AFT vê **uma fiscalização dele** dentro do painel. A
partir dali ele tem onde se apoiar, e o resto ele pergunta.

## As regras da condução

1. **Um passo por vez.** Nunca liste os seis passos de uma vez: isso reproduz
   exatamente a sensação de excesso que travou a pessoa.
2. **Nada acontece sem o "pode ir".** Antes de cada passo, diga em uma frase o
   que vai fazer e o que vai mudar. Espere.
3. **Mostre o resultado antes de seguir.** Depois de cada passo, o que apareceu
   na tela e o que aquilo significa, em linguagem de leigo.
4. **Ele pode parar em qualquer ponto.** Diga isso no começo e cumpra. Nada
   fica pela metade de um jeito que atrapalhe depois.
5. **Você executa tudo.** Ele não digita comando, não abre terminal, não edita
   arquivo. No máximo clica em "Permitir", ou faz um login numa janela que você
   abriu.
6. **Sem "é só" e sem "basta".** Ver o Passo 3 da SKILL.md.

Abertura sugerida, em uma frase: *"Vamos até você ver uma fiscalização sua
dentro do painel. São uns quinze minutos, eu faço tudo, e você pode parar
quando quiser."*

## Passo 1 — A instalação está de pé?

Rode a `/aft-doctor` e traduza o resultado. É diagnóstico puro: não altera
nada, e é justamente o que dá a primeira dose de segurança — ele passa a saber
que está tudo no lugar em vez de supor.

- **Tudo verde** → siga, dizendo isso com todas as letras.
- **Amarelo ou vermelho** → resolva você, antes de continuar. Não comece o tour
  em cima de instalação quebrada, e não peça a ele que conserte nada.
- **Nem pasta AFT nem `aft-config.md`** → ele ainda não rodou o `/aft-setup`.
  Ofereça rodá-lo agora; o tour continua depois.

## Passo 2 — Onde as coisas moram

Descubra a pasta real (`_scripts/pasta_aft.py --os-ativas`) e **abra-a para ele
ver** — `explorer` no Windows, `open` no macOS. Ver a pasta no Explorer vale
mais que qualquer explicação.

Diga as três coisas que importam, e só elas:

- é uma pasta comum do computador dele, que ele pode abrir quando quiser;
- **uma subpasta por empresa fiscalizada**, dentro de `OS ATIVAS`;
- tudo o que for produzido cai ali, e **nada disso sai do computador**.

## Passo 3 — A primeira auditoria

Aqui o tour deixa de ser demonstração e passa a ser trabalho dele. Pergunte
qual é o caso, com uma pergunta só:

> Tem alguma fiscalização em andamento agora, ou alguma que você vai começar?

| Resposta | Caminho |
|---|---|
| Tem uma em andamento, com pasta de documentos no computador | Peça para copiar a pasta para dentro de `OS ATIVAS` e rode a `/aft-organiza-os` — ela classifica os documentos e monta a ficha. Copiar a pasta é a única coisa que ele faz com as próprias mãos, e é arrastar, não digitar. |
| Vai começar uma, ou tem só a Ordem de Serviço / a Demanda do SFIT | `/aft-nova-auditoria`. Se ele tiver o PDF do SFIT-WEB, peça para anexar: os dados entram sozinhos. O CNPJ é opcional agora. |
| Nenhuma no momento | Não invente empresa de teste — cadastrar uma OS falsa suja a pasta de trabalho. Vá direto para o Passo 4 com o painel vazio e explique que ele volta aqui quando tiver a primeira. |

Ao terminar, **mostre a ficha** (`memory.md`) e explique em três linhas o que
ela é: a capa da OS, que o assistente lê antes de trabalhar e onde grava o que
apura, e que é por isso que ele nunca vai precisar recontar a história da
fiscalização.

## Passo 4 — O painel

Rode a `/aft-painel`. É o momento em que a ferramenta vira concreta: a
fiscalização dele, num card, com o prazo colorido.

Aponte três coisas:

- **é local** — abre no navegador, mas não há internet nem servidor na nuvem;
- **o card abre** e mostra o detalhe da OS;
- **os prazos do DET podem entrar sozinhos**, pela extensão do navegador — sem
  digitar prazo nunca mais.

Se ele demonstrar interesse na extensão, ofereça instalá-la agora
(`references/painel-det-extensao.md`). Se não, deixe para depois: o tour não
depende dela.

## Passo 5 — Uma tarefa de verdade

Um passo pequeno, com valor imediato, escolhido pelo momento dele:

| Situação | O que oferecer |
|---|---|
| Já foi a campo | *"Me conte o que você viu, do seu jeito"* → `/aft-inspecao-fisica`. É a porta de entrada mais natural do toolkit, e a que costuma convencer. |
| Ainda vai a campo | `/aft-preparacao-acao-fiscal` — o dossiê para levar na visita. |
| Recebeu documento da empresa | `/aft-PGR-analise` ou a análise que couber. |
| Só quer tirar uma dúvida técnica | `/aft-consulta` — ementa e fundamentação. |

Escolha **uma** e conduza até o resultado aparecer.

## Passo 6 — Fechar

Feche com o que ele **já sabe fazer**, não com o que falta aprender. Três ou
quatro linhas, nomeando o que aconteceu na sessão: a auditoria está cadastrada,
a ficha existe, o painel mostra o prazo, e o primeiro documento saiu.

E deixe as duas portas abertas, nesta ordem:

- para qualquer dúvida da ferramenta, **`/aft-ajuda`** — ou simplesmente
  perguntar em português, a qualquer momento;
- se algo der errado, **não é culpa dele**: `/aft-erro` registra o defeito para
  o mantenedor.

Uma última frase que vale dizer, porque é verdade e é o que destrava quem está
inseguro: **não é preciso decorar nome de habilidade nenhuma.** Basta pedir o
que se quer, em português.
