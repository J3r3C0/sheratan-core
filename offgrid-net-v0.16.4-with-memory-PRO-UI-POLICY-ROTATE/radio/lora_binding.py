#!/usr/bin/env python3
"""LoRa Binding v0.5

Ziel: Off-grid Announce/Keep-alive über LoRa (keine Bulk-Daten).
- Optional: pyserial für echte UART-Ports (SX127x-Module mit TNC/AT-Firmware)
- Fallback: Mock-Transport (Datei-basierter Bus) für Tests ohne Hardware

Nachrichtenformat (kompakt, JSON-Frame <= ~200 Bytes):
{
  "t": "beacon" | "ping" | "pong",
  "node": "<node_id>",
  "ep": "http://x.x.x.x:port",     # REST Endpoint
  "ts": 1730000000                # unix seconds
}
"""
import os, json, time, base64
from pathlib import Path

try:
    import serial  # type: ignore
except Exception:
    serial = None

MAX_FRAME = 220  # konservativ

class Transport:
    def send(self, b: bytes): raise NotImplementedError
    def recv(self, timeout_s=0.5) -> bytes: raise NotImplementedError
    def close(self): pass

class SerialTransport(Transport):
    def __init__(self, port: str, baud: int = 57600):
        if serial is None:
            raise RuntimeError("pyserial nicht installiert")
        self.ser = serial.Serial(port, baudrate=baud, timeout=0.2)
    def send(self, b: bytes):
        # Rahmen mit \n als Pakettrenner
        self.ser.write(b + b"\n")
    def recv(self, timeout_s=0.5) -> bytes:
        self.ser.timeout = timeout_s
        line = self.ser.readline()
        return line.strip()
    def close(self):
        try: self.ser.close()
        except Exception: pass

class MockTransport(Transport):
    """Einfacher Datei-basierter Bus für lokale Tests (keine gleichzeitige Mehrprozesssicherheit)."""
    def __init__(self, path="./radio/_lora_bus.txt"):
        self.p = Path(path)
        self.p.parent.mkdir(parents=True, exist_ok=True)
        if not self.p.exists(): self.p.write_text("", encoding="utf-8")
        self._ofs = 0
    def send(self, b: bytes):
        with self.p.open("ab") as f:
            f.write(b + b"\n")
    def recv(self, timeout_s=0.5) -> bytes:
        # naive polling
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

def encode_frame(msg: dict) -> bytes:
    raw = json.dumps(msg, separators=(",",":"))  # kompakt
    b = raw.encode()
    if len(b) > MAX_FRAME:
        raise ValueError("Frame zu groß für LoRa: %d > %d" % (len(b), MAX_FRAME))
    return b

def decode_frame(b: bytes) -> dict:
    try:
        return json.loads(b.decode(errors="ignore"))
    except Exception:
        return {}

def make_beacon(node_id: str, endpoint: str) -> dict:
    return {"t":"beacon","node":node_id,"ep":endpoint,"ts":int(time.time())}

def make_ping(node_id: str) -> dict:
    return {"t":"ping","node":node_id,"ts":int(time.time())}

def make_pong(node_id: str) -> dict:
    return {"t":"pong","node":node_id,"ts":int(time.time())}
