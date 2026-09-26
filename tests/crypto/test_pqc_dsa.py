import pytest
from core.crypto.signatures import (
    MLDSA65,
    MLDSAProvider,
    StandardMLDSA65Provider,
    OQSMLDSAProvider,
    DevFallbackDSAProvider,
)

def test_ml_dsa_provider_real():
    """Verify that ML-DSA provider is genuine post-quantum lattice implementation and production safe."""
    metadata = MLDSA65.get_metadata()
    assert metadata["is_post_quantum"] is True
    assert metadata["is_production_safe"] is True
    assert "FIPS 204" in metadata["standard"] or "Dilithium3" in metadata["standard"]
    assert metadata["public_key_size_bytes"] == 1952
    assert metadata["private_key_size_bytes"] == 4000
    assert metadata["signature_size_bytes"] == 3293
    assert not isinstance(MLDSA65.get_provider(), DevFallbackDSAProvider)

def test_ml_dsa_65_sign_verify():
    """Verify ML-DSA-65 key generation, signing, and signature verification."""
    kp = MLDSA65.generate_keypair()
    assert len(kp.public_key_bytes) == 1952
    assert len(kp.private_key_bytes) == 4000
    assert kp.algorithm == "ML-DSA-65"

    message = b"Confidential Decryption Provenance Event #98765"
    signature = MLDSA65.sign(kp.private_key_bytes, message)
    assert len(signature) == 3293

    is_valid = MLDSA65.verify(kp.public_key_bytes, message, signature)
    assert is_valid is True

def test_ml_dsa_modified_message():
    """Verify that any modification to the signed message results in verification failure."""
    kp = MLDSA65.generate_keypair()
    original_msg = b"Authorized Decryption Event for Bob"
    signature = MLDSA65.sign(kp.private_key_bytes, original_msg)

    tampered_msg = b"Authorized Decryption Event for Eve"
    assert MLDSA65.verify(kp.public_key_bytes, tampered_msg, signature) is False

def test_ml_dsa_modified_signature():
    """Verify that any modification to the signature bytes results in rejection."""
    kp = MLDSA65.generate_keypair()
    msg = b"Critical security payload"
    signature = MLDSA65.sign(kp.private_key_bytes, msg)

    tampered_sig = bytearray(signature)
    tampered_sig[100] ^= 0x01
    assert MLDSA65.verify(kp.public_key_bytes, msg, bytes(tampered_sig)) is False

def test_ml_dsa_wrong_public_key():
    """Verify that signature fails verification against another recipient's public key."""
    kp_alice = MLDSA65.generate_keypair()
    kp_bob = MLDSA65.generate_keypair()

    msg = b"Alice signed provenance statement"
    alice_sig = MLDSA65.sign(kp_alice.private_key_bytes, msg)

    # Bob's public key cannot verify Alice's signature
    assert MLDSA65.verify(kp_bob.public_key_bytes, msg, alice_sig) is False
