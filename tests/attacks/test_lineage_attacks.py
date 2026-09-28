"""
SIH26237 - Adversarial Copy Lineage Attack Suite
Implements and validates 20 rigorous attack scenarios (A through T):
- A: Forged Child Copy
- B: Wrong Parent Reference
- C: Modified Parent ID
- D: Replayed Forwarding Receipt
- E: Replayed Export Receipt
- F: Duplicate Events Rejection
- G: Reordered Events / Tampered Hash Chain
- H: Forged Actor Signature
- I: Forged Device ID
- J: Session Substitution
- K: Export Without Re-fingerprint
- L: Lineage Fork Attack
- M: Lineage Merge / Cycle Loop Attack
- N: Cross-Document Substitution
- O: Cross-Release Substitution
- P: Stale Epoch / Expired Session Attack
- Q: Offline Child Dissemination
- R: Bitstream Duplication (Exact Copy Limit)
- S: Screenshot Outside Viewer
- T: Raw File Exfiltration / Physical Print Leak
"""

import pytest
import os
import base64
import hashlib
from datetime import datetime, timezone, timedelta

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
    DeviceAttestationStatus,
    generate_copy_id,
)
from core.lineage.storage import LineageStorage
from core.lineage.verification import LineageVerifier
from core.lineage.service import LineageService
from core.lineage.viewer import ControlledViewer
from core.lineage.device import LocalSoftwareDeviceProvider


# --- Scenario A: Forged Child Copy ---
def test_scenario_a_forged_child_copy():
    storage = LineageStorage()
    service = LineageService(storage)
    root = service.create_document_root(b"Secret Master")

    # Attacker invents a child copy without parent issuance
    forged_copy = CopyInstance(
        copy_id="cpy_forged_child_1234567890abcdef",
        parent_copy_id="cpy_non_existent_parent",
        document_id=root.document_id,
        recipient_principal_id="rec_attacker",
        lineage_depth=1
    )
    storage.store_copy(forged_copy)

    proof = service.get_lineage(forged_copy.copy_id)
    assert proof.is_valid is False
    assert proof.forensic_boundary_state == ForensicBoundaryState.LINEAGE_BROKEN
    assert "Broken ancestry" in (proof.break_reason or "")


# --- Scenario B: Wrong Parent Reference ---
def test_scenario_b_wrong_parent_reference():
    storage = LineageStorage()
    service = LineageService(storage)
    root1 = service.create_document_root(b"Doc 1")
    root2 = service.create_document_root(b"Doc 2")

    c1 = service.issue_initial_copy(root1.document_id, "rec_alice")
    c2 = service.issue_initial_copy(root2.document_id, "rec_bob")

    # Attacker tries to make c3 a child of c1, but assigns it to Doc 2
    forged_child = CopyInstance(
        copy_id="cpy_wrong_parent_child",
        parent_copy_id=c1.copy_id,  # From Doc 1
        document_id=root2.document_id,  # Assigned to Doc 2
        lineage_depth=1
    )
    storage.store_copy(forged_child)

    proof = service.get_lineage(forged_child.copy_id)
    assert proof.is_valid is False
    assert proof.forensic_boundary_state == ForensicBoundaryState.LINEAGE_BROKEN
    assert "Cross-document" in (proof.break_reason or "")


# --- Scenario C: Modified Parent ID ---
def test_scenario_c_modified_parent_id():
    storage = LineageStorage()
    service = LineageService(storage)
    root = service.create_document_root(b"Doc Master")
    c0 = service.issue_initial_copy(root.document_id, "rec_alice")
    kp = MLDSA65.generate_keypair()
    c1, _, _ = service.share_copy(c0.copy_id, "rec_alice", "rec_bob", signer_keypair=(kp.private_key_bytes, kp.public_key_bytes))

    # Attacker mutates parent_copy_id to point to another ID
    c1.parent_copy_id = "cpy_mutated_parent_id"
    storage.store_copy(c1)

    proof = service.get_lineage(c1.copy_id)
    assert proof.is_valid is False
    assert proof.forensic_boundary_state == ForensicBoundaryState.LINEAGE_BROKEN


