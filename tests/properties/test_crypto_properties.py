"""
tests/properties/test_crypto_properties.py

Property-based testing and fuzzing for cryptographic primitives:
- ML-KEM-768 (NIST FIPS 203)
- ML-DSA-65 (NIST FIPS 204) [INVARIANT-010]
- AES-256-GCM (NIST SP 800-38D)
- HKDF-SHA256 (RFC 5869)
"""

import hashlib
import pytest
from core.crypto.kem import MLKEM768
from core.crypto.signatures import MLDSA65
from core.crypto.symmetric import (
    generate_symmetric_key,
    encrypt_aes_gcm,
    decrypt_aes_gcm,
)
from core.crypto.key_derivation import derive_key, derive_recipient_wrapping_key
from core.testing.property_engine import PropertyRunner, DeterministicGenerator
from core.security.invariants import assert_invariant


def test_property_ml_kem_768_invariants(runner: PropertyRunner):
    """
    Property: ML-KEM-768 roundtrip recovers exact shared secret.
    Corrupted ciphertext of wrong length raises ValueError; corrupted ciphertext
    of valid length produces orthogonal shared secret (FIPS 203 implicit rejection).
    """
    kp = MLKEM768.generate_keypair()
    assert len(kp.public_key_bytes) == 1184
    assert len(kp.private_key_bytes) == 2400

    def prop(g: DeterministicGenerator):
        enc = MLKEM768.encapsulate(kp.public_key_bytes)
        assert len(enc.ciphertext) == 1088
        assert len(enc.shared_secret) == 32

        # Roundtrip
        rec_ss = MLKEM768.decapsulate(kp.private_key_bytes, enc.ciphertext)
        assert rec_ss == enc.shared_secret

        # Mutation: Flipped ciphertext
        mutated_ct = g.mutate_bytes(enc.ciphertext, mutation_rate=0.05)
        if mutated_ct != enc.ciphertext:
            if len(mutated_ct) != 1088:
                with pytest.raises(ValueError, match="1088 bytes"):
                    MLKEM768.decapsulate(kp.private_key_bytes, mutated_ct)
            else:
                fuzzed_ss = MLKEM768.decapsulate(kp.private_key_bytes, mutated_ct)
                # FIPS 203 implicit rejection: decapsulating invalid ciphertext produces pseudo-random garbage
                assert fuzzed_ss != enc.shared_secret

    res = runner.run_property("ml_kem_768_invariants", prop, iterations=25)
    assert res.passed, res.error_message


def test_property_ml_dsa_65_unforgeability(runner: PropertyRunner):
    """
    INVARIANT-010: ML-DSA-65 signature verifies if and only if message and signature
    are authentic under matching public key. Corrupted messages/signatures strictly fail.
    """
    # Pre-generate keypair once for speed, fuzz messages & mutations
    kp = MLDSA65.generate_keypair()
    assert len(kp.public_key_bytes) == 1952
    assert len(kp.private_key_bytes) == 4000

    def prop(g: DeterministicGenerator):
        msg_len = g.integer(0, 512)
        msg = g.bytes_data(msg_len)

        sig = MLDSA65.sign(kp.private_key_bytes, msg)
        assert len(sig) == 3293

        # 1. Valid signature verifies
        is_valid = MLDSA65.verify(kp.public_key_bytes, msg, sig)
        assert_invariant(is_valid, "INVARIANT-010", "Valid signature failed verification", g.seed)

        # 2. Corrupted message fails
        corrupted_msg = msg + b"\x01" if not msg else g.mutate_bytes(msg)
        if corrupted_msg != msg:
            tampered_valid = MLDSA65.verify(kp.public_key_bytes, corrupted_msg, sig)
            assert_invariant(not tampered_valid, "INVARIANT-010", "Tampered message verified", g.seed)

        # 3. Corrupted signature fails
        corrupted_sig = g.mutate_bytes(sig)
        if corrupted_sig != sig:
            sig_valid = MLDSA65.verify(kp.public_key_bytes, msg, corrupted_sig)
            assert_invariant(not sig_valid, "INVARIANT-010", "Corrupted signature verified", g.seed)

    res = runner.run_property("ml_dsa_65_unforgeability", prop, iterations=100)
    assert res.passed, res.error_message


def test_property_aes_256_gcm_authenticated_encryption(runner: PropertyRunner):
    """
    Property: AES-256-GCM authenticated encryption guarantees that any modification
    to ciphertext, tag, or AAD causes decryption to fail closed.
    """
    def prop(g: DeterministicGenerator):
        key = generate_symmetric_key()
        pt_len = g.integer(0, 1024)
        plaintext = g.bytes_data(pt_len)
        aad = g.bytes_data(g.integer(0, 128)) if g.boolean() else None

        ciphertext_obj = encrypt_aes_gcm(key, plaintext, associated_data=aad)
        assert len(ciphertext_obj.nonce) == 12
        assert len(ciphertext_obj.tag) == 16

        # Normal decryption
        recovered = decrypt_aes_gcm(key, ciphertext_obj)
        assert recovered == plaintext

        # Tampered ciphertext
        if len(ciphertext_obj.ciphertext) > 0:
            bad_ct = bytearray(ciphertext_obj.ciphertext)
            bad_ct[g.integer(0, len(bad_ct) - 1)] ^= 0xFF
            from core.crypto.models import SymmetricCiphertext
            tampered_obj = SymmetricCiphertext(
                nonce=ciphertext_obj.nonce,
                ciphertext=bytes(bad_ct),
                tag=ciphertext_obj.tag,
                associated_data=aad,
            )
            with pytest.raises(ValueError):
                decrypt_aes_gcm(key, tampered_obj)

        # Tampered tag
        bad_tag = bytearray(ciphertext_obj.tag)
        bad_tag[g.integer(0, 15)] ^= 0x55
        tampered_tag_obj = SymmetricCiphertext(
            nonce=ciphertext_obj.nonce,
            ciphertext=ciphertext_obj.ciphertext,
            tag=bytes(bad_tag),
            associated_data=aad,
        )
        with pytest.raises(ValueError):
            decrypt_aes_gcm(key, tampered_tag_obj)

    res = runner.run_property("aes_256_gcm_authenticated_encryption", prop, iterations=200)
    assert res.passed, res.error_message


def test_property_hkdf_domain_separation(runner: PropertyRunner):
    """
    Property: HKDF-SHA256 with distinct domain separation info strings
    produces orthogonal, unpredictable key streams.
    """
    def prop(g: DeterministicGenerator):
        ikm = g.bytes_data(32)
        info1 = g.alphanumeric(8, 16).encode("utf-8")
        info2 = g.alphanumeric(8, 16).encode("utf-8")

        if info1 != info2:
            k1 = derive_key(ikm, info=info1, length=32)
            k2 = derive_key(ikm, info=info2, length=32)
            assert len(k1) == 32
            assert len(k2) == 32
            assert k1 != k2

    res = runner.run_property("hkdf_domain_separation", prop, iterations=500)
    assert res.passed, res.error_message
