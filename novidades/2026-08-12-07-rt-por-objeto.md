## 12/08/2026
<!-- commit: rt-por-objeto -->

**O Relatório Técnico de interdição/embargo agora sai em dois formatos: por TÓPICO ou por OBJETO.**
O formato de sempre (por tópico) continua sendo o padrão: seções temáticas — 4.
Irregularidades, 5. Fatores de Risco, 6. Medidas, 7. Documentos — cada uma cobrindo todos
os objetos. A novidade é o formato **por objeto**, que alguns AFTs preferem no Sistema
Auditor quando a medida atinge objetos de naturezas diferentes: cada objeto da seção 3
vira um "dossiê" completo, com suas próprias irregularidades, fatores de risco, medidas
e documentos, e a Conclusão renumera sozinha. O que muda no uso:

- **Objetos de tipos diferentes** (ex.: uma máquina + um setor de serviço, ou atividade +
  setor + estabelecimento): a `/aft-embargo-interdicao` agora **pergunta obrigatoriamente**
  qual formato você quer, antes de montar o documento. Com objetos do mesmo tipo, segue
  no padrão por tópico sem perguntar — a menos que você peça "por objeto".
- **No formato por objeto**, o bloco fixo da metodologia da NR-03 (com as Tabelas
  3.1/3.2/3.3) passa para o fim da seção "Da Ação Fiscal", antes da lista de objetos; e a
  alínea fixa "Requerimento expresso..." das medidas é dispensada, porque a mesma
  exigência já consta do bloco fixo DO PEDIDO DE SUSPENSÃO.
- **No formato por tópico com mais de um objeto**, os itens agora saem prefixados com a
  referência ao objeto ("Objeto 1 - ...", "Objetos 2 e 3 - ..."), como os AFTs fazem no
  Sistema Auditor — antes não dava para saber qual irregularidade era de qual objeto.
- **A seção Conclusão/Observação pode ser preenchida pelo script** (campo novo, opcional)
  — antes ela sempre saía em branco para completar no Word.
- **O tipo ESTABELECIMENTO entrou na lista de objetos** da skill. A NR-03 prevê quatro
  hipóteses de interdição (atividade, máquina/equipamento, setor de serviço e
  estabelecimento) e a última não constava.
- O verificador de coerência RT × autos reconhece os dois formatos — e, no formato por
  objeto, sabe que uma ementa repetida em vários objetos rende um auto só.
