"""
AegisTrace Device Crypto Helpers for Attestation Verification.

Provides standards-compliant verification of NIST P-256, RSA, and ML-DSA-65
signatures across hardware attestation quotes and challenge responses.
"""

import base64
import hashlib
from typing import Optional, Tuple
from Crypto.PublicKey import ECC, RSA
from Crypto.Signature import DSS, pkcs1_15
from Crypto.Hash import SHA256

from core.crypto.signatures import MLDSA65


def verify_device_signature(
    public_key_pem: str,
    algorithm: str,
    message: bytes,
    signature: bytes,
) -> bool:
    """
    Verifies a signature using the device public key.
    Supported algorithms: "P-256" (ECDSA), "RSA-2048", "ML-DSA-65".
    """
    try:
        alg = algorithm.upper()
        if alg in ("P-256", "ECDSA", "SECP256R1"):
            key = ECC.import_key(public_key_pem)
            h = SHA256.new(message)
            verifier = DSS.new(key, 'fips-186-3')
            verifier.verify(h, signature)
            return True

        elif alg in ("RSA", "RSA-2048", "RSA-3072", "RSA-4096"):
            key = RSA.import_key(public_key_pem)
            h = SHA256.new(message)
            pkcs1_15.new(key).verify(h, signature)
            return True

        elif alg in ("ML-DSA-65", "MLDSA65"):
            # PEM or raw base64
            pub_bytes = base64.b64decode(public_key_pem) if not public_key_pem.startswith("-----") else public_key_pem.encode()
            return MLDSA65.verify(pub_bytes, message, signature)

        return False
    except Exception:
        return False
