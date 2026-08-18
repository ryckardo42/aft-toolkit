## 26/07/2026 (2)
<!-- commit: prefixo-aft-em-todas-as-skills -->

**Agora TODAS as skills do toolkit começam com `aft-`.** Antes, os nomes eram um
sortimento: algumas já tinham o prefixo (`/aft-setup`, `/aft-doctor`), a maioria não
(`/nova-os`, `/gera-ai`, `/painel`). Isso fazia com que, ao digitar `/` no Claude Code,
as skills do toolkit ficassem espalhadas no meio de tudo que você tem instalado — sem
como saber, olhando, o que era do AFT Toolkit e o que era outra coisa.

A partir desta atualização, **basta digitar `/aft` para ver todas as suas ferramentas de
fiscalização juntas, em bloco**. `/NR12` virou `/aft-NR12`, `/gera-ai` virou
`/aft-gera-ai`, `/painel` virou `/aft-painel`, e assim por diante. As quatro que já
tinham o prefixo (`/aft-setup`, `/aft-doctor`, `/aft-atualizar`, `/aft-rt-rgi`) não
mudaram.

**O que você precisa fazer: nada.** A atualização renomeia tudo sozinha e o seu perfil
(`CLAUDE.md`) é re-sincronizado no mesmo `/aft-atualizar`. Só há uma consequência
prática: **o nome antigo deixa de funcionar**. Se você digitar `/gera-ai`, não vai achar
— é `/aft-gera-ai` agora. Pedir em português continua funcionando igual ("empacota os
autos", "monta o painel", "qual a ementa para máquina sem proteção") — as skills
continuam sendo encontradas pelo que você descreve, não só pelo comando.

Suas skills próprias (as que começam com `minha-`) **não foram tocadas** — continuam com
o nome que você deu.

Tabela de-para, para consulta:

| Antes | Agora | Antes | Agora |
|---|---|---|---|
| `/nova-os` | `/aft-nova-os` | `/jornada-analise` | `/aft-jornada-analise` |
| `/organiza-os` | `/aft-organiza-os` | `/jornada-atestado` | `/aft-jornada-atestado` |
| `/painel` | `/aft-painel` | `/jornada-auto-afd-aej` | `/aft-jornada-auto-afd-aej` |
| `/agenda-det` | `/aft-agenda-det` | `/jornada-valida-afd-aej` | `/aft-jornada-valida-afd-aej` |
| `/sessoes-os` | `/aft-sessoes-os` | `/registro` | `/aft-registro` |
| `/nova-skill` | `/aft-nova-skill` | `/det-630` | `/aft-det-630` |
| `/notebooklm-login` | `/aft-notebooklm-login` | `/tn-nco` | `/aft-tn-nco` |
| `/preparacao-acao-fiscal` | `/aft-preparacao-acao-fiscal` | `/NAD` | `/aft-NAD` |
| `/inspecao-fisica` | `/aft-inspecao-fisica` | `/consulta` | `/aft-consulta` |
| `/auditoria-geral` | `/aft-auditoria-geral` | `/PGR-analise` | `/aft-PGR-analise` |
| `/gera-ai` | `/aft-gera-ai` | `/aet-auditoria` | `/aft-aet-auditoria` |
| `/revisa-auto` | `/aft-revisa-auto` | `/analise-acidente` | `/aft-analise-acidente` |
| `/autos-lavrados` | `/aft-autos-lavrados` | `/auditoria-AR-NR12` | `/aft-auditoria-AR-NR12` |
| `/sfitweb-rel` | `/aft-sfitweb-rel` | `/rt-manutencao` | `/aft-rt-manutencao` |
| `/modelo-docx` | `/aft-modelo-docx` | `/NR01` `/NR12` `/NR18` | `/aft-NR01` `/aft-NR12` `/aft-NR18` |
| `/cnae-grau-risco-nr04` | `/aft-cnae-grau-risco-nr04` | `/dimensionamento-sesmt-nr04` | `/aft-dimensionamento-sesmt-nr04` |
| `/cipa-nr05-dimensionamento` | `/aft-cipa-nr05-dimensionamento` | | |

> Detalhe técnico, para quem tiver curiosidade: esta atualização mexe em muitos arquivos
> de uma vez (é uma renomeação em massa). Se o `/aft-atualizar` mostrar uma lista grande
> de mudanças, é isso — e é esperado.

---
