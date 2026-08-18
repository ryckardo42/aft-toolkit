# -*- coding: utf-8 -*-
"""
montar_novidades.py - O changelog do AFT deixa de ser um arquivo disputado.

O NOVIDADES.md e o changelog escrito para o AFT, e regra da casa alimenta-lo a
cada mudanca. So que TODA sessao escreve a entrada nova na MESMA linha (o topo
do arquivo): das mudancas da ultima semana, 20 tocaram esse arquivo. Duas
sessoes em paralelo colidiam ali sempre.

A solucao e a de changelog de projeto grande: cada mudanca vira um ARQUIVO
PROPRIO em novidades/, e o NOVIDADES.md passa a ser montado a partir deles.
Sessao nenhuma escreve no arquivo do outro - e conflito nao acontece.

    novidades/2026-08-18-01-cat-trabalhador.md   <- a sessao escreve isto
    NOVIDADES.md                                 <- montado a partir da pasta

Nome do arquivo: AAAA-MM-DD-NN-<assunto>.md, onde NN e a ordem dentro do dia
(01 para a primeira). O conteudo e a entrada como ela aparece no changelog,
comecando pelo cabecalho de data:

    ## 18/08/2026
    <!-- commit: cat-trabalhador-skill -->

    **Titulo em negrito.** O texto para o AFT, sem jargao...

Modos:
    --migrar     fatia o NOVIDADES.md atual em novidades/ (uma vez so)
    --montar     regera o NOVIDADES.md a partir da pasta novidades/
    --conferir   o NOVIDADES.md esta igual ao que a pasta produz? (exit 1 se nao)

Quem monta e publica e o _scripts/publicar.py, rodando na copia principal - um
lugar so, serializado, sem duas sessoes montando ao mesmo tempo.
"""

try:  # ticket automatico de erro (ver _scripts/erro_ticket.py e a skill /aft-erro)
    import sys as _sys
    from pathlib import Path as _Path
    _aqui = _Path(__file__).resolve()
    for _p in (_aqui.parent, *(_a / "_scripts" for _a in _aqui.parents)):
        if (_p / "erro_ticket.py").is_file():
            _sys.path.insert(0, str(_p))
            from erro_ticket import ativar as _ativar_ticket
            _ativar_ticket(__file__)
            break
except Exception:
    pass

import argparse
import re
import sys
import unicodedata
from pathlib import Path

try:  # console do Windows e cp1252
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ARQUIVO = "NOVIDADES.md"
PASTA = "novidades"
# O cabecalho de entrada e "## dd/mm/aaaa", as vezes com um contador do dia que
# o changelog ja usava ("## 10/08/2026 (8)"). Os dois contam como entrada.
RE_DATA = re.compile(r"^## (\d{2})/(\d{2})/(\d{4})(?:\s+.*)?$")
RE_NOME = re.compile(r"^(\d{4})-(\d{2})-(\d{2})-(\d{2})-(.+)\.md$")


def raiz_repo(inicio=None):
    p = Path(inicio or Path(__file__).resolve().parent).resolve()
    for cand in (p, *p.parents):
        if (cand / "AGENTS.md").is_file() and (cand / ARQUIVO).is_file():
            return cand
    return None


def _slug(texto):
    s = unicodedata.normalize("NFD", str(texto or ""))
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"[^A-Za-z0-9]+", "-", s).strip("-").lower()
    return s[:60] or "entrada"


# ---------------------------------------------------------------------------
# Fatiar o arquivo existente
# ---------------------------------------------------------------------------
def fatiar(texto):
    """(cabecalho, [(data, corpo)]) na ordem em que aparecem no arquivo. O corpo
    vai VERBATIM - inclusive o '---' que separa da entrada seguinte -, so sem as
    quebras de linha do fim. E o que permite remontar byte a byte."""
    linhas = texto.splitlines(keepends=True)
    inicios = [i for i, l in enumerate(linhas) if RE_DATA.match(l.rstrip("\n"))]
    if not inicios:
        return texto.rstrip("\n"), []
    cabecalho = "".join(linhas[:inicios[0]]).rstrip("\n")
    entradas = []
    for n, i in enumerate(inicios):
        fim = inicios[n + 1] if n + 1 < len(inicios) else len(linhas)
        corpo = "".join(linhas[i:fim]).rstrip("\n")
        m = RE_DATA.match(linhas[i].rstrip("\n"))
        entradas.append((f"{m.group(3)}-{m.group(2)}-{m.group(1)}", corpo))
    return cabecalho, entradas


def nome_fragmento(data_iso, ordem, corpo):
    m = re.search(r"<!--\s*commit:\s*([^\s>-]+(?:[^>]*?))\s*-->", corpo)
    if m:
        assunto = _slug(m.group(1))
    else:
        m2 = re.search(r"\*\*(.+?)\*\*", corpo, re.S)
        assunto = _slug(m2.group(1) if m2 else "entrada")
    return f"{data_iso}-{ordem:02d}-{assunto}.md"


def migrar(raiz):
    pasta = raiz / PASTA
    if pasta.is_dir() and any(pasta.glob("*.md")):
        return {"ok": False, "erro": f"{PASTA}/ já existe e tem arquivos - "
                                     "a migração é uma vez só"}
    texto = (raiz / ARQUIVO).read_text(encoding="utf-8")
    cabecalho, entradas = fatiar(texto)
    if not entradas:
        return {"ok": False, "erro": "nenhuma entrada '## dd/mm/aaaa' encontrada"}
    pasta.mkdir(parents=True, exist_ok=True)
    (pasta / "_cabecalho.md").write_text(cabecalho + "\n", encoding="utf-8")
    por_data = {}
    escritos = []
    for data_iso, corpo in entradas:  # ordem do arquivo: 01 e a entrada do topo
        por_data[data_iso] = por_data.get(data_iso, 0) + 1
        nome = nome_fragmento(data_iso, por_data[data_iso], corpo)
        (pasta / nome).write_text(corpo + "\n", encoding="utf-8")
        escritos.append(nome)
    return {"ok": True, "fragmentos": escritos, "pasta": str(pasta)}


