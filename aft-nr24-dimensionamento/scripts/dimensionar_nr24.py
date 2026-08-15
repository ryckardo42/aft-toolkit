#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""dimensionar_nr24.py — dimensionamento das instalações exigidas pela NR-24.

Cálculo determinístico das quantidades mínimas de instalações sanitárias (bacia
sifonada + lavatório), mictórios, chuveiros, vestiários (área e armários),
bebedouros, local para refeições e alojamento, a partir do número de homens e
mulheres do TURNO COM MAIOR CONTINGENTE (item 24.1.1 da NR-24).

Toda divisão é arredondada PARA CIMA (a norma diz "ou fração").

Uso:
    python dimensionar_nr24.py --homens 258 --mulheres 132 [opções]

Opções de contexto (o que o AFT constatou ou vai constatar em campo):
    --construcao {ate-23-09-2019,apos-24-09-2019}   data de construção (mictórios)
    --agentes          exposição/manuseio de material infectante, substâncias
                       tóxicas, irritantes ou aerodispersóides (24.2.2.1, 24.3.5 a)
    --poeira           contato com substâncias que provocam deposição de poeiras
                       que impregnam pele e roupas (24.2.2.1, 24.3.5 b)
    --esforco-calor    esforço físico ou calor intenso (24.3.5 b)
    --uniforme / --sem-uniforme   troca de vestimenta/uniforme no local (24.4.1 a)
    --sanitario-individual        instalação sanitária masculina essencialmente de
                                  uso individual (dispensa mictório, 24.2.1.1)
    --alojados-h N --alojados-m N  trabalhadores hospedados em alojamento (24.7)
    --beliche                      leito predominante é beliche (24.7.3 g, 24.9.7.1)
    --json                         saída apenas em JSON

Sem os flags de exposição, o script devolve o CENÁRIO BASE (sem exposição) e,
junto, o que cada hipótese mudaria — que é o formato útil antes da visita, quando
o AFT ainda não sabe o que vai encontrar.

Fonte: NR-24, redação da Portaria SEPRT nº 1.066/2019 (texto atualizado 2022).
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
import json
import sys

