from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel, HttpUrl
from uuid import uuid4
from datetime import datetime, timezone
from pathlib import Path
import hashlib, hmac, json, os, time, base64

DATA = Path("/data"); DATA.mkdir(exist_ok=True)
app = FastAPI(title="CiscoTech Payment Auditor", version="0.2.0")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "elnerro2024@gmail.com").lower()
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
TOKEN_SECRET = os.getenv("TOKEN_SECRET")
if not ADMIN_PASSWORD or not TOKEN_SECRET:
    raise RuntimeError("ADMIN_PASSWORD y TOKEN_SECRET deben configurarse como secretos del entorno")

class LoginRequest(BaseModel):
    email: str
    password: str
class AuditRequest(BaseModel):
    url: HttpUrl
    project: str = "Auditoría"
    authorization_id: str = ""
    scope: list[str] = ["checkout", "payment", "webhooks"]

def make_token(email):
    payload=f"{email}|superuser|{int(time.time())+86400}"
    sig=hmac.new(TOKEN_SECRET.encode(),payload.encode(),hashlib.sha256).hexdigest()
    return base64.urlsafe_b64encode(f"{payload}|{sig}".encode()).decode()

def require_auth(authorization):
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(401,"Autenticación requerida")
    try:
        raw=base64.urlsafe_b64decode(authorization[7:].encode()).decode()
        email,role,exp,sig=raw.rsplit("|",3)
        expected=hmac.new(TOKEN_SECRET.encode(),f"{email}|{role}|{exp}".encode(),hashlib.sha256).hexdigest()
        if role!="superuser" or email!=ADMIN_EMAIL or int(exp)<int(time.time()) or not hmac.compare_digest(sig,expected):
            raise ValueError()
        return {"email":email,"role":role}
    except Exception:
        raise HTTPException(401,"Token inválido o expirado")

def save(aid,data):
    (DATA/f"{aid}.json").write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding="utf-8")

@app.get("/health")
def health(): return {"status":"ok","service":"ciscotech-payment-auditor","version":"0.2.0"}

@app.post("/api/auth/login")
def login(req: LoginRequest):
    if req.email.lower()!=ADMIN_EMAIL or not hmac.compare_digest(req.password,ADMIN_PASSWORD):
        raise HTTPException(401,"Correo o contraseña incorrectos")
    return {"access_token":make_token(ADMIN_EMAIL),"token_type":"bearer","role":"superuser"}

@app.get("/api/auth/me")
def me(authorization: str|None=Header(default=None)): return require_auth(authorization)

@app.post("/api/audits")
def create_audit(req: AuditRequest, authorization: str|None=Header(default=None)):
    require_auth(authorization); aid=str(uuid4())
    record={"id":aid,"created_at":datetime.now(timezone.utc).isoformat(),"status":"queued","request":req.model_dump(mode="json")}
    save(aid,record); return record

@app.get("/api/audits/{aid}")
def get_audit(aid:str,authorization:str|None=Header(default=None)):
    require_auth(authorization); p=DATA/f"{aid}.json"
    if not p.exists(): raise HTTPException(404,"Auditoría no encontrada")
    return json.loads(p.read_text(encoding="utf-8"))

@app.get("/api/audits")
def list_audits(authorization:str|None=Header(default=None)):
    require_auth(authorization); out=[]
    for p in sorted(DATA.glob("*.json"),key=lambda x:x.stat().st_mtime,reverse=True):
        try: out.append(json.loads(p.read_text(encoding="utf-8")))
        except Exception: pass
    return out[:100]
