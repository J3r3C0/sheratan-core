"""memory/synopses.py
Leichtgewichtige Synopsis-Datenstrukturen: Bloom + Reservoir.
Deutsche Kommentare / einfache API.
"""
import hashlib, random

class Bloom:
    """Ein sehr kleiner Bloom-Filter. m bits und k Hash-Funktionen.
    Speicherfreundlich und leicht serialisierbar.
    """
    def __init__(self, m=1024, k=3):
        self.m = m
        self.k = k
        self.bit = bytearray((m + 7) // 8)

    def _hashes(self, b: bytes):
        h = hashlib.sha256(b).digest()
        for i in range(self.k):
            start = (i * 4) % len(h)
            yield int.from_bytes(h[start:start+4], 'big') % self.m

    def add(self, item):
        b = item if isinstance(item, bytes) else str(item).encode('utf-8')
        for idx in self._hashes(b):
            self.bit[idx//8] |= (1 << (idx%8))

    def __contains__(self, item):
        b = item if isinstance(item, bytes) else str(item).encode('utf-8')
        for idx in self._hashes(b):
            if not (self.bit[idx//8] & (1 << (idx%8))):
                return False
        return True

    def serialize(self) -> bytes:
        return bytes(self.bit)

    @classmethod
    def deserialize(cls, b: bytes, k=3):
        obj = cls(m=len(b)*8, k=k)
        obj.bit = bytearray(b)
        return obj

class Reservoir:
    """Reservoir-Sampling (mergebar): behält eine Stichprobe aus dem Stream.
    Nützlich als small exemplar cache.
    """
    def __init__(self, k=32):
        self.k = k
        self.n = 0
        self.res = []

    def add(self, item):
        self.n += 1
        if len(self.res) < self.k:
            self.res.append(item)
        else:
            i = random.randrange(self.n)
            if i < self.k:
                self.res[i] = item

    def merge(self, other:'Reservoir'):
        for item in other.res:
            self.add(item)
        if len(self.res) > self.k:
            import random as _random
            self.res = _random.sample(self.res, self.k)

    def serialize(self):
        return list(self.res)
