from __future__ import annotations

import hashlib
import hmac
import os
import time
from typing import Optional

from fastapi import FastAPI, Header, HTTPException, Request

from .orchestrator.idempotency import (
    IdempotencyConflictError,
    create_idempotency_store,
)
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

HMAC_SECRET_ENV = "SHERATAN_HMAC_SECRET"
SIGNATURE_HEADER = "Signature"
TIMESTAMP_HEADER = "Timestamp"
IDEMPOTENCY_HEADER = "X-Sheratan-Idempotency"
TIMESTAMP_TOLERANCE_SECONDS = 300

_idempotency_store = create_idempotency_store()


def _load_hmac_secret() -> str:
    secret = os.getenv(HMAC_SECRET_ENV, "").strip()
    if not secret:
        raise HTTPException(status_code=500, detail="HMAC secret not configured")
    return secret


def _verify_timestamp(timestamp_header: str) -> int:
    try:
        ts = int(timestamp_header)
    except (TypeError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid timestamp header")

    now = int(time.time())
    if abs(now - ts) > TIMESTAMP_TOLERANCE_SECONDS:
        raise HTTPException(status_code=401, detail="Timestamp outside allowed window")
    return ts


def _verify_signature(secret: str, timestamp: str, idempotency: str, body: bytes, signature: Optional[str]) -> None:
    if not signature:
        raise HTTPException(status_code=401, detail="Missing signature header")

    message = b"|".join([timestamp.encode("utf-8"), idempotency.encode("utf-8"), body])
    digest = hmac.new(secret.encode("utf-8"), message, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(digest, signature):
        raise HTTPException(status_code=401, detail="Invalid signature")


async def _verify_hmac(
    request: Request,
    timestamp: Optional[str],
    idempotency: Optional[str],
    signature: Optional[str],
) -> None:
    secret = _load_hmac_secret()
    if timestamp is None:
        raise HTTPException(status_code=401, detail="Missing timestamp header")

    ts = _verify_timestamp(timestamp)
    body = await request.body()
    if idempotency is None:
        raise HTTPException(status_code=401, detail="Missing idempotency header")

    _verify_signature(secret, timestamp, idempotency, body, signature)

    fingerprint = hashlib.sha256(body).hexdigest()
    try:
        _idempotency_store.reserve(idempotency, fingerprint, ts)
    except IdempotencyConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@app.post("/relay/status", response_model=AckResponse)
async def relay_status(
    request: Request,
    evt: RelayStatus,
    timestamp: Optional[str] = Header(None, alias=TIMESTAMP_HEADER),
    idempotency: Optional[str] = Header(None, alias=IDEMPOTENCY_HEADER),
    signature: Optional[str] = Header(None, alias=SIGNATURE_HEADER),
) -> AckResponse:
    await _verify_hmac(request, timestamp, idempotency, signature)
    return AckResponse()


@app.post("/relay/final", response_model=AckResponse)
async def relay_final(
    request: Request,
    evt: RelayFinal,
    timestamp: Optional[str] = Header(None, alias=TIMESTAMP_HEADER),
    idempotency: Optional[str] = Header(None, alias=IDEMPOTENCY_HEADER),
    signature: Optional[str] = Header(None, alias=SIGNATURE_HEADER),
) -> AckResponse:
    await _verify_hmac(request, timestamp, idempotency, signature)
    return AckResponse()


def _reset_hmac_state() -> None:
    """Testing helper to reset HMAC and idempotency state."""

    global _idempotency_store
    _idempotency_store = create_idempotency_store()
