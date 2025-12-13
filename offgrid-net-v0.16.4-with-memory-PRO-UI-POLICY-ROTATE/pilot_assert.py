#!/usr/bin/env python3
import argparse, json, sys, os, time
from pathlib import Path

def jload(p: Path):
    try:
        return json.loads(p.read_text(encoding='utf-8'))
    except FileNotFoundError:
        return None
    except Exception as e:
        return {"__error__": str(e)}

def is_fresh(p: Path, fresh_seconds: int) -> bool:
    try:
        m = p.stat().st_mtime
        return (time.time() - m) <= fresh_seconds
    except FileNotFoundError:
        return False

def parse_csv(s):
    if not s: return []
    return [x.strip() for x in s.split(',') if x.strip()]

def check_reputation(rep_file: Path, expected_nodes, min_rep: float, fresh_seconds: int, errors, warns):
    data = jload(rep_file)
    if data is None:
        warns.append(f"reputation file missing: {rep_file}")
        return None
    if '__error__' in (data or {}):
        errors.append(f"reputation json parse error: {data['__error__']}")
        return None
    if fresh_seconds and not is_fresh(rep_file, fresh_seconds):
        warns.append(f"reputation not fresh (>{fresh_seconds}s): {rep_file}")

    nodes = (data or {}).get('nodes', {})
    if expected_nodes:
        for n in expected_nodes:
            if n not in nodes:
                warns.append(f"expected node '{n}' missing in reputation.json")
    rep_issues = []
    for n, rec in nodes.items():
        r = float(rec.get('rep', 0.5))
        if not (0.0 <= r <= 1.0):
            rep_issues.append(f"{n}: rep out of bounds {r}")
        if min_rep is not None and r < min_rep:
            rep_issues.append(f"{n}: rep below min {r} < {min_rep}")
    if rep_issues:
        errors.extend(["reputation issues:"] + rep_issues)
    return nodes

def check_swim(swim_file: Path, expected_endpoints, strict_swim: bool, fresh_seconds: int, errors, warns):
    data = jload(swim_file)
    if data is None:
        warns.append(f"swim state file missing: {swim_file}")
        return None
    if '__error__' in (data or {}):
        errors.append(f"swim json parse error: {data['__error__']}")
        return None
    if fresh_seconds and not is_fresh(swim_file, fresh_seconds):
        warns.append(f"swim state not fresh (>{fresh_seconds}s): {swim_file}")
    members = (data or {}).get('members', {})
    if expected_endpoints:
        for ep in expected_endpoints:
            if ep not in members:
                warns.append(f"expected endpoint not in swim members: {ep}")
    non_confirm = [ep for ep, m in members.items() if m.get('state') != 'confirm']
    if not non_confirm:
        errors.append("SWIM: all members are 'confirm' (dead).")
    if strict_swim:
        alive = [ep for ep, m in members.items() if m.get('state') == 'alive']
        if not alive:
            errors.append("SWIM(strict): no member is 'alive'.")
    return members

def check_receipts(receipts_dir: Path, min_receipts: int, errors, warns):
    if min_receipts is None or min_receipts <= 0:
        return 0
    if not receipts_dir.exists():
        warns.append(f"receipts dir missing: {receipts_dir}")
        return 0
    files = [p for p in receipts_dir.iterdir() if p.is_file()]
    cnt = len(files)
    if cnt < min_receipts:
        errors.append(f"receipts: found {cnt}, need >= {min_receipts}")
    return cnt

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--rep-file', default='state/reputation.json')
    ap.add_argument('--swim-file', default='discovery/swim_state.json')
    ap.add_argument('--receipts-dir', default='receipts')
    ap.add_argument('--expected-nodes', default='')
    ap.add_argument('--expected-endpoints', default='')
    ap.add_argument('--min-rep', type=float, default=0.45)
    ap.add_argument('--min-receipts', type=int, default=1)
    ap.add_argument('--fresh-seconds', type=int, default=600, help='max age for state files')
    ap.add_argument('--strict-swim', action='store_true')
    args = ap.parse_args()

    rep_file = Path(args.rep_file)
    swim_file = Path(args.swim_file)
    receipts_dir = Path(args.receipts_dir)

    expected_nodes = [x.strip() for x in args.expected_nodes.split(',') if x.strip()]
    expected_endpoints = [x.strip() for x in args.expected_endpoints.split(',') if x.strip()]

    errors, warns = [], []

    check_reputation(rep_file, expected_nodes, args.min_rep, args.fresh_seconds, errors, warns)
    check_swim(swim_file, expected_endpoints, args.strict_swim, args.fresh_seconds, errors, warns)
    receipts_cnt = check_receipts(receipts_dir, args.min_receipts, errors, warns)

    summary = {
        "rep_file": str(rep_file),
        "swim_file": str(swim_file),
        "receipts_dir": str(receipts_dir),
        "expected_nodes": expected_nodes,
        "expected_endpoints": expected_endpoints,
        "receipts_found": receipts_cnt,
        "errors": errors,
        "warnings": warns,
    }
    print(json.dumps(summary, indent=2))

    if errors:
        sys.exit(3)
    if warns:
        sys.exit(2)
    sys.exit(0)

if __name__ == '__main__':
    try:
        main()
    except SystemExit as e:
        raise
    except Exception as e:
        print(json.dumps({"fatal": str(e)}))
        sys.exit(4)
