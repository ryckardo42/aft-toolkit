## 15/08/2026
<!-- commit: agenda-det-rotina-diaria -->

**A sincronização dos prazos de DET com o Google Calendar agora pode rodar sozinha — se
você quiser.** Até aqui, o `/aft-setup` até perguntava se você queria a sincronização
diária, mas parava na pergunta: anotava a resposta e não instalava nada. Na prática, só
funcionava sob demanda, quando você pedia `/aft-agenda-det`. Agora, quando você responde
que quer, o toolkit cria de fato uma tarefa agendada do Claude, que roda toda manhã
(sugestão: 07h15, logo depois da rotina do painel) e espelha os prazos.

**Continua sendo escolha sua, em duas perguntas separadas:** primeiro se quer os prazos
no Google Calendar; depois, só se disse que sim, se prefere sob demanda ou todo dia. Quem
não quiser não instala nada, e quem mudar de ideia pede para apagar a tarefa. Nada é
instalado sem você pedir, e a skill nunca apaga eventos do seu calendário.

Uma limitação importante, avisada na hora da instalação: a tarefa **só roda com o
aplicativo do Claude aberto**. Se o computador estiver desligado no horário, ela não se
perde — roda na próxima vez que você abrir o app.
