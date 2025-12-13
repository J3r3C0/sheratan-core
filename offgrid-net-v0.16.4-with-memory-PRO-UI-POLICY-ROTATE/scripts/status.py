#!/usr/bin/env python3
import sys, json
from urllib.request import urlopen
host = sys.argv[1] if len(sys.argv)>1 else "http://127.0.0.1:8081"
print(urlopen(f"{host}/announce", timeout=3).read().decode())
