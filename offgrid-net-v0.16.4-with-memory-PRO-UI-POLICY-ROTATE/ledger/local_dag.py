import json, hashlib, time
from pathlib import Path

class LocalDAG:
    def __init__(self, base_dir="./_ledger"):
        self.base = Path(base_dir)
        self.base.mkdir(parents=True, exist_ok=True)

    def append_block(self, receipts_batch: dict):
        # simple block with parent hash reference
        parent = self._last_hash()
        block = {
            "ts": int(time.time()*1000),
            "parent": parent,
            "merkle_root": receipts_batch.get("root",""),
            "count": receipts_batch.get("count",0)
        }
        raw = json.dumps(block, sort_keys=True).encode()
        h = hashlib.sha256(raw).hexdigest()
        block["hash"] = h
        (self.base / f"{block['ts']}_{h}.json").write_text(json.dumps(block, indent=2), encoding="utf-8")
        return block

    def _last_hash(self):
        files = sorted(self.base.glob("*.json"))
        if not files: return None
        import json
        return json.loads(files[-1].read_text(encoding="utf-8")).get("hash")
