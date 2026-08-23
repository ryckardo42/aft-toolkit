## 23/08/2026
<!-- commit: porte-do-auto-lavrado -->

**O porte da empresa e o número de trabalhadores vêm de graça do primeiro auto lavrado.**
Várias skills perguntam o porte (regra de dupla visita, pares de ementa ME/EPP) e o
número de trabalhadores (CIPA, SESMT, NR-24) — dados que, assim que existe um auto
efetivamente lavrado, já estão impressos no próprio PDF do Sistema Auditor. A
`/aft-autos-lavrados` agora extrai os dois campos na varredura e completa a ficha
(`memory.md`) da OS com eles. Duas cautelas embutidas: auto ainda em rascunho não tem
esses campos preenchidos (saem em branco no PDF) e é ignorado; e o que você já escreveu
na ficha à mão nunca é sobrescrito — o dado do PDF só entra onde estiver faltando.

---
