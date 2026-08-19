## 28/07/2026 (2)
<!-- commit: preparacao-le-a-os-do-sfit -->

**Anexou a Ordem de Serviço ou a Demanda? O toolkit lê sozinho — e protege o
denunciante.** A `/aft-preparacao-acao-fiscal` e a `/aft-nova-os` agora entendem os dois
PDFs que o SFIT-WEB gera: a **Demanda** ("Detalhar Demanda", com a denúncia e os dados
do demandante) e a **Ordem de Serviço** (mais resumida, com os prazos da fiscalização e
a equipe de AFTs). Basta anexar um deles — ou os dois — e dizer que vai fiscalizar
aquela empresa. A pasta da OS é criada com tudo preenchido — razão social, CNPJ,
endereço completo, telefone, CNAE (já com o grau de risco), número da OS e da demanda,
prazos para iniciar e terminar a fiscalização, equipe — sem redigitar nada; a sessão da
empresa no menu lateral continua aparecendo sozinha, como sempre.

- **Ementas da OS no dossiê** — a tabela de irregularidades "a fiscalizar" da demanda
  vira a seção `## Ementas da OS` no memory.md, com caixinhas para marcar o que já foi
  verificado; ela também guia o estudo prévio e o checklist de documentos da preparação.
- **Denunciante protegido** — nome, telefone e e-mail de quem denunciou **nunca**
  aparecem no chat nem nos arquivos de trabalho: o assistente se refere a ele como
  `[[DENUNCIANTE_01]]` e reescreve o resumo da denúncia sem os traços que o identificam
  (parentesco, tempo de casa, função). A única cópia do contato é o próprio PDF da
  demanda, arquivado dentro da pasta da OS — quem precisar ligar, abre o PDF.
- **Chegada planejada (Google Maps)** — a preparação grava no `preparacao.md` o link do
  endereço no Maps (montado no seu computador, sem consultar ninguém) e, se você quiser,
  abre o mapa para confirmar o local e anotar observações de acesso antes da visita.
- **Alarme de contato esquecido** — o guarda de privacidade (`checar_pii.py`), que já
  apontava CPF/PIS, agora avisa também e-mails e telefones que escapem para um arquivo
  de trabalho; as skills já mandam ignorar o telefone da própria empresa, então o alarme
  que sobrar merece atenção (pode ser o contato do denunciante).
- **`preparacao.docx`: a triagem para levar impressa na visita** — além da ficha em
  markdown, a preparação passa a gerar um documento no padrão do toolkit (cabeçalho
  oficial, pronto para imprimir) montado sobre uma única pergunta: *o que dá para
  constatar no local e o que, só faltando isso, precisa ser notificado?* São três
  seções — o quadro de triagem (ementas da OS de um lado, o que verificar em campo do
  outro), os documentos a exigir logo na chegada e, por último, o mínimo que sobra para
  o DET. A ideia é que a inspeção física resolva a maior parte: documento pedido por
  notificação chega depois e já ajustado.
- **Fim do "estudo prévio"** — a preparação não pergunta mais quais temas você quer
  estudar nos NotebookLMs antes da visita. Ela ficou focada no que é dela: organizar a
  OS, as ementas, o endereço e o checklist de documentos. Para tirar dúvida técnica,
  achar a ementa certa ou entender o que exigir sobre um tema, use a `/aft-consulta` —
  antes, durante ou depois da preparação, quantas vezes precisar.

**O que você precisa fazer: nada.** Anexe o PDF da OS na conversa e diga que vai
fiscalizar a empresa — o resto do fluxo segue como sempre.

---
