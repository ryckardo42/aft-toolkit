#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validador de arquivo fiscal AEJ (Arquivo Eletronico de Jornada) — Portaria MTP 671/2021.

Valida estrutura + integridade do AEJ (delimitado por "|", ISO-8859-1, CRLF):
  - estrutura de cada tipo de registro (01 a 08, 99): numero de campos, formatos
    de data/hora/hora, versao "001";
  - integridade referencial entre registros (marcacao -> vinculo/REP/horario);
  - contagens do trailer (tipo 99).

O AFD foi EXCLUIDO desta skill (a pedido): se um arquivo AFD for informado, ele e
reportado como IGNORADO (fora de escopo), sem invalidar o lote.

As regras foram CALIBRADAS contra um AEJ real gerado por REP certificado
(SmartControl / Maestro Tecnologia), que e o modelo de "AEJ correto" desta skill.
Onde o leiaute teorico e o arquivo certificado divergem, vale o arquivo certificado:
  - campos H (hora) sao gravados como "hh:mm:ss" (alem do "hhmm" do leiaute);
  - campos DH gravam os segundos reais (o leiaute fixa ":00");
  - codHorContratual e comparado ignorando zeros a esquerda ("0003" == "3");
  - idRepAej (tipo 05) e opcional (so e exigido quando fonteMarc='O');
  - qtMinutos/tipoMovBH (tipo 07) sao opcionais (so exigidos quando
    tipoAusenOuComp='3').

Uso:
    python3 validar.py ARQUIVO [ARQUIVO ...] [--out RELATORIO.md]

Saida: relatorio markdown (--out ou ao lado do arquivo) + resumo no stdout.
Exit code: 0 se todos VALIDOS (mesmo com avisos) ou IGNORADOS, 1 se algum INVALIDO.

Severidades:
  ERRO   -> torna o arquivo INVALIDO (formato/integridade quebrados).
  AVISO  -> conteudo suspeito ou nao confirmavel (nao invalida sozinho).
