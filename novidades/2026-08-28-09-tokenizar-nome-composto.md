## 28/08/2026
<!-- commit: tokenizar-substituir-multi-palavra -->

**Conserto na pseudonimizacao: nome de trabalhador com mais de uma palavra podia deixar
de ser trocado pelo token, sem aviso nenhum.** A rotina que torna a busca insensivel a
maiuscula/minuscula acabava corrompendo, sem querer, o proprio espaco em branco que
separa as palavras do nome. O efeito era a substituicao principal falhar em silencio,
caindo num atalho de reserva que so reconhece a forma sem acento: a ocorrencia acentuada
do nome real continuava no arquivo. Quem rodasse a troca confiando no numero de
"substituicoes" mostrado na tela podia achar que o nome tinha saido do documento quando
na verdade ele seguia la. Corrigido, com casos de teste (nome ficticio) cobrindo nome de
uma palavra, de varias palavras, com acento, em maiuscula e com espaco duplo.

---
