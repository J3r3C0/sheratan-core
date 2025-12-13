# Placeholder: Verzögerungstoleranter Store-and-Forward-Queue (DTN)
# v0: In-Memory Queue + persistente JSON-Liste als Demo.
import json, time
from pathlib import Path

class DTNQueue:
    def __init__(self, path="./_dtn_queue.json"):
        self.path = Path(path)
        if not self.path.exists():
            self.path.write_text("[]", encoding="utf-8")

    def enqueue(self, pkt: dict):
        arr = json.loads(self.path.read_text(encoding="utf-8"))
        pkt["ts"] = int(time.time()*1000)
        arr.append(pkt)
        self.path.write_text(json.dumps(arr, indent=2), encoding="utf-8")

    def drain(self, max_items=10):
        arr = json.loads(self.path.read_text(encoding="utf-8"))
        take = arr[:max_items]
        rest = arr[max_items:]
        self.path.write_text(json.dumps(rest, indent=2), encoding="utf-8")
        return take
