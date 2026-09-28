"""
AegisTrace Cryptographic Key Lifecycle Manager.

Thread-safe orchestration of key generation, enrollment, activation, rotation,
suspension, revocation, compromise reporting, and multi-tenant isolation.
"""

from datetime import datetime, timezone
import os
import threading
from typing import Dict, List, Optional, Tuple, Any

from core.crypto.lifecycle.models import (
    KeyRecord,
    KeyState,
    KeyType,
    KeyCustodyClass,
    KeyRecoveryClassification,
    generate_key_id,
)
from core.crypto.lifecycle.state_machine import KeyStateMachine, KeyLifecycleTransitionError
from core.crypto.lifecycle.audit import KeyLifecycleAuditLogger, default_key_audit_logger


class KeyCustodyError(PermissionError):
    """Raised when key custody rules are violated (e.g. dev keys in production)."""
    pass


class KeyLifecycleManager:
    """
    Production-grade Key Lifecycle Manager.
    Guarantees thread-safe atomic transitions, strict tenant isolation,
    and fail-closed revocation boundaries.
    """
    def __init__(self, audit_logger: Optional[KeyLifecycleAuditLogger] = None):
        self.audit_logger = audit_logger or default_key_audit_logger
        self._records: Dict[str, KeyRecord] = {}  # key_id -> KeyRecord
        
        # Primary lookup index: (owner, key_type, algorithm, tenant_id) -> List[key_id] (sorted by epoch)
        self._owner_index: Dict[Tuple[str, str, str, str], List[str]] = {}
        
        # Active key index: (owner, key_type, algorithm, tenant_id) -> active key_id
        self._active_index: Dict[Tuple[str, str, str, str], str] = {}
        
        self._lock = threading.RLock()
        self._entity_locks: Dict[Tuple[str, str, str, str], threading.Lock] = {}

    def _get_entity_lock(self, owner: str, key_type: KeyType, algorithm: str, tenant_id: str) -> threading.Lock:
        key = (owner, key_type.value, algorithm, tenant_id)
        with self._lock:
            if key not in self._entity_locks:
                self._entity_locks[key] = threading.Lock()
            return self._entity_locks[key]

    def _validate_custody_policy(self, custody_class: KeyCustodyClass) -> None:
        """Enforces that DEVELOPMENT_ONLY keys fail closed in production mode."""
        env_mode = os.environ.get("AEGISTRACE_ENV", os.environ.get("SIH26237_ENV", "")).lower()
        if env_mode == "production" and custody_class == KeyCustodyClass.DEVELOPMENT_ONLY:
            raise KeyCustodyError(
                "PRODUCTION_CUSTODY_VIOLATION: DEVELOPMENT_ONLY key custody is strictly prohibited in production."
            )

    def register_key(
        self,
        owner: str,
        key_type: KeyType,
        algorithm: str,
        purpose: str,
        tenant_id: str = "default_tenant",
        epoch: int = 1,
        custody_class: KeyCustodyClass = KeyCustodyClass.LOCAL_PROTECTED_STORE,
        recovery_class: KeyRecoveryClassification = KeyRecoveryClassification.RECOVERABLE,
        public_material_b64: Optional[str] = None,
        encrypted_private_material_b64: Optional[str] = None,
        activate_immediately: bool = False,
        authorized_actor: str = "SYSTEM_ADMIN",
        metadata: Optional[Dict[str, Any]] = None
    ) -> KeyRecord:
        """
        Registers a newly generated key record.
        """
        self._validate_custody_policy(custody_class)
        entity_key = (owner, key_type.value, algorithm, tenant_id)

        with self._get_entity_lock(owner, key_type, algorithm, tenant_id):
            with self._lock:
                key_id = generate_key_id(owner, key_type, epoch)
                now_iso = datetime.now(timezone.utc).isoformat()

                record = KeyRecord(
                    key_id=key_id,
                    key_type=key_type,
                    algorithm=algorithm,
                    purpose=purpose,
                    owner=owner,
                    tenant_id=tenant_id,
                    creation_epoch=epoch,
                    status=KeyState.GENERATED,
                    creation_timestamp=now_iso,
                    storage_class=custody_class,
                    recovery_class=recovery_class,
                    public_material_b64=public_material_b64,
                    encrypted_private_material_b64=encrypted_private_material_b64,
                    metadata=metadata or {}
                )

                self._records[key_id] = record
                self._owner_index.setdefault(entity_key, []).append(key_id)

                self.audit_logger.log_transition(
                    record=record,
                    previous_state=KeyState.UNKNOWN,
                    new_state=KeyState.GENERATED,
                    reason="Initial registration",
                    authorized_actor=authorized_actor,
                    timestamp=now_iso
                )

                if activate_immediately:
                    self._activate_key_internal(record, authorized_actor=authorized_actor, timestamp=now_iso)

                return record

    def _activate_key_internal(self, record: KeyRecord, authorized_actor: str, timestamp: str) -> None:
        entity_key = (record.owner, record.key_type.value, record.algorithm, record.tenant_id)
        prev_state = record.status
        
        # Retire previously active key of same algorithm if exists and not same
        curr_active_id = self._active_index.get(entity_key)
        if curr_active_id and curr_active_id != record.key_id:
            curr_active = self._records[curr_active_id]
            if curr_active.status == KeyState.ACTIVE:
                KeyStateMachine.transition(curr_active, KeyState.RETIRED, reason=f"Superseded by {record.key_id}", timestamp=timestamp)
                self.audit_logger.log_transition(
                    record=curr_active,
                    previous_state=KeyState.ACTIVE,
                    new_state=KeyState.RETIRED,
                    reason=f"Superseded by {record.key_id}",
                    authorized_actor=authorized_actor,
                    timestamp=timestamp
                )

        KeyStateMachine.transition(record, KeyState.ACTIVE, reason="Activation", timestamp=timestamp)
        self._active_index[entity_key] = record.key_id

        self.audit_logger.log_transition(
            record=record,
            previous_state=prev_state,
            new_state=KeyState.ACTIVE,
            reason="Activation",
            authorized_actor=authorized_actor,
            timestamp=timestamp
        )

    def activate_key(
        self,
        key_id: str,
        tenant_id: str = "default_tenant",
        authorized_actor: str = "SYSTEM_ADMIN"
    ) -> KeyRecord:
        """Activates a registered key."""
        with self._lock:
            record = self.get_key(key_id, tenant_id=tenant_id)
            if not record:
                raise KeyError(f"Key '{key_id}' not found in tenant '{tenant_id}'")

        with self._get_entity_lock(record.owner, record.key_type, record.algorithm, tenant_id):
            with self._lock:
                now_iso = datetime.now(timezone.utc).isoformat()
                self._activate_key_internal(record, authorized_actor, now_iso)
                return record

    def rotate_key(
        self,
        owner: str,
        key_type: KeyType,
        algorithm: Optional[str] = None,
        new_algorithm: Optional[str] = None,
        new_purpose: Optional[str] = None,
        new_public_material_b64: Optional[str] = None,
        new_encrypted_private_material_b64: Optional[str] = None,
        tenant_id: str = "default_tenant",
        custody_class: Optional[KeyCustodyClass] = None,
        authorized_actor: str = "SECURITY_OFFICER",
        reason: str = "Scheduled cryptographic rotation"
    ) -> Tuple[KeyRecord, KeyRecord]:
        """
        Executes atomic key rotation:
        - Locates current active key for (owner, key_type, algorithm).
        - Generates successor key with epoch = current_epoch + 1.
        - Updates predecessor and successor links.
        - Transitions current key from ACTIVE -> ROTATING -> RETIRED.
        - Transitions successor key to ACTIVE.
        Returns: (predecessor_record, successor_record)
        """
        with self._lock:
            target_algo = algorithm or new_algorithm
            if target_algo:
                entity_key = (owner, key_type.value, target_algo, tenant_id)
                current_active_id = self._active_index.get(entity_key)
            else:
                matches = [(k, v) for k, v in self._active_index.items() if k[0] == owner and k[1] == key_type.value and k[3] == tenant_id]
                if not matches:
                    current_active_id = None
                    target_algo = "DEFAULT"
                else:
                    entity_key, current_active_id = matches[0]
                    target_algo = entity_key[2]

            if not current_active_id or current_active_id not in self._records:
                raise ValueError(f"No active key found to rotate for ({owner}, {key_type.value}, {target_algo}) in tenant '{tenant_id}'")

            prev_key = self._records[current_active_id]
            target_algo = prev_key.algorithm

        with self._get_entity_lock(owner, key_type, target_algo, tenant_id):
            with self._lock:
                if prev_key.status != KeyState.ACTIVE:
                    raise KeyLifecycleTransitionError(f"Cannot rotate key in state {prev_key.status.value}")

                now_iso = datetime.now(timezone.utc).isoformat()
                next_epoch = prev_key.creation_epoch + 1
                succ_algo = new_algorithm or prev_key.algorithm

                # Step 1: Mark predecessor as ROTATING
                KeyStateMachine.transition(prev_key, KeyState.ROTATING, reason=reason, timestamp=now_iso)
                self.audit_logger.log_transition(
                    record=prev_key,
                    previous_state=KeyState.ACTIVE,
                    new_state=KeyState.ROTATING,
                    reason=reason,
                    authorized_actor=authorized_actor,
                    timestamp=now_iso
                )

                # Step 2: Register successor key
                new_key_id = generate_key_id(owner, key_type, next_epoch)
                successor = KeyRecord(
                    key_id=new_key_id,
                    key_type=key_type,
                    algorithm=succ_algo,
                    purpose=new_purpose or prev_key.purpose,
                    owner=owner,
                    tenant_id=tenant_id,
                    creation_epoch=next_epoch,
                    status=KeyState.GENERATED,
                    creation_timestamp=now_iso,
                    predecessor_key_id=prev_key.key_id,
                    storage_class=custody_class or prev_key.storage_class,
                    recovery_class=prev_key.recovery_class,
                    public_material_b64=new_public_material_b64,
                    encrypted_private_material_b64=new_encrypted_private_material_b64
                )

                # Link predecessor to successor
                prev_key.successor_key_id = successor.key_id

                succ_entity_key = (owner, key_type.value, succ_algo, tenant_id)
                prev_entity_key = (owner, key_type.value, prev_key.algorithm, tenant_id)

                self._records[new_key_id] = successor
                self._owner_index.setdefault(succ_entity_key, []).append(new_key_id)

                self.audit_logger.log_transition(
                    record=successor,
                    previous_state=KeyState.UNKNOWN,
                    new_state=KeyState.GENERATED,
                    reason=f"Successor in rotation of {prev_key.key_id}",
                    authorized_actor=authorized_actor,
                    timestamp=now_iso
                )

                # Step 3: Activate successor
                KeyStateMachine.transition(successor, KeyState.ACTIVE, reason="Rotation cutover", timestamp=now_iso)
                self._active_index[succ_entity_key] = successor.key_id
                self.audit_logger.log_transition(
                    record=successor,
                    previous_state=KeyState.GENERATED,
                    new_state=KeyState.ACTIVE,
                    reason="Rotation cutover",
                    authorized_actor=authorized_actor,
                    timestamp=now_iso
                )

                # Step 4: Retire predecessor
                KeyStateMachine.transition(prev_key, KeyState.RETIRED, reason=f"Rotated to {successor.key_id}", timestamp=now_iso)
                if prev_entity_key != succ_entity_key and prev_entity_key in self._active_index:
                    del self._active_index[prev_entity_key]

                self.audit_logger.log_transition(
                    record=prev_key,
                    previous_state=KeyState.ROTATING,
                    new_state=KeyState.RETIRED,
                    reason=f"Rotated to {successor.key_id}",
                    authorized_actor=authorized_actor,
                    timestamp=now_iso
                )

                return prev_key, successor

    def revoke_key(
        self,
        key_id: str,
        reason: str,
        tenant_id: str = "default_tenant",
        authorized_actor: str = "SECURITY_OFFICER",
        timestamp: Optional[str] = None
    ) -> KeyRecord:
        """
        Permanently revokes a key for new operations.
        Sets T_revocation timestamp. Historical events before T_revocation remain verifiable.
        """
        with self._lock:
            record = self.get_key(key_id, tenant_id=tenant_id)
            if not record:
                raise KeyError(f"Key '{key_id}' not found in tenant '{tenant_id}'")

        with self._get_entity_lock(record.owner, record.key_type, record.algorithm, tenant_id):
            with self._lock:
                now_iso = timestamp or datetime.now(timezone.utc).isoformat()
                prev_state = record.status

                KeyStateMachine.transition(record, KeyState.REVOKED, reason=reason, timestamp=now_iso)

                # Clear active index if this was the active key
                entity_key = (record.owner, record.key_type.value, record.algorithm, tenant_id)
                if self._active_index.get(entity_key) == record.key_id:
                    del self._active_index[entity_key]

                self.audit_logger.log_transition(
                    record=record,
                    previous_state=prev_state,
                    new_state=KeyState.REVOKED,
                    reason=reason,
                    authorized_actor=authorized_actor,
                    timestamp=now_iso
                )
                return record

    def report_compromise(
        self,
        key_id: str,
        reason: str,
        tenant_id: str = "default_tenant",
        authorized_actor: str = "INCIDENT_RESPONDER",
        timestamp: Optional[str] = None
    ) -> KeyRecord:
        """
        Marks a key as COMPROMISED.
        Future operations are rejected. Historical events remain cryptographically verifiable
        but are flagged with COMPROMISED_KEY_HISTORICAL_VERIFIED.
        """
        with self._lock:
            record = self.get_key(key_id, tenant_id=tenant_id)
            if not record:
                raise KeyError(f"Key '{key_id}' not found in tenant '{tenant_id}'")

        with self._get_entity_lock(record.owner, record.key_type, record.algorithm, tenant_id):
            with self._lock:
                now_iso = timestamp or datetime.now(timezone.utc).isoformat()
                prev_state = record.status

                KeyStateMachine.transition(record, KeyState.COMPROMISED, reason=reason, timestamp=now_iso)

                entity_key = (record.owner, record.key_type.value, record.algorithm, tenant_id)
                if self._active_index.get(entity_key) == record.key_id:
                    del self._active_index[entity_key]

                self.audit_logger.log_transition(
                    record=record,
                    previous_state=prev_state,
                    new_state=KeyState.COMPROMISED,
                    reason=reason,
                    authorized_actor=authorized_actor,
                    timestamp=now_iso
                )
                return record

    def suspend_key(
        self,
        key_id: str,
        reason: str,
        tenant_id: str = "default_tenant",
        authorized_actor: str = "SECURITY_OFFICER"
    ) -> KeyRecord:
        with self._lock:
            record = self.get_key(key_id, tenant_id=tenant_id)
            if not record:
                raise KeyError(f"Key '{key_id}' not found in tenant '{tenant_id}'")

        with self._get_entity_lock(record.owner, record.key_type, record.algorithm, tenant_id):
            with self._lock:
                now_iso = datetime.now(timezone.utc).isoformat()
                prev_state = record.status
                KeyStateMachine.transition(record, KeyState.SUSPENDED, reason=reason, timestamp=now_iso)
                self.audit_logger.log_transition(
                    record=record,
                    previous_state=prev_state,
                    new_state=KeyState.SUSPENDED,
                    reason=reason,
                    authorized_actor=authorized_actor,
                    timestamp=now_iso
                )
                return record

    def unsuspend_key(
        self,
        key_id: str,
        reason: str,
        tenant_id: str = "default_tenant",
        authorized_actor: str = "SECURITY_OFFICER"
    ) -> KeyRecord:
        with self._lock:
            record = self.get_key(key_id, tenant_id=tenant_id)
            if not record:
                raise KeyError(f"Key '{key_id}' not found in tenant '{tenant_id}'")

        with self._get_entity_lock(record.owner, record.key_type, record.algorithm, tenant_id):
            with self._lock:
                now_iso = datetime.now(timezone.utc).isoformat()
                prev_state = record.status
                KeyStateMachine.transition(record, KeyState.ACTIVE, reason=reason, timestamp=now_iso)
                self.audit_logger.log_transition(
                    record=record,
                    previous_state=prev_state,
                    new_state=KeyState.ACTIVE,
                    reason=reason,
                    authorized_actor=authorized_actor,
                    timestamp=now_iso
                )
                return record

    def get_key(self, key_id: str, tenant_id: str = "default_tenant") -> Optional[KeyRecord]:
        """O(1) key lookup with strict tenant isolation."""
        with self._lock:
            record = self._records.get(key_id)
            if record and record.tenant_id == tenant_id:
                return record
            return None

    def get_active_key(
        self,
        owner: str,
        key_type: KeyType,
        algorithm: Optional[str] = None,
        tenant_id: str = "default_tenant"
    ) -> Optional[KeyRecord]:
        """Returns the current ACTIVE key for the principal, or None."""
        with self._lock:
            if algorithm:
                entity_key = (owner, key_type.value, algorithm, tenant_id)
                active_id = self._active_index.get(entity_key)
                if active_id:
                    record = self._records.get(active_id)
                    if record and record.status == KeyState.ACTIVE and record.tenant_id == tenant_id:
                        return record
                return None
            else:
                for (o, kt, algo, t), active_id in self._active_index.items():
                    if o == owner and kt == key_type.value and t == tenant_id:
                        rec = self._records.get(active_id)
                        if rec and rec.status == KeyState.ACTIVE and rec.tenant_id == tenant_id:
                            return rec
                return None

    def get_keys_for_owner(
        self,
        owner: str,
        key_type: KeyType,
        algorithm: Optional[str] = None,
        tenant_id: str = "default_tenant"
    ) -> List[KeyRecord]:
        """Returns all historical and current keys for an owner, sorted by epoch ascending."""
        with self._lock:
            if algorithm:
                entity_key = (owner, key_type.value, algorithm, tenant_id)
                key_ids = self._owner_index.get(entity_key, [])
                records = [self._records[kid] for kid in key_ids if kid in self._records and self._records[kid].tenant_id == tenant_id]
            else:
                records = []
                for (o, kt, algo, t), key_ids in self._owner_index.items():
                    if o == owner and kt == key_type.value and t == tenant_id:
                        for kid in key_ids:
                            if kid in self._records and self._records[kid].tenant_id == tenant_id:
                                records.append(self._records[kid])
            records.sort(key=lambda r: r.creation_epoch)
            return records


default_key_lifecycle_manager = KeyLifecycleManager()
