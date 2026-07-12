---
name: inspecao-fisica
model: sonnet
description: >
  Use SEMPRE que o AFT chegar de uma inspeção/fiscalização de campo e narrar — por voz ditada
  ou texto corrido — o que encontrou in loco, e quiser registrar isso como um relato
  estruturado. Dispare com /inspecao-fisica, ou frases como "cheguei da inspeção e vou narrar
  o que vi", "registra o relato da visita", "transforma minha narrativa em bullet points",
  "monta o inspecao-fisica.md", "anota os achados de campo da empresa X", "documenta a
  inspeção física". A skill pega a narrativa bruta e a converte numa lista de bullet points
  fiéis (descrição da visita + irregularidades constatadas), salvando em `inspecao-fisica.md`
  na pasta da OS para ser consumida depois por /PGR-analise (confronto campo × PGR) e
  /inspecao-inicial (redação dos autos). É PURAMENTE DESCRITIVA: não classifica NR, não cita
  ementa, não enquadra infração nem opina — só organiza os fatos relatados. Não confundir com
  /inspecao-inicial, que redige os autos de infração; esta skill apenas produz o relato de
  campo que aquela consome.
---

# Skill: Inspeção Física (relato de campo → bullets)
**AFT Toolkit**

## Objetivo

O AFT volta da inspeção com tudo fresco na cabeça e narra, de forma corrida, o que viu. Essa
narrativa é valiosa mas desorganizada: fatos sobre o mesmo trabalhador aparecem espalhados,
observações de setores diferentes se misturam, e o relato precisa virar um registro limpo e
durável.

Esta skill faz **uma coisa só, muito bem**: transforma essa narrativa em uma lista de bullet
points fiéis e salva em `inspecao-fisica.md` na pasta da OS. Esse arquivo é a memória de campo
da fiscalização — depois a `/PGR-analise` o lê para confrontar a realidade in loco contra o
PGR, e a `/inspecao-inicial` o usa como base factual para redigir os autos.

**Princípio central — fidelidade acima de tudo.** O valor deste relato é ser uma transcrição
honesta do que o AFT constatou. Nomes, datas, valores, jornadas, funções e CNPJ têm peso
jurídico: um fato perdido vira um auto não lavrado; um fato inventado ou trocado vira nulidade.
Por isso a regra é preservar **todos** os fatos narrados, sem acrescentar nada que o AFT não
disse e sem remover nada que ele disse.

**Esta skill NÃO classifica.** Ela não cita NR, não menciona ementa, não escreve "isso
configura infração ao item X", não sugere enquadramento. Essa inteligência jurídica é trabalho
da `/inspecao-inicial` e da `/PGR-analise`. Aqui, só os fatos.

**Nota de privacidade (política do toolkit).** O relato salvo em disco é a fonte de prova local
e mantém os nomes reais — ele nunca sai do computador do AFT. Os dados pessoais entram no chat
uma única vez, no ditado; depois que o relato é salvo e os trabalhadores são registrados no
mapa de-para da OS (se existir), as skills seguintes referem-se a eles por tokens
(`[[TRAB_NN]]`), e o TXT final do Sistema Auditor é re-hidratado por script (ver `/gera-ai`).

---

## Passo a passo

### Passo 1 — Localizar a pasta da OS

O arquivo precisa ser salvo na pasta certa para as skills seguintes o encontrarem. Determine a
pasta da empresa em `~/Documents/AFT/OS ATIVAS/`:

- Se o AFT já citou a empresa/CNPJ nesta conversa, use-a.
- A narrativa às vezes não nomeia a empresa ("na empresa", "nessa obra"). Se você não tiver
  certeza de qual OS é, **pergunte** antes de salvar — ou liste as pastas de `OS ATIVAS/` como
  candidatas.

```bash
ls ~/Documents/AFT/"OS ATIVAS"/
```

Se a OS ainda não tiver pasta (empresa nova), pergunte ao AFT como quer nomear a pasta
(padrão do toolkit: `<NOME DA EMPRESA> <CNPJ 14 dígitos>`) e crie-a.

### Passo 2 — Receber a narrativa

