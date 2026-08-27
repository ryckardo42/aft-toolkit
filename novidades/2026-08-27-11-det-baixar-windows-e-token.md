## 27/08/2026
<!-- commit: det-baixar-windows-issue-104 -->

**Download do DET consertado no Windows — e o extrato agora diz de quando é.** Um
caso real no Windows (pasta de trabalho no OneDrive) revelou quatro problemas
encadeados no download de notificação, todos corrigidos:

- **Caminho longo não trava mais.** A convenção nova de pastas (numeração +
  subpasta "baixada em") deixou os caminhos compridos, e o Windows tem um limite
  antigo de 260 caracteres — empresa com razão social longa estourava o limite e o
  download morria com um erro enganoso de "caminho não encontrado". Agora o toolkit
  usa a forma estendida de caminho do Windows, que não tem esse limite.
- **OneDrive não derruba mais o download.** Ao arrumar as pastas, o OneDrive às
  vezes segura por instantes uma pasta vazia que ia ser removida; isso virava
  "Acesso negado" e abortava tudo. Pasta vazia que sobra é só cosmética: agora o
  toolkit desiste dela em silêncio e o download segue.
- **Extrato antigo nunca mais se passa por novo (o mais importante).** Quando o
  download quebrava no meio, o histórico dos itens do download ANTERIOR podia parar
  na pasta do dia com cara de recém-baixado — e induzir uma análise com dados
  velhos (num caso real, quase virou conclusão errada de que a empresa não tinha
  respondido). Duas defesas: o `historico-itens.md` (e o `mensagens.md` do canal)
  agora carimbam no cabeçalho **a data e a hora em que foram extraídos do DET**, e a
  arrumação das pastas antigas só roda **depois** de o download terminar, nunca
  antes.
- **Menos idas ao Chrome para Sincronizar.** O `/aft-atualizar` reiniciava o
  servidor do painel a cada atualização, e o reinício apaga o crachá do DET da
  memória — obrigando um novo Sincronizar. Agora ele troca o código por dentro,
  sem derrubar o servidor, e o crachá sobrevive; só reinicia de verdade quando o
  próprio servidor mudou, e nesse caso avisa que vai pedir um Sincronizar.

De quebra, o ticket automático de erro ficou mais discreto: o código da
notificação do DET agora também é removido do texto antes de o ticket ser gravado
(aparece como `<NOTIFICACAO>`), junto com empresa, CNPJ/CPF e caminhos.

---