if hasattr(sys.stdout, "reconfigure"):     # console cp1252 no Windows
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def teto(n, divisor):
    """Divisão com arredondamento PARA CIMA — a "fração" de que fala a NR-24."""
    if n <= 0:
        return 0
    return -(-n // divisor)


def dec(x, casas=2):
    """Número no padrão brasileiro: vírgula decimal, sem separador de milhar."""
    return f"{x:.{casas}f}".replace(".", ",")


def area_vestiario(n):
    """Área mínima do vestiário, em m², para n usuários (itens 24.4.2 e 24.4.2.1).

    Até 750 usuários: área por trabalhador = 1,5 - (n/1000), aplicada sobre n.
    Acima de 750: 0,75 m² por trabalhador. As duas regras se encontram em 750
    (1,5 - 0,75 = 0,75), então a curva é contínua.
    """
    if n <= 0:
        return 0.0
    por_trabalhador = (1.5 - n / 1000) if n <= 750 else 0.75
    return round(n * por_trabalhador, 2)


# ---------------------------------------------------------------- mictórios
def mictorios(homens, construcao, individual=False):
    """Mictórios exigidos na instalação sanitária masculina (item 24.2.1.1).

    A alínea "b" (estabelecimento construído a partir de 24/09/2019) é uma regra
    progressiva fechada e devolve um número.

    A alínea "a" remete à NR-24 "com redação dada pela Portaria MTb nº 3.214/1978",
    que NÃO fixa proporção de mictórios por trabalhador. Nesse caso o script não
    devolve quantidade nenhuma: a exigência que se sustenta é a do CAPUT — a
    instalação sanitária masculina coletiva deve SER DOTADA de mictório. Ou seja,
    autua-se a ausência, não a insuficiência (ver references/nr24_parametros.md).
    """
    if homens <= 0:
        return {"exigidos": 0, "criterio": "quantidade",
                "regra": "sem homens no turno dimensionado",
                "memoria": [], "alerta": None}

    if individual:
        return {
            "exigidos": 0,
            "criterio": "dispensado",
            "regra": "dispensado — instalação sanitária essencialmente de uso individual",
            "memoria": ["O item 24.2.1.1 excetua da exigência de mictório a instalação "
                        "sanitária masculina essencialmente de uso individual."],
            "alerta": "Uso individual é fato a constatar em campo: confirme que a "
                      "instalação não é coletiva antes de dispensar o mictório.",
        }

    if construcao == "apos-24-09-2019":
        if homens <= 100:
            q = teto(homens, 20)
            mem = [f"{homens} homens (até 100): {homens} / 20 = "
                   f"{dec(homens / 20)} → arredondando para cima = {q} mictório(s)."]
        else:
            exc = homens - 100
            q_exc = teto(exc, 50)
            q = 5 + q_exc
            mem = ["1ª faixa (até 100 homens): 100 / 20 = 5 mictórios.",
                   f"2ª faixa (excedente de {homens} − 100 = {exc} homens): "
                   f"{exc} / 50 = {dec(exc / 50)} → arredondando para cima = {q_exc}.",
                   f"Total: 5 + {q_exc} = {q} mictórios."]
        return {"exigidos": q, "criterio": "quantidade",
                "regra": "1:20 até 100 homens e 1:50 no que exceder (24.2.1.1 \"b\")",
                "memoria": mem, "alerta": None}

    # ---- estabelecimento construído até 23/09/2019 (alínea "a")
    return {
        "exigidos": None,
        "criterio": "existencia",
        "regra": "existência de mictório, sem proporção por trabalhador "
                 "(24.2.1.1, caput e alínea \"a\")",
        "memoria": [
            "A alínea \"a\" remete à NR-24 na redação da Portaria MTb nº 3.214/1978, "
            "que não fixa proporção de mictórios por número de trabalhadores.",
            "O que se exige, pelo caput do item 24.2.1.1, é que a instalação sanitária "
            "masculina seja DOTADA de mictório — salvo quando essencialmente de uso "
            "individual.",
            "Fundamento da obrigatoriedade na norma antiga: ela trazia critério de "
            "dimensionamento do próprio mictório (item 24.1.6.1 — na calha de uso "
            "coletivo, cada segmento de 0,60 m equivale a 1 mictório tipo cuba). Não "
            "se dimensiona o que não é obrigatório.",
        ],
        "alerta": "Neste caso, autue a AUSÊNCIA de mictório na instalação sanitária "
                  "masculina coletiva, não a insuficiência de quantidade: não há "
                  "proporção por trabalhador a confrontar. Havendo mictório tipo calha, "
                  "converta por segmento de 0,60 m antes de concluir que não há.",
    }


# ---------------------------------------------------------- vestiário/armários
DIM_ARMARIOS = [
    ("Simples", "0,40 m (altura) x 0,30 m (largura) x 0,40 m (profundidade)", "24.4.6"),
    ("Duplo — divisão horizontal",
     "0,80 x 0,30 x 0,40 m, com prateleira formando 2 compartimentos de 0,40 m de "
     "altura (um para roupa comum, outro para roupa de trabalho)", "24.4.6.1 \"a\""),
    ("Duplo — divisão vertical",
     "0,80 x 0,50 x 0,40 m, com divisão vertical formando 2 compartimentos de 0,25 m "
     "de largura, em isolamento rigoroso", "24.4.6.1 \"b\""),
]


def armarios_e_verificacoes(exigido, homens, mulheres, agentes=False, poeira=False,
                            higienizacao_diaria=False, guarda_volumes=False,
                            obra=False):
    """Quantidade e tipo de armário + o que conferir em campo (item 24.4).

    Não é cálculo, é regra de decisão: a exposição obriga o duplo (24.4.5), a
    higienização diária ou a vestimenta descartável dispensa o duplo (24.4.5.1),
    o guarda-volumes dispensa o armário (24.4.7) e, sem vestiário, ainda resta o
    escaninho ou gaveta com tranca (24.4.8)."""
    exposicao = agentes or poeira
    checks = []

    if guarda_volumes:
        qtd_f = qtd_m = 0
        tipo = ("dispensados — a empresa oferece serviço de guarda-volumes para roupas "
                "e acessórios pessoais (item 24.4.7)")
        checks.append("Dispensa por guarda-volumes (24.4.7): confirme que o serviço "
                      "cobre roupas E acessórios pessoais de todos os trabalhadores, e "
                      "não apenas um balcão improvisado.")
    else:
        qtd_f, qtd_m = mulheres, homens
        if exposicao and not higienizacao_diaria:
            tipo = ("compartimentos duplos, ou dois armários simples por trabalhador "
                    "(item 24.4.5) — para isolar a roupa comum da roupa de trabalho "
                    "contaminada")
        elif exposicao and higienizacao_diaria:
            tipo = ("1 armário simples por trabalhador — a organização promove "
                    "higienização diária das vestimentas ou fornece vestimentas "
                    "descartáveis, o que dispensa o duplo (item 24.4.5.1)")
            checks.append("Dispensa do armário duplo (24.4.5.1): exija prova da "
                          "higienização diária (contrato de lavanderia, registro de "
                          "coleta e entrega) ou da vestimenta descartável. Declaração "
                          "verbal não sustenta a dispensa.")
        else:
            tipo = ("simples e/ou duplos, individuais, com sistema de trancamento "
                    "(item 24.4.3 \"e\")")

    if not exigido:
        # Sem vestiário não há armário de vestiário a contar: o que resta é a
        # obrigação do item 24.4.8 (escaninho, gaveta com tranca ou similar).
        checks.append("Estabelecimento desobrigado de vestiário ainda deve garantir "
                      "escaninho, gaveta com tranca ou similar que permita a guarda "
                      "individual dos pertences pessoais, ou serviço de guarda-volumes "
                      "(item 24.4.8). Não há hipótese de o trabalhador ficar sem onde "
                      "guardar seus pertences.")
        return {"feminino": 0, "masculino": 0,
                "tipo": "não se aplica — sem vestiário exigido, o que se exige é "
                        "escaninho, gaveta com tranca ou similar, ou guarda-volumes "
                        "(item 24.4.8)",
                "dimensoes_minimas": DIM_ARMARIOS, "verificacoes": checks}

    checks[:0] = [
        "Separação por sexo do vestiário — além da NR-24, o art. 389 da CLT obriga a "
        "instalação de vestiários com armários individuais privativos das mulheres "
        "(confirme a capitulação exata pela /aft-consulta antes de autuar).",
        "Uso rotativo de armário simples é admitido (24.4.4), MAS é proibido quando o "
        "armário guarda EPI ou vestimenta exposta a material infectante, substâncias "
        "tóxicas, irritantes ou que provoquem sujidade. Pergunte a quem usa se o "
        "armário é dele ou é compartilhado por turno.",
        "Sistema de trancamento em todos os armários (24.4.3 \"e\") — armário sem "
        "tranca não atende, ainda que individual.",
        "Meça um armário de cada tipo: a irregularidade de dimensão é frequente e só "
        "aparece com trena.",
        "Vestiário: piso e parede em material impermeável e lavável, ventilação para o "
        "exterior ou exaustão forçada, assentos laváveis em número compatível, e "
        "conservação, limpeza e higiene (24.4.3, alíneas \"a\" a \"d\").",
    ]
    if not obra:
        checks.append("Havendo exigência de chuveiro, ele deve fazer parte ou estar "
                      "anexo ao vestiário (item 24.3.5.1) — chuveiro em outro ponto do "
                      "estabelecimento não atende.")
    else:
        checks.append("No canteiro, o chuveiro é sempre exigido (18.5.3) e deve fazer "
                      "parte ou estar anexo ao vestiário (item 24.3.5.1 da NR-24, por "
                      "remissão do 18.5.2).")
    if exposicao and not higienizacao_diaria:
        checks.append("Armário duplo/duas unidades (24.4.5): confira o isolamento real "
                      "entre roupa comum e roupa de trabalho — dois vãos sem separação "
                      "efetiva não cumprem a finalidade da norma.")

    return {"feminino": qtd_f, "masculino": qtd_m, "tipo": tipo,
            "dimensoes_minimas": DIM_ARMARIOS, "verificacoes": checks}


# ------------------------------------------------------------- canteiro (NR-18)
def dimensionar_obra(homens, mulheres, frente=False, agentes=False, poeira=False,
                     higienizacao_diaria=False, guarda_volumes=False):
    """Canteiro de obras e frente de trabalho — NR-18, item 18.5.

    A NR-18 é norma SETORIAL e prevalece sobre a NR-24 no que dispõe (chuveiro
    1:10 e bebedouro 1:25, contra 1:20 e 1:50 da NR-24). No que ela não dispõe,
    a NR-24 se aplica por remissão expressa do item 18.5.2 ("no que for cabível"):
    é dela que vêm a separação por sexo (24.2.2), a área do vestiário (24.4.2), o
    regime do local para refeições (24.5) e o dimensionamento do alojamento (24.7).
    """
    total = homens + mulheres
    cs_f, cs_m = teto(mulheres, 20), teto(homens, 20)

    if frente:
        # 18.5.7 "a": só bacia sifonada com assento e tampo + lavatório, 1:20.
        # O texto não exige mictório nem chuveiro na frente de trabalho.
        resultado = {
            "modo": "frente-de-trabalho",
            "entrada": {"homens": homens, "mulheres": mulheres, "total": total,
                        "agentes": agentes, "poeira": poeira},
            "conjuntos_sanitarios": {
                "feminino": cs_f, "masculino": cs_m,
                "regra": "1 instalação sanitária (bacia sanitária sifonada, dotada de "
                         "assento com tampo, + lavatório) para cada 20 trabalhadores "
                         "ou fração (item 18.5.7 \"a\" da NR-18)",
                "composicao_masculina": "bacia sifonada com assento e tampo + lavatório",
                "composicao_feminina": "bacia sifonada com assento e tampo + lavatório",
                "memoria": [
                    f"Feminino: {mulheres} / 20 = {dec(mulheres / 20)} → {cs_f} "
                    "instalação(ões).",
                    f"Masculino: {homens} / 20 = {dec(homens / 20)} → {cs_m} "
                    "instalação(ões).",
                ],
            },
            "mictorios": {"exigidos": 0, "criterio": "nao_exigido",
                          "regra": "o item 18.5.7 \"a\" não exige mictório na frente de "
                                   "trabalho", "memoria": [], "alerta": None},
            "chuveiros": {"feminino": 0, "masculino": 0,
                          "regra": "o item 18.5.7 \"a\" não exige chuveiro na frente de "
                                   "trabalho (diferente do canteiro, item 18.5.3)"},
            "bebedouros": {
                "quantidade": teto(total, 25),
                "regra": "1 bebedouro ou dispositivo equivalente para cada 25 "
                         "trabalhadores ou fração — a NR-18 alcança expressamente as "
                         "frentes de trabalho (item 18.5.6); vedado o copo coletivo",
            },
            "local_refeicoes": {
                "regime": "obrigatório na frente de trabalho (item 18.5.7 \"b\")",
                "observacao": "Local para refeição com condições mínimas de conforto e "
                              "higiene e proteção contra as intempéries. Pode ser "
                              "atendido por convênio formal com estabelecimento próximo, "
                              "garantido o transporte dos trabalhadores (18.5.7.1).",
            },
            "verificacoes": [
                "Banheiro químico é admitido na frente de trabalho, desde que tenha "
                "mecanismo de descarga ou de isolamento dos dejetos, respiro e "
                "ventilação, material para lavagem e enxugo das mãos (proibida toalha "
                "coletiva) e higienização diária dos módulos (18.5.7 \"a\").",
                "Bacia \"turca\" (no nível do piso) não atende: a norma exige bacia "
                "SIFONADA e DOTADA DE ASSENTO COM TAMPO.",
                "Bebedouro: deslocamento máximo de 100 m no plano horizontal e 15 m no "
                "vertical (18.5.6.1); fora disso, água potável em recipientes portáteis "
                "herméticos nos postos de trabalho (18.5.6.2).",
            ],
            "avisos": [],
        }
        return resultado

    # ---- canteiro de obras (18.5.3)
    arm = armarios_e_verificacoes(True, homens, mulheres, agentes, poeira,
                                  higienizacao_diaria, guarda_volumes, obra=True)
    lav_f, lav_m = cs_f, cs_m
    lav_regra = ("1 lavatório por conjunto sanitário, isto é, 1 para cada 20 "
                 "trabalhadores ou fração (item 18.5.3 da NR-18)")
    avisos = []
    if agentes or poeira:
        lav_f = max(lav_f, teto(mulheres, 10))
        lav_m = max(lav_m, teto(homens, 10))
        lav_regra = ("1 lavatório para cada 10 trabalhadores ou fração — item 24.2.2.1 "
                     "da NR-24, aplicável por remissão do item 18.5.2 da NR-18, por ser "
                     "mais rigoroso que o 1:20 do item 18.5.3")

    return {
        "modo": "canteiro-de-obras",
        "entrada": {"homens": homens, "mulheres": mulheres, "total": total,
                    "agentes": agentes, "poeira": poeira},
        "conjuntos_sanitarios": {
            "feminino": cs_f, "masculino": cs_m,
            "regra": "1 conjunto sanitário para cada 20 trabalhadores ou fração "
                     "(item 18.5.3 da NR-18), separados por sexo (item 24.2.2 da NR-24, "
                     "por remissão do item 18.5.2)",
            "composicao_masculina": "bacia sanitária sifonada, dotada de assento com "
                                    "tampo + lavatório + mictório",
            "composicao_feminina": "bacia sanitária sifonada, dotada de assento com "
                                   "tampo + lavatório (sem mictório — o mictório é da "
                                   "instalação masculina, item 24.2.1.1 da NR-24)",
            "memoria": [
                f"Feminino: {mulheres} / 20 = {dec(mulheres / 20)} → {cs_f} conjunto(s).",
                f"Masculino: {homens} / 20 = {dec(homens / 20)} → {cs_m} conjunto(s).",
            ],
        },
        "lavatorios": {"feminino": lav_f, "masculino": lav_m, "regra": lav_regra},
        "mictorios": {
            "exigidos": cs_m, "criterio": "quantidade",
            "regra": "1 mictório por conjunto sanitário masculino, isto é, 1 para cada "
                     "20 homens ou fração (item 18.5.3 da NR-18)",
            "memoria": [f"O mictório integra o conjunto do item 18.5.3: {cs_m} "
                        f"conjunto(s) masculino(s) → {cs_m} mictório(s)."],
            "alerta": "No canteiro NÃO se aplica a regra progressiva da NR-24 (1:20 até "
                      "100 e 1:50 no excedente) nem a distinção por data de construção: "
                      "a NR-18 é setorial e fixa 1 mictório por conjunto de 20.",
        },
        "chuveiros": {
            "feminino": teto(mulheres, 10), "masculino": teto(homens, 10),
            "regra": "1 chuveiro para cada 10 trabalhadores ou fração (item 18.5.3 da "
                     "NR-18) — prevalece sobre o 1:20 do item 24.3.5 da NR-24",
        },
        "vestiario": {
            "exigido": True,
            "motivo": "sempre obrigatório no canteiro de obras (item 18.5.1 \"b\" da "
                      "NR-18) — não depende de uniforme nem de chuveiro, como na NR-24",
            "area_minima_m2": {"feminino": area_vestiario(mulheres),
                               "masculino": area_vestiario(homens)},
            "armarios": {"feminino": arm["feminino"], "masculino": arm["masculino"]},
            "tipo_armario": arm["tipo"],
            "dimensoes_minimas": arm["dimensoes_minimas"],
            "verificacoes": arm["verificacoes"],
        },
        "bebedouros": {
            "quantidade": teto(total, 25),
            "regra": "1 bebedouro ou dispositivo equivalente para cada 25 trabalhadores "
                     "ou fração, com água potável, filtrada e fresca (item 18.5.6 da "
                     "NR-18) — prevalece sobre o 1:50 do item 24.9.1.1 da NR-24; vedado "
                     "o copo coletivo",
        },
        "local_refeicoes": {
            "regime": ("obrigatório no canteiro (item 18.5.1 \"c\" da NR-18) — "
                       + ("mais de 30 trabalhadores: item 24.5.3 da NR-24"
                          if total > 30 else
                          "até 30 trabalhadores: item 24.5.2 da NR-24")),
            "observacao": "A NR-18 obriga o local para refeição em qualquer canteiro; as "
                          "características saem da NR-24 por remissão do item 18.5.2.",
        },
        "verificacoes": [
            "Deslocamento do posto de trabalho até a instalação sanitária mais próxima: "
            "no máximo 150 m (item 18.5.5).",
            "Bebedouro: deslocamento máximo de 100 m no plano horizontal e 15 m no "
            "vertical (18.5.6.1); fora disso, água potável em recipientes portáteis "
            "herméticos nos postos de trabalho (18.5.6.2).",
            "Bacia \"turca\" (no nível do piso) não atende: a norma exige bacia "
            "SIFONADA e DOTADA DE ASSENTO COM TAMPO (18.5.3).",
            "Havendo trabalhador alojado, o alojamento é obrigatório e deve ter cozinha "
            "(se houver preparo de refeições), local para refeição, instalação "
            "sanitária, lavanderia e área de lazer (18.5.4) — o dimensionamento dos "
            "dormitórios vem do item 24.7 da NR-24.",
            "O projeto da área de vivência do canteiro e de eventual frente de trabalho "
            "integra o PGR e deve ser elaborado por profissional legalmente habilitado "
            "(18.4.3 \"a\").",
        ],
        "avisos": avisos,
    }


# --------------------------------------------------------------- cenário NR-24
def dimensionar(homens, mulheres, construcao="apos-24-09-2019", agentes=False,
                poeira=False, esforco_calor=False, uniforme=None,
                sanitario_individual=False, higienizacao_diaria=False,
                guarda_volumes=False):
    total = homens + mulheres
    avisos = []

    # --- instalações sanitárias: bacia sifonada com assento e tampo + lavatório
    is_f, is_m = teto(mulheres, 20), teto(homens, 20)

    # --- lavatórios: 1 por instalação sanitária (24.2.1); 1:10 na exposição (24.2.2.1)
    if agentes or poeira:
        lav_f, lav_m = max(is_f, teto(mulheres, 10)), max(is_m, teto(homens, 10))
        lav_regra = ("1 lavatório para cada 10 trabalhadores ou fração "
                     "(item 24.2.2.1 — exposição/manuseio)")
    else:
        lav_f, lav_m = is_f, is_m
        lav_regra = ("1 lavatório por instalação sanitária, isto é, 1 para cada "
                     "20 trabalhadores ou fração (itens 24.2.1 e 24.2.2)")

    # --- chuveiros (24.3.5)
    if agentes:
        chu_f, chu_m = teto(mulheres, 10), teto(homens, 10)
        chu_regra = ("1 chuveiro para cada 10 trabalhadores ou fração "
                     "(item 24.3.5, alínea \"a\")")
    elif poeira or esforco_calor:
        chu_f, chu_m = teto(mulheres, 20), teto(homens, 20)
        chu_regra = ("1 chuveiro para cada 20 trabalhadores ou fração "
                     "(item 24.3.5, alínea \"b\")")
    else:
        chu_f = chu_m = 0
        chu_regra = ("não exigido pelo item 24.3.5 — nenhuma das hipóteses das "
                     "alíneas \"a\" e \"b\" foi informada")
        avisos.append("Chuveiro pode ser exigido por outra norma (NR-18, NR-31, "
                      "NR-32, NR-15) ainda que o item 24.3.5 não o exija aqui.")

    # --- vestiário (24.4.1) e sua área (24.4.2 / 24.4.2.1)
    exige_por_chuveiro = (chu_f + chu_m) > 0
    if uniforme is None:
        vest_exigido = True if exige_por_chuveiro else None
    else:
        vest_exigido = bool(uniforme) or exige_por_chuveiro
    arm = armarios_e_verificacoes(vest_exigido is not False, homens, mulheres,
                                  agentes, poeira, higienizacao_diaria, guarda_volumes)
    vestiario = {
        "exigido": vest_exigido,
        "motivo": ("exige chuveiro (24.4.1 \"b\")" if exige_por_chuveiro else
                   "troca de vestimenta/uniforme no local (24.4.1 \"a\")" if uniforme else
                   "a verificar em campo — depende de haver troca de vestimenta ou "
                   "imposição de uniforme trocado no local (24.4.1 \"a\")"),
        "area_minima_m2": {"feminino": area_vestiario(mulheres),
                           "masculino": area_vestiario(homens)},
        "armarios": {"feminino": arm["feminino"], "masculino": arm["masculino"]},
        "tipo_armario": arm["tipo"],
        "dimensoes_minimas": arm["dimensoes_minimas"],
        "verificacoes": arm["verificacoes"],
    }

    # --- bebedouros (24.9.1.1)
    bebedouros = teto(total, 50)

    # --- local para refeições (24.5)
    if total > 30:
        refeicoes = {"regime": "mais de 30 trabalhadores — item 24.5.3",
                     "observacao": "Local destinado a este fim e FORA da área de "
                                   "trabalho, com os requisitos das alíneas \"a\" a "
                                   "\"k\". O item 24.5.1.1 permite dividir os "
                                   "trabalhadores em grupos para a tomada de refeições: "
                                   "se cada grupo atendido for de até 30, aplica-se o "
                                   "item 24.5.2."}
    else:
        refeicoes = {"regime": "até 30 trabalhadores — item 24.5.2",
                     "observacao": "Local destinado ou adaptado ao fim, arejado, com "
                                   "assentos e mesas suficientes; nas proximidades, "
                                   "conservação/aquecimento das refeições, local e "
                                   "material para lavagem de utensílios e água potável "
                                   "(24.5.2.1)."}

    return {
        "entrada": {"homens": homens, "mulheres": mulheres, "total": total,
                    "construcao": construcao, "agentes": agentes, "poeira": poeira,
                    "esforco_calor": esforco_calor, "uniforme": uniforme,
                    "sanitario_individual": sanitario_individual},
        "instalacoes_sanitarias": {
            "feminino": is_f, "masculino": is_m,
            "regra": "1 instalação sanitária para cada 20 trabalhadores ou fração, "
                     "separadas por sexo (item 24.2.2)",
            "composicao": "cada instalação = 1 bacia sanitária sifonada, dotada de "
                          "assento com tampo, + 1 lavatório (item 24.2.1)",
            "memoria": [
                f"Feminino: {mulheres} / 20 = {dec(mulheres / 20)} → "
                f"{is_f} instalação(ões).",
                f"Masculino: {homens} / 20 = {dec(homens / 20)} → "
                f"{is_m} instalação(ões).",
            ],
        },
        "lavatorios": {"feminino": lav_f, "masculino": lav_m, "regra": lav_regra},
        "mictorios": mictorios(homens, construcao, sanitario_individual),
        "chuveiros": {"feminino": chu_f, "masculino": chu_m, "regra": chu_regra},
        "vestiario": vestiario,
        "bebedouros": {"quantidade": bebedouros,
                       "regra": "1 bebedouro para cada 50 trabalhadores ou fração, "
                                "sobre o total do turno (item 24.9.1.1)"},
        "local_refeicoes": refeicoes,
        "avisos": avisos,
    }


def cenarios_condicionais(homens, mulheres):
    """O que muda em cada hipótese de exposição — para levar impresso à visita."""
    return {
        "exposicao_agentes": {
            "hipotese": "exposição e manuseio de material infectante, substâncias "
                        "tóxicas, irritantes ou aerodispersóides que impregnem pele "
                        "e roupas (24.2.2.1 e 24.3.5 \"a\")",
            "lavatorios": {"feminino": teto(mulheres, 10), "masculino": teto(homens, 10)},
            "chuveiros": {"feminino": teto(mulheres, 10), "masculino": teto(homens, 10)},
            "armarios": "compartimentos duplos ou dois armários simples (24.4.5)",
        },
        "deposicao_de_poeiras": {
            "hipotese": "contato com substâncias que provocam deposição de poeiras "
                        "que impregnem pele e roupas (24.2.2.1 e 24.3.5 \"b\")",
            "lavatorios": {"feminino": teto(mulheres, 10), "masculino": teto(homens, 10)},
            "chuveiros": {"feminino": teto(mulheres, 20), "masculino": teto(homens, 20)},
            "armarios": "compartimentos duplos ou dois armários simples (24.4.5)",
        },
        "esforco_fisico_ou_calor_intenso": {
            "hipotese": "esforço físico ou condições ambientais de calor intenso "
                        "(24.3.5 \"b\")",
            "lavatorios": "sem alteração — o item 24.2.2.1 não alcança esta hipótese",
            "chuveiros": {"feminino": teto(mulheres, 20), "masculino": teto(homens, 20)},
            "armarios": "sem alteração",
        },
        "vestiario": {
            "hipotese": "troca de vestimenta/uniforme no local ou exigência de chuveiro "
                        "(24.4.1)",
            "area_minima_m2": {"feminino": area_vestiario(mulheres),
                               "masculino": area_vestiario(homens)},
            "armarios": {"feminino": mulheres, "masculino": homens},
        },
    }


# --------------------------------------------------------------- alojamento
def dimensionar_alojamento(alojados_h, alojados_m, beliche=False):
    """Item 24.7 da NR-24 — dormitórios, sanitários com chuveiro e armários."""
    if alojados_h <= 0 and alojados_m <= 0:
        return None

    def por_sexo(n):
        if n <= 0:
            return {"trabalhadores": 0, "quartos": 0, "sanitarios_com_chuveiro": 0,
                    "armarios": 0, "area_dormitorios_m2": 0.0}
        leitos = teto(n, 2) if beliche else n           # 1 beliche atende 2 pessoas
        return {"trabalhadores": n,
                "quartos": teto(n, 8),
                "sanitarios_com_chuveiro": teto(n, 10),
                "armarios": n,
                "area_dormitorios_m2": round(leitos * (4.5 if beliche else 3.0), 2)}

    return {
        "leito": "beliche" if beliche else "cama simples (leito individual)",
        "feminino": por_sexo(alojados_m),
        "masculino": por_sexo(alojados_h),
        "pe_direito_minimo_m": 3.0 if beliche else 2.5,
        "regras": [
            "Capacidade máxima de 8 trabalhadores por quarto (24.7.3 \"e\").",
            "1 instalação sanitária com chuveiro para cada 10 trabalhadores "
            "hospedados ou fração (24.7.2 \"c\").",
            "Área mínima de 3,00 m² por cama simples ou 4,50 m² por beliche, "
            "incluídas circulação e armário (24.7.3 \"g\") — 1 beliche atende 2 "
            "trabalhadores.",
            "Vedado o uso de 3 ou mais camas na mesma vertical (24.7.3 \"a\").",
            "Dormitórios separados por sexo (24.7.2 \"d\"); armários individuais com "
            "sistema de trancamento (24.7.3 \"f\" e 24.7.3.2).",
            "Pé-direito mínimo de 2,50 m, ou 3,00 m nos quartos com beliche, na "
            "ausência de código de obras local (24.9.7.1).",
            "Sanitários que não integrem o dormitório: a no máximo 50 m, ligados "
            "por passagem com piso lavável e cobertura (24.7.2.1).",
        ],
    }


# -------------------------------------------------------------------- saída
def imprime_obra(r, aloj):
    e = r["entrada"]
    frente = r["modo"] == "frente-de-trabalho"
    titulo = ("FRENTE DE TRABALHO — NR-18, item 18.5.7" if frente else
              "CANTEIRO DE OBRAS — NR-18, item 18.5")
    print(f"{titulo}: {e['total']} trabalhadores "
          f"({e['homens']} homens, {e['mulheres']} mulheres)")
    print("Base: turno com maior contingente (item 24.1.1 da NR-24, por remissão do "
          "item 18.5.2 da NR-18)")
    print()

    cs = r["conjuntos_sanitarios"]
    print("CONJUNTOS SANITÁRIOS — " + cs["regra"])
    for linha in cs["memoria"]:
        print(f"  · {linha}")
    print(f"  Masculino: {cs['masculino']} — {cs['composicao_masculina']}")
    print(f"  Feminino: {cs['feminino']} — {cs['composicao_feminina']}")
    print()

    if not frente:
        lav = r["lavatorios"]
        print(f"LAVATÓRIOS — {lav['regra']}")
        print(f"  Feminino: {lav['feminino']}   ·   Masculino: {lav['masculino']}")
        print()

    mic = r["mictorios"]
    print(f"MICTÓRIOS — {mic['regra']}")
    for linha in mic["memoria"]:
        print(f"  · {linha}")
    print(f"  Masculino: {mic['exigidos']}   ·   Feminino: 0")
    if mic["alerta"]:
        print(f"  !! {mic['alerta']}")
    print()

    chu = r["chuveiros"]
    print(f"CHUVEIROS — {chu['regra']}")
    print(f"  Feminino: {chu['feminino']}   ·   Masculino: {chu['masculino']}")
    print()

    if not frente:
        imprime_vestiario(r["vestiario"])

    print(f"BEBEDOUROS — {r['bebedouros']['regra']}")
    print(f"  {r['bebedouros']['quantidade']} bebedouro(s) para o total de {e['total']}")
    print()

    ref = r["local_refeicoes"]
    print(f"LOCAL PARA REFEIÇÕES — {ref['regime']}")
    print(f"  {ref['observacao']}")
    print()

    if aloj:
        imprime_alojamento(aloj)

    print("A VERIFICAR EM CAMPO:")
    for chk in r["verificacoes"]:
        print(f"  · {chk}")
    print()
    for a in r["avisos"]:
        print(f"  !! {a}")
    print("  !! A NR-18 de 2022 NÃO exige água quente nos chuveiros do canteiro — essa "
          "exigência era da redação anterior (item 18.4.2.7.1), revogada. Não a inclua "
          "em auto sem outra base.")
    print("  !! O dimensionamento é do TURNO COM MAIOR CONTINGENTE. Se o número acima "
          "vier do efetivo total da obra e houver mais de um turno, ele é teto, não a "
          "base exata — confirme o maior turno em campo.")


def medida_curta(medida: str) -> str:
    """De "0,40 m (altura) x 0,30 m (largura) x 0,40 m (profundidade)" para
    "0,40x0,30x0,40 m" — a medida por extenso só cabe no .docx."""
    n = [t for t in medida.replace("x", " ").split()
         if "," in t and t[0].isdigit()]
    return "x".join(n[:3]) + " m"


def imprime_vestiario(v):
    """Vestiário em três linhas: se é devido, quanto, e a medida do armário.

    A checklist de campo (trancamento, uso rotativo, dispensas do 24.4) vive no
    .docx que o AFT leva na visita — aqui ela só afasta o número da vista."""
    rotulo = {True: "SIM", False: "NÃO", None: "A VERIFICAR"}[v["exigido"]]
    print(f"VESTIÁRIO — exigido: {rotulo} ({v['motivo']})")
    if v["exigido"] is not False:
        print(f"  Sendo devido: {dec(v['area_minima_m2']['feminino'])} m² (F) e "
              f"{dec(v['area_minima_m2']['masculino'])} m² (M) · "
              f"{v['armarios']['feminino']} armários (F) e "
              f"{v['armarios']['masculino']} (M), individuais e com trancamento "
              '(24.4.3 "e")')
    medidas = " · ".join(
        f"{' '.join(nome.replace('—', ' ').replace('divisão', ' ').split()).lower()}"        f" {medida_curta(medida)}"
        for nome, medida, _ in v["dimensoes_minimas"])
    print(f"  Armário (24.4.6 e 24.4.6.1): {medidas}")
    print()


def imprime_alojamento(aloj):
    print(f"ALOJAMENTO (item 24.7 da NR-24) — leito: {aloj['leito']}")
    for sexo in ("feminino", "masculino"):
        d = aloj[sexo]
        if d["trabalhadores"]:
            print(f"  {sexo.capitalize()} ({d['trabalhadores']} hospedados): "
                  f"{d['quartos']} quarto(s) · {d['sanitarios_com_chuveiro']} "
                  f"sanitário(s) com chuveiro · {d['armarios']} armário(s) · "
                  f"área mínima {dec(d['area_dormitorios_m2'])} m²")
    print(f"  Pé-direito mínimo: {dec(aloj['pe_direito_minimo_m'])} m")
    for reg in aloj["regras"]:
        print(f"  · {reg}")
    print()


def linha_quadro(rotulo, fem, masc, item):
    print(f"  {rotulo:<38}{fem:>9}{masc:>11}   {item}")


def imprime(r, aloj, cen):
    """Quadro do que e devido, e so.

    O AFT le isto para contar bacia, mictorio e bebedouro no percurso: o numero
    tem de estar visivel de relance. Memoria de calculo so onde a conta nao e
    obvia (mictorio progressivo); cenarios de exposicao viram uma linha, porque
    antes da visita sao hipotese — confirmada alguma, roda-se de novo com o flag."""
    e = r["entrada"]
    construida = ("a partir de 24/09/2019" if e["construcao"] == "apos-24-09-2019"
                  else "até 23/09/2019")
    ins, lav, mic = r["instalacoes_sanitarias"], r["lavatorios"], r["mictorios"]
    chu = r["chuveiros"]

    print(f"NR-24 — {e['total']} trabalhadores ({e['homens']} homens, "
          f"{e['mulheres']} mulheres) · construído {construida}")
    print("Base: turno com maior contingente (item 24.1.1)")
    print()
    print(f"  {'':<38}{'Feminino':>9}{'Masculino':>11}   Item")
    linha_quadro("Bacias sanitárias (assento e tampo)", ins["feminino"],
                 ins["masculino"], "24.2.1 e 24.2.2")
    linha_quadro("Lavatórios", lav["feminino"], lav["masculino"], "24.2.1")
    linha_quadro("Mictórios",
                 "—", mic["exigidos"] if mic["exigidos"] is not None else "existir",
                 "24.2.1.1")
    linha_quadro("Chuveiros", chu["feminino"], chu["masculino"], "24.3.5")
    linha_quadro("Bebedouros (total do turno)", "", r["bebedouros"]["quantidade"],
                 "24.9.1.1")
    print()
    for linha in mic["memoria"]:
        print(f"  {linha}")
    if mic["alerta"]:
        print(f"  !! {mic['alerta']}")
    print()

    imprime_vestiario(r["vestiario"])

    ref = r["local_refeicoes"]
    print(f"LOCAL PARA REFEIÇÕES — {ref['regime']}")
    print(f"  {ref['observacao']}")
    print()

    if aloj:
        imprime_alojamento(aloj)

    if cen:
        print("  !! Havendo exposição a agente infectante/químico, poeira que impregne "
              "pele e roupas, esforço físico ou calor intenso, sobem os lavatórios e "
              "passam a ser exigidos chuveiros (24.2.2.1 e 24.3.5). Confirmado em "
              "campo, rode de novo com --agentes, --poeira ou --esforco-calor.")
    for a in r["avisos"]:
        print(f"  !! {a}")
    print("  !! O dimensionamento é do TURNO COM MAIOR CONTINGENTE (24.1.1). Se o "
          "número acima vier do efetivo total do estabelecimento e houver mais de um "
          "turno, ele é teto, não a base exata — confirme o maior turno em campo.")
    print("  !! Verifique se incide algum Anexo da NR-24 (I: shopping center; "
          "II: trabalho externo; III: transporte público rodoviário) — os Anexos têm "
          "proporções próprias.")


def main():
    ap = argparse.ArgumentParser(description="Dimensionamento da NR-24.")
    ap.add_argument("--homens", type=int, required=True)
    ap.add_argument("--mulheres", type=int, required=True)
    ap.add_argument("--construcao", choices=("ate-23-09-2019", "apos-24-09-2019"),
                    default="apos-24-09-2019")
    ap.add_argument("--agentes", action="store_true")
    ap.add_argument("--poeira", action="store_true")
    ap.add_argument("--esforco-calor", dest="esforco_calor", action="store_true")
    ap.add_argument("--uniforme", dest="uniforme", action="store_true", default=None)
    ap.add_argument("--sem-uniforme", dest="uniforme", action="store_false")
    ap.add_argument("--sanitario-individual", dest="sanitario_individual",
                    action="store_true")
    ap.add_argument("--higienizacao-diaria", dest="higienizacao_diaria",
                    action="store_true",
                    help="a organização higieniza as vestimentas diariamente ou fornece "
                         "descartáveis — dispensa o armário duplo (item 24.4.5.1)")
    ap.add_argument("--guarda-volumes", dest="guarda_volumes", action="store_true",
                    help="há serviço de guarda-volumes — dispensa armários (24.4.7)")
    ap.add_argument("--alojados-h", dest="alojados_h", type=int, default=0)
    ap.add_argument("--alojados-m", dest="alojados_m", type=int, default=0)
    ap.add_argument("--beliche", action="store_true")
    ap.add_argument("--obra", action="store_true",
                    help="canteiro de obras — aplica a NR-18 (item 18.5), setorial")
    ap.add_argument("--frente-trabalho", dest="frente", action="store_true",
                    help="frente de trabalho da construção (item 18.5.7 da NR-18)")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    if a.homens < 0 or a.mulheres < 0:
        ap.error("número de trabalhadores não pode ser negativo")
    if a.homens + a.mulheres == 0:
        ap.error("informe ao menos um trabalhador em --homens ou --mulheres")

    aloj = dimensionar_alojamento(a.alojados_h, a.alojados_m, a.beliche)

    if a.obra or a.frente:
        r = dimensionar_obra(a.homens, a.mulheres, frente=a.frente,
                             agentes=a.agentes, poeira=a.poeira,
                             higienizacao_diaria=a.higienizacao_diaria,
                             guarda_volumes=a.guarda_volumes)
        r["alojamento"] = aloj
        r["cenarios"] = None
        if a.json:
            print(json.dumps(r, ensure_ascii=False, indent=2))
            return
        imprime_obra(r, aloj)
        return

    r = dimensionar(a.homens, a.mulheres, a.construcao, a.agentes, a.poeira,
                    a.esforco_calor, a.uniforme, a.sanitario_individual,
                    a.higienizacao_diaria, a.guarda_volumes)
    r["modo"] = "nr24"
    # os cenários só fazem sentido enquanto o AFT não sabe o que vai encontrar
    cen = (cenarios_condicionais(a.homens, a.mulheres)
           if not (a.agentes or a.poeira or a.esforco_calor) else None)

    r["alojamento"] = aloj
    r["cenarios"] = cen

    if a.json:
        print(json.dumps(r, ensure_ascii=False, indent=2))
        return
    imprime(r, aloj, cen)


if __name__ == "__main__":
    main()
