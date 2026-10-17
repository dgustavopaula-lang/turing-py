import os
import json
import secrets
from pathlib import Path

import psycopg
from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel

BASE = Path(__file__).resolve().parent.parent
ARQ = BASE / "data" / "revisoes.json"
router = APIRouter()
DECISOES = ["ataque", "falso_positivo", "conhecido"]


def auth(x_admin_token: str = Header(default="")):
    t = os.getenv("ADMIN_TOKEN", "")
    if not t or not secrets.compare_digest(x_admin_token.encode(), t.encode()):
        raise HTTPException(status_code=401, detail="nao autorizado")


def ler():
    if ARQ.exists():
        return json.loads(ARQ.read_text(encoding="utf-8"))
    return {}


class Decisao(BaseModel):
    id: int
    decisao: str


@router.get("/admin/api/revisao", dependencies=[Depends(auth)])
def listar():
    url = os.getenv("DB_LEITOR_URL", "")
    if not url:
        return {"erro": "DB_LEITOR_URL vazia"}
    dec = ler()
    try:
        with psycopg.connect(url, connect_timeout=5) as c:
            cur = c.cursor()
            cur.execute(
                "SELECT id, criado_em, evento, estado, contexto->>%s FROM turing_security_events "
                "WHERE estado IN (%s, %s) ORDER BY criado_em DESC LIMIT 40",
                ("motivo", "WARN", "ALERT"),
            )
            itens = [
                {"id": r[0], "quando": r[1].isoformat(), "evento": r[2], "estado": r[3],
                 "motivo": r[4], "decisao": dec.get(str(r[0]))}
                for r in cur.fetchall()
            ]
        return {"itens": itens}
    except Exception as e:
        return {"erro": type(e).__name__}


@router.post("/admin/api/revisao", dependencies=[Depends(auth)])
def decidir(d: Decisao):
    if d.decisao not in DECISOES:
        raise HTTPException(status_code=400, detail="decisao invalida")
    dec = ler()
    dec[str(d.id)] = d.decisao
    ARQ.parent.mkdir(exist_ok=True)
    ARQ.write_text(json.dumps(dec, indent=2), encoding="utf-8")
    return {"ok": True}
