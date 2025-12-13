"""memory/api.py
Einfache HTTP-mäßige API-Schnittstellen (nur als Funktions-Skellet, kein Webserver eingebettet).
Diese Funktionen können in den Host-Daemon gemountet werden.
Deutsch kommentare helfen beim Einbinden.
"""
from .store import MemoryStore
import json

store = MemoryStore()

def ingest_endpoint(payload_bytes: bytes, etype:int=0, meta:dict=None, score:float=1.0):
    """Schematischer Handler für POST /memory/ingest
    Return: eid
    """
    eid = store.ingest_event(payload_bytes, etype=etype, meta=meta or {}, score=score)
    return {'eid':eid}

def get_event_endpoint(eid: str):
    r = store.get_event(eid)
    if not r:
        return {'error':'not_found'}
    return r

def query_endpoint(since_ts: int=0, limit: int=100):
    rows = store.query_events(since_ts=since_ts, limit=limit)
    return {'count': len(rows), 'events': rows}
