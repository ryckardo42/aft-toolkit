## 28/08/2026
<!-- commit: endereco-local-fiscalizacao -->

**A notificação do DET não trava mais por endereço incompleto de fazenda ou obra.**

Ao criar o rascunho de uma notificação (`/aft-tn-nco` ou `/aft-NAD`), o toolkit pegava o
endereço do cadastro da ordem de serviço. Em fiscalização rural esse cadastro costuma vir
pela metade — só "zona rural" e o CEP, sem rua, número, município e estado. Como o DET
recusa a lavratura sem esses quatro campos, o rascunho simplesmente não era criado, e a
mensagem de erro não dizia o que fazer.

Agora:

- **A ficha da auditoria (`memory.md`) pode guardar o endereço do local onde a
  fiscalização aconteceu** — a fazenda, o canteiro, a frente de serviço. O toolkit usa
  esse endereço para completar o que faltava no cadastro.
- **A pergunta acontece uma vez por auditoria.** Quando o endereço falta, a skill pergunta
  e grava na ficha; da próxima notificação em diante, não pergunta mais. Vale para as duas
  skills que escrevem no DET.
- **Antes de perguntar, ela procura.** O endereço costuma já estar na inspeção física da
  OS ou numa notificação anterior da mesma auditoria — nesse caso ela só pede sua
  confirmação, em vez de fazer você digitar tudo de novo.
- **É o endereço do local fiscalizado, não o da Receita Federal.** Numa montagem em
  fazenda os dois ficam a centenas de quilômetros um do outro, e o que vale para a
  notificação é onde você esteve.
- **O que você já informou nunca é sobrescrito.** A ficha só preenche campo que estava em
  branco — se o cadastro da ordem de serviço já trazia o dado, ele é mantido.

Auditoria nova (`/aft-nova-auditoria`) já nasce com os campos de endereço na ficha, vazios
para preencher quando você souber.

---
