#!/usr/bin/env python3
import json, glob
from pathlib import Path

def main():
    disc = Path("./discovery/mesh_hosts.json")
    print("== Discovery ==")
    if disc.exists():
        print(disc.read_text(encoding="utf-8"))
    else:
        print("no discovery file")

    print("\n== Receipts ==")
    for p in sorted(Path(".").glob("receipts_*.json")):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            print(f"{p.name}: {len(data)} entries")
        except Exception as e:
            print(f"{p.name}: error {e}")

if __name__ == "__main__":
    main()
