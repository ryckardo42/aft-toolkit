## 22/08/2026
<!-- commit: cnpjs-endereco-skill -->

**Nova habilidade: descobrir os outros CNPJs do endereço antes da visita.** Cenário
conhecido de todo AFT: a Ordem de Serviço aponta uma empresa, mas ao chegar ao
estabelecimento há várias pessoas jurídicas funcionando no mesmo lote — prestadoras
de "apoio administrativo" abertas uma por ano, com o telefone e o e-mail da
principal. A nova `/aft-cnpjs-endereco` descobre isso antes: com o CEP do local, ela
consulta a busca pública de CNPJs pelo navegador do próprio app (só o CEP é enviado,
nada da fiscalização), puxa o cadastro público de cada CNPJ encontrado e cruza tudo
na sua máquina — mesmo lote (mesmo com o endereço escrito de formas diferentes),
CNAE de apoio administrativo em série, telefone, e-mail e sócios compartilhados,
datas de abertura escalonadas. O resultado é um relatório de indícios de possível
grupo econômico, gravado na ficha da empresa, sempre como indício a confirmar em
campo. A habilidade também aceita uma consulta de sistema interno que você colar
(aqueles blocos com "CNPJ:", "Razão Social:", "Endereço:") e faz o mesmo cruzamento
sem nada sair do computador. A `/aft-preparacao-acao-fiscal` ganhou a FASE 4.6, que
chama essa consulta automaticamente quando há CEP — o resumo entra no
`preparacao.md` e nos pontos de atenção da visita.

---
