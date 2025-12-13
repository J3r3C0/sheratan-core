#!/usr/bin/env python3
import sys, json
from economy.wallet import transfer
from pathlib import Path

def parse_cfg_fee():
    # tiny extract from config
    p = Path("./config/config.example.yaml")
    if not p.exists(): return 0.001
    tx_min = 0.001; tx_max = 0.01
    for line in p.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if s.startswith("tx_fee_min:"):
            try: tx_min = float(s.split(":")[1].strip())
            except: pass
        if s.startswith("tx_fee_max:"):
            try: tx_max = float(s.split(":")[1].strip())
            except: pass
    # choose mid
    return (tx_min + tx_max)/2.0

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python scripts/transfer.py <from> <to> <amount>")
        sys.exit(1)
    rate = parse_cfg_fee()
    res = transfer(sys.argv[1], sys.argv[2], float(sys.argv[3]), tx_fee_rate=rate)
    print(json.dumps(res, indent=2))
