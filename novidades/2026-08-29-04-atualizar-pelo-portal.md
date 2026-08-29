## 29/08/2026
<!-- commit: atualizar-orquestra-script -->

**A atualização do toolkit passou a mostrar uma versão e o que mudou, antes de instalar qualquer coisa.** Até agora, quem digitava `/aft-atualizar` recebia uma parede de mensagens técnicas de dezenas de mudanças e não tinha como saber qual versão estava rodando. Agora o comando pergunta ao portal o que existe de novo, mostra o **número da versão** e o **changelog do seu período**, escrito para o auditor, e só instala depois do seu sim. Se não houver novidade, ele responde numa linha e não baixa nada.

Quem instala fica sabendo o essencial: a versão anterior é guardada numa pasta de backup ao lado, o conteúdo que está chegando é conferido e varrido antes de qualquer arquivo ser escrito, e as suas skills próprias — as `minha-*` e também as que você criou sem prefixo nenhum — não são tocadas.

A primeira vez pede um **código de acesso**, que chega uma única vez no e-mail de liberação do portal (<https://notebooks-aft.vercel.app/aft-toolkit>, com a sua conta Google). É só me passar o código que eu guardo; ele fica fora da pasta de skills, não aparece na tela e nunca entra num relato de erro. Depois disso, nunca mais incomoda.

**Se o seu toolkit for de antes desta mudança**, o `/aft-atualizar` reconhece a situação e explica em português o que aconteceu, conduzindo você ao cadastro no portal — sem erro técnico na cara e sem nada quebrado: o que já está instalado continua funcionando enquanto isso.

---
