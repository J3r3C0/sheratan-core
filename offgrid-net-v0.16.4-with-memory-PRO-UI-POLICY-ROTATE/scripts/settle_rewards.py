#!/usr/bin/env python3
import json, glob, pathlib, sys
from economy.settlement import settle_from_batch

def latest_batch():
    import glob
    files = sorted(glob.glob("_receipts/batch_*.json"))
    return files[-1] if files else None

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/settle_rewards.py '<node_id_to_hosturl_json>'")
        print("Example: python scripts/settle_rewards.py '{"did:key:z-demo":"http://127.0.0.1:8081"}'")
        sys.exit(1)
    mapping = sys.argv[1]
    lb = latest_batch()
    assert lb, "No batch found; export one via /receipts/export"
    res = settle_from_batch(lb, json.loads(mapping), host_reserve_rate=0.01)
    print(json.dumps(res, indent=2))
