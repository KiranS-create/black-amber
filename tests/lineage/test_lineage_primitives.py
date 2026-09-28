"""
SIH26237 - Active Cryptographic Copy Lineage: Primitives & Service Tests
Validates DocumentRoot, CopyInstance, AccessSession, ForwardingEvent,
ExportEvent, and LineageService orchestration.
"""

import pytest
import os
import hashlib
from datetime import datetime, timezone

from core.crypto.signatures import MLDSA65
from core.lineage.models import (
    DocumentRoot,
    CopyInstance,
    AccessSession,
    ForwardingEvent,
    ExportEvent,
    LineageEdge,
    LineageProof,
    TransitionActionType,
    ExportFormat,
    ForensicAttributionLevel,
    ForensicBoundaryState,
    generate_copy_id,
)
from core.lineage.storage import LineageStorage
from core.lineage.verification import LineageVerifier
from core.lineage.service import LineageService


def test_document_root_creation_and_hashing():
    storage = LineageStorage()
    service = LineageService(storage)

    doc_bytes = b"%PDF-1.7 Master Plaintext Document for Lineage Testing"
    root = service.create_document_root(doc_bytes, metadata={"classification": "RESTRICTED"})

    assert root.document_id.startswith("doc_root_")
    assert root.canonical_hash == hashlib.sha256(doc_bytes).hexdigest()
    assert root.byte_size == len(doc_bytes)
    assert root.status == "ACTIVE"
    assert storage.get_document_root(root.document_id) is not None


def test_copy_id_derivation_deterministic_and_unique():
    canonical_hash = "a" * 64
    ts = datetime.now(timezone.utc).isoformat()
    nonce1 = "nonce_1"
    nonce2 = "nonce_2"

    cid1 = generate_copy_id(canonical_hash, None, "rec_alice", ts, nonce1)
    cid1_again = generate_copy_id(canonical_hash, None, "rec_alice", ts, nonce1)
    cid2 = generate_copy_id(canonical_hash, None, "rec_alice", ts, nonce2)

    assert cid1 == cid1_again
    assert cid1 != cid2
    assert cid1.startswith("cpy_")
    assert len(cid1) == 36  # "cpy_" + 32 chars


def test_issue_initial_copy():
    storage = LineageStorage()
    service = LineageService(storage)
    root = service.create_document_root(b"Sample PDF bytes")

    copy = service.issue_initial_copy(
        document_id=root.document_id,
        recipient_principal_id="rec_alice_001",
        release_id="rel_2026_01",
        embedded_fingerprint_reference="fp_tardos_alice"
    )

    assert copy.parent_copy_id is None
    assert copy.lineage_depth == 0
    assert copy.recipient_principal_id == "rec_alice_001"
    assert copy.status == "ACTIVE"

    proof = service.get_lineage(copy.copy_id)
    assert proof.is_valid is True
    assert proof.highest_attribution_level == ForensicAttributionLevel.LEVEL_2_ORIGINAL_RECIPIENT_IDENTIFIED
    assert proof.forensic_boundary_state == ForensicBoundaryState.ATTRIBUTED_TO_CONTROLLED_ACTOR
    assert proof.last_known_controlled_holder == "rec_alice_001"


def test_start_access_session():
    storage = LineageStorage()
    service = LineageService(storage)
    root = service.create_document_root(b"Confidential Report")
    copy = service.issue_initial_copy(root.document_id, "rec_bob_002")

    session = service.start_access_session(
        copy_id=copy.copy_id,
        identity_id="id_bob_enterprise",
        device_key_id="dkey_laptop_bob"
    )

    assert session.session_id.startswith("ses_")
    assert session.session_fingerprint_key.startswith("sf_")
    assert session.is_active is True
    assert session.copy_id == copy.copy_id

    # Lookup by fingerprint
    found = service.find_session_by_fingerprint(session.session_fingerprint_key)
    assert found is not None
    assert found.session_id == session.session_id


def test_controlled_share_forwarding_receipt():
    storage = LineageStorage()
    service = LineageService(storage)
    root = service.create_document_root(b"Target Master Doc")
    alice_copy = service.issue_initial_copy(root.document_id, "rec_alice")

    kp_alice = MLDSA65.generate_keypair()
    alice_pub, alice_priv = kp_alice.public_key_bytes, kp_alice.private_key_bytes

    child_copy, fwd_event, edge = service.share_copy(
        parent_copy_id=alice_copy.copy_id,
        actor_principal_id="rec_alice",
        target_recipient_principal_id="rec_carol",
        signer_keypair=(alice_priv, alice_pub),
        action_type=TransitionActionType.CONTROLLED_SHARE,
        sender_device_id="dev_alice_workstation"
    )

    assert child_copy.parent_copy_id == alice_copy.copy_id
    assert child_copy.lineage_depth == 1
    assert child_copy.recipient_principal_id == "rec_carol"
    assert fwd_event.signature_b64 is not None

    # Verify signature
    ok_sig, err_sig = service.verifier.verify_forwarding_event(fwd_event)
    assert ok_sig is True
    assert err_sig is None

    # Verify lineage proof from root to Carol
    proof = service.get_lineage(child_copy.copy_id)
    assert proof.is_valid is True
    assert proof.highest_attribution_level == ForensicAttributionLevel.LEVEL_4_LINEAGE_IDENTIFIED
    assert proof.forensic_boundary_state == ForensicBoundaryState.LINEAGE_CONTINUES
    assert proof.last_known_controlled_holder == "rec_carol"
    assert len(proof.path) == 1  # 1 hop: Alice -> Carol
    assert proof.details["hop_count"] == 1


