#!/usr/bin/env python3
import sys, json
from urllib.request import Request, urlopen
host = sys.argv[1] if len(sys.argv)>1 else "http://127.0.0.1:8081"
job_id = sys.argv[2] if len(sys.argv)>2 else "job-manual"
payload = {"job_id":job_id, "resource_type":"compute", "units":0.1, "metrics":{"compute_tokens_m":0.1,"latency_ms":800}}
req = Request(f"{host}/run", data=json.dumps(payload).encode(), headers={"Content-Type":"application/json"})
print(urlopen(req, timeout=5).read().decode())
