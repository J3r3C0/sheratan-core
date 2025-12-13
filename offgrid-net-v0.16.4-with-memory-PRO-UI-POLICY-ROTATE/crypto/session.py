# (same as in monolithic 0.16-alpha) — copy into your tree if not present
from nacl import public, signing, secret, utils
import base64, json, hmac, hashlib, time
from dataclasses import dataclass

def hkdf_sha256(ikm: bytes, salt: bytes = b"", info: bytes = b"", length: int = 32) -> bytes:
    if not salt: salt = b"\x00" * 32
    prk = hmac.new(salt, ikm, hashlib.sha256).digest()
    t=b""; okm=b""; blk=0
    while len(okm)<length:
        blk+=1; t = hmac.new(prk, t+info+bytes([blk]), hashlib.sha256).digest(); okm+=t
    return okm[:length]

@dataclass
class Identity:
    ed25519_sign: signing.SigningKey
    ed25519_verify: signing.VerifyKey
    x25519_static: public.PrivateKey
    x25519_public: public.PublicKey
    @staticmethod
    def from_json(d: dict) -> "Identity":
        ed_sk = signing.SigningKey(base64.b64decode(d["ed25519"]["signing_key"]))
        ed_vk = ed_sk.verify_key
        x_sk = public.PrivateKey(base64.b64decode(d["x25519"]["private_key"]))
        x_pk = x_sk.public_key
        return Identity(ed_sk, ed_vk, x_sk, x_pk)
