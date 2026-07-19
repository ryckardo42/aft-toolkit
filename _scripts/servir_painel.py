#!/usr/bin/env python3
"""
servir_painel.py — modo INTERATIVO do painel AFT (servidor local).

Sobe um mini-servidor em http://127.0.0.1:8347 que serve o painel sempre
recém-gerado e aceita as AÇÕES MECÂNICAS dos cards (os controles só aparecem
no navegador quando o painel é aberto por este endereço, não pelo file://):

  - marcar/desmarcar uma notificação DET como respondida ([ ] ↔ [x]);
  - resolver uma pendência ([ ] → [x], com carimbo de data);
  - registrar uma atividade (nova linha na tabela Registro de atividades);
  - mudar o status da OS (front-matter `status:`);
  - alternar embargo/interdição entre vigente/suspenso (front-matter
    `embargo_interdicao:`, preservando a descrição existente).

Cada escrita: backup do memory.md antes (via backup_arquivo.py, em .backups/),
edição cirúrgica da linha, e o painel é regenerado no próximo carregamento.
Ações que exigem julgamento (analisar resposta, gerar AI) NÃO passam por aqui —
o painel oferece botões que copiam o comando pronto para colar no Claude Code.

Só escuta em 127.0.0.1 (inacessível pela rede). Consumo: ~20 MB de RAM,
CPU zero enquanto ocioso. Sem dependências além da biblioteca padrão.

Uso:
    python servir_painel.py [PASTA_OS_ATIVAS] [--porta 8347] [--abrir]

  PASTA_OS_ATIVAS (opcional): padrão ~/Documents/AFT/OS ATIVAS
  --porta N       (opcional): porta local (padrão 8347)
  --abrir         (opcional): abre o navegador no painel ao iniciar

Se a porta já estiver em uso (servidor já rodando), apenas informa o endereço
e sai — pode chamar quantas vezes quiser.
"""
from __future__ import annotations

import datetime
import html
import json
import re
import socket
import subprocess
import sys
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

AQUI = Path(__file__).resolve().parent
GERAR = AQUI / "gerar_painel.py"
BACKUP = AQUI / "backup_arquivo.py"
PORTA_PADRAO = 8347
MAX_BODY = 64_000

# Sync do DET via extensão Chrome "SisOS — Sync DET" (ver det_sync.py).
# CORS restrito ao site do DET: é de lá que a extensão dispara o fetch.
sys.path.insert(0, str(AQUI))
import det_sync  # noqa: E402

ORIGEM_DET = "https://auditor-det.sit.trabalho.gov.br"
CORS_DET = {
    "Access-Control-Allow-Origin": ORIGEM_DET,
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Allow-Private-Network": "true",
}

RE_FM = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
RE_CHECKBOX = re.compile(r"^(\s*-\s*\[)([ xX]?)(\]\s*)(.*)$")
STATUS_VALIDOS = {"em_andamento", "aguardando_resposta", "encerrada"}


def args_posicionais() -> list[str]:
    out, pular = [], False
    for i, a in enumerate(sys.argv[1:], 1):
        if pular:
            pular = False
            continue
        if a == "--porta":
            pular = True
        elif not a.startswith("--"):
            out.append(a)
    return out


def porta_escolhida() -> int:
    argv = sys.argv[1:]
    if "--porta" in argv:
        try:
            return int(argv[argv.index("--porta") + 1])
        except (IndexError, ValueError):
            pass
    return PORTA_PADRAO


def base_os() -> Path:
    pos = args_posicionais()
    if pos and pos[0].strip():
        return Path(pos[0])
    return Path.home() / "Documents" / "AFT" / "OS ATIVAS"


# ── Edições cirúrgicas no memory.md ─────────────────────────────────────────

def limites_secao(linhas: list[str], titulos: tuple[str, ...]) -> tuple[int, int]:
    """(inicio, fim) das linhas do corpo da seção '## titulo' (fim exclusivo),
    ou (-1, -1) se não existir."""
    ini = -1
    for i, l in enumerate(linhas):
        if l.strip().startswith("## ") and l.strip()[3:].strip() in titulos:
            ini = i + 1
            break
    if ini < 0:
        return -1, -1
    fim = len(linhas)
    for i in range(ini, len(linhas)):
        if linhas[i].strip().startswith("## "):
            fim = i
            break
    return ini, fim


