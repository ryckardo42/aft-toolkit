## 28/08/2026
<!-- commit: ementas-arquivo-proprio -->

**As ementas saíram do memory.md e ganharam arquivo próprio — que agora responde o
Relatório de Inspeção.** A lista de ementas da Ordem de Serviço morava dentro da ficha
`memory.md`. Numa auditoria real ela chegou a quase um quarto do arquivo, e o memory.md
é lido no começo de toda conversa da empresa — para uma lista que só interessa em três
momentos: quando você prepara a ação fiscal, quando enquadra uma irregularidade e quando
encerra. Agora ela mora num arquivo à parte, o **`ementas.md`**, na mesma pasta da
auditoria. Na ficha ficou só uma linha dizendo onde ele está.

Mas o ganho maior não é o tamanho: é o que o arquivo passou a fazer. Ele virou a **folha
de resposta do item 2.5 do Relatório de Inspeção** — aquela tela do SFIT-WEB onde cada
ementa precisa de uma *situação encontrada* (Regular, Irregular, Não aplicável, Não
fiscalizada) e, quando irregular, das *ações aplicadas* (Autuação, Notificação,
Interdição, Embargo, Regularizada, Termo de Compromisso e as demais). A folha tem três
partes, do mesmo jeito que a tela: as ementas da OS (as que aparecem com asterisco), as
que chegaram sozinhas porque você lavrou um auto, e as que você fiscalizou por fora e
digita no campo "Informe as ementas fiscalizadas que não constam na OS".

**O toolkit preenche o que já sabe; o juízo continua sendo seu.** Auto transmitido,
termo de interdição ou embargo e notificação lavrada já estão registrados na pasta da
auditoria — então o assistente vai buscar lá e propõe o preenchimento, sempre mostrando
antes de gravar e sempre anotando de onde tirou (o número do AI, o arquivo do relatório
técnico, o arquivo da notificação). O que é decisão sua — dizer que uma ementa está
regular, que não se aplica, que não foi fiscalizada, ou que a empresa regularizou — nunca
é preenchido sozinho: o assistente lista o que falta e pergunta.

No encerramento, o `/aft-relatorio` fecha a folha com você e imprime a lista na ordem da
tela, para digitar conferindo linha a linha. E ganhamos quatro conferências novas, todas
de erro que iria parar em documento oficial: ementa autuada marcada como regular, "não
aplicável" e "não fiscalizada" sem a justificativa que o SFIT exige, "regularizada" sem
nenhuma comprovação registrada, e autuação numa auditoria marcada como de dupla visita.

Você não precisa fazer nada: nas auditorias já abertas, a mudança de lugar acontece
sozinha na próxima vez que rodar o `/aft-organiza-os` (com cópia de segurança antes), e
tudo continua funcionando enquanto ela não acontece — a preparação e o dossiê impresso
leem os dois formatos.

---
