## 24/08/2026
<!-- commit: notificacoes-por-ordem-e-por-dia -->

**As pastas de NOTIFICACOES agora contam a história da notificação.** Três mudanças
pedidas pelo AFT, valendo para o botão do painel e para as skills de download do DET:

- **Ordem de lavratura no nome.** Cada pasta de notificação agora começa por um
  número: `01 - CODIGO 20-08-2026`, `02 - ...`. Ao abrir a pasta NOTIFICACOES, dá para
  ver de relance qual foi a primeira notificação da fiscalização, qual foi a segunda, e
  assim por diante. Se uma notificação antiga for baixada depois, as pastas se
  renumeram sozinhas para manter a ordem verdadeira.
- **A data no nome é a da lavratura**, não a do dia em que você baixou. Antes, uma
  notificação lavrada dia 20 e baixada dia 24 ficava com 24 no nome da pasta — agora
  fica com 20, que é a data que importa.
- **Uma subpasta por dia de download.** Tudo o que chega num download — os arquivos
  entregues pela empresa, o relatório de atendimento e o histórico dos itens — vai para
  uma subpasta `baixada em 24-08-2026` dentro da pasta da notificação. Como a mesma
  notificação pode ter prazos diferentes por item, cada dia de entrega fica separado, e
  o auditor sabe exatamente o que a empresa apresentou em cada data. O que já foi
  baixado num dia anterior não baixa de novo.

As pastas antigas se arrumam sozinhas no próximo download daquela notificação. Para
arrumar uma auditoria inteira de uma vez (ou todas), o `/aft-organiza-os` ganhou esse
passo — pode pedir "organiza as pastas de notificações" que ele aplica o padrão novo.

---
