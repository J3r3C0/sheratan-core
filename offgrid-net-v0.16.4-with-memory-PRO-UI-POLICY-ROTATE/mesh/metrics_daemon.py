#!/usr/bin/env python3
import time, json, argparse
from pathlib import Path
from binding import save_metrics

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--interval", type=float, default=5.0)
    ap.add_argument("--out", default="./mesh/last_metrics.json")
    args = ap.parse_args()
    Path(Path(args.out).parent).mkdir(parents=True, exist_ok=True)
    print(f"[mesh-daemon] writing metrics to {args.out} every {args.interval}s")
    try:
        while True:
            m = save_metrics(args.out)
            time.sleep(args.interval)
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()
