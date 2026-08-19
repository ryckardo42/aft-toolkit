## 04/08/2026
<!-- commit: skill-relatorio-acidentes -->

**Nova skill `/aft-relatorio-acidentes`: o histórico de CATs da empresa, em um
comando.** Você informa o CNPJ (ou anexa o CSV do Portal AFT) e sai o Relatório
de Acidentes do Trabalho da fiscalizada: todas as CATs em ordem cronológica,
com lesão, parte do corpo, CID, agente causador, local, duração do tratamento
e óbitos em destaque, mais um resumo estatístico no topo.

- **Dois modos.** Modo A: o CSV `CatsCNPJ_*.csv` exportado do Portal AFT.
  Modo B: a base estadual de CATs (planilhas do eSocial, uma por ano) — no
  primeiro uso a skill pergunta onde está a pasta das planilhas do seu estado
  e grava a escolha no `aft-config.md`; depois basta o CNPJ.
- **Tudo local, nada na nuvem.** As CATs têm nome, CPF e dados de saúde de
  trabalhadores. Quem lê os arquivos e monta o relatório é um script Python na
  sua máquina; no chat aparecem só os números agregados e os caminhos dos
  arquivos — nenhum nome de trabalhador.
- **Dois formatos, na pasta certa.** `Relatorio-Acidentes-<cnpj>.md` e `.docx`
  (padrão visual do toolkit), gravados na subpasta `Acidentes/` da empresa em
  OS ATIVAS. Se já existirem, o script faz backup antes de regravar.
- **Limpeza de dados.** O script conserta sozinho os defeitos de codificação
  típicos dessas bases (acentos virados em `Ã§`/`ø`), descarta CATs
  substituídas por retificação e anota reaberturas e comunicações de óbito.
- **Divisão de trabalho.** Esta skill levanta o histórico; a análise
  aprofundada de um acidente (IN 2/2022) continua com a `/aft-analise-acidente`.
- **Integrada à preparação da ação fiscal.** A `/aft-preparacao-acao-fiscal`
  ganhou a FASE 4.5: quando o CNPJ é conhecido, ela chama a
  `/aft-relatorio-acidentes` e leva o histórico de CATs para o planejamento —
  o `preparacao.md` ganha a seção "Histórico de acidentes (CATs)" com os
  agregados (totais, óbitos, período, principais agentes causadores e partes
  do corpo mais atingidas), e os pontos de atenção da visita passam a apontar
  o setor e o tipo de risco onde a empresa mais se acidenta. O relatório
  completo fica na pasta `Acidentes/` da OS; no chat e no `preparacao.md`
  entram só os números.

---
