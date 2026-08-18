## 05/08/2026
<!-- commit: instalacao-windows-tres-mensagens -->

**Instalação no Windows: o Passo 3 virou três mensagens, e agora funciona.**
Colegas estavam esbarrando numa recusa do próprio Claude na hora de instalar as
skills. O motivo não era o toolkit: o passo antigo mandava baixar o repositório
**direto** para `~/.claude/skills`, que é a pasta de onde o Claude lê as
instruções dele — e ele é treinado (com razão) para desconfiar de conteúdo da
internet indo direto para lá.

- **Baixar → conferir → instalar.** O `COMO-INSTALAR.md` agora pede três
  mensagens em vez de uma: a primeira instala Git/Python/notebooklm, a segunda
  baixa o toolkit para `Documentos\aft-toolkit` e manda o Claude **ler e
  explicar** o que veio, e só a terceira move para a pasta de skills. Quando
  chega a hora de instalar, ele já conferiu o que está instalando — e a recusa
  não acontece.
- **Saiu o parágrafo de "contexto de confiança".** O texto que afirmava que os
  repositórios eram oficiais e estavam autorizados fazia o efeito contrário:
  insistir que algo é confiável é justamente um sinal de alerta para o Claude.
- **Se ele recusar mesmo assim, não discuta.** Argumentar deixa ele mais
  desconfiado, não menos. O guia explica isso e traz o Plano B (os mesmos
  comandos, colados no PowerShell) já corrigido.
- **`notebooklm skill install` agora é opcional.** As skills do toolkit usam o
  comando de terminal `notebooklm`, não a skill `/notebooklm` — um passo a menos
  na instalação.

Quem já está instalado não precisa fazer nada: a mudança é só no guia de
instalação, para repassar a colegas.

---
