## 23/08/2026
<!-- commit: organiza-os-ordem-servico -->

**O `/aft-organiza-os` aprendeu a ler a Ordem de Serviço e a arrumar os relatórios.**
Ao organizar uma pasta, a skill agora reconhece o PDF da Ordem de Serviço do SFIT,
extrai o número da OS, o vencimento e a tabela inteira de ementas a fiscalizar (código e
descrição literais, nunca resumidos) e grava tudo na ficha da OS — a mesma seção
`## Ementas da OS` que o `/aft-nova-auditoria` cria quando você anexa a OS no cadastro.
Pasta antiga que tem a Ordem de Serviço mas não tem essa seção na ficha passa a ser
detectada e completada automaticamente. E os relatórios de fiscalização (relatório
final, dossiê de autos e anexos, relatórios avulsos) ganharam morada oficial: a subpasta
`Relatórios de Fiscalização/`, a mesma que o `/aft-relatorio` já usava.

---
