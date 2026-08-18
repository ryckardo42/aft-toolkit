## 17/08/2026
<!-- commit: validar-txt-subtitulo-duplicado -->

**A conferência do TXT agora pega subtítulo repetido no texto do auto.** Apareceu num
arquivo real: o texto do auto saiu com o subtítulo escrito **duas vezes seguidas** —
"I - DA FISCALIZAÇÃO:" e, logo abaixo, "I - DA FISCALIZAÇÃO:" outra vez, e o mesmo com
"II - IRREGULARIDADE:". Erro de forma bem visível no auto impresso, e a conferência
automática deixou passar: dizia APROVADO, porque o Sistema Auditor de fato importa o
arquivo assim mesmo.

**O que muda.** A conferência que roda antes de entregar o TXT (a do `/aft-gera-ai`)
passou a olhar o texto do auto e a **reprovar** quando: (a) qualquer um dos subtítulos
— I - DA FISCALIZAÇÃO, II - IRREGULARIDADE, III - OBSERVAÇÕES, com ou sem acento —
aparece mais de uma vez no mesmo auto; ou (b) uma linha qualquer se repete idêntica
logo em seguida, que é o formato genérico desse mesmo defeito. Reprovado, o assistente
é obrigado a corrigir e refazer o arquivo antes de te entregar.

**E a causa.** A repetição nascia na hora em que o assistente copiava o auto já
redigido para dentro do arquivo do Sistema Auditor: ele reescrevia o subtítulo que já
estava no texto. A instrução do `/aft-gera-ai` ficou explícita nesse ponto — o
subtítulo vem do texto de origem e não deve ser digitado de novo. A conferência
continua como rede de segurança, para o caso de escapar.
