import asyncio
import hmac
import hashlib
import json
import sys
import time
from pathlib import Path

import pytest
from fastapi import HTTPException
from starlette.requests import Request

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from sheratan_core.api import (
    IDEMPOTENCY_HEADER,
    SIGNATURE_HEADER,
    TIMESTAMP_HEADER,
    _reset_hmac_state,
    relay_status,
)
from sheratan_core.schemas import RelayStatus


@pytest.fixture(autouse=True)
def reset_state(monkeypatch):
    monkeypatch.setenv("SHERATAN_HMAC_SECRET", "super-secret")
    monkeypatch.delenv("SHERATAN_IDEMPOTENCY_SQLITE_PATH", raising=False)
    _reset_hmac_state()
    yield
    _reset_hmac_state()


def _sign(secret: str, timestamp: str, idempotency: str, payload: dict) -> str:
    body = json.dumps(payload).encode("utf-8")
    message = b"|".join([timestamp.encode("utf-8"), idempotency.encode("utf-8"), body])
    return hmac.new(secret.encode("utf-8"), message, hashlib.sha256).hexdigest()


def _make_headers(secret: str, payload: dict, timestamp: str | None = None, idempotency: str = "abc123"):
    ts = timestamp or str(int(time.time()))
    signature = _sign(secret, ts, idempotency, payload)
    return {
        TIMESTAMP_HEADER: ts,
        IDEMPOTENCY_HEADER: idempotency,
        SIGNATURE_HEADER: signature,
    }


def test_relay_status_valid_signature():
    payload = {"job_id": "job-1", "phase": "running"}
    headers = _make_headers("super-secret", payload)

    response = asyncio.run(_call_status(payload, headers))

    assert response.ok is True


def test_relay_status_invalid_signature():
    payload = {"job_id": "job-2", "phase": "running"}
    timestamp = str(int(time.time()))
    headers = {
        TIMESTAMP_HEADER: timestamp,
        IDEMPOTENCY_HEADER: "abc123",
        SIGNATURE_HEADER: "invalid",
    }

    with pytest.raises(HTTPException) as exc:
        asyncio.run(_call_status(payload, headers))
    assert exc.value.status_code == 401


def test_relay_status_duplicate_returns_same_ack():
    payload = {"job_id": "job-3", "phase": "running"}
    timestamp = str(int(time.time()))
    headers = _make_headers("super-secret", payload, timestamp=timestamp, idempotency="replay-key")

    first = asyncio.run(_call_status(payload, headers))
    assert first.ok is True

    second = asyncio.run(_call_status(payload, headers))
    assert second.ok is True


def test_relay_status_conflicting_payload():
    timestamp = str(int(time.time()))
    key = "conflict-key"
    payload = {"job_id": "job-4", "phase": "running"}
    headers = _make_headers("super-secret", payload, timestamp=timestamp, idempotency=key)
    asyncio.run(_call_status(payload, headers))

    conflicting_payload = {"job_id": "job-4", "phase": "done"}
    conflicting_headers = _make_headers("super-secret", conflicting_payload, timestamp=timestamp, idempotency=key)

    with pytest.raises(HTTPException) as exc:
        asyncio.run(_call_status(conflicting_payload, conflicting_headers))

    assert exc.value.status_code == 409


def test_relay_status_sqlite_backend(tmp_path, monkeypatch):
    db_path = tmp_path / "idem.db"
    monkeypatch.setenv("SHERATAN_IDEMPOTENCY_SQLITE_PATH", str(db_path))
    _reset_hmac_state()

    payload = {"job_id": "job-5", "phase": "running"}
    headers = _make_headers("super-secret", payload, idempotency="sqlite-key")

    first = asyncio.run(_call_status(payload, headers))
    assert first.ok is True

    second = asyncio.run(_call_status(payload, headers))
    assert second.ok is True


def _build_request(payload: dict, headers: dict[str, str]) -> Request:
    body = json.dumps(payload).encode("utf-8")
    header_pairs = [(k.lower().encode("utf-8"), v.encode("utf-8")) for k, v in headers.items()]
    scope = {
        "type": "http",
        "method": "POST",
        "path": "/relay/status",
        "headers": header_pairs,
    }

    async def receive():
        return {"type": "http.request", "body": body, "more_body": False}

    request = Request(scope, receive)
    request._body = body  # cache for repeated reads
    return request


async def _call_status(payload: dict, headers: dict[str, str]):
    request = _build_request(payload, headers)
    event = RelayStatus(**payload)
    return await relay_status(
        request=request,
        evt=event,
        timestamp=headers[TIMESTAMP_HEADER],
        idempotency=headers[IDEMPOTENCY_HEADER],
        signature=headers.get(SIGNATURE_HEADER),
    )
