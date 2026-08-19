## 17/08/2026
<!-- commit: skills-calculo-caminho-absoluto -->

**Os três cálculos automáticos voltaram a funcionar fora do Claude Code.** As skills que
calculam SESMT (`/aft-dimensionamento-sesmt-nr04`), CIPA
(`/aft-cipa-nr05-dimensionamento`) e grau de risco por CNAE
(`/aft-cnae-grau-risco-nr04`) mandavam rodar o script por um caminho *encurtado*, que só
acertava se o assistente já estivesse "parado" dentro da pasta da própria skill. No
Claude Code isso acontece por acaso e funcionava; em outros assistentes (o Hermes, e
possivelmente o Codex e o Antigravity), o assistente está parado na pasta da sua
auditoria — e o comando falhava com "arquivo não encontrado".

**Por que isso era grave.** Ao ver o comando falhar, o assistente não avisava: ele
desistia do script e ia ler a tabela do Anexo II *por conta própria*, que é exatamente o
que a regra de ouro dessas três skills proíbe. O resultado saía com cara de certo e
número errado. Num caso real de 17/08/2026, um dimensionamento de SESMT veio com o
número de profissionais trocado. São justo as três skills em que a conta é fechada e
verificável — e um número errado aí pode sustentar uma autuação indevida.

**O que mudou.** As três passaram a usar o caminho completo do script, o mesmo padrão
que as outras 47 skills do toolkit já usavam. Agora o comando roda a partir de qualquer
pasta, em qualquer assistente. De quebra, cada uma ganhou um lembrete de que o
interpretador Python é o do seu `aft-config.md` (o `python3` solto costuma ser um atalho
vazio no Windows) e de que, se ainda assim algo falhar, o assistente deve dizer — e
**nunca** responder o cálculo de cabeça.

Você não precisa fazer nada: o `/aft-atualizar` já traz a correção.

---
