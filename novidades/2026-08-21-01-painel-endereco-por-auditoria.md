## 21/08/2026
<!-- commit: painel-endereco-por-auditoria -->

**Cada auditoria ganhou endereço próprio: dá para abrir uma por aba.** Até agora o painel
inteiro morava num endereço só — `127.0.0.1:8347` era a mesma coisa com a auditoria aberta ou
fechada, e por isso não havia como abrir duas empresas ao mesmo tempo. Agora abrir uma auditoria
muda o endereço do navegador para `127.0.0.1:8347/#os=NOME DA EMPRESA...`, e os cards passaram a
ser links de verdade. Na prática: **⌘+clique** (ou o clique do meio do mouse) abre a auditoria
numa **aba nova**, o botão direito oferece "abrir em nova aba", e o endereço de uma auditoria
pode ser copiado, favoritado ou colado em qualquer aba — abre direto naquela empresa. O **botão
voltar do navegador** também passou a funcionar: volta para a grade em vez de te tirar do painel.

Na barra de cima, ao lado de "ordenar por", entrou **"abrir auditoria: nesta tela · em nova aba"**.
O padrão continua sendo *nesta tela*, exatamente como era; escolhendo *em nova aba*, o clique
simples já abre a aba separada. A escolha fica guardada no navegador.

Nada mudou no que você já fazia: registrar uma pendência, resolver, editar constatação — tudo
continua recarregando e voltando para a mesma auditoria, agora porque o endereço diz onde você
estava (uma gambiarra a menos por dentro).
