## 10/08/2026 (5)
<!-- commit: autos-lavrados-reenquadramento-ementa -->

**O `/aft-autos-lavrados` agora reconhece quando você reenquadra a ementa de um auto
direto no Sistema Auditor, na hora de lavrar.** Isso acontece: o rascunho local prevê
uma ementa, mas ao lavrar você percebe que outro código descreve melhor a mesma
irregularidade e troca ali mesmo, no sistema. Antes, a skill não sabia disso — mostrava
o auto como "pendente de transmissão" (a ementa planejada não apareceu) mesmo ele já
tendo sido lavrado, só que sob outro código.

Agora, quando a constatação de fato bate (mesmo equipamento, mesmo local, mesma
descrição), a skill reconhece sozinha que é a mesma irregularidade sob outro
enquadramento: conta o auto como lavrado, explica a troca numa seção própria ("Ementas
reenquadradas no Sistema Auditor") e deixa uma nota no rascunho local (`autos.md`) sem
reescrever o texto do auto. Não pergunta nada — o que vale é o que foi efetivamente
lavrado, quem decidiu o reenquadramento foi você, no Sistema Auditor.

---
