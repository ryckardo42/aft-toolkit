## 06/08/2026 (2)
<!-- commit: preparacao-vinculos-ativos-sesmt -->

**Anexe a Relação de Vínculos Ativos e a preparação sabe o efetivo exato, quem
procurar e se o SESMT está completo.**

- **A Relação de Vínculos vira dado, sem você fazer nada.** Anexe o PDF
  (`ImprimirVinculosAtivosPDF...`) junto com a OS. Um script lê o arquivo
  **inteiramente no seu computador** — nem o PDF nem a lista de nomes chegam a ser
  lidos pelo Claude — e devolve o efetivo, quantos homens e mulheres, quantos PCD,
  aprendizes e menores de 18. Esses números vão para o `memory.md`.
- **Quem procurar no estabelecimento.** O dossiê passa a trazer, com nome e
  ocupação, o pessoal do SESMT e os prováveis interlocutores: gerente de
  departamento pessoal (ou o RH de maior nível que houver) e gerente de produção.
  É quem vai prestar informação na visita. Nenhum outro trabalhador é nomeado —
  os demais viram contagem por ocupação.
- **SESMT devido x SESMT existente.** Com o CNAE e o efetivo, a preparação agora
  também roda a `/aft-dimensionamento-sesmt-nr04` e põe no dossiê uma tabela
  comparando o Anexo II com o que consta da Relação: "exige 3 técnicos de
  segurança, a Relação traz 2 — faltam 1". O documento avisa, junto, que isso é
  indício a confirmar em campo: o profissional pode estar registrado sob outra
  ocupação, lotado em outro estabelecimento, ou o serviço ser comum a mais de uma
  empresa.
- **Efetivo é homens + mulheres.** Na Relação, os PCD e os aprendizes já estão
  contados dentro desses dois números — somar as cinco colunas contaria gente duas
  vezes e inflaria SESMT e CIPA. O script ainda confere o quadro-resumo contra a
  lista nominal e avisa se divergirem.

Sem a Relação de Vínculos nada muda: a preparação continua funcionando com o
número que você informar.

---
