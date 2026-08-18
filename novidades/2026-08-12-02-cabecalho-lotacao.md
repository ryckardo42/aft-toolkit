## 12/08/2026
<!-- commit: cabecalho-lotacao -->

**Seus documentos passam a sair com a sua unidade no cabeçalho.**
Até agora todo `.docx` do toolkit saía com um cabeçalho genérico, só com os logos. Agora
o cabeçalho é o institucional completo — brasão da República, "Ministério do Trabalho e
Emprego", "Secretaria de Inspeção do Trabalho", **a sua lotação** e os logos SIT e AFT:

```
Ministério do Trabalho e Emprego
Secretaria de Inspeção do Trabalho
Gerência Regional do Trabalho e Emprego em Nova Iguaçu - RJ
```

- **Vale para tudo**: relatório de fiscalização, dossiê de preparação, análise de
  acidente, relatório de acidentes, Relação de autos e também o **Relatório Técnico de
  interdição/embargo** — nesse, só o cabeçalho muda; todo o texto fixo do modelo oficial
  (tabelas da NR-3, fundamentos legais, pedido de suspensão) continua intocado.
- **A lotação é perguntada uma vez.** Em instalação nova, o `/aft-setup` já pergunta; em
  quem já usa o toolkit, o `/aft-atualizar` mostra o nome da sua unidade como ela sairá
  impressa e pede confirmação — a tabela oficial de UORGs ainda tem nomes antigos ("do
  Trabalho" onde hoje se lê "do Trabalho e Emprego") e grafias com erro, então vale a
  pena conferir. Você pode corrigir o texto na hora; fica gravado no `aft-config.md`.
- Se preferir o cabeçalho sem a linha da unidade, é só dizer: ficam as duas linhas fixas.
- Junto disso, você ganha um **"Template com cabeçalho.docx"** na sua pasta AFT, já com a
  sua lotação, para quando quiser escrever um documento à mão no Word.
