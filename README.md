# AFT Toolkit

## Este repositório mudou de função

Até aqui, este repositório **era** o AFT Toolkit: você clonava com `git clone` e o
conteúdo virava a sua pasta de skills (`~/.claude/skills`). Isso mudou.

**O toolkit passou a ser distribuído pelo portal `notebooks-aft`**, onde você já tem
cadastro verificado (o mesmo CIF conferido contra a lista do DOU que libera o
NotebookLM). Em vez de acompanhar commits soltos no GitHub, você agora recebe
**versões** — com changelog em português, do seu período — e decide quando instalar.

Não foi um problema seu.

**Se as suas habilidades sumirem da pasta, elas voltam em segundos** — leia
"O que fazer agora" logo abaixo. Ao atualizar pelo caminho antigo, o `/aft-atualizar`
que você tinha instalado apaga as habilidades de fiscalização da sua pasta. Nada se
perde: a cópia continua no seu computador e o comando novo repõe tudo, sem internet.

### Por quê

O roteiro operacional de uma fiscalização (como se audita um PGR, uma AET, um laudo de
NR-12) estava público e clonável por qualquer um — inclusive por quem é fiscalizado. E
não havia canal nenhum para avisar alguém de uma mudança que quebra algo, porque o
mantenedor não sabe quem são os usuários de um repositório público. O portal resolve as
duas coisas: cadastro conferido e, pela primeira vez, um jeito de falar com você.

## O que fazer agora

Se você já tem o AFT Toolkit instalado, **não precisa fazer nada por conta própria** —
inclusive se as habilidades tiverem sumido do `/`. Abra o aplicativo Claude, comece uma
conversa e digite:

```
/aft-atualizar
```

(ou simplesmente peça "atualize o AFT Toolkit"). O comando reconhece a sua situação e
resolve na ordem certa: se as habilidades saíram da pasta, ele **repõe todas na hora**, a
partir da cópia que já está no seu computador — sem baixar nada, e sem tocar nas
habilidades que você mesmo criou. Depois disso ele explica, na tela, o próximo passo:
pedir acesso ao portal com a sua conta Google, em

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

Abra uma Issue neste repositório, ou fale com o mantenedor (Ricardo de Oliveira, AFT —
SRTE/GO).
