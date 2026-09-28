"""
AegisTrace Tamper-Evident Recovery Audit Trail Engine.

Maintains an independent, hash-chained audit log of all privileged recovery,
restoration, rollback, key extraction, and incident-response actions.
Guarantees non-circular trust: audit logs do not depend on the state being recovered.
Enforces separation of duties and dual-authorization for security-sensitive recovery actions.
"""

from datetime import datetime, timezone
import hashlib
import json
import os
import threading
from typing import List, Dict, Optional, Any, Set, Tuple

from core.recovery.models import RecoveryAuditRecord


class AuditSecurityViolation(PermissionError):
    """Raised when separation of duties or authorization requirements are violated."""
    pass


class AuditIntegrityViolation(ValueError):
    """Raised when audit record hash chain verification fails."""
    pass


class RecoveryAuditLog:
    """
    Independent hash-chained recovery audit trail.
    Enforces sequential cryptographic chaining from genesis.
    """
    GENESIS_HASH = "0" * 64

    # Actions that strictly require two distinct authorized actors (Separation of Duties)
    SENSITIVE_ACTIONS: Set[str] = {
        "ROLLBACK_OVERRIDE",
        "BREAK_GLASS_UNFREEZE",
        "PURGE_QUARANTINE",
        "FORCE_CORRUPTED_RESTORE",
        "EMERGENCY_KEY_REVOCATION",
        "DISASTER_RECOVERY_OVERRIDE",
    }

    # Roles permitted to act as primary operator
    OPERATOR_ROLES: Set[str] = {
        "OPERATOR",
        "RECOVERY_LEAD",
        "SYSTEM_ADMIN",
        "SECURITY_OFFICER",
        "AUDITOR",
        "ADMIN",
        "RECOVERY_OPERATOR",
        "SECURITY_ADMIN",
        "INCIDENT_COMMANDER",
        "FORENSIC_OFFICER",
    }

    # Roles permitted to provide dual-authorization endorsement
    DUAL_AUTHORIZER_ROLES: Set[str] = {
        "SECURITY_OFFICER",
        "AUDITOR",
        "CISO",
        "SECURITY_ADMIN",
        "ADMIN",
        "INCIDENT_COMMANDER",
        "RECOVERY_LEAD",
    }

    def __init__(self, log_path: Optional[str] = None):
        self._lock = threading.RLock()
        self.log_path = log_path
        self.records: List[RecoveryAuditRecord] = []
        self._record_hashes: List[str] = []
        self._seen_audit_ids: Set[str] = set()

        if self.log_path and os.path.exists(self.log_path):
            self._load_from_disk()

    def get_tip_hash(self) -> str:
        with self._lock:
            if not self._record_hashes:
                return self.GENESIS_HASH
            return self._record_hashes[-1]

    def record_action(
        self,
        operator_id: str,
        operator_role: str,
        action: str,
        tenant_id: str,
        previous_state: str = "NORMAL",
        new_state: str = "NORMAL",
        result: str = "SUCCESS",
        target_backup_id: Optional[str] = None,
        target_recovery_id: Optional[str] = None,
        failure_reason: Optional[str] = None,
        dual_authorizer_id: Optional[str] = None,
        dual_authorizer_role: Optional[str] = None,
    ) -> RecoveryAuditRecord:
        """
        Appends an audit record to the hash chain, enforcing separation of duties.
        """
        with self._lock:
            # Enforce operator role validation
            if operator_role not in self.OPERATOR_ROLES:
                raise AuditSecurityViolation(
                    f"UNAUTHORIZED_OPERATOR_ROLE: Role '{operator_role}' is not authorized."
                )

            # Enforce separation of duties for sensitive operations
            if action in self.SENSITIVE_ACTIONS:
                if not dual_authorizer_id:
                    raise AuditSecurityViolation(
                        f"SEPARATION_OF_DUTIES_VIOLATION: Action '{action}' requires dual-authorization."
                    )
                if dual_authorizer_id == operator_id:
                    raise AuditSecurityViolation(
                        f"SEPARATION_OF_DUTIES_VIOLATION: Dual authorizer '{dual_authorizer_id}' cannot be identical to primary operator."
                    )
                if dual_authorizer_role and dual_authorizer_role not in self.DUAL_AUTHORIZER_ROLES:
                    raise AuditSecurityViolation(
                        f"SEPARATION_OF_DUTIES_VIOLATION: Role '{dual_authorizer_role}' not permitted as dual authorizer."
                    )

            audit_id = f"aud_{hashlib.sha256(os.urandom(16)).hexdigest()[:20]}"
            now_str = datetime.now(timezone.utc).isoformat()
            prev_hash = self.get_tip_hash()

            record = RecoveryAuditRecord(
                audit_id=audit_id,
                timestamp=now_str,
                operator_id=operator_id,
                operator_role=operator_role,
                action=action,
                tenant_id=tenant_id,
                target_backup_id=target_backup_id,
                target_recovery_id=target_recovery_id,
                previous_state=previous_state,
                new_state=new_state,
                result=result,
                failure_reason=failure_reason,
                dual_authorizer_id=dual_authorizer_id,
                previous_record_hash=prev_hash,
            )
            rec_hash = record.compute_record_hash()
            record.record_hash = rec_hash

            self.records.append(record)
            self._record_hashes.append(rec_hash)
            self._seen_audit_ids.add(audit_id)

            if self.log_path:
                self._append_to_disk(record)

            return record

    def append_record(
        self,
        operator_id: str,
        operator_role: str,
        action: str,
        tenant_id: str,
        target_backup_id: Optional[str] = None,
        target_recovery_id: Optional[str] = None,
        previous_state: str = "NORMAL",
        new_state: str = "NORMAL",
        result: str = "SUCCESS",
        failure_reason: Optional[str] = None,
        dual_authorizer_id: Optional[str] = None,
        dual_authorizer_role: Optional[str] = None,
    ) -> RecoveryAuditRecord:
        """Alias for record_action to support both interfaces."""
        return self.record_action(
            operator_id=operator_id,
            operator_role=operator_role,
            action=action,
            tenant_id=tenant_id,
            previous_state=previous_state,
            new_state=new_state,
            result=result,
            target_backup_id=target_backup_id,
            target_recovery_id=target_recovery_id,
            failure_reason=failure_reason,
            dual_authorizer_id=dual_authorizer_id,
            dual_authorizer_role=dual_authorizer_role,
        )

    def verify_integrity(self) -> Tuple[bool, List[str]]:
        """
        Verifies the full cryptographic hash chain of the audit log.
        """
        with self._lock:
            errors = []
            prev_hash = self.GENESIS_HASH

            for idx, rec in enumerate(self.records):
                if rec.previous_record_hash != prev_hash:
                    errors.append(
                        f"AUDIT_CHAIN_BROKEN at index {idx} ({rec.audit_id}): "
                        f"previous_record_hash '{rec.previous_record_hash}' != expected '{prev_hash}'"
                    )
                computed = rec.compute_record_hash()
                if rec.record_hash != computed:
                    errors.append(
                        f"AUDIT_RECORD_CORRUPTED at index {idx} ({rec.audit_id}): "
                        f"stored hash '{rec.record_hash}' != computed '{computed}'"
                    )
                prev_hash = computed

            return len(errors) == 0, errors

    def verify_audit_chain(self) -> Tuple[bool, List[str]]:
        """Alias for verify_integrity."""
        return self.verify_integrity()

    def to_dict_list(self) -> List[Dict[str, Any]]:
        with self._lock:
            return [rec.dict() for rec in self.records]

    def _append_to_disk(self, record: RecoveryAuditRecord) -> None:
        try:
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record.dict(), sort_keys=True) + "\n")
        except Exception:
            pass

    def _load_from_disk(self) -> None:
        try:
            with open(self.log_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    data = json.loads(line)
                    rec = RecoveryAuditRecord(**data)
                    self.records.append(rec)
                    self._record_hashes.append(rec.record_hash or rec.compute_record_hash())
                    self._seen_audit_ids.add(rec.audit_id)
        except Exception:
            pass

    def load_from_file(self, file_path: str) -> None:
        self.log_path = file_path
        self._load_from_disk()
