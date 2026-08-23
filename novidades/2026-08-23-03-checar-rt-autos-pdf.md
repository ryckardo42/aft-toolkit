## 23/08/2026
<!-- commit: checar-rt-autos-pdf -->

**Interdição: a conferência entre o Relatório Técnico e os autos agora aceita o RT em
PDF.** Quando o Termo de Interdição já está lavrado e o que falta são os autos, o
relatório que o AFT tem em mãos é o PDF impresso, não o Word que o toolkit gerou. Nessa
situação a conferência automática (a que avisa quando o RT e os autos não batem) quebrava
com erro de programa e abria ticket, e a checagem simplesmente não acontecia — justo no
caso mais comum. Agora ela lê o RT tanto em Word quanto em PDF, nos dois formatos de
relatório (por tópico e por objeto), contando uma ementa repetida em vários objetos uma
vez só, como manda a regra de um auto por ementa. Correção do colega Diego.

**Na revisão, um segundo defeito foi corrigido antes de ir para a sua máquina.** A
primeira versão procurava no PDF um título escrito "IRREGULARIDADES", mas o relatório
escreve "4. IRREGULARIDADE(S):" — com os parênteses e com o número da seção. O resultado
seria uma conferência que nunca encontrava nada e avisava "não encontrei o bloco de
irregularidades" em todo RT de verdade: sem quebrar, mas sem conferir. Agora os títulos
são reconhecidos como aparecem no documento, e as ementas são localizadas pelo próprio
código (formato 000000-0), sem depender do marcador de lista que cada impressora de PDF
desenha de um jeito. Testado com relatório fictício nos dois formatos e nas duas mídias.

**Limite que vale conhecer:** RT escaneado (foto do papel, sem texto de verdade dentro do
PDF) não dá para conferir — a habilidade avisa. E, no PDF, o relatório precisa citar as
ementas pelo código; se ele citar só itens de NR, a conferência acusa divergência de
contagem para chamar a sua atenção, em vez de dizer que está tudo certo.

---
