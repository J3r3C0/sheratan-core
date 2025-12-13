#!/usr/bin/env python3
import argparse, json
from consensus.quorum import create_or_get, add_ack, is_finalized, get_record, list_records

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kind", choices=["upload","job","token","custom"], required=True)
    ap.add_argument("--id")
    ap.add_argument("--required", type=int, default=1)
    ap.add_argument("--ack_from")
    ap.add_argument("--show", action="store_true")
    ap.add_argument("--list", action="store_true")
    args = ap.parse_args()

    if args.list:
        print(json.dumps(list_records(args.kind if args.kind!='custom' else None), indent=2)); return
    if args.show and args.id:
        print(json.dumps(get_record(args.id, args.kind) or {}, indent=2)); return
    if args.id and args.ack_from:
        print(json.dumps(add_ack(args.id, args.kind, args.ack_from), indent=2)); return
    if args.id:
        print(json.dumps(create_or_get(args.id, args.kind, args.required), indent=2)); return
    ap.print_help()

if __name__ == "__main__":
    main()
