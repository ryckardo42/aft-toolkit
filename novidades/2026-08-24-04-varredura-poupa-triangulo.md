## 24/08/2026
<!-- commit: varredura-poupa-pendentes -->

**A varredura do DET agora respeita o triângulo amarelo.** Regra nova na
sincronização em lote do /aft-organiza-os: notificação com alerta de atualização
pendente (o triângulo amarelo do DET) **nunca entra na varredura** — nem mesmo quando
a pasta dela ainda não existe. Motivo: o download completo registra a visualização no
DET e apagaria o alerta em silêncio, sendo que o triângulo é justamente o aviso de
que há entrega que você ainda não viu.

Essas notificações voltam listadas no relatório da varredura, e a skill pergunta se
você quer baixar alguma — cada uma que você autorizar é baixada individualmente (o
mesmo /aft-det-baixar de sempre), e aí sim o alerta se apaga, como decisão sua, uma a
uma. O lote continua baixando normalmente tudo o que falta nas pastas e não tem
alerta aceso.

---
