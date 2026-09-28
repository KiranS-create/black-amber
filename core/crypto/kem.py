from abc import ABC, abstractmethod
import os
import hashlib
import warnings
import threading
from typing import Optional, Dict, Any, Tuple
from core.crypto.models import KeyPair, EncapsulationResult

# Check if native liboqs is available
try:
    import oqs
    _OQS_AVAILABLE = True
except Exception:
    _OQS_AVAILABLE = False

# Check if pure Python standard FIPS 203 / Kyber is available
try:
    from kyber_py.kyber import Kyber768 as _Kyber768_Engine
    _KYBER_PY_AVAILABLE = True
except Exception:
    _KYBER_PY_AVAILABLE = False


class MLKEMProvider(ABC):
    """Abstract Base Class for ML-KEM-768 / FIPS 203 Providers."""

    @abstractmethod
    def generate_keypair(self) -> KeyPair:
        """Generate an ML-KEM-768 public and private keypair."""
        pass

    @abstractmethod
    def encapsulate(self, public_key_bytes: bytes) -> EncapsulationResult:
        """Encapsulate a shared secret against a recipient's public key."""
        pass

    @abstractmethod
    def decapsulate(self, private_key_bytes: bytes, ciphertext: bytes) -> bytes:
        """Decapsulate the shared secret using recipient's private key."""
        pass

    @abstractmethod
    def algorithm_metadata(self) -> Dict[str, Any]:
        """Return cryptographic parameters and metadata."""
        pass


class OQSMLKEMProvider(MLKEMProvider):
    """
    Genuine Post-Quantum ML-KEM-768 provider using native liboqs (Open Quantum Safe).
    Target: FIPS 203 / Kyber-768 C-implementation.
    """
    ALGORITHM_NAME = "ML-KEM-768"

    def __init__(self):
        if not _OQS_AVAILABLE:
            raise RuntimeError("liboqs native library is not available in the current environment")

    def generate_keypair(self) -> KeyPair:
        with oqs.KeyEncapsulation("Kyber768") as client:
            public_key = client.generate_keypair()
            private_key = client.export_secret_key()
            return KeyPair(
                algorithm=self.ALGORITHM_NAME,
                public_key_bytes=public_key,
                private_key_bytes=private_key
            )

    def encapsulate(self, public_key_bytes: bytes) -> EncapsulationResult:
        with oqs.KeyEncapsulation("Kyber768") as client:
            ciphertext, shared_secret = client.encap_secret(public_key_bytes)
            return EncapsulationResult(
                ciphertext=ciphertext,
                shared_secret=shared_secret
            )

    def decapsulate(self, private_key_bytes: bytes, ciphertext: bytes) -> bytes:
        with oqs.KeyEncapsulation("Kyber768", secret_key=private_key_bytes) as client:
            return client.decap_secret(ciphertext)

    def algorithm_metadata(self) -> Dict[str, Any]:
        return {
            "algorithm": self.ALGORITHM_NAME,
            "standard": "FIPS 203 / Kyber-768",
            "provider": "liboqs (native C)",
            "public_key_size_bytes": 1184,
            "private_key_size_bytes": 2400,
            "ciphertext_size_bytes": 1088,
            "shared_secret_size_bytes": 32,
            "is_post_quantum": True,
            "is_production_safe": True
        }


class StandardMLKEM768Provider(MLKEMProvider):
    """
    Genuine NIST FIPS 203 / Kyber-768 lattice-based implementation.
    Operates without external native C DLLs while strictly executing the
    Module-Lattice Key Encapsulation Mechanism (ML-KEM-768) mathematics.
    """
    ALGORITHM_NAME = "ML-KEM-768"
    _lock = threading.Lock()

    def __init__(self):
        if not _KYBER_PY_AVAILABLE:
            raise RuntimeError("NIST FIPS 203 Kyber engine is not available")

    def generate_keypair(self) -> KeyPair:
        with self._lock:
            pk, sk = _Kyber768_Engine.keygen()
        if len(pk) != 1184 or len(sk) != 2400:
            raise ValueError(f"Invalid ML-KEM-768 key dimensions: pk={len(pk)}, sk={len(sk)}")
        return KeyPair(
            algorithm=self.ALGORITHM_NAME,
            public_key_bytes=pk,
            private_key_bytes=sk
        )

    def encapsulate(self, public_key_bytes: bytes) -> EncapsulationResult:
        if len(public_key_bytes) != 1184:
            raise ValueError(f"ML-KEM-768 public key must be exactly 1184 bytes, got {len(public_key_bytes)}")
        with self._lock:
            shared_secret, ciphertext = _Kyber768_Engine.encaps(public_key_bytes)
        if len(ciphertext) != 1088 or len(shared_secret) != 32:
            raise ValueError(f"Unexpected ML-KEM output dimensions: ct={len(ciphertext)}, ss={len(shared_secret)}")
        return EncapsulationResult(
            ciphertext=ciphertext,
            shared_secret=shared_secret
        )

    def decapsulate(self, private_key_bytes: bytes, ciphertext: bytes) -> bytes:
        if len(private_key_bytes) != 2400:
            raise ValueError(f"ML-KEM-768 secret key must be exactly 2400 bytes, got {len(private_key_bytes)}")
        if len(ciphertext) != 1088:
            raise ValueError(f"ML-KEM-768 ciphertext must be exactly 1088 bytes, got {len(ciphertext)}")
        # FIPS 203 decapsulation with implicit rejection
        with self._lock:
            shared_secret = _Kyber768_Engine.decaps(private_key_bytes, ciphertext)
        return shared_secret

    def algorithm_metadata(self) -> Dict[str, Any]:
        return {
            "algorithm": self.ALGORITHM_NAME,
            "standard": "FIPS 203 (ML-KEM-768)",
            "provider": "kyber_py (Standard Lattice Implementation)",
            "public_key_size_bytes": 1184,
            "private_key_size_bytes": 2400,
            "ciphertext_size_bytes": 1088,
            "shared_secret_size_bytes": 32,
            "is_post_quantum": True,
            "is_production_safe": True
        }


