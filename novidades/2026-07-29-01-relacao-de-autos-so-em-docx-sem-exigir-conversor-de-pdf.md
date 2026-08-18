## 29/07/2026 (3)
<!-- commit: relacao-de-autos-so-em-docx-sem-exigir-conversor-de-pdf -->

**Sumiu o aviso "nem LibreOffice nem Word encontrados nesta máquina".** Vários colegas
no Windows viram esse alerta no `/aft-doctor` — inclusive em computador **com o Word
instalado e funcionando**. Era falso alarme: a checagem procurava o Word num único lugar
do sistema e não o encontrava quando o Office é de 32 bits e o Python de 64 (combinação
comum). O susto era gratuito, e a conversão que ele cobrava era dispensável.

- **A Relação de autos lavrados agora sai só em `.docx`** — e é esse o documento que vai
  ao processo. O toolkit não tenta mais convertê-la para PDF sozinho.
- **Se você quiser um PDF**, é o caminho de sempre: abra o `.docx` no Word e use
  **Arquivo > Salvar como... > PDF**. Nada mudou aí.
- **Uma dependência a menos.** A skill `/aft-autos-lavrados` não precisa de LibreOffice
  nem de permissão para o toolkit dirigir o Word por trás. Menos coisa para dar errado
  na sua máquina.
- **O `/aft-doctor` deixou de conferir conversor de PDF** — a checagem inteira saiu, junto
  com o aviso.

**O que você precisa fazer: nada.** Se o aviso te incomodava, ele não volta.

---
