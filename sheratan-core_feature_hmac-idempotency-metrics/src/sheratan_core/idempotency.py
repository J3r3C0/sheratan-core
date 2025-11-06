from __future__ import annotations
import os, sqlite3, threading, time
from typing import Optional

_BACKEND = os.getenv("SHERATAN_IDEMP_BACKEND", "mem").lower()
_SQLITE_PATH = os.getenv("SHERATAN_IDEMP_SQLITE_PATH", "./_runtime/idempotency.sqlite")
_TTL_SEC = 3600

class MemStore:
    def __init__(self, ttl=_TTL_SEC, max_size=5000):
        self.ttl = ttl
        self.max = max_size
        self.data = {}
        self.lock = threading.Lock()

    def put_once(self, key: str) -> bool:
        now = time.time()
        with self.lock:
            # purge
            for k, (ts, _) in list(self.data.items()):
                if now - ts > self.ttl:
                    self.data.pop(k, None)
            if key in self.data:
                return False
            if len(self.data) >= self.max:
                # drop oldest
                oldest = sorted(self.data.items(), key=lambda kv: kv[1][0])[0][0]
                self.data.pop(oldest, None)
            self.data[key] = (now, True)
            return True

class SqliteStore:
    def __init__(self, path=_SQLITE_PATH, ttl=_TTL_SEC):
        self.path = path
        self.ttl = ttl
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with sqlite3.connect(self.path) as db:
            db.execute("CREATE TABLE IF NOT EXISTS idempotency (k TEXT PRIMARY KEY, ts INTEGER)")
            db.commit()

    def put_once(self, key: str) -> bool:
        now = int(time.time())
        with sqlite3.connect(self.path) as db:
            db.execute("DELETE FROM idempotency WHERE ts < ?", (now - self.ttl,))
            try:
                db.execute("INSERT INTO idempotency(k, ts) VALUES(?,?)", (key, now))
                db.commit()
                return True
            except sqlite3.IntegrityError:
                return False

def get_store():
    if _BACKEND == "sqlite":
        return SqliteStore()
    return MemStore()
