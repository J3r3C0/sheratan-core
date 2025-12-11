import requests
import os

CORE_URL = os.getenv("SHERATAN_CORE_URL", "http://core:8000")

def core_post(path: str, payload: dict):
    resp = requests.post(f"{CORE_URL}{path}", json=payload)
    resp.raise_for_status()
    return resp.json()

def core_get(path: str, params: dict | None = None):
    resp = requests.get(f"{CORE_URL}{path}", params=params)
    resp.raise_for_status()
    return resp.json()
