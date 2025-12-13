#!/usr/bin/env python3
import sys, json
from urllib.request import Request, urlopen
url = sys.argv[1] if len(sys.argv)>1 else "http://127.0.0.1:8081/toggle"
active = (sys.argv[2].lower() == "true") if len(sys.argv)>2 else True
req = Request(url, data=json.dumps({"active":active}).encode(), headers={"Content-Type":"application/json"})
print(urlopen(req, timeout=3).read().decode())
