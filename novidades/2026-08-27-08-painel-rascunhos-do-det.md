## 27/08/2026
<!-- commit: det-sync-rascunhos -->

**O painel agora mostra as notificações que você deixou como rascunho no DET.** Uma
notificação montada e não lavrada é fácil de esquecer: ela não tem prazo, não aparece em
lugar nenhum e some da memória — o AFT descobria semanas depois que havia uma notificação
pronta parada no site. A sincronização do DET passou a trazer também essas notificações
em elaboração (antes ela descartava tudo o que ainda não tinha sido lavrado, embora o
próprio DET as devolvesse), e cada uma vira uma linha na ficha e um item no cartão de
Notificações DET, em cor de aviso: "RASCUNHO no DET · 7 itens · salvo em 26/08/2026 ·
AINDA NÃO LAVRADO".

O rascunho aparece, mas não se confunde com notificação de verdade: não conta no total de
DET da auditoria, não corre prazo, não colore o cartão, não vai para a agenda e não pode
ser marcado como respondido nem ter arquivos baixados — porque nada disso existe antes da
lavratura. No dia em que você lavrar no site, a sincronização seguinte troca a linha pela
data de lavratura e o aviso de rascunho some sozinho.

Também foi corrigido, na sincronização do DET, no servidor do painel e no leitor de
contexto das OS, o mesmo defeito de leitura da ficha que já havia sido corrigido no
painel: um campo deixado em branco no cabeçalho técnico fazia o programa ler a linha
seguinte como se fosse o valor dele. O caso mais sério era o do campo do RI: em branco,
ele parecia preenchido, e a sincronização nunca gravava o RI da auditoria.

---
