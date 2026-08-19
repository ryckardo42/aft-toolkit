## 19/08/2026

<!-- commit: det-cancelada-e-canal-comunicacao -->

**Notificação cancelada some dos prazos, e o painel passa a avisar quando o empregador
te mandou mensagem no DET.** Duas mudanças no cartão de Notificações DET.

**1. Notificação cancelada não vira mais prazo.** Quando você cancela uma notificação no
DET, ela deixa de valer — não corre prazo, não cabe auto por omissão, não é compromisso
nenhum. Mas o painel vinha tratando ela como qualquer outra: entrava na ficha da OS,
contava no total e até ia parar na agenda de vencimentos.

Agora **notificação cancelada nunca mais entra na ficha**. E a que já estava lá — porque
foi cancelada *depois* de importada — **não é apagada**: ela continua aparecendo, mas
riscada e apagadinha, com o selo "cancelada no DET". Sai do contador, sai de todo cálculo
de prazo, sai da agenda. Fica visível porque você precisa saber que ela foi cancelada
(às vezes o cancelamento é notícia), mas para de cobrar coisa nenhuma de você. Se quiser
tirar a linha da ficha, é você quem decide — o toolkit não apaga linha sua sozinho.

O relatório da sincronização também passou a dizer quantas canceladas encontrou.

**2. O envelope laranja do DET agora aparece no painel.** Na tela de notificações do DET
existe um ícone de carta laranja: quer dizer que o **empregador mandou mensagem no canal
de comunicação daquela notificação e ela está esperando resposta sua**. Isso não aparecia
em lugar nenhum do painel — só se você entrasse no DET e olhasse.

Agora esse aviso aparece nos **dois lugares**: no quadro inicial, direto no cartão da
auditoria (ao lado do "⚠️ atualização pendente", no mesmo estilo), e lá dentro, na
notificação exata que tem a mensagem — assim você vê de longe que aquela empresa está
esperando resposta, sem precisar abrir a OS. Se houver mais de uma notificação com
mensagem, o selo do quadro inicial mostra quantas.

O selo some sozinho quando você responde lá no DET, então não tem botão de dispensar: se ainda está ali, é
porque a mensagem continua sem resposta. (Diferente do "⚠️ atualização pendente", que
teima em não sumir e por isso tem o "já vi".)

Nenhuma das duas exige atualizar a extensão do Chrome nem mexer em configuração: as
informações já vinham do DET, só não estavam sendo aproveitadas — basta sincronizar uma
vez para os selos aparecerem.

**3. E um conserto silencioso, que você nunca teria como descobrir.** Ao testar as duas
mudanças acima, apareceu um problema mais velho: o motor que conversa com o DET era
carregado **uma única vez, quando o servidor do painel liga** — e o servidor fica ligado
por semanas. Resultado: uma atualização do toolkit era instalada e simplesmente **não
valia**, sem erro nenhum, até o computador ser reiniciado. Foi o que aconteceu aqui: a
sincronização rodou com o motor de quatro dias antes e gravou as fichas do jeito antigo.
Agora a publicação de uma atualização reinicia esse serviço sozinha, no Mac e no Windows.

---
