## 24/08/2026
<!-- commit: textos-do-modelo-det -->

**A notificação que aproveita a introdução e as observações do seu modelo do DET
voltou a funcionar.** Quando você pedia a NAD (ou a notificação para correção)
reaproveitando os textos do modelo que já tem no DET, em vez dos textos padrão do
toolkit, o painel respondia com um erro sem sentido nenhum — `KeyError: 'ordem'` —
e não gerava nem a prévia nem o rascunho. Nada do que você tinha escrito estava
errado: os blocos de texto que o DET devolve num modelo vêm sem a numeração que o
site espera, e o toolkit os aproveitava exatamente como vinham.

Agora todo texto de notificação passa pela mesma preparação, venha do seu arquivo
`.md` ou do modelo do DET: recebe a numeração na ordem certa (introdução primeiro,
observações depois) e os campos que o formulário do site exige. Você não muda nada
no seu jeito de pedir — só deixa de esbarrar no erro.

**De quebra, uma trava nova antes de escrever no DET.** Se por qualquer motivo um
texto chegar sem posição definida, ou com duas posições iguais, a conferência
segura o rascunho e avisa em português — a empresa não recebe uma notificação com
os parágrafos fora da ordem em que você escreveu. Antes isso passaria em silêncio.

Obrigado ao colega que relatou o defeito com o passo a passo completo: foi o
relato dele que mostrou onde estava o problema.

---
