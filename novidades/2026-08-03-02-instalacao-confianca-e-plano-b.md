## 03/08/2026
<!-- commit: instalacao-confianca-e-plano-b -->

**O guia de instalação ficou mais robusto contra um tropeço real: o Claude do
colega pode recusar a instalação por precaução de segurança.** Aconteceu com uma
auditora: o assistente dela travou nos dois últimos passos (baixar o `notebooklm`
e o toolkit dos repositórios no GitHub) por considerar fontes "pessoais" um risco
— excesso de zelo, mas deixou a instalação pela metade. Duas mudanças no
COMO-INSTALAR.md resolvem:

- **A mensagem do Passo 3 agora se apresenta.** O texto que o colega cola no
  Claude passou a abrir dizendo que os dois repositórios são as fontes oficiais
  do toolkit, mantidas por Auditor-Fiscal, e que o dono da máquina autoriza a
  instalação — o contexto de confiança que faltou naquele caso.
- **O Plano B ficou completo.** Antes só ensinava a baixar o toolkit à mão;
  agora traz também os comandos manuais do `notebooklm`, prontos para colar no
  PowerShell — na forma que funciona mesmo quando o `pipx` não entrou no PATH e
  com o extra `cookies` (necessário para o login automático pelo navegador), que
  faltava nas instruções antigas. Serve para rede bloqueada, computador sem
  winget ou assistente que recusou.

---
