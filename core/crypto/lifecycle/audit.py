"""
AegisTrace Key Lifecycle Audit Logger.

Emits structured, sanitized cryptographic audit records for every key lifecycle transition.
Guarantees zero leakage of private keys or master secrets.
"""

from datetime import datetime, timezone
import hashlib
import json
import threading
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from core.crypto.lifecycle.models import KeyRecord, KeyState, KeyType


class KeyAuditEvent(BaseModel):
    """Sanitized key lifecycle audit event."""
    event_id: str
    key_id: str
    key_type: str
    owner: str
    tenant_id: str
    previous_state: str
    new_state: str
    epoch: int
    timestamp: str
    reason: str
    authorized_actor: str
    predecessor_key_id: Optional[str] = None
    successor_key_id: Optional[str] = None
    integrity_reference: str

    def compute_integrity_reference(self) -> str:
        payload = f"{self.event_id}:{self.key_id}:{self.tenant_id}:{self.previous_state}:{self.new_state}:{self.epoch}:{self.timestamp}:{self.authorized_actor}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class KeyLifecycleAuditLogger:
    """
    Thread-safe audit logger for key lifecycle events.
    Maintains chronological integrity chains and integrates with the audit ledger.
    """
    def __init__(self):
        self._events: List[KeyAuditEvent] = []
        self._lock = threading.Lock()
        self._latest_hash = "0" * 64

    def log_transition(
        self,
        record: KeyRecord,
        previous_state: KeyState,
        new_state: KeyState,
        reason: str,
        authorized_actor: str = "SYSTEM_ADMIN",
        timestamp: Optional[str] = None
    ) -> KeyAuditEvent:
        with self._lock:
            now_iso = timestamp or datetime.now(timezone.utc).isoformat()
            event_id = f"aud_key_{hashlib.sha256(f'{record.key_id}:{len(self._events)}:{now_iso}'.encode('utf-8')).hexdigest()[:16]}"
            
            # Compute chaining integrity reference
            preimage = f"{event_id}:{record.key_id}:{record.tenant_id}:{previous_state.value}:{new_state.value}:{record.creation_epoch}:{now_iso}:{self._latest_hash}"
            integrity_ref = hashlib.sha256(preimage.encode("utf-8")).hexdigest()
            self._latest_hash = integrity_ref

            event = KeyAuditEvent(
                event_id=event_id,
                key_id=record.key_id,
                key_type=record.key_type.value,
                owner=record.owner,
                tenant_id=record.tenant_id,
                previous_state=previous_state.value,
                new_state=new_state.value,
                epoch=record.creation_epoch,
                timestamp=now_iso,
                reason=reason,
                authorized_actor=authorized_actor,
                predecessor_key_id=record.predecessor_key_id,
                successor_key_id=record.successor_key_id,
                integrity_reference=integrity_ref
            )
            self._events.append(event)
            return event

    def get_events_for_key(self, key_id: str, tenant_id: str = "default_tenant") -> List[KeyAuditEvent]:
        with self._lock:
            return [e for e in self._events if e.key_id == key_id and e.tenant_id == tenant_id]

    def get_all_events(self, tenant_id: Optional[str] = None) -> List[KeyAuditEvent]:
        with self._lock:
            if tenant_id:
                return [e for e in self._events if e.tenant_id == tenant_id]
            return list(self._events)


default_key_audit_logger = KeyLifecycleAuditLogger()
