#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
reune_autos_pdf.py (AFT Toolkit) — reúne todos os autos de infração lavrados
(PDFs AI_*.PDF do Sistema Auditor) de uma empresa em um único PDF, na ordem
cronológica de lavratura, intercalando cada auto com seu anexo (pasta AX_<nº>).

Uso:
    python reune_autos_pdf.py <NOME_EMPRESA> <CNPJ_OU_8DIGITOS> <SAIDA.pdf>
                              [--pasta-pro PASTA] [--paginas-anexo N]

  <CNPJ_OU_8DIGITOS>: CNPJ (14) ou CPF/CAEPF (11) do autuado; bastam os 8
  primeiros dígitos — toda pasta criada pelo Sistema Auditor termina com eles.
  <SAIDA.pdf>: caminho do PDF final (a pasta é criada se não existir).
  --pasta-pro: pasta "PRO" do Sistema Auditor, se a instalação for fora do
  padrão. Sem ela, usa SISTEMA_AUDITOR_PRO, depois procura o disco do Parallels
  em /Volumes/*/SistemasAFT/... (Mac) e por fim o padrão do Windows.
  --paginas-anexo: se maior que zero, limita o anexo de CADA auto a N páginas
  (o corte fica registrado no JSON). Padrão 0 = anexo entra inteiro.

Montagem: AI + anexo, AI + anexo... do auto mais antigo ao mais novo (a
numeração do AI é crescente no tempo). Exceção: autos de JORNADA (ementas de
excesso de jornada, intervalos, AFD/AEJ e atestado do REP — anexos volumosos)
vão para o FIM do arquivo, na ordem cronológica entre si. Dentro do anexo, os
PDFs entram em ordem alfabética. Ao final o arquivo é comprimido (Ghostscript
/ebook se houver; senão pikepdf) e a versão menor é mantida.

Read-only sobre o Sistema Auditor: nada é gravado nem alterado na pasta PRO.
Saída: JSON em stdout com o resumo da montagem.
"""
from __future__ import annotations

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
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unicodedata
from pathlib import Path

PADRAO_PRO_WINDOWS = r"C:\SistemasAFT\Auditor\Docs\AutosDeInfracao\PRO"
RE_AI_NOME = re.compile(r"AI_(\d{9})")
RE_EMENTA_ROTULO = re.compile(r"Ementa:\s*(\d{7})")
RE_EMENTA_NUM = re.compile(r"(\d{6}-\d)")

# Ementas de JORNADA — autos que costumam carregar anexos volumosos (relatórios
# de ponto por empregado) e por isso vão para o fim do PDF reunido:
#   000017-5 excesso de jornada semanal · 000018-3 excesso de jornada diária ·
#   000035-3 intervalo interjornada · 000044-2 intervalo intrajornada ·
#   001008-1 intervalo do art. 384/71 · 002277-2 e 002278-0 atestado REP ·
#   002279-9 AFD (art. 81 Port. 671) · 002280-2 AEJ (art. 83, I Port. 671).
EMENTAS_JORNADA = {
    "000017-5", "000018-3", "000035-3", "000044-2", "001008-1",
    "002277-2", "002278-0", "002279-9", "002280-2",
}


def numero_ai_formatado(digitos9: str) -> str:
    d = digitos9
    return f"{d[0:2]}.{d[2:5]}.{d[5:8]}-{d[8]}"


def mac_parallels_pro():
    """Em Mac com Parallels, o disco C: do Windows aparece montado em
    /Volumes/<nome>/. Procura a pasta PRO sob qualquer volume montado."""
    if sys.platform != "darwin":
        return None
    from glob import glob as _glob
    padrao = "/Volumes/*/SistemasAFT/Auditor/Docs/AutosDeInfracao/PRO"
    for cand in sorted(_glob(padrao)):
        p = Path(cand)
        if p.is_dir():
            return p
    return None


def base_pro(arg_pasta: str | None) -> Path:
    if arg_pasta:
        return Path(arg_pasta)
    env = os.environ.get("SISTEMA_AUDITOR_PRO")
    if env:
        return Path(env)
    mac = mac_parallels_pro()
    if mac is not None:
        return mac
    return Path(PADRAO_PRO_WINDOWS)


