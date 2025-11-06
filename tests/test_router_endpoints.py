import asyncio
import sys
from pathlib import Path
from typing import Any, Dict, List

import pytest
from fastapi import HTTPException


sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from sheratan_core import api


class StubRouter:
    def __init__(self) -> None:
        self._health_payload = {"status": "green"}
        self._models = ["alpha", "beta"]
        self._metadata = {"vendor": "stub"}

    def name(self) -> str:
        return "stub-router"

    async def health(self) -> Dict[str, Any]:
        return self._health_payload

    def models(self) -> List[str]:
        return list(self._models)

    def metadata(self) -> Dict[str, Any]:
        return dict(self._metadata)

    async def complete(self, req: Dict[str, Any]) -> Dict[str, Any]:
        return {"model": req.get("model", "alpha"), "output": "ok", "usage": {}}

    async def stream(self, req: Dict[str, Any]):
        yield {"chunk": 0}


def test_router_health_endpoint(monkeypatch):
    stub = StubRouter()
    monkeypatch.setattr(api, "load_router", lambda: stub)

    payload = asyncio.run(api.router_health())

    assert payload.name == "stub-router"
    assert payload.status == {"status": "green"}
    assert payload.metadata == {"vendor": "stub"}


def test_router_models_endpoint(monkeypatch):
    stub = StubRouter()
    monkeypatch.setattr(api, "load_router", lambda: stub)

    payload = asyncio.run(api.router_models())

    assert payload.name == "stub-router"
    assert payload.models == ["alpha", "beta"]
    assert payload.metadata == {"vendor": "stub"}


def test_router_endpoints_without_router(monkeypatch):
    monkeypatch.setattr(api, "load_router", lambda: None)

    with pytest.raises(HTTPException) as health_exc:
        asyncio.run(api.router_health())
    assert health_exc.value.status_code == 501

    with pytest.raises(HTTPException) as models_exc:
        asyncio.run(api.router_models())
    assert models_exc.value.status_code == 501
