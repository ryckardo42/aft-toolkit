## 27/08/2026
<!-- commit: analise-preliminar-skill -->

**Nova habilidade: `/aft-analise-preliminar` — triagem da resposta do empregador ao
DET.** Depois que a `/aft-det-baixar` traz os arquivos de uma notificação, esta skill
confere item por item o que a empresa entregou, **separado por dia de entrega**, e
classifica cada item: ATENDIDO, PARCIALMENTE ATENDIDO, IRREGULAR (veio outra coisa no
lugar — por exemplo, a mesma petição de dilação de prazo respondendo cinco itens, que
ela flagra porque detecta documento duplicado), ENTREGUE — MÉRITO PENDENTE (é um PGR,
uma AET, um laudo ou arquivo de ponto: a análise de fundo é da skill dedicada, que
consome muito e **só roda se você mandar**) ou PRECISA AUDITORIA AFT (pasta volumosa ou
formato que exige seus olhos). O resultado fica em `analise-preliminar-<CODIGO>.md` na
pasta da OS, e a constatação entra sozinha na `## Auditoria de documentos` da ficha.

Duas economias importantes: a leitura toda acontece **fora da sua conversa** (nenhum PDF
do empregador entra no seu contexto, então a triagem não come o limite da sessão), e
rodar de novo depois de um download novo **analisa só o dia que chegou** — os dias já
triados ficam como estão. A `/aft-det-baixar` passa a oferecer a triagem ao final de
cada download com arquivos novos.

Sobre privacidade: o inventário roda inteiro na sua máquina, e a leitura dos documentos
passa pelo assistente como em toda skill de análise do toolkit — mas o relatório e o
resumo **nunca ecoam dado pessoal** (CPF, dado de saúde, salário nominal: descreve em
agregado, não transcreve). E você pode deixar itens de fora da triagem ("tria tudo menos
o item 4"): eles saem no relatório como NÃO TRIADO, só com a lista de nomes e tamanhos.

---
