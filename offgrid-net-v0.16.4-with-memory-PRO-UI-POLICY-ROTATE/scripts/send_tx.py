#!/usr/bin/env python3
import json, sys, urllib.request, base64
from pathlib import Path
from economy.txlog import create_tx, sign_tx, pool_add_or_update

def load_signing_key_b64(keys_path: str) -> str:
    obj = json.loads(Path(keys_path).read_text(encoding="utf-8"))
    return obj["ed25519"]["signing_key"]

if __name__ == "__main__":
    if len(sys.argv)<6:
        print("Usage: python scripts/send_tx.py <src> <dst> <amount> <fee> <nonce> [keys_path] [peer...]")
        sys.exit(1)
    src, dst, amount, fee, nonce = sys.argv[1], sys.argv[2], float(sys.argv[3]), float(sys.argv[4]), int(sys.argv[5])
    keys = sys.argv[6] if len(sys.argv)>6 else "./keys/node-A.json"
    peers = sys.argv[7:]
    tx = create_tx(src, dst, amount, fee, nonce, meta={})
    sig = sign_tx(tx, load_signing_key_b64(keys))
    tx["sign"] = sig
    tx["witnesses"] = [sig]  # author counts as witness 1
    pool_add_or_update(tx)
    # broadcast to peers
    for p in peers:
        try:
            req = urllib.request.Request(f"{p}/gossip/tx_witness", data=json.dumps(tx).encode(), headers={"Content-Type":"application/json"})
            urllib.request.urlopen(req, timeout=5).read()
        except Exception:
            pass
    print(json.dumps({"id": tx["id"], "broadcasted_to": peers}, indent=2))
