#!/usr/bin/env python3
import argparse, json, base64, sys
from pathlib import Path
from urllib.request import urlopen
from urllib.error import URLError
from storage.ec_rs import decode as ec_decode
from transfer.common import retry_backoff, log
from storage.encrypt_real import derive_shared_key, decrypt_xchacha
from nacl import public

def fetch_shard(endpoint: str, asset_id: str, index: int) -> bytes:
    def go():
        obj = json.loads(urlopen(f"{endpoint}/fetch?asset_id={asset_id}&index={index}", timeout=5).read().decode())
        return base64.b64decode(obj["data_b64"].encode())
    return retry_backoff(go, max_tries=5, base=0.3, jitter=0.2, on_error=lambda e,t: log(f"[get] retry shard {index} @ {endpoint}: {e} (try {t+1})"))

def load_local_keys(keys_path: str):
    k = json.loads(Path(keys_path).read_text(encoding="utf-8"))
    return public.PrivateKey(base64.b64decode(k["x25519"]["private_key"]))

def load_peer_xpk(endpoint: str) -> public.PublicKey:
    obj = json.loads(urlopen(f"{endpoint}/pubkeys", timeout=3).read().decode())
    return public.PublicKey(base64.b64decode(obj["x25519_public_key"]))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("asset_id")
    ap.add_argument("--mode", choices=["ec","rep"], default="ec")
    ap.add_argument("--k", type=int, default=12)
    ap.add_argument("--n", type=int, default=20)
    ap.add_argument("--r", type=int, default=5)
    ap.add_argument("--keys", default="./keys/node-A.json")
    ap.add_argument("--outfile", default="./_downloads/output.bin")
    ap.add_argument("--hostlist", nargs="+", default=None)
    args = ap.parse_args()

    # endpoints from meta if available
    meta_path = Path(f"./_ec_out/{args.asset_id}_meta.json")
    if meta_path.exists():
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        endpoints = meta.get("endpoints", [])
        m = meta.get("meta", {})
        args.k = m.get("k", args.k); args.n = m.get("n", args.n)
        args.mode = meta.get("meta", {}).get("mode", args.mode)
    else:
        if args.hostlist is None:
            # try discovery
            f = Path("./discovery/mesh_hosts.json")
            if f.exists():
                endpoints = list(json.loads(f.read_text(encoding="utf-8")).keys())
            else:
                endpoints = ["http://127.0.0.1:8081"]
        else:
            endpoints = args.hostlist

    xsk = load_local_keys(args.keys)

    # Parallel window
    WINDOW = 8
    import threading, queue
    q = queue.Queue()
    for i, ep in enumerate(endpoints):
        q.put((i, ep))

    shards_payloads = []
    shard_indices = []
    lock = threading.Lock()

    def worker():
        nonlocal shards_payloads, shard_indices
        while True:
            try:
                i, ep = q.get_nowait()
            except queue.Empty:
                return
            try:
                raw = fetch_shard(ep, args.asset_id, i)
                if raw:
                    ct = json.loads(raw.decode())
                    xpk = load_peer_xpk(ep)
                    aead_key = derive_shared_key(xsk, xpk)
                    pt = decrypt_xchacha(ct["nonce"], ct["ciphertext"], aead_key, aad=f"{args.asset_id}:{i}".encode())
                    with lock:
                        shards_payloads.append(pt)
                        shard_indices.append(i)
                        log(f"[get] got shard {i} from {ep} ({len(pt)} bytes)")
                else:
                    log(f"[get] empty shard {i} from {ep}")
            except Exception as e:
                log(f"[get] fail shard {i} @ {ep}: {e}")
            finally:
                q.task_done()

    workers = [threading.Thread(target=worker, daemon=True) for _ in range(WINDOW)]
    for w in workers: w.start()

    # Wait until enough shards received
    if args.mode == "ec":
        need = args.k
    else:
        need = 1
    while True:
        with lock:
            if len(shards_payloads) >= need:
                break
        if all(not t.is_alive() for t in workers):
            break
        time.sleep(0.05)
    for w in workers: w.join()
    
    if args.mode == "ec":
        assert len(shards_payloads) >= args.k, f"need >= {args.k} shards; got {len(shards_payloads)}"
        data = ec_decode(shards_payloads[:args.k], shard_indices[:args.k], {"k":args.k,"n":args.n,"shard_size":len(shards_payloads[0]),"orig_len":None,"parity_matrix":json.loads(Path('./_ec_out/%s_meta.json'%args.asset_id).read_text())['meta']['parity_matrix'] if meta_path.exists() else None})
        # If parity_matrix missing (no meta), we can't decode; keeping meta path as requirement for now.
    else:
        assert len(shards_payloads)>=1, "need at least 1 replica"
        data = shards_payloads[0]

    Path(args.outfile).parent.mkdir(parents=True, exist_ok=True)
    Path(args.outfile).write_bytes(data)
    print(f"[get] wrote {args.outfile} ({len(data)} bytes)")

if __name__ == "__main__":
    main()
