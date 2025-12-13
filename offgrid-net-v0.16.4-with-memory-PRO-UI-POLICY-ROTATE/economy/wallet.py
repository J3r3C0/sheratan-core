#!/usr/bin/env python3
import json
from pathlib import Path

BAL_FILE = Path("./_balances.json")

def _load():
    if BAL_FILE.exists():
        return json.loads(BAL_FILE.read_text(encoding="utf-8"))
    return {"system": 0.0}

def _save(obj):
    BAL_FILE.write_text(json.dumps(obj, indent=2), encoding="utf-8")

def balance(acct: str) -> float:
    bal = _load()
    return float(bal.get(acct, 0.0))

def credit(acct: str, amount: float):
    bal = _load()
    bal[acct] = float(bal.get(acct, 0.0)) + float(amount)
    _save(bal)

def debit(acct: str, amount: float) -> bool:
    bal = _load()
    cur = float(bal.get(acct, 0.0))
    if cur < amount:
        return False
    bal[acct] = cur - float(amount)
    _save(bal)
    return True

def transfer(src: str, dst: str, amount: float, tx_fee_rate: float = 0.001):
    amount = float(amount)
    fee = amount * float(tx_fee_rate)
    net = amount - fee
    if not debit(src, amount):
        raise ValueError("Insufficient funds")
    credit(dst, net)
    credit("system", fee)
    return {"src": src, "dst": dst, "amount": amount, "fee": fee, "net_received": net}
