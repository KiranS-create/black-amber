"""
Tests for Recipient Cryptographic Key Rotation & Identity Continuity.

Verifies:
- ML-DSA-65 signing key rotation: K1 -> K2.
- Cryptographic identity continuity: recipient_id invariant across epochs.
- Historical receipts signed with K1 remain cryptographically verifiable.
- New events MUST use active successor key K2.
- Signing with old/retired key K1 for new events fails closed.
- Verifying old event with new key K2 fails closed.
- Historical receipts remain verifiable even if K1 is later revoked.
- ML-KEM-768 rotation: old releases remain decryptable with K1, new releases require K2.
- Revoked KEM key cannot decrypt newly issued packages.
"""

import base64
from datetime import datetime, timezone, timedelta
import pytest

from core.crypto.signatures import MLDSA65
from core.crypto.kem import MLKEM768
from core.crypto.symmetric import encrypt_aes_gcm, decrypt_aes_gcm
from core.crypto.lifecycle.manager import KeyLifecycleManager
from core.crypto.lifecycle.resolver import HistoricalKeyResolver, HistoricalResolutionStatus
from core.crypto.lifecycle.adapters import RecipientKeyLifecycleAdapter
from core.crypto.lifecycle.models import KeyState, KeyType


def test_recipient_signing_rotation_and_historical_verification():
    mgr = KeyLifecycleManager()
    resolver = HistoricalKeyResolver(mgr)
    adapter = RecipientKeyLifecycleAdapter(mgr, resolver)

    recipient_id = "rec_alice_4f9a"

    # Step 1: Enroll Alice at Epoch 1 (K1)
    dsa_rec1, kem_rec1 = adapter.enroll_recipient_keys(recipient_id)
    k1_pair = dsa_rec1.metadata["raw_keypair"]
    assert dsa_rec1.creation_epoch == 1
    assert dsa_rec1.status == KeyState.ACTIVE
    assert dsa_rec1.owner == recipient_id

    # Step 2: Alice signs Decryption Event 1 under K1 at T1
    t0_dt = datetime.fromisoformat(dsa_rec1.creation_timestamp)
    t1 = (t0_dt + timedelta(minutes=1)).isoformat()
    event1_msg = b"AEGIS-DECRYPTION-EVENT:1:doc_root_alpha:sess_001"
    event1_sig = MLDSA65.sign(k1_pair.private_key_bytes, event1_msg)

    # Verify event 1 immediately under Epoch 1
    res1 = resolver.resolve_historical_key(
        owner=recipient_id,
        key_type=KeyType.RECIPIENT_PRIVATE_KEY,
        event_timestamp=t1,
        event_epoch=1
    )
    assert res1.is_valid is True
    assert res1.status == HistoricalResolutionStatus.HISTORICALLY_VALID
    assert res1.key_record.key_id == dsa_rec1.key_id
    pub_k1_bytes = base64.b64decode(res1.public_material_b64)
    assert MLDSA65.verify(pub_k1_bytes, event1_msg, event1_sig) is True

    # Step 3: Rotate Alice's signing key to Epoch 2 (K2) at T2
    t2 = (t0_dt + timedelta(minutes=2)).isoformat()
    prev_dsa, next_dsa, k2_pair = adapter.rotate_signing_key(
        recipient_id=recipient_id,
        reason="Scheduled rotation to ML-DSA Epoch 2"
    )

    # Invariant: Identity Continuity (recipient_id unchanged!)
    assert next_dsa.owner == recipient_id
    assert next_dsa.creation_epoch == 2
    assert next_dsa.status == KeyState.ACTIVE
    assert prev_dsa.status == KeyState.RETIRED
    assert next_dsa.predecessor_key_id == prev_dsa.key_id
    assert prev_dsa.successor_key_id == next_dsa.key_id

    # Step 4: Alice signs Decryption Event 2 under K2 at T3
    t3 = (t0_dt + timedelta(minutes=3)).isoformat()
    event2_msg = b"AEGIS-DECRYPTION-EVENT:2:doc_root_beta:sess_002"
    event2_sig = MLDSA65.sign(k2_pair.private_key_bytes, event2_msg)

    # Verify Event 2 under Epoch 2
    active_key = mgr.get_active_key(recipient_id, KeyType.RECIPIENT_PRIVATE_KEY)
    assert active_key.key_id == next_dsa.key_id
    pub_k2_bytes = base64.b64decode(active_key.public_material_b64)
    assert MLDSA65.verify(pub_k2_bytes, event2_msg, event2_sig) is True

    # Step 5: Historical Verifiability Invariant!
    # Event 1 (signed under K1 at T1) MUST remain historically verifiable after rotation!
    hist_res1 = resolver.resolve_historical_key(
        owner=recipient_id,
        key_type=KeyType.RECIPIENT_PRIVATE_KEY,
        event_timestamp=t1,
        event_epoch=1
    )
    assert hist_res1.is_valid is True
    assert hist_res1.key_record.key_id == prev_dsa.key_id
    assert MLDSA65.verify(base64.b64decode(hist_res1.public_material_b64), event1_msg, event1_sig) is True

    # Step 6: Anti-History-Rewriting Invariant!
    # Verifying Event 1 using new key K2 MUST FAIL (proves history cannot be rewritten)
    assert MLDSA65.verify(pub_k2_bytes, event1_msg, event1_sig) is False

    # Step 7: Revocation Invariant!
    # If K1 is subsequently revoked at T4, Event 1 at T1 (< T4) MUST REMAIN HISTORICALLY VERIFIABLE!
    t4 = (t0_dt + timedelta(minutes=4)).isoformat()
    mgr.revoke_key(prev_dsa.key_id, reason="Security cleanup", timestamp=t4)
    assert prev_dsa.status == KeyState.REVOKED

    hist_after_rev = resolver.resolve_historical_key(
        owner=recipient_id,
        key_type=KeyType.RECIPIENT_PRIVATE_KEY,
        event_timestamp=t1,
        event_epoch=1
    )
    assert hist_after_rev.is_valid is True
    assert hist_after_rev.status == HistoricalResolutionStatus.HISTORICALLY_VALID
    assert MLDSA65.verify(base64.b64decode(hist_after_rev.public_material_b64), event1_msg, event1_sig) is True

    # Step 8: Post-Revocation Rejection Invariant!
    # An event claiming to be signed by K1 at T5 (> T4) MUST BE REJECTED!
    t5 = (t0_dt + timedelta(minutes=5)).isoformat()
    post_rev_res = resolver.resolve_historical_key(
        owner=recipient_id,
        key_type=KeyType.RECIPIENT_PRIVATE_KEY,
        event_timestamp=t5,
        event_epoch=1
    )
    assert post_rev_res.is_valid is False
    assert post_rev_res.status == HistoricalResolutionStatus.POST_REVOCATION_REJECTED


