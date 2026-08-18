## 28/07/2026 (5)
<!-- commit: mudanca-de-pasta-a-prova-de-caminho-longo -->

**Mudar a pasta de lugar ficou seguro de verdade.** A função lançada hoje mais cedo foi
testada de ponta a ponta numa máquina real, com 9 auditorias e 444 arquivos, e falhou:
seis PDFs de uma análise de acidente fatal (um ASO, um PCMSO, documentos CAF/CEF)
**ficaram para trás sem nenhum aviso**, e uma cópia pela metade dos documentos sigilosos
foi abandonada no destino. A causa é uma armadilha antiga do Windows, e ela agora está
resolvida.

- **Caminhos longos deixaram de sumir.** As pastas que o DET baixa aninham muito
  (`OS ATIVAS › EMPRESA › notificacao-XXXX › NOTIFICACAO_XXXX › NOTIFICACAO_XXXX ›
  ITEM_NN › arquivo.pdf`) e passam dos 260 caracteres que o Windows aceita por padrão.
  Acima desse limite, o computador se comporta como se o arquivo **não existisse** — e a
  cópia o pulava calada. A mudança de pasta agora usa o modo de caminho estendido do
  Windows e enxerga todos eles.
- **Conferência antes de apagar.** A pasta antiga só é removida depois que a nova é
  conferida arquivo a arquivo e byte a byte. Se algo não fechar, a cópia incompleta é
  desfeita sozinha e **os seus dados continuam onde estavam** — nunca fica um duplicado
  parcial de documento sigiloso largado por aí.
- **Nada de meio-termo perigoso.** Se a cópia conferiu mas algum arquivo da pasta antiga
  não pôde ser apagado (o caso comum: um `.docx` aberto no Word), a mudança se completa
  normalmente e isso vira apenas um aviso. Antes, esse caso era tratado como erro e o
  toolkit continuava apontando para a pasta já esvaziada.
- **Voltar atrás funciona.** Uma pasta de destino que contenha só diretórios vazios
  deixou de bloquear a operação — é o esqueleto que o Windows deixa para trás quando um
  programa está com a pasta aberta, não dado seu.
- **O painel não fica mais servindo a pasta errada.** Ao reinstalar o servidor do painel
  depois de mudar a pasta, a instância antiga era mantida viva segurando o endereço, e o
  `/aft-doctor` dizia "no ar" enquanto o painel lia o lugar de antes — chegando a recriar
  a pasta antiga sozinho. Agora o servidor velho é encerrado antes de o novo subir.

**O que você precisa fazer: nada.** Quem não mudou a pasta de lugar não é afetado.

**Uma ressalva honesta:** a pasta não pode ser renomeada enquanto estiver aberta em algum
programa — e a própria conversa do Claude Code aberta na auditoria conta como um deles.
Por isso a mudança quase sempre copia (mais lento que renomear) e costuma deixar para
trás a casca vazia da pasta antiga, que você pode apagar pelo Explorer depois de fechar o
aplicativo. Feche também os documentos abertos no Word antes de mudar a pasta: além de
travarem a limpeza, eles continuam apontando para o caminho velho.

---
