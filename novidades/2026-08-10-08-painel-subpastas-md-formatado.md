## 10/08/2026
<!-- commit: painel-subpastas-md-formatado -->

**O painel agora enxerga os relatórios guardados em subpastas — e a leitura
deles no navegador ficou mais bem formatada.**

- **Relatórios de subpasta entram no painel.** Até agora, o cartão "Relatórios
  da OS" só listava os `.md` da raiz da pasta da empresa. Os que as skills
  salvam em subpasta ficavam invisíveis: os autos da interdição
  (`interdicao-embargo/autos.md`, da `/aft-rt-rgi`), os relatórios de acidentes
  e doenças (`Acidentes/`, da `/aft-relatorio-acidentes`) e o texto-fonte do
  relatório final (`Relatórios de Fiscalização/`, da `/aft-relatorio`). Agora
  todos aparecem no painel, identificados pelo caminho ("interdicao-embargo/
  autos.md"), clicáveis e legíveis no navegador como os demais. Nada muda de
  lugar no disco: o painel apenas passou a enxergar onde os arquivos já estavam.
- **Leitura mais fiel ao documento.** O visualizador de relatórios do painel
  passou a entender listas dentro de listas (antes achatava tudo num nível só),
  links clicáveis, citações e blocos de código — além do que já fazia: títulos,
  negrito, tabelas e as caixinhas de tarefa. Documento com aparência de
  documento, inclusive para imprimir.
- **Aviso semanal de pendências (novo, opcional).** Toda segunda-feira de manhã
  o seu computador pode te avisar, com uma notificação nativa, quantas
  pendências estão em aberto nas suas auditorias — ex.: "17 pendências em 8
  auditorias". De propósito, a notificação mostra **só os números** (ela pode
  aparecer com a tela bloqueada); a lista completa fica na nova seção
  **"Pendências por auditoria"** do painel, logo abaixo dos próximos
  vencimentos. Sem pendência em aberto, nada é exibido. Roda inteiramente fora
  do Claude Code (agendamento do próprio sistema, zero tokens) e o
  `/aft-atualizar` vai te oferecer a ativação uma única vez.
- **Cards em ordem de cadastro.** Os cards das auditorias agora aparecem do
  cadastro mais recente para o mais antigo — pela data em que a OS entrou no
  painel (criação da ficha `memory.md`), o que vale para todas as auditorias,
  mesmo as sem data de início registrada. Antes a ordem era por urgência de
  DET (vencidos primeiro) — os prazos continuam cobertos pelos selos coloridos
  de cada card e pela agenda "Próximos vencimentos" no rodapé.
- **O painel passa a se atualizar de verdade.** Descobrimos que o servidor do
  painel continuava rodando a versão antiga mesmo depois de uma atualização —
  ele só carrega o código novo quando reinicia (o que antes só acontecia no
  próximo login). O `/aft-atualizar` agora reinicia o servidor sozinho sempre
  que baixa novidade, então as melhorias passam a valer na hora.
---
