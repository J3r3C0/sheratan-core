from __future__ import annotations

import asyncio
import time
from typing import Set

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

router = APIRouter(prefix="/metrics", tags=["metrics"])


class ModuleCallEvent(BaseModel):
    timestamp: float = Field(default_factory=lambda: time.time())
    source: str
    target: str
    duration_ms: float
    status: str = "ok"  # z.B. "ok", "error", "timeout"
    correlation_id: str | None = None


# Sehr simpler In-Memory-Broadcaster
class WebSocketBroadcaster:
    def __init__(self) -> None:
        self._clients: Set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        async with self._lock:
            self._clients.add(ws)

    async def disconnect(self, ws: WebSocket) -> None:
        async with self._lock:
            self._clients.discard(ws)

    async def broadcast(self, payload: dict) -> None:
        # sendet an alle aktuell verbundenen Clients
        async with self._lock:
            clients = list(self._clients)

        to_remove: list[WebSocket] = []
        for ws in clients:
            try:
                await ws.send_json(payload)
            except Exception:
                to_remove.append(ws)

        if to_remove:
            async with self._lock:
                for ws in to_remove:
                    self._clients.discard(ws)


broadcaster = WebSocketBroadcaster()


@router.post("/module-calls")
async def push_module_call(event: ModuleCallEvent):
    """
    Sheratan Core (oder andere Services) POSTen hier alle Modulaufrufe hin.
    Diese werden 1:1 in Echtzeit an alle WebSocket-Clients weitergegeben.
    """
    await broadcaster.broadcast({"type": "module_call", "data": event.dict()})
    return {"ok": True}


@router.websocket("/ws/module-calls")
async def ws_module_calls(ws: WebSocket):
    """
    WebSocket-Stream für das Frontend:
    - sendet alle eingehenden ModuleCallEvents
    - hält die Verbindung offen, bis der Client schließt
    """
    await broadcaster.connect(ws)
    try:
        while True:
            # Wir erwarten keine Messages vom Client, brauchen aber
            # ein receive() um Disconnects sauber mitzubekommen.
            await ws.receive_text()
    except WebSocketDisconnect:
        await broadcaster.disconnect(ws)
    except Exception:
        await broadcaster.disconnect(ws)
