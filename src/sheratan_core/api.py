from __future__ import annotations

import hashlib
import hmac
import os
import time
from typing import Optional

from fastapi import FastAPI, Header, HTTPException, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

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

try:
    from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
except ModuleNotFoundError:  # pragma: no cover - optional dependency guard
    import math
    from typing import Dict, Iterable, Tuple

    CONTENT_TYPE_LATEST = "text/plain; version=0.0.4; charset=utf-8"

    _METRIC_REGISTRY: list["_FallbackMetricBase"] = []

    class _FallbackMetricBase:
        def __init__(self, name: str, documentation: str, labelnames: Iterable[str]):
            self.name = name
            self.documentation = documentation
            self.labelnames = tuple(labelnames)
            _METRIC_REGISTRY.append(self)

        def _key(self, labels: Dict[str, str]) -> Tuple[str, ...]:
            missing = set(self.labelnames) - set(labels)
            if missing:
                raise ValueError(f"Missing labels: {missing}")
            extras = set(labels) - set(self.labelnames)
            if extras:
                raise ValueError(f"Unexpected labels: {extras}")
            return tuple(str(labels[name]) for name in self.labelnames)

        def _pairs(self, key: Tuple[str, ...]) -> Tuple[Tuple[str, str], ...]:
            return tuple((self.labelnames[idx], key[idx]) for idx in range(len(self.labelnames)))

        @staticmethod
        def _format_labels(pairs: Iterable[Tuple[str, str]]) -> str:
            pairs = tuple(pairs)
            if not pairs:
                return ""
            return "{" + ",".join(f'{k}="{v}"' for k, v in pairs) + "}"


    class Counter(_FallbackMetricBase):
        def __init__(self, name: str, documentation: str, labelnames: Iterable[str]):
            super().__init__(name, documentation, labelnames)
            self._values: Dict[Tuple[str, ...], float] = {}

        class _Child:
            def __init__(self, parent: "Counter", key: Tuple[str, ...]):
                self._parent = parent
                self._key = key

            def inc(self, amount: float = 1.0) -> None:
                self._parent._values[self._key] = self._parent._values.get(self._key, 0.0) + amount

        def labels(self, **labels: str) -> "Counter._Child":
            key = self._key(labels)
            return Counter._Child(self, key)

        def render(self) -> list[str]:
            lines = [f"# HELP {self.name} {self.documentation}", f"# TYPE {self.name} counter"]
            for key in sorted(self._values):
                value = self._values[key]
                lines.append(f"{self.name}{self._format_labels(self._pairs(key))} {float(value)}")
            return lines


    class Histogram(_FallbackMetricBase):
        _DEFAULT_BUCKETS = (
            0.005,
            0.01,
            0.025,
            0.05,
            0.075,
            0.1,
            0.25,
            0.5,
            0.75,
            1.0,
            2.5,
            5.0,
            7.5,
            10.0,
            math.inf,
        )

        def __init__(self, name: str, documentation: str, labelnames: Iterable[str]):
            super().__init__(name, documentation, labelnames)
            self._values: Dict[Tuple[str, ...], Dict[str, object]] = {}

        class _Child:
            def __init__(self, parent: "Histogram", key: Tuple[str, ...]):
                self._parent = parent
                self._key = key

            def observe(self, value: float) -> None:
                record = self._parent._values.setdefault(
                    self._key,
                    {
                        "buckets": [0 for _ in Histogram._DEFAULT_BUCKETS],
                        "sum": 0.0,
                        "count": 0,
                    },
                )
                buckets = record["buckets"]  # type: ignore[index]
                for idx, upper in enumerate(Histogram._DEFAULT_BUCKETS):
                    if value <= upper:
                        buckets[idx] += 1
                record["sum"] = float(record["sum"]) + float(value)  # type: ignore[index]
                record["count"] = int(record["count"]) + 1  # type: ignore[index]

        def labels(self, **labels: str) -> "Histogram._Child":
            key = self._key(labels)
            return Histogram._Child(self, key)

        def render(self) -> list[str]:
            lines = [f"# HELP {self.name} {self.documentation}", f"# TYPE {self.name} histogram"]
            for key in sorted(self._values):
                record = self._values[key]
                base_pairs = self._pairs(key)
                buckets = record["buckets"]  # type: ignore[index]
                for idx, upper in enumerate(self._DEFAULT_BUCKETS):
                    label_value = "+Inf" if math.isinf(upper) else str(upper)
                    bucket_pairs = base_pairs + (("le", label_value),)
                    lines.append(
                        f"{self.name}_bucket{self._format_labels(bucket_pairs)} {float(buckets[idx])}"
                    )
                lines.append(
                    f"{self.name}_count{self._format_labels(base_pairs)} {float(record['count'])}"
                )
                lines.append(
                    f"{self.name}_sum{self._format_labels(base_pairs)} {float(record['sum'])}"
                )
            return lines


    def generate_latest() -> bytes:
        lines: list[str] = []
        for metric in _METRIC_REGISTRY:
            render = getattr(metric, "render", None)
            if callable(render):
                lines.extend(render())
        return ("\n".join(lines) + "\n").encode("utf-8")

app = FastAPI(title="Sheratan Core", version="1.0.0")

METRICS_ENABLED = os.getenv("SHERATAN_METRICS_ENABLED", "1").lower() not in {"0", "false", "no"}


def _metric_label_path(request: Request) -> str:
    route = request.scope.get("route")
    if route and getattr(route, "path", None):
        return route.path  # type: ignore[return-value]
    return request.url.path


if METRICS_ENABLED and Counter and Histogram:
    _REQUEST_LATENCY = Histogram(
        "sheratan_api_request_duration_seconds",
        "Time spent processing Sheratan API requests",
        ("method", "path", "status"),
    )
    _REQUEST_ERRORS = Counter(
        "sheratan_api_request_errors_total",
        "Total number of error responses from Sheratan API requests",
        ("method", "path", "status"),
    )

    class ApiMetricsMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request: Request, call_next):  # type: ignore[override]
            path = request.url.path
            if not path.startswith("/api/"):
                return await call_next(request)

            labels = {"method": request.method, "path": _metric_label_path(request)}
            start = time.perf_counter()
            try:
                response = await call_next(request)
            except Exception:
                duration = time.perf_counter() - start
                _REQUEST_LATENCY.labels(status="exception", **labels).observe(duration)
                _REQUEST_ERRORS.labels(status="exception", **labels).inc()
                raise

            duration = time.perf_counter() - start
            status = str(response.status_code)
            _REQUEST_LATENCY.labels(status=status, **labels).observe(duration)
            if response.status_code >= 400:
                _REQUEST_ERRORS.labels(status=status, **labels).inc()

            return response

    app.add_middleware(ApiMetricsMiddleware)


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
