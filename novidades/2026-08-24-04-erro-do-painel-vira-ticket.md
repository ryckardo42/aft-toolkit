## 24/08/2026
<!-- commit: erro-do-painel-vira-ticket -->

**Quando o painel falha, ele agora explica em português e grava o ticket
sozinho.** Até aqui, defeito numa ação do painel — marcar uma notificação,
registrar pendência, baixar arquivos do DET, criar o rascunho da notificação —
aparecia na tela como um punhado de jargão de programador (`KeyError: 'ordem'`) e
não gerava ticket nenhum: o toolkit prometia gravar o ticket sozinho e, justamente
no painel, não gravava.

Agora a mensagem diz **o que ele não conseguiu fazer** ("não consegui criar o
rascunho da notificação no DET...") e traz o caminho do ticket já gravado, pronto
para a `/aft-erro` completar antes de você enviar ao mantenedor. O ticket sai com
os dados de fiscalização removidos, como sempre: nome de empresa, CNPJ e o caminho
das suas pastas aparecem como `<EMPRESA>`, `<INSCRICAO>` e `<PASTA AFT>`.

Um mesmo defeito, na mesma ação, gera **um** ticket por vez que o painel está no
ar — clicar de novo no botão que falhou não enche a sua pasta de tickets iguais.

---
