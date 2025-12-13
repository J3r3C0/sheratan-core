#!/usr/bin/env python3
import json
from pathlib import Path

BAL_FILE = Path("./_balances.json")
TX_LOG = Path("./_txlog.json")

def load_bal():
    if BAL_FILE.exists(): return json.loads(BAL_FILE.read_text(encoding="utf-8"))
    return {"system":0.0}

def save_bal(obj): BAL_FILE.write_text(json.dumps(obj, indent=2), encoding="utf-8")

def load_log():
    if TX_LOG.exists(): return json.loads(TX_LOG.read_text(encoding="utf-8"))
    return []

def save_log(arr): TX_LOG.write_text(json.dumps(arr, indent=2), encoding="utf-8")

def reconcile(remote_bal: dict):
    local = load_bal()
    log = load_log()
    # naive: align to max on each key; if divergence > threshold, record conflict entry
    conflicts = []
    for k,v in remote_bal.items():
        if k not in local:
            local[k] = v
        else:
            if abs(local[k]-v) > 1e-9:
                # conflict -> choose max, record
                chosen = max(local[k], v)
                conflicts.append({"account":k, "local":local[k], "remote":v, "chosen":chosen})
                local[k] = chosen
    save_bal(local)
    if conflicts:
        log.append({"ts": int(__import__("time").time()*1000), "conflicts": conflicts})
        save_log(log)
    return {"balances": local, "conflicts": conflicts}

if __name__ == "__main__":
    import argparse, json
    ap = argparse.ArgumentParser()
    ap.add_argument("remote_bal_json", help="path to remote balances json")
    args = ap.parse_args()
    rem = json.loads(Path(args.remote_bal_json).read_text(encoding="utf-8"))
    print(json.dumps(reconcile(rem), indent=2))
