## 20/08/2026
<!-- commit: extrato-ja-existe -->

**PGR, AET e laudo da NR-12 não são mais extraídos duas vezes.** As três skills de análise
de documento longo (`/aft-PGR-analise`, `/aft-aet-auditoria`, `/aft-auditoria-AR-NR12`)
mandam o documento para o agente extrator antes de analisar, justamente para não gastar a
sua conversa lendo cem páginas. Só que elas não conferiam se aquele documento **já tinha
sido extraído antes** — e, no silêncio, mandavam extrair de novo. Quem sentia isso era
quem extraiu o PGR numa etapa anterior (numa triagem de vários documentos entregues pela
empresa, por exemplo) e depois acionou a skill: o mesmo documento ia para o extrator pela
segunda vez, dobrando a parte mais cara do trabalho, sem nenhum aviso na tela. Agora cada
uma das três olha primeiro se o extrato correspondente (`pgr-extrato.md`, `aet-extrato.md`
ou `laudo-extrato.md`) já está na pasta da OS: se estiver, confere se ele cobre o roteiro
esperado e vai direto para a análise. Se o extrato estiver vazio, truncado ou fora do
roteiro, ela refaz a extração e diz a você por quê.

---
