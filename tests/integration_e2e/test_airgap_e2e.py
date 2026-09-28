"""
SIH26237 - Air-Gap Enforcement & Zero-Socket Isolation Integration Tests.

Validates that:
1. The entire AegisTrace forensic pipeline operates fully air-gapped.
2. System execution completes successfully when all socket network creation is strictly blocked.
3. Offline verifier independently verifies packages without external network or DNS lookups.
"""

import socket
import pytest
from core.integration.orchestrator import AegisTraceEndToEndOrchestrator
from core.evidence_package.models import VerificationStatus


class BlockedNetworkCallError(RuntimeError):
    pass


def _guarded_socket(*args, **kwargs):
    raise BlockedNetworkCallError("Network socket access attempted in strict air-gap mode!")


def test_strict_airgap_pipeline_and_verifier(monkeypatch):
    """Executes full pipeline with socket.socket patched to raise on any network attempt."""
    # Patch all socket creation to guarantee 100% air-gap compliance
    monkeypatch.setattr(socket, "socket", _guarded_socket)

    orchestrator = AegisTraceEndToEndOrchestrator(tenant_id="tenant_airgap_enforced")
    result = orchestrator.run_full_golden_pipeline(leak_recipient_id="alice")

    assert result.verification_result.overall_status == VerificationStatus.VERIFIED
    assert result.verification_result.manifest_signature_valid is True
    assert result.verification_result.merkle_root_valid is True
    assert result.verification_result.recipient_signature_valid is True
    assert result.verification_result.ledger_proof_valid is True
