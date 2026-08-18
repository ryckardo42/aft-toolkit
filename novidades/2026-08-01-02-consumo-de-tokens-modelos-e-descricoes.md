## 01/08/2026
<!-- commit: consumo-de-tokens-modelos-e-descricoes -->

**O toolkit ficou bem mais econômico — e nenhuma skill depende mais do modelo que
estiver escolhido na caixa do chat.** Alguns colegas relataram gasto excessivo de
uso. Fomos atrás e achamos três causas. Você não precisa fazer nada: tudo chega pelo
`/aft-atualizar`.

- **Menos texto carregado o tempo todo.** O app precisa manter em memória um resumo de
  cada uma das 40 skills, mesmo as que você não usa naquele dia. Esses resumos estavam
  longos demais e foram enxugados pela metade — só isso já corta cerca de 5 mil
  "palavras de contexto" de toda conversa, antes mesmo de você pedir qualquer coisa.
  O arquivo de perfil (o CLAUDE.md do toolkit) também foi apertado.
- **Cada skill agora diz qual modelo usar.** Dez skills não diziam e acabavam herdando
  o que estivesse selecionado na caixa — inclusive as que redigem auto de infração e
  relatório de interdição, que podiam cair num modelo rápido demais para a tarefa, e as
  calculadoras de CNAE, SESMT e CIPA, que só rodam uma conta e estavam consumindo um
  modelo caro à toa. Todas foram acertadas.
- **Fim de uma cobrança extra silenciosa.** Cinco skills pediam uma variante do modelo
  com "memória estendida" (o sufixo `[1m]`). Nos planos Max, Team e Enterprise isso não
  fazia diferença nenhuma; **no plano Pro, essa variante é paga à parte e vinha
  consumindo créditos avulsos sem necessidade**. O pedido foi retirado, e de quebra as
  skills passaram a usar a geração mais recente do modelo, pelo mesmo preço.
- **Raciocínio proporcional à tarefa.** Skills mecânicas (conferir instalação, gerar
  documento, agendar prazo) passaram a trabalhar em modo econômico. As que exigem
  análise — PGR, AET, acidente, interdição, laudo de máquina — continuam no modo mais
  caprichado.
- **Conversa longa perde menos coisa importante.** Quando o app precisa resumir uma
  conversa que ficou muito longa, agora ele sabe o que preservar: a pasta da OS em uso,
  CNPJ, códigos de DET, ementas e enquadramentos já decididos, e o que já foi gravado
  em disco. Os apelidos de trabalhador (`[[TRAB_01]]`) continuam protegidos no resumo.

**E uma recomendação simples, que vale mais que todas as outras juntas: deixe a caixa de
modelo do app em Sonnet.** Depois desta atualização, 31 das 40 skills usam Sonnet — com a
caixa nele, o toolkit inteiro trabalha sem ficar trocando de modelo no meio da conversa
(cada troca faz o app reler tudo o que já foi dito, e é isso que mais consome). Duas
observações:

- **Ponha a caixa em Opus só quando a sessão for julgar um documento técnico que a
  empresa entregou** — análise de PGR, de AET, de acidente, de laudo de máquina, ou RT de
  manutenção de interdição. Nesses casos o Claude passa a te lembrar sozinho no começo da
  conversa. Nas demais, Sonnet.
- **O nível de esforço fica em "alto"** — o `/aft-setup` já configura isso para quem
  ainda não escolheu um nível (se você já escolheu o seu, ele não mexe). As tarefas
  mecânicas do toolkit baixam esse nível sozinhas quando é o caso; o que continua no alto
  é justamente enquadrar irregularidade, consultar ementa e redigir auto ou RT.
