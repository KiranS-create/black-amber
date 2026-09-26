import copy
import base64
import hashlib
from typing import Optional, Dict, Any, Tuple, List

from core.release import ReleaseRecipientPackage
from core.ledger.ledger import EvidenceEvent, TamperEvidentLedger
from core.traceability.provider import TraceabilityMarker

from attacks.base import (
    BaseAttack,
    AttackFamily,
    ExecutionMode,
    ArtifactType,
    AttackOutput,
    AttackResult,
    DegradationMetrics,
)

# 1. Modified Artifact (Ciphertext Bit-Flip) Fixture
def create_modified_artifact_fixture(package: ReleaseRecipientPackage) -> ReleaseRecipientPackage:
    pkg = package.model_copy(deep=True)
    raw_ct = base64.b64decode(pkg.encrypted_doc_ciphertext_b64)
    # Flip first byte
    flipped = bytes([raw_ct[0] ^ 0xFF]) + raw_ct[1:] if raw_ct else b"\xFF"
    pkg.encrypted_doc_ciphertext_b64 = base64.b64encode(flipped).decode('utf-8')
    return pkg


# 2. Altered Metadata Fixture
def create_altered_metadata_fixture(package: ReleaseRecipientPackage, spoofed_doc_hash: str = "deadbeef" * 8) -> ReleaseRecipientPackage:
    """Tamper with package cryptographic metadata such as document_hash or algorithms."""
    pkg = package.model_copy(deep=True)
    pkg.document_hash = spoofed_doc_hash
    return pkg


# 3. Corrupted Release ID Fixture
def create_corrupted_release_id_fixture(package: ReleaseRecipientPackage) -> ReleaseRecipientPackage:
    pkg = package.model_copy(deep=True)
    pkg.release_id = f"corrupted_{pkg.release_id[:8]}"
    return pkg


# 4. Recipient ID Substitution Fixture (Framing Attack)
def create_recipient_substitution_fixture(package: ReleaseRecipientPackage, target_recipient_id: str = "alice") -> ReleaseRecipientPackage:
    pkg = package.model_copy(deep=True)
    pkg.recipient_id = target_recipient_id
    return pkg


# 5. Wrong Document / Mismatched Release Scope Fixture
def create_wrong_document_fixture(doc_bytes: bytes, marker: TraceabilityMarker) -> Tuple[bytes, TraceabilityMarker]:
    """Pair a valid marker with completely wrong document bytes and mismatched release scope."""
    corrupted_doc = doc_bytes + b"\n\n% UNRELATED ATTACHMENT ADDED BY ATTACKER"
    tampered_marker = marker.model_copy(deep=True)
    tampered_marker.release_id = "rel_mismatched_scope_unauthorized"
    return (corrupted_doc, tampered_marker)


# 6. Stale Artifact Replay Fixture
def create_stale_artifact_fixture(event: EvidenceEvent, new_release_id: str = "rel_future_9999") -> EvidenceEvent:
    stale_event = event.model_copy(deep=True)
    stale_event.release_id = new_release_id
    return stale_event


# 7. Forged Provenance Event Fixture
def create_forged_provenance_event_fixture(
    event_id: str,
    recipient_id: str,
    document_id: str,
    release_id: str,
    prev_event_hash: str
) -> EvidenceEvent:
    """Creates a forged provenance event with counterfeit signature."""
    return EvidenceEvent(
        event_id=event_id,
        event_type="DECRYPTION_EVENT",
        timestamp="2026-09-26T12:00:00Z",
        document_id=document_id,
        release_id=release_id,
        recipient_id=recipient_id,
        algorithm="ML-DSA-65",
        artifact_hash="deadbeef" * 8,
        evidence_hash="cafebabe" * 8,
        previous_event_hash=prev_event_hash,
        signature=base64.b64encode(b"FORGED_COUNTERFEIT_SIGNATURE_BYTES_12345").decode('utf-8'),
        signer_public_key_b64=base64.b64encode(b"FORGED_PUBLIC_KEY_BYTES").decode('utf-8'),
        metadata={"forged": True}
    )


# 8. Modified Signature Fixture
def create_modified_signature_fixture(event: EvidenceEvent) -> EvidenceEvent:
    tampered_event = event.model_copy(deep=True)
    sig_bytes = base64.b64decode(tampered_event.signature)
    corrupted = sig_bytes[:-1] + bytes([sig_bytes[-1] ^ 0x01]) if sig_bytes else b"\x00"
    tampered_event.signature = base64.b64encode(corrupted).decode('utf-8')
    return tampered_event


# 9. Modified Ledger Event Fixture (In-place tampering)
def create_modified_ledger_fixture(ledger: TamperEvidentLedger, event_index: int = 0) -> TamperEvidentLedger:
    tampered_ledger = TamperEvidentLedger()
    tampered_ledger.events = [e.model_copy(deep=True) for e in ledger.events]
    if 0 <= event_index < len(tampered_ledger.events):
        tampered_ledger.events[event_index].artifact_hash = "0000000000000000tamperedhash0000000000000000"
    return tampered_ledger


# 10. Reordered Ledger Entries Fixture
def create_reordered_ledger_fixture(ledger: TamperEvidentLedger) -> TamperEvidentLedger:
    tampered_ledger = TamperEvidentLedger()
    tampered_ledger.events = [e.model_copy(deep=True) for e in ledger.events]
    if len(tampered_ledger.events) >= 2:
        tampered_ledger.events[0], tampered_ledger.events[1] = tampered_ledger.events[1], tampered_ledger.events[0]
    return tampered_ledger


# 11. Deleted Ledger Entry Fixture
def create_deleted_ledger_fixture(ledger: TamperEvidentLedger, delete_index: int = 0) -> TamperEvidentLedger:
    tampered_ledger = TamperEvidentLedger()
    tampered_ledger.events = [e.model_copy(deep=True) for e in ledger.events]
    if 0 <= delete_index < len(tampered_ledger.events):
        del tampered_ledger.events[delete_index]
    return tampered_ledger


# 12. Duplicated Ledger Event Fixture
def create_duplicated_ledger_fixture(ledger: TamperEvidentLedger, dup_index: int = 0) -> TamperEvidentLedger:
    tampered_ledger = TamperEvidentLedger()
    tampered_ledger.events = [e.model_copy(deep=True) for e in ledger.events]
    if 0 <= dup_index < len(tampered_ledger.events):
        tampered_ledger.events.append(tampered_ledger.events[dup_index].model_copy(deep=True))
    return tampered_ledger


# 13. Substituted Artifact Fixture
def create_substituted_artifact_fixture(decoy_bytes: bytes) -> bytes:
    """Return unrelated decoy bytes pretending to be the target decrypted artifact."""
    return decoy_bytes
