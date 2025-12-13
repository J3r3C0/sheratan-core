#!/usr/bin/env python3
import json, time, base64, hashlib, os
from pathlib import Path
from nacl import signing

TX_POOL = Path("./_txpool.json")      # pending txs (with witnesses)
TX_LOG  = Path("./_txlog.json")       # finalized txs
BAL     = Path("./_balances.json")    # balances snapshot

def _read_json(p: Path, default):
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return default

def _write_json(p: Path, obj):
    p.write_text(json.dumps(obj, indent=2), encoding="utf-8")

def tx_hash(tx_body: dict) -> str:
    # canonical hash excluding signatures & witnesses
    body = {k:v for k,v in tx_body.items() if k not in ("sign","witnesses")}
    raw = json.dumps(body, sort_keys=True, separators=(",",":")).encode()
    return hashlib.sha256(raw).hexdigest()

def sign_tx(tx_body: dict, signing_key_b64: str) -> dict:
    sk = signing.SigningKey(base64.b64decode(signing_key_b64))
    vk_b64 = base64.b64encode(bytes(sk.verify_key)).decode()
    h = tx_hash(tx_body)
    sig = sk.sign(h.encode()).signature
    return {"verify_key": vk_b64, "signature": base64.b64encode(sig).decode(), "hash": h}

def verify_sig(h: str, verify_key_b64: str, sig_b64: str) -> bool:
    try:
        vk = signing.VerifyKey(base64.b64decode(verify_key_b64))
        vk.verify(h.encode(), base64.b64decode(sig_b64))
        return True
    except Exception:
        return False

def create_tx(src: str, dst: str, amount: float, fee: float, nonce: int, meta: dict=None) -> dict:
    tx = {
        "version": "0.11",
        "ts": int(time.time()*1000),
        "src": src,
        "dst": dst,
        "amount": float(amount),
        "fee": float(fee),
        "nonce": int(nonce),
        "meta": meta or {},
    }
    tx["id"] = tx_hash(tx)
    tx["witnesses"] = []
    return tx

def add_witness(tx: dict, witness_sig: dict) -> dict:
    # expects keys: verify_key, signature, hash
    if witness_sig["hash"] != tx["id"]:
        raise ValueError("hash mismatch")
    # de-dup by verify_key
    keys = {w["verify_key"] for w in tx.get("witnesses",[])}
    if witness_sig["verify_key"] in keys:
        return tx
    tx.setdefault("witnesses", []).append(witness_sig)
    return tx

def pool_add_or_update(tx: dict):
    pool = _read_json(TX_POOL, [])
    # replace by id
    found = False
    for i, t in enumerate(pool):
        if t["id"] == tx["id"]:
            pool[i] = tx
            found = True
            break
    if not found:
        pool.append(tx)
    _write_json(TX_POOL, pool)

def pool_get(id_: str):
    for t in _read_json(TX_POOL, []):
        if t["id"] == id_:
            return t
    return None

def pool_list():
    return _read_json(TX_POOL, [])

def pool_remove(id_: str):
    pool = [t for t in _read_json(TX_POOL, []) if t["id"] != id_]
    _write_json(TX_POOL, pool)

def _load_bal():
    return _read_json(BAL, {"system": 0.0})

def _save_bal(bal):
    _write_json(BAL, bal)

def apply_tx_to_balances(tx: dict):
    bal = _load_bal()
    src = tx["src"]; dst = tx["dst"]; amount = float(tx["amount"]); fee = float(tx["fee"])
    # mint account can go negative (infinite), otherwise require sufficient funds
    if src != "mint":
        if bal.get(src, 0.0) < amount + fee:
            raise ValueError("insufficient funds for src")
        bal[src] = bal.get(src, 0.0) - amount - fee
    # credit dst and system (fee)
    bal[dst] = bal.get(dst, 0.0) + amount
    bal["system"] = bal.get("system", 0.0) + fee
    _save_bal(bal)
    return bal

def finalize_tx(id_: str, quorum_m: int = 2) -> dict:
    # move from pool to log if quorum reached
    pool = pool_list()
    tx = None
    for t in pool:
        if t["id"] == id_:
            tx = t; break
    if tx is None:
        raise ValueError("tx not in pool")
    # verify distinct witness signatures
    good = 0
    seen = set()
    for w in tx.get("witnesses", []):
        if w["verify_key"] in seen: continue
        if verify_sig(tx["id"], w["verify_key"], w["signature"]):
            good += 1
            seen.add(w["verify_key"])
    if good < quorum_m:
        return {"ok": False, "reason": f"quorum {good}/{quorum_m}"}
    # apply balances (idempotent guard: check log)
    log = _read_json(TX_LOG, [])
    if any(l["id"] == tx["id"] for l in log):
        return {"ok": True, "already": True}
    apply_tx_to_balances(tx)
    log.append(tx)
    _write_json(TX_LOG, log)
    pool_remove(tx["id"])
    return {"ok": True, "finalized": tx["id"]}