class DevFallbackKEMProvider(MLKEMProvider):
    """
    CRITICAL WARNING: DEVELOPMENT ONLY FALLBACK.
    THIS PROVIDER DOES NOT USE LATTICE CRYPTOGRAPHY AND MUST NEVER BE USED
    IN PRODUCTION OR FINAL SIH EVALUATION.
    """
    ALGORITHM_NAME = "DEV-MOCK-KEM-NON-PQC"

    def __init__(self):
        warnings.warn(
            "DevFallbackKEMProvider is active. This is an insecure simulation fallback!",
            UserWarning,
            stacklevel=2
        )

    def generate_keypair(self) -> KeyPair:
        priv = os.urandom(64)
        pub_seed = hashlib.sha3_512(priv + b"DEV-MOCK-KEM").digest()
        public_key = pub_seed + hashlib.shake_256(pub_seed).digest(1184 - len(pub_seed))
        private_key = priv + public_key + hashlib.shake_256(priv).digest(2400 - len(priv) - len(public_key))
        return KeyPair(
            algorithm=self.ALGORITHM_NAME,
            public_key_bytes=public_key,
            private_key_bytes=private_key
        )

    def encapsulate(self, public_key_bytes: bytes) -> EncapsulationResult:
        token = os.urandom(32)
        ciphertext = token + hashlib.shake_256(token + public_key_bytes).digest(1088 - 32)
        shared_secret = hashlib.sha256(token + public_key_bytes[:32]).digest()
        return EncapsulationResult(
            ciphertext=ciphertext,
            shared_secret=shared_secret
        )

    def decapsulate(self, private_key_bytes: bytes, ciphertext: bytes) -> bytes:
        token = ciphertext[:32]
        public_key_part = private_key_bytes[64:128]
        return hashlib.sha256(token + public_key_part[:32]).digest()

    def algorithm_metadata(self) -> Dict[str, Any]:
        return {
            "algorithm": self.ALGORITHM_NAME,
            "standard": "NON-STANDARD (INSECURE DEV FALLBACK)",
            "provider": "MockSimulation",
            "is_post_quantum": False,
            "is_production_safe": False
        }


# Provider Selection & Unified MLKEM768 Class
def get_default_kem_provider(fail_closed: Optional[bool] = None) -> MLKEMProvider:
    if _OQS_AVAILABLE:
        try:
            return OQSMLKEMProvider()
        except Exception:
            pass
    if _KYBER_PY_AVAILABLE:
        return StandardMLKEM768Provider()
    
    # Check if production mode or explicit strictness requires fail-closed behavior
    is_prod = (
        os.environ.get("SIH26237_ENV", "").strip().lower() in ("production", "prod") or
        os.environ.get("AEGISTRACE_ENV", "").strip().lower() in ("production", "prod") or
        os.environ.get("SIH26237_STRICT_PQC", "").strip().lower() in ("1", "true", "yes")
    )
    should_fail_closed = fail_closed if fail_closed is not None else is_prod

    if should_fail_closed:
        raise RuntimeError(
            "FATAL [ML-KEM-768]: No genuine post-quantum lattice provider (liboqs or kyber-py) is available. "
            "Insecure DevFallbackKEMProvider is strictly blocked in production mode."
        )
    return DevFallbackKEMProvider()



class MLKEM768:
    """
    Standardized ML-KEM-768 API interface for SIH26237.
    Dispatches to verified PQC providers (liboqs native or StandardMLKEM768Provider).
    """
    ALGORITHM_NAME = "ML-KEM-768"
    _provider: MLKEMProvider = get_default_kem_provider()

    @classmethod
    def set_provider(cls, provider: MLKEMProvider):
        cls._provider = provider

    @classmethod
    def get_provider(cls) -> MLKEMProvider:
        return cls._provider

    @classmethod
    def is_native_oqs(cls) -> bool:
        return isinstance(cls._provider, OQSMLKEMProvider)

    @classmethod
    def is_production_safe(cls) -> bool:
        return cls._provider.algorithm_metadata().get("is_production_safe", False)

    @classmethod
    def generate_keypair(cls) -> KeyPair:
        return cls._provider.generate_keypair()

    @classmethod
    def encapsulate(cls, public_key_bytes: bytes) -> EncapsulationResult:
        return cls._provider.encapsulate(public_key_bytes)

    @classmethod
    def decapsulate(cls, private_key_bytes: bytes, ciphertext: bytes) -> bytes:
        return cls._provider.decapsulate(private_key_bytes, ciphertext)

    @classmethod
    def get_metadata(cls) -> Dict[str, Any]:
        return cls._provider.algorithm_metadata()
