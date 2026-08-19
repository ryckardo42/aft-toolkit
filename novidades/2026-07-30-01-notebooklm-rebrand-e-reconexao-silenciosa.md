## 30/07/2026
<!-- commit: notebooklm-rebrand-e-reconexao-silenciosa -->

**A conexão com o NotebookLM ficou imune ao rebrand do Google — e se renova sozinha,
sem janela.** Em 16/07/2026 o Google rebatizou o NotebookLM como "Gemini Notebook" e
mudou o endereço da página. Resultado: em muitas máquinas o login por janela passou a
falhar com "Login not detected within 5 minutes" **mesmo com o login feito
corretamente** — não era erro seu, nem do seu computador. O que muda:

- **Instalação corrigida.** O toolkit passa a instalar o comando `notebooklm` da
  versão que já entende o endereço novo (por enquanto, direto do projeto no GitHub;
  quando sair a versão oficial corrigida, o `/aft-atualizar` volta ao canal normal
  sozinho).
- **Reconexão sem janela.** Quando a sessão do NotebookLM expira (isso é normal e
  vai continuar acontecendo), o toolkit agora renova pelo login que ficou salvo da
  primeira vez — **sem abrir janela e sem você fazer nada**. Só quando esse login
  salvo também vence é que a janela do Google aparece de novo.
- **O `/aft-doctor` avisa.** Se a sua máquina estiver com a versão antiga do
  `notebooklm` (a que quebrou com o rebrand) ou com a reconexão automática no modo
  antigo (que abria janela), o doctor aponta e diz o que pedir ao Claude.
- **Ticket de correção mais preciso.** Corrigido um detalhe que fazia o campo
  "Skill" do ticket sair como um caminho estranho (`C:/Program Files/Git/...`) em
  vez do nome da skill.
