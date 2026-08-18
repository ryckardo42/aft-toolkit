## 07/08/2026 (4)
<!-- commit: cats-conexao-fantasma -->

**Conexão do histórico de CATs que travava em "já conectado" sem funcionar.**

- **O sintoma:** ao ativar a sincronização de CATs (`/aft-setup` ou `/aft-atualizar`),
  se o login do Google no navegador demorasse um pouco mais que o esperado, o toolkit
  criava a conexão pela metade — sem salvar a autorização de verdade — e depois passava
  a dizer "já conectado" para sempre, sem nunca funcionar. A única saída era apagar a
  conexão manualmente e recomeçar, coisa que o AFT não tem como fazer sozinho.
- **A correção:** a checagem de conexão passou a conferir se a autorização foi mesmo
  salva, não só se existe uma conexão com o nome certo. Encontrando uma conexão pela
  metade, o toolkit agora **apaga e recria sozinho** na próxima tentativa — sem exigir
  nenhuma limpeza manual.

**O que você precisa fazer: nada**, a menos que já tenha passado por esse travamento —
nesse caso, é só pedir para ativar de novo (`/aft-setup`, Passo 2a).

---
