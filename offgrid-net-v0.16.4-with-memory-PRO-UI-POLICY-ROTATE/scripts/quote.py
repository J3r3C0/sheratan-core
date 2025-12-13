#!/usr/bin/env python3
import sys, json
from urllib.request import urlopen
host = sys.argv[1] if len(sys.argv)>1 else "http://127.0.0.1:8081"
typ = sys.argv[2] if len(sys.argv)>2 else "compute"
size = float(sys.argv[3]) if len(sys.argv)>3 else 0.25
print(urlopen(f"{host}/quote?type={typ}&size={size}", timeout=3).read().decode())
