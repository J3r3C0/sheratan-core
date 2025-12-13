#!/usr/bin/env python3
"""radio/transport.py — Unified radio abstraction (v0.12)

Transports:
- UDP Multicast (default simulation; works on any laptop): class UdpMulticast
- LoRa Serial (optional, requires pyserial): class LoRaSerial
- FileBus (fallback/dev): class FileBus

All provide:
- send(frame: bytes) -> None
- recv(timeout_s: float) -> bytes  (empty bytes if timeout)
- close() -> None
"""
import os, socket, struct, time
from pathlib import Path

# ---------- UDP Multicast (robust sim) ----------
class UdpMulticast:
    def __init__(self, group="239.23.0.7", port=47007, iface="0.0.0.0", ttl=1):
        self.group = group; self.port = port
        # Sender
        self.tx = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.tx.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)
        # Receiver
        self.rx = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.rx.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            self.rx.bind(("", port))
        except OSError:
            # on some OS require binding to group
            self.rx.bind((group, port))
        mreq = struct.pack("=4sl", socket.inet_aton(group), socket.INADDR_ANY)
        self.rx.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        self.rx.settimeout(0.5)

    def send(self, b: bytes):
        self.tx.sendto(b, (self.group, self.port))

    def recv(self, timeout_s=0.5) -> bytes:
        self.rx.settimeout(timeout_s)
        try:
            data, _ = self.rx.recvfrom(2048)
            return data
        except socket.timeout:
            return b""

    def close(self):
        try: self.tx.close()
        except: pass
        try: self.rx.close()
        except: pass

# ---------- LoRa Serial (optional pyserial) ----------
try:
    import serial  # type: ignore
except Exception:
    serial = None

class LoRaSerial:
    """Line-oriented frames over UART (e.g., TNC/AT firmware).
    Assumes module echoes one JSON frame per line.
    """
    def __init__(self, port="/dev/ttyUSB0", baud=57600, timeout=0.5):
        if serial is None:
            raise RuntimeError("pyserial not installed: pip install pyserial")
        self.ser = serial.Serial(port, baudrate=baud, timeout=timeout)

    def send(self, b: bytes):
        self.ser.write(b + b"\n")

    def recv(self, timeout_s=0.5) -> bytes:
        self.ser.timeout = timeout_s
        line = self.ser.readline()
        return line.strip()

    def close(self):
        try: self.ser.close()
        except: pass

# ---------- FileBus (legacy dev fallback) ----------
class FileBus:
    def __init__(self, path="./radio/_bus.txt"):
        self.p = Path(path); self.p.parent.mkdir(parents=True, exist_ok=True)
        if not self.p.exists(): self.p.write_text("", encoding="utf-8")
        self._ofs = 0

    def send(self, b: bytes):
        with self.p.open("ab") as f: f.write(b + b"\n")

    def recv(self, timeout_s=0.5) -> bytes:
        import time
        t0 = time.time()
        while time.time()-t0 < timeout_s:
            data = self.p.read_bytes()
            nl = data.find(b"\n", self._ofs)
            if nl != -1:
                frame = data[self._ofs:nl]
                self._ofs = nl + 1
                return frame
            time.sleep(0.05)
        return b""

    def close(self):
        pass
