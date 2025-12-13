#!/usr/bin/env python3
import json, time
from pathlib import Path
from consensus.quorum import list_records, get_policy

STATE = Path("./_failover_state.json")
REQQ  = Path("./_requeue_jobs.json")
DISC  = Path("./discovery/mesh_hosts.json")

def _read(p, d):
    if p.exists():
        try: return json.loads(p.read_text(encoding="utf-8"))
        except Exception: return d
    return d

def _write(p, o):
    p.write_text(json.dumps(o, indent=2), encoding="utf-8")

def candidates(exclude_ids: set):
    disc = _read(DISC, {})
    # sort by via preference: policy feed already adjusts weights, but we fallback to via order
    prio = {"file": 1.2, "lora": 1.1, "ble":1.05, "udp":1.0}
    arr = []
    for ep, rec in disc.items():
        if ep in exclude_ids: continue
        via = rec.get("via", "udp")
        arr.append((prio.get(via,1.0), ep))
    arr.sort(reverse=True)
    return [ep for _,ep in arr]

def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--kind", choices=["job","upload"], default="job")
    ap.add_argument("--interval", type=float, default=8.0)
    ap.add_argument("--stall_age_s", type=int, default=90)         # minimal age before we consider stall
    ap.add_argument("--min_progress_delta", type=float, default=0.05)  # minimal sum_w growth to consider progress
    ap.add_argument("--cooldown_s", type=int, default=60)          # cooldown per id between reassigns
    ap.add_argument("--max_retries", type=int, default=3)
    ap.add_argument("--suggest_only", action="store_true", help="for uploads: only write alerts, don't enqueue")
    args = ap.parse_args()

    state = _read(STATE, {})  # id -> {last_sum_w, last_ts, retries}
    while True:
        try:
            recs = list_records(args.kind)
        except Exception:
            recs = []

        queue = _read(REQQ, [])
        now = int(time.time())

        for r in recs:
            if r.get("finalized"): 
                state.pop(r["id"], None)
                continue
            age = now - int(r.get("ts", now))
            sumw = float(r.get("_sum_w", 0.0))
            req  = float(r.get("required", 1.0))
            st = state.get(r["id"], {"last_sum_w": 0.0, "last_ts": now, "retries": 0, "last_action": 0})
            progressed = (sumw - st["last_sum_w"]) >= args.min_progress_delta
            cool = (now - st.get("last_action", 0)) >= args.cooldown_s
            should = (age >= args.stall_age_s) and (not progressed) and cool and (st["retries"] < args.max_retries)

            # track
            st["last_sum_w"] = sumw
            st["last_ts"] = now

            if not should:
                state[r["id"]] = st
                continue

            # Build reassign suggestion
            ack_ids = set([a.get("id") for a in r.get("acks", [])]) if isinstance(r.get("acks"), list) else set()
            cands = candidates(ack_ids)
            if args.kind == "job":
                queue.append({"kind": "job", "job_id": r["id"], "targets": cands[:3], "ts": now})
                st["retries"] += 1
                st["last_action"] = now
                state[r["id"]] = st
            elif args.kind == "upload":
                # For uploads we cannot reconstruct shards here; write an alert entry
                queue.append({"kind": "upload_alert", "asset_id": r["id"], "missing_weight": max(0.0, req - sumw), "suggest_targets": cands[:5], "ts": now})
                st["retries"] += 1
                st["last_action"] = now
                state[r["id"]] = st

        _write(STATE, state)
        _write(REQQ, queue)
        time.sleep(args.interval)

if __name__ == "__main__":
    main()
