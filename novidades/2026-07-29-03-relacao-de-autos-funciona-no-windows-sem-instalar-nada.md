## 29/07/2026 (1)
<!-- commit: relacao-de-autos-funciona-no-windows-sem-instalar-nada -->

**A Relação de autos lavrados voltou a funcionar no Windows.** Um colega reportou que o
Passo 5.5 da `/aft-autos-lavrados` nunca gerava o documento na máquina dele. O defeito
era real e atingia **todo Windows**: o script pedia ao sistema dois programas de
compactação (`zip` e `unzip`) que o Windows não tem. Ele quebrava no meio, deixando a
Relação por fazer.

- **O documento agora é montado pelo próprio Python**, que já sabe fazer isso sozinho.
  Nada para instalar, nada para configurar. O cabeçalho oficial com os logos SIT/AFT
  continua idêntico.
- **O PDF passou a sair pelo Word.** Antes, a versão em PDF só era gerada se você tivesse
  o LibreOffice instalado — que quase ninguém tem. Agora, quando falta o LibreOffice, o
  toolkit usa o **Microsoft Word que você já tem**, sem abrir janela e sem instalar
  biblioteca nenhuma. Se não houver nem um nem outro, o `.docx` sai normalmente e o
  assistente orienta a exportar o PDF na mão.
- **O `/aft-doctor` passou a conferir** se existe um conversor de PDF nesta máquina, para
  você saber disso antes de precisar.

**O painel também ficou muito mais rápido.** Ele era refeito do zero a cada vez que a
página era aberta — com uma dezena de auditorias, isso passava de 10 segundos, e chegava
a fazer o `/aft-doctor` acusar como "fora do ar" um painel perfeitamente saudável. Agora
o painel só é refeito quando alguma coisa muda de verdade: abrir a página de novo é
instantâneo. E o diagnóstico ganhou uma checagem nova, que percebe quando o servidor no
ar está lendo a pasta **errada** (sintoma de um servidor antigo que sobreviveu a uma
mudança de pasta de lugar).

**O que você precisa fazer: nada.**

---