# ---------------------------------------------------------------------------
# Montar o arquivo a partir dos fragmentos
# ---------------------------------------------------------------------------
def ler_fragmentos(raiz):
    """[(chave_ordenacao, nome, corpo)] - mais recente primeiro; dentro do mesmo
    dia, a ordem e a do numero NN (01 antes de 02), como no arquivo original."""
    pasta = raiz / PASTA
    itens = []
    for f in sorted(pasta.glob("*.md")):
        if f.name.startswith("_"):
            continue
        m = RE_NOME.match(f.name)
        if not m:
            print(f"AVISO: '{f.name}' ignorado - fora do padrão "
                  "AAAA-MM-DD-NN-assunto.md")
            continue
        data = f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
        corpo = f.read_text(encoding="utf-8").rstrip("\n")
        itens.append(((data, -int(m.group(4)), m.group(5)), f.name, corpo))
    # data decrescente; dentro do dia, NN crescente (por isso o sinal invertido)
    itens.sort(key=lambda t: t[0], reverse=True)
    return itens


def montar_texto(raiz):
    """Cabecalho + entradas, coladas com uma linha em branco. O separador '---'
    faz parte do corpo de cada entrada - por isso o texto sai igual ao que era
    antes da migracao, sem normalizacao cosmetica."""
    pasta = raiz / PASTA
    cab = pasta / "_cabecalho.md"
    partes = []
    if cab.is_file():
        partes.append(cab.read_text(encoding="utf-8").rstrip("\n"))
    partes += [c for _, _, c in ler_fragmentos(raiz)]
    if not partes:
        return ""
    return "\n\n".join(partes) + "\n"


def montar(raiz):
    novo = montar_texto(raiz)
    alvo = raiz / ARQUIVO
    antigo = alvo.read_text(encoding="utf-8") if alvo.is_file() else ""
    if novo == antigo:
        return {"ok": True, "mudou": False, "entradas": len(ler_fragmentos(raiz))}
    alvo.write_text(novo, encoding="utf-8")
    return {"ok": True, "mudou": True, "entradas": len(ler_fragmentos(raiz))}


def conferir(raiz):
    """(ok, mensagem) - o NOVIDADES.md do disco e o que a pasta produz."""
    alvo = raiz / ARQUIVO
    if not (raiz / PASTA).is_dir():
        return True, "ainda não migrado (sem pasta novidades/) - nada a conferir"
    novo = montar_texto(raiz)
    antigo = alvo.read_text(encoding="utf-8") if alvo.is_file() else ""
    if novo == antigo:
        return True, (f"NOVIDADES.md em dia com {len(ler_fragmentos(raiz))} "
                      f"entradas de {PASTA}/")
    return False, (f"NOVIDADES.md está DIFERENTE do que {PASTA}/ produz - "
                   "rode: python _scripts/montar_novidades.py --montar")


def conteudo_preservado(raiz, texto_original):
    """Checagem de seguranca da migracao: toda entrada do arquivo original
    aparece, com o mesmo texto, no arquivo montado. Devolve (ok, faltando)."""
    _, entradas = fatiar(texto_original)
    montado = montar_texto(raiz)
    faltando = [corpo.strip().splitlines()[0]
                for _, corpo in entradas if corpo.strip() not in montado]
    return (not faltando), faltando


# ---------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description="Changelog do AFT Toolkit por fragmentos")
    ap.add_argument("--migrar", action="store_true",
                    help="fatia o NOVIDADES.md atual em novidades/ (uma vez so)")
    ap.add_argument("--montar", action="store_true",
                    help="regera o NOVIDADES.md a partir de novidades/")
    ap.add_argument("--conferir", action="store_true",
                    help="confere se o NOVIDADES.md bate com os fragmentos")
    ap.add_argument("--repo", help="raiz do repositorio (padrao: a partir daqui)")
    args = ap.parse_args()

    raiz = raiz_repo(args.repo)
    if raiz is None:
        print("ERRO: não achei a raiz do AFT Toolkit (AGENTS.md + NOVIDADES.md).")
        sys.exit(1)

    if args.migrar:
        original = (raiz / ARQUIVO).read_text(encoding="utf-8")
        r = migrar(raiz)
        if not r["ok"]:
            print("ERRO: " + r["erro"])
            sys.exit(1)
        ok, faltando = conteudo_preservado(raiz, original)
        print(f"MIGRADO: {len(r['fragmentos'])} entradas em {r['pasta']}")
        if ok:
            print("  conferência: todas as entradas do arquivo original foram "
                  "preservadas no texto montado.")
        else:
            print(f"  ATENÇÃO: {len(faltando)} entrada(s) não conferem: " +
                  "; ".join(faltando[:3]))
            sys.exit(1)
        res = montar(raiz)
        print(f"  NOVIDADES.md {'regravado' if res['mudou'] else 'inalterado'} "
              f"({res['entradas']} entradas).")
        sys.exit(0)

    if args.montar:
        r = montar(raiz)
        print(f"NOVIDADES.md {'atualizado' if r['mudou'] else 'já estava em dia'} "
              f"({r['entradas']} entradas de {PASTA}/).")
        sys.exit(0)

    if args.conferir:
        ok, msg = conferir(raiz)
        print(("OK: " if ok else "DIVERGENTE: ") + msg)
        sys.exit(0 if ok else 1)

    ap.print_help()


if __name__ == "__main__":
    main()
