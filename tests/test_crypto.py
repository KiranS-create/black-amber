import pytest
import os
from core.crypto.kem import MLKEM768
from core.crypto.signatures import MLDSA65
from core.crypto.symmetric import (
    generate_symmetric_key,
    encrypt_aes_gcm,
    decrypt_aes_gcm,
    wrap_key_aes_kw,
    unwrap_key_aes_kw
)
from core.crypto.key_derivation import derive_key

def test_aes_roundtrip():
    """Verify AES-256-GCM encryption and decryption roundtrip with authentication."""
    key = generate_symmetric_key()
    plaintext = b"Top secret test payload for SIH26237"
    ad = b"AUTH-DATA-CONTEXT"

    encrypted = encrypt_aes_gcm(key, plaintext, associated_data=ad)
    assert len(encrypted.nonce) == 12
    assert len(encrypted.tag) == 16
    assert encrypted.ciphertext != plaintext

    decrypted = decrypt_aes_gcm(key, encrypted)
    assert decrypted == plaintext

def test_aes_invalid_tag():
    """Verify that tampering with ciphertext causes authentication failure."""
    key = generate_symmetric_key()
    plaintext = b"Confidential document content"
    encrypted = encrypt_aes_gcm(key, plaintext)

    # Tamper with 1 byte of ciphertext
    tampered_bytes = bytearray(encrypted.ciphertext)
    tampered_bytes[0] ^= 0xFF
    tampered_encrypted = encrypted.model_copy(update={"ciphertext": bytes(tampered_bytes)})

    with pytest.raises(Exception):
        decrypt_aes_gcm(key, tampered_encrypted)

def test_kem_wrap_unwrap():
    """Verify ML-KEM-768 key encapsulation and decapsulation."""
    keypair = MLKEM768.generate_keypair()
    assert keypair.public_key_bytes is not None
    assert keypair.private_key_bytes is not None

    encap_res = MLKEM768.encapsulate(keypair.public_key_bytes)
    assert encap_res.ciphertext is not None
    assert encap_res.shared_secret is not None

    recovered_secret = MLKEM768.decapsulate(keypair.private_key_bytes, encap_res.ciphertext)
    assert recovered_secret == encap_res.shared_secret

def test_kem_decapsulation_wrong_key():
    """Verify that decapsulation with wrong keypair fails."""
    kp1 = MLKEM768.generate_keypair()
    kp2 = MLKEM768.generate_keypair()

    encap_res = MLKEM768.encapsulate(kp1.public_key_bytes)
    with pytest.raises(ValueError):
        MLKEM768.decapsulate(kp2.private_key_bytes, encap_res.ciphertext)

def test_ml_dsa_signature():
    """Verify ML-DSA-65 digital signature generation and verification."""
    kp = MLDSA65.generate_keypair()
    message = b"Signed Decryption Provenance Event #12345"

    signature = MLDSA65.sign(kp.private_key_bytes, message)
    assert len(signature) > 0

    assert MLDSA65.verify(kp.public_key_bytes, message, signature) is True
    assert MLDSA65.verify(kp.public_key_bytes, b"Tampered message", signature) is False

def test_key_wrap_unwrap_roundtrip():
    """Verify document key wrapping and unwrapping."""
    wrapping_key = generate_symmetric_key()
    doc_key = generate_symmetric_key()

    wrapped = wrap_key_aes_kw(wrapping_key, doc_key)
    unwrapped = unwrap_key_aes_kw(wrapping_key, wrapped)
    assert unwrapped == doc_key

def test_crypto_roundtrip():
    """Full envelope encryption roundtrip test."""
    kem_kp = MLKEM768.generate_keypair()
    doc_key = generate_symmetric_key()
    document = b"Full roundtrip document test"

    # Encapsulate
    encap = MLKEM768.encapsulate(kem_kp.public_key_bytes)
    wrapping_key = derive_key(encap.shared_secret)
    wrapped_doc_key = wrap_key_aes_kw(wrapping_key, doc_key)

    # Encrypt doc
    encrypted_doc = encrypt_aes_gcm(doc_key, document)

    # Decapsulate & Decrypt
    rec_secret = MLKEM768.decapsulate(kem_kp.private_key_bytes, encap.ciphertext)
    rec_wrapping_key = derive_key(rec_secret)
    rec_doc_key = unwrap_key_aes_kw(rec_wrapping_key, wrapped_doc_key)
    decrypted_doc = decrypt_aes_gcm(rec_doc_key, encrypted_doc)

    assert decrypted_doc == document
