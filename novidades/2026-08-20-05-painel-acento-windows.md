## 20/08/2026
<!-- commit: painel-acento-windows -->

**Conserto: o painel não quebra mais com acento no nome da empresa (Windows).** Em
algumas máquinas Windows, o `gerar_painel.py` era interrompido por um erro de
codificação na hora de imprimir o resumo final, quando o nome de um empregador
tinha acento gravado de um jeito específico (o "ã" ou "ç" desmontado em duas
partes, coisa que acontece ao colar o nome de outro sistema). O sintoma era a
sincronização do Google Agenda (/aft-agenda-det) ou o /aft-painel pararem no
meio com um ticket de erro. Agora o script se protege sozinho, como os demais
scripts do toolkit já faziam, e imprime o resumo completo em qualquer console.

---