def strip_accents(s: str) -> str:
    nfkd = unicodedata.normalize("NFKD", s)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def sanitize_for_match(nome: str) -> str:
    """Replica o saneamento que o Sistema Auditor aplica no nome da pasta."""
    s = strip_accents(nome).upper()
    s = re.sub(r"[.,;:'\"()/\\&]", "", s)
    s = re.sub(r"\s+", "_", s.strip())
    return s


def find_pasta_auditor(base: Path, empresa: str, cnpj14: str):
    """Mesma estratégia do scan_autos.py (aft-autos-lavrados): primeiro a raiz
    do CNPJ (8 dígitos como sufixo), depois o prefixo do nome sanitizado."""
    if not base.exists():
        return None, "nao_encontrado", []
    try:
        subdirs = [p for p in base.iterdir() if p.is_dir()]
    except (PermissionError, OSError):
        return None, "nao_encontrado", []

    if len(cnpj14) >= 8:
        raiz = cnpj14[:8]
        cands = [p for p in subdirs if p.name.endswith(f"_{raiz}")]
        if len(cands) == 1:
            return cands[0], "cnpj_raiz", []
        if len(cands) > 1:
            return None, "nao_encontrado", sorted(p.name for p in cands)

    for tamanho in (16, 12):
        prefixo = sanitize_for_match(empresa)[:tamanho]
        if not prefixo:
            continue
        cands = [p for p in subdirs if p.name.startswith(prefixo)]
        if len(cands) == 1:
            return cands[0], "nome_prefixo", []
        if len(cands) > 1:
            return None, "nao_encontrado", sorted(p.name for p in cands)

    return None, "nao_encontrado", []


def list_pdf_autos(pasta: Path) -> list[Path]:
    """AI_*.PDF da raiz, do mais antigo ao mais novo (numeração crescente)."""
    try:
        files = [
            p for p in pasta.iterdir()
            if p.is_file()
            and p.name.upper().startswith("AI_")
            and p.suffix.upper() == ".PDF"
        ]
    except (PermissionError, OSError):
        return []

    def chave(p: Path):
        m = RE_AI_NOME.search(p.name)
        return (int(m.group(1)), p.name) if m else (float("inf"), p.name)
    return sorted(files, key=chave)


def list_pdf_anexos(pasta_ax: Path) -> list[Path]:
    """PDFs da pasta de anexo, em ordem alfabética (case-insensitive)."""
    try:
        files = [
            p for p in pasta_ax.iterdir()
            if p.is_file() and p.suffix.upper() == ".PDF"
        ]
    except (PermissionError, OSError):
        return []
    return sorted(files, key=lambda p: p.name.lower())


def extrair_ementa(reader) -> str | None:
    """Número da ementa do auto, no formato NNNNNN-N. Procura o rótulo
    'Ementa: NNNNNNN' (padrão do Sistema Auditor); em falta, o primeiro
    NNNNNN-N logo após 'EMENTA (Nº/Descrição):'. None se ilegível."""
    try:
        texto = "\n".join((p.extract_text() or "") for p in reader.pages)
    except Exception:
        return None
    m = RE_EMENTA_ROTULO.search(texto)
    if m:
        d = m.group(1)
        return f"{d[:6]}-{d[6]}"
    i = texto.find("EMENTA (Nº/Descrição):")
    if i >= 0:
        m = RE_EMENTA_NUM.search(texto[i:i + 400])
        if m:
            return m.group(1)
    return None


def abrir_pdf(caminho: Path):
    """Abre o PDF com pypdf; devolve (reader, None) ou (None, motivo)."""
    from pypdf import PdfReader
    try:
        reader = PdfReader(str(caminho))
        if reader.is_encrypted:
            try:
                reader.decrypt("")
            except Exception:
                return None, "PDF protegido por senha"
        _ = len(reader.pages)
        return reader, None
    except Exception as e:
        return None, f"leitura falhou ({type(e).__name__})"


