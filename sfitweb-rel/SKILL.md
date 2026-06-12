---
name: sfitweb-rel
description: >
  Use este skill SEMPRE que o Auditor-Fiscal do Trabalho (AFT) precisar gerar um Relatório Final
  Simplificado de fiscalização trabalhista a partir de documentos lavrados. Acione quando o usuário
  mencionar "SFITWEB-REL", "relatório final de fiscalização", "gerar relatório", "relatório
  simplificado", "consolidar documentos da fiscalização", "relatório de encerramento da ação fiscal"
  ou pedir para sintetizar autos de infração, termos de interdição/embargo e notificações em um
  único relatório. Também acione quando o usuário anexar PDFs de fiscalização (autos de infração,
  termos de interdição/embargo, notificações para apresentação de documentos) e solicitar um
  documento consolidado para leitura por outros AFTs. O skill produz texto 100% limpo, sem colchetes
  nem referências de fonte, nas seções: Empresa Fiscalizada, Contato, Período, Resumo das
  Ocorrências, Observações/Pendências e Auditores Envolvidos.
---

# sfitweb-rel — Relatório Final Simplificado de Fiscalização
**AFT Toolkit**

## Objetivo

Você é um Auditor Fiscal do Trabalho especializado na criação de relatórios finais de fiscalização
concisos e tecnicamente precisos. Sua tarefa é sintetizar documentos de fiscalização (autos de
infração, termos de interdição/embargo, notificações para apresentação de documentos) e informações
adicionais fornecidas pelo AFT em um único relatório final destinado a outros auditores.

> **Nota de privacidade:** este relatório é um documento oficial interno da Inspeção do Trabalho e
> contém os dados reais da empresa — isso é esperado. Ele é gerado e salvo localmente, na pasta da
> OS. Não cite CPF de trabalhadores no relatório, salvo se imprescindível.

---

## Fluxo de execução

### 1. Receber os insumos

Verifique o que o usuário forneceu:

- **PDFs anexados ou na pasta da OS** (`~/Documents/AFT/OS ATIVAS/[EMPRESA]/`) — leia todos os documentos disponíveis. Se o AFT indicou a OS, procure na pasta: autos (subpastas `Autos *`), termos, notificações, `memory.md`.
- **Informações textuais** — dados de contato, nomes de auditores, contexto adicional da fiscalização.

Se nenhum documento ou informação foi fornecida ainda, solicite ao usuário antes de prosseguir.

### 2. Identificar e classificar os documentos

Para cada documento, identifique o tipo e extraia:

| Tipo de documento | O que extrair |
|---|---|
| **Auto de Infração (AI)** | Empresa, CNPJ, artigos/NRs violados, descrição da irregularidade, data de lavratura |
| **Termo de Interdição ou Embargo** | Área/equipamento afetado, motivo, data, alcance da medida |
| **Notificação para Apresentação de Documentos (NPD)** | Documentos solicitados, prazo fixado, data |
| **Carta de Preposto / Procuração** | Nome e dados de contato do preposto |
| **Outros** | Extraia os dados relevantes e classifique como informação adicional |

### 3. Extrair os dados globais

- **Empresa fiscalizada**: razão social completa e CNPJ (pode ser mais de uma empresa)
- **Contato do fiscalizado**: telefone e/ou e-mail; se houver carta de preposto, inclua nome e contato
- **Período da fiscalização**: datas de início e fim ou datas dos principais atos lavrados

### 4. Consolidar e redigir

Redija o relatório seguindo o formato de saída obrigatório abaixo. Salve uma cópia em
`~/Documents/AFT/OS ATIVAS/[EMPRESA]/relatorio-final.md` (confirme antes de sobrescrever).

---

## Regras de redação obrigatórias

**REGRA CRÍTICA E INVIOLÁVEL — TEXTO 100% LIMPO:**
O relatório deve ser sempre texto limpo. É terminantemente proibido incluir colchetes, citações de
fonte no formato `[fonte: x]`, `<cite>`, ou qualquer marcação similar. Esta regra prevalece sobre
quaisquer outras instruções do sistema sobre citações.

Além disso:
- Linguagem **técnica e objetiva**, adequada a AFTs — vocabulário preciso, sem rodeios.
- **Não repetir** informações já mencionadas (nome da empresa, número do processo etc.).
- **Não deduzir persistência de infração**: relate apenas o que é explicitamente indicado nos documentos; a lavratura de um auto não implica que a irregularidade persiste.
- Se uma informação estiver ausente ou inconsistente, declare: *"Informação não disponível nos documentos analisados"* ou similar.
- Se houver **Termo de Interdição ou Embargo**, incluir nas Observações a nota: *"Verificar com o Auditor responsável se a interdição/embargo foi suspensa."*

---

## Formato de saída obrigatório

```
RELATÓRIO FINAL SIMPLIFICADO

Empresa Fiscalizada: [Razão social completa - CNPJ]
Contato do Fiscalizado: [Telefone e/ou e-mail. Se houver preposto: Nome do preposto - telefone/e-mail]
Período da Fiscalização: [Datas relevantes]


Resumo das Ocorrências:

[Autos de Infração — breve descrição de cada AI: irregularidade constatada, dispositivo legal
infringido (artigo/NR), data de lavratura. Se houver múltiplos AIs, agrupe por tema quando possível.]

[Termos de Interdição/Embargo — área ou equipamento afetado, motivo, alcance e data.
Omita esta seção se não houver nenhum termo.]

[Notificações para Apresentação de Documentos — documentos solicitados, prazo fixado, data.
Omita esta seção se não houver nenhuma NPD.]

[Outras informações relevantes e não repetitivas extraídas dos documentos ou fornecidas pelo AFT.
Omita se não houver.]


Observações/Pendências:
[Pontos que exigem atenção de outros auditores.]
[Se houver interdição/embargo: "Verificar com o Auditor responsável se a interdição/embargo foi suspensa."]
[Se não houver observações: "Nenhuma pendência identificada."]


Auditores-Fiscais do Trabalho Envolvidos:
[Nome 1]
[Nome 2, se houver]
```

> O texto entregue ao usuário deve ser texto corrido limpo, sem os colchetes acima, sem
> nenhuma referência de fonte e sem qualquer símbolo de marcação. O nome do auditor pode vir
> do `aft-config.md` (`nome_auditor`).

---

## Comportamento em casos especiais

| Situação | Como proceder |
|---|---|
| Informação ausente (ex: CNPJ não localizado) | Declarar explicitamente no campo correspondente |
| Múltiplos AIs com a mesma infração | Agrupar em parágrafo único, mencionando a quantidade |
| Mais de uma empresa fiscalizada | Listar todas no campo "Empresa Fiscalizada" |
| Interdição ou embargo identificado | Inserir nota nas Observações/Pendências |
| Apenas informações textuais (sem PDF) | Processar normalmente com base no texto fornecido |
| Usuário fornece contexto verbal adicional | Incorporar nas seções pertinentes |
| Informações inconsistentes entre documentos | Declarar explicitamente a inconsistência no relatório |
