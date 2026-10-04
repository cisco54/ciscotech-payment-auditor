from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl
from uuid import uuid4
from datetime import datetime, timezone
from pathlib import Path
import json

DATA = Path("/data")
DATA.mkdir(exist_ok=True)
app = FastAPI(title="CiscoTech Payment Auditor", version="0.1.0")

class AuditRequest(BaseModel):
    url: HttpUrl
    project: str = "Auditoría"
    authorization_id: str = ""
    scope: list[str] = ["checkout", "payment", "webhooks"]

def save(aid, data):
    (DATA / f"{aid}.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

@app.get("/health")
def health():
    return {"status":"ok","service":"ciscotech-payment-auditor"}

@app.post("/api/audits")
def create_audit(req: AuditRequest):
    aid = str(uuid4())
    record = {
        "id": aid,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "queued",
        "request": req.model_dump(mode="json")
    }
    save(aid, record)
    return record

@app.get("/api/audits/{aid}")
def get_audit(aid: str):
    p = DATA / f"{aid}.json"
    if not p.exists():
        raise HTTPException(404, "Auditoría no encontrada")
    return json.loads(p.read_text(encoding="utf-8"))

@app.get("/api/audits")
def list_audits():
    out=[]
    for p in sorted(DATA.glob("*.json"), key=lambda x:x.stat().st_mtime, reverse=True):
        try:
            out.append(json.loads(p.read_text(encoding="utf-8")))
        except Exception:
            pass
    return out[:100]
