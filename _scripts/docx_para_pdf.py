#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
docx_para_pdf.py — converte um .docx em .pdf preservando o visual, usando o que
a máquina do AFT já tem instalado. Ponto único do toolkit para essa conversão.

Ordem de tentativa:

  1. LibreOffice (`soffice --headless --convert-to pdf`) — multiplataforma,
     sem diálogo nenhum. É a primeira opção quando está instalado.
  2. Microsoft Word, no Windows, por automação COM dirigida pelo PowerShell.
     Cobre a máquina típica do AFT: Word instalado, LibreOffice não.

Sobre a segunda: o toolkit NÃO usa a biblioteca `docx2pdf` de propósito — ela
chama `sys.exit(1)` por dentro quando a automação do Word falha, derrubando o
processo Python inteiro em vez de deixar o erro ser tratado. O PowerShell já
fala COM nativamente, então a falha volta como código de saída comum, tratável
— e sem exigir a instalação do `pywin32`.

No macOS o Word não é tentado: a automação exige a permissão de Automação do
sistema, que num terminal costuma vir negada e trava esperando o diálogo.

Uso:
    python docx_para_pdf.py <arquivo.docx> [saida.pdf]
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

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

TIMEOUT_SOFFICE = 90
TIMEOUT_WORD = 180

# Mensagem única para quando nenhum motor serve — a skill repassa ao AFT.
INSTRUCAO_MANUAL = (
    "Abra o {arquivo} no Word, confira os dados e use "
    "Arquivo > Salvar como... > formato PDF para gerar o PDF manualmente."
)


def _via_soffice(docx: Path, pdf: Path) -> bool:
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if not soffice:
        return False
    try:
        with tempfile.TemporaryDirectory() as tmp:
            subprocess.run(
                [soffice, "--headless", "--convert-to", "pdf", "--outdir", tmp, str(docx)],
                check=True, timeout=TIMEOUT_SOFFICE, capture_output=True,
            )
            gerado = Path(tmp) / (docx.stem + ".pdf")
            if gerado.exists():
                pdf.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy(gerado, pdf)
                return True
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError):
        pass
    return False


def _ps_aspas(s: str) -> str:
    """Escapa para dentro de aspas simples do PowerShell (dobra aspas simples)."""
    return "'" + str(s).replace("'", "''") + "'"


# wdFormatPDF = 17 (o mesmo valor serve para SaveAs2 e ExportAsFixedFormat).
_PS_WORD = """$ErrorActionPreference = 'Stop'
$docx = {docx}
$pdf  = {pdf}
$code = 1
$word = $null
try {{
    $word = New-Object -ComObject Word.Application
    $word.Visible = $false
    $word.DisplayAlerts = 0
    $doc = $word.Documents.Open($docx, $false, $true)
    try {{ $doc.SaveAs2($pdf, 17) }} catch {{ $doc.ExportAsFixedFormat($pdf, 17) }}
    $doc.Close(0)
    $code = 0
}} catch {{
    Write-Output ('ERRO: ' + $_.Exception.Message)
}} finally {{
    if ($word -ne $null) {{ try {{ $word.Quit() }} catch {{ }} }}
}}
exit $code
"""


def _matar_word_de_automacao() -> None:
    """Só depois de um timeout: encerra a instância INVISÍVEL do Word que a
    automação abriu (linha de comando com -Embedding). Nunca toca no Word que
    o AFT esteja usando na tela."""
    try:
        subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command",
             "Get-CimInstance Win32_Process -Filter \"Name='WINWORD.EXE'\" | "
             "Where-Object { $_.CommandLine -like '*-Embedding*' } | "
             "ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }"],
            capture_output=True, timeout=30)
    except Exception:
        pass


def _via_word(docx: Path, pdf: Path) -> bool:
    if not sys.platform.startswith("win"):
        return False
    script = _PS_WORD.format(docx=_ps_aspas(docx.resolve()), pdf=_ps_aspas(pdf.resolve()))
    ps1 = None
    try:
        pdf.parent.mkdir(parents=True, exist_ok=True)
        # O script vai para um arquivo .ps1 em UTF-8 COM BOM em vez de ir na
        # linha de comando: e assim que caminho com acento (Interdicao, Serviços)
        # chega inteiro ao PowerShell 5.1, sem virar mojibake.
        with tempfile.NamedTemporaryFile("w", suffix=".ps1", delete=False,
                                         encoding="utf-8-sig") as fh:
            fh.write(script)
            ps1 = Path(fh.name)
        r = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive",
             "-ExecutionPolicy", "Bypass", "-File", str(ps1)],
            capture_output=True, text=True, timeout=TIMEOUT_WORD, errors="replace")
        return r.returncode == 0 and pdf.exists()
    except subprocess.TimeoutExpired:
        _matar_word_de_automacao()
        return False
    except OSError:
        return False
    finally:
        if ps1 is not None:
            try:
                ps1.unlink()
            except OSError:
                pass


def converter(docx, pdf=None) -> tuple[Path, str]:
    """Converte e devolve (caminho_do_pdf, motor). Levanta RuntimeError com a
    orientação manual se nenhum motor estiver disponível nesta máquina."""
    docx = Path(docx)
    pdf = Path(pdf) if pdf else docx.with_suffix(".pdf")
    if not docx.is_file():
        raise RuntimeError(f"arquivo não encontrado: {docx}")

    if _via_soffice(docx, pdf):
        return pdf, "LibreOffice"
    if _via_word(docx, pdf):
        return pdf, "Word"

    tem_word = sys.platform.startswith("win")
    raise RuntimeError(
        "PDF não gerado automaticamente: "
        + ("nem o LibreOffice nem o Word conseguiram converter nesta máquina "
           "(o Word pode não estar instalado, ou a conversão falhou)."
           if tem_word else
           "o LibreOffice (soffice) não está instalado ou a conversão falhou.")
        + " " + INSTRUCAO_MANUAL.format(arquivo=docx.name)
    )


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    docx = Path(sys.argv[1]).expanduser()
    pdf = Path(sys.argv[2]).expanduser() if len(sys.argv) > 2 else None
    try:
        saida, motor = converter(docx, pdf)
    except RuntimeError as e:
        print(f"AVISO: {e}")
        return 1
    print(f"OK pdf: {saida} (via {motor})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
