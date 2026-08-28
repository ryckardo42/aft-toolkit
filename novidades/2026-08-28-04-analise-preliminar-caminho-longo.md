## 28/08/2026 (4)
<!-- commit: analise-preliminar-caminho-longo -->

**A triagem preliminar não perde mais itens por caminho longo no Windows.** Um AFT
relatou (ticket de 28/08/2026) que a `/aft-analise-preliminar` de uma notificação com 8
itens listou só 6 e ainda subcontou os arquivos de um terceiro: a pasta dele fica dentro
do OneDrive, os nomes de item do DET são longos, e o caminho completo passava dos 260
caracteres que o Windows aceita por padrão. Acima desse limite o inventário simplesmente
não enxergava as pastas, sem nenhum erro na tela — e item entregue podia aparecer como
"não entregue".

- **Corrigido na raiz.** O script de inventário agora usa o modo de caminho estendido do
  Windows (o mesmo remédio já aplicado no download do DET, que tinha o defeito irmão) e
  enxerga qualquer profundidade de pasta. Quem usa Mac não era afetado e não muda nada.
- **Fim das falhas silenciosas.** Se algum arquivo não puder ser lido por qualquer outro
  motivo (por exemplo, arquivo do OneDrive "somente na nuvem" sem internet no momento), a
  varredura não pula mais calada: o arquivo entra na contagem quando possível e o
  problema sai listado no relatório, na seção de decisões pendentes, avisando que a
  contagem daquele item merece conferência.
- **Conferência cruzada.** A triagem passou a comparar os itens do inventário com a lista
  da própria notificação: item que existe na notificação mas não aparece na pasta agora
  gera conferência manual, nunca um "não entregue" automático.

**O que você precisa fazer: nada.** Basta atualizar o toolkit (`/aft-atualizar`). Se uma
triagem recente sua bateu com contagem estranha em pasta do OneDrive, vale rodar a
`/aft-analise-preliminar` de novo naquela notificação.

---