Aceite a narrativa como texto colado ou ditado. Ela costuma ser um parágrafo corrido, com
pontuação irregular (fruto de ditado por voz). Não peça que o AFT reescreva — é seu trabalho
organizar.

### Passo 3 — Converter em bullet points

Transforme a narrativa em uma lista de bullets seguindo estas regras:

1. **Um bullet por situação/observação distinta.** Cada irregularidade, cada constatação, cada
   condição do estabelecimento vira um bullet próprio.

2. **Agrupe os fatos sobre o mesmo sujeito.** Quando o AFT descreve um trabalhador, junte num
   único bullet tudo que se refere a ele — nome, função, jornada, salário, situação de
   registro, ASO, data de início, uniformização — ainda que esses fatos apareçam espalhados em
   pontos diferentes da narrativa. O leitor precisa ver a situação completa de cada pessoa de
   uma vez.

3. **Abra pelo contexto da visita.** O primeiro bullet normalmente registra a abertura da ação:
   data/dia de início, empresa, e quem acompanhou (preposto, responsável).

4. **Preserve cada fato exatamente.** Nomes próprios, datas, valores em reais, horários,
   número de funcionários, grau de risco, CNPJ — copie como narrado. Não arredonde valores, não
   "corrija" datas, não normalize nomes. **E nunca descarte um fato narrado** — mesmo que a frase
   chegue truncada ou com cara de erro de ditado (ex: "máquina destruída de proteção"). Mantenha
   o trecho o mais fiel possível, verbatim quando você não tiver certeza do que ele quis dizer,
   e leve a dúvida para o eco do Passo 4. Descartar é pior do que manter confuso: o AFT relê e
   corrige um bullet estranho, mas não recupera o que sumiu do relato.

5. **Limpeza apenas leve.** Você pode quebrar o texto corrido em frases legíveis e remover
   muletas de fala ("aí", "então", repetições do ditado). Mas **não parafraseie**, não troque o
   vocabulário do AFT por sinônimos, não mude o tom e não acrescente interpretação. O relato
   deve soar como o AFT falou, só que organizado.

6. **Sem classificação jurídica.** Nenhum número de NR, nenhuma ementa, nenhum juízo de
   infração. Só descrição.

7. **Pontuação dos bullets.** Termine cada bullet com ponto e vírgula (`;`); o último pode
   terminar com ponto (`.`).

8. **Não use travessões** (em-dash). É convenção do toolkit (e o latin-1 do Sistema Auditor não
   os aceita): substitua por vírgula, dois pontos, parênteses ou hífen simples.

#### Exemplo de referência

Este exemplo mostra o nível de fidelidade e de agrupamento esperado. Repare que os fatos da
trabalhadora (sem registro, função, jornada, salário, ASO, data de início, uniformização)
foram reunidos em um único bullet, mesmo tendo sido narrados de forma dispersa. (Exemplo
fictício.)

**Narrativa (entrada):**

> a inspeção iniciada no dia sexta-feira, dia 29 de maio de 2026 na empresa e acompanhada da
> preposta Juliana Rodrigues. Durante a inspeção no setor de produção foi encontrada a
> trabalhadora Melissa Oliveira sem registro, Trabalhando na função de auxiliar de produção, de
> segunda a sexta-feira, de 8 às 18 com uma hora de almoço Com o valor prometido de salário de
> R$ 2.000 Essa trabalhadora não havia sido submetida à aso admissional também E declarou ter
> começado a trabalhar no dia 22 de maio de 2026 Estava plenamente uniformizada. Constatei que
> a empresa, apesar de possuir 50 funcionários e grau de risco 3, não possui CIPA. Apesar da
> empresa exigir uniforme, não possui vestiário. Flagrei uma máquina de fabricação de
> cremosinho no setor de produção com partes móveis expostas, sem proteção fixa ou móvel com
> intertravamento, operada por Antonio Luiz.

**Bullets (saída):**

