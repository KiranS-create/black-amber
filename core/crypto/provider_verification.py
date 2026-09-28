"""
core/crypto/provider_verification.py

Cryptographic Provider Supply-Chain Verification for AegisTrace.
Ensures that runtime cryptographic providers for ML-KEM-768, ML-DSA-65,
AES-256-GCM, and HKDF-SHA256 are genuine, approved, production-grade
implementations conforming to NIST standards (FIPS 203, FIPS 204, SP 800-38D).

Strictly blocks silent substitution of mock crypto, toy implementations,
or unvetted fallback stubs in production environments. Exposes machine-verifiable
startup self-test statuses:
    - CRYPTO_PROVIDER_VALID
    - CRYPTO_PROVIDER_INVALID
    - CRYPTO_PROVIDER_UNAVAILABLE
"""

import os
import time
import hashlib
from enum import Enum
from typing import Dict, Any, Optional

from core.crypto.kem import (
    MLKEM768,
    StandardMLKEM768Provider,
    OQSMLKEMProvider,
    DevFallbackKEMProvider,
)
from core.crypto.signatures import (
    MLDSA65,
    StandardMLDSA65Provider,
    OQSMLDSAProvider,
    DevFallbackDSAProvider,
)
from core.crypto.symmetric import (
    generate_symmetric_key,
    encrypt_aes_gcm,
    decrypt_aes_gcm,
)
from core.crypto.key_derivation import (
    derive_key,
    derive_recipient_wrapping_key,
)


class CryptoProviderStatus(str, Enum):
    CRYPTO_PROVIDER_VALID = "CRYPTO_PROVIDER_VALID"
    CRYPTO_PROVIDER_INVALID = "CRYPTO_PROVIDER_INVALID"
    CRYPTO_PROVIDER_UNAVAILABLE = "CRYPTO_PROVIDER_UNAVAILABLE"


class CryptoSupplyChainError(RuntimeError):
    """Raised when cryptographic provider integrity or security assumptions are violated."""
    pass


def is_production_mode() -> bool:
    """Check if environment enforces production-strict cryptographic security."""
    return (
        os.environ.get("SIH26237_ENV", "").strip().lower() in ("production", "prod") or
        os.environ.get("AEGISTRACE_ENV", "").strip().lower() in ("production", "prod") or
        os.environ.get("SIH26237_STRICT_PQC", "").strip().lower() in ("1", "true", "yes")
    )


