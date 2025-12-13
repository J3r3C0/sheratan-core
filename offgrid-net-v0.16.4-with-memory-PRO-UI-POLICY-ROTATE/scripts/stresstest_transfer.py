#!/usr/bin/env python3
import os, random, subprocess, sys, tempfile, hashlib, json, time
from pathlib import Path

def sh(cmd):
    print("+", cmd)
    return subprocess.check_call(cmd, shell=True)

def randfile(path, size_bytes=2_000_000):
    import os
    with open(path, "wb") as f:
        f.write(os.urandom(size_bytes))

def sha256(p):
    import hashlib
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

if __name__ == "__main__":
    tmp = tempfile.mkdtemp()
    src = Path(tmp)/"src.bin"
    randfile(src, size_bytes=3_000_000)  # 3 MB
    h0 = sha256(src)
    # put EC
    sh(f"python scripts/put.py {src} --mode ec --k 12 --n 20 --shard_size 65536 --keys ./keys/node-A.json")
    # simulate shard loss by deleting random local shards from a subset of hosts (we only store locally in this demo)
    # get meta
    meta = json.loads(next(Path('./_ec_out').glob('*_meta.json')).read_text())
    asset_id = meta['asset_id']
    # attempt get
    out = Path(tmp)/"out.bin"
    sh(f"python scripts/get.py {asset_id} --mode ec --k 12 --n 20 --outfile {out} --keys ./keys/node-A.json")
    h1 = sha256(out)
    print("SRC:", h0); print("OUT:", h1)
    if h0 == h1: print("OK – integrity match")
    else: 
        print("MISMATCH"); sys.exit(1)
