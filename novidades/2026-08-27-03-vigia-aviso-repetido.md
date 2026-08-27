## 27/08/2026
<!-- commit: vigia-aviso-repetido -->

**O vigia das sessões parou de repetir o mesmo aviso e de fazer trabalho à toa.** Quem
cria sozinho a sessão de cada auditoria no grupo "OS ATIVAS" é um vigia que fica em
segundo plano. Para ler os grupos do app, ele usa um componente extra que, quando falta,
ele tenta instalar sozinho.

Em algumas máquinas essa instalação nunca pode dar certo (o Python instalado ali recusa,
por segurança, instalar coisas por fora). O vigia não guardava essa informação: tentava
de novo a cada volta, mais ou menos a cada minuto, para sempre — e cada tentativa deixava
uma linha de AVISO no registro `.sessoes-os.log`. No caso real, o registro acumulou
avisos idênticos de um dia inteiro. Pior: mesmo sem o componente, ele ainda copiava 15 MB
de dados do app antes de descobrir que não ia conseguir ler nada.

Agora ele tenta **uma vez só** por execução. Não deu, avisa uma vez e segue pelo caminho
alternativo, em silêncio, sem copiar nada. O registro volta a mostrar só o que interessa,
e a máquina para de trabalhar de graça enquanto você usa o computador.

Nada muda no que você vê: as sessões continuam sendo criadas do mesmo jeito.

---
