#!/usr/bin/env python3
"""
inspecionar_assinatura.py

Inspeção ESTRUTURAL (não criptográfica) das assinaturas de um PDF de
Atestado Técnico e Termo de Responsabilidade (art. 89, Portaria MTP nº 671/2021).

O que este script FAZ:
- Detecta a presença de campos de assinatura (/FT /Sig) no AcroForm;
- Conta quantas assinaturas existem;
- Lê, de cada assinatura: SubFilter (indica PAdES vs. legada), nome do
  signatário (/Name), data declarada (/M) e tamanho do blob PKCS#7;
- Classifica o SubFilter para sinalizar se há INDÍCIO de padrão PAdES.

O que este script NÃO FAZ (limite deliberado):
- NÃO valida a cadeia de certificação ICP-Brasil;
- NÃO confirma que a assinatura é "qualificada" no sentido jurídico;
- NÃO verifica integridade criptográfica (hash do documento) nem carimbo
  de tempo. Isso exige validador externo (validar.iti.gov.br) e/ou rede.

Saída: JSON em stdout. Uso:
    python3 inspecionar_assinatura.py "/caminho/atestado.pdf"
"""

import json
import sys


# SubFilters relevantes. ETSI.* => família CAdES/PAdES (ETSI EN 319 142).
# adbe.* => assinaturas Adobe legadas (PKCS#7), NÃO são PAdES.
SUBFILTER_MAP = {
    "/ETSI.CAdES.detached": ("PAdES (CAdES detached)", True),
    "/ETSI.RFC3161": ("Carimbo de tempo de documento (DTS)", True),
    "/adbe.pkcs7.detached": ("Adobe PKCS#7 detached (legada, NÃO PAdES)", False),
    "/adbe.pkcs7.sha1": ("Adobe PKCS#7 SHA-1 (legada, NÃO PAdES)", False),
    "/adbe.x509.rsa_sha1": ("Adobe x509 RSA SHA-1 (legada, NÃO PAdES)", False),
}


def _str(v):
    if v is None:
        return None
    try:
        return str(v)
    except Exception:
        return None


def inspecionar(caminho):
    resultado = {
        "arquivo": caminho,
        "biblioteca_usada": None,
        "possui_acroform": False,
        "qtd_campos_assinatura": 0,
        "qtd_assinaturas_preenchidas": 0,
        "assinaturas": [],
        "indicio_pades": False,
        "observacoes": [],
        "erro": None,
    }

    try:
        import pikepdf
    except ImportError:
        resultado["erro"] = (
            "pikepdf não instalado. Instale com: pip install pikepdf"
        )
        return resultado

    resultado["biblioteca_usada"] = f"pikepdf {pikepdf.__version__}"

    try:
        pdf = pikepdf.open(caminho)
    except Exception as e:
        resultado["erro"] = f"Falha ao abrir o PDF: {e}"
        return resultado

    root = pdf.Root
    acroform = root.get("/AcroForm")
    if acroform is None:
        resultado["observacoes"].append(
            "Nenhum AcroForm encontrado: o PDF provavelmente não contém "
            "campos de assinatura digital embutidos."
        )
        pdf.close()
        return resultado

    resultado["possui_acroform"] = True

    sigflags = acroform.get("/SigFlags")
    if sigflags is not None:
        resultado["observacoes"].append(f"/SigFlags = {int(sigflags)}")

    fields = acroform.get("/Fields", [])
    for field in fields:
        try:
            ft = field.get("/FT")
        except Exception:
            continue
        if _str(ft) != "/Sig":
            continue

        resultado["qtd_campos_assinatura"] += 1

        nome_campo = _str(field.get("/T"))
        v = field.get("/V")

        if v is None:
            resultado["assinaturas"].append({
                "campo": nome_campo,
                "preenchida": False,
                "subfilter": None,
                "subfilter_descricao": None,
                "e_pades": None,
                "signatario": None,
                "data_declarada": None,
                "motivo": None,
                "tamanho_pkcs7_bytes": 0,
            })
            continue

        resultado["qtd_assinaturas_preenchidas"] += 1

        subfilter = _str(v.get("/SubFilter"))
        desc, e_pades = SUBFILTER_MAP.get(
            subfilter, (f"Desconhecido ({subfilter})", False)
        )
        if e_pades:
            resultado["indicio_pades"] = True

        contents = v.get("/Contents")
        tamanho = 0
        if contents is not None:
            try:
                tamanho = len(bytes(contents))
            except Exception:
                tamanho = 0

        resultado["assinaturas"].append({
            "campo": nome_campo,
            "preenchida": True,
            "subfilter": subfilter,
            "subfilter_descricao": desc,
            "e_pades": e_pades,
            "signatario": _str(v.get("/Name")),
            "data_declarada": _str(v.get("/M")),
            "motivo": _str(v.get("/Reason")),
            "tamanho_pkcs7_bytes": tamanho,
        })

    if resultado["qtd_campos_assinatura"] == 0:
        resultado["observacoes"].append(
            "AcroForm presente, porém sem campos de assinatura (/FT /Sig)."
        )

    pdf.close()
    return resultado


def main():
    if len(sys.argv) < 2:
        print(json.dumps(
            {"erro": "Uso: python3 inspecionar_assinatura.py <caminho.pdf>"},
            ensure_ascii=False,
        ))
        sys.exit(1)

    res = inspecionar(sys.argv[1])
    print(json.dumps(res, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