"""

import sys
import os
import re
import argparse
import datetime as _dt


# --------------------------------------------------------------------------- #
# Coletor de achados
# --------------------------------------------------------------------------- #

class Report:
    def __init__(self, path, kind):
        self.path = path
        self.kind = kind            # "AEJ" | "AFD" | "?"
        self.errors = []            # (linha:int|None, msg)
        self.warnings = []
        self.stats = {}             # rotulo -> valor
        self.fatal = None           # impede prosseguir (ex.: arquivo ilegivel)
        self.skipped = None         # motivo de ter sido ignorado (ex.: AFD)

    def err(self, line, msg):
        self.errors.append((line, msg))

    def warn(self, line, msg):
        self.warnings.append((line, msg))

    @property
    def valid(self):
        # Ignorado (fora de escopo) e ilegivel nao reprovam o lote por erro de
        # conteudo; so erros de validacao reprovam.
        return self.fatal is None and not self.errors

    @property
    def verdict(self):
        if self.skipped:
            return "IGNORADO (fora de escopo)"
        if self.fatal:
            return "ILEGIVEL"
        if self.errors:
            return "INVALIDO"
        if self.warnings:
            return "VALIDO (com avisos)"
        return "VALIDO"


# --------------------------------------------------------------------------- #
# Leitura comum
# --------------------------------------------------------------------------- #

def read_lines(path, rep):
    """Le o arquivo em bytes, decodifica latin-1, separa linhas.
    Retorna lista de (numero_linha, texto_sem_terminador, tinha_crlf)."""
    with open(path, "rb") as f:
        raw = f.read()
    if not raw:
        rep.fatal = "Arquivo vazio."
        return []
    text = raw.decode("latin-1")
    parts = text.split("\n")
    # Se o arquivo termina em \n, split gera um ultimo elemento vazio: descarta.
    if parts and parts[-1] == "":
        parts = parts[:-1]
    out = []
    for i, p in enumerate(parts, start=1):
        crlf = p.endswith("\r")
        out.append((i, p[:-1] if crlf else p, crlf))
    return out


def check_line_terminators(lines, rep):
    """Avisa se as linhas (exceto possivelmente a ultima) nao usam CRLF e
    sinaliza linhas em branco no meio do arquivo (proibidas pelo leiaute)."""
    n = len(lines)
    bad_term = 0
    for idx, (ln, text, crlf) in enumerate(lines):
        is_last = (idx == n - 1)
        if not crlf and not is_last:
            bad_term += 1
        if text == "" and not is_last:
            rep.err(ln, "Linha em branco (nao permitida).")
    if bad_term:
        rep.warn(None, f"{bad_term} linha(s) sem terminador CRLF (chars 13,10) — "
                       "exigido pelo leiaute.")


# --------------------------------------------------------------------------- #
# Validadores de campo
# --------------------------------------------------------------------------- #

_RE_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
# DH: "AAAA-MM-ddThh:mm:ssZZZZZ". O leiaute fixa os segundos em "00", mas o REP
# certificado grava os segundos reais — aceitamos qualquer ss valido (00-59).
_RE_DH = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:[0-5]\d[+-]\d{4}$")
# H: o leiaute define "hhmm"; o REP certificado grava "hh:mm:ss". Aceitamos
# "hhmm", "hh:mm" e "hh:mm:ss".
_RE_H = re.compile(r"^([01]\d|2[0-3])(:?[0-5]\d){1,2}$")


def valid_date(s):
    if not _RE_DATE.match(s):
        return False
    try:
        _dt.date(int(s[0:4]), int(s[5:7]), int(s[8:10]))
        return True
    except ValueError:
        return False


def valid_dh(s):
    if not _RE_DH.match(s):
        return False
    try:
        _dt.datetime(int(s[0:4]), int(s[5:7]), int(s[8:10]),
                     int(s[11:13]), int(s[14:16]), int(s[17:19]))
    except ValueError:
        return False
    # fuso horario ZZZZZ = sinal + HHMM
    h, m = int(s[20:22]), int(s[22:24])
    return h <= 23 and m <= 59


def cpf_ok(s):
    """CPF: 11 digitos + digitos verificadores."""
    if len(s) != 11 or not s.isdigit():
        return False
    if s == s[0] * 11:
        return False
    for j in (9, 10):
        soma = sum(int(s[i]) * ((j + 1) - i) for i in range(j))
        d = (soma * 10) % 11
        d = 0 if d == 10 else d
        if d != int(s[j]):
            return False
    return True


def cnpj_ok(s):
    if len(s) != 14 or not s.isdigit():
        return False
    if s == s[0] * 14:
        return False
    pesos1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    pesos2 = [6] + pesos1
    for pesos, pos in ((pesos1, 12), (pesos2, 13)):
        soma = sum(int(s[i]) * pesos[i] for i in range(pos))
        r = soma % 11
        d = 0 if r < 2 else 11 - r
        if d != int(s[pos]):
            return False
    return True


def _norm(v):
    """Normaliza um codigo numerico ignorando zeros a esquerda ('0003' -> '3')."""
    return v.lstrip("0") or "0"


# --------------------------------------------------------------------------- #
# AEJ
# --------------------------------------------------------------------------- #
# tipo -> (min_campos, max_campos, [(idx, nome, tipo, obrigatorio)])
# idx refere-se a fields[idx] (fields[0] = tipoReg).
# tipo de campo: N, A, D, DH, H, CPF, IDENT (CNPJ ou CPF), FIX:<valor>
AEJ_SPECS = {
    "01": (10, 10, [
        (1, "tpIdtEmpregador", "N", True), (2, "idtEmpregador", "IDENT", True),
        (3, "caepf", "N", False), (4, "cno", "N", False),
        (5, "razaoOuNome", "A", True), (6, "dataInicialAej", "D", True),
        (7, "dataFinalAej", "D", True), (8, "dataHoraGerAej", "DH", True),
        (9, "versaoAej", "FIX:001", True),
    ]),
    "02": (4, 4, [
        (1, "idRepAej", "N", True), (2, "tpRep", "N", True), (3, "nrRep", "N", True),
    ]),
    "03": (4, 4, [
        (1, "idtVinculoAej", "N", True), (2, "cpf", "CPF", True),
        (3, "nomeEmp", "A", True),
    ]),
    "04": (7, 99, [
        (1, "codHorContratual", "A", True), (2, "durJornada", "N", True),
        (3, "hrEntrada01", "H", True), (4, "hrSaida01", "H", True),
        (5, "hrEntrada02", "H", False), (6, "hrSaida02", "H", False),
    ]),
    "05": (9, 9, [
        (1, "idtVinculoAej", "N", True), (2, "dataHoraMarc", "DH", True),
        # idRepAej e "0 a 9" no leiaute: opcional (so exigido quando fonteMarc='O').
        (3, "idRepAej", "N", False), (4, "tpMarc", "A", True),
        (5, "seqEntSaida", "N", True), (6, "fonteMarc", "A", True),
        (7, "codHorContratual", "A", False), (8, "motivo", "A", False),
    ]),
    "06": (3, 3, [
        (1, "idtVinculoAej", "N", True), (2, "matEsocial", "A", True),
    ]),
    "07": (6, 6, [
        (1, "idtVinculoAej", "N", True), (2, "tipoAusenOuComp", "N", True),
        # qtMinutos/tipoMovBH so sao exigidos quando tipoAusenOuComp='3'.
        (3, "data", "D", True), (4, "qtMinutos", "N", False),
        (5, "tipoMovBH", "N", False),
    ]),
    "08": (7, 7, [
        (1, "nomeProg", "A", True), (2, "versaoProg", "A", True),
        (3, "tpIdtDesenv", "N", True), (4, "idtDesenv", "IDENT", True),
        (5, "razaoNomeDesenv", "A", True), (6, "emailDesenv", "A", True),
    ]),
}


def validate_aej(path, lines, rep):
    rep.kind = "AEJ"
    if not lines:
        return
    check_line_terminators(lines, rep)

    counts = {t: 0 for t in ("01", "02", "03", "04", "05", "06", "07", "08")}
    vinculos = set()      # idtVinculoAej (tipo 03), normalizado
    reps = set()          # idRepAej (tipo 02), normalizado
    horarios = set()      # codHorContratual (tipo 04), normalizado
    header = None
    trailer = None
    sig_seen = False
    MAXSHOW = 50
    ref_pending = []      # (ln, kind, value) checados depois de ler tudo

    for (ln, text, _) in lines:
        if text == "":
            continue
        if text.startswith("ASSINATURA_DIGITAL_EM_ARQUIVO_P7S"):
            sig_seen = True
            if len(text) != 100:
                rep.warn(ln, f"linha de assinatura com {len(text)} caracteres (esperado 100).")
            continue
        if "|" not in text:
            rep.err(ln, f"linha sem delimitador '|': '{text[:40]}'.")
            continue
        fields = text.split("|")
        tipo = fields[0]

        if tipo == "99":
            trailer = (ln, fields)
            continue
        if tipo == "01":
            header = (ln, fields)
        if tipo not in AEJ_SPECS:
            rep.err(ln, f"tipo de registro desconhecido '{tipo}'.")
            continue
        counts[tipo] += 1

        nmin, nmax, specs = AEJ_SPECS[tipo]
        ncampos = len(fields)
        if not (nmin <= ncampos <= nmax):
            faixa = f"{nmin}" if nmin == nmax else f"{nmin}-{nmax}"
            if len([e for e in rep.errors if "campo(s)" in e[1]]) < MAXSHOW:
                rep.err(ln, f"registro tipo {tipo}: {ncampos} campo(s) "
                            f"(esperado {faixa}).")
            continue

        # valida cada campo (idx refere fields[idx])
        for (i, name, ftyp, req) in specs:
            if i >= ncampos:
                continue
            v = fields[i]
            if req and v.strip() == "":
                if ftyp == "H":
                    # PTRP pode encodar jornada de periodo unico deixando um
                    # par entrada/saida vazio — comum e aceito. Aviso, nao erro.
                    rep.warn(ln, f"tipo {tipo}: par entrada/saida incompleto "
                                 f"({name} vazio).")
                elif ftyp != "A":
                    rep.err(ln, f"tipo {tipo}: campo obrigatorio {name} vazio.")
                continue
            validate_aej_field(rep, ln, tipo, name, v, ftyp)

        # coleta chaves e referencias
        if tipo == "02":
            reps.add(_norm(fields[1]))
        elif tipo == "03":
            vinculos.add(_norm(fields[1]))
        elif tipo == "04":
            horarios.add(_norm(fields[1]))
        elif tipo == "05":
            ref_pending.append((ln, "vinc", _norm(fields[1])))
            idrep = fields[3].strip()
            if idrep and _norm(idrep) != "0":
                ref_pending.append((ln, "rep", _norm(idrep)))
            cod = fields[7].strip()
            # codHor "000...0" e o sentinela de "sem horario especifico": ignora.
            if cod and cod.strip("0"):
                ref_pending.append((ln, "hor", _norm(cod)))
            # regras condicionais (tipo 05 sempre tem 9 campos aqui)
            tpmarc = fields[4]
            fonte = fields[6]
            # idRepAej e obrigatorio quando a marcacao e original do REP.
            if fonte == "O" and not idrep:
                rep.warn(ln, "tipo 05: idRepAej ausente em marcacao fonteMarc='O' "
                             "(deveria referenciar o REP de origem).")
            # motivo e obrigatorio para marcacao desconsiderada/incluida.
            if (tpmarc == "D" or fonte == "I") and not fields[8].strip():
                rep.warn(ln, "tipo 05: motivo obrigatorio quando tpMarc='D' "
                             "ou fonteMarc='I'.")
        elif tipo == "06":
            ref_pending.append((ln, "vinc", _norm(fields[1])))
        elif tipo == "07":
            ref_pending.append((ln, "vinc", _norm(fields[1])))
            # qtMinutos e obrigatorio para movimento de banco de horas.
            if fields[2].strip() == "3" and fields[4].strip() == "":
                rep.warn(ln, "tipo 07: qtMinutos obrigatorio quando "
                             "tipoAusenOuComp='3'.")

    # ----- integridade referencial -----
    miss_v = miss_r = miss_h = 0
    for (ln, kind, val) in ref_pending:
        if kind == "vinc" and val not in vinculos:
            miss_v += 1
            if miss_v <= MAXSHOW:
                rep.err(ln, f"idtVinculoAej '{val}' nao existe em nenhum registro tipo 03.")
        elif kind == "rep" and val not in reps:
            miss_r += 1
            if miss_r <= MAXSHOW:
                rep.err(ln, f"idRepAej '{val}' nao existe em nenhum registro tipo 02.")
        elif kind == "hor" and val not in horarios:
            miss_h += 1
            if miss_h <= MAXSHOW:
                rep.err(ln, f"codHorContratual '{val}' nao existe em nenhum registro tipo 04.")
    for label, n in (("vinculos", miss_v), ("REPs", miss_r), ("horarios", miss_h)):
        if n > MAXSHOW:
            rep.err(None, f"... e mais {n - MAXSHOW} referencia(s) de {label} ausentes.")

    # ----- header: coerencia tipo id x conteudo -----
    if header:
        hln, hf = header
        tp = hf[1]
        ident = hf[2]
        if tp == "1" and not cnpj_ok(ident):
            rep.warn(hln, f"cabecalho: CNPJ do empregador invalido ('{ident}').")
        elif tp == "2" and not cpf_ok(ident):
            rep.warn(hln, f"cabecalho: CPF do empregador invalido ('{ident}').")
    else:
        rep.err(None, "cabecalho (tipo 01) ausente.")

    # ----- trailer -----
    if trailer is None:
        rep.err(None, "trailer (tipo 99) ausente.")
    else:
        tln, tf = trailer
        if len(tf) != 9:
            rep.err(tln, f"trailer: {len(tf)} campo(s) (esperado 9).")
        else:
            ordem = ["01", "02", "03", "04", "05", "06", "07", "08"]
            for k, t in enumerate(ordem, start=1):
                d = tf[k]
                if not d.isdigit():
                    rep.err(tln, f"trailer: contagem do tipo {t} nao numerica ('{d}').")
                    continue
                if int(d) != counts[t]:
                    rep.err(tln, f"trailer: declara {int(d)} registro(s) tipo {t}, "
                                 f"arquivo contem {counts[t]}.")
    if not sig_seen:
        rep.warn(None, "linha de assinatura digital "
                       "(ASSINATURA_DIGITAL_EM_ARQUIVO_P7S) ausente.")

    # ----- estatisticas -----
    if header:
        hf = header[1]
        rep.stats["Empregador"] = hf[5].strip() if len(hf) > 5 else ""
        if len(hf) > 7:
            rep.stats["Periodo"] = f"{hf[6]} a {hf[7]}"
    rep.stats["REPs (tipo 02)"] = counts["02"]
    rep.stats["Vinculos (tipo 03)"] = counts["03"]
    rep.stats["Horarios contratuais (tipo 04)"] = counts["04"]
    rep.stats["Marcacoes (tipo 05)"] = counts["05"]
    rep.stats["Ausencias/banco de horas (tipo 07)"] = counts["07"]


def validate_aej_field(rep, ln, tipo, name, v, ftyp):
    if ftyp.startswith("FIX:"):
        exp = ftyp[4:]
        if v != exp:
            rep.err(ln, f"tipo {tipo} campo {name}: esperado '{exp}', encontrado '{v}'.")
    elif ftyp == "N":
        if v.strip() and not v.isdigit():
            rep.err(ln, f"tipo {tipo} campo {name}: nao numerico ('{v}').")
    elif ftyp == "D":
        if not valid_date(v):
            rep.err(ln, f"tipo {tipo} campo {name}: data invalida '{v}'.")
    elif ftyp == "DH":
        if not valid_dh(v):
            rep.err(ln, f"tipo {tipo} campo {name}: data/hora invalida '{v}'.")
    elif ftyp == "H":
        if v and not _RE_H.match(v):
            rep.err(ln, f"tipo {tipo} campo {name}: hora invalida '{v}' "
                        "(esperado hhmm ou hh:mm:ss).")
    elif ftyp == "CPF":
        if not cpf_ok(v):
            rep.warn(ln, f"tipo {tipo} campo {name}: CPF invalido ('{v}').")
    elif ftyp == "IDENT":
        if len(v) == 14:
            if not cnpj_ok(v):
                rep.warn(ln, f"tipo {tipo} campo {name}: CNPJ invalido ('{v}').")
        elif len(v) == 11:
            if not cpf_ok(v):
                rep.warn(ln, f"tipo {tipo} campo {name}: CPF invalido ('{v}').")


# --------------------------------------------------------------------------- #
# Orquestracao + relatorio
# --------------------------------------------------------------------------- #

def detect_kind(path, lines):
    """AEJ pelo nome (AEJ*) ou conteudo ('01|'). AFD e reconhecido apenas para
    ser reportado como fora de escopo."""
    name = os.path.basename(path).upper()
    if name.startswith("AEJ"):
        return "AEJ"
    if name.startswith("AFD"):
        return "AFD"
    if lines:
        first = lines[0][1]
        if first.startswith("01|"):
            return "AEJ"
        if first[:9] == "000000000" and first[9:10] == "1":
            return "AFD"
    return "?"


def validate_file(path):
    rep = Report(path, "?")
    if not os.path.isfile(path):
        rep.fatal = "Arquivo nao encontrado."
        return rep
    lines = read_lines(path, rep)
    if rep.fatal:
        return rep
    kind = detect_kind(path, lines)
    rep.kind = kind
    if kind == "AFD":
        rep.skipped = ("Arquivo AFD — fora de escopo. Esta skill agora valida apenas "
                       "AEJ (o AFD foi excluido da validacao a pedido).")
        rep.stats["Linhas no arquivo"] = len(lines)
        return rep
    if kind != "AEJ":
        rep.fatal = ("Tipo nao identificado como AEJ (o nome nao comeca com 'AEJ' e "
                     "o conteudo nao inicia com '01|').")
        return rep
    try:
        validate_aej(path, lines, rep)
    except Exception as e:   # nunca derruba o lote por um arquivo
        rep.fatal = f"Erro interno ao validar: {e}"
    rep.stats["Linhas no arquivo"] = len(lines)
    return rep


def render_report(reps):
    L = []
    L.append("# Relatorio de validacao — AEJ")
    L.append("")
    L.append(f"_Gerado por jornada-valida-afd-aej · {len(reps)} arquivo(s)_")
    L.append("")
    # resumo
    L.append("| Arquivo | Tipo | Veredito | Erros | Avisos |")
    L.append("|---|---|---|---:|---:|")
    for r in reps:
        L.append(f"| {os.path.basename(r.path)} | {r.kind} | **{r.verdict}** | "
                 f"{len(r.errors)} | {len(r.warnings)} |")
    L.append("")
    for r in reps:
        L.append("---")
        L.append(f"## {os.path.basename(r.path)} — {r.verdict}")
        L.append("")
        L.append(f"`{r.path}`")
        L.append("")
        if r.skipped:
            L.append(f"> {r.skipped}")
            L.append("")
            continue
        if r.fatal:
            L.append(f"> **{r.fatal}**")
            L.append("")
            continue
        if r.stats:
            L.append("### Estatisticas")
            for k, v in r.stats.items():
                L.append(f"- **{k}:** {v}")
            L.append("")
        if r.errors:
            L.append(f"### Erros ({len(r.errors)})")
            for (ln, msg) in r.errors:
                loc = f"linha {ln}" if ln else "geral"
                L.append(f"- [{loc}] {msg}")
            L.append("")
        if r.warnings:
            L.append(f"### Avisos ({len(r.warnings)})")
            for (ln, msg) in r.warnings:
                loc = f"linha {ln}" if ln else "geral"
                L.append(f"- [{loc}] {msg}")
            L.append("")
        if not r.errors and not r.warnings:
            L.append("Nenhuma inconsistencia encontrada. ✅")
            L.append("")
    return "\n".join(L)


def print_summary(reps):
    for r in reps:
        if r.skipped:
            mark = "⏭️"
        elif r.valid:
            mark = "✅"
        else:
            mark = "❌"
        print(f"{mark} {os.path.basename(r.path)} [{r.kind}] -> {r.verdict} "
              f"({len(r.errors)} erro(s), {len(r.warnings)} aviso(s))")


def expand_paths(paths):
    out = []
    for p in paths:
        if os.path.isdir(p):
            for fn in sorted(os.listdir(p)):
                up = fn.upper()
                if up.startswith("AEJ") and up.endswith(".TXT"):
                    out.append(os.path.join(p, fn))
        else:
            out.append(p)
    return out


def main():
    ap = argparse.ArgumentParser(description="Validador de arquivo fiscal AEJ.")
    ap.add_argument("paths", nargs="+", help="arquivo(s) AEJ ou pasta(s)")
    ap.add_argument("--out", help="caminho do relatorio .md (padrao: ao lado do 1o arquivo)")
    args = ap.parse_args()

    files = expand_paths(args.paths)
    if not files:
        print("Nenhum arquivo AEJ encontrado.", file=sys.stderr)
        return 2

    reps = [validate_file(f) for f in files]

    report_md = render_report(reps)
    if args.out:
        out_path = args.out
    else:
        base = os.path.dirname(os.path.abspath(files[0]))
        out_path = os.path.join(base, "relatorio-validacao-aej.md")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(report_md)

    print_summary(reps)
    print(f"\nRelatorio salvo em: {out_path}")
    return 0 if all(r.valid for r in reps) else 1


if __name__ == "__main__":
    sys.exit(main())
