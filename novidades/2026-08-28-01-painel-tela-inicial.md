## 28/08/2026
<!-- commit: painel-tela-inicial -->

**A tela inicial do painel ficou mais útil: filtros, busca e o próximo passo em cada
card.** Cinco mudanças que se sentem logo ao abrir o painel, mais três consertos de
bastidor:

- **Os contadores do topo agora filtram a grade.** Clique em "vencendo em ≤ 7 dias" (ou
  "DETs vencidos", ou "notif. sem registro") e os cards fora do critério ficam
  esmaecidos — não somem, a grade continua inteira à vista. Clique de novo (ou em
  "OS ativas") para limpar.
- **Campo de busca acima da grade**: digite parte do nome da empresa, do município, do
  CNPJ ou do código de uma notificação e a grade destaca só o que casa. Acentos não
  atrapalham ("goiania" acha "Goiânia").
- **Cada card diz o que fazer, não só quanto existe.** O card ganhou o contador de
  pendências e uma linha de "próximo passo" — a mesma sugestão que o dossiê já mostrava
  no destaque interno, agora ecoada na grade.
- **"Próximos vencimentos" agrupado por data.** Quatro DETs vencendo no mesmo dia eram
  quatro linhas repetidas; agora são um bloco só daquele dia, e o botão "agendar os 4 no
  Google Calendar" cria um evento único listando todos (evento por notificação continua
  sendo o /aft-agenda-det).
- **"Pendências por auditoria" deixou de ser um paredão de texto.** Virou um cartão por
  empresa, com a contagem, as 3 primeiras pendências resumidas e o link "abrir dossiê" —
  a empresa mais carregada vem primeiro. A lista completa continua no dossiê da OS.

Os consertos: as fontes do painel (Source Serif 4 e Hanken Grotesk) eram declaradas mas
nunca carregadas — todo mundo via o painel numa fonte substituta sem saber; agora elas
vêm do Google Fonts (só a fonte é baixada, nenhum dado da fiscalização sai da máquina, e
sem internet o painel segue funcionando com a fonte substituta). O markdown leve das
fichas (**negrito** e `código`) aparecia cru na tela, com asteriscos e crases — agora é
convertido de verdade, nas pendências da tela inicial e do dossiê. E um detalhe interno
de CSS (variável de fonte usada antes de ser definida) foi posto no lugar certo.

---
