#!/usr/bin/env python3
import argparse, json, base64, os, uuid
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError
from storage.ec_rs import encode as ec_encode
from consensus.quorum import create_or_get, add_ack
from transfer.common import retry_backoff, log
from storage.encrypt_real import derive_shared_key, encrypt_xchacha
from nacl import public
import hashlib

def load_peer_xpk(endpoint: str) -> public.PublicKey:
    obj = json.loads(urlopen(f"{endpoint}/pubkeys", timeout=3).read().decode())
    xpk_b64 = obj["x25519_public_key"]
    return public.PublicKey(base64.b64decode(xpk_b64))

def load_local_keys(keys_path: str):
    k = json.loads(Path(keys_path).read_text(encoding="utf-8"))
    return public.PrivateKey(base64.b64decode(k["x25519"]["private_key"]))

def store_shard(endpoint: str, asset_id: str, index: int, blob: bytes) -> bool:
    payload = {"asset_id": asset_id, "index": index, "data_b64": base64.b64encode(blob).decode()}
    req = Request(f"{endpoint}/store", data=json.dumps(payload).encode(), headers={"Content-Type":"application/json"})
    try:
        urlopen(req, timeout=5).read()
        return True
    except URLError as e:
        raise e

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--mode", choices=["ec","rep"], default="ec", help="ec=12/20, rep=r=5")
    ap.add_argument("--r", type=int, default=5)
    ap.add_argument("--k", type=int, default=12)
    ap.add_argument("--n", type=int, default=20)
    ap.add_argument("--shard_size", type=int, default=1024*64)
    ap.add_argument("--keys", default="./keys/node-A.json")
    ap.add_argument("--hostlist", nargs="+", default=None, help="Override endpoints list")
    ap.add_argument("--asset_id", default=None)
    args = ap.parse_args()

    asset_id = args.asset_id or ("asset-" + hashlib.sha256(Path(args.file).read_bytes()).hexdigest()[:16])
    data = Path(args.file).read_bytes()

    # choose endpoints
    if args.hostlist is None:
        # try discovery file
        import json as _J
        from pathlib import Path as _P
        f = _P("./discovery/mesh_hosts.json")
        if f.exists():
            hosts_map = _J.loads(f.read_text(encoding="utf-8"))
            endpoints = list(hosts_map.keys())
        else:
            endpoints = ["http://127.0.0.1:8081"]
    else:
        endpoints = args.hostlist
    assert endpoints, "keine Hosts gefunden"

    # prepare encryption keys (local xsk -> peer xpk per-host)
    xsk = load_local_keys(args.keys)
    peer_keys = {}
    for ep in endpoints:
        try:
            peer_keys[ep] = load_peer_xpk(ep)
        except Exception:
            pass
    assert peer_keys, "keine peer keys gefunden (/pubkeys)"

    # encode
    shards = []
    meta = {"mode": args.mode}
    if args.mode == "ec":
        shards, m = ec_encode(data, k=args.k, n=args.n, shard_size=args.shard_size)
        meta.update(m)
    else:
        # replication: no EC; split into r chunks of equal size? we replicate the whole ciphertext r times
        shards = [data]  # single shard; will be replicated
        meta.update({"k":1,"n":args.r,"shard_size":len(data),"orig_len":len(data),"pad":0,"systematic":True})

    # dispatch
    plan = []
    if args.mode == "ec":
        assert len(shards) == args.n
        if len(endpoints) < args.n:
            # round-robin assign
            for i in range(len(shards)):
                plan.append(endpoints[i % len(endpoints)])
        else:
            plan = endpoints[:args.n]
    else:
        # replication: send same shard to r endpoints
        plan = (endpoints * args.r)[:args.r]


    # windowed uploader with resume file
    WINDOW = 8

    # resume manifest path
    manifest_dir = Path("./_ec_out"); manifest_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = manifest_dir / f"{asset_id}_upload.json"
    progress = {"asset_id": asset_id, "done": []}
    if manifest_path.exists():
        try:
            progress = json.loads(manifest_path.read_text(encoding="utf-8"))
        except Exception:
            pass

    # Task queue
    import threading, queue
    q = queue.Queue()
    failed = []
    total = len(plan)
    for i, ep in enumerate(plan):
        if i in set(progress.get("done", [])):  # already uploaded
            continue
        q.put((i, ep))

    lock = threading.Lock()

    def worker():
        while True:
            try:
                i, ep = q.get_nowait()
            except queue.Empty:
                return
            blob = shards[i] if args.mode == "ec" else shards[0]
            aead_key = derive_shared_key(xsk, peer_keys[ep])
            ct = encrypt_xchacha(blob, aead_key, aad=f"{asset_id}:{i}".encode())
            packed = json.dumps(ct).encode()
            def attempt():
                return store_shard(ep, asset_id, i, packed)
            try:
                retry_backoff(attempt, max_tries=5, base=0.4, jitter=0.3, on_error=lambda e,t: log(f"[put] retry shard {i} @ {ep}: {e} (try {t+1})"))
                with lock:
                    progress["done"].append(i)
                    manifest_path.write_text(json.dumps(progress, indent=2), encoding="utf-8")
                    log(f"[put] stored shard {i}/{total-1} -> {ep}")
                    try:
                        add_ack(asset_id, "upload", ep)
                    except Exception:
                        pass
            except Exception as e:
                with lock:
                    failed.append((i, ep, str(e)))
                log(f"[put] FAIL shard {i} @ {ep}: {e}")
            finally:
                q.task_done()

    # spawn workers
    workers = [threading.Thread(target=worker, daemon=True) for _ in range(WINDOW)]
    for w in workers: w.start()
    for w in workers: w.join()
    ok_ct = len(progress["done"])
    


    # write meta for client
    out_meta = {"asset_id": asset_id, "meta": meta, "endpoints": plan}
    Path(f"./_ec_out/{asset_id}_meta.json").parent.mkdir(parents=True, exist_ok=True)
    Path(f"./_ec_out/{asset_id}_meta.json").write_text(json.dumps(out_meta, indent=2), encoding="utf-8")
    print(f"[put] done asset_id={asset_id}, shards_ok={ok_ct}/{len(plan)}")

if __name__ == "__main__":
    main()
