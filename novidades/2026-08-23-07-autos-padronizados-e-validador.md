## 23/08/2026
<!-- commit: autos-padronizados-e-validador -->

**Autos de uma mesma leva saem padronizados, e o validador pega defeito de forma que o
Sistema Auditor aceitava calado.** Melhorias colhidas numa fiscalização real de agosto:

- A `/aft-auditoria-geral` agora fixa a frase de abertura do bloco de irregularidade —
  uma fórmula para achado de campo, outra para achado documental, idêntica em todos os
  autos da mesma fonte — e um fechamento padronizado de enquadramento. Também passa a
  exigir que cada auto nomeie explicitamente a máquina ou equipamento envolvido (conferido
  na fonte primária, nunca de memória) e a impedir que duas ementas da mesma NR, uma geral
  e uma específica, autuem o mesmo ponto físico da máquina (princípio da especialidade).
  Antes de apresentar, a skill relê a leva inteira lado a lado e corrige divergências.
- Nos autos de AET (`/aft-aet-auditoria`), as evidências saem em parágrafos corridos, sem
  lista numerada — no Sistema Auditor a lista virava um bloco ilegível.
- O `/aft-gera-ai` ganhou avisos duros contra dois erros silenciosos que aconteceram de
  verdade: subtítulo escrito sem acento ("FISCALIZACAO") e o passo do recuo de parágrafo
  esquecido ao regenerar o TXT. E o validador (`validar_txt.py`) agora confere as três
  coisas no arquivo final: subtítulos I/II/III presentes, acentuação correta e recuo
  aplicado — defeitos que o Sistema Auditor importa sem reclamar e só apareciam quando
  você conferia o auto já dentro do sistema.
- Para quem usa Windows: o login do NotebookLM voltou a encontrar o Python certo na
  instalação mais nova do pipx.

---
