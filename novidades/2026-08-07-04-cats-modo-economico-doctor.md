## 07/08/2026 (2)
<!-- commit: cats-modo-economico-doctor -->

**Empresa com dezenas de acidentes não gera mais relatório quilométrico — e o
/aft-doctor avisa se a sua base de CATs está vazia.**

- **Modo econômico no relatório de acidentes.** Acima de 25 CATs, a
  `/aft-relatorio-acidentes` mostra os números (total, óbitos, distribuição por
  ano) e pergunta como você quer o relatório: completo, só os **25 mais graves**
  (óbito sempre entra; depois, quem teve o maior afastamento; empate vai para o
  mais recente) ou um **recorte temporal** ("só de 2024 para cá"). O resumo
  estatístico do topo continua cobrindo todos os acidentes, seja qual for a
  escolha — e o próprio relatório declara o recorte, para quem ler depois.
- **Na preparação da visita, sem perguntas.** A `/aft-preparacao-acao-fiscal`
  aplica o modo econômico sozinha quando passa de 25 — o dossiê não fica
  gigante e a preparação não para para perguntar. O relatório completo pode ser
  pedido depois pela `/aft-relatorio-acidentes`.
- **`/aft-doctor` agora confere a pasta `CATs`.** Se não houver planilha
  nenhuma, o diagnóstico avisa com todas as letras: sem elas o relatório de
  acidentes não sai e o dossiê da visita fica sem o histórico — e mostra os dois
  caminhos (ativar o acesso automático ou baixar do ENIT).

---
