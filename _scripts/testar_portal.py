# -*- coding: utf-8 -*-
"""
testar_portal.py - Prova o cliente do portal contra um portal de mentira.

O portal de verdade ainda nao existe (ele e outro repositorio, ver a issue
#138). O que existe e o CONTRATO - e contrato se exercita: este programa sobe
um servidor local que responde exatamente o que o portal promete responder, e
manda o atualizar_toolkit.py conversar com ele.

O que se prova aqui:

  * a consulta devolve versao, se ha novidade e o changelog, SEM baixar nada;
  * a consulta acontece no maximo uma vez por dia (a segunda sai do registro,
    sem tocar a rede) - e --forcar fura o registro quando o AFT manda;
  * o codigo de acesso e lido de arquivo proprio, na pasta de trabalho do AFT,
    e nunca do aft-config.md;
  * o codigo de acesso nao aparece em saida nenhuma, nem no ticket de erro;
  * sem codigo, codigo recusado, e-mail sem acesso e nada de novo: cada um com
    a sua mensagem em portugues e o proximo passo;
  * ponta a ponta: o pacote baixado do portal de mentira e realmente instalado
    na pasta de destino.

Nada real e tocado: nem ~/.claude/skills, nem a pasta de trabalho do AFT (o
PASTA_AFT aponta para uma pasta descartavel durante o teste inteiro).

Uso:
    python testar_portal.py
    python testar_portal.py --manter    # nao apaga a area de teste no fim
"""

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

AQUI = Path(__file__).resolve().parent
PY = sys.executable or "python3"

TOKEN_BOM = "tk-de-mentira-0123456789abcdef"
GMAIL_BOM = "aft.de.mentira@exemplo.invalido"
GMAIL_SEM_ACESSO = "outro.aft@exemplo.invalido"

falhas = []


def checar(condicao, descricao, extra=""):
    marca = "OK  " if condicao else "FALHOU"
    print(f"  [{marca}] {descricao}" + (f"\n           {extra}" if extra and not condicao else ""))
    if not condicao:
        falhas.append(descricao)


# ------------------------------------------------------- o portal de mentira

class PortalDeMentira(HTTPServer):
    """Responde o contrato da issue #138 e conta quantas vezes foi chamado -
    e a contagem que prova a regra de uma consulta por dia."""

    manifesto = {}          # o que a rota anuncia: versao, sha256, novidades
    pacote = None           # Path do .zip que a url assinada entrega
    consultas = 0


class Rota(BaseHTTPRequestHandler):
    def log_message(self, *a):  # sem ruido no meio do relatorio
        pass

    def _responder(self, codigo, corpo):
        dados = json.dumps(corpo).encode("utf-8")
        self.send_response(codigo)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(dados)))
        self.end_headers()
        self.wfile.write(dados)

    def do_GET(self):
        # A "url assinada": aqui ela e so um caminho combinado, mas o que
        # importa e que ela vem da resposta autenticada, e nao adivinhada.
        if self.path.startswith("/pacote-assinado") and self.server.pacote:
            dados = Path(self.server.pacote).read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "application/zip")
            self.send_header("Content-Length", str(len(dados)))
            self.end_headers()
            self.wfile.write(dados)
            return
        self.send_error(404)

    def do_POST(self):
        tamanho = int(self.headers.get("Content-Length") or 0)
        try:
            pedido = json.loads(self.rfile.read(tamanho).decode("utf-8"))
        except ValueError:
            return self._responder(400, {"erro": "corpo ilegível"})
        self.server.consultas += 1

        if pedido.get("token") != TOKEN_BOM:
            return self._responder(401, {"erro": "token_invalido"})
        if pedido.get("gmail") != GMAIL_BOM:
            return self._responder(403, {"erro": "sem_acesso"})
        resposta = dict(self.server.manifesto)
        resposta["url"] = f"http://127.0.0.1:{self.server.server_port}/pacote-assinado"
        return self._responder(200, resposta)