# --- Scenario D: Replayed Forwarding Receipt ---
def test_scenario_d_replayed_forwarding_receipt():
    storage = LineageStorage()
    service = LineageService(storage)
    root = service.create_document_root(b"Doc Master")
    c0 = service.issue_initial_copy(root.document_id, "rec_alice")
    kp = MLDSA65.generate_keypair()
    c1, fwd_event, _ = service.share_copy(c0.copy_id, "rec_alice", "rec_bob", signer_keypair=(kp.private_key_bytes, kp.public_key_bytes))

    # Attempting to store the same forwarding event again must trigger replay rejection
    with pytest.raises(ValueError, match="Replay detected"):
        storage.store_forwarding_event(fwd_event)


# --- Scenario E: Replayed Export Receipt ---
def test_scenario_e_replayed_export_receipt():
    storage = LineageStorage()
    service = LineageService(storage)
    root = service.create_document_root(b"Doc Master")
    c0 = service.issue_initial_copy(root.document_id, "rec_alice")
    session = service.start_access_session(c0.copy_id)

    kp = MLDSA65.generate_keypair()
    c1, exp_event, _ = service.export_copy(
        session_id=session.session_id,
        export_format=ExportFormat.PDF,
        signer_keypair=(kp.private_key_bytes, kp.public_key_bytes)
    )

    # Attempting to store the same export event again must trigger replay rejection
    with pytest.raises(ValueError, match="Replay detected"):
        storage.store_export_event(exp_event)


# --- Scenario F: Duplicate Events Rejection ---
def test_scenario_f_duplicate_events():
    storage = LineageStorage()
    ev = ForwardingEvent(
        forwarding_event_id="fwd_dup_test",
        parent_copy_id="cpy_p",
        child_copy_id="cpy_c",
        actor_principal_id="rec_actor",
        recipient_principal_id="rec_target",
        previous_event_hash="0" * 64
    )
    storage.store_forwarding_event(ev)

    # Re-inserting exact same event raises ValueError
    with pytest.raises(ValueError, match="Replay detected"):
        storage.store_forwarding_event(ev)


# --- Scenario G: Reordered Events / Tampered Hash Chain ---
def test_scenario_g_reordered_events_tampered_hash():
    storage = LineageStorage()
    service = LineageService(storage)
    root = service.create_document_root(b"Doc Master")
    c0 = service.issue_initial_copy(root.document_id, "rec_alice")
    kp = MLDSA65.generate_keypair()
    c1, fwd_event, _ = service.share_copy(c0.copy_id, "rec_alice", "rec_bob", signer_keypair=(kp.private_key_bytes, kp.public_key_bytes))

    # Attacker alters the signed_event_hash
    fwd_event.signed_event_hash = "f" * 64

    ok, err = service.verifier.verify_forwarding_event(fwd_event)
    assert ok is False
    assert "Event hash mismatch" in err


# --- Scenario H: Forged Actor Signature ---
def test_scenario_h_forged_actor_signature():
    storage = LineageStorage()
    service = LineageService(storage)
    root = service.create_document_root(b"Doc Master")
    c0 = service.issue_initial_copy(root.document_id, "rec_alice")

    # Honest Alice keypair vs Mallory forged keypair
    kp_alice = MLDSA65.generate_keypair()
    kp_mallory = MLDSA65.generate_keypair()

    # Share claims to be from Alice, but is signed by Mallory's private key
    c1, fwd_event, _ = service.share_copy(
        parent_copy_id=c0.copy_id,
        actor_principal_id="rec_alice",
        target_recipient_principal_id="rec_bob",
        signer_keypair=(kp_mallory.private_key_bytes, kp_alice.public_key_bytes)  # signature doesn't match claimed pubkey!
    )

    ok, err = service.verifier.verify_forwarding_event(fwd_event)
    assert ok is False
    assert "signature verification failed" in err.lower()


# --- Scenario I: Forged Device ID ---
def test_scenario_i_forged_device_id():
    provider = LocalSoftwareDeviceProvider()
    dev = provider.enroll_device()

    # Attacker tries to attest a device with invalid ID
    with pytest.raises(ValueError, match="not enrolled"):
        provider.attest_device("dev_fake_spoofed_device", b"nonce")


# --- Scenario J: Session Substitution ---
def test_scenario_j_session_substitution():
    storage = LineageStorage()
    service = LineageService(storage)
    viewer = ControlledViewer(service)
    doc_bytes = b"Secret Document"
    root = service.create_document_root(doc_bytes)
    c0 = service.issue_initial_copy(root.document_id, "rec_alice")
    viewer.register_master_document(root.document_id, doc_bytes)

    session = viewer.open_session(c0.copy_id, identity_id="id_alice")

    # Attacker tries to export using a non-existent or wrong session ID
    with pytest.raises(PermissionError):
        viewer.controlled_export("ses_fake_attacker_session", ExportFormat.PDF)


