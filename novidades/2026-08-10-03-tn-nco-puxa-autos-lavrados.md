## 10/08/2026 (6)
<!-- commit: tn-nco-puxa-autos-lavrados -->

**A `/aft-tn-nco` agora já sabe sozinha o que você autuou.** Antes, se você pedia "faz
uma notificação para toda irregularidade autuada", ela dependia de você ter rodado o
`/aft-autos-lavrados` antes — senão trabalhava de memória, com risco de deixar auto de
fora ou notificar o que não foi lavrado.

Agora, toda vez que a skill roda, ela confere primeiro o Sistema Auditor (reaproveita o
retrato do dia, se já existir), mostra a lista numerada do que foi lavrado e abre um
**checklist na tela** para você marcar quais ementas quer notificar no DET. Se o Sistema
Auditor não estiver ao alcance na hora, ela avisa em uma linha e segue pela ficha da OS
— a notificação nunca fica travada. Em OS ainda não autuada (dupla visita, ME/EPP), nada
muda: ela segue direto pelo que foi constatado.

Os autos que vieram de **interdição ou embargo** aparecem no checklist já desmarcados,
com o lembrete de que a correção deles costuma seguir o rito próprio (a empresa
apresenta laudo/AR, você julga e depois levanta a medida), e não uma notificação comum
pelo DET. Se a mesma exigência valer para outras máquinas não interditadas, é só marcar
— quem decide é você.

---