def sem_comentario(s: str) -> str:
    return re.sub(r"<!--.*?-->", "", s).strip()


def acao_det(texto: str, codigo: str) -> tuple[str, str]:
    """Alterna [ ]/[x] na linha da notificação DET com o código dado."""
    linhas = texto.splitlines(keepends=True)
    ini, fim = limites_secao(linhas, ("Notificações DET", "Notificacoes DET"))
    if ini < 0:
        raise ValueError("seção 'Notificações DET' não encontrada")
    for i in range(ini, fim):
        m = RE_CHECKBOX.match(linhas[i].rstrip("\n"))
        if m and codigo in m.group(4):
            novo = " " if m.group(2).strip().lower() == "x" else "x"
            fim_l = "\n" if linhas[i].endswith("\n") else ""
            linhas[i] = m.group(1) + novo + m.group(3) + m.group(4) + fim_l
            estado = "respondida" if novo == "x" else "reaberta"
            return "".join(linhas), f"DET {codigo} marcada como {estado}"
    raise ValueError(f"notificação {codigo} não encontrada no memory.md")


def acao_pendencia(texto: str, alvo: str) -> tuple[str, str]:
    """Marca [x] a pendência em aberto cujo texto visível bate com `alvo`."""
    linhas = texto.splitlines(keepends=True)
    ini, fim = limites_secao(linhas, ("Pendências", "Pendencias"))
    if ini < 0:
        raise ValueError("seção 'Pendências' não encontrada")
    hoje = datetime.date.today().strftime("%d/%m/%Y")
    for i in range(ini, fim):
        m = RE_CHECKBOX.match(linhas[i].rstrip("\n"))
        if m and m.group(2).strip().lower() != "x" \
                and sem_comentario(m.group(4)) == alvo.strip():
            fim_l = "\n" if linhas[i].endswith("\n") else ""
            linhas[i] = (m.group(1) + "x" + m.group(3) + m.group(4)
                         + f" <!-- resolvida em {hoje} (painel) -->" + fim_l)
            return "".join(linhas), "pendência resolvida"
    raise ValueError("pendência não encontrada (ou já resolvida)")


def acao_atividade(texto: str, descricao: str) -> tuple[str, str]:
    """Acrescenta uma linha na tabela Registro de atividades (data de hoje)."""
    descricao = " ".join(descricao.split())
    if not descricao:
        raise ValueError("descrição vazia")
    if "|" in descricao:
        descricao = descricao.replace("|", "/")
    linhas = texto.splitlines(keepends=True)
    ini, fim = limites_secao(linhas, ("Registro de atividades",))
    if ini < 0:
        raise ValueError("seção 'Registro de atividades' não encontrada")
    ultima_tab = -1
    for i in range(ini, fim):
        if linhas[i].strip().startswith("|"):
            ultima_tab = i
    if ultima_tab < 0:
        raise ValueError("tabela do Registro de atividades não encontrada")
    hoje = datetime.date.today().strftime("%d/%m/%Y")
    nova = f"| {hoje} | {descricao} | painel |\n"
    linhas.insert(ultima_tab + 1, nova)
    return "".join(linhas), "atividade registrada"


def editar_fm(texto: str, chave: str, valor: str) -> str:
    """Troca (ou insere) `chave: valor` no front-matter."""
    m = RE_FM.match(texto)
    if not m:
        raise ValueError("memory.md sem front-matter")
    fm = m.group(1)
    if re.search(rf"^{chave}\s*:", fm, re.MULTILINE):
        fm_novo = re.sub(rf"^{chave}\s*:.*$", f"{chave}: {valor}", fm,
                         count=1, flags=re.MULTILINE)
    else:
        fm_novo = fm + f"\n{chave}: {valor}"
    return texto[:m.start(1)] + fm_novo + texto[m.end(1):]


def acao_status(texto: str, valor: str) -> tuple[str, str]:
    if valor not in STATUS_VALIDOS:
        raise ValueError(f"status inválido: {valor}")
    return editar_fm(texto, "status", valor), f"status → {valor}"


