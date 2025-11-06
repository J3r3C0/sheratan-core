from __future__ import annotations
import hmac, hashlib, os, time
from typing import Tuple

SKEW = int(os.getenv("SHERATAN_HMAC_SKEW_SEC", "300"))
SECRET = os.getenv("SHERATAN_HMAC_SECRET", "")

def verify_hmac(ts: str, signature: str, body_bytes: bytes) -> Tuple[bool,str]:
    if not SECRET:
        return False, "secret-missing"
    try:
        t = int(ts)
    except Exception:
        return False, "timestamp-invalid"
    now = int(time.time())
    if abs(now - t) > SKEW:
        return False, "timestamp-skew"
    msg = ts.encode() + b"." + body_bytes
    expected = hmac.new(SECRET.encode(), msg, hashlib.sha256).hexdigest()
    if not signature.startswith("sha256="):
        return False, "signature-format"
    provided = signature.split("=",1)[1]
    if not hmac.compare_digest(expected, provided):
        return False, "signature-mismatch"
    return True, "ok"
