#!/usr/bin/env python3
import time, sys, random

def retry_backoff(fn, max_tries=5, base=0.3, jitter=0.25, on_error=None):
    """Call fn() with exponential backoff. Returns fn() result or raises last error."""
    tries = 0
    last_exc = None
    while tries < max_tries:
        try:
            return fn()
        except Exception as e:
            last_exc = e
            if on_error:
                try: on_error(e, tries)
                except: pass
            delay = base * (2 ** tries) + random.random()*jitter
            time.sleep(delay)
            tries += 1
    if last_exc:
        raise last_exc

def log(msg):
    ts = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    sys.stdout.write(f"[{ts}] {msg}\n")
    sys.stdout.flush()
