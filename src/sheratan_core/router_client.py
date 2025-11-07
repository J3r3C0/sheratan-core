from __future__ import annotations
import os, httpx
from typing import Any, Dict

class RouterClient:
    def __init__(self, base_url: str | None = None, timeout_s: float = 30.0):
        self.base = (base_url or os.getenv("SHERATAN_ROUTER_BASE") or "").rstrip("/")
        if not self.base:
            raise RuntimeError("SHERATAN_ROUTER_BASE missing")
        self.client = httpx.Client(timeout=timeout_s)

    def health(self) -> Dict[str, Any]:
        r = self.client.get(f"{self.base}/health")
        r.raise_for_status()
        return r.json()

    def models(self) -> list[str]:
        r = self.client.get(f"{self.base}/models")
        r.raise_for_status()
        return r.json()

    def complete(self, prompt: str, max_tokens: int = 128, model: str | None = None) -> Dict[str, Any]:
        payload = {"prompt": prompt, "max_tokens": max_tokens}
        if model: payload["model"] = model
        r = self.client.post(f"{self.base}/complete", json=payload)
        r.raise_for_status()
        return r.json()
