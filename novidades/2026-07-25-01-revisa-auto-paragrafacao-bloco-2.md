## 25/07/2026
<!-- commit: revisa-auto-paragrafacao-bloco-2 -->

**O bloco II dos autos não sai mais como um parágrafo gigante e ilegível no Sistema
Auditor.** Você notou isso num auto de PGR: o "II - IRREGULARIDADE" inteiro (a
identificação de perigos, as páginas citadas, o dano coletivo, a conclusão) tinha saído
como uma única linha corrida, sem nenhuma quebra. A causa: a skill que redige o texto
(no caso, a `/PGR-analise`) escrevia o bloco II como um parágrafo só, e ninguém depois
dividia isso.

Agora a `/revisa-auto` (o revisor de qualidade que já roda sozinho antes de todo
`/gera-ai`) ganhou um passo novo: ela olha o bloco II de cada auto e, se estiver tudo
em um parágrafo só, divide em vários — um para o enquadramento normativo, um por grupo
de constatações relacionadas, um para o dano coletivo, um para a conclusão. Só insere
linhas em branco onde o texto já muda de assunto; não muda, resume nem acrescenta uma
palavra sequer. Essas linhas em branco são exatamente o que já virava quebra de linha
de verdade no TXT do Sistema Auditor (com o recuo de 8 espaços que já corrigimos na
atualização anterior) - só que antes não existiam para o bloco II ser dividido.

Também reforcei as skills que mais geram bloco II em parágrafo único (`/PGR-analise`,
`/auditoria-geral`, `/aet-auditoria`) para já escreverem em parágrafos separados na
origem — a `/revisa-auto` continua sendo a rede de segurança para qualquer auto que
escapar disso.

---
