#!/usr/bin/env python3
"""
validar_txt.py — validacao pre-importacao do TXT do Sistema Auditor (skill /aft-gera-ai).

Confere o arquivo .txt ANTES de o AFT tentar importar no Sistema Auditor, pegando
em segundos os erros que, de outro modo, so apareceriam como "AI RECUSADO" la dentro
(ex.: CEP vazio, numero de campos errado, ementa malformada, anexo inexistente,
anexos de um auto somando mais de 10 MB).

Roda sobre o TXT REAL (latin-1) ja re-hidratado. Tambem aceita o .tokenized.txt
(UTF-8) para uma checagem estrutural antecipada — nesse caso campos com tokens
[[...]] sao tratados como preenchidos.

Uso:
    python validar_txt.py <arquivo.txt>

Saida: relatorio legivel. Exit 0 = tudo ok; exit 1 = ha erro que o Sistema Auditor
recusaria (lista cada AI problematico no mesmo estilo do aviso do sistema).
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

import os
import re
import sys

try:  # console do Windows (cp1252) nao deve derrubar o relatorio
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

TOKEN = re.compile(r"\[\[[A-Z0-9_]+\]\]")

# Subtitulos obrigatorios do texto_autuacao (campo 18) - com acento correto.
# O latin-1 final suporta acentuacao normalmente; nao ha motivo para tirar acento
# aqui. Ja aconteceu de um script de montagem escrever "FISCALIZACAO"/"OBSERVACOES"
# sem acento, ou descartar o subtitulo III inteiro por erro de regex na extracao -
# nenhum dos dois quebra o TXT (o Sistema Auditor aceita e importa normalmente),
# entao so aparece quando o AFT confere o auto ja importado. Pegamos aqui antes.
SUBTITULOS_OK = ["I - DA FISCALIZAÇÃO:", "II - IRREGULARIDADE:", "III - OBSERVAÇÕES:"]
# "IRREGULARIDADE" nao tem acento em portugues - so FISCALIZACAO e OBSERVACOES
# denunciam perda de acento (deveriam ser FISCALIZAÇÃO e OBSERVAÇÕES).
SUBTITULOS_SEM_ACENTO = re.compile(r"\b(FISCALIZACAO|OBSERVACOES)\s*:", re.IGNORECASE)
# "#13#10" que precede texto real (nao o marcador de linha em branco " . ") deve
# vir seguido de exatamente 8 espacos - e o recuo de paragrafo que indenta_quebras.py
# aplica. Sem ele, o Sistema Auditor mostra o subtitulo "I" com recuo (automatico,
# so na primeira linha do campo) e todo o resto colado na margem.
QUEBRA_SEM_RECUO = re.compile(r"#13#10(?! \. )(?!        )")

# O Sistema Auditor limita os anexos a 10 MB por AUTO DE INFRACAO, somando os
# anexos daquele auto — nao por arquivo. Estourou num auto, a importacao e recusada.
# O mesmo PDF anexado a varios autos e permitido: pesa 1 vez no orcamento de cada um.
LIMITE_ANEXOS_MB = 10.0

# Subtitulos fixos do texto de autuacao (campo 18), no formato romano da /aft-gera-ai.
# Defeito ja observado: o subtitulo sai DUPLICADO ("I - DA FISCALIZACAO:#13#10 . #13#10
# I - DA FISCALIZACAO:"), porque foi digitado de novo ao transcrever o autos.md. E erro
# de forma que aparece no auto impresso, entao reprova.
SUBTITULO = re.compile(
    r"\bI{1,3}\s*-\s*(?:DA\s+FISCALIZA[CÇ][AÃ]O|IRREGULARIDADE|"
    r"OBSERVA[CÇ][OÕ]ES)\s*:")

# Comprimento minimo para tratar linha repetida como defeito (evita alarme com "a)",
# numeros soltos e outras linhas curtas que podem legitimamente se repetir).
MIN_LINHA_REPETIDA = 10


def sem_acento(v):
    tab = str.maketrans("ÁÀÂÃÉÊÍÓÔÕÚÇ", "AAAAEEIOOOUC")
    return (v or "").translate(tab)


def chave_subtitulo(v):
    """Normaliza o subtitulo para comparacao: sem acento, espacos colapsados."""
    return re.sub(r"\s+", " ", sem_acento(v).upper()).strip()


def checar_texto_autuacao(texto, rotulo, erros):
    """Campo 18: subtitulo repetido e linha repetida logo em seguida."""
    contagem = {}
    for m in SUBTITULO.finditer(texto):
        k = chave_subtitulo(m.group(0))
        contagem[k] = contagem.get(k, 0) + 1
    for k, n in sorted(contagem.items()):
        if n > 1:
            erros.append(f"{rotulo} -> Erro: o subtitulo '{k}' aparece {n} vezes no texto "
                         f"do auto (campo 18); deve aparecer UMA unica vez. Duplicado, ele "
                         f"sai repetido no auto impresso. Apague a repeticao no "
                         f".tokenized.txt e rode indenta_quebras.py + rehydrate.py de novo.")

    # Padrao generico do mesmo erro: a linha volta identica logo depois, seja colada,
    # seja separada so pelo marcador de linha em branco `#13#10 . #13#10`.
    seg = [s.strip() for s in texto.split("#13#10")]
    ja_visto = set()
    for i, a in enumerate(seg[:-1]):
        if len(a) < MIN_LINHA_REPETIDA or a == "." or a in ja_visto:
            continue
        if seg[i + 1] == a:
            sep = "coladas"
        elif i + 2 < len(seg) and seg[i + 1] == "." and seg[i + 2] == a:
            sep = "separadas so por `#13#10 . #13#10`"
        else:
            continue
        ja_visto.add(a)
        if SUBTITULO.fullmatch(a):
            continue  # ja reportado como subtitulo duplicado
        trecho = a if len(a) <= 60 else a[:60] + "..."
        erros.append(f"{rotulo} -> Erro: linha repetida duas vezes seguidas no texto do "
                     f"auto (campo 18), {sep}: \"{trecho}\". Apague a repeticao no "
                     f".tokenized.txt e rode indenta_quebras.py + rehydrate.py de novo.")


def is_filled(v):
    """Campo preenchido: nao-vazio ou contendo token (sera re-hidratado)."""
    return bool(v and (v.strip() or TOKEN.search(v)))


def only_digits(v):
    return re.sub(r"\D", "", v or "")


def resolver_anexo(anexo):
    """Devolve o caminho local do anexo (ou None se nao existir). O TXT carrega o
    path Windows absoluto (exigencia do Sistema Auditor). Em macOS/Linux esse path
    nunca existe literalmente: traduz o prefixo `path_windows` do aft-config.md
    para a pasta AFT local antes de checar."""
    if os.path.isfile(anexo):
        return anexo
    if os.name == "nt":
        return None
    try:
        from pasta_aft import pasta_aft, pasta_os_ativas
        base = str(pasta_aft())
        pw = None
        with open(os.path.join(base, "aft-config.md"), encoding="utf-8") as f:
            for linha in f:
                m = re.match(r'\s*path_windows:\s*"?([^"#]+?)"?\s*(#.*)?$', linha)
                if m:
                    pw = m.group(1).strip().replace("\\\\", "\\")
                    break
        if not pw or not anexo.lower().startswith(pw.lower()):
            return None
        resto = anexo[len(pw):].replace("\\", "/")
        if os.path.isfile(base + resto):
            return base + resto
        # `pasta_os:` pode redirecionar OS ATIVAS para fora da pasta AFT
        if resto.lower().startswith("/os ativas/"):
            alt = str(pasta_os_ativas()) + resto[len("/OS ATIVAS"):]
            if os.path.isfile(alt):
                return alt
    except Exception:
        return None
    return None


def main():
    if len(sys.argv) != 2:
        print("uso: python validar_txt.py <arquivo.txt>", file=sys.stderr)
        sys.exit(2)

    path = sys.argv[1]
    if not os.path.isfile(path):
        print(f"ERRO: arquivo nao encontrado: {path}", file=sys.stderr)
        sys.exit(2)

    # TXT real do Sistema Auditor e latin-1; o tokenizado e UTF-8. Tentamos os dois.
    raw = open(path, "rb").read()
    try:
        text = raw.decode("utf-8-sig")  # remove BOM se houver
    except UnicodeDecodeError:
        text = raw.decode("latin-1")
    text = text.lstrip("﻿")

    # Cada caractere precisa caber em latin-1 (o Sistema Auditor so aceita esse encoding).
    erros = []
    avisos = []
    for i, ch in enumerate(text):
        try:
            ch.encode("latin-1")
        except UnicodeEncodeError:
            ctx = text[max(0, i - 15):i + 15].replace("\n", " ")
            erros.append(f"Caractere fora do latin-1 (pos {i}): ...{ctx}... "
                         f"(troque travessao/aspas curvas/emoji por equivalente simples)")
            break

    linhas = [l for l in text.split("\n") if l != ""]
    if not linhas:
        print("ERRO: arquivo vazio.", file=sys.stderr)
        sys.exit(1)

    n_tipo1 = 0
    n_tipo6 = 0
    # anexos agrupados por auto: [(rotulo, [(anexo, caminho_local_ou_None), ...]), ...]
    anexos_por_auto = []
    anexos_do_auto = None
    bloco_atual = None  # (cnpj, ementa) para rotular erros do AI corrente

    for ln, linha in enumerate(linhas, start=1):
        campos = linha.split("\t")
        tipo = campos[0]

        if tipo == "1":
            n_tipo1 += 1
            ident = only_digits(campos[1]) if len(campos) > 1 else ""
            ementa = campos[12] if len(campos) > 12 else "?"
            bloco_atual = (ident or "?", ementa)
            rotulo = f"AI CNPJ/CPF:{ident or '?'} Ementa:{ementa}"
            anexos_do_auto = []
            anexos_por_auto.append((rotulo, anexos_do_auto))

            if len(campos) != 23:
                erros.append(f"{rotulo} -> linha tipo 1 com {len(campos)} campos "
                             f"(esperado 23 / 22 tabs).")
            # Identificador: 11 (CPF/CAEPF) ou 14 (CNPJ) digitos.
            if len(ident) not in (11, 14):
                erros.append(f"{rotulo} -> Erro: identificador CNPJ/CPF invalido "
                             f"('{campos[1] if len(campos)>1 else ''}'): "
                             f"deve ter 11 (CPF/CAEPF) ou 14 (CNPJ) digitos.")
            # Razao social (campo 3).
            if len(campos) > 2 and not is_filled(campos[2]):
                erros.append(f"{rotulo} -> Erro: razao social/nome nao informado!")
            # CEP (campo 8) — causa classica de 'AI RECUSADO'.
            if len(campos) > 7 and not is_filled(campos[7]):
                erros.append(f"{rotulo} -> Erro: CEP nao informado! AI seria RECUSADO.")
            # Ementa sem hifen (campo 13 / cod_3): 7 digitos.
            if len(campos) > 12:
                cod3 = campos[12]
                if not re.fullmatch(r"\d{7}", cod3):
                    erros.append(f"{rotulo} -> Erro: codigo de ementa '{cod3}' invalido "
                                 f"(esperado 7 digitos, ementa sem hifen).")
            # Texto do auto (campo 18): subtitulo/linha duplicados.
            if len(campos) > 17:
                checar_texto_autuacao(campos[17], rotulo, erros)

            # texto_autuacao (campo 18): subtitulos I/II/III presentes e acentuados,
            # e recuo de paragrafo aplicado (indenta_quebras.py ja rodado).
            if len(campos) > 17:
                texto = campos[17]
                faltando = [s for s in SUBTITULOS_OK if s not in texto]
                if faltando:
                    erros.append(f"{rotulo} -> Erro: subtitulo(s) ausente(s) ou sem acento "
                                 f"correto no texto_autuacao: {', '.join(faltando)}. Confira "
                                 f"se a extracao do bloco III do autos.md descartou o "
                                 f"cabecalho, ou se o script de montagem escreveu o rotulo "
                                 f"sem acento.")
                sem_acento = SUBTITULOS_SEM_ACENTO.findall(texto)
                if sem_acento:
                    erros.append(f"{rotulo} -> Erro: subtitulo(s) sem acento no texto_autuacao: "
                                 f"{', '.join(sorted(set(sem_acento)))}. O latin-1 aceita "
                                 f"acento normalmente - corrija o script de montagem.")
                if QUEBRA_SEM_RECUO.search(texto):
                    avisos.append(f"{rotulo} -> recuo de paragrafo nao aplicado no "
                                  f"texto_autuacao (rode indenta_quebras.py sobre o "
                                  f"tokenized.txt antes de re-hidratar).")

        elif tipo == "2":
            rotulo = (f"AI CNPJ/CPF:{bloco_atual[0]} Ementa:{bloco_atual[1]}"
                      if bloco_atual else f"linha {ln}")
            # Layout oficial: se a linha tipo 2 existir, os 3 campos sao obrigatorios.
            if len(campos) != 3 or not campos[1].strip() or not campos[2].strip():
                erros.append(f"{rotulo} -> linha tipo 2 (informacao complementar) "
                             f"malformada (esperado 2[TAB]codigo[TAB]valor).")

        elif tipo == "5":
            rotulo = (f"AI CNPJ/CPF:{bloco_atual[0]} Ementa:{bloco_atual[1]}"
                      if bloco_atual else f"linha {ln}")
            if len(campos) < 3:
                erros.append(f"{rotulo} -> linha tipo 5 (anexo) malformada "
                             f"({len(campos)} campos, esperado 3).")
            else:
                anexo = campos[1]
                local = None if TOKEN.search(anexo) else resolver_anexo(anexo)
                if anexos_do_auto is None:  # linha tipo 5 antes de qualquer tipo 1
                    anexos_do_auto = []
                    anexos_por_auto.append((rotulo, anexos_do_auto))
                anexos_do_auto.append((anexo, local))
                if not TOKEN.search(anexo) and not local:
                    erros.append(f"{rotulo} -> Erro: anexo nao encontrado no disco: {anexo}")
                if not anexo.upper().endswith(".PDF"):
                    avisos.append(f"{rotulo} -> anexo nao termina em .PDF maiusculo: {anexo}")

        elif tipo == "4":
            rotulo = (f"AI CNPJ/CPF:{bloco_atual[0]} Ementa:{bloco_atual[1]}"
                      if bloco_atual else f"linha {ln}")
            if len(campos) < 5:
                erros.append(f"{rotulo} -> linha tipo 4 (trabalhador) com poucos campos "
                             f"({len(campos)}).")
            else:
                cpf = campos[3]
                if cpf and not TOKEN.search(cpf) and len(only_digits(cpf)) != 11:
                    erros.append(f"{rotulo} -> Erro: CPF de trabalhador invalido "
                                 f"('{cpf}'): 11 digitos.")
                if not is_filled(campos[4]):
                    avisos.append(f"{rotulo} -> data de admissao do trabalhador vazia "
                                  f"(campo obrigatorio no Sistema Auditor).")

        elif tipo == "6":
            n_tipo6 += 1
            cif = only_digits(campos[1]) if len(campos) > 1 else ""
            if len(cif) != 6:
                erros.append(f"Linha tipo 6 (CIF) invalida: '{campos[1] if len(campos)>1 else ''}' "
                             f"(esperado 6 digitos).")

    # Limite de 10 MB do Sistema Auditor: vale para a SOMA dos anexos DE CADA AUTO.
    # O mesmo PDF em varios autos e normal (PGR, AET) — pesa 1 vez no orcamento de cada um.
    linha_anexos = ""
    com_anexo = [(rot, itens) for rot, itens in anexos_por_auto if itens]
    if com_anexo:
        somas = []      # (rotulo, itens, mb_do_auto)
        sem_medir = 0
        for rotulo, itens in com_anexo:
            medidos = [p for _, p in itens if p]
            sem_medir += len(itens) - len(medidos)
            somas.append((rotulo, medidos,
                          sum(os.path.getsize(p) for p in medidos) / (1024 * 1024)))
        total_anexos = sum(len(itens) for _, itens in com_anexo)
        linha_anexos = (f"Anexos: {total_anexos} em {len(com_anexo)} auto(s); maior soma por "
                        f"auto: {max(m for _, _, m in somas):.1f} MB "
                        f"(limite {LIMITE_ANEXOS_MB:.0f} MB por auto)")
        if sem_medir:
            linha_anexos += f" - {sem_medir} anexo(s) nao medido(s): soma parcial"
        for rotulo, medidos, mb_auto in somas:
            if mb_auto > LIMITE_ANEXOS_MB:
                detalhe = "; ".join(f"{os.path.basename(p)} "
                                    f"{os.path.getsize(p)/(1024*1024):.1f} MB" for p in medidos)
                erros.append(f"{rotulo} -> Erro: os anexos deste auto somam {mb_auto:.1f} MB, "
                             f"acima do limite de {LIMITE_ANEXOS_MB:.0f} MB por auto de "
                             f"infracao. O limite vale para a SOMA dos anexos do auto, nao "
                             f"por arquivo - a importacao do TXT seria recusada. Comprima com "
                             f"_scripts/comprimir_pdf.py (o TXT nao precisa ser regerado, os "
                             f"nomes nao mudam) ou tire anexos deste auto. Tamanhos: {detalhe}")

    if n_tipo1 == 0:
        erros.append("Nenhuma linha tipo 1 (auto) encontrada.")
    if n_tipo6 != 1:
        erros.append(f"Esperada exatamente 1 linha tipo 6 (CIF) ao final; "
                     f"encontradas {n_tipo6}.")

    print(f"Arquivo: {path}")
    print(f"Autos (linhas tipo 1): {n_tipo1}")
    if linha_anexos:
        print(linha_anexos)
    if avisos:
        print(f"\nAVISOS ({len(avisos)}):")
        for a in avisos:
            print("  - " + a)
    if erros:
        print(f"\nERROS ({len(erros)}) - o Sistema Auditor recusaria a importacao "
              f"ou o auto sairia com defeito de forma:")
        for e in erros:
            print("  X " + e)
        print("\nRESULTADO: REPROVADO. Corrija os erros acima antes de importar.")
        sys.exit(1)
    print("\nRESULTADO: APROVADO. O TXT esta integro para importacao no Sistema Auditor.")
    sys.exit(0)


if __name__ == "__main__":
    main()
