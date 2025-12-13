#!/usr/bin/env python3
import argparse, json, time, threading
from pathlib import Path
from radio.transport_udp import UdpMulticast
from radio.frames_real import enc, dec, beacon, sign_frame, verify_frame

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--node_id", required=True)
    ap.add_argument("--endpoint", required=True)
    ap.add_argument("--ed25519_sk_b64", default="")
    ap.add_argument("--group", default="239.23.0.7")
    ap.add_argument("--port", type=int, default=47007)
    ap.add_argument("--interval", type=float, default=3.0)
    ap.add_argument("--out", default="discovery/mesh_hosts.json")
    args = ap.parse_args()

    out = Path(args.out); out.parent.mkdir(parents=True, exist_ok=True)
    udp = UdpMulticast(group=args.group, port=args.port)
    last = {}

    def tx_loop():
        while True:
            msg = beacon(args.node_id, args.endpoint)
            if args.ed25519_sk_b64:
                msg = sign_frame(msg, args.ed25519_sk_b64)
            udp.send(enc(msg))
            time.sleep(args.interval)

    def rx_loop():
        while True:
            raw = udp.recv(timeout_s=1.0)
            if not raw:
                continue
            try:
                obj = dec(raw)
            except Exception:
                continue
            if obj.get("t") != "beacon":
                continue
            if ("sig" in obj or "vk" in obj) and not verify_frame(obj):
                continue
            key = f"{obj.get('node')}|{obj.get('ep')}"
            last[key] = {"node": obj.get("node"), "endpoint": obj.get("ep"),
                         "seen": time.time(), "vk": obj.get("vk","")}
            if len(last) % 2 == 0:
                data = {"updated": time.time(), "hosts": list(last.values())}
                out.write_text(json.dumps(data, indent=2), encoding="utf-8")

    threading.Thread(target=tx_loop, daemon=True).start()
    threading.Thread(target=rx_loop, daemon=True).start()
    print(f"[radio] {args.node_id} on {args.group}:{args.port} (interval={args.interval}s)")
    try:
        while True:
            time.sleep(5)
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()