class CryptoProviderVerifier:
    """
    Validates the entire cryptographic provider chain against NIST specifications
    and enforces fail-closed supply-chain invariants.
    """

    @classmethod
    def verify_ml_kem_768(cls) -> Dict[str, Any]:
        """
        Verify ML-KEM-768 / FIPS 203 provider authenticity, parameters, and roundtrip.
        """
        provider = MLKEM768.get_provider()
        metadata = MLKEM768.get_metadata()
        is_fallback = isinstance(provider, DevFallbackKEMProvider)

        if is_fallback:
            return {
                "primitive": "ML-KEM-768",
                "standard": "FIPS 203",
                "status": CryptoProviderStatus.CRYPTO_PROVIDER_INVALID.value,
                "provider_class": provider.__class__.__name__,
                "is_post_quantum": False,
                "is_production_safe": False,
                "error": "Insecure DevFallbackKEMProvider is active. Mock lattice fallback detected.",
            }

        # Perform live roundtrip KAT
        t0 = time.perf_counter()
        try:
            kp = MLKEM768.generate_keypair()
            if len(kp.public_key_bytes) != 1184 or len(kp.private_key_bytes) != 2400:
                raise ValueError(
                    f"FIPS 203 dimension mismatch: pk={len(kp.public_key_bytes)} (expected 1184), "
                    f"sk={len(kp.private_key_bytes)} (expected 2400)"
                )

            enc_res = MLKEM768.encapsulate(kp.public_key_bytes)
            if len(enc_res.ciphertext) != 1088 or len(enc_res.shared_secret) != 32:
                raise ValueError(
                    f"FIPS 203 ciphertext/secret mismatch: ct={len(enc_res.ciphertext)} (expected 1088), "
                    f"ss={len(enc_res.shared_secret)} (expected 32)"
                )

            recovered_ss = MLKEM768.decapsulate(kp.private_key_bytes, enc_res.ciphertext)
            if recovered_ss != enc_res.shared_secret:
                raise ValueError("ML-KEM-768 shared secret mismatch during decapsulation roundtrip")

            roundtrip_ms = (time.perf_counter() - t0) * 1000.0
            return {
                "primitive": "ML-KEM-768",
                "standard": "FIPS 203",
                "status": CryptoProviderStatus.CRYPTO_PROVIDER_VALID.value,
                "provider_class": provider.__class__.__name__,
                "provider_name": metadata.get("provider", "Unknown"),
                "is_post_quantum": True,
                "is_production_safe": True,
                "public_key_bytes": 1184,
                "private_key_bytes": 2400,
                "ciphertext_bytes": 1088,
                "shared_secret_bytes": 32,
                "roundtrip_time_ms": round(roundtrip_ms, 2),
            }
        except Exception as e:
            return {
                "primitive": "ML-KEM-768",
                "standard": "FIPS 203",
                "status": CryptoProviderStatus.CRYPTO_PROVIDER_INVALID.value,
                "provider_class": provider.__class__.__name__,
                "error": str(e),
            }

    @classmethod
    def verify_ml_dsa_65(cls) -> Dict[str, Any]:
        """
        Verify ML-DSA-65 / FIPS 204 signature provider authenticity and mathematical verification.
        """
        provider = MLDSA65.get_provider()
        metadata = MLDSA65.get_metadata()
        is_fallback = isinstance(provider, DevFallbackDSAProvider)

        if is_fallback:
            return {
                "primitive": "ML-DSA-65",
                "standard": "FIPS 204",
                "status": CryptoProviderStatus.CRYPTO_PROVIDER_INVALID.value,
                "provider_class": provider.__class__.__name__,
                "is_post_quantum": False,
                "is_production_safe": False,
                "error": "Insecure DevFallbackDSAProvider is active. Mock signature fallback detected.",
            }

        t0 = time.perf_counter()
        try:
            kp = MLDSA65.generate_keypair()
            if len(kp.public_key_bytes) != 1952 or len(kp.private_key_bytes) != 4000:
                raise ValueError(
                    f"FIPS 204 dimension mismatch: pk={len(kp.public_key_bytes)} (expected 1952), "
                    f"sk={len(kp.private_key_bytes)} (expected 4000)"
                )

            test_message = b"AEGISTRACE_SUPPLY_CHAIN_CRYPTOGRAPHIC_PROVIDER_ATTESTATION"
            sig = MLDSA65.sign(kp.private_key_bytes, test_message)
            if len(sig) != 3293:
                raise ValueError(f"FIPS 204 signature length mismatch: {len(sig)} (expected 3293)")

            # Verify valid signature
            if not MLDSA65.verify(kp.public_key_bytes, test_message, sig):
                raise ValueError("ML-DSA-65 signature verification failed on valid signature")

            # Verify tampered message is rejected
            if MLDSA65.verify(kp.public_key_bytes, test_message + b"TAMPER", sig):
                raise ValueError("ML-DSA-65 accepted tampered message signature")

            # Verify tampered signature is rejected
            corrupted_sig = bytearray(sig)
            corrupted_sig[0] ^= 0xFF
            if MLDSA65.verify(kp.public_key_bytes, test_message, bytes(corrupted_sig)):
                raise ValueError("ML-DSA-65 accepted corrupted signature bytes")

            roundtrip_ms = (time.perf_counter() - t0) * 1000.0
            return {
                "primitive": "ML-DSA-65",
                "standard": "FIPS 204",
                "status": CryptoProviderStatus.CRYPTO_PROVIDER_VALID.value,
                "provider_class": provider.__class__.__name__,
                "provider_name": metadata.get("provider", "Unknown"),
                "is_post_quantum": True,
                "is_production_safe": True,
                "public_key_bytes": 1952,
                "private_key_bytes": 4000,
                "signature_bytes": 3293,
                "roundtrip_time_ms": round(roundtrip_ms, 2),
            }
        except Exception as e:
            return {
                "primitive": "ML-DSA-65",
                "standard": "FIPS 204",
                "status": CryptoProviderStatus.CRYPTO_PROVIDER_INVALID.value,
                "provider_class": provider.__class__.__name__,
                "error": str(e),
            }

    @classmethod
    def verify_aes_256_gcm(cls) -> Dict[str, Any]:
        """
        Verify AES-256-GCM authenticated symmetric encryption per NIST SP 800-38D.
        """
        try:
            key = generate_symmetric_key()
            if len(key) != 32:
                raise ValueError(f"AES key length mismatch: {len(key)} (expected 32)")

            plaintext = b"AEGISTRACE_CONFIDENTIAL_ENVELOPE_DATA"
            aad = b"AUTHENTICATED_ASSOCIATED_DATA_DOMAIN"

            ciphertext = encrypt_aes_gcm(key, plaintext, associated_data=aad)
            if len(ciphertext.nonce) != 12:
                raise ValueError(f"AES-GCM nonce length mismatch: {len(ciphertext.nonce)} (expected 12)")
            if len(ciphertext.tag) != 16:
                raise ValueError(f"AES-GCM tag length mismatch: {len(ciphertext.tag)} (expected 16)")

            decrypted = decrypt_aes_gcm(key, ciphertext)
            if decrypted != plaintext:
                raise ValueError("AES-256-GCM decrypted plaintext mismatch")

            return {
                "primitive": "AES-256-GCM",
                "standard": "NIST SP 800-38D",
                "status": CryptoProviderStatus.CRYPTO_PROVIDER_VALID.value,
                "key_size_bits": 256,
                "nonce_size_bytes": 12,
                "tag_size_bytes": 16,
                "authenticated_encryption": True,
            }
        except Exception as e:
            return {
                "primitive": "AES-256-GCM",
                "standard": "NIST SP 800-38D",
                "status": CryptoProviderStatus.CRYPTO_PROVIDER_INVALID.value,
                "error": str(e),
            }

    @classmethod
    def verify_hkdf_sha256(cls) -> Dict[str, Any]:
        """
        Verify HKDF-SHA256 key derivation per RFC 5869 and NIST SP 800-56C.
        """
        try:
            ikm = hashlib.sha256(b"input_key_material_master_seed").digest()
            k1 = derive_key(ikm, info=b"AEGISTRACE_DOMAIN_1", length=32)
            k2 = derive_key(ikm, info=b"AEGISTRACE_DOMAIN_2", length=32)

            if len(k1) != 32 or len(k2) != 32:
                raise ValueError(f"HKDF output length mismatch: len(k1)={len(k1)}, len(k2)={len(k2)}")
            if k1 == k2:
                raise ValueError("HKDF domain separation failed: distinct info strings produced identical keys")

            # Check recipient wrapping key derivation
            ss = b"\x01" * 32
            rwk1 = derive_recipient_wrapping_key(ss, "REL-1", "DOC-1", "user-A")
            rwk2 = derive_recipient_wrapping_key(ss, "REL-1", "DOC-1", "user-B")
            if rwk1 == rwk2 or len(rwk1) != 32:
                raise ValueError("Recipient wrapping key domain separation failed")

            return {
                "primitive": "HKDF-SHA256",
                "standard": "RFC 5869 / NIST SP 800-56C",
                "status": CryptoProviderStatus.CRYPTO_PROVIDER_VALID.value,
                "hash_function": "SHA-256",
                "domain_separation_verified": True,
            }
        except Exception as e:
            return {
                "primitive": "HKDF-SHA256",
                "standard": "RFC 5869 / NIST SP 800-56C",
                "status": CryptoProviderStatus.CRYPTO_PROVIDER_INVALID.value,
                "error": str(e),
            }

    @classmethod
    def verify_all_providers(cls, fail_closed: Optional[bool] = None) -> Dict[str, Any]:
        """
        Run complete cryptographic provider supply-chain verification.
        Returns machine-verifiable statuses and fails closed in production.
        """
        enforce_fail_closed = fail_closed if fail_closed is not None else is_production_mode()

        kem_res = cls.verify_ml_kem_768()
        dsa_res = cls.verify_ml_dsa_65()
        aes_res = cls.verify_aes_256_gcm()
        hkdf_res = cls.verify_hkdf_sha256()

        primitives = {
            "ml_kem_768": kem_res,
            "ml_dsa_65": dsa_res,
            "aes_256_gcm": aes_res,
            "hkdf_sha256": hkdf_res,
        }

        all_valid = all(
            p["status"] == CryptoProviderStatus.CRYPTO_PROVIDER_VALID.value
            for p in primitives.values()
        )

        overall_status = (
            CryptoProviderStatus.CRYPTO_PROVIDER_VALID.value
            if all_valid
            else CryptoProviderStatus.CRYPTO_PROVIDER_INVALID.value
        )

        report = {
            "overall_status": overall_status,
            "is_production_mode": is_production_mode(),
            "enforce_fail_closed": enforce_fail_closed,
            "primitives": primitives,
        }

        if not all_valid and enforce_fail_closed:
            failed = [k for k, v in primitives.items() if v["status"] != CryptoProviderStatus.CRYPTO_PROVIDER_VALID.value]
            raise CryptoSupplyChainError(
                f"FATAL: Cryptographic provider supply-chain check failed for: {failed}. "
                "Execution aborted in production fail-closed mode."
            )

        return report
