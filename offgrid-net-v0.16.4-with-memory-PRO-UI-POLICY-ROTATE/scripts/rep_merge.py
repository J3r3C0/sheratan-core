#!/usr/bin/env python3
import json, sys
from pathlib import Path

REP_FILE = Path("./_reputation.json")
def load_rep():
    if REP_FILE.exists(): return json.loads(REP_FILE.read_text(encoding="utf-8"))
    return {}
def save_rep(obj): REP_FILE.write_text(json.dumps(obj, indent=2), encoding="utf-8")

if __name__ == "__main__":
    if len(sys.argv)<2:
        print("Usage: python scripts/rep_merge.py remote_rep.json"); sys.exit(1)
    remote = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    local = load_rep()
    for host, rv in remote.items():
        lv = local.get(host, {"hits":0,"misses":0})
        local[host] = {"hits": max(lv.get("hits",0), rv.get("hits",0)),
                       "misses": max(lv.get("misses",0), rv.get("misses",0))}
    save_rep(local)
    print(json.dumps(local, indent=2))
