#!/usr/bin/env python3
"""BT-LR Binding v0.7
- Ziel: Announce/Keep-alive über Bluetooth-Long-Range-ähnlichen Kanal.
- Ohne echte BT-Stack-Abhängigkeiten: Mock-Transport (Datei-Bus).
- Nachrichten wie bei LoRa: kleine JSON-Frames (<= ~220B).
"""
import json, time
from pathlib import Path

MAX_FRAME = 220

class MockBTBus:
    def __init__(self, path="./radio/_bt_bus.txt"):
        self.p = Path(path); self.p.parent.mkdir(parents=True, exist_ok=True)
        if not self.p.exists(): self.p.write_text("", encoding="utf-8")
        self._ofs = 0
    def send(self, frame: bytes):
        with self.p.open("ab") as f: f.write(frame + b"\n")
    def recv(self, timeout_s=0.5):
        t0 = time.time()
        while time.time() - t0 < timeout_s:
            data = self.p.read_bytes()
            if len(data) > self._ofs:
                nl = data.find(b"\n", self._ofs)
                if nl != -1:
                    frame = data[self._ofs:nl]
                    self._ofs = nl + 1
                    return frame
            time.sleep(0.05)
        return b""

def encode(msg: dict) -> bytes:
    b = json.dumps(msg, separators=(",",":")).encode()
    if len(b) > MAX_FRAME: raise ValueError("frame too large")
    return b

def decode(b: bytes) -> dict:
    try: return json.loads(b.decode())
    except Exception: return {}

def make_beacon(node_id: str, endpoint: str) -> dict:
    return {"t":"beacon","node":node_id,"ep":endpoint,"ts":int(time.time())}
