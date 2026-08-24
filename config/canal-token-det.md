# Como o painel consegue o token do DET

> Texto canônico do AFT Toolkit. Toda skill que precisa falar com o DET aponta
> para cá — não repita este conteúdo dentro da skill.

O painel local só conversa com o DET usando o **crachá que o próprio site emitiu
para o AFT logado**: um token de sessão que vale cerca de 30 minutos e não se
renova sozinho. O toolkit nunca guarda senha, nunca faz login e nunca grava o
token em disco — ele vive só na memória do painel, e some quando o serviço
reinicia.

Há **duas vias** para o crachá chegar ao painel. Elas fazem exatamente a mesma
coisa; mudam o esforço e o que precisa estar instalado.

## Via 1 (principal) — o navegador do assistente

Vale quando o assistente tem navegador próprio (é o caso do Claude Code no app
de desktop). **É a via preferida**: não depende de extensão aprovada em loja
nenhuma, não exige instalação e a entrega é instantânea.

> **Antes de começar, confira se você tem ferramenta de navegador** (algo como
> `javascript_tool`/`navigate` na sua lista de ferramentas). **Não tendo, vá
> direto para a Via 2** e diga ao AFT, em uma frase, que nesta sessão o token
> vem pelo Sincronizar da extensão. Não anuncie falha nem tente contornar: é
> diferença de ambiente, não defeito. Idem se a execução de JavaScript no
> navegador estiver bloqueada por permissão — uma tentativa, e siga para a Via 2.

1. Abra (ou peça ao AFT que abra) `https://auditor-det.sit.trabalho.gov.br` no
   navegador do assistente e confirme que ele está **logado**. O login é sempre
   do AFT: o assistente não digita senha nem preenche credencial.
2. Leia o token do armazenamento da própria página:
   `sessionStorage.getItem('token')` — é onde o site do DET o guarda (não é
   `localStorage`).
3. Entregue ao painel **pelo terminal**, com o token na entrada padrão e nunca
   como argumento de comando:

   ```bash
   printf '%s' "<token>" | python ~/.claude/skills/_scripts/det_token.py --gravar
   ```

   > **Nunca tente fazer a PÁGINA do DET chamar o painel.** Uma página servida em
   > `https://` não alcança `http://127.0.0.1` — o navegador barra, e nem um
   > `GET /api/ping` passa (política de rede privada). É por isso que a extensão
   > da Via 2 precisa de um *service worker*: aquele contexto não sofre a
   > restrição, a página sofre. Quem tenta esse caminho conclui, errado, que a
   > Via 1 não funciona — **a entrega é feita pelo terminal, e funciona**.

4. Confira quanto tempo resta, quando precisar:

   ```bash
   python ~/.claude/skills/_scripts/det_token.py --status
   ```

## Via 2 (alternativa) — a extensão Sync DET

Vale para quem usa um assistente **sem navegador** (Codex, Antigravity) ou
prefere não depender do assistente. A extensão lê o mesmo token da mesma aba e o
envia sozinha ao painel enquanto o AFT navega no DET; o botão flutuante
**Sincronizar**, no canto inferior direito do site, força o envio na hora.

Peça ao AFT, em uma frase: *abra a aba do DET logado no Chrome e clique em
Sincronizar*. Um envio cobre o lote inteiro pelos ~25 minutos seguintes.

## Quando o token expira

Resposta com `token_expirado: true` (ou `409`) significa que o crachá venceu —
não é erro do toolkit. Refaça a via 1 (ou peça o Sincronizar) e repita a
chamada. Reiniciar o serviço do painel também apaga o token, porque ele só
existe na memória.

## Regras invioláveis

- **Nunca** exiba o token no chat, em log, em mensagem de erro ou em nome de
  arquivo. Ele dá acesso ao DET em nome do AFT.
- **Nunca** passe o token como argumento de linha de comando: ele ficaria no
  histórico do shell e nos logs do sistema. Use sempre a entrada padrão.
- **Nunca** grave o token em arquivo, nem "temporariamente".
- **Nunca** peça a senha do DET ao AFT, e nunca a guarde em lugar nenhum. Quem
  faz login é ele, no navegador dele.
