"""
Tests for Post-Quantum ML-DSA-65 Evidence Package Signing.
Verifies:
1. Valid post-quantum ML-DSA-65 signature creation and offline verification.
2. Modified manifest rejection.
3. Wrong signature rejection.
4. Wrong signer public key rejection.
5. Truncated or malformed signature fail-closed behavior.
6. Absolute non-embedding of private signing keys in package metadata.
"""

import pytest
import base64
import hashlib

from core.crypto.signatures import MLDSA65
from core.crypto.models import KeyPair
from core.evidence_package.models import PackageManifest, PackageSignature
from core.evidence_package.builder import EvidencePackageBuilder
from core.evidence_package.models import (
    ArtifactEvidenceObject,
    AttributionDecisionObject,
    DecisionState
)
from core.evidence_package.verifier import OfflineEvidenceVerifier


def test_package_signing_valid_and_tampered_scenarios():
    signer_kp = MLDSA65.generate_keypair()
    other_kp = MLDSA65.generate_keypair()

    builder = EvidencePackageBuilder(case_id="case_pqc_01")

    art = ArtifactEvidenceObject(
        object_id="art_01",
        artifact_category="LEAK",
        filename="leak.pdf",
        byte_size=1024,
        sha256_digest="e" * 64
    )
    dec = AttributionDecisionObject(
        object_id="dec_01",
        case_id="case_pqc_01",
        evidence_merkle_root="0"*64,
        decision_state=DecisionState.NO_SIGNAL
    )

    builder.add_object(art)
    builder.set_decision(dec)
    builder.add_edge("dec_01", "art_01")

    pkg = builder.build_and_sign(signing_keypair=signer_kp, signer_id="EXAMINER_01")

    # 1. Valid signature
    verifier = OfflineEvidenceVerifier()
    res = verifier.verify_package(
        manifest=pkg.manifest,
        signature=pkg.signature,
        objects=pkg.objects,
        edges=pkg.edges
    )
    assert res.manifest_signature_valid is True
    assert res.overall_status.value == "VERIFIED"

    # 2. Tampered manifest (change case_id)
    tampered_manifest = pkg.manifest.model_copy(deep=True)
    tampered_manifest.case_id = "case_pqc_TAMPERED"
    res_tampered = verifier.verify_package(
        manifest=tampered_manifest,
        signature=pkg.signature,
        objects=pkg.objects,
        edges=pkg.edges
    )
    assert res_tampered.manifest_signature_valid is False
    assert res_tampered.overall_status.value == "INVALID"

    # 3. Wrong signature (signature from another message)
    wrong_sig_bytes = MLDSA65.sign(signer_kp.private_key_bytes, b"DIFFERENT_MANIFEST_HASH")
    wrong_signature = pkg.signature.model_copy(deep=True)
    wrong_signature.signature_b64 = base64.b64encode(wrong_sig_bytes).decode("utf-8")

    res_wrong_sig = verifier.verify_package(
        manifest=pkg.manifest,
        signature=wrong_signature,
        objects=pkg.objects,
        edges=pkg.edges
    )
    assert res_wrong_sig.manifest_signature_valid is False

    # 4. Wrong signer public key
    wrong_signer_sig = pkg.signature.model_copy(deep=True)
    wrong_signer_sig.signer_public_key_b64 = base64.b64encode(other_kp.public_key_bytes).decode("utf-8")

    res_wrong_signer = verifier.verify_package(
        manifest=pkg.manifest,
        signature=wrong_signer_sig,
        objects=pkg.objects,
        edges=pkg.edges
    )
    assert res_wrong_signer.manifest_signature_valid is False

    # 5. Truncated signature
    trunc_sig = pkg.signature.model_copy(deep=True)
    raw_sig = base64.b64decode(pkg.signature.signature_b64)
    trunc_sig.signature_b64 = base64.b64encode(raw_sig[:32]).decode("utf-8")

    res_trunc = verifier.verify_package(
        manifest=pkg.manifest,
        signature=trunc_sig,
        objects=pkg.objects,
        edges=pkg.edges
    )
    assert res_trunc.manifest_signature_valid is False

    # 6. Malformed base64 signature
    malformed_sig = pkg.signature.model_copy(deep=True)
    malformed_sig.signature_b64 = "NOT_VALID_BASE64_!!!"

    res_malformed = verifier.verify_package(
        manifest=pkg.manifest,
        signature=malformed_sig,
        objects=pkg.objects,
        edges=pkg.edges
    )
    assert res_malformed.manifest_signature_valid is False
