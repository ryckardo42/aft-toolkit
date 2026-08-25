## 24/08/2026

<!-- commit: extensao-sync-det-v4 -->

**A extensão do navegador ficou mais simples: agora é só instalar.** A Sync DET
— a extensão que traz as notificações do DET para o painel — foi republicada na
Chrome Web Store na **versão 4.0**, e a instalação deixou de ter configuração
nenhuma.

Antes, depois de instalar, você ainda precisava clicar no ícone da extensão e
marcar uma caixa chamada "Painel local" para ela começar a funcionar. Quem não
marcasse ficava com uma extensão instalada que não fazia nada, sem nenhum aviso
do porquê. Essa caixa existia porque a extensão podia mandar os dados para dois
lugares: o seu computador ou um sistema na nuvem. **O modo nuvem foi removido**
— agora o único destino é o painel na sua máquina, então não havia mais nada a
escolher. A caixa saiu.

São quatro passos, e o último é só conferir que deu certo:

1. abrir a página da extensão na loja;
2. clicar em "Usar no Chrome" e confirmar;
3. conferir em `chrome://extensions` que ela está ativada;
4. entrar no DET e ver se aparece o botão flutuante **Sincronizar**, no canto
   inferior direito da tela.

O passo a passo completo, com o link e o que fazer se o botão não aparecer, está
no `/aft-ajuda` — é só perguntar "como instalo a extensão".

**Duas melhorias que vêm junto**, e que você não precisa fazer nada para ter:

- A extensão passou a **enviar sozinha**, enquanto você navega no DET. O botão
  Sincronizar continua lá, para forçar a atualização de todas as fichas na hora,
  mas no dia a dia não é mais preciso clicar em nada.
- Quando o Chrome atualiza a extensão em segundo plano e você está com o DET
  aberto, a parte dela que vive dentro daquela página fica desligada. Antes isso
  fazia a sincronização parar **em silêncio**. Agora a extensão percebe e avisa
  na própria tela: recarregue a página (F5) e pronto.

Ela continua sendo 100% local: nada é enviado para a internet, e a política de
privacidade agora mora no próprio toolkit
(https://ryckardo42.github.io/aft-toolkit/privacidade.html).

---
