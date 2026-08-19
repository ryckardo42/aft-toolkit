## 06/08/2026
<!-- commit: aft-autos-pdf-reunidos -->

**Nova skill `/aft-autos-pdf-reunidos`: todos os autos da empresa em um único
PDF.** Você pede, ela varre a pasta da empresa no Sistema Auditor e entrega um
só arquivo, do auto mais antigo ao mais novo, cada um seguido do próprio anexo
**completo** (as fotos e documentos da pasta `AX_` daquele auto).

- **Dois modos, e ela pergunta antes:** **Completo** (anexos inteiros) ou
  **Econômico** (cada anexo entra com até 10 páginas — dossiê bem menor, bom
  para leitura rápida ou envio). Os cortes do modo Econômico são listados no
  relatório, auto por auto.
- **Anexo repetido entra uma vez só.** O mesmo PGR ou AET anexado a vários
  autos é incluído apenas no primeiro; nos demais o relatório indica onde ele
  já está. A comparação é pelo conteúdo do arquivo, então funciona mesmo
  quando o documento foi salvo com nomes diferentes.
- **Autos de jornada vão para o fim.** Os autos de excesso de jornada,
  intervalos e AFD/AEJ carregam centenas de páginas de relatórios de ponto; a
  skill lê a ementa de cada auto e desloca esses para o final do arquivo, para
  não afogar os demais no meio do dossiê.
- **Fácil de navegar:** o PDF sai com índice lateral (um marcador por auto, com
  os anexos aninhados) e já comprimido.
- **Nada muda no Sistema Auditor:** a skill só lê os PDFs de lá; o arquivo
  final é salvo na pasta da OS, em `AUTOS/Autos reunidos/`.
- **Anexo do relatório final.** O `/aft-sfitweb-rel` agora avisa, ao montar o
  relatório, que este dossiê também será gerado — e o entrega junto, como
  anexo do relatório. Nesse fluxo, o `autos-reunidos.pdf` é salvo na própria
  pasta `Relatórios de Fiscalização/`, ao lado do relatório.
- **Página "ANEXOS - Autos de Infração" no relatório.** O `relatorio-final.docx`
  ganha uma página final apresentando o dossiê, com as observações que
  importam: no modo Econômico, que os anexos foram limitados a 10 páginas e
  que o inteiro teor pode ser solicitado ao Núcleo de Multas; sempre, que
  anexos repetidos aparecem uma única vez; e o total de páginas dos arquivos
  originais que ficaram de fora. Regerar não duplica a página, só a atualiza.

É diferente do `/aft-autos-lavrados`: aquele interpreta os autos e gera o
snapshot e a Relação em `.docx`; este só junta os PDFs num dossiê único.

---
