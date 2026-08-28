## 28/08/2026
<!-- commit: fix-content-types-foto -->

**Foto em .jpg deixou de corromper o documento.** Ao inserir uma fotografia num
documento do toolkit, o programa embutia a imagem mas esquecia de registrar, na ficha
interna do arquivo, que aquele tipo de imagem estava ali dentro. O Word recusava o
documento inteiro, dizendo que o arquivo estava corrompido. Aparecia justamente com foto
de celular em .jpg, que e o caso mais comum. Corrigido: o registro passa a ser feito
sozinho, para qualquer tipo de imagem.

---
