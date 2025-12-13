#!/usr/bin/env python3
import json, argparse, threading, time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

class ReceiptStore:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text("[]", encoding="utf-8")
        self.lock = threading.Lock()

    def add(self, item: dict):
        with self.lock:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            data.append(item)
            self.path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def all(self):
        with self.lock:
            return json.loads(self.path.read_text(encoding="utf-8"))

def make_handler(receipts: ReceiptStore, node_id: str):
    class H(BaseHTTPRequestHandler):
        def _send(self, code=200, body=b"OK", ctype="application/json"):
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            if self.path.startswith("/status"):
                body = json.dumps({"ok": True, "node_id": node_id, "receipts": len(receipts.all())}).encode()
                return self._send(200, body)
            return self._send(404, b'{"error":"not found"}')

        def do_POST(self):
            length = int(self.headers.get("Content-Length","0") or "0")
            data = self.rfile.read(length) if length>0 else b"{}"
            try:
                payload = json.loads(data.decode() or "{}")
            except Exception:
                payload = {"raw": data.decode(errors="ignore")}
            receipts.add({"ts": time.time(), "node_id": node_id, "payload": payload})
            return self._send(200, b'{"ok":true}')
    return H

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, required=True)
    ap.add_argument("--node_id", required=True)
    ap.add_argument("--keys", default="")
    args = ap.parse_args()

    receipts = ReceiptStore(Path(f"./receipts_{args.node_id}.json"))
    srv = HTTPServer(("127.0.0.1", args.port), make_handler(receipts, args.node_id))
    print(f"[host] {args.node_id} listening on 127.0.0.1:{args.port}")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()
