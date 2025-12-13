#!/usr/bin/env python3
import argparse, json, time
from pathlib import Path
from fastapi import FastAPI, Request
import uvicorn

def make_app(node_id: str):
    receipts_path = Path(f"./receipts_{node_id}.json")
    if not receipts_path.exists():
        receipts_path.write_text("[]", encoding="utf-8")

    app = FastAPI()

    
@app.on_event("startup")
def _start_policy_worker():
    import threading, json, time
    from pathlib import Path
    try:
        from config.loader import load_config
        cfg = load_config(None)
        auto_accept = bool(cfg.get("policy", {}).get("auto_accept", False))
    except Exception:
        auto_accept = False
    PROV_PATH = Path("discovery/provisional.json")
    PEERS_PATH = Path("discovery/peers.json")
    REVOKE_PATH = Path("keys/revocations.json")

    def _js_load(p):
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def _js_save(p, obj):
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(obj, indent=2), encoding="utf-8")

    def _meets(entry):
        m = entry.get("meta", {}) or {}
        return bool(entry.get("trusted")) and bool(m.get("sig_ok")) and bool(m.get("challenge_ok"))

    def worker():
        if not auto_accept:
            return
        while True:
            try:
                prov = _js_load(PROV_PATH) or {}
                peers = _js_load(PEERS_PATH) or {}
                changed = False
                for k, v in list(prov.items()):
                    if _meets(v):
                        v["accepted_ts"] = int(time.time()*1000)
                        v["accepted_by"] = "policy-auto"
                        peers[k] = v
                        prov.pop(k, None)
                        changed = True
                if changed:
                    _js_save(PROV_PATH, prov)
                    _js_save(PEERS_PATH, peers)
            except Exception:
                pass
            time.sleep(5)

    def _ensure_revocations():
        try:
            REVOKE_PATH.parent.mkdir(parents=True, exist_ok=True)
            if not REVOKE_PATH.exists():
                REVOKE_PATH.write_text("[]", encoding="utf-8")
        except Exception:
            pass

    threading.Thread(target=worker, daemon=True).start()
    _ensure_revocations()

@app.get("/revocations")
def get_revocations():
    from pathlib import Path
    import json
    p = Path("keys/revocations.json")
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        data = []
    return {"revocations": data}
@app.get("/status")
    def status():
        try:
            data = json.loads(receipts_path.read_text(encoding="utf-8"))
        except Exception:
            data = []
        return {"ok": True, "node_id": node_id, "receipts": len(data), "ts": time.time()}

    @app.post("/receipt")
    async def receipt(req: Request):
        payload = await req.json()
        try:
            data = json.loads(receipts_path.read_text(encoding="utf-8"))
        except Exception:
            data = []
        data.append({"ts": time.time(), "payload": payload})
        receipts_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return {"ok": True}
    return app

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, required=True)
    ap.add_argument("--node_id", required=True)
    args = ap.parse_args()
    app = make_app(args.node_id)
    uvicorn.run(app, host="127.0.0.1", port=args.port)

if __name__ == "__main__":
    main()
