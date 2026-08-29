## 29/08/2026
<!-- commit: doctor-codigo-acesso -->

**O `/aft-doctor` passou a conferir se o código de acesso ao portal está configurado.** Ele é o comando que responde "está tudo certo na minha instalação?", e faltava justamente o item que decide se você continua recebendo atualização. Agora aparece na lista: configurado, ou o aviso com o passo para pedir o acesso.

Como manda a regra do toolkit, ele confere que o código **existe** e nunca mostra o valor — nem na tela, nem em relato de erro. Em instalação anterior à mudança de distribuição, o item simplesmente não aparece, sem virar alarme falso.

---
