#!/usr/bin/env python3
"""Public Assets Policy (signed) v0.7

Schema (policy.json):
{
  "version": "0.1",
  "asset_id": "CID-or-hash",
  "license": "SPDX or URL",
  "distribution": {"mode": "replication", "r": 5}   # or {"mode":"ec","k":12,"n":20}
  "safety_tags": ["permissive","no-pii"],
  "timestamp": 1730000000,
  "signed_by": "<node_id>",
  "verify_key": "<base64 Ed25519 verify key>",
  "signature": "<base64 sig over canonical body>"
}
"""
import json, base64, time
from pathlib import Path
from nacl import signing

def b64e(b: bytes) -> str: return base64.b64encode(b).decode()
def b64d(s: str) -> bytes: return base64.b64decode(s.encode())

def canonical(obj: dict) -> bytes:
    # exclude signature field for signing
    clean = {k: v for k, v in obj.items() if k != "signature"}
    return json.dumps(clean, sort_keys=True, separators=(",",":")).encode()

def create_policy(keys_path: str, node_id: str, asset_id: str, license_str: str, distribution: dict, safety_tags=None) -> dict:
    sk = signing.SigningKey(b64d(json.loads(Path(keys_path).read_text())["ed25519"]["signing_key"]))
    vk_b64 = b64e(bytes(sk.verify_key))
    pol = {
        "version": "0.1",
        "asset_id": asset_id,
        "license": license_str,
        "distribution": distribution,
        "safety_tags": safety_tags or ["permissive"],
        "timestamp": int(time.time()),
        "signed_by": node_id,
        "verify_key": vk_b64
    }
    sig = sk.sign(canonical(pol)).signature
    pol["signature"] = b64e(sig)
    return pol

def verify_policy(pol: dict) -> bool:
    try:
        vk = signing.VerifyKey(b64d(pol["verify_key"]))
        vk.verify(canonical(pol), b64d(pol["signature"]))
        return True
    except Exception:
        return False

if __name__ == "__main__":
    import argparse, json
    ap = argparse.ArgumentParser()
    ap.add_argument("--keys", default="./keys/node-A.json")
    ap.add_argument("--node_id", default="node-A")
    ap.add_argument("--asset_id", required=True)
    ap.add_argument("--license", required=True)
    ap.add_argument("--mode", choices=["replication","ec"], default="replication")
    ap.add_argument("--r", type=int, default=5)
    ap.add_argument("--k", type=int, default=12)
    ap.add_argument("--n", type=int, default=20)
    ap.add_argument("--out", default="./assets/policy.json")
    args = ap.parse_args()

    if args.mode == "replication":
        dist = {"mode":"replication","r":args.r}
    else:
        dist = {"mode":"ec","k":args.k,"n":args.n}

    pol = create_policy(args.keys, args.node_id, args.asset_id, args.license, dist)
    Path(args.out).write_text(json.dumps(pol, indent=2), encoding="utf-8")
    print(f"[policy] wrote {args.out}; verify={verify_policy(pol)}")
