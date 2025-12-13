# Minimal copy; use full variant from monolithic 0.16-alpha if present
import time, json, math
from pathlib import Path
DISC = Path('./discovery/mesh_hosts.json')
VIA_SCORE = {'file':1.2,'lora':1.1,'ble':1.05,'udp':1.0}
def load_hosts():
    try: return json.loads(DISC.read_text(encoding='utf-8'))
    except: return {}
def availability(rec, now=None):
    now = now or int(time.time()); age = max(0, now-int(rec.get('last_seen', now)))
    base = VIA_SCORE.get(rec.get('via','udp'),1.0)
    return base*(0.5**(age/60.0))
def choose_k_n(hosts, target='balanced'):
    m=len(hosts); 
    if m<=2: return (1, max(1,m))
    if target=='fast': n=min(6,m); k=max(2, math.ceil(n*0.5))
    elif target=='durable': n=min(12,m); k=max(3, math.ceil(n*0.7))
    else: n=min(10,m); k=max(3, math.ceil(n*0.6))
    return (k,n)
def failure_domain(rec): return (rec.get('via'), rec.get('power','?'), rec.get('cluster','?'))
def place_shards(asset_id, hosts, n):
    scored = sorted(hosts.items(), key=lambda kv: availability(kv[1]), reverse=True)
    chosen, doms = [], set()
    for ep, rec in scored:
        dom = failure_domain(rec)
        if dom in doms: continue
        chosen.append(ep); doms.add(dom)
        if len(chosen)>=n: break
    if len(chosen)<n:
        for ep,_ in scored:
            if ep not in chosen:
                chosen.append(ep)
                if len(chosen)>=n: break
    return chosen
