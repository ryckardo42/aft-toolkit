## 27/08/2026
<!-- commit: vigia-sessoes-fechamento-rapido -->

**A sessão da OS nova que não aparecia depois de fechar e reabrir o app.** O toolkit cria
sozinho a sessão de cada auditoria no grupo "OS ATIVAS", e faz isso enquanto o app do
Claude está fechado — é a única hora em que dá para mexer com segurança. Quem cuida disso
é um vigia que fica em segundo plano olhando de tempos em tempos se o app fechou.

O intervalo dessa olhada era de 20 a 60 segundos. Se você fechava e reabria o app depressa
— um reinício rápido leva bem menos que isso —, o vigia simplesmente não via a janela de
app fechado: a sessão não era criada, e nada aparecia no registro dizendo por quê. Ficava
esperando o próximo fechamento, que podia ser só no fim do expediente.

Agora, **enquanto houver auditoria esperando sessão**, o vigia confere de 5 em 5 segundos.
Fechamento rápido deixa de escapar. Medido num teste com relógio controlado: numa janela
de 8 segundos de app fechado, o vigia antigo pegava 15 vezes em 50; o novo, 47.

Fora dessa espera ele continua no ritmo largo de sempre, e a conferência curta é a barata
— só olhar se o app está aberto. A conferência pesada, que copia dados do app, continua no
ritmo antigo, para não pesar na sua máquina justamente enquanto você trabalha.

Achado e corrigido pelo colega Diego.

---
