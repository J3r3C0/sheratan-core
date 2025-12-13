#!/usr/bin/env python3
import json, glob
from pathlib import Path

LEDGER_DIR = Path("./_ledger")

def merge_from(dir_path: str):
    src = Path(dir_path)
    for p in sorted(src.glob("*.json")):
        blk = json.loads(p.read_text(encoding="utf-8"))
        out = LEDGER_DIR / p.name
        if not out.exists():
            out.write_text(json.dumps(blk, indent=2), encoding="utf-8")

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("dir", help="ledger directory to merge from")
    args = ap.parse_args()
    merge_from(args.dir)
    print("[merge] done")
