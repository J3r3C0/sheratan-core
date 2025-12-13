"""memory/compact.py
Einfacher Kompaktierungs-Workflow: Micro-summary aus Events erzeugen.
Ziel: sehr wenig Speicher pro Window, mergebar.
"""
import os, json
from .synopses import Bloom, Reservoir

SUMMARY_DIR = os.environ.get('OFFGRID_SUMMARY_DIR', '/mnt/data/offgrid_summaries')
os.makedirs(SUMMARY_DIR, exist_ok=True)

def write_summary(window_id: str, bloom: Bloom, reservoir: Reservoir, topk: dict):
    path = os.path.join(SUMMARY_DIR, f"{window_id}.json")
    obj = {
        'bloom': bloom.serialize().hex(),
        'reservoir': reservoir.serialize(),
        'topk': topk
    }
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(obj, f, separators=(',',':'))

def compact_window(events, window_id: str, reservoir_k:int=32):
    """Erzeugt eine Micro-Summary aus einer Liste von Event-Dicts.
    events: [{'eid':..., 'ts':..., 'etype':..., 'meta':..., 'pref':...}, ...]
    """
    bloom = Bloom(m=1024, k=3)
    reservoir = Reservoir(k=reservoir_k)
    topk = {}
    for e in events:
        bloom.add(e['eid'])
        reservoir.add({'eid': e['eid'], 'ts': e['ts'], 'etype': e['etype'], 'meta': e.get('meta'), 'pref': e.get('pref')})
        topk[e['etype']] = topk.get(e['etype'], 0) + 1
    write_summary(window_id, bloom, reservoir, topk)
    return {'window_id': window_id, 'count': len(events), 'reservoir': len(reservoir.res)}
