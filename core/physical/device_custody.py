"""
SIH26237 - Device Custody Chain & Evidence Transition Ledger
============================================================
Tracks physical and device evidence states across the forensic lifecycle:
CONNECTED -> OBSERVED -> TRANSFERRED -> IMPORTED -> HASHED -> ANALYZED -> SEALED

STRICT INVARIANT:
- 'CAPTURED' is reserved exclusively for genuine optical/camera captures.
- Digital transfers between phones, laptop, and local server must use 'TRANSFERRED'.
- Any attempt to label a digital transfer as 'CAPTURED' fails closed via AntiFabricationGuard.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from enum import Enum
import hashlib
import json
from pydantic import BaseModel, Field

from core.physical.epistemic import EpistemicStatus, AntiFabricationGuard, AntiFabricationViolation


class DeviceCustodyAction(str, Enum):
    CONNECTED = "CONNECTED"
    OBSERVED = "OBSERVED"
    CAPTURED = "CAPTURED"          # RESERVED FOR PHYSICAL OPTICAL SENSOR CAPTURE ONLY
    TRANSFERRED = "TRANSFERRED"    # DIGITAL FILE / NETWORK / USB TRANSFER
    IMPORTED = "IMPORTED"
    HASHED = "HASHED"
    ANALYZED = "ANALYZED"
    SEALED = "SEALED"


class DeviceCustodyEvent(BaseModel):
    """Immutable single step in the device chain of custody."""
    event_id: str
    action: DeviceCustodyAction
    device_id: str
    artifact_hash: str
    operator: str = "operator_secops"
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    previous_event_hash: str = "GENESIS"
    event_hash: str = ""
    epistemic_status: EpistemicStatus = EpistemicStatus.DEVICE_IN_LOOP
    is_optical_capture: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DeviceCustodyLedger(BaseModel):
    """Append-only cryptographic ledger tracking custody for a device validation session."""
    ledger_id: str
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    sealed_at: Optional[str] = None
    is_sealed: bool = False
    events: List[DeviceCustodyEvent] = Field(default_factory=list)
    root_custody_hash: Optional[str] = None

    def record_transition(
        self,
        action: DeviceCustodyAction,
        device_id: str,
        artifact_hash: str,
        operator: str = "operator_secops",
        is_optical_capture: bool = False,
        epistemic_status: EpistemicStatus = EpistemicStatus.DEVICE_IN_LOOP,
        metadata: Optional[Dict[str, Any]] = None
    ) -> DeviceCustodyEvent:
        """
        Records a validated custody transition with anti-fabrication enforcement.
        """
        if self.is_sealed:
            raise ValueError("Cannot append event to a sealed DeviceCustodyLedger.")

        # Anti-fabrication check: cannot declare CAPTURED without genuine optical capture!
        AntiFabricationGuard.validate_transfer_vs_capture(action.value, is_optical_capture)

        prev_hash = self.events[-1].event_hash if self.events else "GENESIS"
        ts = datetime.now(timezone.utc).isoformat()
        entropy = hashlib.sha256(f"{action.value}:{device_id}:{artifact_hash}:{ts}".encode()).hexdigest()[:10]
        event_id = f"DCUST-{entropy}"

        meta = metadata or {}
        raw_canonical = f"{event_id}|{action.value}|{device_id}|{artifact_hash}|{operator}|{ts}|{prev_hash}|{json.dumps(meta, sort_keys=True)}"
        ev_hash = hashlib.sha256(raw_canonical.encode("utf-8")).hexdigest()

        event = DeviceCustodyEvent(
            event_id=event_id,
            action=action,
            device_id=device_id,
            artifact_hash=artifact_hash,
            operator=operator,
            timestamp=ts,
            previous_event_hash=prev_hash,
            event_hash=ev_hash,
            epistemic_status=epistemic_status,
            is_optical_capture=is_optical_capture,
            metadata=meta
        )

        self.events.append(event)
        return event

    def seal_ledger(self) -> str:
        """Computes incremental root custody hash and seals ledger."""
        self.is_sealed = True
        self.sealed_at = datetime.now(timezone.utc).isoformat()

        hasher = hashlib.sha256(self.ledger_id.encode())
        for ev in self.events:
            hasher.update(f"{ev.event_id}:{ev.action.value}:{ev.event_hash}".encode())
        self.root_custody_hash = hasher.hexdigest()
        return self.root_custody_hash
