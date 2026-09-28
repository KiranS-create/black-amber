import json
import hashlib
import base64
import threading
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any, Tuple, Set
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
        Canonical JSON sorting ensures cross-platform consistency.
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
    Enforces sequential cryptographic linking, event deduplication, and full chain audit.
    """
    GENESIS_HASH = "0" * 64

    def __init__(self, storage_file: Optional[str] = None):
        self._lock = threading.RLock()
        self.storage_file = storage_file
        self.events: List[EvidenceEvent] = []
        self._event_hashes: List[str] = []
        self._seen_event_ids: Set[str] = set()
        self._by_recipient: Dict[str, List[EvidenceEvent]] = {}
        self._by_release: Dict[str, List[EvidenceEvent]] = {}
        self._by_document: Dict[str, List[EvidenceEvent]] = {}

    def clear(self):
        """Reset ledger to zero events and remove any backing persistence file."""
        with self._lock:
            self.events.clear()
            self._event_hashes.clear()
            self._seen_event_ids.clear()
            self._by_recipient.clear()
            self._by_release.clear()
            self._by_document.clear()
            if self.storage_file and os.path.exists(self.storage_file):
                try:
                    os.remove(self.storage_file)
                except Exception:
                    pass

    def get_last_event_hash(self) -> str:
        with self._lock:
            if not self._event_hashes:
                return self.GENESIS_HASH
            return self._event_hashes[-1]

    def append_event(self, event: EvidenceEvent) -> str:
        """
        Append an event to the ledger, verifying that:
        1. event_id is unique (anti-duplicate/anti-replay)
        2. previous_event_hash matches the current tip of the hash chain.
        """
        with self._lock:
            if event.event_id in self._seen_event_ids:
                raise ValueError(f"Replay detected: duplicate event_id '{event.event_id}' rejected")

            expected_prev = self.get_last_event_hash()
            if event.previous_event_hash != expected_prev:
                raise ValueError(
                    f"Invalid previous_event_hash in event {event.event_id}. "
                    f"Expected: {expected_prev}, Got: {event.previous_event_hash}"
                )
            
            event_hash = event.compute_event_hash()
            self.events.append(event)
            self._event_hashes.append(event_hash)
            self._seen_event_ids.add(event.event_id)

            # Update O(1) indexes
            self._by_recipient.setdefault(event.recipient_id, []).append(event)
            self._by_release.setdefault(event.release_id, []).append(event)
            self._by_document.setdefault(event.document_id, []).append(event)

            return event_hash

    def find_decryption_event(
        self,
        recipient_id: str,
        release_id: str,
        document_id: Optional[str] = None
    ) -> Optional[EvidenceEvent]:
        """O(1) indexed lookup for decryption provenance event."""
        candidates = self._by_recipient.get(recipient_id, [])
        for ev in candidates:
            if ev.event_type == "DECRYPTION_EVENT" and ev.release_id == release_id:
                if not document_id or ev.document_id == document_id:
                    return ev
        return None

    def verify_chain(self) -> Tuple[bool, List[str]]:
        """
        Verify the complete integrity of the hash chain:
        - Exact correspondence between event count and hash count
        - Correct chaining of previous_event_hash from GENESIS_HASH
        - Unaltered event hashes
        - Non-duplication of event_ids
        """
        errors = []
        if len(self.events) != len(self._event_hashes):
            errors.append(
                f"Ledger length desynchronization: {len(self.events)} events vs {len(self._event_hashes)} hashes"
            )

        prev_hash = self.GENESIS_HASH
        seen_ids: Set[str] = set()

        for idx, event in enumerate(self.events):
            if event.event_id in seen_ids:
                errors.append(f"Duplicate event_id detected at index {idx}: '{event.event_id}'")
            seen_ids.add(event.event_id)

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

    def verify_chain_and_signatures(
        self,
        recipient_public_keys: Optional[Dict[str, bytes]] = None
    ) -> Tuple[bool, List[str]]:
        """
        Verify both hash-chain integrity and cryptographic authenticity of digital signatures:
        1. Full verify_chain() structural, sequential, and hash validation
        2. ML-DSA-65 post-quantum signature verification across all signed events
        """
        is_chain_valid, errors = self.verify_chain()
        if not is_chain_valid:
            return (False, errors)

        from core.crypto.signatures import MLDSA65

        for idx, event in enumerate(self.events):
            if not event.signature:
                continue

            pub_bytes = None
            if recipient_public_keys and event.recipient_id in recipient_public_keys:
                pub_bytes = recipient_public_keys[event.recipient_id]
            elif event.signer_public_key_b64:
                try:
                    pub_bytes = base64.b64decode(event.signer_public_key_b64)
                except Exception:
                    pub_bytes = None

            if not pub_bytes:
                errors.append(
                    f"Missing public key for signature verification at index {idx} (event {event.event_id}, recipient {event.recipient_id})"
                )
                continue

            try:
                sig_bytes = base64.b64decode(event.signature)
                sign_payload = (
                    f"DECRYPTION_PROVENANCE:{event.event_id}:{event.document_id}:"
                    f"{event.release_id}:{event.recipient_id}:{event.artifact_hash}:"
                    f"{event.previous_event_hash}:{event.timestamp}"
                ).encode('utf-8')

                if not MLDSA65.verify(pub_bytes, sign_payload, sig_bytes):
                    errors.append(
                        f"Cryptographic signature mismatch at index {idx} (event {event.event_id}) for recipient '{event.recipient_id}'"
                    )
            except Exception as ex:
                errors.append(
                    f"Signature verification error at index {idx} (event {event.event_id}): {str(ex)}"
                )

        return (len(errors) == 0, errors)

    def get_events_for_release(self, release_id: str) -> List[EvidenceEvent]:
        return [e for e in self.events if e.release_id == release_id]

    def get_events_for_recipient(self, recipient_id: str) -> List[EvidenceEvent]:
        return [e for e in self.events if e.recipient_id == recipient_id]

    def export_evidence(self) -> List[EvidenceEvent]:
        return list(self.events)

# Global default ledger instance
default_ledger = TamperEvidentLedger()
