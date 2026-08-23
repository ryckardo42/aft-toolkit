## 23/08/2026
<!-- commit: lre-ferias-folha -->

**A `/aft-lre-esocial` agora audita férias e remuneração, não só o registro.** Quando o
download do eSocial no SISFGTS é feito com a opção **"LRE e demais registros"**, vêm
junto os afastamentos e as bases de FGTS da folha — e a habilidade passou a usar os dois
para responder duas perguntas que antes exigiam pedir documento à empresa:

**1. Quem está com férias atrasadas?** A análise de férias reconstitui os períodos
aquisitivos de cada trabalhador desde a admissão e casa cada um com as férias que o
eSocial registra. O painel `Ferias_painel.html` (mais planilha e resumo) aponta, por
trabalhador:

- **férias vencidas** — período concessivo estourado sem gozo suficiente: indício da
  dobra do art. 137 da CLT;
- **férias gozadas fora do prazo** — o trabalhador até gozou, mas depois do prazo
  concessivo: a dobra é devida mesmo assim (Súmula 81 do TST);
- **prazo vencendo** nos próximos 60 dias — bom para notificar antes de virar infração;
- **conferir abono** — gozo de 20 a 29 dias pode ser regular se houve venda de até 10
  dias (art. 143), que o eSocial não mostra; por isso a habilidade só aponta dobra firme
  com gozo abaixo de 20 dias, e o resto vem como "conferir".

Quatro proteções evitam acusação injusta: só entram períodos iniciados depois que a
empresa (e cada trabalhador, no caso de sucessão ou cessão) chegou ao eSocial — férias
anteriores podem ter sido gozadas sem deixar rastro no arquivo; as faltas que reduzem o
direito (art. 130) não constam, então tudo é **indício** a confirmar nos recibos;
afastamento previdenciário longo zera o período, como manda o art. 133; e o abono é
sempre presumido a favor da empresa. Num teste com empresa real, ignorar a primeira
regra multiplicava os indícios por dez — todos falsos.

**2. A folha declarada fecha com os vínculos?** A análise da remuneração monta a grade
mês a mês de cada trabalhador (`Folha_painel.html`, mais planilha e resumo) e aponta:

- **buraco na folha** — mês dentro do vínculo sem nenhuma base declarada e sem
  afastamento que o justifique;
- **ano sem base de 13º**;
- **últimos 3 meses abaixo de 90% do salário contratual** do LRE — possível pagamento
  "por fora" (a comparação é só com meses recentes: mês antigo abaixo do salário atual é
  normal para quem teve aumento);
- **dispensado pelo empregador sem base rescisória** de FGTS declarada.

Um limite importante, dito com todas as letras no painel: o arquivo traz a base
**declarada**, não o recolhimento — FGTS em atraso quem aponta é o próprio SISFGTS.

**A leitura já vem pronta.** O painel de férias abre com a seção **"Leitura da
auditoria"**: os indícios caso a caso, em frases prontas — quem tem férias vencidas e de
qual período, quem está com o prazo vencendo (avisando quando o trabalhador está de
férias neste momento), quem provavelmente vendeu 10 dias. E uma proteção a mais de
privacidade: **os painéis e planilhas de férias e folha mostram o CPF mascarado**
(`***.***.NNN-NN`) — matrícula e nome bastam para o trabalho; o CPF completo fica só no
painel do LRE, que é o livro de registro propriamente.

Dispare com "férias vencidas", "quem está sem gozar férias", "buraco na folha" ou rode a
`/aft-lre-esocial` normalmente: ela oferece as duas análises quando os dados existem, e
avisa qual opção marcar no SISFGTS quando faltam. Tudo local, como o resto da habilidade:
os painéis abrem sem internet e não fazem requisição nenhuma — nada sai da sua máquina.

---
