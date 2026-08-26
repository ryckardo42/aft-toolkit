## 26/08/2026
<!-- commit: consulta-cnpj-cache-pasta-aft -->

**A pasta "AFT" fantasma que voltava sozinha em Documentos.** Quem tem a pasta de
trabalho fora do lugar padrão — no OneDrive, num HD externo, em outro disco — via
aparecer, do nada, uma segunda pasta `AFT` dentro de `Documentos`, vazia de
fiscalizações. O `/aft-doctor` então avisava "pasta de trabalho duplicada". Apagar não
adiantava: na consulta seguinte a pasta renascia.

A culpada era a consulta de CNPJ na Receita Federal. Ela guarda no computador uma cópia
das respostas (para não perguntar duas vezes a mesma coisa à Receita, o que é mais rápido
e expõe menos o CNPJ na rede), e essa cópia estava sendo gravada num caminho fixo, sem
perguntar onde a sua pasta de trabalho realmente está.

Agora a cópia vai para dentro da sua pasta AFT, onde quer que ela esteja. Nenhuma
fiscalização foi afetada — o que ia parar na pasta fantasma era só o cache da consulta.

Se a pasta duplicada já existe na sua máquina, pode apagá-la: ela não volta mais. Depois,
rode `/aft-doctor` e o aviso some.

Correção do colega Diego.

---
