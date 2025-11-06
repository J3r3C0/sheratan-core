import os, time
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Response

REQ_LATENCY = Histogram("sheratan_req_latency_seconds", "Request latency", ["path","method","status"])
REQ_COUNT   = Counter("sheratan_req_total", "Request count", ["path","method","status"])

ENABLED = os.getenv("SHERATAN_METRICS_ENABLED", "true").lower() == "true"

def metrics_endpoint():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

class TimingMiddleware:
    def __init__(self, app):
        self.app = app
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        start = time.time()
        method = scope["method"]
        path = scope["path"]
        status_holder = {"code": "200"}
        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                status_holder["code"] = str(message["status"])
            await send(message)
        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            dur = time.time() - start
            if ENABLED:
                REQ_LATENCY.labels(path, method, status_holder["code"]).observe(dur)
                REQ_COUNT.labels(path, method, status_holder["code"]).inc()
