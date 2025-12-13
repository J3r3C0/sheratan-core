#!/usr/bin/env python3
import subprocess, time, os, sys, json, hashlib, tempfile, shutil, signal
from pathlib import Path

PY = sys.executable

def sh(cmd, **kwargs):
    print("+", cmd)
    return subprocess.Popen(cmd, shell=True, **kwargs)

def wait_for_hosts(expected_endpoints, timeout=15):
    disc = Path("./discovery/mesh_hosts.json")
    t0 = time.time()
    while time.time() - t0 < timeout:
        if disc.exists():
            try:
                obj = json.loads(disc.read_text(encoding="utf-8"))
                if all(ep in obj for ep in expected_endpoints):
                    return True
            except Exception:
                pass
        time.sleep(0.5)
    return False

def sha256(p):
    import hashlib
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main():
    # 0) Ensure keys
    sh(f"{PY} keys/key_utils.py --node_id node-A").wait()
    sh(f"{PY} keys/key_utils.py --node_id node-B").wait()

    procs = []

    try:
        # 1) Start 2 hosts
        procs.append(sh(f"{PY} host_daemon/daemon_stub.py --port 8081 --node_id node-A", stdout=subprocess.PIPE, stderr=subprocess.STDOUT))
        procs.append(sh(f"{PY} host_daemon/daemon_stub.py --port 8082 --node_id node-B", stdout=subprocess.PIPE, stderr=subprocess.STDOUT))
        time.sleep(1.5)

        # 2) Start 2 UDP radio gateways with signed beacons
        procs.append(sh(f"{PY} radio/radio_gateway.py --node_id node-A --endpoint http://127.0.0.1:8081 --transport udp --interval 2 --keys ./keys/node-A.json", stdout=subprocess.PIPE, stderr=subprocess.STDOUT))
        procs.append(sh(f"{PY} radio/radio_gateway.py --node_id node-B --endpoint http://127.0.0.1:8082 --transport udp --interval 3 --keys ./keys/node-B.json", stdout=subprocess.PIPE, stderr=subprocess.STDOUT))

        # 3) Start broker
        procs.append(sh(f"{PY} broker/broker_stub.py --jobs 2", stdout=subprocess.PIPE, stderr=subprocess.STDOUT))

        # 4) Wait for discovery
        ok = wait_for_hosts(["http://127.0.0.1:8081", "http://127.0.0.1:8082"], timeout=20)
        if not ok:
            print("! Discovery did not see both endpoints within timeout")
            return 2
        print("✓ Discovery OK")

        # 5) Create a random test file (2 MB)
        tmpdir = Path(tempfile.mkdtemp())
        src = tmpdir / "src.bin"
        src.write_bytes(os.urandom(2_000_000))
        h0 = sha256(src)

        # 6) PUT EC (smaller n for speed)
        put_cmd = f"{PY} scripts/put.py {src} --mode ec --k 6 --n 10 --shard_size 32768 --keys ./keys/node-A.json"
        if sh(put_cmd).wait() != 0:
            print("! put failed"); return 3

        # 7) Find asset_id from meta
        meta_files = sorted(Path('./_ec_out').glob('*_meta.json'))
        if not meta_files:
            print("! no meta found after put"); return 4
        meta = json.loads(meta_files[-1].read_text(encoding="utf-8"))
        asset_id = meta["asset_id"]

        # 8) GET EC
        out = tmpdir / "out.bin"
        get_cmd = f"{PY} scripts/get.py {asset_id} --mode ec --k 6 --n 10 --outfile {out} --keys ./keys/node-A.json"
        if sh(get_cmd).wait() != 0:
            print("! get failed"); return 5

        h1 = sha256(out)
        print("SRC:", h0); print("OUT:", h1)
        if h0 != h1:
            print("! Integrity mismatch"); return 6

        print("✓ Smoke test PASSED")
        return 0

    finally:
        # Shutdown all subprocesses
        for p in procs:
            try:
                p.terminate()
            except Exception:
                pass
        time.sleep(1.0)
        for p in procs:
            try:
                p.kill()
            except Exception:
                pass

if __name__ == "__main__":
    sys.exit(main())
