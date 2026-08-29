# AFT Toolkit

## Sumiram as suas habilidades? Elas voltam em segundos

Abra o aplicativo Claude, comece uma conversa e digite:

```
/aft-atualizar
```

(ou simplesmente peça "atualize o AFT Toolkit"). Ele repõe tudo na hora, a partir da
cópia que já está no seu computador — sem baixar nada, sem internet, e sem tocar nas
habilidades que você mesmo criou.

**Não foi um problema seu, e nada se perdeu.** Este repositório mudou de função, e a sua
instalação antiga ainda não sabia disso. O que vem abaixo explica o resto.

---

## O que mudou

Até aqui, este repositório **era** o AFT Toolkit: você clonava com `git clone` e o
conteúdo virava a sua pasta de skills (`~/.claude/skills`). Isso acabou.

**O toolkit passou a ser distribuído pelo portal `notebooks-aft`**, onde você já tem
cadastro verificado (o mesmo CIF conferido contra a lista do DOU que libera o
NotebookLM). Em vez de acompanhar commits soltos no GitHub, você agora recebe
**versões** — com changelog em português, do seu período — e decide quando instalar.

### Por quê

O roteiro operacional de uma fiscalização (como se audita um PGR, uma AET, um laudo de
NR-12) estava público e clonável por qualquer um — inclusive por quem é fiscalizado. E
não havia canal nenhum para avisar alguém de uma mudança que quebra algo, porque o
mantenedor não sabe quem são os usuários de um repositório público. O portal resolve as
duas coisas: cadastro conferido e, pela primeira vez, um jeito de falar com você.

## O passo seguinte: pedir acesso ao portal

Depois de repor as suas habilidades, o `/aft-atualizar` explica na tela o próximo passo —
pedir acesso com a sua conta Google, em

**<https://notebooks-aft.vercel.app/aft-toolkit>**

Você recebe um código de acesso por e-mail, uma única vez. Cole o código quando o
Claude pedir — ele guarda o código fora da pasta de skills, nunca mostra o valor na tela
e nunca mais pergunta de novo. Feito isso, `/aft-atualizar` passa a mostrar a versão
disponível e o que mudou, e só instala com o seu sim.

**Se `/aft-atualizar` não responder nada disso** (ficou preso, ou parece não ter mudado):
feche o aplicativo Claude pela bandeja do sistema e abra de novo, depois repita o
comando — a sua instalação precisa buscar este repositório uma vez antes de reconhecer
o comando novo.

### Nunca usou o AFT Toolkit?

Você não precisa clonar este repositório. Peça acesso direto no portal, no mesmo
endereço acima — o cadastro te leva ao roteiro de instalação atualizado.

## Dúvidas ou problemas

Fale com o mantenedor pelo portal: **<https://notebooks-aft.vercel.app/aft-toolkit>**
(Ricardo de Oliveira, AFT — SRTE/GO). Este repositório vai sair do ar quando a migração
terminar; o portal continua.
