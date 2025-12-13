#!/usr/bin/env python3
import argparse, json
from consensus.quorum import set_policy, get_policy, set_kind_policy

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kind", choices=["upload","job","token"], help="apply to specific kind (for decay/max_age)")
    ap.add_argument("--weight_default", type=float)
    ap.add_argument("--decay_half_life_s", type=int)
    ap.add_argument("--max_age_s", type=int)
    ap.add_argument("--set_weight", action="append", help="node_id=weight (can repeat; applies to global weights)")
    ap.add_argument("--show", action="store_true")
    args = ap.parse_args()

    if args.show:
        print(json.dumps(get_policy(args.kind) if args.kind else get_policy(), indent=2)); return

    weights = {}
    if args.set_weight and not args.kind:
        for item in args.set_weight:
            if "=" in item:
                k,v = item.split("=",1)
                try: weights[k]=float(v)
                except: pass

    if args.kind:
        pol = set_kind_policy(args.kind, args.decay_half_life_s, args.max_age_s)
        print(json.dumps(get_policy(args.kind), indent=2))
    else:
        pol = set_policy(args.weight_default, args.decay_half_life_s, args.max_age_s, weights if weights else None)
        print(json.dumps(pol, indent=2))

if __name__ == "__main__":
    main()
