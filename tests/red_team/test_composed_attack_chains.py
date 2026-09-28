"""
AegisTrace Composed Attack Chains Evaluation Tests.

Executes composed attack chains (A through G) combining multiple adversary actions
against the forensic tracking and evidence verification pipeline:
- CHAIN A: Stolen Account + Device Mismatch + Partial Telemetry + Valid Old Session
- CHAIN B: Valid Receipt + Modified Ledger Tail + Stale Checkpoint
- CHAIN C: Watermark Fragment + Wrong Document Binding + Forged Metadata (Transplantation)
- CHAIN D: Replayed Receipt + Rotated Key + Stale Evidence Package
- CHAIN E: Cross-Tenant Artifact + Valid Foreign Signature + Wrong Tenant Metadata
- CHAIN F: Valid Artifact + Modified Lineage + Conflicting Telemetry
- CHAIN G: Corrupted Evidence Package + Attempted Recovery + Stale State Rollback
"""

import pytest
from core.integration.orchestrator import AegisTraceEndToEndOrchestrator
from core.red_team.composed_attacks import (
    ComposedAttackSimulator,
    ComposedAttackVerdict,
)


@pytest.fixture(scope="module")
def golden_pipeline_setup():
    orchestrator = AegisTraceEndToEndOrchestrator(
        tenant_id="tenant_composed_defense_01",
        validator_count=4
    )
    doc_bytes = b"%PDF-1.7 COMPOSED ATTACK CHAIN TEST MATRIX\n" + b"RESTRICTED DEFENSE INTEL " * 50
    result = orchestrator.run_full_golden_pipeline(
        document_bytes=doc_bytes,
        document_name="Composed_Chain_Intel.pdf",
        leak_recipient_id="alice"
    )
    return orchestrator, result


def test_chain_a_stolen_account_device_mismatch(golden_pipeline_setup):
    _, result = golden_pipeline_setup
    attack_res = ComposedAttackSimulator.execute_chain_a(result)
    assert attack_res.security_maintained is True
    assert attack_res.verdict == ComposedAttackVerdict.DETECTED
    assert len(attack_res.evidence_errors) > 0


def test_chain_b_ledger_tail_mutation_and_fork(golden_pipeline_setup):
    orchestrator, _ = golden_pipeline_setup
    attack_res = ComposedAttackSimulator.execute_chain_b(orchestrator)
    assert attack_res.security_maintained is True
    assert attack_res.verdict == ComposedAttackVerdict.DETECTED


def test_chain_c_watermark_transplantation(golden_pipeline_setup):
    _, result = golden_pipeline_setup
    attack_res = ComposedAttackSimulator.execute_chain_c(result)
    assert attack_res.security_maintained is True
    assert attack_res.verdict == ComposedAttackVerdict.DETECTED
    assert len(attack_res.evidence_errors) > 0


def test_chain_d_post_revocation_stale_key_replay(golden_pipeline_setup):
    _, result = golden_pipeline_setup
    attack_res = ComposedAttackSimulator.execute_chain_d(result)
    assert attack_res.security_maintained is True
    assert attack_res.verdict == ComposedAttackVerdict.DETECTED


def test_chain_e_cross_tenant_foreign_injection(golden_pipeline_setup):
    _, result = golden_pipeline_setup
    attack_res = ComposedAttackSimulator.execute_chain_e(result)
    assert attack_res.security_maintained is True
    assert attack_res.verdict == ComposedAttackVerdict.DETECTED


def test_chain_f_lineage_downstream_gap_violation(golden_pipeline_setup):
    _, result = golden_pipeline_setup
    attack_res = ComposedAttackSimulator.execute_chain_f(result)
    assert attack_res.security_maintained is True
    assert attack_res.verdict == ComposedAttackVerdict.DETECTED


def test_chain_g_corrupted_package_manifest_forgery(golden_pipeline_setup):
    _, result = golden_pipeline_setup
    attack_res = ComposedAttackSimulator.execute_chain_g(result)
    assert attack_res.security_maintained is True
    assert attack_res.verdict == ComposedAttackVerdict.DETECTED
