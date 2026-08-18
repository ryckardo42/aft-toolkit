## 06/08/2026
<!-- commit: preparacao-perfil-empresa-cipa -->

**A preparação da ação fiscal agora chega sabendo o que a empresa faz — e qual CIPA
ela deve ter.** O `preparacao.docx` que você imprime e leva na visita ganhou duas
seções novas, e perdeu o que não servia para nada em campo.

- **Seção 1 — A empresa.** Com o CNPJ (ou o PDF da OS), a skill faz uma busca rápida
  na internet e resume o que a empresa produz, onde opera, o porte e notícias que
  interessam à fiscalização (acidente noticiado, autuação, ação do MPT). Cada
  parágrafo vem com a fonte. É indício para orientar o olhar, nunca prova — o que
  vale continua sendo o constatado no local. Só vão para o buscador razão social,
  CNPJ e município: teor de denúncia e nome de pessoa **nunca** saem da sua máquina.
- **Seção 2 — Grau de risco e CIPA devida.** O nº de trabalhadores virou pergunta
  obrigatória da preparação (se você anexar a lista de empregados, ele sai da lista).
  Com ele e o CNAE, a skill roda a `/aft-cnae-grau-risco-nr04` e a
  `/aft-cipa-nr05-dimensionamento` e põe no documento a CIPA que aquele
  estabelecimento deve ter — Quadro I por representação e o total paritário, para
  você comparar com a ata de eleição ainda na visita. Se você não souber o efetivo,
  a preparação segue sem a seção e deixa a pendência anotada; nada trava.
- **Saiu o que não ajudava.** Sem "Equipe AFT", sem "prazo da fiscalização" e sem a
  linha de assinatura no fim — o documento é seu roteiro de trabalho, não uma peça
  para assinar. Em "Ordem de Serviço" ficou só o número.
- **O vencimento não se perdeu.** O prazo limite para término da fiscalização agora é
  gravado no `memory.md` como `**Vencimento da OS:**`, junto com o número da OS.

Os números da CIPA no documento são calculados pelos scripts na hora de gerar o
arquivo, a partir do `memory.md` — não são digitados pelo Claude. Se algum sair
diferente do que você viu na conversa, é sinal de CNAE ou efetivo desatualizado no
`memory.md`.

---
