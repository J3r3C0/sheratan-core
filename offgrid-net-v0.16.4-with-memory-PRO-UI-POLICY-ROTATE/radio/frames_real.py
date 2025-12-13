#!/usr/bin/env python3
import json, time, base64
from typing import Optional

MAX = 480  # conservative MTU for safety

def enc(obj: dict) -> bytes:
    raw = json.dumps(obj, separators=(",",":"))
    b = raw.encode("utf-8")
    if len(b) > MAX:
        raise ValueError("frame too large")
    return b

def dec(b: bytes) -> dict:
    return json.loads(b.decode("utf-8"))

def beacon(node_id: str, endpoint: str) -> dict:
    return {"t":"beacon","node":node_id,"ep":endpoint,"ts":int(time.time())}

# --- Ed25519 signing helpers (PyNaCl) ---
def sign_frame(obj: dict, ed25519_sk_b64: str) -> dict:
    """Add signature field 'sig' to obj, based on compact JSON of {t,node,ep,ts}."""
    try:
        from nacl import signing
    except Exception as e:
        raise RuntimeError("PyNaCl required for signing") from e
    core = {k: obj[k] for k in ("t","node","ep","ts") if k in obj}
    sk = signing.SigningKey(base64.b64decode(ed25519_sk_b64))
    sig = sk.sign(json.dumps(core, separators=(",",":")).encode("utf-8")).signature
    out = dict(obj)
    out["sig"] = base64.b64encode(sig).decode("ascii")
    out["vk"]  = base64.b64encode(sk.verify_key.encode()).decode("ascii")
    return out

def verify_frame(obj: dict) -> bool:
    """Verify signature against included verify key 'vk'."""
    try:
        from nacl import signing
    except Exception:
        return False
    if "sig" not in obj or "vk" not in obj:
        return False
    core = {k: obj[k] for k in ("t","node","ep","ts") if k in obj}
    vk = signing.VerifyKey(base64.b64decode(obj["vk"]))
    sig = base64.b64decode(obj["sig"])
    try:
        vk.verify(json.dumps(core, separators=(",",":")).encode("utf-8"), sig)
        return True
    except Exception:
        return False
