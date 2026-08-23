## 23/08/2026
<!-- commit: consulta-cnpj-rfb -->

**A OS agora nasce sabendo quem é a empresa.** Quando você informa o CNPJ, o toolkit
consulta sozinho o cadastro da Receita Federal e preenche o que antes você digitava à
mão: razão social, município, endereço, telefones, CNAE principal (e daí o grau de risco
da NR-04), natureza jurídica, porte e Simples Nacional. É a mesma consulta do cartão CNPJ
que você já faz no site da Receita — dado público de empresa, sem login nem senha.

Vale em duas habilidades:

- **`/aft-nova-auditoria`** — ao cadastrar a auditoria, a ficha `memory.md` já sai
  preenchida. O que **você** informou sempre prevalece: se o cadastro divergir, o toolkit
  mantém o seu dado e avisa a diferença em uma linha — pode ser filial, endereço
  desatualizado na Receita, ou engano de digitação. Quem decide é você.
- **`/aft-preparacao-acao-fiscal`** — a consulta acontece **antes** da busca na internet,
  para a pesquisa já partir da razão social exata. E alimenta o resto do planejamento: o
  CNAE vai para o dimensionamento de SESMT e CIPA, o endereço vai para o acesso no mapa e
  para a checagem de outros CNPJs no mesmo local.

**Dois avisos que a preparação passa a te dar antes de você sair de casa:**

1. **Empresa que não está ATIVA** (baixada, inapta, suspensa), com a data. Pode não haver
   empresa no endereço, ou haver sucessão.
2. **Atividade de risco escondida nos CNAEs secundários.** Acontece muito: o CNAE
   principal é de escritório, e nos secundários aparecem imunização de pragas, instalação
   hidráulica, limpeza. Muda o EPI, a NR aplicável e o que procurar no local. É indício
   para orientar o olhar — a atividade real se confirma na inspeção.

**O que a consulta não traz:** o e-mail do empregador. A Receita não distribui esse campo
nos dados abertos (ele aparece no cartão CNPJ como "ENDEREÇO ELETRÔNICO"). E o pacote não
diz de quando é o retrato — para ato com efeito legal, confirme na fonte oficial. Empregador
pessoa física (CPF/CAEPF) não é consultado.

Se faltar internet ou o CNPJ não for encontrado, nada trava: o toolkit avisa em uma linha e
segue o fluxo normal.

Para consultar avulso, fora das habilidades:

```
python ~/.claude/skills/_scripts/consulta_cnpj.py 00000000000191
```

---