def test_export_copy_receipt_and_refingerprinting():
    storage = LineageStorage()
    service = LineageService(storage)
    root = service.create_document_root(b"Sensitive Strategy Doc")
    alice_copy = service.issue_initial_copy(root.document_id, "rec_alice")
    session = service.start_access_session(alice_copy.copy_id, "id_alice")

    kp = MLDSA65.generate_keypair()
    key_pub, key_priv = kp.public_key_bytes, kp.private_key_bytes

    child_copy, exp_event, edge = service.export_copy(
        session_id=session.session_id,
        export_format=ExportFormat.PDF,
        actor_principal_id="rec_alice",
        signer_keypair=(key_priv, key_pub),
        device_id="dev_workstation_export"
    )

    assert child_copy.parent_copy_id == alice_copy.copy_id
    assert child_copy.lineage_depth == 1
    assert child_copy.status == "EXPORTED"
    assert exp_event.signature_b64 is not None
    assert edge.transition_type == TransitionActionType.EXPORT

    ok_sig, err = service.verifier.verify_export_event(exp_event)
    assert ok_sig is True

    proof = service.get_lineage(child_copy.copy_id)
    assert proof.is_valid is True
    assert proof.highest_attribution_level == ForensicAttributionLevel.LEVEL_4_LINEAGE_IDENTIFIED


def test_multi_hop_lineage_chain():
    storage = LineageStorage()
    service = LineageService(storage)
    root = service.create_document_root(b"Executive Multi-Hop Memo")

    # Hop 0: Root issuance -> Alice
    c0 = service.issue_initial_copy(root.document_id, "rec_alice")
    kp0 = MLDSA65.generate_keypair()
    pub0, priv0 = kp0.public_key_bytes, kp0.private_key_bytes

    # Hop 1: Alice -> Bob
    c1, _, _ = service.share_copy(c0.copy_id, "rec_alice", "rec_bob", signer_keypair=(priv0, pub0))
    kp1 = MLDSA65.generate_keypair()
    pub1, priv1 = kp1.public_key_bytes, kp1.private_key_bytes

    # Hop 2: Bob -> Charlie
    c2, _, _ = service.share_copy(c1.copy_id, "rec_bob", "rec_charlie", signer_keypair=(priv1, pub1))
    kp2 = MLDSA65.generate_keypair()
    pub2, priv2 = kp2.public_key_bytes, kp2.private_key_bytes

    # Hop 3: Charlie -> Dave
    c3, _, _ = service.share_copy(c2.copy_id, "rec_charlie", "rec_dave", signer_keypair=(priv2, pub2))

    assert c3.lineage_depth == 3

    proof = service.get_lineage(c3.copy_id)
    assert proof.is_valid is True
    assert proof.highest_attribution_level == ForensicAttributionLevel.LEVEL_4_LINEAGE_IDENTIFIED
    assert proof.ancestor_copy_ids == [c0.copy_id, c1.copy_id, c2.copy_id, c3.copy_id]
    assert proof.last_known_controlled_holder == "rec_dave"
    assert len(proof.path) == 3
    assert proof.details["hop_count"] == 3


def test_lineage_hash_chain_continuity():
    """
    Asserts SEC-LIN-002: Transition receipts are chained cryptographically
    (H_prev = H_event(prev_copy)) rather than static 0^64.
    """
    storage = LineageStorage()
    service = LineageService(storage)
    root = service.create_document_root(b"Chained Event Proof Document")

    # Hop 0: Root issuance -> Alice
    c0 = service.issue_initial_copy(root.document_id, "rec_alice")
    kp0 = MLDSA65.generate_keypair()

    # Hop 1: Alice -> Bob
    c1, fwd1, _ = service.share_copy(
        c0.copy_id, "rec_alice", "rec_bob",
        signer_keypair=(kp0.private_key_bytes, kp0.public_key_bytes)
    )

    # First hop must chain back to root canonical hash
    assert fwd1.previous_event_hash == root.canonical_hash
    h1 = fwd1.compute_event_hash()

    # Hop 2: Bob -> Charlie
    kp1 = MLDSA65.generate_keypair()
    c2, fwd2, _ = service.share_copy(
        c1.copy_id, "rec_bob", "rec_charlie",
        signer_keypair=(kp1.private_key_bytes, kp1.public_key_bytes)
    )

    # Second hop must chain back to first hop's event hash
    assert fwd2.previous_event_hash == h1
    h2 = fwd2.compute_event_hash()

    # Hop 3: Export by Charlie
    session = service.start_access_session(c2.copy_id, "id_charlie")
    kp2 = MLDSA65.generate_keypair()
    c3, exp1, _ = service.export_copy(
        session_id=session.session_id,
        export_format=ExportFormat.PDF,
        actor_principal_id="rec_charlie",
        signer_keypair=(kp2.private_key_bytes, kp2.public_key_bytes)
    )

    # Export event must chain back to second hop's event hash
    assert exp1.previous_event_hash == h2

