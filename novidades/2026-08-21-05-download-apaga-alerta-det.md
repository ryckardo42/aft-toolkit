## 21/08/2026
<!-- commit: download-apaga-alerta-det -->

**O download agora conta como visualização no DET.** Baixar os arquivos pelo
botão "⬇ baixar arquivos" ou pela /aft-det-baixar deixava o triângulo amarelo
"Existe atualização pendente" aceso na tela do DET, como se o auditor não
tivesse visto a entrega. Corrigido: ao final de cada download, o motor faz as
mesmas leituras que o site faz quando você abre a notificação e cada item — o
DET registra a visualização e o triângulo se apaga sozinho (confirmado em caso
real). Efeito colateral bem-vindo: no próximo Sincronizar, o alerta
"atualização pendente" do painel também se apaga sem precisar do clique
"já vi". Se o registro falhar, o download não é afetado: o resultado avisa com
"visto_no_det: false".

---
