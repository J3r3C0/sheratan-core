#!/usr/bin/env python3
import sys, json, base64, time
from pathlib import Path
from nacl.signing import SigningKey
from nacl.public import PrivateKey

KEYS_DIR = Path("keys")
ARCHIVE_DIR = KEYS_DIR / "archive"
REVOKE_PATH = KEYS_DIR / "revocations.json"
KEYS_DIR.mkdir(parents=True, exist_ok=True)
ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)

def b64(b: bytes) -> str:
    import base64
    return base64.b64encode(b).decode()

def load_json(p: Path, default):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return default

def save_json(p: Path, obj):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, indent=2), encoding="utf-8")

def rotate(node_id: str):
    now = int(time.time())
    cur = KEYS_DIR / f"{node_id}.json"
    if cur.exists():
        old = load_json(cur, {})
        save_json(ARCHIVE_DIR / f"{node_id}-{now}.json", old)
        revs = load_json(REVOKE_PATH, [])
        revs.append({
            "node": node_id,
            "ts": now,
            "ed25519_verify_key": old.get("ed25519", {}).get("verify_key"),
            "x25519_public_key": old.get("x25519", {}).get("public_key"),
            "reason": "rotated",
        })
        save_json(REVOKE_PATH, revs)
    from nacl.signing import SigningKey
    from nacl.public import PrivateKey
    sk = SigningKey.generate(); vk = sk.verify_key
    priv = PrivateKey.generate(); pub = priv.public_key
    save_json(cur, {
        "node": node_id,
        "ed25519": {"signing_key": b64(bytes(sk)), "verify_key": b64(bytes(vk))},
        "x25519": {"private_key": b64(bytes(priv)), "public_key": b64(bytes(pub))},
        "generated_ts": now
    })
    return cur

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/rotate_keys.py <node_id>")
        sys.exit(1)
    p = rotate(sys.argv[1])
    print("Rotated keys ->", p)
