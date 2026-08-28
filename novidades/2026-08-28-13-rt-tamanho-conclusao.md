## 28/08/2026
<!-- commit: fix-tamanho-conclusao -->

**A conclusao do Relatorio Tecnico de Interdicao saia com letra menor que o resto do
documento.** O item "8. CONCLUSAO/OBSERVACAO" vinha em 9pt, enquanto todo o corpo do RT
usa 10,5pt: o paragrafo do modelo onde esse texto entra nao declarava tamanho proprio, e
acabava herdando um tamanho menor. O programa ja sabia consertar a fonte nesse caso, mas
nunca cuidava do tamanho. Agora cuida dos dois, e o RT sai com o corpo todo do mesmo
tamanho. Notado pelo AFT ao revisar um RT gerado pelo toolkit.

---
