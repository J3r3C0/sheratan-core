#!/usr/bin/env python3
"""radio/ble_binding.py — BLE scanner (bleak) for Offgrid-Net (v0.13)

- Abhängig von: bleak (pip install bleak)
- Wir scannen nach Geräten, deren *Gerätename* mit `OFFGRID:` beginnt.
- Danach folgt eine Base64URL-kodierte Endpoint-URL (z. B. http://192.168.4.1:8081).
- Auf den meisten Laptops ist *Scannen* über bleak problemlos; *Advertise/Peripheral* ist
  plattformabhängig und wird hier NICHT erzwungen (separat via OS-Tools lösbar).

Beispiel Gerätename:
  OFFGRID:aHR0cDovLzEyNy4wLjAuMTo4MDgx   # base64url("http://127.0.0.1:8081")

Dieser Scanner extrahiert den Endpoint und aktualisiert discovery/mesh_hosts.json.
"""
import asyncio, base64, json, time
from pathlib import Path
from typing import Optional

DISC = Path("./discovery/mesh_hosts.json")
from discovery.atomic_hosts import merge_entry
PREFIX = "OFFGRID:"

def b64url_decode(s: str) -> Optional[str]:
    try:
        # add padding if missing
        pad = '=' * (-len(s) % 4)
        return base64.urlsafe_b64decode((s + pad).encode()).decode()
    except Exception:
        return None

async def scan_once(timeout_s=8.0):
    from bleak import BleakScanner
    devices = await BleakScanner.discover(timeout=timeout_s)
    found = []
    for d in devices:
        name = d.name or ""
        if name.startswith(PREFIX):
            enc = name[len(PREFIX):]
            ep = b64url_decode(enc)
            if ep:
                found.append((ep, getattr(d, "address", "?")))
    return found

def update_hosts(entries):
    for ep, addr in entries:
        merge_entry(ep, addr, "ble")
    return


def main():
    import argparse, asyncio
    ap = argparse.ArgumentParser()
    ap.add_argument("--interval", type=float, default=10.0)
    ap.add_argument("--once", action="store_true")
    args = ap.parse_args()

    async def loop():
        while True:
            ent = await scan_once(timeout_s=min(8.0, args.interval))
            if ent:
                update_hosts(ent)
                print(f"[ble] found {len(ent)} endpoints")
            if args.once: break
            await asyncio.sleep(args.interval)

    try:
        asyncio.run(loop())
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()
