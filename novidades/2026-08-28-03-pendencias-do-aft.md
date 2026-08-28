## 28/08/2026
<!-- commit: pendencias-do-aft -->

**A seção Pendências da ficha voltou a ser sua.** A lista `## Pendências` do memory.md
foi criada para você anotar as suas tarefas da auditoria, mas o assistente e as skills
vinham enchendo a seção sozinhos, e ela estava ficando poluída. Três mudanças:

- **O assistente agora pergunta antes.** Se ele achar que algo merece virar pendência,
  ele oferece ("quer que eu registre X como pendência da OS?") e só grava com o seu sim.
  Vale também para o RT de interdição que ficou faltando após uma auditoria.
- **A preparação da ação fiscal não escreve mais nada ali.** Lacunas da preparação
  (efetivo não levantado, NAD não gerada) já aparecem no próprio documento de preparação;
  não precisam sujar a ficha.
- **Duas exceções continuam automáticas, mas em linguagem clara**: autos redigidos
  aguardando o empacotamento agora entram como "Há N autos redigidos (NR-XX) esperando
  serem transformados para importação no Sistema Auditor" (em vez do antigo "Empacotar
  autos via /aft-gera-ai..."), e as irregularidades de dupla visita aguardando a
  notificação para correção seguem o mesmo estilo, sem jargão nem nome de skill.

De quebra, linhas que eram registro de coisa feita (parecer de laudo NR-12, RT de
manutenção/levantamento de interdição) deixam de ir para Pendências e passam para a
seção certa da ficha (Auditoria de documentos ou Interdições/Embargos). Nada disso
muda o painel: ele continua mostrando e resolvendo as pendências normalmente.

---
