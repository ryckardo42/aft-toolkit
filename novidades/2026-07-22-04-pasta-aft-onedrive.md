## 22/07/2026 (2)
<!-- commit: pasta-aft-onedrive -->

**Correção importante para quem usa Windows com OneDrive** — a pasta de
trabalho (`AFT` com `OS ATIVAS` e `OS ARQUIVADAS`) podia ser criada num lugar
que você nunca encontrava. Motivo: o toolkit presumia
`C:\Users\<você>\Documents`, mas quando o **OneDrive faz backup das suas
pastas**, "Documentos" passa a ser `C:\Users\<você>\OneDrive\Documentos` — e no
Windows em português ela se chama **Documentos**, não *Documents*. Resultado: o
`/aft-setup` criava uma pasta invisível no caminho errado e o AFT ficava sem
saber onde ficaram as fiscalizações.

Agora o toolkit descobre a sua pasta Documentos **de verdade** (lendo o registro
do Windows, que já sabe do OneDrive e do idioma) — e o **`/aft-doctor` passa a
criar a pasta se ela faltar**, dizendo o caminho exato onde criou. Basta rodar:

```
/aft-doctor
```

**Se você já instalou antes e a pasta ficou no lugar errado**, o toolkit **não
abandona os seus dados**: continua usando a pasta onde as suas fiscalizações
estão (elas funcionam normalmente ali). O `/aft-doctor` agora **avisa** que essa
pasta não é a sua "Documentos" de verdade — que é por isso que você não a acha
pelo Explorer — e **oferece mudar tudo de lugar**, com os dados. Se aceitar, ele
fecha o app (para soltar os arquivos), move a pasta inteira para a Documentos
correta e ainda atualiza o `path_windows` do seu `aft-config.md`. Nada é apagado,
e nada é sobrescrito: se já houver uma pasta com conteúdo no destino, ele recusa
e explica. Se preferir deixar como está, também tudo bem — continua funcionando.

O painel, o servidor e o vigia de sessões passam a usar o mesmo caminho
resolvido.
