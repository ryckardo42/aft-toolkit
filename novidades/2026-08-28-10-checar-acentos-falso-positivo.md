## 28/08/2026
<!-- commit: checar-acentos-caminho-frontmatter -->

**O conferidor de acentuacao parou de reprovar documento correto.** A ferramenta que
confere se o texto foi escrito com acentuacao completa vinha acusando "erro" em duas
coisas que nao sao prosa: o caminho de um arquivo (`_scripts/montar_rt.py`, `memory.md`)
e o cabecalho de configuracao no topo das notificacoes, cujos valores sao escritos sem
acento de proposito porque o DET os exige assim. Numa notificacao real do acervo isso
dava nove reclamacoes, nenhuma delas erro de grafia de verdade. Guarda que reprova o
documento certo ensina a ignorar a guarda, e ai ela deixa de proteger de tudo. Corrigido:
os dois casos passam a ser ignorados, e o erro de acentuacao de verdade continua sendo
apontado. De quebra, razao social com "E" no meio ("MOVEIS E DECORACOES LTDA") tambem
deixou de ser confundida com prosa sem acento.

---
