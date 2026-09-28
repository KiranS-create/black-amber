"""
Comprehensive 16-Field Adversarial Tampering Attack Suite for Evidence Packages.

Verifies that any adversarial attempt to tamper with:
1. Case identifier
2. Artifact hash/content
3. Watermark payload/token
4. Watermark confidence score
5. Recipient identity (impersonation)
6. Recipient ML-DSA-65 signature
7. Receipt timestamp (temporal key validity boundary violation)
8. Ledger block hash
9. Ledger Merkle audit path
10. Ledger validator signatures / quorum shortfall
11. Lineage synthetic cycle
12. Missing / ungrounded dependency link
13. Inverted attribution decision (e.g., claiming ATTRIBUTED without recipient proof)
14. Chain of custody intermediate link hash
15. Manifest timestamp / content-hash tampering
16. Manifest ML-DSA-65 signature corruption / stripping
17. Cross-tenant package injection

is immediately detected and rejected with fail-closed INVALID or CONFLICT verdicts.
"""

import copy
import base64
import hashlib
from datetime import datetime, timezone, timedelta

import pytest

from core.crypto.signatures import MLDSA65
from core.evidence_package.models import (
    VerificationStatus,
    DecisionState,
    CustodyAction,
    TelemetryDependencyRelation,
    DependencyEdge
)
from core.evidence_package.verifier import OfflineEvidenceVerifier
from tests.evidence_package.test_offline_verifier import create_sample_valid_package_data


@pytest.fixture
def baseline_package_data():
    """Provides a fresh, valid base package and tenant ID."""
    pkg, tenant_id = create_sample_valid_package_data()
    return pkg, tenant_id


def test_attack_01_mutated_case_id(baseline_package_data):
    """Attack 1: Attacker changes case_id in the manifest to match another investigation."""
    pkg, tenant_id = baseline_package_data
    verifier = OfflineEvidenceVerifier(expected_tenant_id=tenant_id)

    tampered_manifest = pkg.manifest.model_copy(deep=True)
    tampered_manifest.case_id = "case_adversarial_hijack"

    res = verifier.verify_package(
        manifest=tampered_manifest,
        signature=pkg.signature,
        objects=pkg.objects,
        edges=pkg.edges,
        custody_chain=pkg.custody_chain
    )
    assert res.overall_status == VerificationStatus.INVALID
    assert res.manifest_signature_valid is False
    assert any("MANIFEST_DIGEST_MISMATCH" in err for err in res.errors)


def test_attack_02_mutated_artifact_hash(baseline_package_data):
    """Attack 2: Attacker alters the SHA-256 digest of the artifact evidence object."""
    pkg, tenant_id = baseline_package_data
    verifier = OfflineEvidenceVerifier(expected_tenant_id=tenant_id)

    tampered_objects = [copy.deepcopy(o) for o in pkg.objects]
    for obj in tampered_objects:
        if obj.object_id == "art_leak_pdf":
            obj.sha256_digest = "f" * 64
            # If content hash not updated: pillar 4 fails. If updated: pillar 3 Merkle fails.
            break

    res = verifier.verify_package(
        manifest=pkg.manifest,
        signature=pkg.signature,
        objects=tampered_objects,
        edges=pkg.edges,
        custody_chain=pkg.custody_chain
    )
    assert res.overall_status in (VerificationStatus.INVALID, VerificationStatus.INCOMPLETE)
    assert res.object_hashes_valid is False or res.merkle_root_valid is False


def test_attack_03_mutated_watermark_token(baseline_package_data):
    """Attack 3: Attacker modifies extracted watermark token to frame another party."""
    pkg, tenant_id = baseline_package_data
    verifier = OfflineEvidenceVerifier(expected_tenant_id=tenant_id)

    tampered_objects = [copy.deepcopy(o) for o in pkg.objects]
    for obj in tampered_objects:
        if obj.object_id == "wm_extracted_01":
            obj.extracted_token = "adversarial_forged_token"
            obj.seal_content_hash()
            break

    res = verifier.verify_package(
        manifest=pkg.manifest,
        signature=pkg.signature,
        objects=tampered_objects,
        edges=pkg.edges,
        custody_chain=pkg.custody_chain
    )
    assert res.overall_status == VerificationStatus.INVALID
    assert res.merkle_root_valid is False or res.watermark_binding_valid is False