def acao_embargo(texto: str, estado: str) -> tuple[str, str]:
    """Alterna vigente/suspenso preservando a descrição já registrada."""
    if estado not in ("vigente", "suspenso"):
        raise ValueError(f"estado inválido: {estado}")
    m = RE_FM.match(texto)
    atual = ""
    if m:
        vm = re.search(r"^embargo_interdicao\s*:\s*(.*)$", m.group(1), re.MULTILINE)
        if vm:
            atual = vm.group(1).strip().strip('"').strip("'")
            if atual in ("null", "~"):
                atual = ""
    desc = re.sub(r"\s*[—–-]\s*(vigente|suspenso)\s*$", "", atual,
                  flags=re.IGNORECASE).strip()
    if desc.lower() in ("vigente", "suspenso"):
        desc = ""
    novo = f"{desc} — {estado}" if desc else estado
    return (editar_fm(texto, "embargo_interdicao", novo),
            f"embargo/interdição → {novo}")


ACOES = {
    "det": lambda t, p: acao_det(t, p.get("codigo", "")),
    "pendencia": lambda t, p: acao_pendencia(t, p.get("texto", "")),
    "atividade": lambda t, p: acao_atividade(t, p.get("texto", "")),
    "status": lambda t, p: acao_status(t, p.get("valor", "")),
    "embargo": lambda t, p: acao_embargo(t, p.get("estado", "")),
}


# ── Visualização de relatórios .md (rota /doc/) ──────────────────────────────
# Os relatórios das skills (analise-preliminar-*.md, autos-lavrados.md etc.)
# são a fonte de verdade em markdown; esta rota os converte em HTML legível
# on-the-fly, na mesma paleta do painel. Nada é gravado em disco.

def _md_inline(s: str) -> str:
    s = html.escape(s)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"(?<!\*)\*([^*\s][^*]*)\*(?!\*)", r"<i>\1</i>", s)
    return s


def md_para_html(md: str) -> str:
    """Conversor mínimo (stdlib) do subconjunto de markdown usado nos
    relatórios do ecossistema: títulos, negrito/itálico/código, listas,
    tabelas e réguas. O que não reconhece vira parágrafo."""
    m = RE_FM.match(md)
    if m:  # front-matter não interessa ao leitor
        md = md[m.end():]
    out: list[str] = []
    lista: str | None = None   # "ul" | "ol" abertas
    tabela: list[str] = []

    def fecha_lista():
        nonlocal lista
        if lista:
            out.append(f"</{lista}>")
            lista = None

    def fecha_tabela():
        nonlocal tabela
        if not tabela:
            return
        linhas = [l for l in tabela if not re.match(r"^\s*\|?[\s:|-]+\|?\s*$", l)]
        for j, l in enumerate(linhas):
            cels = [c.strip() for c in l.strip().strip("|").split("|")]
            tag = "th" if j == 0 else "td"
            out.append("<tr>" + "".join(f"<{tag}>{_md_inline(c)}</{tag}>"
                                        for c in cels) + "</tr>")
        if linhas:
            out.insert(len(out) - len(linhas), "<table>")
            out.append("</table>")
        tabela = []

    for linha in md.splitlines():
        s = linha.strip()
        if s.startswith("|"):
            fecha_lista()
            tabela.append(s)
            continue
        fecha_tabela()
        m_h = re.match(r"^(#{1,4})\s+(.*)$", s)
        m_ul = re.match(r"^[-*]\s+(.*)$", s)
        m_ol = re.match(r"^\d+[.)]\s+(.*)$", s)
        if m_h:
            fecha_lista()
            n = len(m_h.group(1))
            out.append(f"<h{n}>{_md_inline(m_h.group(2))}</h{n}>")
        elif m_ul or m_ol:
            tipo = "ul" if m_ul else "ol"
            if lista != tipo:
                fecha_lista()
                out.append(f"<{tipo}>")
                lista = tipo
            out.append(f"<li>{_md_inline((m_ul or m_ol).group(1))}</li>")
        elif s in ("---", "***", "___"):
            fecha_lista()
            out.append("<hr>")
        elif s:
            fecha_lista()
            out.append(f"<p>{_md_inline(s)}</p>")
        else:
            fecha_lista()
    fecha_lista()
    fecha_tabela()
    return "\n".join(out)


