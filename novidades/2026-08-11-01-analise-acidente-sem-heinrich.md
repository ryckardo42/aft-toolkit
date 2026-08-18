## 11/08/2026
<!-- commit: analise-acidente-sem-heinrich -->

**A `/aft-analise-acidente` não fala mais em "ato inseguro" nem "condição insegura".**
Esse par vem da teoria dominó de Heinrich, dos anos 1930, e não é a metodologia da
inspeção do trabalho — que trabalha com a Árvore de Causas: fatos objetivos, sem rótulo
de culpa colado na conduta do trabalhador. O defeito foi detectado em uso real: a skill
chegou a classificar como "ato inseguro" o manuseio de ferramenta fornecida pela própria
empresa, em análise de acidente fatal. O que muda:

- **Os Fatores Imediatos agora são enunciados como fatos** — o que a tarefa exigia, que
  meios a organização forneceu, que condições existiam, que medida de prevenção estava
  ausente. Fica expressamente proibido rotular conduta do trabalhador como "ato
  inseguro", "erro", "falha humana" ou "desatenção", e rotular o ambiente de "inseguro".
- **Vedação registrada nas restrições de segurança da skill:** o par de Heinrich só pode
  aparecer para ser criticado. Os fatores causais são mapeados nas famílias de gestão da
  tabela oficial do SFIT (251 a 260), que nunca teve família "ato inseguro".
- **A consulta ao guia de análise de acidentes deixou de ser opcional.** Antes de
  redigir as seções de análise, a skill agora consulta obrigatoriamente o NotebookLM
  guia-analise-acidentes e a Instrução Normativa de regência. Se a sessão do NotebookLM
  estiver expirada, a análise para e pede o `/aft-notebooklm-login` — não segue mais no
  improviso do roteiro interno.

---
