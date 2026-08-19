## 21/07/2026 (3)
<!-- commit: sessoes-vigia-automatico -->

**Sessões por empresa agora são 100% automáticas** — ontem as sessões do grupo
"OS ATIVAS" ainda dependiam de você aceitar uma oferta e fechar o app na hora.
Agora existe o **vigia de sessões**: um serviço em segundo plano (instalado por
padrão pelo `/aft-setup` e garantido pelo `/aft-atualizar`, como o servidor do
painel) que observa as suas pastas de OS ATIVAS e, toda vez que o app do Claude
é fechado, cria sozinho as sessões que faltam — com o nome da empresa, apontando
para a pasta da OS, dentro do grupo "OS ATIVAS". Você não responde mais nada:
criou uma auditoria (`/nova-os`), organizou um lote (`/organiza-os`) ou copiou
uma pasta à mão, e as sessões simplesmente **aparecem na próxima vez que você
abrir o app**. O `/aft-doctor` ganhou a checagem do vigia, e a `/sessoes-os`
vira a skill das exceções: conferir ("verifica as sessões"), aplicar AGORA sem
esperar o próximo reinício, desfazer tudo ou desligar o automático.

E cada sessão de empresa agora **nasce sabendo quem é**: o vigia mantém um
arquivo de contexto (`CLAUDE.md`) na pasta de cada OS, que o app carrega ao
abrir a sessão. Na primeira mensagem — "fiz essa notificação hoje, atualiza o
card e as datas" — o Claude já sabe que deve ler a ficha `memory.md`, que
"card/painel" é o painel do toolkit, quais skills usar e as regras de
privacidade. Sem esse briefing, a sessão nova respondia como um chat genérico.
