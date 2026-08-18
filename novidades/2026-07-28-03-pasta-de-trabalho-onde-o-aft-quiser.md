## 28/07/2026 (3)
<!-- commit: pasta-de-trabalho-onde-o-aft-quiser -->

**Suas fiscalizações podem morar onde você quiser — e a atualização não desfaz mais
isso.** Até agora a pasta de trabalho era sempre `Documentos\AFT`. Quem precisava dela
em outro lugar (um **HD externo**, uma pasta sincronizada na **nuvem**, um segundo
disco) não tinha como: mesmo mudando à força, as skills continuavam procurando no
caminho antigo. Agora é só pedir — *"quero minhas fiscalizações no HD externo"* — e o
assistente muda tudo de lugar.

- **Ele leva os arquivos junto** e **nunca sobrescreve**: se já houver dados no destino,
  ele para e explica como juntar as duas pastas, em vez de misturar.
- **A escolha é permanente.** Ela fica guardada fora da pasta das skills, então
  **`/aft-atualizar` nunca mais a desfaz** — configure uma vez e esqueça. Era esse o
  risco real: atualizar o toolkit e ver o assistente voltar a procurar no lugar errado.
- **O painel acompanha.** O `/aft-painel` e o painel automático passam a ler a pasta
  nova. Como os dois serviços de fundo guardam o caminho por dentro, o `/aft-doctor`
  agora **avisa se algum deles ficou apontando para a pasta antiga** e reinstala com o
  caminho certo se você pedir.
- **O `/aft-setup` pergunta** onde você quer a pasta na hora da instalação, e o
  `/aft-doctor` sempre mostra onde ela está — dizendo, quando for o caso, que aquele
  lugar foi **escolhido por você** (e não um defeito a consertar).
- **Skills suas já nascem preparadas.** As habilidades que você cria com
  `/aft-nova-skill` (as `minha-*`) passam a procurar a pasta do jeito certo desde o
  primeiro dia. E se você já tinha alguma com o caminho antigo escrito por dentro, o
  `/aft-doctor` avisa — elas são suas, o toolkit nunca as edita sozinho.

**O que você precisa fazer: nada.** Quem está satisfeito com `Documentos\AFT` continua
exatamente como está — nada muda. A mudança só acontece se você pedir.

---