# --- Scenario K: Export Without Re-fingerprint ---
def test_scenario_k_export_without_refingerprint():
    storage = LineageStorage()
    service = LineageService(storage)
    viewer = ControlledViewer(service)
    doc_bytes = b"Financial Projections"
    root = service.create_document_root(doc_bytes)
    c0 = service.issue_initial_copy(root.document_id, "rec_alice")
    viewer.register_master_document(root.document_id, doc_bytes)

    session = viewer.open_session(c0.copy_id, identity_id="id_alice")

    # Viewer controlled export MUST produce child copy with non-empty fingerprint
    _, child_copy, exp_event, _ = viewer.controlled_export(session.session_id, ExportFormat.PDF)
    assert child_copy.embedded_fingerprint_reference is not None
    assert len(child_copy.embedded_fingerprint_reference) > 0
    assert child_copy.lineage_depth == 1


# --- Scenario L: Lineage Fork Attack ---
def test_scenario_l_lineage_fork_attack():
    storage = LineageStorage()
    service = LineageService(storage)
    root = service.create_document_root(b"Doc Master")
    c0 = service.issue_initial_copy(root.document_id, "rec_alice")

    kp = MLDSA65.generate_keypair()
    # Fork 1: Alice shares to Bob
    c1, _, _ = service.share_copy(c0.copy_id, "rec_alice", "rec_bob", signer_keypair=(kp.private_key_bytes, kp.public_key_bytes))
    # Fork 2: Alice shares to Charlie
    c2, _, _ = service.share_copy(c0.copy_id, "rec_alice", "rec_charlie", signer_keypair=(kp.private_key_bytes, kp.public_key_bytes))

    # Both children must resolve valid independent lineage proofs back to root c0
    p1 = service.get_lineage(c1.copy_id)
    p2 = service.get_lineage(c2.copy_id)

    assert p1.is_valid is True and p1.last_known_controlled_holder == "rec_bob"
    assert p2.is_valid is True and p2.last_known_controlled_holder == "rec_charlie"
    assert c1.copy_id != c2.copy_id


# --- Scenario M: Lineage Merge / Cycle Loop Attack ---
def test_scenario_m_lineage_merge_cycle():
    storage = LineageStorage()
    service = LineageService(storage)
    root = service.create_document_root(b"Doc Master")
    c0 = service.issue_initial_copy(root.document_id, "rec_alice")

    kp = MLDSA65.generate_keypair()
    c1, _, _ = service.share_copy(c0.copy_id, "rec_alice", "rec_bob", signer_keypair=(kp.private_key_bytes, kp.public_key_bytes))

    # Malicious cycle: c0 parent set to c1
    c0.parent_copy_id = c1.copy_id
    storage.store_copy(c0)

    proof = service.get_lineage(c1.copy_id)
    assert proof.is_valid is False
    assert proof.forensic_boundary_state == ForensicBoundaryState.LINEAGE_BROKEN
    assert ("cycle" in (proof.break_reason or "").lower() or "depth" in (proof.break_reason or "").lower())


# --- Scenario N: Cross-Document Substitution ---
def test_scenario_n_cross_document_substitution():
    storage = LineageStorage()
    service = LineageService(storage)
    root_a = service.create_document_root(b"Doc A")
    root_b = service.create_document_root(b"Doc B")

    ca = service.issue_initial_copy(root_a.document_id, "rec_alice")
    cb = service.issue_initial_copy(root_b.document_id, "rec_bob")

    # Attempt derivation with mismatched root
    verifier = service.verifier
    ok, err = verifier.verify_copy_derivation(ca, None, root_b)
    assert ok is False
    assert "Cross-document" in err


# --- Scenario O: Cross-Release Substitution ---
def test_scenario_o_cross_release_substitution():
    storage = LineageStorage()
    service = LineageService(storage)
    root = service.create_document_root(b"Doc")
    ca = service.issue_initial_copy(root.document_id, "rec_alice", release_id="rel_2026_01")
    cb = service.issue_initial_copy(root.document_id, "rec_bob", release_id="rel_2026_02")

    assert ca.release_id != cb.release_id
    assert ca.copy_id != cb.copy_id


