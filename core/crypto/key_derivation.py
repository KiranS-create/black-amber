import os
import hmac
import hashlib
from typing import Optional

def derive_key(
    shared_secret: bytes,
    length: int = 32,
    salt: Optional[bytes] = None,
    info: bytes = b"SIH26237-HKDF-KEY-DERIVATION"
) -> bytes:
    """
    Derive a cryptographically secure key of specified length using standard RFC 5869 HKDF-SHA256.
    Uses pure hashlib/hmac to guarantee zero native DLL dependencies.
    """
    if salt is None:
        salt = b"\x00" * 32
    
    # 1. HKDF Extract: PRK = HMAC-Hash(salt, IKM)
    prk = hmac.new(salt, shared_secret, hashlib.sha256).digest()

    # 2. HKDF Expand: OKM = HMAC-Hash(PRK, info || 0x01) || ...
    okm = b""
    t = b""
    block_num = 1
    while len(okm) < length:
        msg = t + info + bytes([block_num])
        t = hmac.new(prk, msg, hashlib.sha256).digest()
        okm += t
        block_num += 1

    return okm[:length]
