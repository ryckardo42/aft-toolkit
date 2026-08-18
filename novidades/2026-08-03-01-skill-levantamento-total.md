## 03/08/2026 (tarde)
<!-- commit: skill-levantamento-total -->

**Nova skill `/aft-levantamento-total`: o Relatório Técnico que levanta a
interdição ou o embargo.** Até agora o toolkit cobria a origem da medida
(`/aft-rt-rgi`), o julgamento do laudo (`/aft-auditoria-AR-NR12`) e a negativa
da suspensão (`/aft-rt-manutencao`) — faltava o desfecho feliz: a empresa
cumpriu tudo, o risco grave e iminente foi afastado e o auditor decide
levantar. A nova skill redige esse RT.

- **Documento breve, de propósito.** O levantamento não reabre o mérito: são 7
  seções curtas que registram as datas (requerimento, análise dos documentos no
  SEI e, se houve, a nova inspeção física), o número do processo SEI, o objeto
  liberado e a conclusão pelo levantamento total. Se o auditor quiser destacar
  algo, o registro entra no item 2 ou na conclusão.
- **Mesmo visual do RT original.** O `.docx` sai com o cabeçalho institucional,
  a fonte e os espaçamentos do template do `/aft-rt-rgi` — mas sem o bloco de
  instruções de pedido de suspensão no rodapé, que deixa de fazer sentido
  quando a medida se encerra.
- **Quem decide é sempre o auditor.** A skill só redige quando o levantamento
  total já foi decidido; se a intenção for negar, ela aponta para a
  `/aft-rt-manutencao`, e se o laudo ainda precisa ser julgado, para a
  `/aft-auditoria-AR-NR12`.

---
