#!/usr/bin/env python3
import time, json, argparse
from pathlib import Path
from lora_binding import SerialTransport, MockTransport, encode_frame, decode_frame, make_beacon

DISCOVERY_FILE = Path("./discovery/mesh_hosts.json")

from discovery.atomic_hosts import merge_entry

def update_hosts(endpoint: str, node_id: str):
    merge_entry(endpoint, node_id, "lora")
    DISCOVERY_FILE.parent.mkdir(parents=True, exist_ok=True)
    hosts = {}
    if DISCOVERY_FILE.exists():
        try: hosts = json.loads(DISCOVERY_FILE.read_text(encoding="utf-8"))
        except Exception: hosts = {}
    hosts[endpoint] = {"node_id": node_id, "last_seen": int(time.time()), "via": "lora"}
    DISCOVERY_FILE.write_text(json.dumps(hosts, indent=2), encoding="utf-8")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--node_id", default="node-A")
    ap.add_argument("--endpoint", default="http://127.0.0.1:8081")
    ap.add_argument("--serial", default=None, help="z.B. /dev/ttyUSB0 (wenn gesetzt, nutzt Serial; sonst Mock)")
    ap.add_argument("--baud", type=int, default=57600)
    ap.add_argument("--interval", type=float, default=10.0, help="Beacon-Intervall Sekunden")
    args = ap.parse_args()

    tr = None
    if args.serial:
        tr = SerialTransport(args.serial, args.baud)
        print(f"[lora] serial transport on {args.serial}@{args.baud}")
    else:
        tr = MockTransport()
        print("[lora] MOCK transport (File-Bus) aktiv")

    try:
        last = 0
        while True:
            now = time.time()
            if now - last >= args.interval:
                frame = encode_frame(make_beacon(args.node_id, args.endpoint))
                tr.send(frame)
                last = now
            b = tr.recv(timeout_s=0.5)
            if b:
                msg = decode_frame(b)
                if msg.get("t") == "beacon" and "ep" in msg:
                    update_hosts(msg["ep"], msg.get("node","?"))
            time.sleep(0.05)
    except KeyboardInterrupt:
        pass
    finally:
        try: tr.close()
        except Exception: pass

if __name__ == "__main__":
    main()
