## 23/08/2026
<!-- commit: simples-nacional-dupla-visita -->

**A preparação agora lê o Simples Nacional para avisar sobre a dupla visita.** O porte
que aparece no cadastro da Receita (ME/EPP) é declarado pela própria empresa e costuma
ficar desatualizado: empresa que cresceu segue constando como pequena por anos. Já a
opção pelo Simples Nacional é confiável na direção que importa: **quem é optante é,
necessariamente, ME ou EPP** — e portanto candidata ao critério de dupla visita do
art. 627-A da CLT.

Na `/aft-preparacao-acao-fiscal`, a consulta do CNPJ passa a concluir isso para você,
antes de você sair de casa:

- **Empresa optante do Simples** → entra nos pontos de atenção da visita: "optante desde
  dd/mm/aaaa, empresa ME/EPP, candidata à dupla visita". A decisão de aplicar o critério
  continua sendo sua, na autuação — e as exceções (falta de registro, grave e iminente,
  reincidência, fraude, embaraço) continuam valendo.
- **Porte ME/EPP no cadastro, mas sem opção pelo Simples** → o toolkit avisa que o porte
  sozinho não basta para presumir dupla visita. Se a empresa já foi optante e saiu, ele
  mostra a data da exclusão — indício de que cresceu além do porte.

O dado vem dos dados abertos da Receita, atualizados todo mês (bem mais frescos que o
porte cadastral). Para a certeza do dia, a consulta atualizada é o portal do Simples
Nacional ("Consulta Optantes") — ele exige resolver um captcha, então essa confirmação é
manual, sua; a preparação te entrega o link pronto.

Na consulta avulsa (`consulta_cnpj.py`), a linha "Regime" agora mostra desde quando a
empresa é optante e alerta quando o porte cadastral é ME/EPP sem Simples.

---
