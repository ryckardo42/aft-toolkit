# -*- coding: utf-8 -*-
"""
atualizar_toolkit.py - Aplica um pacote do toolkit numa pasta de destino.

Esta e a costura da atualizacao (issue #138): a logica que hoje mora no texto
da /aft-atualizar passa a morar aqui, onde da para ler, rodar e corrigir. Este
arquivo cobre a fatia que se prova sozinha - PACOTE LOCAL, sem rede e sem
token (issue #141). O caminho do portal (--verificar / baixar) entra depois,
neste mesmo script.

O QUE ESTE PROGRAMA APAGA, E O QUE ELE NUNCA APAGA
--------------------------------------------------
Este e o coracao do assunto. Em 19/08/2026 uma atualizacao levou junto onze
skills que um AFT tinha escrito. A regra que impede a repeticao disso tem duas
metades, e as duas dependem do manifesto _scripts/skills_oficiais.txt (a lista
do que o toolkit instala, regravada a cada publicacao pelo remontar.py):

  * REMOVE-SE o que SAIU do manifesto: a pasta estava na lista da instalacao
    antiga e nao esta na lista do pacote novo. E uma skill que o toolkit tinha
    e deixou de ter - se ficasse, dispararia sozinha para sempre.

  * NAO SE TOCA no que NUNCA esteve no manifesto. Isso cobre, de uma vez, a
    skill pessoal com prefixo "minha-", a skill pessoal SEM prefixo nenhum
    (foi este o caso do incidente) e qualquer pasta que o AFT tenha ali.

Repare que a decisao nao olha o nome da pasta: "aft-grant" tem cara de oficial
e e skill pessoal de um AFT. Palpite por prefixo deixaria ela desprotegida.

Dentro das pastas que SAO do toolkit, o pacote manda: arquivo que existe na
instalacao e nao existe no pacote e sobra de versao velha, e sai. Fora delas,
nada e removido - nem os arquivos soltos na raiz (README, NOVIDADES...), que
sao atualizados mas nunca apagados.

A TRANSACAO, EM ORDEM
---------------------
  1. confere o sha256 do pacote contra a soma esperada;
  2. descompacta numa area temporaria (recusando caminho que escape dela);
  3. monta o diff do que esta CHEGANDO e passa pelo checar_diff.py - se ele
     acusar sinal suspeito, para antes de escrever qualquer coisa;
  4. tira o retrato das skills pessoais (skills_pessoais.py);
  5. guarda a instalacao atual em <destino>-backup-<versao>, mantendo as duas
     ultimas;
  6. escreve os arquivos do pacote, remove o que saiu do manifesto e as sobras
     dentro das pastas do toolkit;
  7. confere o retrato: nenhuma skill pessoal pode ter sumido no caminho.

Os passos 1 a 3 acontecem ANTES de qualquer escrita: pacote corrompido ou
suspeito nao chega a tocar na pasta do AFT.

Uso:
    python atualizar_toolkit.py --origem-local <pacote.zip> --destino <pasta> --simular
    python atualizar_toolkit.py --origem-local <pacote.zip> --destino <pasta> --aplicar

A soma esperada vem do arquivo <pacote.zip>.sha256 ao lado do pacote (e o que
o empacotar.py grava) ou de --sha256. Saida: um objeto JSON no stdout - so
JSON, para quem chama nao precisar interpretar prosa. Codigos de saida:
0 = feito, 1 = erro de uso, 2 = transacao recusada.
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
import difflib
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
from remontar import EXCLUIR  # noqa: E402  (mesma lista que o empacotar usa)

try:  # console do Windows e cp1252
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

MANIFESTO = "_scripts/skills_oficiais.txt"
# Marca deixada dentro de cada backup feito por este programa - e o que
# distingue os nossos de qualquer outra pasta "skills-backup-*" do AFT.
MARCA = ".aft-backup"
VERSAO = "_scripts/versao.txt"


# --------------------------------------------------------------- utilidades

def sha256_de(caminho):
    h = hashlib.sha256()
    with open(caminho, "rb") as f:
        for bloco in iter(lambda: f.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


def _ignorado(partes):
    """Caminho que nao e do toolkit e nunca entra na conta: .git, __pycache__,
    .DS_Store, o roteiro de instalacao... A mesma lista do empacotador, para os
    dois nunca divergirem sobre o que e conteudo do pacote."""
    return any(p in EXCLUIR for p in partes)


def arquivos_de(raiz):
    """Caminhos relativos (str, com '/') de todo arquivo sob `raiz`, fora os
    ignorados. Ordenado, para o relatorio sair estavel."""
    if not raiz.is_dir():
        return []
    achados = []
    for caminho in raiz.rglob("*"):
        if not caminho.is_file():
            continue
        rel = caminho.relative_to(raiz).parts
        if _ignorado(rel):
            continue
        achados.append("/".join(rel))
    return sorted(achados)


def ler_manifesto(arquivo):
    if not arquivo.is_file():
        return set()
    return {l.strip() for l in arquivo.read_text(encoding="utf-8").splitlines()
            if l.strip()}


def ler_versao(arquivo):
    """versao.txt e um 'chave: valor' por linha. Devolve {} se nao existir."""
    if not arquivo.is_file():
        return {}
    dados = {}
    for linha in arquivo.read_text(encoding="utf-8").splitlines():
        chave, _, valor = linha.partition(":")
        if valor:
            dados[chave.strip()] = valor.strip()
    return dados


def texto_ou_none(caminho):
    """Conteudo em linhas se o arquivo for texto; None se for binario (nao da
    para varrer .docx nem .pdf, e nao adianta fingir que da)."""
    try:
        return caminho.read_text(encoding="utf-8").splitlines(keepends=True)
    except (UnicodeDecodeError, OSError):
        return None


# ------------------------------------------------------ descompactar seguro

def descompactar(zip_path, alvo):
    """Descompacta recusando membro com caminho absoluto ou com '..' - um zip
    preparado podia, sem isso, escrever fora da area temporaria."""
    with zipfile.ZipFile(zip_path) as z:
        for nome in z.namelist():
            p = Path(nome)
            if p.is_absolute() or ".." in p.parts or nome.startswith("/"):
                raise ValueError(f"caminho suspeito dentro do pacote: {nome}")
        z.extractall(alvo)


# ------------------------------------------------------------------- o plano

def montar_plano(pacote, destino):
    """Decide, sem escrever nada, o que sera copiado, o que sera removido e o
    que sera preservado. Devolve um dicionario pronto para virar JSON."""
    oficiais_novo = ler_manifesto(pacote / MANIFESTO)
    oficiais_antigo = ler_manifesto(destino / MANIFESTO)
    conhecidas = oficiais_novo | oficiais_antigo

    novos, alterados, iguais, fora_do_manifesto = [], [], [], []
    for rel in arquivos_de(pacote):
        topo = rel.split("/")[0]
        # Arquivo solto na raiz do pacote (README, NOVIDADES, a apostila) nao
        # aparece no manifesto, que so lista pastas - mas e nosso e atualiza.
        if "/" in rel and topo not in oficiais_novo:
            fora_do_manifesto.append(rel)
            continue
        atual = destino / rel
        if not atual.is_file():
            novos.append(rel)
        elif atual.read_bytes() != (pacote / rel).read_bytes():
            alterados.append(rel)
        else:
            iguais.append(rel)

    do_pacote = set(novos) | set(alterados) | set(iguais)

    # Pastas do toolkit que saem inteiras: estavam no manifesto antigo e nao
    # estao no novo. So essas - o resto da pasta do AFT nao e da nossa conta.
    skills_removidas = sorted(n for n in (oficiais_antigo - oficiais_novo)
                              if (destino / n).is_dir())

    # Sobras DENTRO das pastas que continuam sendo do toolkit - e so nas que
    # JA eram nossas antes. Se a pasta existe no destino mas nao estava no
    # manifesto antigo, ela e do AFT (uma skill pessoal que casou de nome com
    # uma skill oficial nova, como o "aft-grant" que o codigo cita): o pacote
    # escreve por cima o que traz, mas nao apaga o que o AFT pos ali.
    sobras = []
    for nome in sorted(oficiais_novo & oficiais_antigo):
        pasta = destino / nome
        if not pasta.is_dir():
            continue
        for rel in arquivos_de(pasta):
            inteiro = f"{nome}/{rel}"
            if inteiro not in do_pacote:
                sobras.append(inteiro)

    # O que sobrevive intacto: tudo o que nunca esteve em manifesto nenhum.
    preservadas = sorted(
        d.name for d in destino.iterdir()
        if d.is_dir() and not d.name.startswith(".")
        and d.name not in conhecidas and d.name not in EXCLUIR)

    return {
        "novos": novos, "alterados": alterados, "iguais": iguais,
        "skills_removidas": skills_removidas, "sobras_removidas": sobras,
        "preservadas": preservadas, "fora_do_manifesto": fora_do_manifesto,
        "_oficiais_novo": oficiais_novo, "_conhecidas": conhecidas,
    }


# ------------------------------------------------- varredura do que esta chegando

def montar_diff(pacote, destino, plano):
    """Diff unificado do conteudo que esta CHEGANDO, no formato que o
    checar_diff.py le pelo stdin. Arquivo binario fica de fora (nao ha o que
    varrer nele) e e contado a parte."""
    partes, binarios = [], 0
    for rel in plano["novos"] + plano["alterados"]:
        novo = texto_ou_none(pacote / rel)
        if novo is None:
            binarios += 1
            continue
        velho = texto_ou_none(destino / rel) or []
        partes.extend(difflib.unified_diff(velho, novo, fromfile=f"a/{rel}",
                                           tofile=f"b/{rel}", n=0))
    texto = "".join(p if p.endswith("\n") else p + "\n" for p in partes)
    return texto, binarios


def varrer(diff):
    """Passa o diff pelo checar_diff.py (pelo cano, que e o contrato dele) e
    devolve (limpo, relatorio). Falha-fechado de proposito: se a varredura nao
    puder ser feita, a atualizacao nao anda. Guard-rail que se pode pular nao
    e guard-rail."""
    if not diff.strip():
        return True, "Nada a varrer (nenhuma linha nova chegando)."
    script = AQUI / "checar_diff.py"
    if not script.is_file():
        return False, f"nao encontrei o {script.name} para varrer o pacote."
    try:
        r = subprocess.run([sys.executable or "python3", str(script), "-"],
                           input=diff, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=180)
    except (OSError, subprocess.SubprocessError) as e:
        return False, f"nao consegui rodar a varredura de seguranca ({e})."
    saida = (r.stdout or "").strip()
    # O checar_diff sempre sai com 0 (e alarme, nao portao). Quem decide parar
    # e este script: so segue com a linha de "nada suspeito" na mao. Procurar a
    # palavra "suspeito" solta nao serve - ela aparece nas DUAS mensagens
    # ("nada suspeito" e "sinal(is) suspeito(s)"). Os marcadores abaixo sao
    # procurados por linha e em dobro (simbolo e texto), porque o console do
    # Windows pode comer o emoji.
    linhas = [l.strip() for l in saida.splitlines()]
    alarme = any(l.startswith("⚠") for l in linhas) or "sinal(is) suspeito" in saida
    tranquilo = (any(l.startswith("✓") for l in linhas)
                 or "nada suspeito nas linhas" in saida)
    return (tranquilo and not alarme), saida or (r.stderr or "").strip()


# ------------------------------------------------------------------ escrever

def fazer_backup(destino, plano, versao_anterior):
    """Copia para <destino>-backup-<versao> o que esta prestes a ser mexido:
    as pastas que a instalacao atual declara como do toolkit, mais os arquivos
    soltos na raiz. So isso - as skills pessoais nao sao mexidas por este
    programa e ja tem o retrato do skills_pessoais.py."""
    alvo = destino.parent / f"{destino.name}-backup-{versao_anterior or 'sem-versao'}"
    # Monta ao lado e so troca no fim: apagar o backup antigo ANTES de a copia
    # nova ficar pronta deixa a versao anterior sem nenhuma copia inteira
    # enquanto a copia corre (e ela pode falhar no meio, por disco cheio).
    parcial = destino.parent / f"{alvo.name}.parcial"
    shutil.rmtree(parcial, ignore_errors=True)
    alvo_final, alvo = alvo, parcial
    alvo.mkdir(parents=True)
    for nome in sorted(plano["_conhecidas"]):
        origem = destino / nome
        if origem.is_dir():
            shutil.copytree(origem, alvo / nome,
                            ignore=shutil.ignore_patterns(*EXCLUIR))
    for arq in sorted(destino.iterdir()):
        if arq.is_file() and not _ignorado((arq.name,)):
            shutil.copy2(arq, alvo / arq.name)
    if not any(alvo.iterdir()):
        # Primeira instalacao: nao havia nada para guardar. Pasta de backup
        # vazia so ocuparia uma das duas vagas e nao serviria para voltar.
        alvo.rmdir()
        return None, []
    (alvo / MARCA).write_text(f"{versao_anterior or 'sem-versao'}\n",
                              encoding="utf-8")
    shutil.rmtree(alvo_final, ignore_errors=True)
    alvo.rename(alvo_final)
    alvo = alvo_final

    # Mantem as duas ultimas, a mais nova inclusive. So conta pasta com a
    # nossa marca dentro: ao lado de ~/.claude/skills ja existe backup antigo
    # feito a mao (skills-backup-20260525-...-aftcowork-migration), e apagar
    # pasta do AFT que nao fomos nos que criamos seria estrago, nao faxina.
    irmas = sorted((d for d in destino.parent.iterdir()
                    if d.is_dir() and d.name.startswith(f"{destino.name}-backup-")
                    and (d / MARCA).is_file()),
                   key=lambda d: d.stat().st_mtime_ns, reverse=True)
    for velha in irmas[2:]:
        shutil.rmtree(velha, ignore_errors=True)
    return alvo, [d.name for d in irmas[:2]]


def aplicar_arquivos(pacote, destino, plano):
    for rel in plano["novos"] + plano["alterados"]:
        alvo = destino / rel
        alvo.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(pacote / rel, alvo)
    for rel in plano["sobras_removidas"]:
        (destino / rel).unlink(missing_ok=True)
    for nome in plano["skills_removidas"]:
        shutil.rmtree(destino / nome, ignore_errors=True)
    # Pasta que ficou vazia depois de tirar as sobras - so dentro do que e nosso.
    for nome in sorted(plano["_oficiais_novo"]):
        raiz = destino / nome
        if not raiz.is_dir():
            continue
        for pasta in sorted(raiz.rglob("*"), key=lambda p: len(p.parts),
                            reverse=True):
            if pasta.is_dir() and not any(pasta.iterdir()):
                pasta.rmdir()


def _skills_pessoais(destino, manifesto_uniao, *args):
    """Chama o skills_pessoais.py apontado para ESTA pasta de destino - e nao
    para ~/.claude/skills. O manifesto passado e a UNIAO do antigo com o novo:
    uma skill que acabou de sair do toolkit ainda e nossa, e nao pode ser
    contada como pessoal so porque saiu da lista nova."""
    script = AQUI / "skills_pessoais.py"
    if not script.is_file():
        return None, f"nao encontrei o {script.name}"
    r = subprocess.run([sys.executable or "python3", str(script), *args,
                        "--skills", str(destino),
                        "--manifesto", str(manifesto_uniao)],
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace")
    return r.returncode, (r.stdout or r.stderr).strip()


# ----------------------------------------------------------------- transacao

def transacao(zip_path, destino, soma_esperada, simular, confirmado=False):
    res = {"ok": True, "modo": "simular" if simular else "aplicar",
           "erro": None, "detalhe": "", "destino": str(destino),
           "pacote": {"arquivo": str(zip_path)}}

    soma = sha256_de(zip_path)
    res["pacote"]["sha256"] = soma
    res["pacote"]["sha256_esperado"] = soma_esperada
    if soma != soma_esperada:
        res.update(ok=False, erro="soma_divergente", detalhe=(
            "A soma de verificação do pacote não bate com a esperada. O arquivo "
            "chegou corrompido ou não é o pacote anunciado - nada foi instalado."))
        return res, 2

    tmp = Path(tempfile.mkdtemp(prefix="aft-aplicar-"))
    try:
        pacote = tmp / "pacote"
        try:
            descompactar(zip_path, pacote)
        except (ValueError, zipfile.BadZipFile) as e:
            res.update(ok=False, erro="pacote_invalido",
                       detalhe=f"Não consegui abrir o pacote: {e}")
            return res, 2

        if not (pacote / MANIFESTO).is_file():
            res.update(ok=False, erro="pacote_invalido", detalhe=(
                f"O pacote não traz o {MANIFESTO}, que é a lista do que o "
                "toolkit instala. Sem ela não dá para saber o que pode ser "
                "removido - nada foi instalado."))
            return res, 2

        res["pacote"].update(ler_versao(pacote / VERSAO))
        anterior = ler_versao(destino / VERSAO)
        res["versao_anterior"] = anterior.get("versao")
        # Sem o manifesto instalado nao ha instalacao anterior conhecida: nada
        # a remover (o que nunca esteve no manifesto nao e nosso) e nada com o
        # que comparar na varredura.
        primeira_instalacao = not (destino / MANIFESTO).is_file()
        res["primeira_instalacao"] = primeira_instalacao

        plano = montar_plano(pacote, destino)

        # A varredura compara o que esta CHEGANDO com o que ja esta instalado.
        # Sem instalacao anterior nao ha com o que comparar: o toolkit inteiro
        # conta como "linha nova", inclusive a propria tabela de padroes do
        # checar_diff.py - e ele acusaria a si mesmo, barrando toda primeira
        # instalacao. Nesse caso a varredura nao roda, e o JSON diz isso com
        # todas as letras (quem protege a primeira instalacao e a soma de
        # verificacao e a rota autenticada do portal, nao o alarme de diff).
        if primeira_instalacao:
            res["varredura"] = {"limpo": None, "relatorio": (
                "Primeira instalação nesta pasta: não há versão anterior para "
                "comparar, então a varredura de segurança do diff não se aplica."),
                "binarios_nao_varridos": 0}
            limpo = True
        else:
            diff, binarios = montar_diff(pacote, destino, plano)
            limpo, relatorio = varrer(diff)
            res["varredura"] = {"limpo": limpo, "relatorio": relatorio,
                                "binarios_nao_varridos": binarios}
        publico = {k: v for k, v in plano.items() if not k.startswith("_")}
        res["plano"] = {k: (v if k != "iguais" else len(v))
                        for k, v in publico.items()}

        if plano["fora_do_manifesto"]:
            # O empacotar.py gera o manifesto e o conteudo da MESMA arvore: se
            # sobrou arquivo fora da lista, o manifesto esta defeituoso (foi o
            # que aconteceu com a pasta Template, que o git entregava entre
            # aspas). Instalar assim entregaria uma instalacao incompleta
            # dizendo "pronto".
            res.update(ok=False, erro="manifesto_incompleto", detalhe=(
                f"O pacote traz {len(plano['fora_do_manifesto'])} arquivo(s) em "
                "pastas que o próprio manifesto dele não lista - o pacote está "
                "defeituoso e instalá-lo deixaria a pasta incompleta. Nada foi "
                "instalado. Primeiro arquivo: "
                + plano["fora_do_manifesto"][0]))
            return res, 2

        if not limpo and confirmado:
            res["varredura"]["confirmado_pelo_aft"] = True
        elif not limpo:
            res.update(ok=False, erro="conteudo_suspeito", detalhe=(
                "A varredura de segurança apontou sinal suspeito no conteúdo que "
                "está chegando. NADA foi instalado. Mostre o relatório ao AFT e, "
                "só se ele confirmar que a atualização é legítima, repita o "
                "comando com --confirmado."))
            return res, 2

        if simular:
            res["detalhe"] = (
                f"Simulação: {len(plano['novos'])} arquivo(s) novo(s), "
                f"{len(plano['alterados'])} alterado(s), "
                f"{len(plano['skills_removidas'])} skill(s) removida(s), "
                f"{len(plano['preservadas'])} pasta(s) preservada(s). "
                "Nada foi escrito.")
            return res, 0

        uniao = tmp / "manifesto-uniao.txt"
        uniao.write_text("\n".join(sorted(plano["_conhecidas"])) + "\n",
                         encoding="utf-8")
        _, retrato = _skills_pessoais(destino, uniao, "--backup")
        res["retrato_pessoais"] = retrato

        backup, mantidos = fazer_backup(destino, plano, res["versao_anterior"])
        res["backup"] = str(backup) if backup else None
        res["backups_mantidos"] = mantidos

        try:
            aplicar_arquivos(pacote, destino, plano)
        except OSError as e:
            # Disco cheio, permissao negada, .docx aberto no Windows... A pasta
            # ficou pela metade e nao ha como saber quanto. Quem chama precisa
            # receber isso em JSON, e nao um traceback - e precisa do caminho
            # do backup na mesma frase.
            res.update(ok=False, erro="falha_ao_aplicar", detalhe=(
                f"A instalação parou no meio: {e}. A pasta ficou incompleta. A "
                "versão anterior está inteira em "
                + (res["backup"] or "nenhum backup (era a primeira instalação)")
                + " - restaure de lá antes de tentar de novo."))
            return res, 2

        codigo, conferencia = _skills_pessoais(destino, uniao, "--conferir")
        res["conferencia_pessoais"] = conferencia
        if codigo == 3:
            res.update(ok=False, erro="skill_pessoal_sumiu", detalhe=(
                "Uma skill pessoal do AFT sumiu durante a atualização - isto é "
                "defeito do toolkit, não erro dele. Reponha com: "
                f"python skills_pessoais.py --restaurar --skills {destino}"))
            return res, 2

        res["detalhe"] = (
            f"Instalado: {len(plano['novos'])} arquivo(s) novo(s), "
            f"{len(plano['alterados'])} atualizado(s), "
            f"{len(plano['skills_removidas'])} skill(s) removida(s), "
            f"{len(plano['preservadas'])} pasta(s) do AFT preservada(s).")
        return res, 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def soma_esperada_de(zip_path, informada):
    if informada:
        return informada.strip().lower()
    lado = Path(str(zip_path) + ".sha256")
    if lado.is_file():
        campos = lado.read_text(encoding="utf-8").split()
        if not campos:
            raise SystemExit(f"ERRO: {lado.name} está vazio - não dá para "
                             "conferir a soma do pacote.")
        return campos[0].strip().lower()
    raise SystemExit(
        f"ERRO: não achei a soma de verificação do pacote.\n"
        f"  Esperava o arquivo {lado.name} ao lado dele, ou --sha256 <soma>.\n"
        "  Sem soma não dá para saber se o pacote chegou inteiro - e um pacote "
        "de origem desconhecida não se instala.")


def main():
    ap = argparse.ArgumentParser(
        description="Aplica um pacote do toolkit numa pasta de destino")
    modo = ap.add_mutually_exclusive_group(required=True)
    modo.add_argument("--aplicar", action="store_true",
                      help="executa a transação completa")
    modo.add_argument("--simular", action="store_true",
                      help="percorre tudo e relata, sem escrever nada")
    ap.add_argument("--confirmado", action="store_true",
                    help="segue mesmo com sinal suspeito na varredura - só "
                         "depois de o AFT ver o relatório e confirmar que a "
                         "atualização é legítima")
    ap.add_argument("--origem-local", required=True,
                    help="pacote .zip já baixado (dispensa rede e token)")
    ap.add_argument("--destino", required=True,
                    help="pasta instalada onde aplicar")
    ap.add_argument("--sha256", help="soma esperada (padrão: o arquivo "
                                     "<pacote>.sha256 ao lado do pacote)")
    args = ap.parse_args()

    zip_path = Path(args.origem_local).expanduser().resolve()
    destino = Path(args.destino).expanduser().resolve()
    if not zip_path.is_file():
        raise SystemExit(f"ERRO: pacote não encontrado: {zip_path}")
    if not destino.is_dir():
        raise SystemExit(
            f"ERRO: a pasta de destino não existe: {destino}\n"
            "  O aplicador atualiza uma instalação que já existe; ele não cria "
            "pasta nova (um caminho digitado errado viraria uma instalação "
            "fantasma).")

    soma = soma_esperada_de(zip_path, args.sha256)
    try:
        res, codigo = transacao(zip_path, destino, soma,
                                simular=args.simular, confirmado=args.confirmado)
    except Exception as e:
        # Quem chama le o stdout como JSON. Um traceback aqui deixaria a skill
        # sem nenhuma resposta para dar ao AFT - pior do que a propria falha.
        res = {"ok": False, "modo": "simular" if args.simular else "aplicar",
               "erro": "falha_inesperada", "destino": str(destino),
               "detalhe": (f"A atualização parou com um erro inesperado "
                           f"({type(e).__name__}: {e}). Se a pasta ficou "
                           "incompleta, a versão anterior está na pasta de "
                           f"backup ao lado de {destino}.")}
        codigo = 2
    print(json.dumps(res, ensure_ascii=False, indent=2))
    sys.exit(codigo)


if __name__ == "__main__":
    main()
