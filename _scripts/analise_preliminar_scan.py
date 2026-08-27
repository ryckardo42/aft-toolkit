# -*- coding: utf-8 -*-
"""
analise_preliminar_scan.py — inventário determinístico do pacote de uma
notificação DET, para a skill /aft-analise-preliminar.

SOMENTE LEITURA: não move, não renomeia, não apaga nada. O pacote é o que a
/aft-det-baixar gravou e a estrutura por dia de entrega é informação de prova
(entrega parcelada tem prazos diversos) — por isso este script, ao contrário do
antecessor pessoal (scan_items.py, pré-toolkit), não tem fase de "flatten".

O que ele faz, por pacote NOTIFICACOES/<NN> - <CODIGO> <dd-mm-aaaa>/:
  a. Varre cada subpasta "baixada em <dd-mm-aaaa>/" (um dia de download) e,
     dentro dela, cada pasta item<N>_<descrição>.
  b. Para cada arquivo: SHA-256, tipo lógico (pdf, jornada_afd, jornada_aej,
     txt, docx, xlsx, xls, imagem, zip, outro) e tamanho. Arquivo dentro de
     invalidados/ (rejeitado/dispensado pelo AFT no DET) entra no inventário
     marcado, mas não conta como entrega válida.
  c. Duplicatas: mesmo SHA-256 aparecendo 2+ vezes entre arquivos válidos
     (entre itens diferentes ou entre dias diferentes).
  d. Layout antigo (pastas item<N> na raiz do pacote, sem subpasta de dia):
     inventariado como o dia "(layout antigo)".
  e. JSON no stdout, ou em arquivo com --saida (inventário grande estoura a
     tela; prefira --saida).

Uso:
    python analise_preliminar_scan.py "<pasta do pacote da notificação>"
    python analise_preliminar_scan.py "<pacote>" --saida "<arquivo.json>"

Códigos de saída:
    0 — sucesso
    1 — pasta inválida
    9 — erro de I/O
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

# Console do Windows costuma ser cp1252: força UTF-8 com substituição.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

ITEM_RE = re.compile(r"^item(\d+)[_ ]?(.*)$", re.IGNORECASE)
DIA_RE = re.compile(r"^baixada em (\d{2}-\d{2}-\d{4})$", re.IGNORECASE)

# Limiar de "item volumoso" num dia: a partir daqui a skill não lê arquivo por
# arquivo — amostra e devolve PRECISA AUDITORIA AFT. Uma fonte só, aqui.
VOLUMOSO_N_ANALISAVEIS = 5
VOLUMOSO_MB = 5.0
ANALISAVEIS = {"pdf", "txt", "docx"}


def classify(filename: str) -> str:
    """Tipo lógico de um arquivo a partir do nome."""
    lower = filename.lower()
    ext = Path(lower).suffix.lstrip(".")
    if ext == "pdf":
        return "pdf"
    if ext == "txt":
        if "afd" in lower:
            return "jornada_afd"
        if "aej" in lower:
            return "jornada_aej"
        return "txt"
    if ext in {"docx", "xlsx", "xls", "zip"}:
        return ext
    if ext in {"jpg", "jpeg", "png"}:
        return "imagem"
    return "outro"


def sha256_of(path: Path, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for blob in iter(lambda: f.read(chunk), b""):
            h.update(blob)
    return h.hexdigest()


def inventariar_arquivos(pasta: Path, invalidado: bool) -> list[dict]:
    """Arquivos no nível raiz de `pasta` (sem recursão além de invalidados/)."""
    out = []
    for entry in sorted(pasta.iterdir(), key=lambda p: p.name.lower()):
        if entry.is_dir():
            continue
        try:
            size = entry.stat().st_size
        except OSError:
            continue
        out.append({
            "nome": entry.name,
            "tipo": classify(entry.name),
            "sha256": sha256_of(entry),
            "tamanho_kb": round(size / 1024, 1),
            "invalidado": invalidado,
        })
    return out


def inventariar_item(item_dir: Path) -> dict:
    m = ITEM_RE.match(item_dir.name)
    numero = int(m.group(1)) if m else None
    descricao = (m.group(2) if m else item_dir.name).strip()

    arquivos = inventariar_arquivos(item_dir, invalidado=False)
    inval_dir = item_dir / "invalidados"
    if inval_dir.is_dir():
        arquivos += inventariar_arquivos(inval_dir, invalidado=True)

    validos = [a for a in arquivos if not a["invalidado"]]
    analisaveis = [a for a in validos if a["tipo"] in ANALISAVEIS]
    total_mb = round(sum(a["tamanho_kb"] for a in validos) / 1024, 2)
    return {
        "numero": numero,
        "descricao": descricao,
        "n_arquivos_validos": len(validos),
        "n_invalidados": len(arquivos) - len(validos),
        "n_analisaveis": len(analisaveis),
        "tamanho_total_mb": total_mb,
        "volumoso": (len(analisaveis) >= VOLUMOSO_N_ANALISAVEIS
                     or total_mb > VOLUMOSO_MB),
        "tipos_presentes": sorted({a["tipo"] for a in validos}),
        "arquivos": arquivos,
    }


def inventariar_dia(dia_dir: Path, rotulo: str) -> dict:
    itens = sorted(
        (inventariar_item(p) for p in dia_dir.iterdir()
         if p.is_dir() and ITEM_RE.match(p.name)),
        key=lambda it: (it["numero"] is None, it["numero"]),
    )
    relatorio = sorted(dia_dir.glob("relatorio-atendimento-*.pdf"))
    historico = dia_dir / "historico-itens.md"
    return {
        "dia": rotulo,
        "pasta": str(dia_dir),
        "relatorio_atendimento": str(relatorio[0]) if relatorio else None,
        "historico_itens": str(historico) if historico.is_file() else None,
        "itens": itens,
    }


def detectar_duplicatas(dias: list[dict]) -> list[dict]:
    """SHA-256 que aparece 2+ vezes entre arquivos VÁLIDOS, em qualquer
    combinação de item e dia."""
    bucket: dict[str, list[dict]] = {}
    for d in dias:
        for it in d["itens"]:
            for a in it["arquivos"]:
                if a["invalidado"]:
                    continue
                bucket.setdefault(a["sha256"], []).append({
                    "dia": d["dia"],
                    "item": it["numero"],
                    "nome": a["nome"],
                })
    dups = []
    for sha, occ in bucket.items():
        if len(occ) >= 2:
            dups.append({
                "sha256": sha,
                "exemplo_nome": occ[0]["nome"],
                "n_ocorrencias": len(occ),
                "itens_envolvidos": sorted({o["item"] for o in occ
                                            if o["item"] is not None}),
                "ocorrencias": occ,
            })
    dups.sort(key=lambda d: (-len(d["itens_envolvidos"]), -d["n_ocorrencias"]))
    return dups


def main(argv: list[str]) -> int:
    args = [a for a in argv[1:] if a != "--saida"]
    saida = None
    if "--saida" in argv:
        i = argv.index("--saida")
        if i + 1 >= len(argv):
            print("ERRO: --saida exige um caminho de arquivo.", file=sys.stderr)
            return 9
        saida = Path(argv[i + 1]).expanduser()
        args = [a for a in args if a != argv[i + 1]]
    if len(args) != 1:
        print("Uso: analise_preliminar_scan.py <pacote> [--saida arquivo.json]",
              file=sys.stderr)
        return 9

    pacote = Path(args[0]).expanduser().resolve()
    if not pacote.is_dir():
        print(f"ERRO: pasta não encontrada: {pacote}", file=sys.stderr)
        return 1

    # Código da notificação: token alfanumérico maiúsculo no nome do pacote
    # ("<NN> - <CODIGO> <dd-mm-aaaa>", ou legados "notificacao-<CODIGO>" etc.).
    nome = re.sub(r"^\d+\s*-\s*", "", pacote.name).replace("notificacao-", "", 1)
    m = re.search(r"[A-Z0-9]{8,}", nome.upper())
    codigo = m.group(0) if m else nome
    if not m:
        print(f"AVISO: não reconheci um código de notificação em "
              f"'{pacote.name}' — prosseguindo mesmo assim", file=sys.stderr)

    empresa_dir = pacote.parent
    if empresa_dir.name.upper() == "NOTIFICACOES":
        empresa_dir = empresa_dir.parent

    dias = []
    for sub in sorted(pacote.iterdir(), key=lambda p: p.name):
        if not sub.is_dir():
            continue
        dm = DIA_RE.match(sub.name)
        if dm:
            dias.append(inventariar_dia(sub, dm.group(1)))
    # Layout antigo: pastas item<N> direto na raiz do pacote.
    if any(p.is_dir() and ITEM_RE.match(p.name) for p in pacote.iterdir()):
        dias.append(inventariar_dia(pacote, "(layout antigo)"))
    # Ordena por data (dd-mm-aaaa -> aaaa-mm-dd); layout antigo primeiro.
    dias.sort(key=lambda d: ("-".join(reversed(d["dia"].split("-")))
                             if DIA_RE.match(f"baixada em {d['dia']}") or
                             re.match(r"^\d{2}-\d{2}-\d{4}$", d["dia"])
                             else ""))

    notificacao_pdf = sorted(pacote.glob("notificacao-*.pdf"))
    out = {
        "notificacao": codigo,
        "pacote": str(pacote),
        "empresa_dir": str(empresa_dir),
        "notificacao_pdf": str(notificacao_pdf[0]) if notificacao_pdf else None,
        "dias": dias,
        "duplicatas": detectar_duplicatas(dias),
    }

    texto = json.dumps(out, ensure_ascii=False, indent=2)
    if saida:
        try:
            saida.parent.mkdir(parents=True, exist_ok=True)
            saida.write_text(texto, encoding="utf-8")
        except OSError as e:
            print(f"ERRO de I/O ao gravar {saida}: {e}", file=sys.stderr)
            return 9
        n_itens = len({(it["numero"]) for d in dias for it in d["itens"]})
        print(f"Inventário gravado em: {saida}")
        print(f"Notificação {codigo}: {len(dias)} dia(s) de entrega, "
              f"{n_itens} item(ns) com pasta, "
              f"{len(out['duplicatas'])} duplicata(s).")
    else:
        print(texto)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
