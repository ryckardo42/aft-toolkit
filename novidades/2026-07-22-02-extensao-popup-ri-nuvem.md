## 22/07/2026 (3)
<!-- commit: extensao-popup-ri-nuvem -->

**Duas correções na extensão Sync DET** (a do botão "Sincronizar" na tela do DET).

**O indicador de token voltou a dizer a verdade.** Ao clicar no ícone da
extensão, o status dizia "Token DET não encontrado" mesmo quando a sincronização
estava funcionando perfeitamente — ele procurava o crachá do DET numa gaveta
errada. Agora ele olha no lugar certo e usa o mesmo critério do botão (crachá com
menos de 25 minutos), então o que o indicador mostra é exatamente o que vai
acontecer se você clicar em Sincronizar.

**O destino na nuvem (SisOS) passou a respeitar o RI da auditoria.** Ele
importava *todas* as notificações do CNPJ — inclusive as de fiscalizações
antigas ou de outros auditores — e, ao preencher sozinho o RI, adotava a
notificação mais antiga da lista, podendo até trocar um RI que você já tinha
declarado. Agora vale a mesma regra que já corrigimos no painel local: **o RI que
você declarou manda**; auditoria ainda sem RI adota o da notificação **mais
recente**; e notificação de outra fiscalização não entra nem some em silêncio —
volta na resposta da sincronização para você decidir.

Isso só afeta quem usa o SisOS na nuvem. No uso local (painel em
`127.0.0.1:8347`), nada muda — a regra já era essa.

---
