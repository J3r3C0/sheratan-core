#!/usr/bin/env python3
"""Auto-Settlement Daemon v0.7
- Läuft lokal am Host.
- Baut regelmäßig ein Mapping {node_id: endpoint} aus discovery/mesh_hosts.json.
- Triggert lokalen /receipts/export (optional) und settled die neueste Batch in Wallets.
- Wendet host_reserve an, schreibt _balances.json.
"""
import time, json, glob, urllib.request
from pathlib import Path
from economy.settlement import settle_from_batch
from economy.txlog import create_tx, sign_tx, pool_add_or_update, finalize_tx

DISCOVERY = Path("./discovery/mesh_hosts.json")
RECEIPTS_DIR = Path("./_receipts")

def build_mapping():
    m = {}
    if DISCOVERY.exists():
        try:
            hosts = json.loads(DISCOVERY.read_text(encoding="utf-8"))
            # try to get node_id via /announce
            for ep in list(hosts.keys()):
                try:
                    obj = json.loads(urllib.request.urlopen(f"{ep}/announce", timeout=2).read().decode())
                    nid = obj.get("node_id") or hosts[ep].get("node_id")
                    if nid: m[nid] = ep
                except Exception:
                    pass
        except Exception:
            pass
    return m

def latest_batch():
    files = sorted(RECEIPTS_DIR.glob("batch_*.json"))
    return files[-1] if files else None

def export_local_batch(local_endpoint="http://127.0.0.1:8081"):
    try:
        urllib.request.urlopen(f"{local_endpoint}/receipts/export", timeout=3).read()
    except Exception:
        pass

def load_signing_key_b64(keys_path: str):
    obj = json.loads(Path(keys_path).read_text(encoding='utf-8'))
    return obj['ed25519']['signing_key']

def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--interval", type=int, default=30)
    ap.add_argument("--host_reserve", type=float, default=0.01)
    ap.add_argument("--local_endpoint", default="http://127.0.0.1:8081")
    ap.add_argument("--keys", default="./keys/node-A.json")
    ap.add_argument("--quorum", type=int, default=2)
    ap.add_argument("--peers", nargs="+", default=[])
    args = ap.parse_args()

    print(f"[auto-settle] every {args.interval}s, reserve={args.host_reserve}")
    seen_batches = set()
    try:
        while True:
            # 1) Export local receipts to a new batch (if any)
            export_local_batch(args.local_endpoint)
            # 2) Build mapping
            mp = build_mapping()
            # 3) Find latest batch
            lb = latest_batch()
            if lb and lb.as_posix() not in seen_batches:
                res = settle_from_batch(lb.as_posix(), mp, host_reserve_rate=args.host_reserve)
                print(json.dumps({"batch": lb.name, "settlement": res}, indent=2))
                # emit TXs: mint -> host (net), mint -> system (reserve)
                sk_b64 = load_signing_key_b64(args.keys)
                nonce = int(time.time())
                for it in res.get('items', []):
                    host_acct = it['account']
                    net = float(it['net']); reserve = float(it['reserve'])
                    # net to host
                    tx1 = create_tx('mint', host_acct, net, 0.0, nonce, meta={'type':'settlement','batch':lb.name})
                    sig1 = sign_tx(tx1, sk_b64); tx1['sign']=sig1; tx1['witnesses']=[sig1]
                    pool_add_or_update(tx1)
                    # reserve to system (explicit, though balances accrue fee anyway; for audit)
                    if reserve > 0:
                        tx2 = create_tx('mint', 'system', reserve, 0.0, nonce+1, meta={'type':'reserve','batch':lb.name})
                        sig2 = sign_tx(tx2, sk_b64); tx2['sign']=sig2; tx2['witnesses']=[sig2]
                        pool_add_or_update(tx2)
                    nonce += 2
                # simple local finalize if quorum==1; else wait for witnesses and attempt finalize
                for pending in [] if args.quorum>1 else [tx1['id']]:
                    finalize_tx(pending, quorum_m=args.quorum)
                seen_batches.add(lb.as_posix())
            time.sleep(args.interval)
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()
