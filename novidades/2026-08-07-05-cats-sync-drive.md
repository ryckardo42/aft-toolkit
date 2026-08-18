## 07/08/2026
<!-- commit: cats-sync-drive -->

**As planilhas de CAT do seu estado agora podem baixar e se atualizar sozinhas.**

- **Para quem tem cadastro aprovado nos Notebooks**: primeiro ative seu acesso em
  <https://notebooks-aft.vercel.app/aft-toolkit#cats> (digite o Gmail do cadastro e
  clique em "Ativar acesso" — vale na hora). Depois, o `/aft-setup` (Passo 2a)
  conecta a sua conta Google uma única vez — abre o navegador, você escolhe a
  conta e clica em Permitir — e baixa as planilhas de CAT **só da sua UF** direto
  para `Documentos\AFT\CATs`. Nada de procurar pasta no SharePoint.
- **Sempre em dia, sem você lembrar.** A cada `/aft-atualizar`, o toolkit confere
  o espelho e baixa o que for novo ("chegou a planilha de 2027"). Planilha que
  você mesmo colocou na pasta nunca é apagada.
- **A permissão é só de leitura** do seu Drive, usada exclusivamente para copiar a
  pasta de CATs (ferramenta rclone, cliente verificado pelo Google).
- **O caminho manual continua valendo** para quem não tem o Gmail autorizado ou
  prefere não conectar conta: a área do ENIT no SharePoint do MTE segue documentada
  no mesmo Passo 2a.

Vale para a `/aft-relatorio-acidentes` e, por tabela, para a
`/aft-preparacao-acao-fiscal` (histórico de acidentes no dossiê da visita).

---
