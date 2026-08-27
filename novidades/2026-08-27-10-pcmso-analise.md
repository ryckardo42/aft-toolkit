## 27/08/2026
<!-- commit: pcmso-skill-token-optimization -->

**Nova skill: análise de PCMSO (NR-07).** A `/aft-PCMSO-analise` audita o Programa de
Controle Médico de Saúde Ocupacional entregue pela empresa contra uma base fixa de 32
ementas da NR-07: da elaboração e implantação do programa aos exames por função e risco,
passando pelo conteúdo mínimo do ASO, pelo Relatório Analítico anual e pelos controles
dos Anexos (audiometria e poeiras minerais). Como nas análises de PGR e AET, o PDF é
lido fora da conversa, por um agente extrator próprio, e a análise corre sobre o extrato
com citação de página: o documento grande não consome o limite da sua conversa nem é
relido a cada mensagem. A skill entende PCMSO entregue em partes pelo DET (aqueles
arquivos fatiados "1-11", "12-22"...) como um documento só, confronta o programa com os
riscos do PGR e com o que você viu na inspeção física, e ao final oferece os autos das
ementas não conformes prontos para o `/aft-gera-ai` e uma carta de recomendação para a
empresa. Dado de saúde é tratado como sensível: nome de trabalhador de ASO ou prontuário
nunca aparece no chat nem nos autos, só a função ou o setor.

---
