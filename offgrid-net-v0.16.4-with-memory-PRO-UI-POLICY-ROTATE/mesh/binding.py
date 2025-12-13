#!/usr/bin/env python3
"""Mesh Binding v0.3 (BATMAN-adv & Babel hooks)

- Attempts to read neighbor/route info from:
  * batctl (BATMAN-adv): neighbors, originators
  * babeld sockets (/var/run/babeld.sock) via simple text query (if available)
- Falls back to reading a local JSON metrics file if real tools are not available.

Outputs a normalized metrics dict for broker scoring:
{
  "proto": "batman" | "babel" | "none",
  "neighbors": [{"addr": "...", "last_ttl": 1, "metric": 255, "if": "mesh0"}],
  "routes": [{"dest": "...", "metric": 512, "via": "..."}],
  "health": {"interfaces_up": 1, "mesh_ok": true, "ts": 1730000000}
}
"""
import os, json, time, subprocess, socket
from pathlib import Path

def _run(cmd):
    try:
        out = subprocess.check_output(cmd, stderr=subprocess.STDOUT, timeout=2).decode()
        return True, out
    except Exception as e:
        return False, str(e)

def read_batman_metrics():
    ok, out = _run(["bash","-lc","batctl n || true"])
    if not ok or not out.strip():
        return None
    neigh = []
    for line in out.splitlines():
        # example line parse (very loose; format varies by version)
        if line.strip().startswith("["): # header-ish
            continue
        parts = line.split()
        if len(parts) >= 3:
            addr = parts[0]
            last_ttl = parts[1].strip("()").replace(":", "")
            metric = parts[-1] if parts[-1].isdigit() else "255"
            neigh.append({"addr": addr, "last_ttl": int(last_ttl) if last_ttl.isdigit() else 1, "metric": int(metric), "if": "bat"})
    return {"proto":"batman","neighbors":neigh,"routes":[]}

def read_babel_metrics():
    # Try connecting to babeld local control socket (not implemented fully; placeholder)
    sock_path = "/var/run/babeld.sock"
    if not os.path.exists(sock_path):
        return None
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(1.0)
        s.connect(sock_path)
        s.send(b"dump
")
        data = s.recv(8192).decode(errors="ignore")
        s.close()
        routes = []
        for line in data.splitlines():
            if line.startswith("route "):
                # rough parse
                parts = line.split()
                dest = parts[2] if len(parts)>2 else "0.0.0.0/0"
                metric = int(parts[4]) if len(parts)>4 and parts[4].isdigit() else 256
                via = parts[6] if len(parts)>6 else "-"
                routes.append({"dest":dest,"metric":metric,"via":via})
        return {"proto":"babel","neighbors":[],"routes":routes}
    except Exception:
        return None

def read_fallback():
    # fallback file: mesh/metrics.json
    p = Path("./mesh/metrics.json")
    if p.exists():
        try:
            obj = json.loads(p.read_text(encoding="utf-8"))
            obj.setdefault("proto","none")
            return obj
        except Exception:
            pass
    return {"proto":"none","neighbors":[],"routes":[], "health":{"interfaces_up":0,"mesh_ok":False,"ts":int(time.time())}}

def read_metrics():
    m = read_batman_metrics()
    if m is None:
        m = read_babel_metrics()
    if m is None:
        m = read_fallback()
    # augment health
    health = {"interfaces_up": (1 if (m.get("neighbors") or m.get("routes")) else 0),
              "mesh_ok": bool(m.get("neighbors") or m.get("routes")),
              "ts": int(time.time())}
    m["health"] = health
    return m

def save_metrics(path="./mesh/last_metrics.json"):
    m = read_metrics()
    Path(path).write_text(json.dumps(m, indent=2), encoding="utf-8")
    return m

if __name__ == "__main__":
    print(json.dumps(save_metrics(), indent=2))
