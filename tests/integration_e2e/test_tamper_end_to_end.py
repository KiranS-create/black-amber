"""
SIH26237 - Adversarial Tamper & Fault Injection Matrix Integration Tests.

Executes comprehensive fault injection attacks across the entire pipeline:
1. Ciphertext bitflip
2. Recipient key spoofing
3. Dynamic watermark token tampering
4. Recipient ML-DSA-65 signature corruption
5. Ledger Merkle audit path tampering
6. Key lifecycle post-revocation replay
7. Package manifest signature forgery
8. Cross-tenant evidence injection
"""

import pytest
from core.integration.orchestrator import AegisTraceEndToEndOrchestrator
from core.integration.harness import EndToEndFaultHarness


@pytest.fixture
def golden_pipeline_context():
    orch = AegisTraceEndToEndOrchestrator(tenant_id="tenant_tamper_suite")
    res = orch.run_full_golden_pipeline(leak_recipient_id="alice")
    return orch, res


def test_adversarial_ciphertext_tamper(golden_pipeline_context):
    orch, res = golden_pipeline_context
    alice = orch.registry.get("alice")
    rel = orch.release_manager.releases[res.release_id]
    pkg = rel.packages["alice"]

    result = EndToEndFaultHarness.test_ciphertext_tamper(pkg, alice)
    assert result.detected_and_blocked is True
    assert result.attack_succeeded is False


def test_adversarial_key_spoofing(golden_pipeline_context):
    orch, res = golden_pipeline_context
    bob = orch.registry.get("bob")
    rel = orch.release_manager.releases[res.release_id]
    pkg = rel.packages["alice"]

    result = EndToEndFaultHarness.test_key_spoofing(pkg, bob)
    assert result.detected_and_blocked is True
    assert result.attack_succeeded is False


def test_adversarial_watermark_token_tamper(golden_pipeline_context):
    orch, res = golden_pipeline_context
    dyn_id = res.decryption_records["alice"].dynamic_identity

    result = EndToEndFaultHarness.test_watermark_token_tamper(
        token=dyn_id.token,
        salt=dyn_id.salt,
        commitment=dyn_id.commitment
    )
    assert result.detected_and_blocked is True
    assert result.attack_succeeded is False


def test_adversarial_recipient_signature_tamper(golden_pipeline_context):
    orch, res = golden_pipeline_context
    receipt = res.decryption_records["alice"].receipt

    result = EndToEndFaultHarness.test_recipient_signature_tamper(receipt)
    assert result.detected_and_blocked is True
    assert result.attack_succeeded is False


def test_adversarial_ledger_merkle_tamper(golden_pipeline_context):
    orch, res = golden_pipeline_context
    result = EndToEndFaultHarness.test_ledger_merkle_tamper(res.evidence_package)
    assert result.detected_and_blocked is True
    assert result.attack_succeeded is False


def test_adversarial_key_lifecycle_replay(golden_pipeline_context):
    orch, res = golden_pipeline_context
    result = EndToEndFaultHarness.test_key_lifecycle_revocation_replay(res.evidence_package)
    assert result.detected_and_blocked is True
    assert result.attack_succeeded is False


def test_adversarial_manifest_signature_tamper(golden_pipeline_context):
    orch, res = golden_pipeline_context
    result = EndToEndFaultHarness.test_manifest_signature_tamper(res.evidence_package)
    assert result.detected_and_blocked is True
    assert result.attack_succeeded is False


def test_adversarial_cross_tenant_injection(golden_pipeline_context):
    orch, res = golden_pipeline_context
    result = EndToEndFaultHarness.test_cross_tenant_isolation(
        evidence_package=res.evidence_package,
        other_tenant_id="tenant_malicious_infiltrator"
    )
    assert result.detected_and_blocked is True
    assert result.attack_succeeded is False
