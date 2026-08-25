#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
conferir_cotejo.py — acha o documento que entrou na OS e nunca foi confrontado.

Duas lacunas com a mesma raiz, e nenhuma tinha ferramenta:

  - DOCUMENTO SEM SKILL DONA. Cada skill de análise cuida do seu documento: o
    PGR tem a /aft-PGR-analise, a AET tem a /aft-aet-auditoria, o laudo de
    máquinas tem a /aft-auditoria-AR-NR12. O que sobra — planilha de empregados,
    ficha de EPI, certificado de treinamento, projeto elétrico, CCT, protocolo —
    não tem etapa que obrigue a lê-lo, e some da análise sem nada acusar.

  - AS FOTOS DA INSPEÇÃO. Nenhuma skill lê foto. Elas são documento
    complementar da mesma resposta, e ficam à margem exatamente porque nada as
    cobra.

Numa fiscalização real as duas se materializaram juntas: documentos entregues na
resposta a uma notificação foram inventariados e nunca abertos, e a análise foi
concluída sem que as fotos da inspeção entrassem nela.

O QUE ESTE SCRIPT PROVA, E O QUE NÃO PROVA. Ele compara o que EXISTE na pasta
com o que é MENCIONADO nos documentos de análise da própria OS. **Menção não é
análise**: um documento citado de passagem aparece como mencionado, e nenhuma
leitura de arquivo distinguiria isso. O inverso, porém, é conclusivo — documento
que não aparece em lugar nenhum certamente não foi confrontado, e é isso que
interessa achar ANTES de dar a análise por encerrada.

Ele não apaga, não move e não escreve nada. Só lista, e a decisão é do
Auditor-Fiscal.

Uso:
    python conferir_cotejo.py "<pasta da OS>"
    python conferir_cotejo.py "<pasta da OS>" --resumo

Exit 0 = todo documento de entrada aparece nas análises; 1 = há documento sem
menção (ou foto não tratada); 2 = erro de uso.
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

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# O que conta como documento a confrontar.
EXT_DOCUMENTO = {".pdf", ".docx", ".doc", ".xlsx", ".xls", ".csv", ".txt", ".md"}
EXT_FOTO = {".jpg", ".jpeg", ".png", ".heic", ".bmp", ".tif", ".tiff", ".webp"}

# Pastas que guardam o que a FISCALIZACAO produziu, nao o que ela recebeu.
# Documento de saida nao e objeto de cotejo -- ele e o resultado dele.
# ATENCAO ao escrever esta lista: os nomes passam por normalizar(), que troca
# TODO caractere nao alfanumerico por espaco. "interdicao-embargo" com hifen
# nunca casaria -- e nao casava, de modo que o Relatorio Tecnico de embargo,
# documento PRODUZIDO pela fiscalizacao, aparecia como nao confrontado.
PASTAS_SAIDA = {"autos", "relatorios de fiscalizacao", "interdicao embargo",
                "backups", "pycache", "autos reunidos"}

# Arquivos que o proprio fluxo produz e que, por isso, nao se confrontam.
# AGENTS/CLAUDE/README sao instrucoes do toolkit, nao documento de fiscalizacao:
# apareceram como "nao confrontados" na primeira execucao real deste script.
NOMES_SAIDA = re.compile(
    r"^(autos|tn-nco|nco|nad|relatorio|relacao|analise preliminar|memory|"
    r"autos-lavrados|inspecao-fisica|caderno-constatacoes|preparacao|"
    r"lre-esocial|relatorio-validacao)", re.I)

# Instrucoes do toolkit, nao documento de fiscalizacao. Casam por nome EXATO --
# um PDF chamado "Claudete.pdf" continuaria sendo documento a confrontar.
NOMES_INSTRUCAO = re.compile(r"^(agents|claude|readme|notes)$", re.I)

# Pastas cujo conteudo e DERIVADO da analise (extrato, OCR): confrontar o
# derivado seria confrontar o proprio trabalho, nao o documento da empresa.
PASTAS_DERIVADAS = {"extratos", "ocr", "esocial", "cache"}

# Onde a analise mora. As skills de analise escrevem nestes lugares, e e neles
# que um documento confrontado deixa rastro.
FONTES_ANALISE = [
    "memory.md",
    "*-extrato.md", "pgr-extrato.md", "aet-extrato.md", "laudo-extrato.md",
    "inspecao-fisica.md",
    "NOTIFICACOES/*.docx", "NOTIFICACOES/*.md",
    "NOTIFICACOES/EXTRATOS/*.md", "NOTIFICACOES/EXTRATOS/*.docx",
    "RELATÓRIOS DE FISCALIZAÇÃO/*.docx", "RELATORIOS DE FISCALIZACAO/*.docx",
    "AUTOS/**/autos*.md",
]

