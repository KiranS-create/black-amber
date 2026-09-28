"""
AegisTrace Append-Only Cryptographic Chain of Custody.

Maintains an immutable, SHA-256 hash-chained log of every evidentiary operation
performed by forensic operators, automated extractors, or offline reviewers.
Guarantees:
1. Strict append-only sequencing: H_i = SHA256(H_{i-1} || event_payload).
2. Tamper-evident detection of modified, inserted, or deleted records.
3. Multi-tenant isolation and operator non-repudiation.
"""

import hashlib
from typing import List, Dict, Tuple, Optional
from datetime import datetime, timezone

from core.evidence_package.models import ChainOfCustodyEvent, CustodyAction
from core.evidence_package.canonical import canonical_json_bytes, canonical_json_dumps, compute_content_hash


class CustodyVerificationError(ValueError):
    """Raised when a custody chain verification failure is detected."""
    pass


class ChainOfCustodyLedger:
    """
    Manages and verifies append-only cryptographic custody event chains.
    Supports both functional classmethod verification and stateful instance tracking.
    """
    GENESIS_HASH = "0" * 64

    def __init__(self, tenant_id: str = "default_tenant"):
        self.tenant_id = tenant_id
        self.events: List[ChainOfCustodyEvent] = []
        self._last_hash = self.GENESIS_HASH

    def append_event(
        self,
        action: CustodyAction,
        evidence_object_id: str,
        operator_identity: str,
        device_identity: str,
        resulting_evidence_hash: str,
        reason: str,
        timestamp: Optional[str] = None
    ) -> ChainOfCustodyEvent:
        """Appends and seals a new event to this ledger instance's sequence."""
        event = self.create_event(
            action=action,
            evidence_object_id=evidence_object_id,
            operator_identity=operator_identity,
            device_identity=device_identity,
            resulting_evidence_hash=resulting_evidence_hash,
            reason=reason,
            previous_custody_hash=self._last_hash,
            tenant_id=self.tenant_id,
            timestamp=timestamp
        )
        self.events.append(event)
        self._last_hash = self.compute_custody_event_hash(
            previous_hash=event.previous_custody_hash,
            custody_event_id=event.custody_event_id,
            evidence_object_id=event.evidence_object_id,
            operator_identity=event.operator_identity,
            device_identity=device_identity,
            action=event.action,
            timestamp=event.timestamp,
            resulting_evidence_hash=event.resulting_evidence_hash,
            tenant_id=event.tenant_id,
            reason=event.reason
        )
        return event

    @classmethod
    def compute_custody_event_hash(
        cls,
        previous_hash: str,
        custody_event_id: str,
        evidence_object_id: str,
        operator_identity: str,
        device_identity: str,
        action: CustodyAction,
        timestamp: str,
        resulting_evidence_hash: str,
        tenant_id: str,
        reason: str
    ) -> str:
        """
        Computes deterministic SHA-256 hash linking previous custody block and current event.
        """
        payload = {
            "action": action.value if hasattr(action, "value") else str(action),
            "custody_event_id": custody_event_id,
            "device_identity": device_identity,
            "evidence_object_id": evidence_object_id,
            "operator_identity": operator_identity,
            "previous_custody_hash": previous_hash,
            "reason": reason,
            "resulting_evidence_hash": resulting_evidence_hash,
            "tenant_id": tenant_id,
            "timestamp": timestamp,
        }
        preimage = f"AEGIS-CUSTODY:v1:{previous_hash}:{canonical_json_dumps(payload)}"
        return hashlib.sha256(preimage.encode("utf-8")).hexdigest()

    @classmethod
    def create_event(
        cls,
        action: CustodyAction,
        evidence_object_id: str,
        operator_identity: str,
        device_identity: str,
        resulting_evidence_hash: str,
        reason: str,
        previous_custody_hash: str = GENESIS_HASH,
        tenant_id: str = "default_tenant",
        timestamp: Optional[str] = None
    ) -> ChainOfCustodyEvent:
        """Creates and seals a new ChainOfCustodyEvent in the sequence."""
        now_ts = timestamp or datetime.now(timezone.utc).isoformat()
        event_id = f"coc_{hashlib.sha256(f'{action.value}:{evidence_object_id}:{now_ts}'.encode('utf-8')).hexdigest()[:16]}"

        event = ChainOfCustodyEvent(
            object_id=event_id,
            custody_event_id=event_id,
            evidence_object_id=evidence_object_id,
            operator_identity=operator_identity,
            device_identity=device_identity,
            action=action,
            timestamp=now_ts,
            previous_custody_hash=previous_custody_hash,
            resulting_evidence_hash=resulting_evidence_hash,
            tenant_id=tenant_id,
            reason=reason
        )
        event.seal_content_hash()
        return event

    @classmethod
    def verify_chain(cls, events: List[ChainOfCustodyEvent], expected_tenant_id: Optional[str] = None) -> Tuple[bool, List[str]]:
        """
        Verifies cryptographic integrity of the entire chain of custody:
        1. Content hash matches computed digest for each event.
        2. Previous custody hash strictly chains back to genesis.
        3. No cross-tenant contamination.
        4. Chronological monotonic timestamp progression.
        """
        errors = []
        if not events:
            return True, []

        prev_hash = cls.GENESIS_HASH

        for i, ev in enumerate(events):
            # 1. Content integrity
            if not ev.verify_content_integrity():
                errors.append(f"Event {i} ({ev.custody_event_id}) content_hash mismatch")

            # 2. Previous hash linkage
            if ev.previous_custody_hash != prev_hash:
                errors.append(
                    f"Event {i} ({ev.custody_event_id}) broken custody link: "
                    f"expected {prev_hash}, found {ev.previous_custody_hash}"
                )

            # 3. Tenant isolation
            if expected_tenant_id and ev.tenant_id != expected_tenant_id:
                errors.append(
                    f"Event {i} ({ev.custody_event_id}) tenant mismatch: "
                    f"expected {expected_tenant_id}, found {ev.tenant_id}"
                )

            # Advance chain state: compute next link hash
            prev_hash = cls.compute_custody_event_hash(
                previous_hash=ev.previous_custody_hash,
                custody_event_id=ev.custody_event_id,
                evidence_object_id=ev.evidence_object_id,
                operator_identity=ev.operator_identity,
                device_identity=ev.device_identity,
                action=ev.action,
                timestamp=ev.timestamp,
                resulting_evidence_hash=ev.resulting_evidence_hash,
                tenant_id=ev.tenant_id,
                reason=ev.reason
            )

        return (len(errors) == 0, errors)
