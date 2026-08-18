## 02/08/2026
<!-- commit: rt-rgi-embargo-fotos-e-montador -->

**O relatório de interdição aprendeu a diferença entre interditar e embargar, passou
a aceitar fotos e ficou muito menos sujeito a erro na montagem.** Tudo isso saiu de
um teste com dois casos completos (máquinas e obra). Você não precisa fazer nada.

- **Embargo x interdição.** A NR-03 separa as duas medidas pelo objeto, não pela
  gravidade: **obra é sempre embargo**; máquina, setor ou atividade é interdição.
  A skill não sabia disso e produzia um "Termo de Interdição" mesmo para obra, com
  o texto todo falando em interdição e o campo pedindo "identificação da máquina".
  Agora ela decide certo e adapta o documento inteiro sozinha. Também passou a
  restringir a paralisação ao menor escopo possível (só os pavimentos com problema,
  por exemplo), como a norma manda.
- **Fotos dentro do RT.** Antes não havia jeito de pôr foto no relatório. Agora a
  foto entra no corpo do documento, logo abaixo da irregularidade que ela ilustra,
  já no tamanho certo da página e com legenda. A única exigência é que a foto
  exista como arquivo: imagem colada no chat não serve, tem que estar salva.
- **Montagem do documento sem edição manual.** O relatório era montado editando o
  "código" do Word à mão, um campo de cada vez — lento e fácil de errar. Um script
  novo preenche tudo de uma vez e confere o resultado. De quebra, ele evita três
  defeitos que já apareciam: numeração interna inválida que corrompia o arquivo,
  ementas sem marcador (que faziam o conferidor acusar erro à toa) e o item
  "Requerimento expresso" aparecendo entre as medidas em vez de entre os documentos.
- **Conferidor de coerência mais confiável.** Ele acusava "NR-03 sem auto
  correspondente" em **todo** relatório, porque a NR-3 é a norma da própria medida e
  aparece no texto fixo. Esse alarme falso acabou.
- **Erros de português no modelo oficial corrigidos:** "preoposto" virou "preposto",
  "da empresa aptos" virou "apto" e "das Norma Regulamentadoras" virou "das Normas
  Regulamentadoras". Saíam em todos os relatórios emitidos.
- **O modelo passou a usar campos `{{nome_do_campo}}`, com um dicionário próprio.**
  Cada lugar do relatório que recebe texto tem agora um campo identificado, e a skill
  sabe o que vai em cada um: o que descrever no objeto, o que citar na irregularidade,
  como fundamentar consequência e probabilidade. A numeração dos itens e das alíneas
  passou a ser automática do Word — nada de "A)" ou "3." digitados. Um mesmo relatório
  pode ter vários objetos e vários fatores de risco, cada um com seu bloco.
  **Atenção a uma mudança de fundo:** os itens 1, 2 e 8 viraram texto fixo. A data
  da inspeção saiu do item 1 e passou a ter campo próprio no item 2 (veja abaixo).
- **Campo próprio para o contexto da inspeção, no item 2.** É onde entra, no mínimo,
  a data da inspeção física — e, quando houver, quem acompanhou, o que foi percorrido
  e o que a empresa não apresentou na hora. Com isso o item 4 ficou **só com as
  ementas, a descrição da irregularidade e a capitulação**, sem narrativa de visita
  no meio.
- **O texto gerado agora sai com a mesma cara do resto do documento.** Antes, o que a
  skill escrevia podia sair em outra fonte, sem justificação e sem recuo, porque cada
  trecho do modelo carrega sua própria formatação e alguns não a traziam. Agora o
  relatório sai todo em Tahoma, justificado e com o mesmo espaçamento; as ementas
  ganharam marcador; e sumiu a linha em branco que separava demais o último item das
  medidas de proteção.
- **A skill não inventa mais detalhe que você não constatou.** Modo operatório, tipo
  de serviço em execução e número de trabalhadores expostos só entram se estiverem no
  seu relato. Faltando o dado, aparece `[A CONFIRMAR PELO AFT: ...]` no documento,
  para você completar — em vez de um detalhe verossímil que passaria despercebido na
  revisão e cairia na impugnação. Pelo mesmo motivo, medidas e documentos exigidos
  agora só podem decorrer de uma irregularidade efetivamente listada.
- **Consulta obrigatória ao caderno da NR do caso.** A skill já consultava o
  ementário; agora consulta também o caderno da norma específica (NR-12, NR-18...).
  Num teste, essa segunda consulta revelou uma ementa aplicável que a primeira não
  tinha apontado.
- **As irregularidades agora aparecem logo abaixo do título "4. IRREGULARIDADE(S)".**
  Antes iam parar no fim da seção, depois de toda a explicação da metodologia e das
  tabelas — longe de onde se procura por elas. O modelo ganhou marcações com "#"
  indicando onde cada bloco de texto entra, e some do documento final a linha de
  exemplo "OBJETO: 1 – ATIVIDADE", que era só um lembrete de formato.
