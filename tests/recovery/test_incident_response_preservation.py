"""
Unit & Integration Tests for AegisTrace Incident Response FSM,
Forensic Preservation Mode, and Tamper-Evident Recovery Audit.
"""

import pytest
from core.recovery.models import IncidentState
from core.recovery.audit import RecoveryAuditLog
from core.recovery.incident import (
    IncidentResponseEngine,
    IncidentTransitionRequest,
    OperatorRole,
)


def test_incident_response_fsm_valid_lifecycle():
    audit = RecoveryAuditLog()
    engine = IncidentResponseEngine(audit_log=audit)
    assert engine.current_state == IncidentState.NORMAL

    # NORMAL -> SUSPECTED_COMPROMISE
    ok, err = engine.transition_to(
        IncidentTransitionRequest(
            requested_state=IncidentState.SUSPECTED_COMPROMISE,
            operator_id="op_alice",
            operator_role=OperatorRole.INCIDENT_COMMANDER,
            reason="Anomalous decryption burst observed"
        )
    )
    assert ok is True
    assert engine.current_state == IncidentState.SUSPECTED_COMPROMISE

    # SUSPECTED_COMPROMISE -> FORENSIC_PRESERVATION
    ok, err = engine.transition_to(
        IncidentTransitionRequest(
            requested_state=IncidentState.FORENSIC_PRESERVATION,
            operator_id="op_alice",
            operator_role=OperatorRole.FORENSIC_OFFICER,
            reason="Preserve live evidence stores"
        )
    )
    assert ok is True
    assert engine.current_state == IncidentState.FORENSIC_PRESERVATION
    assert engine.is_preservation_active is True

    # Check that mutations are blocked during preservation
    with pytest.raises(PermissionError, match="PRESERVATION_MODE_ACTIVE"):
        engine.assert_mutation_permitted("ledger")

    # FORENSIC_PRESERVATION -> RECOVERY_VALIDATION
    ok, err = engine.transition_to(
        IncidentTransitionRequest(
            requested_state=IncidentState.RECOVERY_VALIDATION,
            operator_id="op_bob",
            operator_role=OperatorRole.RECOVERY_OPERATOR,
            reason="Staging verified backup restoration"
        )
    )
    assert ok is True
    assert engine.current_state == IncidentState.RECOVERY_VALIDATION

    # RECOVERY_VALIDATION -> RESTORED (requires dual authorizer)
    # 1. Attempt without dual authorizer fails
    ok_fail, err_fail = engine.transition_to(
        IncidentTransitionRequest(
            requested_state=IncidentState.RESTORED,
            operator_id="op_bob",
            operator_role=OperatorRole.RECOVERY_OPERATOR,
            reason="Verification passed",
            dual_authorizer_id=None
        )
    )
    assert ok_fail is False
    assert "DUAL_CONTROL_REQUIRED" in err_fail

    # 2. Attempt with same authorizer fails
    ok_same, err_same = engine.transition_to(
        IncidentTransitionRequest(
            requested_state=IncidentState.RESTORED,
            operator_id="op_bob",
            operator_role=OperatorRole.RECOVERY_OPERATOR,
            reason="Verification passed",
            dual_authorizer_id="op_bob"
        )
    )
    assert ok_same is False
    assert "DUAL_CONTROL_VIOLATION" in err_same

    # 3. Valid dual control succeeds
    ok_dual, _ = engine.transition_to(
        IncidentTransitionRequest(
            requested_state=IncidentState.RESTORED,
            operator_id="op_bob",
            operator_role=OperatorRole.RECOVERY_OPERATOR,
            reason="Verification passed",
            dual_authorizer_id="op_alice",
            dual_authorizer_role=OperatorRole.SECURITY_ADMIN
        )
    )
    assert ok_dual is True
    assert engine.current_state == IncidentState.RESTORED
    assert engine.is_preservation_active is False


def test_invalid_transition_rejected():
    audit = RecoveryAuditLog()
    engine = IncidentResponseEngine(audit_log=audit)
    
    # Direct jump from NORMAL to RESTORED is disallowed
    ok, err = engine.transition_to(
        IncidentTransitionRequest(
            requested_state=IncidentState.RESTORED,
            operator_id="op_eve",
            operator_role=OperatorRole.RECOVERY_OPERATOR,
            reason="Unauthorized skip",
            dual_authorizer_id="op_mallory"
        )
    )
    assert ok is False
    assert "INVALID_TRANSITION" in err


def test_recovery_audit_log_hash_chain_integrity():
    audit = RecoveryAuditLog()
    r1 = audit.record_action("op_1", "ADMIN", "BACKUP_CREATE", "tenant_1", "NORMAL", "BACKUP_READY", "SUCCESS")
    r2 = audit.record_action("op_2", "ADMIN", "RESTORE_INIT", "tenant_1", "BACKUP_READY", "RESTORED", "SUCCESS")
    r3 = audit.record_action("op_1", "ADMIN", "INCIDENT_DECLARE", "tenant_1", "NORMAL", "CONTAINMENT", "SUCCESS")

    is_valid, errs = audit.verify_integrity()
    assert is_valid is True
    assert len(errs) == 0

    # Tamper with record 2 hash
    audit.records[1].record_hash = "0" * 64
    is_valid_tampered, errs_tampered = audit.verify_integrity()
    assert is_valid_tampered is False
    assert len(errs_tampered) > 0
