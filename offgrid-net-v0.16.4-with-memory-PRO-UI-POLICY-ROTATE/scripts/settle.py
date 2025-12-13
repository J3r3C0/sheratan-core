#!/usr/bin/env python3
import json, glob, pathlib, sys
from ledger.local_dag import LocalDAG
batch_files = sorted(glob.glob('_receipts/batch_*.json'))
if not batch_files:
    print('Keine Batches gefunden – erst /receipts/export aufrufen.')
    sys.exit(0)
batch = json.loads(pathlib.Path(batch_files[-1]).read_text())
blk = LocalDAG('./_ledger').append_block(batch)
print(json.dumps(blk, indent=2))
