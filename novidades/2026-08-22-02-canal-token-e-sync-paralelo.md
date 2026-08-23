## 22/08/2026
<!-- commit: canal-token-e-sync-paralelo -->

**A sincronização com o DET ficou quase quatro vezes mais rápida, e agora tem
duas portas de entrada.** Atualizar as fichas com o que está no DET levava cerca
de 1 minuto e 45 segundos, porque cada auditoria era consultada depois da outra,
em fila. Agora várias são consultadas ao mesmo tempo: o mesmo trabalho terminou
em **28 segundos** no teste real. Você não precisa fazer nada de diferente — a
melhoria vale para qualquer forma de disparar a sincronização.

E as formas passaram a ser duas, com ordem de preferência clara:

- **Via principal — o navegador do próprio assistente.** Se o seu assistente tem
  navegador (é o caso do Claude Code no aplicativo), basta você estar logado no
  DET nele: o assistente pega o crachá de sessão e entrega ao painel na hora.
  Não depende de instalar nada nem de aprovação de loja.
- **Via alternativa — a extensão Sync DET no Chrome.** Continua funcionando
  igual, com o botão flutuante **Sincronizar** no site do DET. É o caminho de
  quem usa um assistente sem navegador.

Nada muda quanto à segurança: o crachá vale cerca de 30 minutos, vive só na
memória do painel, **nunca é gravado em disco** e nunca aparece na conversa. O
toolkit não guarda a sua senha do DET e não faz login por você — quem entra é
sempre você.

---
