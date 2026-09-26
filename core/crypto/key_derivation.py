import os
import hmac
import hashlib
from typing import Optional

PROTOCOL_VERSION = "SIH26237-v1.0"

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


def derive_recipient_wrapping_key(
    shared_secret: bytes,
    release_id: str,
    document_id: str,
    recipient_id: str,
    algorithm_id: str = "ML-KEM-768",
    protocol_version: str = PROTOCOL_VERSION
) -> bytes:
    """
    Derive a domain-separated 256-bit wrapping key from an ML-KEM shared secret.
    Explicitly cryptographically binds:
    - protocol_version
    - release_id
    - document_id
    - recipient_id
    - algorithm_id
    """
    # Salt incorporates protocol version, algorithm, and release scope
    salt_preimage = f"SALT:{protocol_version}:{algorithm_id}:{release_id}".encode('utf-8')
    salt = hashlib.sha256(salt_preimage).digest()

    # Info context string provides unique per-recipient and per-document domain separation
    info = (
        f"DOC-KEY-WRAP:{protocol_version}:{algorithm_id}:"
        f"REL={release_id}:DOC={document_id}:REC={recipient_id}"
    ).encode('utf-8')

    return derive_key(shared_secret, length=32, salt=salt, info=info)
