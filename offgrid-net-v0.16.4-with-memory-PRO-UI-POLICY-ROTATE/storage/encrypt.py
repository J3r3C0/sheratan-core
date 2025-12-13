# WARNING: Placeholder encryption (NOT SECURE). For demo only.
# Real implementation should use XChaCha20-Poly1305 with X25519 key exchange.

import hashlib

def _derive(key: bytes) -> bytes:
    return hashlib.sha256(key).digest()

def enc_xor(data: bytes, key: bytes) -> bytes:
    k = _derive(key)
    out = bytearray(len(data))
    for i, b in enumerate(data):
        out[i] = b ^ k[i % len(k)]
    return bytes(out)

def dec_xor(data: bytes, key: bytes) -> bytes:
    return enc_xor(data, key)