# Palavras que denunciam que as fotos foram efetivamente tratadas na analise.
RE_FOTO_TRATADA = re.compile(
    r"\bfoto|fotogr|registro fotogr|imagem|imagens|constatad[oa] na imagem", re.I)

# Palavras curtas ou genericas demais para identificar um documento pelo nome.
VAZIAS = {"documento", "documentos", "arquivo", "digitalizado", "scan", "novo",
          "final", "copia", "anexo", "anexos", "parte", "pagina", "paginas",
          "resposta", "empresa", "ltda", "corrigido", "assinado", "versao"}


def normalizar(t: str) -> str:
    t = "".join(c for c in unicodedata.normalize("NFD", t.lower())
                if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]+", " ", t)


def e_saida(caminho: Path, raiz: Path) -> bool:
    rel = caminho.relative_to(raiz)
    partes = {normalizar(p).strip() for p in rel.parts[:-1]}
    if partes & PASTAS_SAIDA:
        return True
    # Derivada: basta a pasta COMECAR pelo nome (EXTRATOS, OCR-item13...).
    if any(any(p.startswith(d) for d in PASTAS_DERIVADAS) for p in partes):
        return True
    if any(p.startswith(".") for p in rel.parts):
        return True
    return bool(NOMES_SAIDA.match(caminho.stem)
                or NOMES_INSTRUCAO.match(caminho.stem))


def texto_das_analises(raiz: Path) -> tuple[str, list[str]]:
    """Junta o texto de toda analise ja produzida na OS. Devolve (texto, fontes)."""
    pedacos, fontes = [], []
    vistos = set()
    for padrao in FONTES_ANALISE:
        for f in raiz.glob(padrao):
            if not f.is_file() or f in vistos:
                continue
            vistos.add(f)
            try:
                if f.suffix.lower() == ".docx":
                    import docx
                    d = docx.Document(str(f))
                    t = "\n".join(p.text for p in d.paragraphs)
                    for tb in d.tables:
                        for lin in tb.rows:
                            t += "\n" + "\n".join(c.text for c in lin.cells)
                else:
                    t = f.read_text(encoding="utf-8", errors="replace")
            except Exception as e:
                fontes.append("%s (ILEGIVEL: %s)" % (f.name, type(e).__name__))
                continue
            pedacos.append(t)
            fontes.append(f.name)
    return normalizar("\n".join(pedacos)), fontes


def mencionado(doc: Path, analise: str) -> bool:
    """O documento aparece na analise? Casa pelo nome inteiro ou pelos termos.

    Nao inventa vinculo: exige que TODOS os termos significativos do nome
    apareçam. "PGR 2026 assinado.pdf" casa com um texto que fale de PGR e 2026;
    nao casa com um texto que so cite "2026".
    """
    nome = normalizar(doc.stem)
    if nome.strip() and nome.strip() in analise:
        return True
    termos = [t for t in nome.split() if len(t) >= 4 and t not in VAZIAS]
    if not termos:
        return False
    return all(t in analise for t in termos)


