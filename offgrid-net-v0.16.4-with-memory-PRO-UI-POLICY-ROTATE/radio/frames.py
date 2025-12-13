#!/usr/bin/env python3
"""radio/frames.py — Compact JSON frame helpers (v0.12)

Frame (<= ~220B typical):
{ "t": "beacon"|"ping"|"pong", "node": "id", "ep": "http://ip:port", "ts": 1730000000 }
"""
import json, time

MAX = 240

def enc(obj: dict) -> bytes:
    raw = json.dumps(obj, separators=(",",":"))
    b = raw.encode()
    if len(b) > MAX: raise ValueError("frame too large: %d > %d" % (len(b), MAX))
    return b

def dec(b: bytes) -> dict:
    try: return json.loads(b.decode())
    except Exception: return {}

def beacon(node_id: str, endpoint: str) -> dict:
    return {"t":"beacon","node":node_id,"ep":endpoint,"ts":int(time.time())}

def ping(node_id: str) -> dict:
    return {"t":"ping","node":node_id,"ts":int(time.time())}

def pong(node_id: str) -> dict:
    return {"t":"pong","node":node_id,"ts":int(time.time())}


# --- Signing (Ed25519) using PyNaCl
import base64, json as _json
from nacl import signing as _signing

def _b64e(b: bytes) -> str: return base64.b64encode(b).decode()
def _b64d(s: str) -> bytes: return base64.b64decode(s.encode())

def _canonical(obj: dict) -> bytes:
    clean = {k:v for k,v in obj.items() if k not in ("sig","verify_key")}
    return _json.dumps(clean, sort_keys=True, separators=(",",":")).encode()

def sign_frame(frame: dict, keys_path: str) -> dict:
    """Attach verify_key + sig to frame using keys_path (ed25519)."""
    k = _json.loads(open(keys_path, "r", encoding="utf-8").read())
    sk = _signing.SigningKey(_b64d(k["ed25519"]["signing_key"]))
    vk_b64 = _b64e(bytes(sk.verify_key))
    sig = sk.sign(_canonical(frame)).signature
    out = dict(frame)
    out["verify_key"] = vk_b64
    out["sig"] = _b64e(sig)
    return out

def verify_frame(signed: dict) -> bool:
    try:
        vk = _signing.VerifyKey(_b64d(signed["verify_key"]))
        vk.verify(_canonical(signed), _b64d(signed["sig"]))
        return True
    except Exception:
        return False
