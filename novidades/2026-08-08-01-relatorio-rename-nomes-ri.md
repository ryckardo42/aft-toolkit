## 08/08/2026 (2)
<!-- commit: relatorio-rename-nomes-ri -->

**O `/aft-sfitweb-rel` agora se chama `/aft-relatorio` — e os arquivos saem
nomeados pelo RI da fiscalização.**

- **Nome novo, hábito antigo preservado.** O comando é `/aft-relatorio`. Se você
  pedir "SFITWEB-REL" por costume, a skill continua atendendo — o nome antigo
  virou frase de acionamento. Todo o toolkit foi atualizado (README, painel,
  arquitetura, CLAUDE.md do AFT). O nome **SFIT-WEB do sistema do governo** não
  mudou em lugar nenhum: os PDFs de Demanda/OS da `/aft-nova-os` e da
  `/aft-preparacao-acao-fiscal`, e o campo do SFITWEB onde você cola o texto,
  seguem com o nome de sempre.
- **Arquivos com o número do RI.** Os três arquivos do relatório passam a se
  chamar `Relatorio auditoria RI <ri>` — ex.: `Relatorio auditoria RI
  320457354.docx` (e o `.md` e o `.json` com o mesmo nome-base). O RI é lido do
  `memory.md` da OS. Se o RI estiver em branco lá, o nome sai como
  `Relatorio auditoria`, sem interromper você para perguntar.
- **O dossiê dos autos vem junto, com o nome do RI.** O PDF único de autos +
  anexos continua sendo gerado pela `/aft-autos-pdf-reunidos` no lugar de sempre
  (`AUTOS/Autos reunidos/`), e agora uma **cópia** vai para a pasta do relatório
  como `RI 320457354 - autos e anexos.pdf`. Assim a pasta
  `Relatórios de Fiscalização/` tem, lado a lado e com nomes que se explicam, o
  relatório e o dossiê que ele cita — e a página "ANEXOS" dentro do .docx passou
  a apontar para o nome certo do arquivo.
- A pasta continua sendo `Relatórios de Fiscalização/` dentro da OS; nada foi
  movido nem renomeado no que você já tinha gerado.

---
