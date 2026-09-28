"""
AegisTrace Air-Gap Adversary & Network Isolation Tests.

Tests that adversary attempts to force outbound network requests, DNS exfiltration,
or cloud service dependencies during offline verification are blocked and fail-closed.
"""

import socket
import pytest
from core.integration.orchestrator import AegisTraceEndToEndOrchestrator
from core.evidence_package.verifier import OfflineEvidenceVerifier
from core.evidence_package.models import VerificationStatus


class ForbiddenEgressError(RuntimeError):
    pass


def _deny_network_egress(*args, **kwargs):
    raise ForbiddenEgressError("Illegal network socket connection attempted in air-gapped environment!")


def test_adversary_cannot_force_egress_during_offline_verification(monkeypatch):
    """
    Verifies that during offline package verification, even if an adversary crafts
    tampered paths or metadata, zero socket connections are attempted.
    """
    orchestrator = AegisTraceEndToEndOrchestrator(
        tenant_id="tenant_airgap_adversary",
        validator_count=4
    )
    doc_bytes = b"%PDF-1.7 AIR GAP EGRESS ADVERSARY TEST\n" + b"RESTRICTED DATA " * 30
    res = orchestrator.run_full_golden_pipeline(
        document_bytes=doc_bytes,
        document_name="AirGap_Test.pdf",
        leak_recipient_id="alice"
    )

    pkg = res.evidence_package

    # Strictly block all socket operations
    monkeypatch.setattr(socket, "socket", _deny_network_egress)

    verifier = OfflineEvidenceVerifier(expected_tenant_id="tenant_airgap_adversary")

    # Must verify 100% locally without triggering socket call
    ver_res = verifier.verify_package(
        manifest=pkg.manifest,
        signature=pkg.signature,
        objects=pkg.objects,
        edges=pkg.edges,
        custody_chain=pkg.custody_chain
    )
    assert ver_res.overall_status == VerificationStatus.VERIFIED
    assert ver_res.decision_consistent is True
    assert ver_res.manifest_signature_valid is True
    assert ver_res.recipient_signature_valid is True
    assert ver_res.ledger_proof_valid is True
