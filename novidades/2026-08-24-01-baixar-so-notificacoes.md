## 24/08/2026
<!-- commit: baixar-so-notificacoes -->

**Agora dá para baixar só as notificações do DET, sem os arquivos que a empresa
enviou.** A skill nova `/aft-det-baixar-notificacoes` traz apenas o PDF de cada
notificação — o documento que você lavrou —, sem o Relatório de Atendimento, sem
o canal de comunicação e sem os anexos do empregador, que podem somar centenas de
megabytes. Serve para ler o que foi notificado, montar o histórico de uma empresa
ou conferir o texto de uma notificação antiga. Peça com "baixa só as notificações
dessa empresa" ou "só as notificações, não os arquivos enviados". Para o pacote
completo, a skill continua sendo a `/aft-det-baixar`.

Os PDFs vão para a mesma pasta de sempre (`NOTIFICACOES/<código> <data>/`), então
se depois você quiser o conteúdo completo daquela notificação, tudo se acumula no
mesmo lugar, sem duplicar.

**Uma diferença de propósito:** este modo **não apaga** o alerta amarelo de
"atualização pendente" no DET. O download completo apaga, porque faz as mesmas
leituras que o site faz quando você abre a notificação. Aqui não faria sentido:
você não olhou o que a empresa entregou, então o aviso continua na sua tela. O
toolkit não vai limpar um alerta que você ainda precisa ver.

---