def test_attack_04_mutated_watermark_confidence(baseline_package_data):
    """Attack 4: Attacker artificially inflates watermark confidence score."""
    pkg, tenant_id = baseline_package_data
    verifier = OfflineEvidenceVerifier(expected_tenant_id=tenant_id)

    tampered_objects = [copy.deepcopy(o) for o in pkg.objects]
    for obj in tampered_objects:
        if obj.object_id == "wm_extracted_01":
            obj.confidence_score = 0.9999
            break

    res = verifier.verify_package(
        manifest=pkg.manifest,
        signature=pkg.signature,
        objects=tampered_objects,
        edges=pkg.edges,
        custody_chain=pkg.custody_chain
    )
    assert res.overall_status in (VerificationStatus.INVALID, VerificationStatus.INCOMPLETE)
    assert res.object_hashes_valid is False


def test_attack_05_mutated_recipient_identity_impersonation(baseline_package_data):
    """Attack 5: Attacker changes recipient_id in DecryptionReceiptObject to Bob."""
    pkg, tenant_id = baseline_package_data
    verifier = OfflineEvidenceVerifier(expected_tenant_id=tenant_id)

    tampered_objects = [copy.deepcopy(o) for o in pkg.objects]
    for obj in tampered_objects:
        if obj.object_id == "receipt_decrypt_alice":
            obj.recipient_id = "rec_innocent_bob"
            # Keep original signature bytes - signature will fail over canonical payload!
            break

    res = verifier.verify_package(
        manifest=pkg.manifest,
        signature=pkg.signature,
        objects=tampered_objects,
        edges=pkg.edges,
        custody_chain=pkg.custody_chain
    )
    assert res.recipient_signature_valid is False
    assert any("invalid ML-DSA-65 signature" in err for err in res.errors)


def test_attack_06_mutated_recipient_signature(baseline_package_data):
    """Attack 6: Attacker flips bits in the recipient ML-DSA-65 signature."""
    pkg, tenant_id = baseline_package_data
    verifier = OfflineEvidenceVerifier(expected_tenant_id=tenant_id)

    tampered_objects = [copy.deepcopy(o) for o in pkg.objects]
    for obj in tampered_objects:
        if obj.object_id == "receipt_decrypt_alice":
            sig_raw = bytearray(base64.b64decode(obj.recipient_signature_b64))
            sig_raw[10] ^= 0xFF
            obj.recipient_signature_b64 = base64.b64encode(sig_raw).decode("utf-8")
            obj.seal_content_hash()
            break

    res = verifier.verify_package(
        manifest=pkg.manifest,
        signature=pkg.signature,
        objects=tampered_objects,
        edges=pkg.edges,
        custody_chain=pkg.custody_chain
    )
    assert res.recipient_signature_valid is False


def test_attack_07_mutated_receipt_timestamp_post_revocation(baseline_package_data):
    """Attack 7: Receipt timestamp occurs after key revocation boundary."""
    pkg, tenant_id = baseline_package_data
    verifier = OfflineEvidenceVerifier(expected_tenant_id=tenant_id)

    tampered_objects = [copy.deepcopy(o) for o in pkg.objects]
    # Revoke key yesterday
    rev_ts = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    for obj in tampered_objects:
        if obj.object_id == "idproof_rec_officer_alice":
            obj.revocation_timestamp = rev_ts
            obj.seal_content_hash()
            break

    res = verifier.verify_package(
        manifest=pkg.manifest,
        signature=pkg.signature,
        objects=tampered_objects,
        edges=pkg.edges,
        custody_chain=pkg.custody_chain
    )
    assert res.historical_keys_valid is False
    assert any("POST_REVOCATION_REJECTION" in err for err in res.errors)