def comprimir(entrada: Path, saida: Path) -> str:
    """Comprime o PDF final. Ghostscript /ebook se houver; senão pikepdf; se
    nada disponível ou o resultado sair maior, mantém o original. Retorna o
    rótulo do método efetivamente usado."""
    gs = next((e for e in ("gs", "gswin64c", "gswin32c") if shutil.which(e)), None)
    if gs:
        tmp = Path(tempfile.NamedTemporaryFile(suffix=".pdf", delete=False).name)
        try:
            subprocess.run(
                [gs, "-sDEVICE=pdfwrite", "-dCompatibilityLevel=1.4",
                 "-dPDFSETTINGS=/ebook", "-dNOPAUSE", "-dQUIET", "-dBATCH",
                 f"-sOutputFile={tmp}", str(entrada)],
                check=True, timeout=600,
            )
            if tmp.stat().st_size < entrada.stat().st_size:
                shutil.move(str(tmp), str(saida))
                return "ghostscript /ebook"
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError):
            pass
        finally:
            if tmp.exists():
                tmp.unlink()
    else:
        try:
            import pikepdf
            tmp = Path(tempfile.NamedTemporaryFile(suffix=".pdf", delete=False).name)
            with pikepdf.open(str(entrada)) as pdf:
                pdf.save(str(tmp), compress_streams=True, recompress_flate=True,
                         object_stream_mode=pikepdf.ObjectStreamMode.generate)
            if tmp.stat().st_size < entrada.stat().st_size:
                shutil.move(str(tmp), str(saida))
                return "pikepdf"
            tmp.unlink()
        except ImportError:
            pass
        except Exception:
            pass
    shutil.move(str(entrada), str(saida))
    return "sem compressao (original ja menor ou compressor indisponivel)"


