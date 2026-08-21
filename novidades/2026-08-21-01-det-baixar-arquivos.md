## 21/08/2026
<!-- commit: det-baixar-arquivos -->

**Botão "baixar arquivos" nas notificações DET do painel.** Cada notificação
do cartão Notificações DET ganhou o botão **⬇ baixar arquivos**: um clique e o
painel busca direto na API do DET o PDF da notificação, o Relatório de
Atendimento e todos os arquivos que o empregador entregou — já organizados na
pasta da OS, uma subpasta por item solicitado, com a descrição oficial do item
no nome (o que o AFT rejeitou ou dispensou no DET vai separado, em
`invalidados/`). Nada de navegador clicando sozinho: são segundos, não minutos.
Funciona com o mesmo gesto de sempre: o **Sincronizar** da extensão Sync DET
abastece o painel por 25 minutos; se a janela passar, o botão avisa e basta
sincronizar de novo. Baixar de novo não duplica nada: o que já está na pasta é
pulado, e cada download entra no Registro de atividades da ficha. Quem prefere
pedir pelo chat usa a skill de download do DET, que agora chama esse mesmo
motor.

---
