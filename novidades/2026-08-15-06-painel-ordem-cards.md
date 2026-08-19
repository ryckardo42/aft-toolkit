## 15/08/2026
<!-- commit: painel-ordem-cards -->

**A ordem dos cards do painel foi corrigida, e agora dá para ordenar por prazo de DET.**
Os cards estavam saindo fora de ordem porque o painel usava a data de criação do
*arquivo* `memory.md` para saber quando cada auditoria nasceu — e essa data muda sozinha
quando a pasta é copiada, restaurada ou recriada por sincronização, além de sair idêntica
para várias OS criadas no mesmo lote (aí o desempate caía no nome, em ordem alfabética).
Agora o painel lê a data de dentro da própria ficha: a linha **"OS cadastrada"** do
Registro de atividades. Para auditorias antigas, que não têm essa linha, ele usa a data
mais antiga entre o início da fiscalização e a primeira atividade registrada — e só
recorre ao carimbo do arquivo se a ficha não tiver nada disso.

Junto veio um seletor **"ordenar por"**, acima dos cards, com duas opções:

- **auditoria mais recente** (padrão) — a ordem de sempre, agora correta;
- **prazo de DET mais urgente** — quem está mais perto de vencer, ou já vencido, aparece
  primeiro; auditorias sem prazo em aberto vão para o fim.

A escolha fica guardada no navegador: se você prefere ver por prazo, o painel abre assim
nas próximas vezes. A troca é instantânea, sem regerar a página.
