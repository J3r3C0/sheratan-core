#!/usr/bin/env python3
import json
from economy.wallet import _load
print(json.dumps(_load(), indent=2))
