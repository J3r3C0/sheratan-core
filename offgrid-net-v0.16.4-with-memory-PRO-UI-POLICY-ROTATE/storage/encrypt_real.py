# Real E2EE using PyNaCl (libsodium)
# - Key exchange: X25519 (nacl.public)
# - AEAD: XChaCha20-Poly1305-IETF (nacl.bindings)

import os, base64, hashlib
from nacl import public, bindings

def hkdf_blake2b(key_material: bytes, salt: bytes = b"offgrid-net", info: bytes = b"e2ee", length: int = 32) -> bytes:
    # Simple HKDF-like KDF using BLAKE2b
    return hashlib.blake2b(key_material + salt + info, digest_size=length).digest()

def derive_shared_key(xsk: public.PrivateKey, peer_xpk: public.PublicKey) -> bytes:
    # X25519 ECDH to get 32-byte shared secret
    shared = bindings.crypto_scalarmult(bytes(xsk), bytes(peer_xpk))
    # Derive AEAD key
    return hkdf_blake2b(shared)

def encrypt_xchacha(plaintext: bytes, aead_key: bytes, aad: bytes = b"") -> dict:
    nonce = os.urandom(bindings.crypto_aead_xchacha20poly1305_ietf_NPUBBYTES)
    ct = bindings.crypto_aead_xchacha20poly1305_ietf_encrypt(plaintext, aad, nonce, aead_key)
    return {"nonce": base64.b64encode(nonce).decode(), "ciphertext": base64.b64encode(ct).decode()}

def decrypt_xchacha(nonce_b64: str, ciphertext_b64: str, aead_key: bytes, aad: bytes = b"") -> bytes:
    nonce = base64.b64decode(nonce_b64.encode())
    ct = base64.b64decode(ciphertext_b64.encode())
    return bindings.crypto_aead_xchacha20poly1305_ietf_decrypt(ct, aad, nonce, aead_key)
