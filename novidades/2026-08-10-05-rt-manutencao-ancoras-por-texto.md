## 10/08/2026 (4)
<!-- commit: rt-manutencao-ancoras-por-texto -->

**Correção: a `/aft-embargo-interdicao-manutencao` voltou a gerar o documento —
estava quebrada desde 02/08/2026.**

- **O que acontecia.** Toda tentativa de gerar o Relatório Técnico de Manutenção
  de interdição/embargo parava com uma mensagem técnica ("template com 124
  blocos (esperado 134)") e nenhum `.docx` era criado. Nada de errado na sua
  máquina: era defeito do toolkit. O script contava os parágrafos do modelo
  oficial e ia buscar o cabeçalho, o bloco final e a linha de cidade/data em
  posições fixas dessa contagem; quando o modelo da `/aft-embargo-interdicao`
  ganhou o campo de contexto da inspeção física, em 02/08/2026, as posições
  saíram do lugar e tudo travou.
- **Como ficou.** O script agora acha cada parte **pelo texto** dela no modelo
  (a linha "RELATÓRIO TÉCNICO", a linha do "CNPJ:", o bloco "DO PEDIDO DE
  SUSPENSÃO"), do mesmo jeito que a `/aft-embargo-interdicao-levantamento` já
  fazia. O modelo pode ganhar ou perder parágrafos que o documento continua
  saindo certo.
- **Uma trava a mais, porque o documento tem efeito legal.** Se algum campo do
  modelo não for preenchido (nome do empregador, CNPJ, data, seu nome), o script
  **não grava o arquivo** e avisa — em vez de entregar um relatório com lacuna
  passando despercebida.

---
