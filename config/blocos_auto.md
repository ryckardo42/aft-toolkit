# Blocos fixos de auto de infração (AFT Toolkit)

Fonte única dos textos FIXOS e LITERAIS dos autos de infração. As skills que redigem
autos (`/inspecao-inicial`, `/aft-rt-rgi`, `/registro`, `/det-630`,
`/jornada-auto-afd-aej`, `/PGR-analise`, ...) **não escrevem mais o bloco 3** — elas
terminam o auto no bloco 2 (IRREGULARIDADE) seguido de ELEMENTOS DE CONVICÇÃO. O
**`/gera-ai` injeta o bloco 3 abaixo automaticamente em todo e qualquer auto**, pelo
script `_scripts/bloco3_inject.py`.

Vantagens: economia de tokens (o bloco não é regerado em cada auto), fidelidade
garantida (texto idêntico, byte a byte, nunca parafraseado) e formato único (acaba a
divergência entre skills).

> NÃO edite o texto entre as marcas `<BLOCO3>` e `</BLOCO3>` sem orientação. É o
> Subtítulo 3 canônico, igual para todo auto. Usa `#13#10` como quebra de linha (lida
> pelo Sistema Auditor) e acentuação completa (convertida para ISO-8859-1 pelo
> `/gera-ai`). O script lê exatamente o conteúdo entre as marcas.

## bloco3 — Subtítulo 3 (OBSERVAÇÕES), canônico e único

<BLOCO3>
3) OBSERVAÇÕES: a) Lavrado no local da inspeção, conforme parágrafo único do art. 4º da Portaria 667/2021.#13#10b) A auditoria foi iniciada no local de trabalho e continuada em unidade do MTE, com análise documental, pesquisa nos sistemas informatizados e lavratura de documentos (necessidade de acesso a bancos de dados oficiais - eSocial - para confirmação das evidências), o que caracteriza ação fiscal mista, de acordo com o artigo 30, § 3º, do Decreto nº 4.552/2002. Desse modo, a fiscalização ainda se encontra em andamento na data de lavratura deste Auto de Infração.
</BLOCO3>
