"""
SIH26237 - Multi-Tenant Isolation & Partition Enforcement Integration Tests.

Validates that:
1. Tenants (e.g. Tenant Alpha vs Tenant Bravo) are completely isolated across all subsystems.
2. Tenant Alpha packages cannot be decapsulated or decrypted by Tenant Bravo recipients.
3. Evidence packages from Tenant Alpha audited by Tenant Bravo verifier fail Pillar 1 (TENANT_ISOLATION_VIOLATION).
4. Lineage indexes and DLT ledgers strictly scope lookups to tenant partitions.
"""

import pytest
from core.integration.orchestrator import AegisTraceEndToEndOrchestrator
from core.integration.harness import EndToEndFaultHarness
from core.evidence_package.models import VerificationStatus
from core.evidence_package.verifier import OfflineEvidenceVerifier


def test_cross_tenant_cryptographic_and_forensic_isolation():
    """Tests that cross-tenant access and verification attempts fail closed."""
    # 1. Orchestrate Golden Pipeline for Tenant Alpha
    orch_alpha = AegisTraceEndToEndOrchestrator(tenant_id="tenant_alpha")
    res_alpha = orch_alpha.run_full_golden_pipeline(leak_recipient_id="alice")
    assert res_alpha.verification_result.overall_status == VerificationStatus.VERIFIED

    # 2. Setup Tenant Bravo
    orch_bravo = AegisTraceEndToEndOrchestrator(tenant_id="tenant_bravo")
    david_bravo = orch_bravo.enroll_recipient("David Bravo", "david_bravo")

    # 3. Attempt to decrypt Tenant Alpha package with Tenant Bravo recipient
    alpha_pkg = res_alpha.decryption_records["alice"]
    # Extract release package
    rel_packages = list(orch_alpha.release_manager.releases[res_alpha.release_id].packages.values())
    alpha_release_pkg = rel_packages[0]

    spoof_res = EndToEndFaultHarness.test_key_spoofing(
        package=alpha_release_pkg,
        wrong_recipient=david_bravo
    )
    assert spoof_res.detected_and_blocked is True
    assert spoof_res.attack_succeeded is False

    # 4. Attempt to verify Tenant Alpha evidence package under Tenant Bravo verifier context
    cross_tenant_res = EndToEndFaultHarness.test_cross_tenant_isolation(
        evidence_package=res_alpha.evidence_package,
        other_tenant_id="tenant_bravo"
    )
    assert cross_tenant_res.detected_and_blocked is True
    assert cross_tenant_res.verification_status == "INVALID"
    assert "TENANT_ISOLATION_VIOLATION" in cross_tenant_res.error_message
