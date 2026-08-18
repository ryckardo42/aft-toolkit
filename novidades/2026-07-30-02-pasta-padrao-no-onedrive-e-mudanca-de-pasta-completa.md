## 30/07/2026
<!-- commit: pasta-padrao-no-onedrive-e-mudanca-de-pasta-completa -->

**No Windows, a pasta de trabalho agora nasce dentro do OneDrive.** Era o que a maioria
dos colegas fazia à mão depois de instalar: as fiscalizações ficavam numa pasta local,
fora do backup da instituição e invisíveis no notebook levado a campo. Numa **instalação
nova**, o toolkit passa a criar a pasta `AFT` dentro do seu OneDrive — o **corporativo**
(o do trabalho) na frente do pessoal —, mesmo quando o OneDrive não faz backup da sua
pasta Documentos.

- **Quem já usa o toolkit não tem nada mudado de lugar.** Uma pasta AFT que já existe com
  fiscalizações dentro nunca é abandonada. O `/aft-doctor` passa a **sugerir** a mudança
  (uma linha, não é defeito) e mover só acontece se você pedir. Se preferir manter onde
  está, é só me dizer: eu fixo a escolha e o aviso não volta.

**Mudar a pasta de lugar agora leva TUDO junto.** Antes, o `--mover` levava os arquivos
com segurança mas deixava para trás duas coisas que guardam o caminho por dentro — e o
colega só descobria depois, sem entender:

- **As suas conversas por empresa.** Cada sessão do menu lateral guarda a pasta da OS
  dentro dela; sem realinhar, o app mostrava **"Sessão não encontrada no disco"** (foi o
  que aconteceu com 2 de 8 empresas numa mudança real). Agora o `cwd` de cada sessão e o
  histórico da conversa acompanham a mudança. Como isso não pode ser feito com o app
  aberto, fica uma pendência que se aplica sozinha **no próximo fechamento do app** —
  feche e reabra uma vez e está pronto.
- **Os serviços que rodam sozinhos** (painel sempre ligado, rotina das 07:00, vigia de
  sessões). Eles guardavam a pasta congelada na instalação e continuavam varrendo o lugar
  antigo — o painel chegava a **recriar a pasta velha** ao se salvar. Agora são derrubados
  antes da mudança e reinstalados depois, já apontando para o lugar novo.

**O que você precisa fazer: nada.** Se um dia mudar a pasta de lugar (OneDrive, HD
externo, outro disco), peça a mudança normalmente e feche o app uma vez ao final.

---
