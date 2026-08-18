## 07/08/2026 (5)
<!-- commit: relatorio-doencas-ocupacionais -->

**`/aft-relatorio-acidentes` agora tem o modo de DOENÇAS OCUPACIONAIS — e ele
caça a doença escondida como "acidente típico".**

- **Peça "as doenças do trabalho da empresa"** e sai o
  `Relatorio-Doencas-<cnpj>.md` + `.docx`, separado do relatório de acidentes.
  Funciona nos dois modos de sempre (CSV do Portal AFT ou base estadual de CATs).
- **Três categorias no relatório.** (1) *Doenças declaradas*: CATs com tipo
  "Doença". (2) *Suspeitas fortes*: CATs cadastradas como "Típico" mas com CID
  de doença ocupacional (síndrome do manguito rotador, túnel do carpo,
  epicondilites, tenossinovites, PAIR, transtornos mentais, pneumoconioses,
  dermatoses de contato, neoplasias ocupacionais) **e** um sinal a mais no
  Agente causador ou na Situação geradora: "esforço excessivo", movimento
  repetitivo ou agente "inexistente". (3) *Suspeitas*: o CID de doença sem o
  sinal a mais, ou dor musculoesquelética inespecífica (lombalgia, mialgia)
  com "esforço excessivo".
- **Por que isso importa:** empresa que registra a LER/DORT como "acidente"
  esconde a falha crônica do GRO/PGR e da AET. Na base de Goiás de 2026, para
  cada CAT de doença declarada há quase duas suspeitas cadastradas como
  típico. O relatório aponta o indício com o motivo escrito em cada CAT; a
  caracterização é sua, caso a caso.
- **Tudo local, como sempre:** as planilhas têm nome, CPF e saúde de
  trabalhador — nada disso passa pelo chat nem vai à nuvem. No chat só
  aparecem números agregados e os caminhos dos arquivos.
- A lista de CIDs vigiados vem da Lista de Doenças Relacionadas ao Trabalho
  (Portaria GM/MS nº 1.999/2023 e Anexo II do Decreto nº 3.048/1999) e fica
  aberta no topo do script, fácil de ampliar.

---
