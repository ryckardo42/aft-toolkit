## 20/07/2026
<!-- commit: modelo-docx-padrao -->

**Todo documento .docx do toolkit agora tem a mesma cara** — nova skill
`/modelo-docx`: o padrão visual oficial dos documentos gerados pelo toolkit.
Qualquer `.docx` — um relatório avulso que você pedir, o Relatório Final do
`/sfitweb-rel`, saídas de skills futuras — sai sobre o template com o cabeçalho
da auditoria (logos AFT e SIT), em Times New Roman 12, com títulos em azul
institucional, corpo justificado e tabelas com cabeçalho azul e linhas
zebradas. A skill traz a biblioteca pronta (`modelo_docx.py`) com as peças do
documento (capa, seções, listas, tabelas, assinatura), então tudo o que for
gerado daqui em diante segue o mesmo modelo sem esforço. Documentos com modelo
oficial próprio — RT de interdição/embargo e Relação de autos — continuam nos
templates deles. O perfil do auditor foi atualizado (v3) para aplicar o padrão
automaticamente também aos documentos pedidos fora das skills.
