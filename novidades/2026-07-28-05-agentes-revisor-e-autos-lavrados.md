## 28/07/2026
<!-- commit: agentes-revisor-e-autos-lavrados -->

**O toolkit ganhou seus dois primeiros agentes: ajudantes que trabalham numa "sala
separada".** Um agente é como um colega para quem o Claude delega uma tarefa pesada: ele
recebe a missão, trabalha isolado e volta só com o resultado — sem entulhar a sua
conversa com o conteúdo de dezenas de arquivos.

- **Revisor de autos (`aft-revisor-autos`)** — quando o `/aft-revisa-auto` roda (também
  como etapa automática do `/aft-gera-ai`), a revisão 5W1H agora acontece com **olhos
  frescos**: o revisor enxerga só o texto dos autos, sem ver a conversa que os redigiu —
  exatamente como o julgador do auto vai ler. Revisão mais dura, autos mais sólidos.
- **Varredura do Sistema Auditor (`aft-autos-lavrados`)** — o snapshot dos autos
  lavrados (leitura de dezenas de PDFs) agora roda fora da sua conversa; de volta, só o
  relatório. Na varredura de todas as OS, pode rodar **em segundo plano** enquanto você
  continua trabalhando. E qualquer decisão que seja sua (pasta ambígua, CNPJ divergente,
  ementa em duplicidade) volta como pergunta — o agente nunca decide por você.

**O que você precisa fazer: nada.** O `/aft-atualizar` instala os agentes sozinho
(ficam em `~/.claude/agents/`) e eles passam a valer no próximo reinício do app. Se por
algum motivo não estiverem instalados, as skills continuam funcionando do jeito antigo
— nada trava. O `/aft-doctor` agora confere isso também.

---
