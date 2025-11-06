import os, importlib
from typing import Optional, Callable, Any

def load_router() -> Optional[Any]:
    spec = os.getenv("SHERATAN_ROUTER", "").strip()
    if not spec:
        return None
    try:
        mod_name, factory_name = spec.split(":", 1)
        mod = importlib.import_module(mod_name)
        factory: Callable[[], Any] = getattr(mod, factory_name)
        return factory()
    except Exception as e:
        # Fail-soft: kein Router geladen
        print(f"[registry] Router load failed: {e}")
        return None
