# -*- coding: utf-8 -*-
"""
atualizar_toolkit.py - Consulta o portal e aplica um pacote do toolkit.

Esta e a costura da atualizacao (issue #138): a logica que hoje mora no texto
da /aft-atualizar passa a morar aqui, onde da para ler, rodar e corrigir. Sao
dois caminhos ate o mesmo pacote:

  * PACOTE LOCAL (--origem-local), sem rede e sem codigo de acesso - e o que
    permite provar a transacao inteira contra uma pasta descartavel;
  * PORTAL (sem --origem-local), que pergunta a versao disponivel, mostra o
    changelog e baixa o pacote pelo endereco assinado.

Quem fala com o portal e o portal_toolkit.py, ao lado deste: e la que moram o
codigo de acesso, o registro da ultima consulta e as frases em portugues de
cada falha. Daqui para baixo, os dois caminhos sao o mesmo programa: o pacote
chega, e a transacao abaixo decide o que entra na pasta do AFT.

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
    python atualizar_toolkit.py --verificar
    python atualizar_toolkit.py --aplicar
    python atualizar_toolkit.py --origem-local <pacote.zip> --destino <pasta> --simular
    python atualizar_toolkit.py --origem-local <pacote.zip> --destino <pasta> --aplicar
    python atualizar_toolkit.py --gravar-token      (o codigo vem pelo stdin)
    python atualizar_toolkit.py --estado-token

Sem --destino, a pasta e ~/.claude/skills (a instalacao de verdade). Com
--origem-local, a soma esperada vem do arquivo <pacote.zip>.sha256 ao lado do
pacote (e o que o empacotar.py grava) ou de --sha256; pelo portal, ela vem da
propria resposta autenticada. Saida: um objeto JSON no stdout - so JSON, para
quem chama nao precisar interpretar prosa. Codigos de saida: 0 = feito (o que
inclui "nao ha novidade"), 1 = erro de uso, 2 = transacao recusada ou consulta
que nao pode ser respondida (falta codigo de acesso, portal fora do ar...).
Toda recusa traz em `detalhe` a frase pronta para o AFT, em portugues e com o
proximo passo.
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
import portal_toolkit as portal  # noqa: E402  (o lado cliente do portal)

try:  # console do Windows e cp1252
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

SKILLS_PADRAO = Path.home() / ".claude" / "skills"
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


# ------------------------------------------------------- o resgate da lapide

# Marcadores do toolkit inteiro: arquivos que existiram em toda versao e que a
# lapide (issue #144) apaga. Sao eles que apontam, no historico do git, o
# ultimo commit em que a pasta ainda tinha o toolkit.
MARCADORES = (MANIFESTO, "AGENTS.md", "COMO-INSTALAR.md")

LINK_PORTAL = "https://notebooks-aft.vercel.app/aft-toolkit"


def _git(args, cwd):
    """(codigo, saida) de um comando git - `saida` e o stdout quando deu certo
    e o stderr quando nao deu, que e o que serve para relatar a falha. Nunca
    levanta excecao: pasta que nao e repositorio git e um estado previsto, e
    nao um acidente."""
    try:
        r = subprocess.run(["git", *args], cwd=str(cwd), capture_output=True,
                           text=True, encoding="utf-8", errors="replace",
                           timeout=120)
    except (OSError, subprocess.SubprocessError) as e:
        return 1, str(e)
    if r.returncode:
        return r.returncode, (r.stderr or r.stdout or "").strip()
    return 0, (r.stdout or "").strip()


def estado_lapide(destino):
    """A pasta caiu na lapide? Devolve {commit, arquivos} quando SIM e ha como
    repor, None quando nao.

    Sim significa: a instalacao nao tem mais o manifesto (o toolkit saiu da
    pasta), ela e um clone git, e o historico ainda guarda um commit em que o
    toolkit estava inteiro. Foi o `git pull` da lapide que a deixou assim - o
    caminho antigo de atualizacao, que a skill velha da maquina do AFT manda
    seguir.
    """
    if (destino / MANIFESTO).is_file():
        return None  # a instalacao tem o toolkit: nao e o caso
    if not (destino / ".git").exists():
        return None  # instalacao por pacote: nao ha historico de onde repor
    for marcador in MARCADORES:
        codigo, apagou = _git(["log", "-1", "--format=%H", "--diff-filter=D",
                               "HEAD", "--", marcador], destino)
        if codigo or not apagou:
            continue
        anterior = apagou + "^"
        if _git(["cat-file", "-e", f"{anterior}:{marcador}"], destino)[0]:
            continue  # o commit anterior tambem nao tinha: marcador errado
        # -z (saida separada por NUL) e obrigatorio, nao enfeite: sem ele o git
        # devolve caminho acentuado ENTRE ASPAS e escapado ("Template/Roteiro
        # de inspe\303\247ao.md"), e esse nome nao existe para repor depois.
        codigo, lista = _git(["diff", "--name-only", "-z", "--diff-filter=D",
                              anterior, "HEAD"], destino)
        if codigo:
            continue
        arquivos = [l for l in lista.split("\0")
                    if l and not _ignorado(tuple(l.split("/")))]
        if arquivos:
            return {"commit": _git(["rev-parse", anterior], destino)[1],
                    "referencia": anterior, "arquivos": arquivos}
    return None


def mensagem_lapide(quantos):
    """A explicacao que o AFT le. Ela precisa dar, de uma vez, as duas noticias:
    o que aconteceu com a pasta dele (e que da para desfazer agora) e por onde
    volta a receber atualizacao."""
    return (
        f"A sua pasta de skills ficou só com o aviso de mudança: as {quantos} "
        "habilidades de fiscalização saíram dela quando o toolkit mudou de "
        "casa, e não foi erro seu.\n\n"
        "Nada se perdeu: a cópia anterior continua nesta máquina e eu consigo "
        "repor tudo agora mesmo, sem internet, para você não ficar sem "
        "ferramenta no meio de uma fiscalização.\n\n"
        "Próximo passo: eu reponho as habilidades e, em paralelo, você pede o "
        f"acesso em {LINK_PORTAL} com a sua conta Google. O código chega por "
        "e-mail uma única vez; a partir dele o toolkit volta a se atualizar "
        "sozinho, pelo portal.")


def cmd_resgatar(destino):
    """--resgatar: repoe, do proprio historico do git, o que a lapide apagou.

    Repoe SO o que sumiu: os arquivos que a lapide manteve (o README novo e a
    /aft-atualizar nova) ficam como estao. Se a versao velha da skill voltasse
    junto, ela mandaria dar `git pull` de novo e o AFT giraria em circulo.
    """
    lapide = estado_lapide(destino)
    if not lapide:
        return {"ok": False, "modo": "resgatar", "erro": "nada_a_resgatar",
                "destino": str(destino), "detalhe": (
                    "Não há nada para repor nesta pasta: ou as habilidades já "
                    "estão no lugar, ou esta instalação não tem de onde "
                    "repô-las. Nada foi alterado.")}, 2

    arquivos = lapide["arquivos"]
    # Em lotes: sao centenas de caminhos, e linha de comando tem limite (o do
    # Windows e o mais apertado).
    for i in range(0, len(arquivos), 100):
        codigo, saida = _git(["checkout", lapide["referencia"], "--",
                              *arquivos[i:i + 100]], destino)
        if codigo:
            # Falha no meio: os lotes anteriores JA repuseram arquivo. Dizer
            # "nada foi alterado" seria mentira - e a frase certa e a que manda
            # repetir, porque repor do mesmo commit e idempotente.
            return {"ok": False, "modo": "resgatar", "erro": "resgate_falhou",
                    "destino": str(destino), "repostos_antes_da_falha": i,
                    "detalhe": (
                        "Não consegui repor todas as habilidades a partir da "
                        f"cópia guardada nesta máquina ({saida or 'o git recusou'})."
                        + (f" {i} arquivo(s) já tinham voltado antes da falha; "
                           "repetir o comando é seguro e continua de onde parou."
                           if i else " Nada foi alterado na pasta.")
                        + " Nenhuma habilidade sua foi apagada.")}, 2
    # Os arquivos repostos ficam como arquivos do AFT, e nao como coisa
    # preparada para virar commit: o git nao e mais o caminho de atualizacao
    # desta pasta, e o proximo pacote do portal escreve por cima deles.
    _git(["reset", "--quiet"], destino)

    return {"ok": True, "modo": "resgatar", "erro": None,
            "destino": str(destino), "commit": lapide["commit"],
            "restaurados": len(arquivos), "detalhe": (
                f"Pronto: {len(arquivos)} arquivo(s) do toolkit voltaram para a "
                "sua pasta, a partir da cópia que já estava nesta máquina - "
                "nada foi baixado da internet. Suas habilidades próprias não "
                "foram tocadas. Feche e reabra o aplicativo para elas "
                "aparecerem de novo.")}, 0


# ------------------------------------------------------------------- o portal

def versao_instalada(destino):
    return ler_versao(destino / VERSAO).get("versao")


def _recusa(modo, estado, destino, **dados):
    """Uma falha da conversa com o portal, no mesmo formato JSON das demais.
    `detalhe` e sempre a frase pronta para o AFT - quem chama nao redige nada,
    e assim a mesma explicacao vale para a skill, para o /aft-bom-dia e para
    quem rodar o script na mao."""
    res = {"ok": False, "modo": modo, "estado": estado, "erro": estado,
           "destino": str(destino),
           "detalhe": portal.mensagem(estado, **dados)}
    if dados.get("detalhe_tecnico"):
        res["detalhe_tecnico"] = dados["detalhe_tecnico"]
    return res, 2


def consultar_portal(destino, base, forcar, precisa_da_url, modo):
    """Pergunta a versao disponivel. Devolve (resposta, res, codigo): com
    `res` preenchido, e para devolver isso a quem chamou e parar.

    `precisa_da_url` marca a diferenca entre olhar e baixar. O registro do dia
    nao guarda o endereco assinado do pacote (ele expira em minutos), entao
    quem vai baixar de fato repete a consulta - mas so DEPOIS de o registro ja
    ter dito, de graca, que existe versao nova. Sem novidade, nao ha chamada de
    rede nenhuma.
    """
    instalada = versao_instalada(destino)
    r = portal.verificar(instalada, base=base, forcar=forcar)
    if (precisa_da_url and r["estado"] == "ok" and r.get("de_registro")
            and r.get("versao") != instalada):
        r = portal.verificar(instalada, base=base, forcar=True)
    if r["estado"] != "ok":
        res, codigo = _recusa(modo, r["estado"], destino,
                              gmail=portal.gmail(),
                              detalhe_tecnico=r.get("detalhe_tecnico"))
        return r, res, codigo
    return r, None, 0


def cmd_verificar(destino, base, forcar):
    """--verificar: diz qual e a versao disponivel, se ha novidade e o que
    mudou. Nao baixa nada e nao escreve nada na pasta de skills."""
    instalada = versao_instalada(destino)
    # A lapide vem ANTES do portal, e de proposito: quem caiu nela e sempre o
    # AFT que nunca atualizou, e portanto nunca teve codigo de acesso. Se a
    # falta de codigo respondesse primeiro, ele ouviria "peca o acesso" sem
    # nunca saber que a pasta dele tinha ficado vazia.
    lapide = estado_lapide(destino)
    if lapide:
        return {"ok": False, "modo": "verificar", "estado": "lapide",
                "erro": "lapide", "destino": str(destino),
                "versao_instalada": instalada, "resgate_disponivel": True,
                "arquivos_a_repor": len(lapide["arquivos"]),
                "detalhe": mensagem_lapide(len(lapide["arquivos"]))}, 2

    r, res, codigo = consultar_portal(destino, base, forcar,
                                      precisa_da_url=False, modo="verificar")
    if res:
        res["versao_instalada"] = instalada
        return res, codigo

    ha_novidade = r["versao"] != instalada
    res = {"ok": True, "modo": "verificar",
           "estado": "ok" if ha_novidade else "sem_novidade",
           "erro": None, "destino": str(destino),
           "versao_instalada": instalada, "versao": r["versao"],
           "ha_novidade": ha_novidade, "novidades": r.get("novidades", ""),
           "consulta_de_hoje": bool(r.get("de_registro")),
           "detalhe": ""}
    if ha_novidade:
        res["detalhe"] = (f"Há uma versão nova do toolkit disponível: "
                          f"{r['versao']} (a sua é "
                          f"{instalada or 'de antes da numeração de versões'}).")
    else:
        res["detalhe"] = portal.mensagem("sem_novidade", versao=r["versao"])
    return res, 0


def baixar_do_portal(destino, base, forcar, tmp, modo):
    """Consulta, confere se ha novidade e traz o pacote. Devolve
    (zip, soma, versao, res, codigo) - com `res` preenchido, e para parar."""
    instalada = versao_instalada(destino)
    r, res, codigo = consultar_portal(destino, base, forcar,
                                      precisa_da_url=True, modo=modo)
    if res:
        return None, None, None, res, codigo

    if r["versao"] == instalada:
        # Sai barato: e o caso comum, e ele nao pode custar download nenhum.
        return None, None, None, {
            "ok": True, "modo": modo, "estado": "sem_novidade",
            "erro": None, "destino": str(destino),
            "versao_instalada": instalada, "versao": r["versao"],
            "ha_novidade": False,
            "detalhe": portal.mensagem("sem_novidade", versao=r["versao"]),
        }, 0

    if not r.get("url"):
        return (None, None, None,
                *_recusa(modo, "portal_indisponivel", destino,
                         detalhe_tecnico="o portal anunciou a versão "
                                         f"{r['versao']} mas não mandou o "
                                         "endereço do pacote"))

    # Nome fixo, e nao a versao que o portal anunciou: nome de arquivo vindo
    # de fora nunca decide onde se escreve (uma "versao" com barra ou com ".."
    # apontaria para fora da area temporaria).
    zip_path = tmp / "pacote.zip"
    try:
        portal.baixar(r["url"], zip_path)
    except Exception as e:
        # O endereco assinado tem validade curta: uma consulta guardada de
        # horas atras, uma queda no meio do download, ou o portal fora do ar
        # entre uma chamada e outra caem todos aqui.
        return (None, None, None,
                *_recusa(modo, "portal_indisponivel", destino,
                         detalhe_tecnico=f"o download do pacote falhou ({e})"))
    return zip_path, r["sha256"], r["versao"], None, 0


# ------------------------------------------------------- o codigo de acesso

def cmd_gravar_token():
    """--gravar-token: o codigo chega pela ENTRADA PADRAO, nunca como
    argumento (argumento fica no historico do terminal e nos logs). O valor
    nao e ecoado em lugar nenhum - a saida so diz onde ele ficou."""
    try:
        bruto = sys.stdin.read()
    except Exception as e:
        return {"ok": False, "erro": "leitura_falhou",
                "detalhe": f"Não consegui ler o código de acesso ({e})."}, 1
    try:
        alvo = portal.gravar_token(bruto)
    except ValueError as e:
        # Nome proprio, e nao "token_invalido": aquele e o do portal, e quer
        # dizer codigo antigo/cancelado. Sao problemas diferentes, com saidas
        # diferentes - regravar num caso, pedir outro no outro -, e foi
        # justamente confundi-los que custou uma manha em 30/08/2026.
        return {"ok": False, "erro": "codigo_malformado",
                "detalhe": f"O código de acesso não foi guardado: {e}."}, 1
    except OSError as e:
        return {"ok": False, "erro": "gravacao_falhou",
                "detalhe": f"Não consegui gravar o código de acesso ({e})."}, 2
    return {"ok": True, "erro": None, "arquivo": str(alvo), "detalhe": (
        "Código de acesso guardado. Ele fica na sua pasta de trabalho, fora da "
        "pasta de skills - assim a própria atualização não o apaga. Você não "
        "precisa digitá-lo de novo.")}, 0


def cmd_estado_token():
    """--estado-token: existe codigo de acesso nesta maquina? Responde sim ou
    nao e o caminho do arquivo - NUNCA o valor."""
    tem = portal.tem_token()
    return {"ok": True, "erro": None, "tem_token": tem,
            "arquivo": str(portal.caminho_token()),
            "gmail": portal.gmail(),
            "detalhe": ("Código de acesso ao portal já configurado nesta máquina."
                        if tem else portal.mensagem("sem_token"))}, 0


def main():
    ap = argparse.ArgumentParser(
        description="Consulta o portal e aplica um pacote do toolkit")
    modo = ap.add_mutually_exclusive_group(required=True)
    modo.add_argument("--aplicar", action="store_true",
                      help="executa a transação completa")
    modo.add_argument("--simular", action="store_true",
                      help="percorre tudo e relata, sem escrever nada")
    modo.add_argument("--verificar", action="store_true",
                      help="pergunta ao portal qual é a versão disponível e o "
                           "que mudou, sem baixar nem instalar nada")
    modo.add_argument("--gravar-token", action="store_true",
                      help="guarda o código de acesso ao portal (ele vem pela "
                           "entrada padrão, nunca como argumento)")
    modo.add_argument("--estado-token", action="store_true",
                      help="diz se já há código de acesso nesta máquina - "
                           "nunca mostra o valor")
    modo.add_argument("--resgatar", action="store_true",
                      help="repõe, do histórico do git desta máquina, as "
                           "habilidades que a lápide do repositório público "
                           "apagou da pasta (não usa rede)")
    ap.add_argument("--confirmado", action="store_true",
                    help="segue mesmo com sinal suspeito na varredura - só "
                         "depois de o AFT ver o relatório e confirmar que a "
                         "atualização é legítima")
    ap.add_argument("--origem-local",
                    help="pacote .zip já baixado (dispensa rede e código de "
                         "acesso); sem ele, o pacote vem do portal")
    ap.add_argument("--destino", default=str(SKILLS_PADRAO),
                    help="pasta instalada onde aplicar (padrão: ~/.claude/skills)")
    ap.add_argument("--sha256", help="soma esperada (padrão: o arquivo "
                                     "<pacote>.sha256 ao lado do pacote)")
    ap.add_argument("--portal", default=portal.PORTAL,
                    help="endereço do portal (para ensaio contra um portal de "
                         "mentira)")
    ap.add_argument("--forcar", action="store_true",
                    help="consulta o portal mesmo já tendo consultado hoje")
    args = ap.parse_args()

    if args.gravar_token or args.estado_token:
        res, codigo = (cmd_gravar_token() if args.gravar_token
                       else cmd_estado_token())
        print(json.dumps(res, ensure_ascii=False, indent=2))
        sys.exit(codigo)

    destino = Path(args.destino).expanduser().resolve()
    if not destino.is_dir():
        raise SystemExit(
            f"ERRO: a pasta de destino não existe: {destino}\n"
            "  O aplicador atualiza uma instalação que já existe; ele não cria "
            "pasta nova (um caminho digitado errado viraria uma instalação "
            "fantasma).")

    if args.resgatar:
        try:
            res, codigo = cmd_resgatar(destino)
        except Exception as e:
            # Mesma regra do --verificar: quem chama le o stdout como JSON, e um
            # traceback deixaria a skill sem nenhuma resposta para dar ao AFT.
            res, codigo = {
                "ok": False, "modo": "resgatar", "erro": "falha_inesperada",
                "destino": str(destino),
                "detalhe": (f"A reposição parou com um erro inesperado "
                            f"({type(e).__name__}: {e}). Nenhuma habilidade sua "
                            "foi apagada - o que o resgate faz é só repor.")}, 2
        print(json.dumps(res, ensure_ascii=False, indent=2))
        sys.exit(codigo)

    if args.verificar:
        try:
            res, codigo = cmd_verificar(destino, args.portal, args.forcar)
        except Exception as e:
            # Defeito nosso nao se disfarca de portal fora do ar: quem le o
            # JSON precisa saber a diferenca entre "tente mais tarde" e "isto
            # aqui esta quebrado".
            res, codigo = _recusa("verificar", "falha_inesperada", destino,
                                  detalhe_tecnico=f"{type(e).__name__}: {e}")
        print(json.dumps(res, ensure_ascii=False, indent=2))
        sys.exit(codigo)

    # A area temporaria cobre o pacote baixado do portal; com --origem-local
    # ela nasce vazia e e apagada no fim, sem custo.
    baixados = Path(tempfile.mkdtemp(prefix="aft-baixar-"))
    try:
        if args.origem_local:
            zip_path = Path(args.origem_local).expanduser().resolve()
            if not zip_path.is_file():
                raise SystemExit(f"ERRO: pacote não encontrado: {zip_path}")
            soma = soma_esperada_de(zip_path, args.sha256)
        else:
            zip_path, soma, _versao, res, codigo = baixar_do_portal(
                destino, args.portal, args.forcar, baixados,
                "simular" if args.simular else "aplicar")
            if res is not None:
                print(json.dumps(res, ensure_ascii=False, indent=2))
                sys.exit(codigo)
        res, codigo = _rodar_transacao(zip_path, destino, soma, args)
    finally:
        shutil.rmtree(baixados, ignore_errors=True)
    print(json.dumps(res, ensure_ascii=False, indent=2))
    sys.exit(codigo)


def _rodar_transacao(zip_path, destino, soma, args):
    try:
        return transacao(zip_path, destino, soma,
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
        return res, 2


if __name__ == "__main__":
    main()
