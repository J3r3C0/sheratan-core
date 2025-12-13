#!/usr/bin/env python3
import sys, json
from economy.txlog import finalize_tx

if __name__ == "__main__":
    if len(sys.argv)<2:
        print("Usage: python scripts/finalize_tx.py <tx_id> [quorum]"); sys.exit(1)
    tx_id = sys.argv[1]
    quorum = int(sys.argv[2]) if len(sys.argv)>2 else 2
    print(json.dumps(finalize_tx(tx_id, quorum_m=quorum), indent=2))