DOC_CSS = """
:root{--cream:#F0EEE6;--paper:#FAF9F5;--coral:#CC785C;--coral-deep:#B0593E;
--t1:#141413;--t2:#5A574E;--t3:#8F8B7D;--bd:#DDD9CC;--bds:#E8E4D6;
--teal:#4F8A7C;--serif:'Source Serif 4',Georgia,'Times New Roman',serif;}
*{box-sizing:border-box}
body{margin:0;background:var(--cream);color:var(--t1);font:15.5px/1.6 var(--serif)}
main{width:min(96vw,max(80vw,860px));margin:0 auto;
padding:36px clamp(16px,4vw,48px) 80px;
background:var(--paper);min-height:100vh;border-left:1px solid var(--bds);
border-right:1px solid var(--bds)}
h1{font-size:25px;font-weight:600;margin:0 0 14px;line-height:1.3}
h1 em{color:var(--coral);font-style:italic}
h2{font-size:14px;letter-spacing:.08em;text-transform:uppercase;color:var(--t3);
border-bottom:1px solid var(--bds);padding-bottom:5px;margin:32px 0 12px}
h3{font-size:16.5px;font-weight:600;margin:24px 0 8px;color:var(--coral-deep)}
h4{font-size:14.5px;margin:18px 0 6px}
p{margin:8px 0}
ul,ol{margin:8px 0;padding-left:24px}
li{margin-bottom:6px}
code{background:var(--cream);border:1px solid var(--bds);border-radius:4px;
padding:1px 5px;font-size:13px}
hr{border:none;border-top:1px solid var(--bds);margin:24px 0}
table{border-collapse:collapse;margin:12px 0;font-size:14px;width:100%}
th,td{border:1px solid var(--bds);padding:6px 10px;text-align:left;vertical-align:top}
th{background:var(--cream);font-weight:600}
.topo{font-size:12.5px;color:var(--t3);margin-bottom:22px}
.topo a{color:var(--coral-deep)}
@media print{main{border:none}.topo{display:none}}
@media (prefers-color-scheme: dark){
:root{--cream:#191917;--paper:#211F1C;--t1:#EDEAE0;--t2:#B5B0A1;--t3:#8F8B7D;
--bd:#3A372F;--bds:#2E2B25}}
"""


