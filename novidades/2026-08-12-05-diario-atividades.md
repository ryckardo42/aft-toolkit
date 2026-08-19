## 12/08/2026
<!-- commit: diario-atividades -->

**Diário de atividades: o toolkit agora anota em que dia você trabalhou em cada
auditoria — e monta sozinho a agenda do mês e as atividades do RI.**
No fim do mês, em vez de reconstruir de memória o que fez em cada dia útil, você pede
`/aft-diario` e recebe: a agenda do mês dia a dia (com alerta dos dias úteis sem nenhum
registro), e, por auditoria, a lista pronta para transcrever na tela **2.1 Atividades**
do RI no SFIT-WEB, já com o texto oficial de cada opção. Como funciona:

- **Cada dia trabalhado entra na ficha da própria OS** (tabela "Registro de
  atividades" do memory.md), classificado com as letras da tela do RI: **A**
  preparação/planejamento · **B** início da fiscalização · **C** inspeção/auditoria/
  entrevista no estabelecimento · **D** análise de documentos fora do estabelecimento ·
  **E** elaboração de documentos e lançamento em sistemas · **F** fim da fiscalização.
- **As skills registram sozinhas**: a preparação registra A, a narração da inspeção
  registra B/C **na data em que você disse ter visitado** (e E no dia do registro), as
  análises documentais (PGR, AET, jornada, acidente...) registram D, a redação de
  autos/notificações/e-mails registra E, o relatório final registra F. Tudo com
  deduplicação: repetir não duplica.
- **Rede de segurança automática**: mesmo fora de skill, toda vez que o Claude mexer na
  ficha de uma OS o dia fica anotado (sem classificação) — nada se perde. Instala-se
  sozinha no `/aft-setup` e no `/aft-atualizar`.
- **O painel ganhou a aba "Calendário"**: grade do mês com as empresas e letras de cada
  dia, contador de dias trabalhados, dias úteis sem registro marcados, e — no modo
  interativo — o botão "Registrar dia trabalhado" (empresa + data + letras) para
  completar manualmente.
- OS **arquivada no meio do mês** continua aparecendo na agenda mensal; o consolidado
  varre OS ATIVAS e OS ARQUIVADAS.
