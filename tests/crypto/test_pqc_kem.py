import pytest
from core.crypto.kem import (
    MLKEM768,
    MLKEMProvider,
    StandardMLKEM768Provider,
    OQSMLKEMProvider,
    DevFallbackKEMProvider,
)

def test_ml_kem_provider_real():
    """Verify that ML-KEM provider is genuine post-quantum lattice implementation and production safe."""
    metadata = MLKEM768.get_metadata()
    assert metadata["is_post_quantum"] is True
    assert metadata["is_production_safe"] is True
    assert "FIPS 203" in metadata["standard"] or "Kyber-768" in metadata["standard"]
    assert metadata["public_key_size_bytes"] == 1184
    assert metadata["private_key_size_bytes"] == 2400
    assert metadata["ciphertext_size_bytes"] == 1088
    assert metadata["shared_secret_size_bytes"] == 32
    assert not isinstance(MLKEM768.get_provider(), DevFallbackKEMProvider)

def test_ml_kem_768_roundtrip():
    """Verify ML-KEM-768 key generation, encapsulation, and decapsulation."""
    kp = MLKEM768.generate_keypair()
    assert len(kp.public_key_bytes) == 1184
    assert len(kp.private_key_bytes) == 2400
    assert kp.algorithm == "ML-KEM-768"

    encap_res = MLKEM768.encapsulate(kp.public_key_bytes)
    assert len(encap_res.ciphertext) == 1088
    assert len(encap_res.shared_secret) == 32

    shared_secret_rec = MLKEM768.decapsulate(kp.private_key_bytes, encap_res.ciphertext)
    assert shared_secret_rec == encap_res.shared_secret

def test_ml_kem_wrong_recipient():
    """Verify that decapsulation with another recipient's private key implicitly rejects."""
    alice_kp = MLKEM768.generate_keypair()
    bob_kp = MLKEM768.generate_keypair()

    # Encapsulate to Alice
    encap_alice = MLKEM768.encapsulate(alice_kp.public_key_bytes)

    # Bob attempts decapsulation
    bob_derived_secret = MLKEM768.decapsulate(bob_kp.private_key_bytes, encap_alice.ciphertext)
    assert bob_derived_secret != encap_alice.shared_secret
    assert len(bob_derived_secret) == 32

def test_ml_kem_modified_ciphertext():
    """Verify that tampering with ciphertext triggers FIPS 203 implicit rejection."""
    kp = MLKEM768.generate_keypair()
    encap_res = MLKEM768.encapsulate(kp.public_key_bytes)

    # Tamper with 1 byte of the ciphertext
    tampered_ct = bytearray(encap_res.ciphertext)
    tampered_ct[15] ^= 0x55

    recovered_secret = MLKEM768.decapsulate(kp.private_key_bytes, bytes(tampered_ct))
    assert recovered_secret != encap_res.shared_secret

def test_ml_kem_modified_public_key():
    """Verify that an invalid length public key is immediately rejected during encapsulation."""
    with pytest.raises(ValueError, match="ML-KEM-768 public key must be exactly 1184 bytes"):
        MLKEM768.encapsulate(b"\x00" * 500)
