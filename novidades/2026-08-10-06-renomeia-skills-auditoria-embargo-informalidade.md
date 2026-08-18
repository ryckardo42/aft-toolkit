## 10/08/2026 (3)
<!-- commit: renomeia-skills-auditoria-embargo-informalidade -->

**Cinco skills mudaram de nome, para dizer o que realmente fazem.** Nada mudou
por dentro: o texto, as ementas e os documentos gerados são exatamente os mesmos.
Só o comando é outro.

| Antes | Agora | Por quê |
|---|---|---|
| `/aft-nova-os` | `/aft-nova-auditoria` | Uma OS pode virar **vários RIs**: num mesmo estabelecimento costumam conviver dois, três ou mais CNPJs, e você abre uma auditoria (um RI) para cada um. O que a skill cadastra é a auditoria, não a OS |
| `/aft-rt-rgi` | `/aft-embargo-interdicao` | "RGI" só diz alguma coisa para quem já conhece a sigla |
| `/aft-rt-manutencao` | `/aft-embargo-interdicao-manutencao` | Agora as três skills de interdição/embargo aparecem juntas quando você digita `/aft-embargo` |
| `/aft-levantamento-total` | `/aft-embargo-interdicao-levantamento` | idem |
| `/aft-registro` | `/aft-informalidade` | É a skill da informalidade: falta de registro (art. 41), CTPS (art. 29) e exame admissional |

**O nome antigo deixa de funcionar.** Se digitar `/aft-rt-rgi`, não vai achar — é
`/aft-embargo-interdicao` agora. Pedir em português continua funcionando igual
("cadastra essa auditoria", "monta o RT de interdição", "trabalhador sem registro"):
as skills continuam sendo encontradas pelo que você descreve.

Seu **perfil de auditor** (o `CLAUDE.md`) é atualizado sozinho nesta atualização,
com os nomes novos — o que você escreveu por fora dos marcadores fica intacto.
Suas skills próprias (`minha-*`) não foram tocadas.

> Detalhe técnico: como na renomeação de 26/07/2026, esta atualização mexe em muitos
> arquivos de uma vez. Lista grande de mudanças é esperado.

---