def test_attack_08_mutated_ledger_block_hash(baseline_package_data):
    """Attack 8: Attacker alters block_hash in ledger proof object."""
    pkg, tenant_id = baseline_package_data
    verifier = OfflineEvidenceVerifier(expected_tenant_id=tenant_id)

    tampered_objects = [copy.deepcopy(o) for o in pkg.objects]
    for obj in tampered_objects:
        if obj.object_id == "ledger_proof_block_5001":
            obj.block_hash = "bh_tampered_fake_block_hash"
            obj.seal_content_hash()
            break

    res = verifier.verify_package(
        manifest=pkg.manifest,
        signature=pkg.signature,
        objects=tampered_objects,
        edges=pkg.edges,
        custody_chain=pkg.custody_chain
    )
    assert res.ledger_proof_valid is False


def test_attack_09_mutated_ledger_merkle_path(baseline_package_data):
    """Attack 9: Attacker modifies the Merkle audit path in ledger proof."""
    pkg, tenant_id = baseline_package_data
    verifier = OfflineEvidenceVerifier(expected_tenant_id=tenant_id)

    tampered_objects = [copy.deepcopy(o) for o in pkg.objects]
    for obj in tampered_objects:
        if obj.object_id == "ledger_proof_block_5001":
            obj.merkle_audit_path = [("0" * 64, "R")]
            obj.seal_content_hash()
            break

    res = verifier.verify_package(
        manifest=pkg.manifest,
        signature=pkg.signature,
        objects=tampered_objects,
        edges=pkg.edges,
        custody_chain=pkg.custody_chain
    )
    assert res.ledger_proof_valid is False
    assert any("Merkle root mismatch" in err for err in res.errors)


def test_attack_10_ledger_quorum_shortfall(baseline_package_data):
    """Attack 10: Attacker removes a validator signature, falling below quorum threshold."""
    pkg, tenant_id = baseline_package_data
    verifier = OfflineEvidenceVerifier(expected_tenant_id=tenant_id)

    tampered_objects = [copy.deepcopy(o) for o in pkg.objects]
    for obj in tampered_objects:
        if obj.object_id == "ledger_proof_block_5001":
            # Remove val-02 signature leaving only 1 vote when threshold is 2
            obj.quorum_signatures.pop("val-02", None)
            obj.seal_content_hash()
            break

    res = verifier.verify_package(
        manifest=pkg.manifest,
        signature=pkg.signature,
        objects=tampered_objects,
        edges=pkg.edges,
        custody_chain=pkg.custody_chain
    )
    assert res.ledger_proof_valid is False
    assert any("Quorum threshold not met" in err for err in res.errors)


def test_attack_11_lineage_synthetic_cycle(baseline_package_data):
    """Attack 11: Attacker injects a synthetic cyclic loop into dependency DAG."""
    pkg, tenant_id = baseline_package_data
    verifier = OfflineEvidenceVerifier(expected_tenant_id=tenant_id)

    # Add edge creating cycle: art_leak_pdf -> decision_final_01
    cyclic_edges = list(pkg.edges)
    cycle_edge = DependencyEdge(
        object_id="edge_cyclic_attack",
        source_id="art_leak_pdf",
        target_id="decision_final_01",
        relationship_type="MALICIOUS_CYCLE",
        tenant_id=tenant_id
    )
    cycle_edge.seal_content_hash()
    cyclic_edges.append(cycle_edge)

    res = verifier.verify_package(
        manifest=pkg.manifest,
        signature=pkg.signature,
        objects=pkg.objects,
        edges=cyclic_edges,
        custody_chain=pkg.custody_chain
    )
    assert res.dependency_graph_valid is False
    assert any("DAG_CYCLE_DETECTED" in err for err in res.errors)


def test_attack_12_ungrounded_decision(baseline_package_data):
    """Attack 12: Attribution decision has no edges grounding it to evidence nodes."""
    pkg, tenant_id = baseline_package_data
    verifier = OfflineEvidenceVerifier(expected_tenant_id=tenant_id)

    # Empty all dependency edges
    res = verifier.verify_package(
        manifest=pkg.manifest,
        signature=pkg.signature,
        objects=pkg.objects,
        edges=[],
        custody_chain=pkg.custody_chain
    )
    assert res.dependency_graph_valid is False
    assert any("has no grounding in empirical evidence nodes" in err for err in res.errors)


