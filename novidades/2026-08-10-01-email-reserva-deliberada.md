## 10/08/2026 (8)
<!-- commit: email-reserva-deliberada -->

**O e-mail da `/aft-email` agora empurra o empregador para dentro do DET.** A ideia é
simples: o e-mail avisa, mas quem tem de dar ciência é o sistema oficial. Por isso o
texto passa a guardar informação de propósito.

O que muda em e-mail de notificação do DET:

- **Assunto genérico**, sem código, sem número, sem o tema da fiscalização — por exemplo
  "Auditoria-Fiscal do Trabalho — nova notificação eletrônica (DET) transmitida".
- **Não perguntamos mais o código da notificação nem o prazo de atendimento.** Se você
  não informar, o e-mail sai sem eles. Se informar, entram normalmente.
- **Só alguns itens são citados** (dois ou três, a título de exemplo), com o aviso
  expresso de que o inteiro teor está no DET e de que o acesso deve ser feito o mais
  rápido possível.
- **A assinatura sai sempre com o seu nome** (o `nome_auditor` do `aft-config.md`), e a
  skill não pergunta mais por outros integrantes da ação fiscal.

**E-mail de Termo de Interdição/Embargo vai no sentido oposto — e ficou mais direto ao
ponto.** Ali não há reserva nenhuma: o Termo e o relatório técnico seguem em anexo, e o
e-mail existe para cobrar uma coisa só, com urgência — **a devolução do anexo assinado
digitalmente, o mais rápido possível**. O pedido aparece no assunto, logo no começo do
texto e de novo no fecho. O corpo frisa algumas informações do ato (o que foi
interditado ou embargado e por quê), lembra que a medida produz efeito desde já, e o
bloco do SEI continua obrigatório para o pedido de suspensão.

---
