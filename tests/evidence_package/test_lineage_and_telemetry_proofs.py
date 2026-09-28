"""
Tests for Lineage Proof Subgraphs and Telemetry Evidence Dependencies.
Verifies:
1. Lineage boundary preservation (LAST_KNOWN_HOLDER, DOWNSTREAM_GAP, MISSING_PARENT).
2. Refusal to fabricate downstream actors when custody gaps exist.
3. Telemetry evidence dependency classification (DIRECTLY_SUPPORTS, CORROBORATES, etc.).
4. Telemetry event hash verification and attribution decision grounding.
"""

import pytest
from datetime import datetime, timezone

from core.crypto.signatures import MLDSA65
from core.evidence_package.models import (
    LineageEvidenceObject,
    TelemetryEvidenceObject,
    TelemetryDependencyRelation,
    AttributionDecisionObject,
    DecisionState
)
from core.evidence_package.builder import EvidencePackageBuilder
from core.evidence_package.verifier import OfflineEvidenceVerifier


def test_lineage_proof_boundary_preservation():
    # Valid lineage evidence object preserving downstream gap
    lin_valid = LineageEvidenceObject(
        object_id="lin_001",
        document_id="doc_alpha",
        root_copy_id="cpy_root_01",
        target_copy_id="cpy_child_02",
        boundary_state="LAST_KNOWN_HOLDER",
        last_known_holder="rec_bob_8b2a",
        has_downstream_gap=True,
        lineage_subgraph=[
            {"parent": "cpy_root_01", "child": "cpy_child_01", "holder": "rec_alice_4f9a"},
            {"parent": "cpy_child_01", "child": "cpy_child_02", "holder": "rec_bob_8b2a"}
        ]
    )
    lin_valid.seal_content_hash()

    signer_kp = MLDSA65.generate_keypair()
    builder = EvidencePackageBuilder(case_id="case_lin_01")
    builder.add_object(lin_valid)
    dec = AttributionDecisionObject(
        object_id="dec_01",
        case_id="case_lin_01",
        evidence_merkle_root="0"*64,
        decision_state=DecisionState.ATTRIBUTED,
        attributed_principal_id="rec_bob_8b2a",
        last_known_holder_id="rec_bob_8b2a"
    )
    builder.set_decision(dec)
    builder.add_edge("dec_01", "lin_001")
    pkg = builder.build_and_sign(signer_kp)

    verifier = OfflineEvidenceVerifier()
    res = verifier.verify_package(pkg.manifest, pkg.signature, pkg.objects, pkg.edges)
    assert res.lineage_valid is True

    # Invalid lineage: claims downstream gap exists but omits last_known_holder
    lin_invalid = LineageEvidenceObject(
        object_id="lin_bad",
        document_id="doc_alpha",
        root_copy_id="cpy_root_01",
        boundary_state="UNKNOWN_DOWNSTREAM_ACTOR",
        last_known_holder=None,
        has_downstream_gap=True
    )
    lin_invalid.seal_content_hash()

    b2 = EvidencePackageBuilder(case_id="case_lin_02")
    b2.add_object(lin_invalid)
    b2.set_decision(dec)
    b2.add_edge("dec_01", "lin_bad")
    pkg2 = b2.build_and_sign(signer_kp)

    res2 = verifier.verify_package(pkg2.manifest, pkg2.signature, pkg2.objects, pkg2.edges)
    assert res2.lineage_valid is False
    assert any("must preserve last_known_holder" in err for err in res2.errors)


def test_telemetry_evidence_dependency_relations():
    now_ts = datetime.now(timezone.utc).isoformat()

    tel1 = TelemetryEvidenceObject(
        object_id="tel_001",
        event_id="edr_ev_101",
        event_hash="h1_" + "a" * 61,
        timestamp=now_ts,
        source_system="EDR",
        source_trust_level="CRYPTOGRAPHICALLY_VERIFIED",
        actor_id="rec_alice_4f9a",
        device_id="dev_workstation_12",
        dependency_relation=TelemetryDependencyRelation.DIRECTLY_SUPPORTS,
        relationship_details="Local decrypt memory buffer observed in EDR driver"
    )
    tel1.seal_content_hash()

    tel2 = TelemetryEvidenceObject(
        object_id="tel_002",
        event_id="dlp_ev_202",
        event_hash="h2_" + "b" * 61,
        timestamp=now_ts,
        source_system="PRINT_SPOOLER",
        source_trust_level="HIGH_SYSTEM",
        actor_id="rec_alice_4f9a",
        device_id="dev_workstation_12",
        dependency_relation=TelemetryDependencyRelation.CORROBORATES,
        relationship_details="Spooler file write matching document byte length"
    )
    tel2.seal_content_hash()

    signer_kp = MLDSA65.generate_keypair()
    builder = EvidencePackageBuilder(case_id="case_tel_01")
    builder.add_object(tel1)
    builder.add_object(tel2)
    dec = AttributionDecisionObject(
        object_id="dec_01",
        case_id="case_tel_01",
        evidence_merkle_root="0"*64,
        decision_state=DecisionState.ATTRIBUTED,
        attributed_principal_id="rec_alice_4f9a"
    )
    builder.set_decision(dec)
    builder.add_edge("dec_01", "tel_001")
    builder.add_edge("dec_01", "tel_002")

    pkg = builder.build_and_sign(signer_kp)

    verifier = OfflineEvidenceVerifier()
    res = verifier.verify_package(pkg.manifest, pkg.signature, pkg.objects, pkg.edges)
    assert res.dependency_graph_valid is True
    assert res.object_hashes_valid is True