def pagina_doc(titulo: str, corpo: str, pasta: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(titulo)}</title>
<style>{DOC_CSS}</style>
</head>
<body>
<main>
<div class="topo"><a href="/">← painel</a> · {html.escape(pasta)} · {html.escape(titulo)}</div>
{corpo}
</main>
</body>
</html>
"""


# ── Servidor ─────────────────────────────────────────────────────────────────

class Handler(BaseHTTPRequestHandler):
    base: Path  # definido em servir()

    def log_message(self, fmt, *args):  # silencioso
        pass

    def _responde(self, code: int, corpo: bytes, ctype: str,
                  extra: dict | None = None):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(corpo)))
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(corpo)

    def _json(self, code: int, obj: dict, extra: dict | None = None):
        self._responde(code, json.dumps(obj, ensure_ascii=False).encode("utf-8"),
                       "application/json; charset=utf-8", extra)

    def _host_ok(self) -> bool:
        host = (self.headers.get("Host") or "").split(":")[0]
        return host in ("127.0.0.1", "localhost")

    def do_GET(self):
        if not self._host_ok():
            return self._json(403, {"ok": False, "erro": "host não permitido"})
        if self.path in ("/", "/index.html", "/painel.html"):
            try:
                subprocess.run([sys.executable, str(GERAR), str(self.base)],
                               capture_output=True, timeout=120)
            except Exception:
                pass  # serve o painel anterior, se existir
            painel = self.base.parent / "painel.html"
            if not painel.exists():
                return self._responde(404, "painel.html não encontrado — rode a skill /painel"
                                      .encode("utf-8"), "text/plain; charset=utf-8")
            self._responde(200, painel.read_bytes(), "text/html; charset=utf-8")
        elif self.path == "/api/ping":
            self._json(200, {"ok": True, "painel_aft": True})
        elif self.path.startswith("/doc/"):
            self._serve_doc()
        else:
            self._json(404, {"ok": False, "erro": "rota desconhecida"})

    def _serve_doc(self):
        """GET /doc/<pasta-da-OS>/<arquivo>.md — renderiza o relatório em HTML.
        Mesma validação de caminho do /api/acao: só .md dentro de OS ATIVAS."""
        try:
            partes = self.path[len("/doc/"):].split("/")
            if len(partes) != 2:
                raise ValueError("use /doc/<pasta>/<arquivo>.md")
            pasta = urllib.parse.unquote(partes[0]).strip()
            arquivo = urllib.parse.unquote(partes[1]).strip()
            if (not pasta or "/" in pasta or "\\" in pasta or pasta.startswith(".")
                    or not arquivo or "/" in arquivo or "\\" in arquivo
                    or arquivo.startswith(".") or not arquivo.endswith(".md")):
                raise ValueError("caminho inválido")
            alvo = (self.base / pasta / arquivo).resolve()
            if self.base.resolve() not in alvo.parents or not alvo.exists():
                raise ValueError(f"{arquivo} não encontrado em {pasta}")
            corpo = md_para_html(alvo.read_text(encoding="utf-8", errors="replace"))
            pag = pagina_doc(arquivo, corpo, pasta)
            self._responde(200, pag.encode("utf-8"), "text/html; charset=utf-8")
        except ValueError as e:
            self._responde(404, html.escape(str(e)).encode("utf-8"),
                           "text/plain; charset=utf-8")
        except Exception as e:
            self._responde(500, f"{type(e).__name__}: {e}".encode("utf-8"),
                           "text/plain; charset=utf-8")

    def do_OPTIONS(self):
        # Preflight do navegador para o POST /api/det-sync vindo do site do DET.
        if self.path == "/api/det-sync":
            self._responde(204, b"", "text/plain", CORS_DET)
        else:
            self._responde(204, b"", "text/plain")

    def do_POST(self):
        if not self._host_ok():
            return self._json(403, {"ok": False, "erro": "host não permitido"})
        if self.path == "/api/det-sync":
            return self._det_sync()
        if self.path != "/api/acao":
            return self._json(404, {"ok": False, "erro": "rota desconhecida"})
        try:
            n = min(int(self.headers.get("Content-Length") or 0), MAX_BODY)
            p = json.loads(self.rfile.read(n).decode("utf-8"))
            acao = p.get("acao")
            if acao not in ACOES:
                raise ValueError(f"ação desconhecida: {acao}")
            pasta = (p.get("pasta") or "").strip()
            if not pasta or "/" in pasta or "\\" in pasta or pasta.startswith("."):
                raise ValueError("pasta inválida")
            mem = (self.base / pasta / "memory.md").resolve()
            if self.base.resolve() not in mem.parents or not mem.exists():
                raise ValueError(f"memory.md não encontrado em {pasta}")
            texto = mem.read_text(encoding="utf-8")
            novo, msg = ACOES[acao](texto, p)
            if BACKUP.exists():
                subprocess.run([sys.executable, str(BACKUP), str(mem)],
                               capture_output=True, timeout=30)
            mem.write_text(novo, encoding="utf-8")
            self._json(200, {"ok": True, "msg": msg})
        except ValueError as e:
            self._json(400, {"ok": False, "erro": str(e)})
        except Exception as e:
            self._json(500, {"ok": False, "erro": f"{type(e).__name__}: {e}"})

    def _det_sync(self):
        """POST /api/det-sync — corpo {det_access_token}; chamado pela
        extensão Chrome. O token vive só nesta requisição (nunca em disco)."""
        try:
            n = min(int(self.headers.get("Content-Length") or 0), MAX_BODY)
            p = json.loads(self.rfile.read(n).decode("utf-8"))
            token = p.get("det_access_token")
            if not token or not isinstance(token, str) or token.count(".") != 2:
                return self._json(400, {"ok": False,
                                        "erro": "det_access_token ausente ou inválido"},
                                  CORS_DET)
            resultado = det_sync.sincronizar_todas(self.base, token)
            self._json(200, resultado, CORS_DET)
        except Exception as e:
            self._json(500, {"ok": False, "erro": f"{type(e).__name__}: {e}"},
                       CORS_DET)


def porta_ocupada(porta: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", porta)) == 0


def main() -> int:
    base = base_os()
    porta = porta_escolhida()
    url = f"http://127.0.0.1:{porta}"
    if not base.exists():
        print(f"ERRO: pasta de OS não existe: {base}", file=sys.stderr)
        return 1
    if porta_ocupada(porta):
        print(f"Painel interativo já está no ar: {url}")
        if "--abrir" in sys.argv[1:]:
            webbrowser.open(url)
        return 0
    Handler.base = base
    srv = ThreadingHTTPServer(("127.0.0.1", porta), Handler)
    print(f"Painel interativo no ar: {url}  (OS: {base})")
    print("Ctrl+C para encerrar. Consumo ocioso ~20 MB de RAM, CPU 0%.")
    if "--abrir" in sys.argv[1:]:
        webbrowser.open(url)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nencerrado.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
