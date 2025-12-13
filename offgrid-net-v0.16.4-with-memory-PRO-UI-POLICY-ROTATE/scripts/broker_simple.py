#!/usr/bin/env python3
import json, time, argparse
from pathlib import Path

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sleep", type=int, default=4)
    args = ap.parse_args()
    disc = Path("./discovery/mesh_hosts.json")
    print("[broker] starting; watching discovery/mesh_hosts.json")
    while True:
        if disc.exists():
            try:
                data = json.loads(disc.read_text(encoding="utf-8"))
                hosts = data.get("hosts", [])
                if hosts:
                    print(f"[broker] {len(hosts)} candidate hosts: " + ", ".join(h.get('endpoint','?') for h in hosts))
                else:
                    print("[broker] no candidate hosts")
            except Exception as e:
                print(f"[broker] discovery parse error: {e}")
        else:
            print("[broker] discovery file missing")
        time.sleep(args.sleep)

if __name__ == "__main__":
    main()
