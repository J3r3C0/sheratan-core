#!/usr/bin/env python3
import time, json
from pathlib import Path
from economy.txlog import finalize_tx
from consensus.quorum import create_or_get, add_ack, is_finalized

POOL = Path("./_txpool.json")

def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--interval", type=float, default=3.0)
    ap.add_argument("--quorum", type=int, default=2)
    args = ap.parse_args()
    while True:
        try:
            pool = json.loads(POOL.read_text(encoding="utf-8")) if POOL.exists() else []
        except Exception:
            pool = []
        for tx in pool:
            txid = tx.get("id"); w = tx.get("witnesses", [])
            if not txid: continue
            create_or_get(txid, "token", args.quorum, meta={"ts": tx.get("ts"), "src": tx.get("src"), "dst": tx.get("dst")})
            for wi in w:
                vk = wi.get("verify_key")
                if vk: add_ack(txid, "token", vk)
            if is_finalized(txid, "token"):
                finalize_tx(txid, quorum_m=args.quorum)
        time.sleep(args.interval)

if __name__ == "__main__":
    main()
