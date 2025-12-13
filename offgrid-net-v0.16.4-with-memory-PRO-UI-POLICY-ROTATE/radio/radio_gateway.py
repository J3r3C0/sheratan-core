#!/usr/bin/env python3
"""radio_gateway.py — Unified radio gateway (v0.12)

- Uses transport: udp (default), lora-serial, or file
- Periodically sends beacons, listens for frames
- Updates discovery/mesh_hosts.json (adds "via")

Run examples:
  # UDP sim (works on any laptop, multiple terminals)
  python radio/radio_gateway.py --node_id node-A --endpoint http://127.0.0.1:8081 --transport udp --interval 5

  # LoRa serial (requires pyserial and a connected module)
  python -m pip install pyserial
  python radio/radio_gateway.py --transport lora --serial /dev/ttyUSB0 --baud 57600 --node_id node-A --endpoint http://192.168.4.1:8081
"""
import argparse, json, time
from pathlib import Path
from frames import enc, dec, beacon, sign_frame, verify_frame
from transport import UdpMulticast, LoRaSerial, FileBus

DISC = Path("./discovery/mesh_hosts.json")
from discovery.atomic_hosts import merge_entry

def update_hosts(endpoint: str, node_id: str, via: str):
    merge_entry(endpoint, node_id, via)  # atomic
    DISC.parent.mkdir(parents=True, exist_ok=True)
    hosts = {}
    if DISC.exists():
        try: hosts = json.loads(DISC.read_text(encoding="utf-8"))
        except Exception: hosts = {}
    hosts[endpoint] = {"node_id": node_id, "last_seen": int(time.time()), "via": via}
    DISC.write_text(json.dumps(hosts, indent=2), encoding="utf-8")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--node_id", default="node-A")
    ap.add_argument("--endpoint", default="http://127.0.0.1:8081")
    ap.add_argument("--transport", choices=["udp","lora","file"], default="udp")
    ap.add_argument("--interval", type=float, default=8.0)
    ap.add_argument("--keys", default="./keys/node-A.json")
    ap.add_argument("--serial", default="/dev/ttyUSB0")
    ap.add_argument("--baud", type=int, default=57600)
    args = ap.parse_args()

    if args.transport == "udp":
        tr = UdpMulticast()
        via = "udp"
    elif args.transport == "lora":
        tr = LoRaSerial(args.serial, args.baud)
        via = "lora"    
    else:
        tr = FileBus()
        via = "file"

    print(f"[radio-gw] transport={args.transport} via={via}")
    try:
        last = 0
        while True:
            now = time.time()
            if now - last >= args.interval:
                tr.send(enc(sign_frame(beacon(args.node_id, args.endpoint), args.keys)))
                last = now
            b = tr.recv(timeout_s=0.5)
            if b:
                msg = dec(b)
                if msg.get("t") == "beacon" and "ep" in msg:
                    if verify_frame(msg):
                        update_hosts(msg["ep"], msg.get("node","?"), via)
            time.sleep(0.02)
    except KeyboardInterrupt:
        pass
    finally:
        try: tr.close()
        except: pass

if __name__ == "__main__":
    main()
