# AegisTrace Disaster Recovery & Incident Response Runbook

## 1. Quick Reference: Incident Escalation & Response Flow

```
[ALERT TRIGGERED] -> Triage Anomaly
       │
       ▼
[STEP 1: Declare Incident] -> Transition to SUSPECTED_COMPROMISE
       │
       ▼
[STEP 2: Engage Forensic Freeze] -> Transition to FORENSIC_PRESERVATION
       │
       ▼
[STEP 3: Capture Volatile Snapshots] -> Content-Addressed Hash Snapshots
       │
       ▼
[STEP 4: Select Authoritative Backup] -> Verify Manifest & Post-Quantum Sig
       │
       ▼
[STEP 5: Execute Staged Restoration] -> Transition to RECOVERY_VALIDATION
       │
       ▼
[STEP 6: Audit Cryptographic Verification] -> Validate Report Outcomes
       │
       ▼
[STEP 7: Dual-Authorized Exit] -> Transition to RESTORED (Dual Control)
       │
       ▼
[STEP 8: Resume Production] -> Transition to NORMAL
```

---

## 2. Phase-by-Phase Operator Runbook

### Phase 1: Incident Declaration & Triage
When automated anomaly detectors (e.g., decryption burst, corrupted block signature, or unexpected tampering alert) fire:
```python
from core.recovery.incident import IncidentResponseEngine, IncidentTransitionRequest, OperatorRole
from core.recovery.models import IncidentState

incident_engine = IncidentResponseEngine()

# Declare incident
ok, err = incident_engine.transition_to(IncidentTransitionRequest(
    requested_state=IncidentState.SUSPECTED_COMPROMISE,
    operator_id="operator_oncall",
    operator_role=OperatorRole.INCIDENT_COMMANDER,
    reason="Anomalous decryption burst observed from unverified IP."
))
assert ok, f"Transition failed: {err}"
```

### Phase 2: Immediate Forensic Preservation Freeze
Block all mutations across live storage volumes to prevent evidence tampering:
```python
ok, err = incident_engine.transition_to(IncidentTransitionRequest(
    requested_state=IncidentState.FORENSIC_PRESERVATION,
    operator_id="operator_oncall",
    operator_role=OperatorRole.FORENSIC_OFFICER,
    reason="Freezing all storage volumes for forensic snapshotting."
))
assert ok, f"Freeze failed: {err}"
assert incident_engine.is_preservation_active is True
```

### Phase 3: Evidence Capture & Snapshotting
Capture immutable SHA-256 snapshots of live volatile database states:
```python
snap = incident_engine.preservation_engine.capture_state_snapshot(
    dataset_name="ledger",
    state_data=live_ledger.to_dict_list(),
    operator_id="operator_oncall"
)
print(f"Captured snapshot {snap['snapshot_id']} with digest {snap['digest']}")
```

### Phase 4: Stage Verified Backup
Transition to `RECOVERY_VALIDATION` to stage backup restoration in isolated sandbox:
```python
ok, err = incident_engine.transition_to(IncidentTransitionRequest(
    requested_state=IncidentState.RECOVERY_VALIDATION,
    operator_id="operator_recovery_lead",
    operator_role=OperatorRole.RECOVERY_OPERATOR,
    reason="Initiating staged recovery from backup bak_9c4e2a81."
))
```

### Phase 5: Execute Restoration Engine
```python
from core.recovery.engine import DisasterRecoveryEngine
from core.recovery.models import FinalRecoveryOutcome

recovery_engine = DisasterRecoveryEngine(storage=store)

report = recovery_engine.restore_backup(
    manifest=target_signed_manifest,
    expected_tenant_id="tenant_defense_01",
    encryption_passphrase=os.environ.get("AEGIS_BACKUP_PASSPHRASE"),
    authority_public_key_bytes=root_authority_pubkey,
    allow_tail_truncation=False,  # Set True only if authorized by Incident Commander
    operator_id="operator_recovery_lead",
    operator_role="RECOVERY_OPERATOR"
)

if report.final_recovery_state != FinalRecoveryOutcome.RECOVERED:
    raise RuntimeError(f"Recovery failed verification: {report.errors}")
```

### Phase 6: Dual-Authorized Finalization (`RESTORED`)
Exiting recovery validation into `RESTORED` strictly requires dual authorization:
```python
ok, err = incident_engine.transition_to(IncidentTransitionRequest(
    requested_state=IncidentState.RESTORED,
    operator_id="operator_recovery_lead",
    operator_role=OperatorRole.RECOVERY_OPERATOR,
    dual_authorizer_id="admin_sec_officer",
    dual_authorizer_role=OperatorRole.SECURITY_ADMIN,
    reason="All 24 subsystem recovery checks green; cryptographic hash chain intact."
))
assert ok, f"Dual control failed: {err}"
```

---

## 3. Troubleshooting Matrix

| Observed Error | Root Cause | Operator Action |
| :--- | :--- | :--- |
| `ROLLBACK_DETECTED` | Target backup sequence is lower than the tenant's current highest sequence counter. | Verify if intentional rollback. If intentional, pass `allow_rollback=True` and provide an independent `dual_authorizer_id`. |
| `TENANT_ISOLATION_VIOLATION` | Backup was created for a different tenant. | Refuse restoration. Cross-tenant restoration violates isolation boundaries. Verify target tenant ID. |
| `MANIFEST_SIGNATURE_INVALID` | Manifest bytes or signature tampered; wrong authority key. | Verify `authority_public_key_bytes`. Check if manifest JSON was altered in transit. |
| `MERKLE_ROOT_MISMATCH` | One or more content-addressed chunk files corrupted or missing. | Check CAS chunk store integrity. Run storage disk fsck. Attempt recovery from replica media. |
| `BROKEN_CHAIN_LINK` | Ledger event sequential hash chain broken at index $k$. | Inspect quarantined events. If authorized to discard corrupted tail, execute with `allow_tail_truncation=True`. |
| `DUAL_CONTROL_VIOLATION` | `dual_authorizer_id` matches `operator_id`. | Separation of duties violation. A distinct authorized security officer must provide dual authorization. |

---

## 4. Post-Incident Review Checklist

- [ ] Archive all volatile memory and disk snapshots captured during `FORENSIC_PRESERVATION`.
- [ ] Verify tamper-evident integrity of `RecoveryAuditLog` hash chain:
  ```python
  is_valid, errs = audit_log.verify_integrity()
  assert is_valid, f"Audit chain broken: {errs}"
  ```
- [ ] Document root cause analysis (RCA) in case management system.
- [ ] Transition lifecycle from `RESTORED` $\rightarrow$ `POST_INCIDENT_REVIEW` $\rightarrow$ `NORMAL`.
