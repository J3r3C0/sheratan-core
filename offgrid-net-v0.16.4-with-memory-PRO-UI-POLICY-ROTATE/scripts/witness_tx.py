#!/usr/bin/env python3
import json, sys, urllib.request
from pathlib import Path
from economy.txlog import pool_get, add_witness, sign_tx, pool_add_or_update

def load_signing_key_b64(keys_path: str) -> str:
    obj = json.loads(Path(keys_path).read_text(encoding="utf-8"))
    return obj["ed25519"]["signing_key"]

if __name__ == "__main__":
    if len(sys.argv)<3:
        print("Usage: python scripts/witness_tx.py <tx_id> <keys_path> [peer...]")
        sys.exit(1)
    tx_id = sys.argv[1]; keys = sys.argv[2]; peers = sys.argv[3:]
    tx = pool_get(tx_id)
    if not tx:
        print("tx not in pool"); sys.exit(2)
    sig = sign_tx(tx, load_signing_key_b64(keys))
    tx = add_witness(tx, sig)
    pool_add_or_update(tx)
    for p in peers:
        try:
            req = urllib.request.Request(f"{p}/gossip/tx_witness", data=json.dumps(tx).encode(), headers={"Content-Type":"application/json"})
            urllib.request.urlopen(req, timeout=5).read()
        except Exception:
            pass
    print(json.dumps({"id": tx_id, "witnesses": len(tx.get("witnesses",[]))}, indent=2))
