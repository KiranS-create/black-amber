"""
Tests for AegisTrace Cryptographic Safe Redaction Engine.

Verifies:
1. Selective disclosure and privacy redaction of sensitive metadata.
2. Redacted objects replaced by RedactedEvidenceStub with explicit classifications:
   - REDACTED
   - NOT_INCLUDED
   - NOT_REQUIRED_FOR_THIS_PROOF
3. Strict preservation of Merkle leaf hashes: H_stub == H_original.
4. Retention of valid post-quantum ML-DSA-65 manifest signature after redaction.
5. Independent offline verifier evaluates redacted package to VERIFIED status.
6. Tampered redacted stub detection.
"""

import copy
import base64
import hashlib
from datetime import datetime, timezone

import pytest

from core.crypto.signatures import MLDSA65
from core.evidence_package.models import (
    BaseEvidenceObject,
    EvidenceObjectType,
    VerificationStatus,
    DeviceEvidenceObject,
    TelemetryEvidenceObject,
    TelemetryDependencyRelation,
    AttributionDecisionObject,
    DecisionState
)
from core.evidence_package.redaction import (
    SafeRedactionEngine,
    RedactedEvidenceStub,
    RedactionClassification
)
from core.evidence_package.builder import EvidencePackageBuilder
from core.evidence_package.verifier import OfflineEvidenceVerifier
from tests.evidence_package.test_offline_verifier import create_sample_valid_package_data


def test_redaction_stub_properties():
    """Verify stub attributes and content hash invariants."""
    device = DeviceEvidenceObject(
        object_id="dev_classified_workstation_99",
        device_id="hardware-uid-9948274",
        platform_type="TPM",
        attestation_status="DEVICE_ATTESTED",
        hardware_key_id="tpm-ek-key-01"
    )
    orig_hash = device.seal_content_hash()

    # Redact with REDACTED classification
    stub1 = SafeRedactionEngine.redact_object(
        obj=device,
        reason="Compartmentalized hardware identifier",
        classification=RedactionClassification.REDACTED,
        redacted_by="SECURITY_OFFICER_01"
    )
    assert isinstance(stub1, RedactedEvidenceStub)
    assert stub1.object_id == device.object_id
    assert stub1.original_object_id == device.object_id
    assert stub1.original_object_type == EvidenceObjectType.DEVICE_EVIDENCE
    assert stub1.content_hash == orig_hash
    assert stub1.redaction_classification == RedactionClassification.REDACTED

    # Redact with NOT_INCLUDED classification
    stub2 = SafeRedactionEngine.redact_object(
        obj=device,
        reason="Omitted from unclassified public evidence package",
        classification=RedactionClassification.NOT_INCLUDED
    )
    assert stub2.redaction_classification == RedactionClassification.NOT_INCLUDED
    assert stub2.content_hash == orig_hash

    # Redact with NOT_REQUIRED_FOR_THIS_PROOF classification
    stub3 = SafeRedactionEngine.redact_object(
        obj=device,
        reason="Tribunal determined device attestation not contested",
        classification=RedactionClassification.NOT_REQUIRED_FOR_THIS_PROOF
    )
    assert stub3.redaction_classification == RedactionClassification.NOT_REQUIRED_FOR_THIS_PROOF
    assert stub3.content_hash == orig_hash


def test_redaction_preserves_merkle_root_and_manifest_signature():
    """
    Verify that applying redactions to an already-sealed and signed package
    preserves both the RFC-6962 Merkle root and the post-quantum ML-DSA-65 manifest signature,
    and passes offline verification with status VERIFIED.
    """
    base_pkg, tenant_id = create_sample_valid_package_data()

    # We will redact the case object to protect sensitive operational details
    target_to_redact = "case_case_2026_audit_001"
    assert any(o.object_id == target_to_redact for o in base_pkg.objects)

    redacted_objects, updated_manifest = SafeRedactionEngine.apply_package_redactions(
        objects=base_pkg.objects,
        target_object_ids_to_redact=[target_to_redact],
        reason="Classified operation code name withheld for privacy",
        manifest=base_pkg.manifest,
        classification=RedactionClassification.REDACTED,
        redacted_by="OFFICIAL_DISCLOSURE_OFFICER"
    )

    # 1. Verify that target object is now a RedactedEvidenceStub
    redacted_stub = next(o for o in redacted_objects if o.object_id == target_to_redact)
    assert isinstance(redacted_stub, RedactedEvidenceStub)
    assert redacted_stub.redaction_classification == RedactionClassification.REDACTED
    assert redacted_stub.redaction_reason == "Classified operation code name withheld for privacy"

    # 2. Verify manifest flags
    assert updated_manifest.is_redacted is True
    assert target_to_redact in updated_manifest.redacted_object_ids

    # 3. Verify OfflineEvidenceVerifier evaluates the redacted package successfully
    verifier = OfflineEvidenceVerifier(expected_tenant_id=tenant_id)
    result = verifier.verify_package(
        manifest=updated_manifest,
        signature=base_pkg.signature,
        objects=redacted_objects,
        edges=base_pkg.edges,
        custody_chain=base_pkg.custody_chain
    )

    assert result.overall_status == VerificationStatus.VERIFIED
    assert result.manifest_signature_valid is True
    assert result.merkle_root_valid is True
    assert result.object_hashes_valid is True
    assert len(result.errors) == 0


def test_tampered_redacted_stub_fails_merkle_verification():
    """Verify that tampering with a redacted stub's content_hash breaks Merkle verification."""
    base_pkg, tenant_id = create_sample_valid_package_data()
    target_to_redact = "case_case_2026_audit_001"

    redacted_objects, updated_manifest = SafeRedactionEngine.apply_package_redactions(
        objects=base_pkg.objects,
        target_object_ids_to_redact=[target_to_redact],
        reason="Redacted metadata",
        manifest=base_pkg.manifest
    )

    # Tamper with the content_hash of the stub
    for obj in redacted_objects:
        if isinstance(obj, RedactedEvidenceStub):
            obj.content_hash = "f" * 64

    verifier = OfflineEvidenceVerifier(expected_tenant_id=tenant_id)
    result = verifier.verify_package(
        manifest=updated_manifest,
        signature=base_pkg.signature,
        objects=redacted_objects,
        edges=base_pkg.edges,
        custody_chain=base_pkg.custody_chain
    )

    assert result.merkle_root_valid is False
    assert result.overall_status == VerificationStatus.INVALID
    assert any("MERKLE_ROOT_MISMATCH" in err for err in result.errors)
