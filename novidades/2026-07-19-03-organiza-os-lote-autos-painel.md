## 19/07/2026 (2)
<!-- commit: organiza-os-lote-autos-painel -->

**/organiza-os agora organiza tudo de uma vez, com menos perguntas** — a skill passou a
varrer a pasta OS ATIVAS inteira num único passe: organiza as pastas novas, atualiza as
já organizadas que receberam arquivos novos e apenas relata as vazias. Você aprova UM
plano consolidado (uma pergunta só) em vez de responder pasta a pasta. Pasta sem a
notificação do DET não trava mais nada: a OS é criada com o campo em branco para
preencher depois. Ao final, ela roda sozinha o `/autos-lavrados` (trazendo os autos já
transmitidos no Sistema Auditor para as fichas e o painel) e abre automaticamente o
painel interativo (http://127.0.0.1:8347) com o panorama geral.

Aprendizados de uso real incorporados: arquivos temporários do Word (`~$...`) são
ignorados em silêncio; nomes de download duplicado ("arquivo (1).pdf") são normalizados;
o relatório de atendimento do DET conta como prova de que a notificação foi respondida;
código de DET só é aceito se vier do PDF da própria notificação (número de acordo
coletivo não engana mais); minutas e análises que você já tinha feito ficam intactas e
anotadas na ficha da OS.
