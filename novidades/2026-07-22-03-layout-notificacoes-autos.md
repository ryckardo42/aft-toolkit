## 22/07/2026 (3)
<!-- commit: layout-notificacoes-autos -->

**A pasta de cada fiscalização ficou muito mais limpa** — antes, tudo se
acumulava solto na raiz: os PDFs de cada notificação do DET, as pastas com os
documentos que a empresa entregou, cada lote de autos lavrados, a relação de
autos... Numa auditoria com várias notificações isso passava de **30 itens
soltos** na mesma tela.

Agora existem duas caixas:

- **`NOTIFICACOES/`** — todos os PDFs de notificação, os relatórios de
  atendimento e as pastas com os documentos entregues pela empresa.
- **`AUTOS/`** — os lotes de autos (`Autos 25-05/` etc.) e a `Relacao de autos/`.

**O que continua na raiz** (e por um bom motivo): o `memory.md` e todos os
relatórios `.md` — `autos-lavrados.md`, as análises preliminares, as análises de
jornada. É de lá que o **painel** os lê e monta os links; se descessem para uma
subpasta, sumiriam do painel.

Você não precisa fazer nada: rode **`/organiza-os`** e ele migra as pastas
antigas sozinho — só criando as caixas e movendo o que já existe. **Nada é
renomeado nem apagado**, e as fiscalizações que ainda não foram migradas
continuam funcionando normalmente. O `/det-baixar-empregador` já baixa direto
para `NOTIFICACOES/`, e o `/gera-ai` já cria os lotes novos dentro de `AUTOS/`.