def subir_portal():
    servidor = PortalDeMentira(("127.0.0.1", 0), Rota)
    threading.Thread(target=servidor.serve_forever, daemon=True).start()
    return servidor, f"http://127.0.0.1:{servidor.server_port}"


# ------------------------------------------------------------------ o roteiro

def rodar(base, ambiente):
    from testar_aplicador import montar_pacotes  # o mesmo empacotador de verdade

    print("Montando os pacotes de teste com o empacotar.py...")
    v1, v2, _v3, _envenenado = montar_pacotes(base)

    destino = base / "skills-de-mentira"
    destino.mkdir()
    pasta_aft = Path(ambiente["PASTA_AFT"])
    pasta_aft.mkdir(parents=True, exist_ok=True)
    (pasta_aft / "aft-config.md").write_text(
        f'---\ngmail: "{GMAIL_BOM}"\ncif: "000000"\n---\n', encoding="utf-8")

    servidor, endereco = subir_portal()
    servidor.pacote = v2
    servidor.manifesto = {
        "versao": versao_do_pacote(v2),
        "sha256": hashlib.sha256(Path(v2).read_bytes()).hexdigest(),
        "novidades": ("## 29/08/2026\n\n**O toolkit passa a chegar por "
                      "pacote.** Você recebe uma versão, e não dezenas de "
                      "commits.\n"),
    }

    def rodar_script(*args, entrada=None):
        r = subprocess.run([PY, str(AQUI / "atualizar_toolkit.py"), *args],
                           input=entrada, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", env=ambiente)
        try:
            return r.returncode, json.loads(r.stdout), r.stdout + r.stderr
        except ValueError:
            raise SystemExit(f"saída não era JSON:\n{r.stdout}\n{r.stderr}")

    comum = ["--destino", str(destino), "--portal", endereco]

    print("\n1. Sem código de acesso nesta máquina")
    codigo, res, bruto = rodar_script("--verificar", *comum)
    checar(codigo == 2 and res["estado"] == "sem_token",
           "a falta de código de acesso tem estado próprio", str(res.get("estado")))
    checar("código de acesso" in res["detalhe"]
           and "Próximo passo" in res["detalhe"],
           "a mensagem é em português e diz o próximo passo", res["detalhe"])
    checar(servidor.consultas == 0,
           "sem código de acesso, o portal nem chega a ser chamado")

    codigo, res, _ = rodar_script("--estado-token", *comum)
    checar(codigo == 0 and res["tem_token"] is False,
           "o estado do código de acesso responde 'não configurado'")

    print("\n2. Guardar o código de acesso")
    codigo, res, bruto = rodar_script("--gravar-token", *comum, entrada=TOKEN_BOM + "\n")
    arquivo = Path(res.get("arquivo", ""))
    checar(codigo == 0 and res["ok"], "gravou o código de acesso", str(res))
    checar(TOKEN_BOM not in bruto, "o código de acesso não aparece na saída")
    checar(arquivo.is_file() and arquivo.parent == pasta_aft,
           "o código foi guardado na pasta de trabalho do AFT", str(arquivo))
    checar(str(destino) not in str(arquivo),
           "e NÃO dentro da pasta de skills, que a atualização substitui")
    cfg = (pasta_aft / "aft-config.md").read_text(encoding="utf-8")
    checar(TOKEN_BOM not in cfg, "o código de acesso não foi parar no aft-config.md")

    print("\n3. Código de acesso recusado pelo portal")
    arquivo.write_text("tk-cancelado-999\n", encoding="utf-8")
    codigo, res, bruto = rodar_script("--verificar", *comum)
    checar(codigo == 2 and res["estado"] == "token_invalido",
           "o código recusado tem estado próprio", str(res.get("estado")))
    checar("Próximo passo" in res["detalhe"] and "novo" in res["detalhe"],
           "a mensagem conduz a pedir um código novo", res["detalhe"])
    checar("tk-cancelado-999" not in bruto,
           "nem o código recusado aparece na saída")

    print("\n4. E-mail sem acesso ao toolkit")
    arquivo.write_text(TOKEN_BOM + "\n", encoding="utf-8")
    (pasta_aft / "aft-config.md").write_text(
        f'---\ngmail: "{GMAIL_SEM_ACESSO}"\n---\n', encoding="utf-8")
    codigo, res, _ = rodar_script("--verificar", *comum)
    checar(codigo == 2 and res["estado"] == "sem_acesso",
           "o e-mail sem acesso tem estado próprio", str(res.get("estado")))
    checar(GMAIL_SEM_ACESSO in res["detalhe"] and "liberação" in res["detalhe"],
           "a mensagem diz qual e-mail e conduz ao pedido de liberação",
           res["detalhe"])

    print("\n4b. Ficha de configuração sem o e-mail do cadastro")
    (pasta_aft / "aft-config.md").write_text("---\ncif: \"000000\"\n---\n",
                                             encoding="utf-8")
    codigo, res, _ = rodar_script("--verificar", *comum)
    checar(codigo == 2 and res["estado"] == "sem_gmail",
           "sem e-mail na ficha, o script pede o e-mail em vez de falhar",
           str(res.get("estado")))
    checar("Próximo passo" in res["detalhe"],
           "com o próximo passo em português", res["detalhe"])

    print("\n5. Consulta com tudo em ordem (sem baixar nada)")
    (pasta_aft / "aft-config.md").write_text(
        f'---\ngmail: "{GMAIL_BOM}"\n---\n', encoding="utf-8")
    antes = retrato(destino)
    servidor.consultas = 0
    codigo, res, _ = rodar_script("--verificar", *comum)
    checar(codigo == 0 and res["ok"] and res["ha_novidade"] is True,
           "a consulta anuncia que há novidade", str(res.get("detalhe")))
    checar(res["versao"] == servidor.manifesto["versao"],
           "a consulta devolve a versão disponível")
    checar("pacote" in res["novidades"],
           "a consulta devolve o changelog", res.get("novidades", ""))
    checar(res["versao_instalada"] is None,
           "e diz que não há versão instalada nesta pasta ainda")
    checar(retrato(destino) == antes, "a consulta não escreveu nada no destino")

    print("\n6. Uma consulta por dia")
    codigo, res, _ = rodar_script("--verificar", *comum)
    checar(servidor.consultas == 1,
           "a segunda consulta do dia não chamou o portal de novo",
           f"{servidor.consultas} chamadas")
    checar(res["consulta_de_hoje"] is True and res["ha_novidade"] is True,
           "e mesmo assim respondeu a mesma coisa")
    registro = pasta_aft / ".aft-toolkit-consulta.json"
    checar(registro.is_file(), "o registro da consulta ficou na pasta do AFT")
    checar(TOKEN_BOM not in registro.read_text(encoding="utf-8")
           and "url" not in json.loads(registro.read_text(encoding="utf-8"))["resposta"],
           "o registro não guarda nem o código de acesso nem o endereço assinado")
    codigo, res, _ = rodar_script("--verificar", *comum, "--forcar")
    checar(servidor.consultas == 2, "--forcar fura o registro do dia",
           f"{servidor.consultas} chamadas")

    print("\n7. Instalar o pacote que veio do portal")
    codigo, res, _ = rodar_script("--aplicar", *comum)
    checar(codigo == 0 and res["ok"], "aplicou o pacote baixado do portal",
           str(res.get("detalhe")) + " / " + str(res.get("erro")))
    checar((destino / "aft-teste-novata" / "SKILL.md").is_file(),
           "a skill do pacote apareceu na pasta de destino")
    checar((destino / "_scripts" / "versao.txt").is_file(),
           "o carimbo de versão foi instalado")

    print("\n8. Nada de novo")
    servidor.consultas = 0
    codigo, res, _ = rodar_script("--verificar", *comum, "--forcar")
    checar(codigo == 0 and res["ok"] and res["ha_novidade"] is False
           and res["estado"] == "sem_novidade",
           "depois de instalar, a consulta diz que não há novidade",
           str(res.get("detalhe")))
    checar("mais recente" in res["detalhe"], "com mensagem própria em português",
           res["detalhe"])
    codigo, res, _ = rodar_script("--aplicar", *comum)
    checar(codigo == 0 and res["estado"] == "sem_novidade",
           "e o --aplicar sai barato, sem instalar nada", str(res.get("estado")))

    print("\n9. Soma de verificação divergente (o portal anunciou outra coisa)")
    servidor.manifesto = dict(servidor.manifesto, versao="9999.99.99-mentira",
                              sha256="0" * 64)
    antes = retrato(destino)
    codigo, res, _ = rodar_script("--aplicar", *comum, "--forcar")
    checar(codigo == 2 and res["erro"] == "soma_divergente",
           "recusou o pacote cuja soma não bate com a anunciada",
           str(res.get("erro")))
    checar(retrato(destino) == antes, "e nada foi escrito na pasta de destino")

    print("\n10. Portal fora do ar")
    servidor.shutdown()
    codigo, res, _ = rodar_script("--verificar", *comum, "--forcar")
    checar(codigo == 2 and res["estado"] == "portal_indisponivel",
           "o portal fora do ar tem estado próprio", str(res.get("estado")))
    checar("Nada foi alterado" in res["detalhe"],
           "e a mensagem tranquiliza o AFT", res["detalhe"])

    print("\n11. O ticket de erro não leva o código de acesso junto")
    arquivo.write_text(TOKEN_BOM + "\n", encoding="utf-8")
    r = subprocess.run(
        [PY, str(AQUI / "erro_ticket.py"), "--titulo", "ensaio",
         "--mensagem", f"o script quebrou com o codigo {TOKEN_BOM} na mao"],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        env=ambiente)
    tickets = sorted((pasta_aft / "tickets").glob("*.md")) if (pasta_aft / "tickets").is_dir() else []
    checar(bool(tickets), "o ticket foi gravado na pasta de mentira",
           r.stdout + r.stderr)
    if tickets:
        texto = tickets[-1].read_text(encoding="utf-8")
        checar(TOKEN_BOM not in texto,
               "o código de acesso não aparece no ticket, nem vindo do traceback")
        checar("<CODIGO DE ACESSO>" in texto,
               "ele sai escondido, e não apagado em silêncio")
        checar("Código de acesso ao portal | configurado" in texto,
               "o ticket diz só que existe um código configurado")


def versao_do_pacote(zip_path):
    """A versao que o empacotar.py carimbou dentro do pacote - e ela que o
    portal de mentira anuncia, para o teste nao inventar numero."""
    import zipfile
    with zipfile.ZipFile(zip_path) as z:
        texto = z.read("_scripts/versao.txt").decode("utf-8")
    for linha in texto.splitlines():
        chave, _, valor = linha.partition(":")
        if chave.strip() == "versao":
            return valor.strip()
    raise SystemExit("o pacote de teste saiu sem carimbo de versão")


def retrato(pasta):
    out = {}
    for p in sorted(pasta.rglob("*")):
        if p.is_file():
            out[str(p.relative_to(pasta))] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out


def main():
    ap = argparse.ArgumentParser(description="Prova o cliente do portal")
    ap.add_argument("--manter", action="store_true",
                    help="não apaga a área de teste no fim")
    args = ap.parse_args()

    sys.path.insert(0, str(AQUI))
    base = Path(tempfile.mkdtemp(prefix="aft-teste-portal-"))
    # PASTA_AFT aponta para a pasta de mentira: e o que garante que o codigo de
    # acesso, o registro da consulta e o ticket nao encostem na pasta real.
    ambiente = dict(os.environ, PASTA_AFT=str(base / "AFT-de-mentira"))
    print(f"Área de teste: {base}\n")
    try:
        rodar(base, ambiente)
    finally:
        if args.manter:
            print(f"\nÁrea de teste mantida em {base}")
        else:
            shutil.rmtree(base, ignore_errors=True)

    print()
    if falhas:
        print(f"{len(falhas)} verificação(ões) FALHARAM:")
        for f in falhas:
            print(f"  - {f}")
        sys.exit(1)
    print("Todas as verificações passaram.")


if __name__ == "__main__":
    main()
