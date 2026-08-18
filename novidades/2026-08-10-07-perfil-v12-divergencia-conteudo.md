## 10/08/2026 (2)
<!-- commit: perfil-v12-divergencia-conteudo -->

**O seu perfil de auditor (CLAUDE.md) volta a receber as novidades — mesmo quando
o número da versão não muda.**

- **A regra do relatório entrou no perfil oficial.** A instrução de que todo
  relatório de fiscalização se chama "RELATÓRIO DE AUDITORIA FISCAL DO TRABALHO"
  e leva na capa o **município/UF da sua lotação** (lidos do `aft-config.md`),
  nunca o da empresa fiscalizada, estava só no arquivo da sua máquina — e teria
  sido apagada na próxima atualização do perfil. Agora ela faz parte do perfil
  que o toolkit distribui.
- **A `/aft-nr24-dimensionamento` apareceu na lista de skills do perfil.** A
  skill de banheiros, mictórios, vestiários e bebedouros existia, mas o Claude
  não a via na lista do seu perfil — por causa do problema descrito no item
  abaixo.
- **Correção: perfil "em dia" que não estava em dia.** O toolkit decidia se o seu
  perfil precisava ser atualizado olhando **só o número da versão**. Se uma
  novidade entrasse no perfil sem que o número mudasse, ela nunca chegava à sua
  máquina — silenciosamente. Agora o `/aft-atualizar` e o `/aft-doctor` comparam
  também o **conteúdo**: mesma versão com texto diferente vira "divergente" e é
  ressincronizada sozinha, sempre com backup e sem tocar no que você escreveu
  fora dos marcadores do toolkit.

---
