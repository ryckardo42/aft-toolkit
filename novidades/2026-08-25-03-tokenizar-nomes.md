## 25/08/2026
<!-- commit: tokenizar-nomes -->

**A troca do nome do trabalhador pelo apelido `[[TRAB_01]]` deixou de ser feita à mão.** O caminho de volta já era automático: na hora de gerar o arquivo do Sistema Auditor, um programa troca o apelido pelo nome verdadeiro, letra por letra, sem o assistente participar — porque um nome errado num auto é inaceitável. O caminho de ida, porém, dependia de o assistente digitar o nome no arquivo de correspondência. Agora ele também é feito por programa: você informa o nome, o programa cria o apelido, substitui no texto e depois confere se sobrou algum nome verdadeiro ou algum CPF perdido no arquivo.

A conferência responde APROVADO ou REPROVADO antes de o texto virar auto. Ela recusa CPF de trabalhador no arquivo de correspondência (o Sistema Auditor não usa esse campo) e nunca renumera um apelido já usado num auto.

---
