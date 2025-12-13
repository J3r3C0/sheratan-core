#!/usr/bin/env python3
"""Patch Plug&Play: radio --noise, daemon /hs, uploader --auto_place."""
import re, json, argparse
from pathlib import Path

def read(p): return Path(p).read_text(encoding="utf-8")
def write(p, s): Path(p).write_text(s, encoding="utf-8")

def patch_radio_gateway(root):
    p = Path(root)/"radio"/"radio_gateway.py"
    if not p.exists(): print(f"[warn] missing {p}"); return
    src = read(p)
    if "crypto.session import Identity" not in src:
        src = src.replace("\nimport ", "\nfrom crypto.session import Identity, initiator_handshake, responder_handshake, session_from_key\nimport ")
    if "--noise" not in src:
        src = re.sub(r"(ap\s*=\s*argparse\.ArgumentParser\([^\)]*\)\s*)", r"\1\n    ap.add_argument('--noise', type=int, default=0)", src, flags=re.S)
    if "SESS_CACHE" not in src:
        src = src.replace("args = ap.parse_args()", "args = ap.parse_args()\nSESS_CACHE = {}\nDISCOVERY_CACHE = {}\nNOISE = bool(getattr(args,'noise',0)) and (args.transport in ('udp','file'))\n")
    if "def _ensure_session(" not in src:
        src += """

def _ensure_session(endpoint: str):
    if endpoint in SESS_CACHE: return SESS_CACHE[endpoint]
    peer = DISCOVERY_CACHE.get(endpoint) or {}
    peer_x_b64 = peer.get('x25519_public_key')
    if not peer_x_b64:
        try:
            import urllib.request as u, json as _J
            j = _J.loads(u.urlopen(endpoint + '/pubkeys', timeout=3).read().decode())
            peer_x_b64 = j.get('x25519_public_key'); DISCOVERY_CACHE[endpoint] = j
        except Exception:
            return None
    from crypto.session import Identity, initiator_handshake, session_from_key
    with open(args.keys, 'r', encoding='utf-8') as f:
        kd = json.load(f)
    hs1, key = initiator_handshake(Identity.from_json(kd), peer_x_b64)
    try:
        import urllib.request as u, json as _J
        req = u.Request(endpoint + '/hs', data=_J.dumps(hs1).encode('utf-8'), headers={'Content-Type':'application/json'})
        rsp = _J.loads(u.urlopen(req, timeout=3).read().decode())
        if rsp.get('ok'):
            sess = session_from_key(key, endpoint); SESS_CACHE[endpoint] = sess; return sess
    except Exception:
        return None
    return None

def send_enveloped(endpoint: str, payload_bytes: bytes, lowlevel_send=None):
    if not NOISE or lowlevel_send is None:
        return lowlevel_send(endpoint, payload_bytes) if lowlevel_send else False
    sess = _ensure_session(endpoint)
    if not sess: return False
    env = sess.seal(payload_bytes, aad={'ep': endpoint})
    import json as _J
    return lowlevel_send(endpoint, _J.dumps({'env': env}).encode('utf-8'))
"""
    write(p, src); print(f"[ok] {p} patched")

def patch_host_daemon(root):
    p = Path(root)/"host_daemon"/"daemon_stub.py"
    if not p.exists(): print(f"[warn] missing {p}"); return
    src = read(p)
    if "/hs" not in src:
        src = src.replace("def do_POST(self):", "def do_POST(self):\n        import json")
        src = src.replace("elif u.path == "/pubkeys":", "elif u.path == "/pubkeys":")
        # append handler block safely at end of function
        src = src.replace("return", "return\n        # /hs responder\n        if u.path == '/hs':\n            body = json.loads(self.rfile.read(int(self.headers.get('Content-Length','0'))))\n            from crypto.session import Identity, responder_handshake\n            with open(STATE.get('keys_path','./keys/node-A.json'), 'r', encoding='utf-8') as f:\n                kd = json.load(f)\n            ID = Identity.from_json(kd)\n            msg2, key, peer_ed = responder_handshake(ID, body)\n            self._send(200, {'ok': True})\n            return")
        write(p, src); print(f"[ok] {p} patched (/hs)")
    else:
        print(f"[info] {p} already has /hs")

def patch_uploader(root):
    p = Path(root)/"transfer"/"uploader.py"
    if not p.exists(): print(f"[warn] missing {p}"); return
    src = read(p)
    if "placement.policy" not in src:
        src = src.replace("import ", "from placement.policy import load_hosts, choose_k_n, place_shards\nimport ")
    if "--auto_place" not in src:
        src = re.sub(r"(ap\s*=\s*argparse\.ArgumentParser\([^\)]*\)\s*)", r"\1\n    ap.add_argument('--auto_place', action='store_true')\n    ap.add_argument('--target', choices=['fast','balanced','durable'], default='balanced')\n", src, flags=re.S)
    if "AUTO_PLACE_PATCHED" not in src:
        src = re.sub(r"(required\s*=\s*args\.k\s*if\s*args\.mode\s*==\s*\"ec\"\s*else\s*1\s*)",
                     r"\1\n    # AUTO_PLACE_PATCHED\n    if args.auto_place:\n        hosts = load_hosts()\n        if args.mode == 'ec':\n            k_auto, n_auto = choose_k_n(hosts, target=args.target)\n            if not args.k: args.k = k_auto\n            if not args.n: args.n = min(max(args.k+1, n_auto), len(hosts))\n        _PLACED_ENDPOINTS = place_shards(asset_id, hosts, n=(args.n if args.mode=='ec' else args.r))\n",
                     src, flags=re.S)
    write(p, src); print(f"[ok] {p} patched (auto_place)")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', default='.')
    args = ap.parse_args()
    patch_radio_gateway(args.root)
    patch_host_daemon(args.root)
    patch_uploader(args.root)
    print('[done] Plug&Play patch applied (best-effort).')

if __name__ == '__main__':
    main()
