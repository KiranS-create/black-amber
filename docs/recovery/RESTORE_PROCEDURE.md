# AegisTrace State Restoration & Reconstitution Procedure

## 1. Scope & Objective

This document prescribes the formal operational procedures for reconstituting AegisTrace state from immutable, content-addressed backup archives. It applies to bare-metal disasters, cluster failovers, corruption recovery, and sandbox verification drills.

---

## 2. Pre-Restoration Security Pre-Flight

Before any state reconstitution is initiated:
1. **Engage Forensic Preservation**:
   If the recovery is responding to suspected corruption, breach, or compromise, engage forensic preservation mode:
   ```python
   incident_engine.transition_to(IncidentTransitionRequest(
       requested_state=IncidentState.FORENSIC_PRESERVATION,
       operator_id="op_lead",
       operator_role=OperatorRole.FORENSIC_OFFICER,
       reason="Freezing volatile disks prior to restore"
   ))
   ```
2. **Verify Offline Signature of Target Manifest**:
   ```python
   is_valid, err = BackupCryptoEngine.verify_manifest(manifest, authority_public_key)
   assert is_valid, f"Manifest signature check failed: {err}"
   ```
3. **Verify Tenant Isolation Boundary**:
   Ensure `manifest.tenant_id == target_tenant_id`. Cross-tenant restoration attempts will immediately fail closed.
4. **Monotonic Sequence Audit**:
   Confirm `manifest.backup_sequence >= current_tenant_sequence`. If rolling back to an earlier sequence, obtain dual-operator authorization.

---

## 3. Standard Restoration Workflow

Restoration is performed via the `DisasterRecoveryEngine`:

```python
from core.recovery.engine import DisasterRecoveryEngine
from core.recovery.models import FinalRecoveryOutcome

engine = DisasterRecoveryEngine(storage=content_addressed_store)

report = engine.restore_backup(
    manifest=target_manifest,
    expected_tenant_id="tenant_defense_hq",
    encryption_passphrase=master_passphrase,  # If encrypted
    authority_public_key_bytes=root_authority_pubkey,
    allow_tail_truncation=False,  # Set True only during authorized partial recovery
    operator_id="operator_alice",
    operator_role="RECOVERY_OPERATOR",
)

if report.final_recovery_state == FinalRecoveryOutcome.RECOVERED:
    print(f"Restore succeeded in {report.recovery_duration_ms:.2f} ms")
elif report.final_recovery_state == FinalRecoveryOutcome.PARTIALLY_RECOVERED:
    print(f"Partial recovery: Clean prefix restored, tail quarantined.")
else:
    raise RuntimeError(f"Restoration failed: {'; '.join(report.errors)}")
```

---

## 4. Reconstitution Ordering Across Subsystems

To prevent dependency cycles and broken foreign keys, state reconstitution executes in strict chronological and dependency order:

```
[1. Cryptographic Keystores & Rotation Epochs]
                      │
                      ▼
[2. Recipient Identity Directory & Policy Rules]
                      │
                      ▼
[3. Tamper-Evident Ledger & Merkle Trees]
                      │
                      ▼
[4. Document Lineage Graph Roots & Copies]
                      │
                      ▼
[5. Dynamic Watermark Token Commitments]
                      │
                      ▼
[6. EDR, Print & DLP Telemetry Stream Deduplication]
                      │
                      ▼
[7. Multi-Channel Evidence Bundles & Attribution Cases]
                      │
                      ▼
[8. BFT Validator Quorum & Ledger Tip Reconstitution]
```

---

## 5. Handling Data Corruptions & Forks

### 5.1. Tail Corruption Quarantine
When a storage volume fails mid-write:
- The `LedgerRecoveryEngine` isolates the point of corruption:
  - If `allow_tail_truncation=False`, the recovery fails closed (`CORRUPTED_RECOVERY`).
  - If `allow_tail_truncation=True` (and approved by incident commanders), the engine restores the valid prefix up to the corruption point, marks the outcome as `PARTIALLY_RECOVERED`, and saves the corrupted tail into quarantine for forensic analysis.

### 5.2. Conflicting Branches & Forks
If the restored tip hash does not match the authoritative Merkle checkpoint or BFT quorum tip, the engine reports `CONFLICTING_RECOVERY`. The engine halts and transitions the incident response state machine to `EVIDENCE_CONFLICT`.

---

## 6. Recovery Verification Report (`RecoveryVerificationReport`)

Every restoration run emits a cryptographically verifiable report:
```json
{
  "recovery_id": "rec_3b9f8a12...",
  "backup_id": "bak_0a8b7c6d...",
  "tenant_id": "tenant_defense_hq",
  "ledger_status": "VALID_RECOVERY",
  "lineage_status": "VALID_RECOVERY",
  "telemetry_status": "VALID_RECOVERY",
  "identity_status": "VALID_RECOVERY",
  "evidence_status": "VALID_RECOVERY",
  "key_status": "VALID_RECOVERY",
  "rollback_status": "VALID_RECOVERY",
  "chain_status": "VALID_RECOVERY",
  "tenant_boundary_status": "VALID_RECOVERY",
  "final_recovery_state": "RECOVERED",
  "components": {
    "ledger": {
      "component_name": "ledger",
      "status": "VALID_RECOVERY",
      "records_recovered": 100000,
      "records_quarantined": 0,
      "errors": []
    }
  },
  "recovery_duration_ms": 142.5
}
```

---

## 7. Dual-Controlled Exit from Recovery

Once verification passes:
1. Transition lifecycle to `RESTORED` with dual-authorization endorsement:
   ```python
   incident_engine.transition_to(IncidentTransitionRequest(
       requested_state=IncidentState.RESTORED,
       operator_id="operator_alice",
       operator_role=OperatorRole.RECOVERY_OPERATOR,
       dual_authorizer_id="admin_bob",
       dual_authorizer_role=OperatorRole.SECURITY_ADMIN,
       reason="All subsystem cryptographic checks verified green"
   ))
   ```
2. Resume production traffic.
