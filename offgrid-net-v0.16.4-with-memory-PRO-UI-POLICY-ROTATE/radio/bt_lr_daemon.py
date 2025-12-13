#!/usr/bin/env python3
import time, json, argparse
from pathlib import Path
from bt_lr_binding import MockBTBus, encode, decode, make_beacon

DISCOVERY_FILE = Path("./discovery/mesh_hosts.json")

from discovery.atomic_hosts import merge_entry

def update_hosts(endpoint: str, node_id: str):
    merge_entry(endpoint, node_id, "bt_lr")
    DISCOVERY_FILE.parent.mkdir(parents=True, exist_ok=True)
    hosts = {}
    if DISCOVERY_FILE.exists():
        try: hosts = json.loads(DISCOVERY_FILE.read_text(encoding="utf-8"))
        except Exception: hosts = {}
    hosts[endpoint] = {"node_id": node_id, "last_seen": int(time.time()), "via": "bt_lr"}
    DISCOVERY_FILE.write_text(json.dumps(hosts, indent=2), encoding="utf-8")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--node_id", default="node-A")
    ap.add_argument("--endpoint", default="http://127.0.0.1:8081")
    ap.add_argument("--interval", type=float, default=8.0)
    args = ap.parse_args()

    bus = MockBTBus()
    print("[bt-lr] MOCK bus aktiv")
    try:
        last = 0
        while True:
            now = time.time()
            if now - last >= args.interval:
                bus.send(encode(make_beacon(args.node_id, args.endpoint)))
                last = now
            b = bus.recv(timeout_s=0.5)
            if b:
                msg = decode(b)
                if msg.get("t") == "beacon" and "ep" in msg:
                    update_hosts(msg["ep"], msg.get("node","?"))
            time.sleep(0.05)
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()
