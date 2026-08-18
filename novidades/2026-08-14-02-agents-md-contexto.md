## 14/08/2026
<!-- commit: agents-md-contexto -->

**O contexto de cada auditoria passa a ser lido por qualquer assistente, não só pelo
Claude Code.**
Até agora o arquivo que faz o assistente "saber quem é" ao abrir a pasta de uma
fiscalização chamava-se `CLAUDE.md` — nome que só o Claude Code procura. Quem usa o Codex
ou outro assistente abria a pasta e ele não sabia nada da auditoria.

- Esse texto agora mora no **`AGENTS.md`** da pasta da OS: é o nome que Claude Code,
  Codex e os demais assistentes leem como contexto de projeto.
- O `CLAUDE.md` continua existindo ao lado, mas **só como ponteiro**: uma linha
  `@AGENTS.md` que o Claude Code resolve sozinho. Nada é duplicado — uma informação, dois
  nomes. Abaixo dessa linha você pode escrever o que for só do Claude Code.
- **Suas auditorias antigas são migradas com o texto preservado.** O toolkit não troca o
  seu arquivo pelo modelo novo: move o que estava lá, como estava, e guarda uma cópia em
  `CLAUDE.md.bak` na mesma pasta.
- Se uma pasta tiver os dois arquivos com textos diferentes, o toolkit **não escolhe por
  você**: avisa e não mexe em nenhum dos dois.
- **O modelo que cada skill pede também vale fora do Claude Code.** Toda skill declara o
  modelo de que precisa. O Claude Code obedece sozinho; o Codex não sabe trocar de modelo
  por skill (lá o modelo vale para a conversa inteira). Agora ele avisa você, em uma linha,
  quando a skill acionada pedir o modelo mais forte — as que julgam PGR, AET, acidente,
  laudo de NR-12 e manutenção de interdição — e espera você decidir.