```markdown
- Inspeção iniciada na sexta-feira, dia 29 de maio de 2026, na empresa, acompanhada da preposta Juliana Rodrigues;
- No setor de produção foi encontrada a trabalhadora Melissa Oliveira sem registro, na função de auxiliar de produção, de segunda a sexta-feira, das 8 às 18 com uma hora de almoço, com salário prometido de R$ 2.000. Não foi submetida a ASO admissional. Declarou ter começado a trabalhar no dia 22 de maio de 2026. Estava plenamente uniformizada;
- A empresa, apesar de possuir 50 funcionários e grau de risco 3, não possui CIPA;
- Apesar de exigir uniforme, a empresa não possui vestiário;
- No setor de produção, máquina de fabricação de cremosinho com partes móveis expostas, sem proteção fixa ou móvel com intertravamento, operada por Antonio Luiz.
```

### Passo 4 — Eco de confirmação (antes de salvar)

Mostre os bullets ao AFT e peça uma conferência rápida antes de gravar:

> "Organizei o relato assim. Confere se não perdi nem troquei nenhum fato antes de eu salvar em
> `inspecao-fisica.md`:"

Essa conferência existe porque o relato é fonte de prova: é barato para o AFT bater o olho
agora, e caro descobrir um fato faltando depois que virou auto. Ajuste conforme o retorno.

### Passo 5 — Salvar `inspecao-fisica.md`

Grave na raiz da pasta da OS. O corpo do arquivo é a lista de bullets; um cabeçalho mínimo
ajuda a rastreabilidade sem poluir o relato:

```markdown
# Inspeção física

**Empresa:** <nome, se conhecido>
**Data da inspeção:** <data narrada, se houver>

- <bullet 1>;
- <bullet 2>;
...
```

Caminho: `~/Documents/AFT/OS ATIVAS/<PASTA_EMPRESA>/inspecao-fisica.md`

**Se o arquivo já existir** (ex: segunda visita à mesma obra), pergunte ao AFT: *"Já existe
`inspecao-fisica.md` nesta OS. Deseja (a) acrescentar estes achados ao final, (b) substituir o
conteúdo, ou (c) cancelar?"* Não sobrescreva sem confirmação.

### Passo 5.1 — Guard-rail de PII (opcional, só avisa)

Logo após salvar, rode o checador de PII de alto dano sobre o relato. Ele detecta apenas
**CPF e PIS/PASEP** (formato fixo + dígito verificador) — o único dado de pessoa natural que
pode escapar para o TXT em texto claro se entrar por engano no ditado. Não troca nem bloqueia
nada; só avisa:

```bash
python ~/.claude/skills/_scripts/checar_pii.py "<PASTA_OS>/inspecao-fisica.md"
```

Se houver um `depara.json` na OS, acrescente `--depara "<PASTA_OS>/depara.json"` para que ele
marque o que já está tokenizado (`[já no de-para]`) versus o que está solto (`[SOLTO]`).

- **Saiu "✓ Nenhum CPF/PIS detectado":** siga normalmente.
- **Apareceu um CPF/PIS:** avise o AFT em uma linha — *"Detectei 1 CPF no relato; confirme que
  ele entra no de-para antes do `/gera-ai`."* O nome do trabalhador em contexto permanece no
  relato por design (é prova local); o alerta é só para o número de documento.

### Passo 6 — Encadeamento

Depois de salvar, ofereça o próximo passo natural do toolkit:

> "Salvei em `inspecao-fisica.md`. Quer que eu siga para `/PGR-analise` (confronta estes
> achados de campo contra o PGR da empresa) ou `/inspecao-inicial` (redige os autos de
> infração a partir do relato)?"

---

## Regras de ouro

- **Fidelidade total:** preserve todos os fatos, não invente nenhum e **não descarte nenhum**.
  Na dúvida sobre um fato ambíguo ou truncado, mantenha as palavras do AFT (verbatim) no bullet e
  sinalize a dúvida no eco, em vez de interpretar ou omitir.
- **Só descrição:** nada de NR, ementa, capitulação ou juízo de infração. Esse é o trabalho das
  skills seguintes.
- **Voz do AFT:** organize, não reescreva. O relato deve soar como ele falou.
- **Sem travessões.**
- **Conferência antes de salvar:** o eco do Passo 4 não é opcional quando há nomes, datas ou
  valores em jogo.
- **O arquivo fica local:** nunca cole o conteúdo do `inspecao-fisica.md` em serviços externos.
