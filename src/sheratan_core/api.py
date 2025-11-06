from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from .registry import load_router

app = FastAPI(title="Sheratan Core", version="1.0.0")

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
        except Exception as _:
            router_health = {"router": "error"}
    return {"status": "ok", "router": router_health}

@app.get("/version")
async def version():
    return {"name": "Sheratan Core", "version": "1.0.0"}

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

# Relay callbacks (skelett)
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

@app.post("/relay/status")
async def relay_status(evt: RelayStatus):
    # TODO: Auth/HMAC prüfen & persistieren
    return {"ok": True}

@app.post("/relay/final")
async def relay_final(evt: RelayFinal):
    # TODO: Auth/HMAC prüfen & persistieren
    return {"ok": True}