def test_attack_13_inverted_attribution_decision(baseline_package_data):
    """Attack 13: Attacker flips decision_state to ATTRIBUTED without specifying principal."""
    pkg, tenant_id = baseline_package_data
    verifier = OfflineEvidenceVerifier(expected_tenant_id=tenant_id)

    tampered_objects = [copy.deepcopy(o) for o in pkg.objects]
    for obj in tampered_objects:
        if obj.object_id == "decision_final_01":
            obj.attributed_principal_id = None
            obj.seal_content_hash()
            break

    res = verifier.verify_package(
        manifest=pkg.manifest,
        signature=pkg.signature,
        objects=tampered_objects,
        edges=pkg.edges,
        custody_chain=pkg.custody_chain
    )
    assert res.decision_consistent is False
    assert any("ATTRIBUTED decision must specify attributed_principal_id" in err for err in res.errors)


def test_attack_14_mutated_custody_chain_link(baseline_package_data):
    """Attack 14: Attacker modifies an intermediate custody event's reason or hash."""
    pkg, tenant_id = baseline_package_data
    verifier = OfflineEvidenceVerifier(expected_tenant_id=tenant_id)

    tampered_chain = [copy.deepcopy(ev) for ev in pkg.custody_chain]
    tampered_chain[1].reason = "Unrecorded tampering during forensic handling"

    res = verifier.verify_package(
        manifest=pkg.manifest,
        signature=pkg.signature,
        objects=pkg.objects,
        edges=pkg.edges,
        custody_chain=tampered_chain
    )
    assert res.custody_chain_valid is False
    assert any("content_hash mismatch" in err or "broken custody link" in err for err in res.errors)


def test_attack_15_mutated_manifest_merkle_root(baseline_package_data):
    """Attack 15: Attacker replaces evidence_merkle_root in manifest."""
    pkg, tenant_id = baseline_package_data
    verifier = OfflineEvidenceVerifier(expected_tenant_id=tenant_id)

    tampered_manifest = pkg.manifest.model_copy(deep=True)
    tampered_manifest.evidence_merkle_root = "0" * 64

    res = verifier.verify_package(
        manifest=tampered_manifest,
        signature=pkg.signature,
        objects=pkg.objects,
        edges=pkg.edges,
        custody_chain=pkg.custody_chain
    )
    assert res.overall_status == VerificationStatus.INVALID
    assert res.manifest_signature_valid is False or res.merkle_root_valid is False


def test_attack_16_corrupted_manifest_signature(baseline_package_data):
    """Attack 16: Attacker corrupts ML-DSA-65 signature bytes on manifest."""
    pkg, tenant_id = baseline_package_data
    verifier = OfflineEvidenceVerifier(expected_tenant_id=tenant_id)

    tampered_sig = pkg.signature.model_copy(deep=True)
    raw_sig = bytearray(base64.b64decode(tampered_sig.signature_b64))
    raw_sig[5] ^= 0xAA
    tampered_sig.signature_b64 = base64.b64encode(raw_sig).decode("utf-8")

    res = verifier.verify_package(
        manifest=pkg.manifest,
        signature=tampered_sig,
        objects=pkg.objects,
        edges=pkg.edges,
        custody_chain=pkg.custody_chain
    )
    assert res.overall_status == VerificationStatus.INVALID
    assert res.manifest_signature_valid is False


def test_attack_17_cross_tenant_injection(baseline_package_data):
    """Attack 17: Attacker attempts to verify package under a different tenant context."""
    pkg, tenant_id = baseline_package_data
    verifier = OfflineEvidenceVerifier(expected_tenant_id="tenant-commercial-99")

    res = verifier.verify_package(
        manifest=pkg.manifest,
        signature=pkg.signature,
        objects=pkg.objects,
        edges=pkg.edges,
        custody_chain=pkg.custody_chain
    )
    assert res.overall_status == VerificationStatus.INVALID
    assert any("TENANT_ISOLATION_VIOLATION" in err for err in res.errors)
