#!/usr/bin/env python3
import json, argparse, time, random
from pathlib import Path

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--outfile", default="receipts_node-A.json")
    args = ap.parse_args()
    p = Path(args.outfile)
    p.parent.mkdir(exist_ok=True)
    # append simple receipt
    data = []
    if p.exists():
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            data = []
    data.append({"ts": time.time(), "kind": "upload", "size": random.randint(1000,5000)})
    p.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(f"[upload] wrote receipt to {p}")

if __name__ == "__main__":
    main()
