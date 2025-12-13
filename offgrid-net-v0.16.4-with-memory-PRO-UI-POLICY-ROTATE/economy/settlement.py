#!/usr/bin/env python3
import json, glob, pathlib, urllib.request
from pathlib import Path
from economy.wallet import credit

CONFIG = Path("./config/config.example.yaml").read_text(encoding="utf-8")

def _parse_yaml_like(text: str):
    # minimalistic parser for a few needed keys from our example YAML
    lines = [l.strip() for l in text.splitlines() if l.strip() and not l.strip().startswith("#")]
    out = {}
    cur = out
    stack = [out]
    keys = []
    for l in lines:
        if ":" in l:
            k, v = l.split(":", 1)
            k = k.strip()
            v = v.strip()
            if not v:
                # section start
                d = {}
                cur[k] = d
                stack.append(cur)
                cur = d
                keys.append(k)
            else:
                # scalar
                try:
                    cur[k] = float(v) if v.replace(".","",1).isdigit() else v
                except Exception:
                    cur[k] = v
        else:
            pass
    return out

def _load_config():
    try:
        return _parse_yaml_like(CONFIG)
    except Exception:
        return {}

def _get_prices(host_url: str):
    # pull /announce for prices
    try:
        obj = json.loads(urllib.request.urlopen(f"{host_url}/announce", timeout=2).read().decode())
        return obj.get("prices", {})
    except Exception:
        return {}

def settle_from_batch(batch_path: str, host_map: dict, host_reserve_rate: float = 0.01):
    batch = json.loads(Path(batch_path).read_text(encoding="utf-8"))
    rewards = {}  # host_url -> gross
    for item in batch.get("items", []):
        node_id = item.get("node_id")
        rtype = item.get("resource_type", "compute")
        units = float(item.get("units", 0.0))
        host_url = host_map.get(node_id, None)
        if not host_url:
            continue
        prices = _get_prices(host_url)
        rate = 0.0
        if rtype == "compute":
            rate = float(prices.get("per_mtoken_infer", 0.03))
        elif rtype == "storage":
            rate = float(prices.get("per_gb_hour", 0.02))
        elif rtype == "transfer":
            rate = float(prices.get("per_gb_transfer", 0.005))
        gross = units * rate
        rewards[host_url] = rewards.get(host_url, 0.0) + gross

    # Apply host_reserve -> system; net to host account (account name derived from node_id or host_url)
    settlements = []
    for host_url, gross in rewards.items():
        reserve = gross * host_reserve_rate
        net = gross - reserve
        acct = host_url  # simplistic account id
        credit(acct, net)
        credit("system", reserve)
        settlements.append({"account": acct, "gross": round(gross,6), "reserve": round(reserve,6), "net": round(net,6)})
    return {"items": settlements, "host_reserve_rate": host_reserve_rate}

if __name__ == "__main__":
    import argparse, json
    ap = argparse.ArgumentParser()
    ap.add_argument("--batch", default=None, help="Path to receipts batch JSON (e.g., _receipts/batch_*.json)")
    ap.add_argument("--host_map", default=None, help='JSON mapping of node_id to host_url, e.g. {"did:key:z-demo":"http://127.0.0.1:8081"}')
    ap.add_argument("--host_reserve", type=float, default=0.01)
    args = ap.parse_args()
    assert args.batch and args.host_map, "Provide --batch and --host_map"
    host_map = json.loads(Path(args.host_map).read_text(encoding="utf-8")) if Path(args.host_map).exists() else json.loads(args.host_map)
    res = settle_from_batch(args.batch, host_map, args.host_reserve)
    print(json.dumps(res, indent=2))
