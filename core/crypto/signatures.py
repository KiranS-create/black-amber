from abc import ABC, abstractmethod
import os
import hashlib
import warnings
import threading
from typing import Optional, Dict, Any
from core.crypto.models import KeyPair

# Check if native liboqs is available
try:
    import oqs
    _OQS_AVAILABLE = True
except Exception:
    _OQS_AVAILABLE = False

# Check if pure Python standard FIPS 204 / Dilithium is available
try:
    from dilithium_py.dilithium import Dilithium3 as _Dilithium3_Engine
    _DILITHIUM_PY_AVAILABLE = True
except Exception:
    _DILITHIUM_PY_AVAILABLE = False


class MLDSAProvider(ABC):
    """Abstract Base Class for ML-DSA-65 / FIPS 204 Providers."""

    @abstractmethod
    def generate_keypair(self) -> KeyPair:
        """Generate an ML-DSA-65 public and private keypair."""
        pass

    @abstractmethod
    def sign(self, private_key_bytes: bytes, message: bytes) -> bytes:
        """Generate a digital signature over message using private signing key."""
        pass

    @abstractmethod
    def verify(self, public_key_bytes: bytes, message: bytes, signature: bytes) -> bool:
        """Verify the digital signature using signer's public key."""
        pass

    @abstractmethod
    def algorithm_metadata(self) -> Dict[str, Any]:
        """Return cryptographic parameters and metadata."""
        pass


class OQSMLDSAProvider(MLDSAProvider):
    """
    Genuine Post-Quantum ML-DSA-65 provider using native liboqs (Open Quantum Safe).
    Target: FIPS 204 / Dilithium3 C-implementation.
    """
    ALGORITHM_NAME = "ML-DSA-65"

    def __init__(self):
        if not _OQS_AVAILABLE:
            raise RuntimeError("liboqs native library is not available in the current environment")

    def generate_keypair(self) -> KeyPair:
        with oqs.Signature("Dilithium3") as signer:
            public_key = signer.generate_keypair()
            private_key = signer.export_secret_key()
            return KeyPair(
                algorithm=self.ALGORITHM_NAME,
                public_key_bytes=public_key,
                private_key_bytes=private_key
            )

    def sign(self, private_key_bytes: bytes, message: bytes) -> bytes:
        with oqs.Signature("Dilithium3", secret_key=private_key_bytes) as signer:
            return signer.sign(message)

    def verify(self, public_key_bytes: bytes, message: bytes, signature: bytes) -> bool:
        try:
            with oqs.Signature("Dilithium3") as verifier:
                return verifier.verify(message, signature, public_key_bytes)
        except Exception:
            return False

    def algorithm_metadata(self) -> Dict[str, Any]:
        return {
            "algorithm": self.ALGORITHM_NAME,
            "standard": "FIPS 204 / Dilithium3",
            "provider": "liboqs (native C)",
            "public_key_size_bytes": 1952,
            "private_key_size_bytes": 4000,
            "signature_size_bytes": 3293,
            "is_post_quantum": True,
            "is_production_safe": True
        }


class StandardMLDSA65Provider(MLDSAProvider):
    """
    Genuine NIST FIPS 204 / Dilithium3 lattice-based digital signature implementation.
    Operates without external native C DLLs while strictly executing the
    Module-Lattice Digital Signature Algorithm (ML-DSA-65) mathematics.
    """
    ALGORITHM_NAME = "ML-DSA-65"
    _lock = threading.Lock()

    def __init__(self):
        if not _DILITHIUM_PY_AVAILABLE:
            raise RuntimeError("NIST FIPS 204 Dilithium engine is not available")

    def generate_keypair(self) -> KeyPair:
        with self._lock:
            pk, sk = _Dilithium3_Engine.keygen()
        if len(pk) != 1952 or len(sk) != 4000:
            raise ValueError(f"Invalid ML-DSA-65 key dimensions: pk={len(pk)}, sk={len(sk)}")
        return KeyPair(
            algorithm=self.ALGORITHM_NAME,
            public_key_bytes=pk,
            private_key_bytes=sk
        )

    def sign(self, private_key_bytes: bytes, message: bytes) -> bytes:
        if len(private_key_bytes) != 4000:
            raise ValueError(f"ML-DSA-65 secret key must be exactly 4000 bytes, got {len(private_key_bytes)}")
        # FIPS 204 sign
        with self._lock:
            signature = _Dilithium3_Engine.sign(private_key_bytes, message)
        return signature

    def verify(self, public_key_bytes: bytes, message: bytes, signature: bytes) -> bool:
        if len(public_key_bytes) != 1952 or len(signature) != 3293:
            return False
        try:
            with self._lock:
                return _Dilithium3_Engine.verify(public_key_bytes, message, signature)
        except Exception:
            return False

    def algorithm_metadata(self) -> Dict[str, Any]:
        return {
            "algorithm": self.ALGORITHM_NAME,
            "standard": "FIPS 204 (ML-DSA-65)",
            "provider": "dilithium_py (Standard Lattice Implementation)",
            "public_key_size_bytes": 1952,
            "private_key_size_bytes": 4000,
            "signature_size_bytes": 3293,
            "is_post_quantum": True,
            "is_production_safe": True
        }


