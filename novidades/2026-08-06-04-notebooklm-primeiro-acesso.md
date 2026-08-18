## 06/08/2026
<!-- commit: notebooklm-primeiro-acesso -->

**Agora o Claude te diz, antes de você precisar, quais notebooks do ementário ele
consegue consultar — e o que fazer com os que faltam.** Era uma armadilha silenciosa:
colegas com o acesso liberado viam a consulta de ementa falhar do nada, em uma NR
específica, sem entender por quê.

- **O motivo era o próprio catálogo.** O mapa de notebooks do toolkit apontava para
  quatro que ninguém conseguia abrir: três já apagados e um que nunca foi compartilhado.
  A skill mandava consultar, o Google respondia "não encontrado" e a consulta morria ali.
  Foram removidos.
- **O que muda.** No `/aft-setup` e sempre que você pedir *"confere meus notebooks"* (ou
  reconectar o NotebookLM), o Claude percorre os notebooks um por um e mostra quantos
  estão prontos — e, se faltar algum, o **link direto de cada um**. Duas coisas podem
  fazer um notebook faltar: a liberação de acesso ainda não veio (solicite no portal), ou
  o Google ainda não o pôs na sua coleção. Nos dois casos vale abrir o link, escrever um
  **oi** na caixa de chat e fechar — resolve de uma vez, para sempre.
- **Não precisa abrir todos** — e o Claude te diz por onde começar. A lista vem em dois
  blocos: primeiro os **13 do dia a dia** (Ementário SST, Ementário Legislação, NR-12,
  NR-01, NR-03, NR-18, NR-10, NR-04, NR-05, NR-24, Informalidade, NR-35 e NR-13), que
  cobrem a maior parte da fiscalização; depois os temáticos, só se você fiscalizar
  aquele assunto. Se algum pedir acesso, é porque a liberação ainda não veio: solicite em
  https://notebooks-aft.vercel.app com a sua conta Google.
- **Fim de um teste que enganava.** A instalação dizia "se a lista de notebooks aparecer,
  está pronto" — mas aquela lista mostra só os notebooks **abertos recentemente**, então
  vinha vazia mesmo com tudo funcionando. Agora a conferência é notebook por notebook.
- **Notebook novo numa atualização?** O `/aft-atualizar` percebe e já avisa quais abrir.

Os cinco notebooks retirados do mapa: `Acidentes`, `Especialista em NR-31` e `NHO 11`
(não existem mais) e `Refrigeração em frigoríficos` e `Apreciação de risco` (particulares
do mantenedor, nunca compartilhados). Nenhuma skill fica sem fonte — a análise de laudo de
máquina da `/aft-auditoria-AR-NR12` sempre consultou o notebook da NR-12.

---
