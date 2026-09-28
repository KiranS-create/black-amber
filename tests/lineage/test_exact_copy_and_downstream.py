"""
SIH26237 - Exact Copy Lineage & Downstream Actor Invariant Test
Validates the fundamental impossibility boundary:
Alice -> Bob -> Unknown X -> Unknown Y -> Leak
System strictly attributes custody up to Bob (last known controlled holder),
flags UNKNOWN_DOWNSTREAM_ACTOR / LAST_KNOWN_HOLDER,
limits attribution to LEVEL_4_LINEAGE_IDENTIFIED,
and refuses to frame Bob or invent downstream identities without evidence.
"""

import pytest
import os
import hashlib
from datetime import datetime, timezone

from core.crypto.signatures import MLDSA65
from core.lineage.models import (
    DocumentRoot,
    CopyInstance,
    ForwardingEvent,
    TransitionActionType,
    ForensicAttributionLevel,
    ForensicBoundaryState,
)
from core.lineage.storage import LineageStorage
from core.lineage.service import LineageService
from core.attribution.evidence import (
    EvidenceBundle,
    LineageObservation,
    WatermarkObservation,
    AttributionState,
    EvidenceConfidenceLevel,
    EvidenceFamily,
    TargetBinding,
)
from core.attribution.fusion import EvidenceFusionEngine


def test_exact_bitwise_copy_uncontrolled_downstream_chain():
    """
    Scenario:
    1. Master document created.
    2. Initial copy issued to Alice (controlled).
    3. Alice shares to Bob inside AegisTrace (controlled forwarding receipt signed with ML-DSA-65).
    4. Bob extracts or sends exact bitstream out-of-band to Unknown X.
    5. Unknown X passes exact bitstream to Unknown Y.
    6. Unknown Y leaks the exact bitstream on the public internet.
    
    Forensic Invariants:
    - Leak inspection detects Bob's copy instance fingerprint.
    - Active Copy Lineage traces ancestry: Root -> Alice -> Bob.
    - Last known controlled holder = Bob.
    - Downstream actors X and Y are UNCONTROLLED and cannot be proven by artifact alone.
    - System reports LAST_KNOWN_HOLDER / UNKNOWN_DOWNSTREAM_ACTOR.
    - System limits attribution level to LEVEL_4_LINEAGE_IDENTIFIED (NEVER LEVEL_5).
    - System does NOT frame Bob as having personally committed the leak.
    """
    storage = LineageStorage()
    service = LineageService(storage)

    # 1. Master Root
    master_bytes = b"%PDF-1.7 Master Blueprint Document with Embedded Secrets"
    root = service.create_document_root(master_bytes)

    # 2. Initial copy to Alice
    c_alice = service.issue_initial_copy(
        document_id=root.document_id,
        recipient_principal_id="rec_alice_corp",
        release_id="rel_2026_defense",
        embedded_fingerprint_reference="fp_alice_mk1"
    )

    # 3. Controlled Forwarding: Alice -> Bob
    kp_alice = MLDSA65.generate_keypair()
    c_bob, fwd_event, edge = service.share_copy(
        parent_copy_id=c_alice.copy_id,
        actor_principal_id="rec_alice_corp",
        target_recipient_principal_id="rec_bob_contractor",
        signer_keypair=(kp_alice.private_key_bytes, kp_alice.public_key_bytes),
        action_type=TransitionActionType.CONTROLLED_SHARE,
        embedded_fingerprint_reference="fp_bob_mk2"
    )

    # 4 & 5. Bob passes exact bitstream to X -> Y -> Public Leak
    # The physical/digital leaked artifact carries Bob's embedded fingerprint
    leaked_fingerprint = "fp_bob_mk2"

    # 6. AegisTrace resolves copy from leaked fingerprint
    detected_copy = service.find_copy_by_fingerprint(leaked_fingerprint)
    assert detected_copy is not None
    assert detected_copy.copy_id == c_bob.copy_id

    # Lineage Verification
    lineage_proof = service.get_lineage(detected_copy.copy_id)
    assert lineage_proof.is_valid is True
    assert lineage_proof.root_document_id == root.document_id
    assert lineage_proof.ancestor_copy_ids == [c_alice.copy_id, c_bob.copy_id]
    assert lineage_proof.last_known_controlled_holder == "rec_bob_contractor"

    # Attribution level must be LEVEL_4, strictly NOT LEVEL_5
    assert lineage_proof.highest_attribution_level == ForensicAttributionLevel.LEVEL_4_LINEAGE_IDENTIFIED
    assert lineage_proof.highest_attribution_level != ForensicAttributionLevel.LEVEL_5_HUMAN_IDENTITY_RESOLVED

    # Now verify Multi-Channel Evidence Fusion Integration
    # Create LineageObservation representing the uncontrolled leak state
    lineage_obs = LineageObservation(
        source_id="lineage_tracer_01",
        title="Active Cryptographic Copy Lineage Analysis",
        copy_id=c_bob.copy_id,
        parent_copy_id=c_alice.copy_id,
        lineage_depth=1,
        attribution_level=ForensicAttributionLevel.LEVEL_4_LINEAGE_IDENTIFIED,
        boundary_state=ForensicBoundaryState.LAST_KNOWN_HOLDER,
        last_known_holder="rec_bob_contractor",
        is_lineage_valid=True,
        session_id=None,
        telemetry_corroborated=False,
        proof_details=lineage_proof.model_dump(),
        target_binding=TargetBinding(
            document_id=root.document_id,
            release_id="rel_2026_defense",
            recipient_id="rec_bob_contractor",
            original_document_hash=root.canonical_hash
        ),
        primary_candidate="rec_bob_contractor",
        log_likelihood_ratio=3.5,
        reliability_prior=1.0,
        effective_reliability=1.0,
    )

    # Watermark observation corroborating Bob's fingerprint
    watermark_obs = WatermarkObservation(
        source_id="watermark_detector_01",
        title="DSSS Watermark Recovery",
        target_binding=TargetBinding(
            document_id=root.document_id,
            release_id="rel_2026_defense",
            recipient_id="rec_bob_contractor",
            original_document_hash=root.canonical_hash
        ),
        primary_candidate="rec_bob_contractor",
        log_likelihood_ratio=4.0,
        reliability_prior=0.95,
        effective_reliability=0.95,
    )

    bundle = EvidenceBundle(
        bundle_id="bnd_leak_uncontrolled_chain",
        target_binding=TargetBinding(
            document_id=root.document_id,
            release_id="rel_2026_defense"
        ),
        observations=[lineage_obs, watermark_obs]
    )

    fusion_engine = EvidenceFusionEngine()
    result = fusion_engine.fuse(bundle)

    # Verify fusion result adheres strictly to the honesty invariant
    assert result.state == AttributionState.ATTRIBUTED
    assert result.top_candidate_id == "rec_bob_contractor"
    assert result.forensic_attribution_level == ForensicAttributionLevel.LEVEL_4_LINEAGE_IDENTIFIED
    assert result.forensic_boundary_state == ForensicBoundaryState.LAST_KNOWN_HOLDER
    assert result.last_known_holder == "rec_bob_contractor"
    assert "intermediary not personally accused" in result.summary

    # Under no circumstances does the engine invent Level 5 or frame Bob
    assert result.forensic_attribution_level != ForensicAttributionLevel.LEVEL_5_HUMAN_IDENTITY_RESOLVED