# --- Scenario P: Stale Epoch / Expired Session Attack ---
def test_scenario_p_expired_session_attack():
    storage = LineageStorage()
    service = LineageService(storage)
    viewer = ControlledViewer(service)
    doc_bytes = b"Doc Content"
    root = service.create_document_root(doc_bytes)
    c0 = service.issue_initial_copy(root.document_id, "rec_alice")
    viewer.register_master_document(root.document_id, doc_bytes)

    # Session created with negative/expired duration
    session = viewer.open_session(c0.copy_id, expires_in_seconds=-10)
    session.is_active = False

    with pytest.raises(PermissionError):
        viewer.render_view(session.session_id)


# --- Scenario Q: Offline Child Dissemination ---
def test_scenario_q_offline_child_dissemination():
    storage = LineageStorage()
    service = LineageService(storage)
    root = service.create_document_root(b"Contract Spec")
    c0 = service.issue_initial_copy(root.document_id, "rec_alice")

    # Alice gives document offline to an unrecorded party (no ForwardingEvent generated)
    # Target leak artifact only possesses c0 markers
    leak_fingerprint = c0.embedded_fingerprint_reference

    # Lineage lookup for c0 returns Alice as last known controlled holder
    proof = service.get_lineage(c0.copy_id)
    assert proof.is_valid is True
    assert proof.last_known_controlled_holder == "rec_alice"
    assert proof.highest_attribution_level == ForensicAttributionLevel.LEVEL_2_ORIGINAL_RECIPIENT_IDENTIFIED


# --- Scenario R: Bitstream Duplication (Exact Copy Limit) ---
def test_scenario_r_bitstream_duplication():
    storage = LineageStorage()
    service = LineageService(storage)
    root = service.create_document_root(b"Classified Operations")
    c0 = service.issue_initial_copy(root.document_id, "rec_bob")

    # Attacker makes 1,000,000 exact bitstream copies
    # When an exact clone leaks, AegisTrace attributes to Bob (the last known holder)
    # and strictly refrains from inventing downstream identities
    proof = service.get_lineage(c0.copy_id)
    assert proof.last_known_controlled_holder == "rec_bob"
    # Never claims Level 5 without external corroboration
    assert proof.highest_attribution_level in (
        ForensicAttributionLevel.LEVEL_2_ORIGINAL_RECIPIENT_IDENTIFIED,
        ForensicAttributionLevel.LEVEL_3_COPY_INSTANCE_IDENTIFIED,
    )


# --- Scenario S: Screenshot Outside Viewer ---
def test_scenario_s_screenshot_outside_viewer():
    storage = LineageStorage()
    service = LineageService(storage)
    viewer = ControlledViewer(service)
    doc_bytes = b"M&A Acquisition Target Details"
    root = service.create_document_root(doc_bytes)
    c0 = service.issue_initial_copy(root.document_id, "rec_alice")
    viewer.register_master_document(root.document_id, doc_bytes)

    session = viewer.open_session(c0.copy_id, identity_id="id_alice_executive")
    render_info = viewer.render_view(session.session_id)

    # Attacker captures screen outside viewer
    # The screen has dynamic watermark 'sf_...'
    session_fp = session.session_fingerprint_key
    found_session = service.find_session_by_fingerprint(session_fp)

    assert found_session is not None
    assert found_session.session_id == session.session_id
    assert found_session.copy_id == c0.copy_id
    assert found_session.identity_id == "id_alice_executive"


# --- Scenario T: Raw File Exfiltration / Physical Print Leak ---
def test_scenario_t_raw_file_exfiltration_physical_print():
    storage = LineageStorage()
    service = LineageService(storage)
    root = service.create_document_root(b"Architectural Blueprints")
    c0 = service.issue_initial_copy(root.document_id, "rec_charlie")

    # Adversary physically prints document and leaves paper at an uncontrolled café
    # Artifact recovered is analyzed:
    proof = service.get_lineage(c0.copy_id)
    assert proof.is_valid is True
    assert proof.last_known_controlled_holder == "rec_charlie"
    # Forensics state reflects boundary condition
    assert proof.forensic_boundary_state in (
        ForensicBoundaryState.ATTRIBUTED_TO_CONTROLLED_ACTOR,
        ForensicBoundaryState.LAST_KNOWN_HOLDER,
        ForensicBoundaryState.LINEAGE_CONTINUES,
    )
    # Must not claim Level 5 human guilt without corroborating evidence
    assert proof.highest_attribution_level != ForensicAttributionLevel.LEVEL_5_HUMAN_IDENTITY_RESOLVED
