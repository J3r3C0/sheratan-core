#!/usr/bin/env python3
import argparse, json
from pathlib import Path
from ec_rs import encode

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file", help="Input file to encode")
    ap.add_argument("--k", type=int, default=12)
    ap.add_argument("--n", type=int, default=20)
    ap.add_argument("--shard_size", type=int, default=1024*64)
    ap.add_argument("--outdir", default="./_ec_out")
    args = ap.parse_args()

    p = Path(args.file)
    data = p.read_bytes()
    shards, meta = encode(data, k=args.k, n=args.n, shard_size=args.shard_size)

    out = Path(args.outdir); out.mkdir(parents=True, exist_ok=True)
    # write meta
    (out / "meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    # write shard files with indices
    for i, s in enumerate(shards):
        (out / f"shard_{i:02d}.bin").write_bytes(s)
    print(f"[ec-encode] wrote {len(shards)} shards to {out} (k={args.k}, n={args.n})")

if __name__ == "__main__":
    main()
