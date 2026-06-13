#!/usr/bin/env python3
"""
scan_autos.py (AFT Toolkit / Windows) — varre o Sistema Auditor e extrai dados
estruturados dos autos lavrados (PDFs AI_*.PDF) de uma OS específica.

Uso:
    python scan_autos.py <NOME_EMPRESA> <CNPJ14> [PASTA_PRO]

  PASTA_PRO (opcional): pasta "PRO" do Sistema Auditor. Se omitida, usa a variável
  de ambiente SISTEMA_AUDITOR_PRO ou o padrão de instalação do Windows:
      C:\\SistemasAFT\\Auditor\\Docs\\AutosDeInfracao\\PRO

Saída: JSON em stdout (mesma estrutura da versão original do ecossistema).

Read-only sobre o Sistema Auditor. Extrai texto com pypdf (puro Python); se o
binário `pdftotext` (poppler) estiver no PATH, usa-o (fidelidade maior).
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import unicodedata
from pathlib import Path

PADRAO_PRO_WINDOWS = r"C:\SistemasAFT\Auditor\Docs\AutosDeInfracao\PRO"

RE_AI_NUM = re.compile(r"AUTO DE INFRAÇÃO Nº\s+(\d{2}\.\d{3}\.\d{3}-\d)")
RE_EMENTA_NUM = re.compile(r"(\d{6}-\d)")
RE_DATA_LAVRATURA = re.compile(r"Data:\s*(\d{2}/\d{2}/\d{4})")
RE_CNPJ_AUTUADO = re.compile(r"CNPJ\s*:\s*(\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2})")
RE_RAZAO_SOCIAL = re.compile(r"Nome/Razão Social:\s*(.+?)\s*$", re.MULTILINE)


def base_pro() -> Path:
    if len(sys.argv) >= 4 and sys.argv[3].strip():
        return Path(sys.argv[3])
    env = os.environ.get("SISTEMA_AUDITOR_PRO")
    if env:
        return Path(env)
    return Path(PADRAO_PRO_WINDOWS)


def strip_accents(s: str) -> str:
    nfkd = unicodedata.normalize("NFKD", s)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def sanitize_for_match(nome: str) -> str:
    """Replica o saneamento que o Sistema Auditor aplica no nome da pasta:
    uppercase, sem acentos, espaços viram underscore, pontuação eliminada."""
    s = strip_accents(nome).upper()
    s = re.sub(r"[.,;:'\"()/\\&]", "", s)
    s = re.sub(r"\s+", "_", s.strip())
    return s


def find_pasta_auditor(base: Path, empresa: str, cnpj14: str):
    """Localiza a pasta do Sistema Auditor.
    Estratégia 1: raiz CNPJ (8 primeiros dígitos como sufixo).
    Estratégia 2: prefixo do nome sanitizado (16, depois 12 chars).
    Múltiplos candidatos -> (None, "nao_encontrado", [candidatos])."""
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


def pdf_to_text(pdf_path: Path) -> str:
    """Extrai texto do PDF. Prefere pdftotext (poppler) se disponível; senão pypdf."""
    if shutil.which("pdftotext"):
        try:
            proc = subprocess.run(
                ["pdftotext", "-layout", "-enc", "UTF-8", str(pdf_path), "-"],
                check=True, capture_output=True, timeout=30,
            )
            return proc.stdout.decode("utf-8", errors="replace")
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
            pass
    # Fallback puro-Python.
    try:
        from pypdf import PdfReader
    except ImportError:
        try:
            from PyPDF2 import PdfReader  # nome antigo do mesmo pacote
        except ImportError:
            return ""
    try:
        reader = PdfReader(str(pdf_path))
        return "\n".join((page.extract_text() or "") for page in reader.pages)
    except Exception:
        return ""


def parse_auto(text: str, pdf_path: Path) -> dict:
    warnings: list[str] = []
    out: dict = {
        "pdf": str(pdf_path),
        "numero_ai": None,
        "ementa_num": None,
        "ementa_descricao": None,
        "historico_raw": None,
        "data_lavratura": None,
        "cnpj_autuado": None,
        "razao_social_autuado": None,
        "warnings": warnings,
    }

    m = RE_AI_NUM.search(text)
    if m:
        out["numero_ai"] = m.group(1)
    else:
        warnings.append("Número do AI não encontrado")

    m_cnpj = RE_CNPJ_AUTUADO.search(text)
    if m_cnpj:
        out["cnpj_autuado"] = re.sub(r"\D", "", m_cnpj.group(1))

    m_rs = RE_RAZAO_SOCIAL.search(text)
    if m_rs:
        out["razao_social_autuado"] = m_rs.group(1).strip()

    ementa_idx = text.find("EMENTA (Nº/Descrição):")
    if ementa_idx == -1:
        warnings.append("Rótulo EMENTA não encontrado")
    else:
        hist_idx = text.find("HISTÓRICO:", ementa_idx)
        if hist_idx == -1:
            hist_idx = len(text)
        bloco_ementa = text[ementa_idx:hist_idx]
        m_num = RE_EMENTA_NUM.search(bloco_ementa)
        if m_num:
            out["ementa_num"] = m_num.group(1)
        else:
            warnings.append("Número de ementa não encontrado")
        if m_num:
            depois = bloco_ementa[m_num.end():]
        else:
            depois = bloco_ementa.split("EMENTA (Nº/Descrição):", 1)[-1]
        linhas = []
        for raw in depois.splitlines():
            s = raw.strip()
            if not s:
                continue
            if re.fullmatch(r"Ementa:\s*\d{7}", s):
                continue
            linhas.append(s)
        if linhas:
            out["ementa_descricao"] = " ".join(linhas).strip()
        else:
            warnings.append("Descrição da ementa vazia")

    hist_idx = text.find("HISTÓRICO:")
    if hist_idx == -1:
        warnings.append("Rótulo HISTÓRICO não encontrado")
    else:
        depois_hist = text[hist_idx + len("HISTÓRICO:"):]
        fim_idx = len(depois_hist)
        for marker in (
            "Observações:", "**Observações:**", "Observação:", "CAPITULAÇÃO:",
            "BASE LEGAL PARA PENALIDADE:", "ELEMENTOS DE CONVICÇÃO:",
        ):
            i = depois_hist.find(marker)
            if 0 <= i < fim_idx:
                fim_idx = i
        bruto = depois_hist[:fim_idx]
        linhas_lim = []
        for raw in bruto.splitlines():
            s = raw.rstrip()
            if not s.strip():
                if linhas_lim and linhas_lim[-1] != "":
                    linhas_lim.append("")
                continue
            if "CIF-AFT emitente:" in s:
                continue
            if "Documento gerado na versão" in s:
                continue
            if re.match(r"^\s*AI\s+Folha\s*$", s):
                continue
            if re.match(r"^\s*\d{9}\s*$", s):
                continue
            if re.match(r"^\s*nº\s+\d+/\d+\s+AUTO DE INFRAÇÃO Nº", s):
                continue
            if re.match(r"^\s*AI\s+\d+\s+Folha\s+nº\s+\d+/\d+", s):
                continue
            linhas_lim.append(s.strip())
        historico = "\n".join(linhas_lim).strip()
        historico = re.sub(r"\n\*\n", "\n\n", historico)
        historico = re.sub(r"\n\*+\n", "\n\n", historico)
        historico = re.sub(r"\n{3,}", "\n\n", historico)
        out["historico_raw"] = historico.strip() or None
        if not out["historico_raw"]:
            warnings.append("Histórico vazio após limpeza")

    m_data = RE_DATA_LAVRATURA.search(text)
    if m_data:
        out["data_lavratura"] = m_data.group(1)

    return out


def list_pdf_autos(pasta: Path) -> list[Path]:
    try:
        files = [
            p for p in pasta.iterdir()
            if p.is_file()
            and p.name.upper().startswith("AI_")
            and p.suffix.upper() == ".PDF"
        ]
    except (PermissionError, OSError):
        return []
    return sorted(files, key=lambda p: p.name)


def main() -> int:
    if len(sys.argv) < 3:
        print("Uso: scan_autos.py <NOME_EMPRESA> <CNPJ14> [PASTA_PRO]", file=sys.stderr)
        return 2

    empresa, cnpj14 = sys.argv[1], sys.argv[2]
    cnpj14 = re.sub(r"\D", "", cnpj14)
    base = base_pro()

    result: dict = {
        "empresa": empresa,
        "cnpj": cnpj14,
        "pasta_pro": str(base),
        "pasta_auditor": None,
        "match_estrategia": "nao_encontrado",
        "candidatos_alternativos": [],
        "autos": [],
        "errors": [],
    }

    if len(cnpj14) != 14:
        result["errors"].append(f"CNPJ inválido (esperados 14 dígitos): {cnpj14!r}")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if not base.exists():
        result["errors"].append(
            f"Pasta do Sistema Auditor não encontrada em {base}. Confirme que o "
            "Sistema Auditor está instalado neste computador. Se a instalação usa "
            "outro caminho, informe-o (a skill aceita um caminho alternativo)."
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    pasta, estrategia, alternativos = find_pasta_auditor(base, empresa, cnpj14)
    result["match_estrategia"] = estrategia
    result["candidatos_alternativos"] = alternativos

    if pasta is None:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    result["pasta_auditor"] = str(pasta)
    pdfs = list_pdf_autos(pasta)
    if not pdfs:
        result["errors"].append(f"Nenhum AI_*.PDF encontrado em {pasta}")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    for pdf in pdfs:
        text = pdf_to_text(pdf)
        if not text:
            result["autos"].append({
                "pdf": str(pdf), "numero_ai": None, "ementa_num": None,
                "ementa_descricao": None, "historico_raw": None,
                "data_lavratura": None, "cnpj_autuado": None,
                "razao_social_autuado": None,
                "warnings": ["extração de texto falhou — PDF ilegível ou pypdf ausente (pip install pypdf)"],
            })
            continue
        result["autos"].append(parse_auto(text, pdf))

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
