## 06/08/2026 (3)
<!-- commit: cats-pasta-padrao -->

**As planilhas de CAT agora têm endereço fixo: a pasta `CATs`, dentro da sua pasta
AFT — ao lado de `OS ATIVAS`.**

- **Nada mais a configurar.** O toolkit procura sozinho em `Documentos\AFT\CATs`.
  Antes, o caminho ficava gravado no `aft-config.md`; quem tinha um caminho antigo
  ali (ou mudou a pasta de lugar) simplesmente parava de ver o histórico de
  acidentes, sem aviso claro. Agora a pasta acompanha a sua pasta de trabalho.
- **Como montar a base, uma vez só.** Abra a área do ENIT no SharePoint do MTE,
  pasta "CATs eSocial por UF", baixe **todas as planilhas do seu estado** (uma por
  ano) e jogue em `Documentos\AFT\CATs`. O link exige a sua conta institucional
  (Microsoft) logada — é conteúdo interno do Ministério, e o Claude não entra por
  você. O endereço aparece na tela sempre que a base não for encontrada, e também
  no `/aft-setup`.
- **Quem guarda em outro lugar continua atendido.** O caminho gravado com
  `--definir-base` prevalece sobre a pasta padrão, desde que exista de verdade.
- Se o seu `aft-config.md` ainda apontar para uma pasta que não existe, o toolkit
  avisa e usa a pasta padrão em vez de falhar.

Isso vale para a `/aft-relatorio-acidentes` e, por tabela, para a
`/aft-preparacao-acao-fiscal`, que leva o histórico de acidentes para a visita.

---
