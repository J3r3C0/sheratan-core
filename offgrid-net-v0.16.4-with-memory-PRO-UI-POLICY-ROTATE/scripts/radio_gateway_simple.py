#!/usr/bin/env python3
import json, time, argparse
from pathlib import Path

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--node_id", required=True)
    ap.add_argument("--endpoint", required=True, help="http://127.0.0.1:PORT")
    ap.add_argument("--peer", default="", help="optional peer endpoint to include")
    ap.add_argument("--interval", type=int, default=3)
    args = ap.parse_args()

    disc = Path("./discovery/mesh_hosts.json")
    disc.parent.mkdir(parents=True, exist_ok=True)

    print(f"[radio] {args.node_id} publishing beacons every {args.interval}s")
    n = 0
    while True:
        n += 1
        hosts = []
        hosts.append({"node": args.node_id, "endpoint": args.endpoint, "via": "udp-sim", "seen": time.time()})
        if args.peer:
            hosts.append({"node": f"peer-of-{args.node_id}", "endpoint": args.peer, "via": "udp-sim", "seen": time.time()})
        disc.write_text(json.dumps({"cycle": n, "hosts": hosts}, indent=2), encoding="utf-8")
        time.sleep(args.interval)

if __name__ == "__main__":
    main()
