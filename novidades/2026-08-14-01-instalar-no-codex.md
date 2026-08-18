## 14/08/2026
<!-- commit: instalar-no-codex -->

**O toolkit agora tem instalação para quem usa o Codex — e para quem quer usar os dois
assistentes ao mesmo tempo.**
As skills e os scripts sempre funcionaram no Codex; o que faltava era o roteiro. Ele está
no `COMO-INSTALAR.md`, na seção "Usando o toolkit no Codex", com dois caminhos:

- **Já uso o Claude e quero o Codex também:** dois atalhos e pronto — mesma pasta de
  skills, mesmas fiscalizações, nada duplicado. Você pede ao assistente e ele cria.
- **Vou começar do zero no Codex:** a mesma instalação de sempre, com três trocas
  (instalar o Codex no lugar do Claude, uma mensagem diferente no Passo 3, e avisar ao
  `/aft-setup` que você está no Codex).

O `/aft-setup` e o `/aft-atualizar` passaram a reconhecer em qual assistente estão: no
Codex eles criam os atalhos e pulam sozinhos as quatro coisas que só existem no app do
Claude (agentes, lista de bloqueios do `settings.json`, vigia de sessões e gancho do
diário). Nenhuma skill depende delas — a tabela "O que muda no dia a dia", no
`COMO-INSTALAR.md`, diz exatamente o que se ganha e o que se perde de cada lado.

O `/aft-doctor` também aprendeu a diferença: se você usa o Codex, ele confere os dois
atalhos e para de cobrar essas três coisas que não existem lá — em vez de três avisos
vermelhos sem nada a fazer. Quem usa os dois assistentes continua vendo os avisos, porque
para esse caso eles são pendência de verdade.
