## 24/08/2026
<!-- commit: organiza-os-varredura-det -->

**O /aft-organiza-os agora oferece sincronizar as pastas com o DET.** Ao final da
organização (ou quando você pedir direto "sincroniza minhas pastas com o DET"), a
skill pergunta se você quer uma varredura completa: ela consulta o DET, importa para
as fichas as notificações que ainda não estavam registradas e baixa, em todas as
auditorias de uma vez, o que falta nas pastas — o PDF da notificação, os documentos
entregues pela empresa e o relatório de atendimento, já no padrão novo (pasta
numerada, subpasta por dia).

A varredura é esperta: notificação que já está em dia na pasta fica quieta — só
baixa o que não existe localmente ou o que tem entrega nova no DET. Se a chave de
sessão vencer no meio, é só renovar e rodar de novo: nada baixa em dobro — e se o
servidor do painel engasgar durante o lote, a varredura espera ele voltar e segue
sozinha. O download
completo registra a visualização no DET (o triângulo amarelo se apaga nas
notificações baixadas), e empresa sem auditoria cadastrada não entra — para essas, o
caminho continua sendo o /aft-nova-auditoria.

---
