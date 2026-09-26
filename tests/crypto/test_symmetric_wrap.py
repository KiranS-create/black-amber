import pytest
import os
import hashlib
from core.crypto.symmetric import (
    generate_symmetric_key,
    encrypt_aes_gcm,
    decrypt_aes_gcm,
    wrap_key_aes_kw,
    unwrap_key_aes_kw,
)
from core.crypto.key_derivation import (
    derive_key,
    derive_recipient_wrapping_key,
    PROTOCOL_VERSION,
)

def test_aes_256_gcm_key_size():
    """Verify that key generation strictly produces 256-bit (32 bytes) keys."""
    key = generate_symmetric_key()
    assert len(key) == 32
    # Reject keys with incorrect length
    with pytest.raises(ValueError, match="AES-256 key must be exactly 32 bytes"):
        encrypt_aes_gcm(b"short_key", b"Test plaintext")

def test_aes_256_gcm_roundtrip():
    """Verify AES-256-GCM encryption and decryption roundtrip."""
    key = generate_symmetric_key()
    plaintext = b"NIST SP 800-38D AES-GCM Confidential Document Stream"
    ad = b"RELEASE_SCOPE_METADATA"

    enc = encrypt_aes_gcm(key, plaintext, associated_data=ad)
    assert len(enc.nonce) == 12
    assert len(enc.tag) == 16
    assert enc.ciphertext != plaintext

    dec = decrypt_aes_gcm(key, enc)
    assert dec == plaintext

def test_aes_256_gcm_modified_ciphertext():
    """Verify that any modification to ciphertext causes decryption failure."""
    key = generate_symmetric_key()
    enc = encrypt_aes_gcm(key, b"Plaintext to protect")
    
    tampered_ct = bytearray(enc.ciphertext)
    tampered_ct[0] ^= 0x01
    tampered_enc = enc.model_copy(update={"ciphertext": bytes(tampered_ct)})

    with pytest.raises(Exception):
        decrypt_aes_gcm(key, tampered_enc)

def test_aes_256_gcm_invalid_tag():
    """Verify that invalid authentication tag is strictly rejected."""
    key = generate_symmetric_key()
    enc = encrypt_aes_gcm(key, b"Plaintext to protect")

    tampered_tag = bytearray(enc.tag)
    tampered_tag[0] ^= 0xAA
    tampered_enc = enc.model_copy(update={"tag": bytes(tampered_tag)})

    with pytest.raises(Exception):
        decrypt_aes_gcm(key, tampered_enc)

def test_nonce_uniqueness():
    """Verify that consecutive encryptions never reuse nonces."""
    key = generate_symmetric_key()
    nonces = set()
    for _ in range(500):
        enc = encrypt_aes_gcm(key, b"Same plaintext block")
        assert len(enc.nonce) == 12
        assert enc.nonce not in nonces
        nonces.add(enc.nonce)
    assert len(nonces) == 500

def test_hkdf_domain_separation():
    """Verify that different recipient IDs, release IDs, or doc IDs produce distinct wrapping keys."""
    shared_secret = os.urandom(32)

    k_alice = derive_recipient_wrapping_key(shared_secret, "rel_1", "doc_1", "alice")
    k_bob = derive_recipient_wrapping_key(shared_secret, "rel_1", "doc_1", "bob")
    k_diff_rel = derive_recipient_wrapping_key(shared_secret, "rel_2", "doc_1", "alice")
    k_diff_doc = derive_recipient_wrapping_key(shared_secret, "rel_1", "doc_2", "alice")

    assert len(k_alice) == 32
    assert len(k_bob) == 32
    assert k_alice != k_bob
    assert k_alice != k_diff_rel
    assert k_alice != k_diff_doc

def test_key_wrapping_authenticated_context():
    """Verify key wrapping roundtrip and associated data context validation."""
    wrapping_key = generate_symmetric_key()
    doc_key = generate_symmetric_key()
    ad = b"KEY-WRAP-AUTH:rel_100:bob"

    wrapped = wrap_key_aes_kw(wrapping_key, doc_key, associated_data=ad)
    unwrapped = unwrap_key_aes_kw(wrapping_key, wrapped, associated_data=ad)
    assert unwrapped == doc_key

    # Mismatched associated data fails unwrapping
    wrong_ad = b"KEY-WRAP-AUTH:rel_100:alice"
    with pytest.raises(Exception):
        unwrap_key_aes_kw(wrapping_key, wrapped, associated_data=wrong_ad)
