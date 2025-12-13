#!/usr/bin/env python3
import time, json
from pathlib import Path
from consensus.quorum import set_policy

DISC = Path("./discovery/mesh_hosts.json")
REP  = Path("./broker/_rep.json")  # optional reputation map {endpoint: score}

VIA_W = {"udp":1.0, "ble":1.05, "lora":1.1, "file":1.2}

def calc_weights():
    weights = {}
    disc = {}
    try:
        disc = json.loads(DISC.read_text(encoding="utf-8")) if DISC.exists() else {}
    except Exception:
        disc = {}
    for ep, rec in disc.items():
        via = rec.get("via","udp")
        base = VIA_W.get(via, 1.0)
        weights[ep] = base
    # reputation multiplier (if available)
    try:
        rep = json.loads(REP.read_text(encoding="utf-8")) if REP.exists() else {}
        for ep, r in rep.items():
            try:
                r = float(r)
                if ep in weights:
                    weights[ep] *= (1.0 + max(-0.9, min(2.0, r)))  # crude scaling
                else:
                    weights[ep] = 1.0 * (1.0 + max(-0.9, min(2.0, r)))
            except Exception:
                pass
    except Exception:
        pass
    return weights

def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--interval", type=float, default=10.0)
    ap.add_argument("--show", action="store_true")
    args = ap.parse_args()
    while True:
        weights = calc_weights()
        set_policy(weights_patch=weights)  # apply global node weights
        if args.show:
            print("[policy-feed] weights:", json.dumps(weights))
        time.sleep(args.interval)

if __name__ == "__main__":
    main()
