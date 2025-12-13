#!/usr/bin/env python3
import json, time, argparse
from pathlib import Path

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--node_id", required=True)
    ap.add_argument("--out", default="_swim_neighbors.json")
    ap.add_argument("--interval", type=float, default=5)
    args = ap.parse_args()

    print(f"[swim] node {args.node_id} heartbeating every {args.interval}s")
    i = 0
    p = Path(args.out)
    while True:
        i += 1
        p.write_text(json.dumps({"node": args.node_id, "heartbeat": i, "ts": time.time()}, indent=2), encoding="utf-8")
        time.sleep(args.interval)

if __name__ == "__main__":
    main()
