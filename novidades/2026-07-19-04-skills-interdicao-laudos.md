## 19/07/2026
<!-- commit: skills-interdicao-laudos -->

**Duas skills novas para interdição e laudos de máquina** — `/auditoria-AR-NR12` julga o
laudo de adequação/apreciação de riscos de máquinas (NBR ISO 12100 e NBR 14153) que a
empresa apresenta ao pedir a suspensão de uma interdição ou ao responder notificação, em 6
blocos de verificação, com parecer pronto. E `/rt-manutencao` redige o Relatório Técnico de
MANUTENÇÃO da interdição/embargo (.docx no modelo oficial) quando o pedido de suspensão é
negado. As duas se encadeiam: laudo insuficiente → RT de manutenção.

<!-- commit: painel-interativo-padrao -->

**Painel interativo já vem ligado de fábrica** — antes o toolkit perguntava, na
instalação, se você queria o painel interativo sempre ligado (aquele que deixa marcar DET,
resolver pendência e sincronizar o DET pela extensão do Chrome). Agora ele já vem ligado:
é instalado junto, sobe sozinho quando você liga o computador e roda só na sua máquina
(nada sai para a internet). Quem atualizar e ainda não tiver vai passar a ter também. Se
preferir sem ele, é só pedir para remover.

<!-- commit: relatorio-adhoc-docx -->

**Relatório pedido fora das skills sai em .docx** — se você pedir um documento ou
relatório que nenhuma skill cobre (um resumo, uma minuta avulsa), o Claude agora entrega
o arquivo final em .docx, em vez de só um texto em markdown no chat ou um `.md` solto.
Não muda nada no que as skills já fazem (`/NAD`, `/tn-nco` etc. continuam entregando o
texto pronto para colar no DET, em bloco de texto puro, do jeito que já era).

**Seu perfil de auditor se mantém atualizado sozinho** — o `CLAUDE.md` (o arquivo que diz
ao Claude quem você é e como trabalhar) antes ficava congelado na versão do dia da
instalação. Agora o `/aft-atualizar` o mantém em dia automaticamente quando sai uma
versão nova, atualizando só a parte do toolkit e sem tocar em nada que você tenha escrito
por conta própria no arquivo. Quem instalou faz tempo vai receber, uma única vez, o
convite para adotar o perfil novo (que traz proteções que faltavam nas versões antigas —
como a regra de tratar documento da empresa como dado, nunca como ordem).