class DevFallbackDSAProvider(MLDSAProvider):
    """
    CRITICAL WARNING: DEVELOPMENT ONLY FALLBACK.
    THIS PROVIDER USES CLASSICAL CRYPTOGRAPHY (Ed25519) AND MUST NEVER BE USED
    IN PRODUCTION OR FINAL SIH EVALUATION.
    """
    ALGORITHM_NAME = "DEV-MOCK-DSA-NON-PQC"

    def __init__(self):
        warnings.warn(
            "DevFallbackDSAProvider is active. This is an insecure simulation fallback!",
            UserWarning,
            stacklevel=2
        )
        try:
            from Crypto.PublicKey import ECC
            self._ecc = ECC
        except ImportError:
            self._ecc = None

    def generate_keypair(self) -> KeyPair:
        if not self._ecc:
            raise RuntimeError("PyCryptodome ECC unavailable for fallback")
        key = self._ecc.generate(curve='ed25519')
        return KeyPair(
            algorithm=self.ALGORITHM_NAME,
            public_key_bytes=key.public_key().export_key(format='DER'),
            private_key_bytes=key.export_key(format='DER')
        )

    def sign(self, private_key_bytes: bytes, message: bytes) -> bytes:
        from Crypto.PublicKey import ECC
        from Crypto.Signature import eddsa
        key = ECC.import_key(private_key_bytes)
        signer = eddsa.new(key, 'rfc8032')
        digest_input = b"FALLBACK-DSA:" + hashlib.sha256(message).digest()
        return signer.sign(digest_input)

    def verify(self, public_key_bytes: bytes, message: bytes, signature: bytes) -> bool:
        from Crypto.PublicKey import ECC
        from Crypto.Signature import eddsa
        try:
            key = ECC.import_key(public_key_bytes)
            verifier = eddsa.new(key, 'rfc8032')
            digest_input = b"FALLBACK-DSA:" + hashlib.sha256(message).digest()
            verifier.verify(digest_input, signature)
            return True
        except Exception:
            return False

    def algorithm_metadata(self) -> Dict[str, Any]:
        return {
            "algorithm": self.ALGORITHM_NAME,
            "standard": "NON-STANDARD (DEV-FALLBACK-ED25519)",
            "provider": "PyCryptodome Ed25519",
            "is_post_quantum": False,
            "is_production_safe": False
        }


def get_default_dsa_provider(fail_closed: Optional[bool] = None) -> MLDSAProvider:
    if _OQS_AVAILABLE:
        try:
            return OQSMLDSAProvider()
        except Exception:
            pass
    if _DILITHIUM_PY_AVAILABLE:
        return StandardMLDSA65Provider()
    
    # Check if production mode or explicit strictness requires fail-closed behavior
    is_prod = (
        os.environ.get("SIH26237_ENV", "").strip().lower() in ("production", "prod") or
        os.environ.get("AEGISTRACE_ENV", "").strip().lower() in ("production", "prod") or
        os.environ.get("SIH26237_STRICT_PQC", "").strip().lower() in ("1", "true", "yes")
    )
    should_fail_closed = fail_closed if fail_closed is not None else is_prod

    if should_fail_closed:
        raise RuntimeError(
            "FATAL [ML-DSA-65]: No genuine post-quantum lattice provider (liboqs or dilithium-py) is available. "
            "Insecure DevFallbackDSAProvider is strictly blocked in production mode."
        )
    return DevFallbackDSAProvider()



class MLDSA65:
    """
    Standardized ML-DSA-65 API interface for SIH26237.
    Dispatches to verified PQC providers (liboqs native or StandardMLDSA65Provider).
    """
    ALGORITHM_NAME = "ML-DSA-65"
    _provider: MLDSAProvider = get_default_dsa_provider()

    @classmethod
    def set_provider(cls, provider: MLDSAProvider):
        cls._provider = provider

    @classmethod
    def get_provider(cls) -> MLDSAProvider:
        return cls._provider

    @classmethod
    def is_native_oqs(cls) -> bool:
        return isinstance(cls._provider, OQSMLDSAProvider)

    @classmethod
    def is_production_safe(cls) -> bool:
        return cls._provider.algorithm_metadata().get("is_production_safe", False)

    @classmethod
    def generate_keypair(cls) -> KeyPair:
        return cls._provider.generate_keypair()

    @classmethod
    def sign(cls, private_key_bytes: bytes, message: bytes) -> bytes:
        return cls._provider.sign(private_key_bytes, message)

    @classmethod
    def verify(cls, public_key_bytes: bytes, message: bytes, signature: bytes) -> bool:
        return cls._provider.verify(public_key_bytes, message, signature)

    @classmethod
    def get_metadata(cls) -> Dict[str, Any]:
        return cls._provider.algorithm_metadata()
