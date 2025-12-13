"""memory/store.py
Minimaler, SQLite-basierter Event-Store + chunk-storage (zlib-komprimiert).
Deutsch kommentare erklären Absicht und einfache Integration.
"""
import os, sqlite3, hashlib, zlib, json, time
from typing import Optional

DB_PATH = os.environ.get('OFFGRID_MEMORY_DB', '/mnt/data/offgrid_memory.db')
CHUNK_DIR = os.environ.get('OFFGRID_CHUNK_DIR', '/mnt/data/offgrid_chunks')
CHUNK_THRESHOLD = int(os.environ.get('OFFGRID_CHUNK_THRESHOLD', '1024'))  # bytes

def _sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

class MemoryStore:
    """Ein sehr kleines, leicht integrierbares Speicher-Backend.
    - SQLite DB für Event-Index
    - chunks/ Verzeichnis für große payloads (zlib-komprimiert)
    """
    def __init__(self, path=DB_PATH, chunk_dir=CHUNK_DIR):
        os.makedirs(chunk_dir, exist_ok=True)
        self.chunk_dir = chunk_dir
        self.conn = sqlite3.connect(path, timeout=30, check_same_thread=False)
        self._init_db()

    def _init_db(self):
        c = self.conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS events (
                eid TEXT PRIMARY KEY,
                ts INTEGER,
                etype INTEGER,
                meta BLOB,
                pref TEXT,
                score REAL
            )
        ''')
        c.execute('CREATE INDEX IF NOT EXISTS idx_ts ON events(ts)')
        self.conn.commit()

    def store_chunk(self, b: bytes) -> str:
        """Chunk speichern (zlib-komprimiert) und SHA256-Hash zurückgeben."""
        h = _sha256(b)
        path = os.path.join(self.chunk_dir, h)
        if not os.path.exists(path):
            comp = zlib.compress(b)
            with open(path, 'wb') as f:
                f.write(comp)
        return h

    def get_chunk(self, h: str) -> Optional[bytes]:
        path = os.path.join(self.chunk_dir, h)
        if not os.path.exists(path):
            return None
        with open(path, 'rb') as f:
            comp = f.read()
        return zlib.decompress(comp)

    def ingest_event(self, payload: bytes, etype: int=0, meta: dict=None, score: float=1.0) -> str:
        """Ereignis aufnehmen: payload wird ggf. als Chunk gespeichert.
        Rückgabe: eid (hex string)
        """
        if meta is None:
            meta = {}
        ts = int(time.time()*1000)
        eid = _sha256(payload)
        pref = None
        # chunken wenn groß
        if len(payload) > CHUNK_THRESHOLD:
            pref = self.store_chunk(payload)
        # meta kompakt serialisieren
        meta_b = json.dumps(meta, separators=(',',':')).encode('utf-8')
        cur = self.conn.cursor()
        try:
            cur.execute('INSERT INTO events(eid, ts, etype, meta, pref, score) VALUES (?,?,?,?,?,?)',
                        (eid, ts, etype, meta_b, pref, float(score)))
            self.conn.commit()
        except sqlite3.IntegrityError:
            # bereits vorhanden -> update timestamp/score evtl.
            cur.execute('UPDATE events SET ts=?, score=? WHERE eid=?', (ts, float(score), eid))
            self.conn.commit()
        return eid

    def get_event(self, eid: str):
        cur = self.conn.cursor()
        r = cur.execute('SELECT eid, ts, etype, meta, pref, score FROM events WHERE eid=?', (eid,)).fetchone()
        if not r:
            return None
        eid, ts, etype, meta_b, pref, score = r
        meta = json.loads(meta_b.decode('utf-8')) if meta_b else {}
        return {'eid':eid, 'ts':ts, 'etype':etype, 'meta':meta, 'pref':pref, 'score':score}

    def query_events(self, since_ts:int=0, limit:int=100):
        cur = self.conn.cursor()
        rows = cur.execute('SELECT eid, ts, etype, meta, pref, score FROM events WHERE ts>=? ORDER BY ts ASC LIMIT ?',
                           (since_ts, limit)).fetchall()
        out = []
        for r in rows:
            eid, ts, etype, meta_b, pref, score = r
            meta = json.loads(meta_b.decode('utf-8')) if meta_b else {}
            out.append({'eid':eid, 'ts':ts, 'etype':etype, 'meta':meta, 'pref':pref, 'score':score})
        return out