def main():
    ap = argparse.ArgumentParser(
        description="Acha documento e foto que entraram na OS e nunca apareceram "
                    "em analise.")
    ap.add_argument("pasta_os", help="pasta da OS")
    ap.add_argument("--resumo", action="store_true", help="so o veredito")
    ap.add_argument("--forcar", action="store_true",
                    help="lista mesmo com a analise incipiente")
    args = ap.parse_args()
    raiz = Path(args.pasta_os).expanduser()
    resumo = args.resumo
    forcar = args.forcar
    if not raiz.is_dir():
        print("ERRO: nao e uma pasta: %s" % raiz, file=sys.stderr)
        return 2

    docs, fotos = [], []
    for f in raiz.rglob("*"):
        if not f.is_file():
            continue
        ext = f.suffix.lower()
        if ext in EXT_FOTO:
            if not any(p.startswith(".") for p in f.relative_to(raiz).parts):
                fotos.append(f)
        elif ext in EXT_DOCUMENTO and not e_saida(f, raiz):
            docs.append(f)

    analise, fontes = texto_das_analises(raiz)
    if not analise.strip():
        print("Nenhum documento de análise encontrado nesta OS.")
        print("Nada a conferir ainda: rode ao ENCERRAR a análise, não antes.")
        return 0

    # ANALISE INCIPIENTE. Numa OS em que a analise mal comecou, quase todo
    # documento estara "sem mencao" -- e listar cento e trinta nomes nao ajuda
    # ninguem, so ensina a ignorar a saida. O script diz o que de fato observou
    # e para. O numero e proposital: quatro fontes de analise ja indicam uma OS
    # em que se escreveu alguma coisa; abaixo disso, o cotejo e prematuro.
    if len(fontes) < 4 and len(docs) > 3 * max(1, len(fontes)):
        print("ANÁLISE AINDA INCIPIENTE nesta OS: %d documento(s) de entrada para "
              "apenas %d de análise." % (len(docs), len(fontes)))
        print("Quase tudo apareceria como não confrontado, o que não seria achado —")
        print("seria o retrato de uma análise que ainda não foi feita.")
        print("Rode de novo ao encerrar a análise. (--forcar lista assim mesmo)")
        if not forcar:
            return 0

    # Um documento cujo EXTRATO ou OCR existe na OS foi lido, ainda que a
    # analise nao o cite pelo nome do arquivo -- e ela raramente cita: fala do
    # ASSUNTO ("o procedimento de seguranca da serra"), nao de "PS001_PS002".
    # Sem esta distincao a ferramenta acusava como nao confrontado justamente o
    # documento que tinha 16 mil caracteres de OCR gravados ao lado.
    extraidos = {normalizar(f.stem).strip()
                 for f in raiz.rglob("*")
                 if f.is_file() and f.suffix.lower() in (".txt", ".md")
                 and any(any(normalizar(p).startswith(d) for d in PASTAS_DERIVADAS)
                         for p in f.relative_to(raiz).parts[:-1])}

    sem_mencao, so_extraidos = [], []
    for d in sorted(docs):
        if mencionado(d, analise):
            continue
        (so_extraidos if normalizar(d.stem).strip() in extraidos
         else sem_mencao).append(d)
    fotos_tratadas = bool(RE_FOTO_TRATADA.search(analise))

    if not resumo:
        print("=" * 72)
        print("  COTEJO -- o que entrou na OS apareceu na análise?")
        print("=" * 72)
        print("  pasta ....... %s" % raiz.name[:56])
        print("  analisado a partir de %d documento(s) de análise" % len(fontes))
        print("  documentos de entrada: %d   |   fotos: %d" % (len(docs), len(fotos)))

    problemas = 0

    print("\n1. DOCUMENTOS SEM MENÇÃO EM NENHUMA ANÁLISE")
    if sem_mencao:
        problemas += len(sem_mencao)
        print("   Estes existem na pasta e não aparecem em análise nenhuma. Antes de")
        print("   encerrar a análise: ou o documento é confrontado, ou o motivo de não")
        print("   o ser é declarado ao AFT, com a ementa que fica sem resposta.")
        for d in sem_mencao:
            print("     - %s" % d.relative_to(raiz))
    else:
        print("   Nenhum: todo documento de entrada aparece em alguma análise.")
        print("   (menção não é análise -- isto exclui o esquecimento, não o descuido)")

    if so_extraidos:
        print("\n1b. EXTRAÍDOS, mas não citados pelo nome do arquivo")
        print("    Existe extrato ou OCR destes na OS, logo foram lidos. A análise")
        print("    costuma falar do ASSUNTO e não do nome do arquivo, então isto")
        print("    normalmente está certo -- confira só se o achado deles apareceu.")
        for d in so_extraidos:
            print("     - %s" % d.relative_to(raiz))

    print("\n2. FOTOS DA INSPEÇÃO — documento complementar da mesma resposta")
    if not fotos:
        print("   Nenhuma foto nesta OS.")
    elif fotos_tratadas:
        print("   %d foto(s) na pasta, e a análise fala de fotografia/imagem." % len(fotos))
        print("   Confira se ela trata do que as fotos MOSTRAM, e não só que existem.")
    else:
        problemas += 1
        print("   %d foto(s) na pasta e NENHUMA análise menciona foto ou imagem." % len(fotos))
        print("   Nenhuma skill lê foto: se a análise não fala delas, elas ficaram fora.")
        print("   Já aconteceu de a conclusão sair sem elas e o AFT ter de perguntar")
        print("   \"você não viu as fotos?\" -- depois de a análise estar pronta.")
        for f in sorted(fotos)[:10]:
            print("     - %s" % f.relative_to(raiz))
        if len(fotos) > 10:
            print("     ... (+%d)" % (len(fotos) - 10))

    print("\n" + "-" * 72)
    if problemas:
        print("%d ponto(s) a resolver antes de encerrar a análise." % problemas)
        return 1
    print("Nada pendente de cotejo nesta OS.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
