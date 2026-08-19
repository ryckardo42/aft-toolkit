## 19/08/2026
<!-- commit: skills-pessoais-protegidas -->

**Suas skills próprias não podem mais ser apagadas por uma atualização.** Se você
criou skills suas e guardou em `~/.claude/skills` junto com as do toolkit, elas
corriam risco: só o prefixo `minha-` era protegido, e uma skill sua com qualquer
outro nome era, para o git, apenas um arquivo "não rastreado" — o primeiro que a
limpeza remove. Foi o que aconteceu com um AFT nesta data: onze skills pessoais
sumiram numa atualização, sem backup e sem aviso.

Agora a regra é a inversa e não depende de você acertar convenção nenhuma: o
toolkit lista o que é **dele** e trata todo o resto como seu, intocável. Vale para
qualquer nome — `cipa-atas`, `cowork-ingest`, `sisos-sync`, o que for.

Três camadas, para o caso de uma falhar:

- O toolkit ignora, no git, tudo que não é pasta oficial dele. Skill sua nunca é
  removida por limpeza — e também nunca sobe por acidente para o repositório
  público (as suas citam caminhos e rotinas da sua máquina).
- Antes de mexer na pasta das skills, o toolkit tira um retrato das suas e guarda
  em `~/.claude/skills-pessoais-backup/`, fora do alcance da atualização. Ficam os
  5 retratos mais recentes.
- Ao terminar, ele confere se alguma sumiu. Se sumiu, avisa e repõe com um comando.

Quem decide o que é seu é uma lista real do que o toolkit instala, não um palpite
pelo nome: uma skill pessoal chamada `aft-grant` parece oficial e ficaria de fora
se a checagem fosse por prefixo.

Se você quiser conferir agora quais skills o toolkit considera suas, peça ao
Claude: ele roda `skills_pessoais.py --listar` e mostra a lista.

---
