# AegisTrace Incident Response & Forensic Preservation Guide

## 1. 12-State Incident Lifecycle State Machine

AegisTrace implements a formal, finite-state machine governing the lifecycle of security incidents, compromised credentials, and emergency recovery operations:

```
                      +------------------------+
                      |         NORMAL         |
                      +-----------+------------+
                                  |
                                  v
                      +------------------------+
                      |  SUSPECTED_COMPROMISE  |<--------+ (False Alarm)
                      +-----------+------------+         |
                                  |                      |
                                  v                      |
                      +------------------------+         |
         +----------->|      CONTAINMENT       +---------+
         |            +-----------+------------+
         |                        |
         |                        v
+--------+-----------+  +------------------------+
|  KEY_COMPROMISED   |  | FORENSIC_PRESERVATION  |
+--------------------+  +-----------+------------+
                                  |
                                  v
                      +------------------------+
                      |  RECOVERY_VALIDATION   |
                      +---+--------+-------+---+
                          |        |       |
            +-------------+        |       +---------------+
            v                      v                       v
+-----------------------+ +-----------------+  +----------------------+
|    RECOVERY_FAILED    | | EVIDENCE_CONFLICT| |  ROLLBACK_DETECTED   |
+-----------+-----------+ +--------+--------+  +-----------+----------+
            |                      |                       |
            +------------+         |         +-------------+
                         v         v         v
                      +------------------------+
                      | REQUIRES_MANUAL_REVIEW |
                      +-----------+------------+
                                  |
                                  v (Dual Control)
                      +------------------------+
                      |        RESTORED        |
                      +-----------+------------+
                                  |
                                  v
                      +------------------------+
                      |  POST_INCIDENT_REVIEW  |
                      +-----------+------------+
                                  |
                                  v
                      +------------------------+
                      |         NORMAL         |
                      +------------------------+
```

---

## 2. Permitted Transitions Matrix

| Current State | Permitted Next States | Authorization Rule |
| :--- | :--- | :--- |
| `NORMAL` | `SUSPECTED_COMPROMISE`, `FORENSIC_PRESERVATION`, `KEY_COMPROMISED`, `REQUIRES_MANUAL_REVIEW` | Single Operator |
| `SUSPECTED_COMPROMISE` | `CONTAINMENT`, `FORENSIC_PRESERVATION`, `NORMAL`, `KEY_COMPROMISED`, `REQUIRES_MANUAL_REVIEW` | Single Operator |
| `CONTAINMENT` | `FORENSIC_PRESERVATION`, `KEY_COMPROMISED`, `RECOVERY_VALIDATION`, `REQUIRES_MANUAL_REVIEW` | Incident Commander / Admin |
| `KEY_COMPROMISED` | `CONTAINMENT`, `FORENSIC_PRESERVATION`, `REQUIRES_MANUAL_REVIEW` | Security Officer / Admin |
| `FORENSIC_PRESERVATION`| `RECOVERY_VALIDATION`, `CONTAINMENT`, `REQUIRES_MANUAL_REVIEW` | Forensic Officer |
| `RECOVERY_VALIDATION` | `RESTORED` *(requires dual control)*, `RECOVERY_FAILED`, `EVIDENCE_CONFLICT`, `ROLLBACK_DETECTED`, `FORENSIC_PRESERVATION`, `REQUIRES_MANUAL_REVIEW` | Dual Authorization for `RESTORED` |
| `RESTORED` | `POST_INCIDENT_REVIEW`, `NORMAL`, `REQUIRES_MANUAL_REVIEW` | Lead Operator |
| `POST_INCIDENT_REVIEW` | `NORMAL`, `REQUIRES_MANUAL_REVIEW` | Incident Commander |
| `RECOVERY_FAILED` | `RECOVERY_VALIDATION`, `REQUIRES_MANUAL_REVIEW` | Recovery Lead |
| `EVIDENCE_CONFLICT` | `REQUIRES_MANUAL_REVIEW` | Fail-closed |
| `ROLLBACK_DETECTED` | `REQUIRES_MANUAL_REVIEW` | Fail-closed |
| `REQUIRES_MANUAL_REVIEW`| `NORMAL`, `SUSPECTED_COMPROMISE`, `CONTAINMENT`, `FORENSIC_PRESERVATION`, `RECOVERY_VALIDATION`, `RESTORED`, `POST_INCIDENT_REVIEW` | **Dual Control Mandatory** |

---

## 3. Forensic Preservation Mode & Immutable Write-Freezes

During active breaches, accidental evidence destruction or covert rollback is prevented via Forensic Preservation Mode:
1. When entering `FORENSIC_PRESERVATION`, `is_preservation_active` evaluates to `True`.
2. Any write, update, or deletion operation on evidence, ledger, lineage, or keys raises:
   ```
   PermissionError: PRESERVATION_MODE_ACTIVE: Mutation of '<component>' is blocked during forensic preservation.
   ```
3. Forensic examiners can capture immutable, content-addressed SHA-256 snapshots of live states prior to recovery initiation:
   ```python
   snapshot = preservation_engine.capture_state_snapshot("ledger", live_ledger_data, "op_forensics")
   ```

---

## 4. Temporal Validity Analysis for Compromised Keys

When a cryptographic key (recipient ML-DSA key, server token, or master keystore) is compromised, historical evidence must not be blindly discarded:
- **Pre-Compromise Evidence**: Generated strictly before $T_{\text{compromise}}$. Validated as legally and forensically sound (`EVIDENCE_VALID`).
- **Post-Compromise Evidence**: Generated at or after $T_{\text{compromise}}$. Marked `EVIDENCE_SUSPECT` or `EVIDENCE_REJECTED`. Digital signatures after compromise cannot be attributed to the genuine key owner.

```python
decision = incident_engine.evaluate_temporal_validity(
    event_timestamp="2026-09-20T10:15:00Z",
    compromise_timestamp="2026-09-25T00:00:00Z",
    item_id="receipt_4920",
    item_type="DECRYPTION_RECEIPT"
)
assert decision.status == "EVIDENCE_VALID"
```

---

## 5. Separation of Duties (Dual Control)

Sensitive actions require two distinct operators with appropriate roles:
- **Action**: Transition to `RESTORED` or Exit from `REQUIRES_MANUAL_REVIEW`.
- **Primary Operator**: Initiates request (e.g., `RECOVERY_OPERATOR`).
- **Dual Authorizer**: Endorses request (e.g., `SECURITY_ADMIN`, `CISO`, `SECURITY_OFFICER`).
- If `dual_authorizer_id == operator_id`: Returns `DUAL_CONTROL_VIOLATION`.
- If `dual_authorizer_id is None`: Returns `DUAL_CONTROL_REQUIRED`.