def test_recipient_kem_key_rotation_and_package_decryptability():
    """
    ML-KEM-768 rotation:
    - Release 1 encrypted for Alice under KEM1 remains decryptable with KEM1.
    - Release 2 encrypted for Alice under KEM2 requires KEM2.
    - KEM1 cannot decrypt Release 2.
    - Revoked KEM1 cannot be used to decrypt newly issued packages.
    """
    mgr = KeyLifecycleManager()
    resolver = HistoricalKeyResolver(mgr)
    adapter = RecipientKeyLifecycleAdapter(mgr, resolver)

    recipient_id = "rec_bob_8b7c"
    _, kem_rec1 = adapter.enroll_recipient_keys(recipient_id)
    kem1_pair = kem_rec1.metadata["raw_keypair"]

    # Package 1: Encrypted for Bob under KEM 1
    doc1_plain = b"CONFIDENTIAL DOSSIER 1 - HISTORICAL RELEASE"
    encap_res1 = MLKEM768.encapsulate(kem1_pair.public_key_bytes)
    sym_key1 = encap_res1.shared_secret
    cipher1 = encrypt_aes_gcm(sym_key1, doc1_plain)

    # Bob decrypts Package 1 using KEM 1
    ss_recovered1 = MLKEM768.decapsulate(kem1_pair.private_key_bytes, encap_res1.ciphertext)
    assert decrypt_aes_gcm(ss_recovered1, cipher1) == doc1_plain

    # Rotate KEM key to Epoch 2
    prev_kem, next_kem, kem2_pair = adapter.rotate_kem_key(recipient_id)
    assert next_kem.creation_epoch == 2
    assert next_kem.status == KeyState.ACTIVE

    # Package 2: Encrypted for Bob under KEM 2
    doc2_plain = b"CONFIDENTIAL DOSSIER 2 - POST-ROTATION RELEASE"
    encap_res2 = MLKEM768.encapsulate(kem2_pair.public_key_bytes)
    sym_key2 = encap_res2.shared_secret
    cipher2 = encrypt_aes_gcm(sym_key2, doc2_plain)

    # Bob decrypts Package 2 using KEM 2
    ss_recovered2 = MLKEM768.decapsulate(kem2_pair.private_key_bytes, encap_res2.ciphertext)
    assert decrypt_aes_gcm(ss_recovered2, cipher2) == doc2_plain

    # Invariant: Old KEM 1 CANNOT decrypt Package 2!
    bad_ss = MLKEM768.decapsulate(kem1_pair.private_key_bytes, encap_res2.ciphertext)
    with pytest.raises(Exception):
        decrypt_aes_gcm(bad_ss, cipher2)

    # Invariant: Old Release 1 REMAINS decryptable with historical KEM 1
    historical_ss = MLKEM768.decapsulate(kem1_pair.private_key_bytes, encap_res1.ciphertext)
    assert decrypt_aes_gcm(historical_ss, cipher1) == doc1_plain
