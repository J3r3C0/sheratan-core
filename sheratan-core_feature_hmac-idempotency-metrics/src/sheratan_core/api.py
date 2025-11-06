from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from .registry import load_router
from .security import verify_hmac
from .idempotency import get_store
from .metrics import metrics_endpoint, TimingMiddleware, ENABLED as METRICS_ENABLED

app = FastAPI(title="Sheratan Core", version="1.1.0")
if METRICS_ENABLED:
    app.middleware("http")(TimingMiddleware(app))

class CompleteRequest(BaseModel):
    model: str = Field(default="gpt-4o-mini")
    prompt: str
    max_tokens: int = Field(default=128, ge=1, le=4096)

class CompleteResponse(BaseModel):
    model: str
    output: str
    usage: Dict[str, Any] = {}

@app.get("/health")
async def health():
    r = load_router()
    router_health = {}
    if r:
        try:
            router_health = await r.health()
        except Exception:
            router_health = {"router": "error"}
    return {"status": "ok", "router": router_health}

@app.get("/version")
async def version():
    return {"name": "Sheratan Core", "version": "1.1.0"}

@app.post("/api/v1/llm/complete", response_model=CompleteResponse)
async def llm_complete(req: CompleteRequest):
    r = load_router()
    if not r:
        raise HTTPException(status_code=501, detail="No router configured")
    try:
        result = await r.complete(req.model_dump())
        return CompleteResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Router error: {e}")

# Relay callbacks (secured with HMAC + idempotency)
class RelayStatus(BaseModel):
    job_id: str
    trace_id: Optional[str] = None
    phase: Optional[str] = None
    progress: Optional[int] = None
    message: Optional[str] = None
    ts: Optional[str] = None

class RelayFinal(BaseModel):
    job_id: str
    trace_id: Optional[str] = None
    status: str
    output: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None
    metrics: Optional[Dict[str, Any]] = None
    ts: Optional[str] = None

_store = get_store()

async def _guard(request: Request, idem_key: Optional[str]) -> None:
    # HMAC verification
    ts = request.headers.get("X-Sheratan-Timestamp", "")
    sig = request.headers.get("X-Sheratan-Signature", "")
    body = await request.body()
    ok, why = verify_hmac(ts, sig, body)
    if not ok:
        raise HTTPException(status_code=401, detail=f"hmac-{why}")
    # Idempotency
    if idem_key:
        if not _store.put_once(idem_key):
            # already processed -> accept deterministically
            raise HTTPException(status_code=200, detail="duplicate")

@app.post("/relay/status")
async def relay_status(evt: RelayStatus, request: Request):
    await _guard(request, evt.job_id)
    return {"ok": True}

@app.post("/relay/final")
async def relay_final(evt: RelayFinal, request: Request):
    await _guard(request, evt.job_id)
    return {"ok": True}

@app.get("/metrics")
async def metrics():
    return metrics_endpoint()
