from fastapi import FastAPI, HTTPException

from .registry import load_router
from .types import LLMRouter
from .schemas import (
    AckResponse,
    CompleteRequest,
    CompleteResponse,
    RouterHealthResponse,
    RouterModelsResponse,
    RelayFinal,
    RelayStatus,
)

app = FastAPI(title="Sheratan Core", version="1.0.0")


def _require_router() -> LLMRouter:
    router = load_router()
    if not router:
        raise HTTPException(status_code=501, detail="No router configured")
    return router


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


@app.get("/metrics")
async def metrics() -> Response:
    if not METRICS_ENABLED or not generate_latest:
        raise HTTPException(status_code=404, detail="Metrics disabled")

    payload = generate_latest()
    return Response(content=payload, media_type=CONTENT_TYPE_LATEST)

@app.post("/api/v1/llm/complete", response_model=CompleteResponse)
async def llm_complete(req: CompleteRequest):
    r = _require_router()
    try:
        result = await r.complete(req.model_dump())
        return CompleteResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Router error: {e}")


@app.get("/api/v1/router/health", response_model=RouterHealthResponse)
async def router_health() -> RouterHealthResponse:
    r = _require_router()
    try:
        status = await r.health()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Router error: {e}")

    try:
        metadata = r.metadata()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Router metadata error: {e}")

    return RouterHealthResponse(name=r.name(), status=status, metadata=metadata)


@app.get("/api/v1/router/models", response_model=RouterModelsResponse)
async def router_models() -> RouterModelsResponse:
    r = _require_router()
    try:
        models = r.models()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Router error: {e}")

    try:
        metadata = r.metadata()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Router metadata error: {e}")

    return RouterModelsResponse(name=r.name(), models=models, metadata=metadata)

@app.post("/relay/status", response_model=AckResponse)
async def relay_status(evt: RelayStatus) -> AckResponse:
    # TODO: Auth/HMAC prüfen & persistieren
    return AckResponse()

@app.post("/relay/final", response_model=AckResponse)
async def relay_final(evt: RelayFinal) -> AckResponse:
    # TODO: Auth/HMAC prüfen & persistieren
    return AckResponse()
