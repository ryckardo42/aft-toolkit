## 06/08/2026
<!-- commit: gera-ai-dados-da-os -->

**O TXT dos autos agora sai com o endereço e o CNAE reais da fiscalizada — sem os
placeholders genéricos de antes.** O `/aft-gera-ai` nasceu antes do
`/aft-preparacao-acao-fiscal`, quando a ficha da OS não guardava endereço nem CNAE;
por isso ele preenchia a linha da empresa com marcadores ("Ja conferiu a UORG?", CNAE
de escritório) e você precisava clicar na lupa do Sistema Auditor para o próprio
sistema completar os dados.

- **O que muda.** Se a OS foi preparada pelo `/aft-preparacao-acao-fiscal` (ou a ficha
  `memory.md` tem a linha de endereço), o TXT importável já sai com logradouro, número,
  complemento, bairro, CEP, município/UF e o CNAE verdadeiros, lidos da própria Ordem
  de Serviço.
- **A lupa vira conferência, não obrigação.** Só é preciso corrigir na lupa se algum
  campo não constar da OS — nesse caso o Claude avisa no chat qual campo saiu com
  placeholder.
- **Nada muda para OS antigas**: sem dados na ficha, o comportamento continua o de
  antes (placeholders + lupa).
- **Correção no Mac:** o conferidor final do TXT reprovava autos com anexo (foto,
  termo, laudo) mesmo com o arquivo no lugar certo — ele procurava o anexo pelo
  caminho do Windows, que não existe no Mac. Agora ele converte o caminho e confere
  o arquivo de verdade.
- **Fim de um engano antigo:** um campo fixo do TXT rotulado de "tipo de ação
  fiscal" (valor `1008`) era, no layout oficial do Sistema Auditor, o **número
  total de trabalhadores da empresa** — todo auto saía dizendo que a empresa tem
  1008 empregados. Agora vai `0` (não informado). Quem instalou antes não precisa
  fazer nada: a skill ignora o valor antigo do config.
- **"Grupo que desenvolveu a ação fiscal" já vai respondido.** Cada auto do TXT
  agora leva essa informação preenchida com "Nenhum" — uma pergunta a menos na
  tela do Sistema Auditor. Se a ação for de grupo móvel (trabalho escravo,
  portuário), avise o Claude na hora de gerar o TXT para ajustar.