def test_lineage_telemetry_corroboration_promotes_to_level_5():
    """
    Asserts SEC-LIN-004: When an uncontrolled leak is corroborated by external
    telemetry (e.g. EDR screenshot, USB exfiltration log), the evidence fusion
    engine legitimately elevates the decision from LEVEL_4 to LEVEL_5_HUMAN_IDENTITY_RESOLVED.
    """
    root_doc_id = "doc_root_corroborated_test"
    c_bob_id = "cpy_bob_corroborated_1234567890ab"

    # Lineage observation with telemetry_corroborated=True
    lineage_obs = LineageObservation(
        source_id="lineage_tracer_02",
        title="Active Cryptographic Copy Lineage with EDR Corroboration",
        copy_id=c_bob_id,
        lineage_depth=1,
        attribution_level=ForensicAttributionLevel.LEVEL_4_LINEAGE_IDENTIFIED,
        boundary_state=ForensicBoundaryState.ATTRIBUTED_TO_CONTROLLED_ACTOR,
        last_known_holder="rec_bob_contractor",
        is_lineage_valid=True,
        telemetry_corroborated=True,  # External EDR/CASB match confirmed
        target_binding=TargetBinding(
            document_id=root_doc_id,
            recipient_id="rec_bob_contractor",
            original_document_hash="a" * 64
        ),
        primary_candidate="rec_bob_contractor",
        log_likelihood_ratio=4.0,
        reliability_prior=1.0,
        effective_reliability=1.0,
    )

    watermark_obs = WatermarkObservation(
        source_id="watermark_detector_02",
        title="Watermark Signal Corroboration",
        target_binding=TargetBinding(
            document_id=root_doc_id,
            recipient_id="rec_bob_contractor",
            original_document_hash="a" * 64
        ),
        primary_candidate="rec_bob_contractor",
        log_likelihood_ratio=4.5,
        reliability_prior=0.95,
        effective_reliability=0.95,
    )

    bundle = EvidenceBundle(
        bundle_id="bnd_leak_corroborated_level5",
        target_binding=TargetBinding(
            document_id=root_doc_id,
        ),
        observations=[lineage_obs, watermark_obs]
    )

    fusion_engine = EvidenceFusionEngine()
    result = fusion_engine.fuse(bundle)

    assert result.state == AttributionState.ATTRIBUTED
    assert result.top_candidate_id == "rec_bob_contractor"
    # Successfully and legitimately promoted to Level 5
    assert result.forensic_attribution_level == ForensicAttributionLevel.LEVEL_5_HUMAN_IDENTITY_RESOLVED

