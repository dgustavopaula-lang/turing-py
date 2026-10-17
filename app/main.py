import os
import json
import time
import secrets
from pathlib import Path

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.responses import FileResponse
from pydantic import BaseModel

load_dotenv()
BASE = Path(__file__).resolve().parent.parent
KB_FILE = BASE / "data" / "conhecimento.json"
LOG_FILE = BASE / "logs" / "vigia.log"
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "")
HEALTH_URL = os.getenv("NEXOTERRA_HEALTH_URL", "")

app = FastAPI(title="Turing PY", version="0.2.0", docs_url=None, redoc_url=None)


def auth(x_admin_token: str = Header(default="")):
    if not ADMIN_TOKEN or not secrets.compare_digest(
        x_admin_token.encode(), ADMIN_TOKEN.encode()
    ):
        raise HTTPException(status_code=401, detail="não autorizado")


def ler_kb():
    if KB_FILE.exists():
        return json.loads(KB_FILE.read_text(encoding="utf-8"))
    return []


def gravar_kb(itens):
    KB_FILE.parent.mkdir(exist_ok=True)
    KB_FILE.write_text(json.dumps(itens, ensure_ascii=False, indent=2), encoding="utf-8")


class Item(BaseModel):
    pergunta: str
    resposta: str


class Pergunta(BaseModel):
    texto: str


@app.get("/health")
def health():
    return {"status": "ok", "servico": "turing-py"}


@app.get("/admin")
def admin():
    return FileResponse(BASE / "app" / "static" / "admin.html")


@app.get("/admin/api/status", dependencies=[Depends(auth)])
def status():
    if not HEALTH_URL:
        return {"online": False, "erro": "NEXOTERRA_HEALTH_URL vazia"}
    try:
        r = httpx.get(HEALTH_URL, timeout=10, follow_redirects=True)
        return {"online": r.status_code == 200, "codigo": r.status_code,
                "ms": int(r.elapsed.total_seconds() * 1000)}
    except Exception as e:
        return {"online": False, "erro": type(e).__name__}


@app.get("/admin/api/logs", dependencies=[Depends(auth)])
def logs():
    if not LOG_FILE.exists():
        return {"linhas": []}
    return {"linhas": LOG_FILE.read_text(encoding="utf-8").splitlines()[-60:]}


@app.get("/admin/api/config", dependencies=[Depends(auth)])
def config():
    nomes = ["NEXOTERRA_API_URL", "NEXOTERRA_API_TOKEN", "NEXOTERRA_HEALTH_URL", "ADMIN_TOKEN"]
    return {n: bool(os.getenv(n)) for n in nomes}


@app.get("/admin/api/kb", dependencies=[Depends(auth)])
def listar():
    return ler_kb()


@app.post("/admin/api/kb", dependencies=[Depends(auth)])
def adicionar(item: Item):
    if not item.pergunta.strip() or not item.resposta.strip():
        raise HTTPException(status_code=400, detail="preencha pergunta e resposta")
    itens = ler_kb()
    itens.append({"id": int(time.time() * 1000), "pergunta": item.pergunta.strip(),
                  "resposta": item.resposta.strip()})
    gravar_kb(itens)
    return {"ok": True, "total": len(itens)}


@app.delete("/admin/api/kb/{item_id}", dependencies=[Depends(auth)])
def remover(item_id: int):
    gravar_kb([i for i in ler_kb() if i["id"] != item_id])
    return {"ok": True}


@app.post("/admin/api/perguntar", dependencies=[Depends(auth)])
def perguntar(p: Pergunta):
    palavras = set(p.texto.lower().split())
    melhor, pontos = None, 0
    for i in ler_kb():
        n = len(palavras & set(i["pergunta"].lower().split()))
        if n > pontos:
            melhor, pontos = i, n
    if melhor:
        return {"resposta": melhor["resposta"], "confianca": pontos}
    return {"resposta": "Ainda não sei responder isso. Ensine na aba Treino.", "confianca": 0}

@app.get("/admin/api/seguranca", dependencies=[Depends(auth)])
def seguranca():
    import psycopg
    url = os.getenv("DB_LEITOR_URL", "")
    if not url:
        return {"erro": "DB_LEITOR_URL vazia"}
    try:
        with psycopg.connect(url, connect_timeout=5) as c:
            cur = c.cursor()
            cur.execute("SELECT estado, COUNT(*) FROM turing_security_events GROUP BY 1")
            totais = {e: n for e, n in cur.fetchall()}
            cur.execute(
                "SELECT criado_em, evento, estado, contexto->>%s FROM turing_security_events "
                "WHERE estado IN (%s, %s) ORDER BY criado_em DESC LIMIT 30",
                ("motivo", "WARN", "ALERT"),
            )
            recentes = [
                {"quando": r[0].isoformat(), "evento": r[1], "estado": r[2], "motivo": r[3]}
                for r in cur.fetchall()
            ]
        return {"totais": totais, "recentes": recentes}
    except Exception as e:
        return {"erro": type(e).__name__}

from fastapi.staticfiles import StaticFiles
app.mount("/static", StaticFiles(directory=str(BASE / "app" / "static")), name="static")

from app.revisao import router as _rv
app.include_router(_rv)
