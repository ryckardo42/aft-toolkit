## 22/07/2026
<!-- commit: det-sync-ri-estrito-alerta-visto -->

**Sync DET: o RI do front-matter agora manda sozinho** — a pesquisa no DET é
por CNPJ do empregador, e vinha acontecendo de o sync puxar notificações de
OUTRA fiscalização do mesmo empregador (outro RI, às vezes de outro auditor).
Agora o campo `ri:` da ficha (`memory.md`) é **o** identificador da auditoria:
só entra notificação daquele RI. Se a sua OS acompanha duas fiscalizações
(ex.: ação fiscal + acidente), declare os dois RIs no próprio campo, separados
por vírgula (`ri: "320038432, 320199999"`). Notificação de RI alheio continua
aparecendo no relatório do sync como "ignorada" — nunca some em silêncio.

**Alerta "⚠️ atualização pendente" agora é dispensável** — constatamos que a
API do DET pode continuar marcando a notificação como "atualização pendente"
mesmo depois de o triângulo amarelo sumir da tela (a tela apaga quando você
abre a notificação; o campo da API, não necessariamente). Então o alerta no
painel ficava aceso para sempre. Agora ele é **clicável**: clicou = "já vi", o
alerta some da ficha e do painel — e **volta sozinho** se a empresa fizer uma
entrega nova naquela notificação (novidade de verdade).
