"""
AegisTrace - Physical Chain of Custody & Evidence Tracking
==========================================================
Cryptographically tracks the physical evidence lifecycle across hardware:
PRINTED -> CAPTURED -> IMPORTED -> HASHED -> ANALYZED -> SEALED

Every custody event binds operator, timestamp, hardware device ID, artifact
SHA-256 digest, and the previous custody event hash in a tamper-evident chain.
"""

from enum import Enum
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime, timezone
import hashlib
import json
from pydantic import BaseModel, Field


class PhysicalCustodyAction(str, Enum):
    PRINTED = "PRINTED"
    CAPTURED = "CAPTURED"
    IMPORTED = "IMPORTED"
    HASHED = "HASHED"
    ANALYZED = "ANALYZED"
    SEALED = "SEALED"


class PhysicalCustodyEvent(BaseModel):
    """Immutable single record in the physical chain of custody."""
    event_id: str = Field(..., description="Unique custody event ID")
    action: PhysicalCustodyAction = Field(..., description="Custody action performed")
    operator: str = Field("operator_secops", description="Operator identity or system role")
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    device_id: str = Field("UNKNOWN", description="Physical hardware identifier or UNKNOWN")
    artifact_hash: str = Field(..., description="SHA-256 hash of artifact being handled")
    previous_custody_hash: str = Field(..., description="SHA-256 hash of prior custody event or 'GENESIS'")
    custody_hash: str = Field(..., description="Tamper-evident hash of this entire custody record")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Operational parameters")

    @classmethod
    def create(
        cls,
        action: PhysicalCustodyAction,
        artifact_hash: str,
        previous_custody_hash: str = "GENESIS",
        operator: str = "operator_secops",
        device_id: str = "UNKNOWN",
        metadata: Optional[Dict[str, Any]] = None
    ) -> "PhysicalCustodyEvent":
        ts = datetime.now(timezone.utc).isoformat()
        entropy = hashlib.sha256(f"{action}:{artifact_hash}:{ts}:{previous_custody_hash}".encode()).hexdigest()[:10]
        event_id = f"PCEVT-{entropy}"
        
        meta = metadata or {}
        # Compute canonical custody hash
        canonical_str = f"{event_id}|{action.value}|{operator}|{ts}|{device_id}|{artifact_hash}|{previous_custody_hash}|{json.dumps(meta, sort_keys=True)}"
        c_hash = hashlib.sha256(canonical_str.encode('utf-8')).hexdigest()
        
        return cls(
            event_id=event_id,
            action=action,
            operator=operator,
            timestamp=ts,
            device_id=device_id,
            artifact_hash=artifact_hash,
            previous_custody_hash=previous_custody_hash,
            custody_hash=c_hash,
            metadata=meta
        )


class PhysicalCustodyChain(BaseModel):
    """Complete chain of custody for a physical evidence artifact."""
    chain_id: str = Field(..., description="Unique custody chain ID")
    run_id: str = Field(..., description="Physical lab run ID reference")
    initial_artifact_hash: str = Field(..., description="Original digital render hash")
    events: List[PhysicalCustodyEvent] = Field(default_factory=list)
    is_sealed: bool = Field(False, description="True if chain has a valid terminal SEALED event")
    final_seal_hash: Optional[str] = Field(None, description="Hash of the terminal SEALED event")

    def append_event(
        self,
        action: PhysicalCustodyAction,
        artifact_hash: str,
        operator: str = "operator_secops",
        device_id: str = "UNKNOWN",
        metadata: Optional[Dict[str, Any]] = None
    ) -> PhysicalCustodyEvent:
        if self.is_sealed:
            raise ValueError(f"Cannot append event to sealed custody chain {self.chain_id}")
            
        prev_hash = self.events[-1].custody_hash if self.events else "GENESIS"
        event = PhysicalCustodyEvent.create(
            action=action,
            artifact_hash=artifact_hash,
            previous_custody_hash=prev_hash,
            operator=operator,
            device_id=device_id,
            metadata=metadata
        )
        self.events.append(event)
        
        if action == PhysicalCustodyAction.SEALED:
            self.is_sealed = True
            self.final_seal_hash = event.custody_hash
            
        return event


    def verify_integrity(self) -> Tuple[bool, List[str]]:
        """
        Validates hash linkage and integrity across all events in the chain.
        Returns: (is_valid, list_of_errors)
        """
        errors = []
        if not self.events:
            return False, ["Custody chain contains zero events."]

        prev_hash = "GENESIS"
        for i, ev in enumerate(self.events):
            if ev.previous_custody_hash != prev_hash:
                errors.append(f"Event {i} ({ev.event_id}) prev_hash mismatch: expected {prev_hash}, got {ev.previous_custody_hash}")
                
            canonical_str = f"{ev.event_id}|{ev.action.value}|{ev.operator}|{ev.timestamp}|{ev.device_id}|{ev.artifact_hash}|{ev.previous_custody_hash}|{json.dumps(ev.metadata, sort_keys=True)}"
            expected_hash = hashlib.sha256(canonical_str.encode('utf-8')).hexdigest()
            if ev.custody_hash != expected_hash:
                errors.append(f"Event {i} ({ev.event_id}) hash invalid: expected {expected_hash}, got {ev.custody_hash}")
                
            prev_hash = ev.custody_hash

        if self.is_sealed and (not self.final_seal_hash or self.final_seal_hash != self.events[-1].custody_hash):
            errors.append("Final seal hash does not match terminal event hash.")

        return len(errors) == 0, errors
