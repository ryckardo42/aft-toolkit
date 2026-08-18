## 16/07/2026
<!-- commit: fix-servidor-painel-windows -->

**Painel sempre ligado agora funciona no Windows** — o recurso de deixar o painel
interativo subindo sozinho a cada login (oferecido no `/aft-setup` e no `/aft-atualizar`)
tinha uma falha que fazia a instalação dar erro no Windows ("Acesso negado"). Corrigido:
agora a tarefa é registrada no seu próprio usuário, sem exigir administrador. Quem já
tinha tentado ativar e não conseguiu, é só pedir de novo.

<!-- commit: agenda-google -->

**Prazos de DET no seu Google Calendar** — nova skill `/agenda-det`: cria um evento de
dia inteiro para cada notificação DET com prazo (ex.: "DET RMNHKD5EWIUTJZ THIAGO
CASTR"), atualiza a data quando o prazo é prorrogado e marca ✓ quando você responde.
Usa o conector Google Calendar do Claude (login único do Google, pela interface do
Claude — nenhuma senha passa pelo toolkit). O `/aft-atualizar` vai te oferecer a
ativação.

**"Próximos vencimentos" no painel** — bloco novo logo abaixo dos cards das auditorias: todas as
notificações DET e pendências datadas, de todas as OS, em ordem de vencimento, cada uma
com selo de urgência e botão "agendar no Google Calendar" (esse funciona sem login
nenhum — abre o evento pronto, você só clica em Salvar).

<!-- commit: subtitulos-romanos -->

**Autos de infração com novo visual** — os subtítulos dos autos passaram de "1) DA
FISCALIZAÇÃO" para "I - DA FISCALIZAÇÃO:", "II - IRREGULARIDADE:" e "III -
OBSERVAÇÕES:", cada um em linha própria (com a quebra de linha que o Sistema Auditor
entende). Vale para todas as skills que redigem autos. Autos antigos, já redigidos no
formato numerado, são convertidos automaticamente pelo `/gera-ai` na hora de gerar o
TXT — você não precisa reescrever nada.
