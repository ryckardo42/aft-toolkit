## 29/07/2026 (2)
<!-- commit: ticket-de-correcao-quando-o-toolkit-quebra -->

**Quando o toolkit quebrar, ele agora escreve o chamado por você.** Até hoje, um defeito
aparecia na sua tela como um monte de linhas em inglês — e não havia como saber o que
dessa bagunça o mantenedor precisava para corrigir. Agora todo script do toolkit, ao
quebrar, grava sozinho um **ticket de correção**:

```
==================================================================
  O AFT TOOLKIT ENCONTROU UM ERRO E PREPAROU UM TICKET.
  Arquivo: ...\AFT\tickets\ticket-2026-07-29-1432.md
==================================================================
```

- **O que vai no ticket:** o erro exato, a versão do toolkit que você tem instalada, e o
  retrato da máquina — sistema, Python, quais programas existem aí, bibliotecas,
  serviços do painel. É a informação que o mantenedor precisaria pedir por mensagem, uma
  a uma.
- **O que NÃO vai, nunca:** nome de empresa, CNPJ/CPF, e-mail, conteúdo de documento de
  fiscalização. Tudo isso sai trocado por `<EMPRESA>`, `<INSCRICAO>`, `<PASTA AFT>`.
  Dê uma lida antes de enviar mesmo assim — quem decide o que sai da sua máquina é você.
- **Nova skill `/aft-erro`.** Para o que dá errado *sem* quebrar — a skill devolveu texto
  torto, o painel abriu em branco, o documento saiu estranho —, peça "/aft-erro" ou
  simplesmente diga "deu erro": o assistente monta o mesmo ticket com o contexto do que
  você estava fazendo. Ele também serve para completar um ticket que nasceu sozinho.
- Os tickets ficam em `tickets/`, dentro da sua pasta de trabalho. Nada é enviado a lugar
  nenhum: o arquivo fica na sua máquina até você encaminhá-lo.

**O que você precisa fazer: nada.** Se aparecer o aviso, peça ao assistente para
resolver — e mande o arquivo para quem mantém o toolkit.

---
