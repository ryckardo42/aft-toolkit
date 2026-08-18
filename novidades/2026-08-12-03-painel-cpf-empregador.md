## 12/08/2026
<!-- commit: painel-cpf-empregador -->

**Empregador pessoa física (produtor rural, empregador doméstico) agora aparece com o
CPF no painel — e volta a ser sincronizado com o DET.**
Quando o empregador é pessoa física, o identificador é o CPF/CAEPF, não o CNPJ. Se a
ficha da OS registrava esse número como `**CPF:**` (no corpo) ou `cpf:` (no
front-matter), o painel não o enxergava: o card mostrava "CNPJ não informado", e o sync
automático do DET pulava a auditoria por "sem CNPJ/CPF nem RI". Agora:

- O painel lê o identificador em qualquer uma das formas — `cnpj:`, `cpf:` ou `caepf:`
  no front-matter, e `**CNPJ:**`, `**CPF:**`, `**CAEPF:**` ou `**CNPJ/CPF:**` no corpo —
  e exibe o CPF formatado (000.000.000-00) no card.
- O sync do DET usa o mesmo critério, então as notificações de empregador pessoa física
  passam a ser importadas normalmente.
- Onde o número realmente não foi informado, o card agora diz "CNPJ/CPF não informado",
  em vez de sugerir que só CNPJ serve.

Nada precisa ser corrigido à mão nas fichas antigas: elas passam a funcionar como estão.

---
