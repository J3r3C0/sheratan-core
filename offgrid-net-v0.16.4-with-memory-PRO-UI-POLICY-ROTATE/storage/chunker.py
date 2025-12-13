import hashlib
from pathlib import Path

def chunk_file(path, chunk_bytes=1024*1024):
    p = Path(path)
    with p.open("rb") as f:
        i = 0
        while True:
            b = f.read(chunk_bytes)
            if not b: break
            h = hashlib.sha256(b).hexdigest()
            yield {"index": i, "len": len(b), "sha256": h, "data": b}
            i += 1
