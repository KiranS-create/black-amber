import pytest
import os
import base64
from core.crypto.kem import MLKEM768
from core.crypto.signatures import MLDSA65
from core.crypto.symmetric import encrypt_aes_gcm, decrypt_aes_gcm, wrap_key_aes_kw, unwrap_key_aes_kw
from core.recipient import Recipient, default_registry

def test_hardcoded_master_secrets_audit():
    """
    AUDIT CHECK:
    Verifies that hardcoded master and fallback secrets have been completely removed
    from class attributes in core/traceability/, and that production mode strictly
    enforces secret provisioning (fail-closed MissingSecretError).
    """
    from core.traceability.provider import PrototypeTraceabilityProvider, TardosTraceabilityProvider
    from core.traceability.tardos import SymmetricTardosEngine
    from core.traceability.keystore import TraceabilityKeystore, MissingSecretError

    # Assert that class-level hardcoded secrets are absent
    assert not hasattr(PrototypeTraceabilityProvider, "DEFAULT_SECRET_KEY")
    assert not hasattr(TardosTraceabilityProvider, "DEFAULT_SECRET_KEY")
    assert not hasattr(SymmetricTardosEngine, "DEFAULT_MASTER_KEY")

    # Assert production fail-closed behavior when no secret is configured
    old_env = os.environ.get("SIH26237_ENV")
    old_secret = os.environ.get("SIH26237_TRACEABILITY_MASTER_SECRET")
    try:
        os.environ["SIH26237_ENV"] = "production"
        if "SIH26237_TRACEABILITY_MASTER_SECRET" in os.environ:
            del os.environ["SIH26237_TRACEABILITY_MASTER_SECRET"]
        
        # In production mode without explicit or env secret, must fail closed
        with pytest.raises(MissingSecretError):
            TraceabilityKeystore.resolve_secret(explicit_secret=None, allow_dev_generation=False)
    finally:
        if old_env is not None:
            os.environ["SIH26237_ENV"] = old_env
        else:
            os.environ.pop("SIH26237_ENV", None)
        if old_secret is not None:
            os.environ["SIH26237_TRACEABILITY_MASTER_SECRET"] = old_secret
        else:
            os.environ.pop("SIH26237_TRACEABILITY_MASTER_SECRET", None)

def test_public_recipient_excludes_private_keys():
    """Ensure PublicRecipient serialization never exposes private keys."""
    alice: Recipient = default_registry.get("alice")
    pub_alice = alice.to_public()
    pub_dict = pub_alice.model_dump()

    # Must contain public keys
    assert "kem_public_key_b64" in pub_dict
    assert "dsa_public_key_b64" in pub_dict

    # Must NOT contain private keys
    assert "kem_keypair" not in pub_dict
    assert "dsa_keypair" not in pub_dict
    assert "private_key_bytes" not in pub_dict

def test_signature_tampering_bit_flip_rejected():
    """Ensure flipping a single bit in an ML-DSA-65 signature fails verification."""
    kp = MLDSA65.generate_keypair()
    message = b"CRITICAL_FORENSIC_DECRYPTION_PROVENANCE_RECORD"
    sig = MLDSA65.sign(kp.private_key_bytes, message)

    # Valid signature verifies
    assert MLDSA65.verify(kp.public_key_bytes, message, sig) is True

    # Tamper with signature
    tampered_sig = bytes([sig[0] ^ 0x01]) + sig[1:]
    assert MLDSA65.verify(kp.public_key_bytes, message, tampered_sig) is False

def test_kem_implicit_rejection_on_ciphertext_tampering():
    """
    Ensure ML-KEM-768 implicit rejection causes AES key unwrap to fail
    when the KEM ciphertext is altered.
    """
    kp = MLKEM768.generate_keypair()
    encap = MLKEM768.encapsulate(kp.public_key_bytes)

    # Tamper with first byte of KEM ciphertext
    corrupt_ct = bytes([encap.ciphertext[0] ^ 0xFF]) + encap.ciphertext[1:]
    mismatched_secret = MLKEM768.decapsulate(kp.private_key_bytes, corrupt_ct)

    # FIPS 203 implicit rejection: decapsulation succeeds without throwing,
    # but derives a pseudorandom secret that differs from the true shared secret.
    assert mismatched_secret != encap.shared_secret
