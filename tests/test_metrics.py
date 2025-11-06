import asyncio
import sys
from pathlib import Path

from starlette.requests import Request
from starlette.responses import Response as StarletteResponse


sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from sheratan_core import api  # noqa: E402


def _build_request(path: str, method: str = "GET") -> Request:
    scope = {
        "type": "http",
        "http_version": "1.1",
        "method": method,
        "path": path,
        "raw_path": path.encode(),
        "root_path": "",
        "scheme": "http",
        "query_string": b"",
        "headers": [],
        "client": ("127.0.0.1", 12345),
        "server": ("testserver", 80),
    }
    scope["route"] = type("Route", (), {"path": path})()
    return Request(scope)


def test_metrics_records_success():
    middleware = api.ApiMetricsMiddleware(api.app)
    request = _build_request("/api/v1/router/models")

    async def call_next(_: Request):
        return StarletteResponse(status_code=200)

    asyncio.run(middleware.dispatch(request, call_next))
    response = asyncio.run(api.metrics())
    body = response.body.decode()

    assert (
        'sheratan_api_request_duration_seconds_count{method="GET",path="/api/v1/router/models",status="200"}'
        in body
    )


def test_metrics_records_errors():
    middleware = api.ApiMetricsMiddleware(api.app)
    request = _build_request("/api/v1/router/health")

    async def call_next(_: Request):
        return StarletteResponse(status_code=502)

    asyncio.run(middleware.dispatch(request, call_next))
    response = asyncio.run(api.metrics())
    body = response.body.decode()

    assert (
        'sheratan_api_request_errors_total{method="GET",path="/api/v1/router/health",status="502"} 1.0'
        in body
    )
