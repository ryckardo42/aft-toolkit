## 12/08/2026
<!-- commit: anexos-limite-soma -->

**Correção importante: os 10 MB de anexo do Sistema Auditor são a SOMA dos anexos de
cada auto de infração — não o tamanho de cada arquivo.**
Até agora o `/aft-gera-ai` tratava os 10 MB como limite por arquivo. Estava errado: o
Sistema Auditor olha o total do auto. Três fotos de 4 MB no mesmo auto, nenhuma acima do
limite, somam 12 MB — e a importação do TXT é recusada inteira, com todos os autos junto.

- O `/aft-gera-ai` agora fecha a conta **auto por auto** e comprime o que for preciso,
  dividindo o orçamento de 10 MB entre os anexos daquele auto.
- Anexar o mesmo PDF a vários autos continua normal — é o caso do PGR e da AET. Ele pesa
  uma vez no orçamento de cada auto que o recebe; o que não pode é estourar em algum.
- A validação que roda antes de o TXT chegar às suas mãos passa a **reprovar** o arquivo
  quando um auto estoura, dizendo qual auto é e quanto cada anexo dele ocupa. O erro
  aparece aqui, em segundos, em vez de virar um "AI RECUSADO" lá dentro do sistema.
- A compressão agora pode ser feita no próprio anexo, sem trocar o nome — quando ela
  entra em cena, o TXT não precisa ser gerado de novo. Comprimir um documento que vai em
  vários autos (o PGR, a AET) alivia todos eles de uma vez.
