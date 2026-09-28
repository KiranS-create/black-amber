"""
AegisTrace Privileged Operator Attack Tests.

Tests that even a rogue system administrator or root operator with direct access
to the database, log files, disk storage, and configuration cannot tamper with
forensic records, ledger history, or evidence packages without immediate cryptographic detection.
"""

import pytest
import copy
from core.integration.orchestrator import AegisTraceEndToEndOrchestrator
from core.red_team.privileged_operator import (
    PrivilegedOperatorAttackSimulator,
    PrivilegedAttackResult,
)
from core.evidence_package.models import VerificationStatus
from core.evidence_package.verifier import OfflineEvidenceVerifier


@pytest.fixture(scope="module")
def golden_setup():
    orchestrator = AegisTraceEndToEndOrchestrator(
        tenant_id="tenant_admin_attack_eval",
        validator_count=4
    )
    doc_bytes = b"%PDF-1.7 ADMIN PRIVILEGE TESTING ARTIFACT\n" + b"ROOT LEVEL SECURITY AUDIT " * 40
    result = orchestrator.run_full_golden_pipeline(
        document_bytes=doc_bytes,
        document_name="Admin_Privilege_Audit.pdf",
        leak_recipient_id="alice"
    )
    return orchestrator, result


def test_admin_tamper_chain_of_custody(golden_setup):
    _, result = golden_setup
    res = PrivilegedOperatorAttackSimulator.test_tamper_chain_of_custody(result)
    assert res.detected_and_prevented is True


def test_admin_delete_ledger_transaction(golden_setup):
    orchestrator, _ = golden_setup
    res = PrivilegedOperatorAttackSimulator.test_delete_ledger_transaction(orchestrator)
    assert res.detected_and_prevented is True


def test_admin_rewrite_attribution_decision(golden_setup):
    _, result = golden_setup
    res = PrivilegedOperatorAttackSimulator.test_rewrite_attribution_decision(result)
    assert res.detected_and_prevented is True


def test_admin_restore_stale_backup_rollback(golden_setup):
    orchestrator, _ = golden_setup
    res = PrivilegedOperatorAttackSimulator.test_restore_stale_backup_rollback(orchestrator)
    assert res.detected_and_prevented is True


def test_admin_tamper_validator_quorum_signatures(golden_setup):
    """
    Rogue admin modifies a validator signature on a committed DLT block.
    Verifies that quorum validation immediately fails closed.
    """
    orchestrator, _ = golden_setup
    dlt = orchestrator.dlt_ledger
    node = list(dlt.nodes.values())[0]
    
    assert len(node.blocks) > 0
    target_block = copy.deepcopy(node.blocks[0])
    
    if target_block.quorum_signatures:
        val_id = list(target_block.quorum_signatures.keys())[0]
        # Corrupt the signature bytes
        target_block.quorum_signatures[val_id] = "corrupted_signature_" + "0" * 40
        
        is_valid, errors = target_block.verify_block_integrity(
            authorized_validators=dlt.val_map,
            quorum_threshold=dlt.quorum_threshold
        )
        assert is_valid is False
        assert len(errors) > 0
