import json
import hashlib
import base64
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any, Tuple
from pydantic import BaseModel, Field

class EvidenceEvent(BaseModel):
    event_id: str
    event_type: str  # e.g., "DECRYPTION_EVENT", "RELEASE_EVENT", "ATTRIBUTION_EVENT"
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    document_id: str
    release_id: str
    recipient_id: str
    algorithm: str
    artifact_hash: str
    evidence_hash: str
    previous_event_hash: str
    signature: str  # Base64 encoded recipient or authority digital signature
    signer_public_key_b64: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def compute_event_hash(self) -> str:
        """
        Compute deterministic SHA-256 hash of event content (excluding hash itself).
        """
        data = {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "timestamp": self.timestamp,
            "document_id": self.document_id,
            "release_id": self.release_id,
            "recipient_id": self.recipient_id,
            "algorithm": self.algorithm,
            "artifact_hash": self.artifact_hash,
            "evidence_hash": self.evidence_hash,
            "previous_event_hash": self.previous_event_hash,
            "signature": self.signature,
            "signer_public_key_b64": self.signer_public_key_b64,
            "metadata": self.metadata,
        }
        serialized = json.dumps(data, sort_keys=True)
        return hashlib.sha256(serialized.encode('utf-8')).hexdigest()

class TamperEvidentLedger:
    """
    Hash-chained tamper-evident audit ledger for cryptographic decryption provenance.
    """
    GENESIS_HASH = "0" * 64

    def __init__(self, storage_file: Optional[str] = None):
        self.storage_file = storage_file
        self.events: List[EvidenceEvent] = []
        self._event_hashes: List[str] = []

    def get_last_event_hash(self) -> str:
        if not self._event_hashes:
            return self.GENESIS_HASH
        return self._event_hashes[-1]

    def append_event(self, event: EvidenceEvent) -> str:
        """
        Append an event to the ledger, verifying that its previous_event_hash
        matches the current tip of the hash chain.
        """
        expected_prev = self.get_last_event_hash()
        if event.previous_event_hash != expected_prev:
            raise ValueError(
                f"Invalid previous_event_hash in event {event.event_id}. "
                f"Expected: {expected_prev}, Got: {event.previous_event_hash}"
            )
        
        event_hash = event.compute_event_hash()
        self.events.append(event)
        self._event_hashes.append(event_hash)
        return event_hash

    def verify_chain(self) -> Tuple[bool, List[str]]:
        """
        Verify the complete integrity of the hash chain.
        Returns (is_valid, list_of_errors).
        """
        errors = []
        prev_hash = self.GENESIS_HASH

        for idx, event in enumerate(self.events):
            if event.previous_event_hash != prev_hash:
                errors.append(
                    f"Chain broken at index {idx} (event {event.event_id}): "
                    f"previous_event_hash '{event.previous_event_hash}' != expected '{prev_hash}'"
                )
            
            computed_hash = event.compute_event_hash()
            if idx < len(self._event_hashes) and self._event_hashes[idx] != computed_hash:
                errors.append(
                    f"Hash mismatch at index {idx} (event {event.event_id}): "
                    f"stored '{self._event_hashes[idx]}' != computed '{computed_hash}'"
                )
            
            prev_hash = computed_hash

        return (len(errors) == 0, errors)

    def get_events_for_release(self, release_id: str) -> List[EvidenceEvent]:
        return [e for e in self.events if e.release_id == release_id]

    def get_events_for_recipient(self, recipient_id: str) -> List[EvidenceEvent]:
        return [e for e in self.events if e.recipient_id == recipient_id]

    def export_evidence(self) -> List[EvidenceEvent]:
        return list(self.events)

# Global default ledger instance
default_ledger = TamperEvidentLedger()
