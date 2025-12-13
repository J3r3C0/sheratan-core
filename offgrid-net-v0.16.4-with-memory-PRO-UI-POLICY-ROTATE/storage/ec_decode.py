#!/usr/bin/env python3
import argparse, json, glob
from pathlib import Path
from ec_rs import decode

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--indir", default="./_ec_out", help="Directory with shards + meta.json")
    ap.add_argument("--k", type=int, default=None, help="Override k if needed")
    ap.add_argument("--outfile", default="./_ec_restore.bin")
    args = ap.parse_args()

    inp = Path(args.indir)
    meta = json.loads((inp / "meta.json").read_text(encoding="utf-8"))
    if args.k is not None:
        meta["k"] = args.k
    k = meta["k"]
    # collect any k shards
    shard_files = sorted(inp.glob("shard_*.bin"))
    assert len(shard_files) >= k, f"need >= {k} shards; found {len(shard_files)}"
    shard_payloads, shard_indices = [], []
    for f in shard_files[:k]:
        shard_payloads.append(f.read_bytes())
        idx = int(f.stem.split("_")[1])
        shard_indices.append(idx)
    data = decode(shard_payloads, shard_indices, meta)
    Path(args.outfile).write_bytes(data)
    print(f"[ec-decode] restored to {args.outfile} ({len(data)} bytes)")

if __name__ == "__main__":
    main()