def main() -> int:
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument("empresa")
    ap.add_argument("identificador")
    ap.add_argument("saida")
    ap.add_argument("--pasta-pro", default=None)
    ap.add_argument("--paginas-anexo", type=int, default=0)
    try:
        args = ap.parse_args()
    except SystemExit:
        print("Uso: reune_autos_pdf.py <NOME_EMPRESA> <CNPJ_OU_8DIGITOS> <SAIDA.pdf> "
              "[--pasta-pro PASTA] [--paginas-anexo N]", file=sys.stderr)
        return 2

    cnpj14 = re.sub(r"\D", "", args.identificador)
    base = base_pro(args.pasta_pro)
    saida = Path(args.saida).expanduser()

    result: dict = {
        "empresa": args.empresa,
        "cnpj": cnpj14,
        "pasta_pro": str(base),
        "pasta_auditor": None,
        "match_estrategia": "nao_encontrado",
        "candidatos_alternativos": [],
        "saida": str(saida),
        "paginas_anexo_limite": args.paginas_anexo if args.paginas_anexo > 0 else None,
        "autos": [],
        "autos_jornada_no_fim": [],
        "anexos_orfaos": [],
        "total_autos": 0,
        "total_paginas": 0,
        "tamanho_mb": None,
        "compressao": None,
        "errors": [],
    }

    def falha(msg: str) -> int:
        result["errors"].append(msg)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if len(cnpj14) < 8:
        return falha("Identificador insuficiente: informe o CNPJ (14 dig.), o "
                     "CPF/CAEPF (11 dig.) ou ao menos os 8 primeiros digitos. "
                     f"Recebido: {cnpj14!r}")

    try:
        from pypdf import PdfWriter  # noqa: F401
    except ImportError:
        return falha("pypdf ausente. Instale com: pip install pypdf "
                     "(o /aft-setup ja faz isso)")

    if not base.exists():
        return falha(f"Pasta do Sistema Auditor nao encontrada em {base}. "
                     "Confirme a instalacao ou informe --pasta-pro.")

    pasta, estrategia, alternativos = find_pasta_auditor(base, args.empresa, cnpj14)
    result["match_estrategia"] = estrategia
    result["candidatos_alternativos"] = alternativos
    if pasta is None:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    result["pasta_auditor"] = str(pasta)

    pdfs = list_pdf_autos(pasta)
    if not pdfs:
        return falha(f"Nenhum AI_*.PDF encontrado em {pasta}")

    from pypdf import PdfWriter
    writer = PdfWriter()
    pagina_atual = 0
    numeros_ai = set()

    # 1º passe: abre cada auto, lê a ementa e separa os de jornada (anexos
    # volumosos), que vão para o fim — cronológicos entre si.
    comuns, jornada = [], []
    for pdf in pdfs:
        m = RE_AI_NOME.search(pdf.name)
        digitos = m.group(1) if m else None
        reader, erro = abrir_pdf(pdf)
        ementa = extrair_ementa(reader) if reader is not None else None
        item = (pdf, digitos, reader, erro, ementa)
        if ementa in EMENTAS_JORNADA:
            jornada.append(item)
        else:
            comuns.append(item)

    result["autos_jornada_no_fim"] = [
        numero_ai_formatado(d) if d else p.name for p, d, *_ in jornada]

    # 2º passe: monta o PDF na ordem final.
    for pdf, digitos, reader, erro, ementa in comuns + jornada:
        info: dict = {
            "arquivo": pdf.name,
            "numero_ai": numero_ai_formatado(digitos) if digitos else None,
            "ementa_num": ementa,
            "jornada": ementa in EMENTAS_JORNADA,
            "paginas_auto": 0,
            "anexos": [],
            "anexo_cortado": False,
            "warnings": [],
        }
        result["autos"].append(info)

        if reader is None:
            info["warnings"].append(f"auto pulado: {erro}")
            continue
        inicio = pagina_atual
        writer.append(reader, import_outline=False)
        info["paginas_auto"] = len(reader.pages)
        pagina_atual += len(reader.pages)
        marcador = writer.add_outline_item(
            f"AI {info['numero_ai'] or pdf.name}", inicio)

        if not digitos:
            continue
        numeros_ai.add(digitos)
        pasta_ax = pasta / f"AX_{digitos}"
        if not pasta_ax.is_dir():
            continue
        sem_limite = args.paginas_anexo <= 0
        restante = args.paginas_anexo
        for anexo in list_pdf_anexos(pasta_ax):
            ax_info = {"arquivo": anexo.name, "paginas_total": None,
                       "paginas_incluidas": 0}
            info["anexos"].append(ax_info)
            r2, erro2 = abrir_pdf(anexo)
            if r2 is None:
                info["warnings"].append(f"anexo {anexo.name} pulado: {erro2}")
                continue
            ax_info["paginas_total"] = len(r2.pages)
            if not sem_limite and restante <= 0:
                info["anexo_cortado"] = True
                continue
            incluir = len(r2.pages) if sem_limite else min(len(r2.pages), restante)
            writer.append(r2, pages=(0, incluir), import_outline=False)
            writer.add_outline_item(f"Anexo: {anexo.name}", pagina_atual,
                                    parent=marcador)
            ax_info["paginas_incluidas"] = incluir
            pagina_atual += incluir
            if not sem_limite:
                restante -= incluir
            if incluir < len(r2.pages):
                info["anexo_cortado"] = True

    # Pastas AX_ sem AI correspondente (informativo, nao entram no PDF).
    try:
        for d in pasta.iterdir():
            if d.is_dir() and re.fullmatch(r"AX_(\d{9})", d.name):
                if d.name[3:] not in numeros_ai:
                    result["anexos_orfaos"].append(d.name)
    except (PermissionError, OSError):
        pass

    if pagina_atual == 0:
        return falha("Nenhuma pagina montada: todos os PDFs falharam na leitura.")

    saida.parent.mkdir(parents=True, exist_ok=True)
    bruto = Path(tempfile.NamedTemporaryFile(suffix=".pdf", delete=False).name)
    with open(bruto, "wb") as f:
        writer.write(f)

    result["compressao"] = comprimir(bruto, saida)
    result["total_autos"] = sum(1 for a in result["autos"] if a["paginas_auto"] > 0)
    result["total_paginas"] = pagina_atual
    result["tamanho_mb"] = round(saida.stat().st_size / (1024 * 1024), 2)

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
