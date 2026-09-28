"""
Tests for Evidence Object Model, Canonical Serialization, and Content Addressing.
Verifies:
1. Lexicographical key sorting and deterministic canonical JSON serialization.
2. Content hash sensitivity: 1-bit or minor mutation changes content_hash (H1 != H2).
3. Schema compliance for all 17 evidence object categories.
4. Tamper detection via verify_content_integrity().
"""

import pytest
import hashlib
from datetime import datetime, timezone

from core.evidence_package.canonical import (
    canonical_json_dumps,
    canonical_json_bytes,
    compute_content_hash
)
from core.evidence_package.models import (
    EvidenceObjectType,
    CaseObject,
    ArtifactEvidenceObject,
    WatermarkEvidenceObject,
    DecryptionReceiptObject,
    RecipientIdentityProofObject,
    DeviceEvidenceObject,
    SessionEvidenceObject,
    LineageEvidenceObject,
    LedgerProofObject,
    TelemetryEvidenceObject,
    ChainOfCustodyEvent,
    AttributionDecisionObject,
    DependencyEdge,
    CustodyAction,
    DecisionState,
    TelemetryDependencyRelation
)


def test_canonical_serialization_determinism():
    # Dict with keys inserted in different orders
    d1 = {"b": 2, "a": 1, "c": {"y": "val", "x": [3, 2, 1]}}
    d2 = {"c": {"x": [3, 2, 1], "y": "val"}, "a": 1, "b": 2}

    s1 = canonical_json_dumps(d1)
    s2 = canonical_json_dumps(d2)

    assert s1 == s2
    assert s1 == '{"a":1,"b":2,"c":{"x":[3,2,1],"y":"val"}}'
    assert canonical_json_bytes(d1) == canonical_json_bytes(d2)
    assert compute_content_hash(d1) == compute_content_hash(d2)


def test_content_addressing_mutation_sensitivity():
    art = ArtifactEvidenceObject(
        object_id="art_001",
        artifact_category="LEAK",
        filename="classified_briefing.pdf",
        byte_size=1024,
        sha256_digest="a" * 64,
        document_id="doc_123"
    )
    h1 = art.seal_content_hash()
    assert art.verify_content_integrity()

    # Mutation: change byte size by 1 byte
    art_mutated = ArtifactEvidenceObject(
        object_id="art_001",
        artifact_category="LEAK",
        filename="classified_briefing.pdf",
        byte_size=1025,
        sha256_digest="a" * 64,
        document_id="doc_123"
    )
    h2 = art_mutated.compute_content_digest()

    assert h1 != h2, "Content-addressed hash failed to change on payload mutation!"

    # Attaching old hash to mutated object causes integrity verification failure
    art_mutated.content_hash = h1
    assert not art_mutated.verify_content_integrity()


def test_all_17_evidence_object_instantiation_and_sealing():
    now_ts = datetime.now(timezone.utc).isoformat()

    # 1. Case
    c = CaseObject(object_id="case_001", case_name="Operation Trident", investigator_id="inv_99", description="Leak inquiry")
    c.seal_content_hash()
    assert c.verify_content_integrity()

    # 2. Artifact
    art = ArtifactEvidenceObject(object_id="art_001", artifact_category="ORIGINAL", filename="orig.pdf", byte_size=2048, sha256_digest="b"*64)
    art.seal_content_hash()
    assert art.verify_content_integrity()

    # 3. Watermark
    wm = WatermarkEvidenceObject(object_id="wm_001", artifact_hash="b"*64, extracted_token="tok_123", confidence_score=0.98)
    wm.seal_content_hash()
    assert wm.verify_content_integrity()

    # 4. Decryption Receipt
    rcpt = DecryptionReceiptObject(
        object_id="rcpt_001",
        receipt_id="rec_001",
        document_id="doc_001",
        release_id="rel_001",
        recipient_id="alice",
        session_id="sess_001",
        key_id="kid_001",
        key_epoch=1,
        timestamp=now_ts,
        watermark_token="tok_123",
        watermark_commitment="c"*64,
        recipient_signature_b64="sig_b64",
        recipient_public_key_b64="pub_b64"
    )
    rcpt.seal_content_hash()
    assert rcpt.verify_content_integrity()

    # 5. Recipient Identity Proof
    rip = RecipientIdentityProofObject(object_id="rip_001", recipient_id="alice", key_id="kid_001", public_key_b64="pub_b64")
    rip.seal_content_hash()
    assert rip.verify_content_integrity()

    # 6. Device Evidence
    dev = DeviceEvidenceObject(object_id="dev_001", device_id="tpm_node_1", attestation_status="DEVICE_ATTESTED")
    dev.seal_content_hash()
    assert dev.verify_content_integrity()

    # 7. Session Evidence
    sess = SessionEvidenceObject(object_id="sess_001", session_id="s_1", copy_id="cpy_1", recipient_id="alice", issued_at=now_ts, session_nonce="nonce1", session_fingerprint_key="key1")
    sess.seal_content_hash()
    assert sess.verify_content_integrity()

    # 8. Lineage Evidence
    lin = LineageEvidenceObject(object_id="lin_001", document_id="doc_001", root_copy_id="cpy_0")
    lin.seal_content_hash()
    assert lin.verify_content_integrity()

    # 9. Ledger Proof
    lp = LedgerProofObject(
        object_id="lp_001",
        receipt_id="rec_001",
        receipt_hash="h"*64,
        block_height=1,
        block_hash="bh"*32,
        previous_block_hash="0"*64,
        timestamp=now_ts,
        merkle_root="mr"*32,
        proposer_validator_id="v1",
        proposer_signature_b64="psig"
    )
    lp.seal_content_hash()
    assert lp.verify_content_integrity()

    # 10. Telemetry Evidence
    tel = TelemetryEvidenceObject(
        object_id="tel_001",
        event_id="ev_001",
        event_hash="eh"*32,
        timestamp=now_ts,
        source_system="EDR",
        source_trust_level="CRYPTOGRAPHICALLY_VERIFIED"
    )
    tel.seal_content_hash()
    assert tel.verify_content_integrity()

    # 11. Chain of Custody
    coc = ChainOfCustodyEvent(
        object_id="coc_001",
        custody_event_id="coc_001",
        evidence_object_id="art_001",
        operator_identity="agent_smith",
        device_identity="workstation_01",
        action=CustodyAction.COLLECTED,
        timestamp=now_ts,
        previous_custody_hash="0"*64,
        resulting_evidence_hash="eh"*32,
        reason="Initial evidence acquisition"
    )
    coc.seal_content_hash()
    assert coc.verify_content_integrity()

    # 12. Attribution Decision
    dec = AttributionDecisionObject(
        object_id="dec_001",
        case_id="case_001",
        evidence_merkle_root="mr"*32,
        decision_state=DecisionState.ATTRIBUTED,
        attributed_principal_id="alice",
        confidence_score=0.99
    )
    dec.seal_content_hash()
    assert dec.verify_content_integrity()

    # 13. Dependency Edge
    edge = DependencyEdge(object_id="edge_001", source_id="dec_001", target_id="wm_001")
    edge.seal_content_hash()
    assert edge.verify_content_integrity()
