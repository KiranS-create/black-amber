import copy
import base64
import hashlib
from typing import Optional, Dict, Any, Tuple, List

from core.release import ReleaseRecipientPackage
from core.ledger.ledger import EvidenceEvent, TamperEvidentLedger
from core.traceability.provider import TraceabilityMarker
from core.attribution.evidence import (
    EvidenceBundle,
    EvidenceObservation,
    EvidenceFamily,
    TargetBinding,
)

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


# =========================================================================
# Generic Adversarial Fault-Injection Harness
# =========================================================================

def tamper_document(doc_bytes: bytes, mode: str = "append", content: Optional[bytes] = None) -> bytes:
    """Tamper with plaintext or serialized document bytes."""
    if content:
        return doc_bytes + content
    if mode == "append":
        return doc_bytes + b"\n\n% ADVERSARIAL FORGERY INSERTION"
    elif mode == "truncate":
        return doc_bytes[:max(1, len(doc_bytes) // 2)]
    elif mode == "flip":
        if not doc_bytes:
            return b"\xFF"
        return bytes([doc_bytes[0] ^ 0xFF]) + doc_bytes[1:]
    return doc_bytes + b"\x00"


def tamper_release(package: ReleaseRecipientPackage, new_release_id: str = "rel_tampered_999") -> ReleaseRecipientPackage:
    """Tamper with package release identifier."""
    pkg = package.model_copy(deep=True)
    pkg.release_id = new_release_id
    return pkg


def tamper_recipient(target: Any, new_recipient_id: str = "rec_adversary_mallory") -> Any:
    """Tamper with recipient identity on package, event, or observation."""
    t = target.model_copy(deep=True)
    if hasattr(t, "recipient_id"):
        t.recipient_id = new_recipient_id
    if hasattr(t, "primary_candidate"):
        t.primary_candidate = new_recipient_id
    if hasattr(t, "target_binding") and t.target_binding:
        t.target_binding.recipient_id = new_recipient_id
    return t


def tamper_hash(target: Any, new_hash: Optional[str] = None) -> Any:
    """Tamper with artifact or document hash."""
    t = target.model_copy(deep=True)
    bad_hash = new_hash or ("bad0" * 16)
    if hasattr(t, "document_hash"):
        t.document_hash = bad_hash
    if hasattr(t, "artifact_hash"):
        t.artifact_hash = bad_hash
    if hasattr(t, "target_binding") and t.target_binding:
        t.target_binding.artifact_hash = bad_hash
    return t


def tamper_signature(event: EvidenceEvent) -> EvidenceEvent:
    """Corrupt or flip the cryptographic signature on a ledger event."""
    return create_modified_signature_fixture(event)


def replay_event(event: EvidenceEvent, target_ledger: TamperEvidentLedger) -> Tuple[bool, str]:
    """Attempt to replay an existing or stale event into a ledger."""
    try:
        event_hash = target_ledger.append_event(event)
        return (True, event_hash)
    except Exception as ex:
        return (False, str(ex))


def duplicate_event(event: EvidenceEvent) -> EvidenceEvent:
    """Produce an exact clone with the same event_id to trigger anti-replay."""
    return event.model_copy(deep=True)


def swap_evidence(obs_a: EvidenceObservation, obs_b: EvidenceObservation) -> Tuple[EvidenceObservation, EvidenceObservation]:
    """Swap target bindings between two observations."""
    swapped_a = obs_a.model_copy(deep=True)
    swapped_b = obs_b.model_copy(deep=True)
    swapped_a.target_binding = obs_b.target_binding.model_copy(deep=True)
    swapped_b.target_binding = obs_a.target_binding.model_copy(deep=True)
    return (swapped_a, swapped_b)


def remove_evidence(bundle: EvidenceBundle, family: EvidenceFamily) -> EvidenceBundle:
    """Strip all observations of a specific family from an evidence bundle."""
    b = bundle.model_copy(deep=True)
    b.observations = [o for o in b.observations if o.family != family]
    return b


def cross_bind_evidence(obs: EvidenceObservation, target_binding: TargetBinding) -> EvidenceObservation:
    """Bind an observation to a mismatched target binding."""
    c = obs.model_copy(deep=True)
    c.target_binding = target_binding.model_copy(deep=True)
    return c


def corrupt_payload(data: bytes, flip_ratio: float = 0.05) -> bytes:
    """Deterministically corrupt bytes according to flip_ratio."""
    if not data:
        return b"\xFF"
    ba = bytearray(data)
    step = max(1, int(1.0 / max(0.001, flip_ratio)))
    for i in range(0, len(ba), step):
        ba[i] ^= 0xAA
    return bytes(ba)


class AdversarialFaultHarness:
    """
    Unified fault-injection test harness for executing cross-binding,
    tampering, replay, and contradiction attacks against AegisTrace.
    """
    tamper_document = staticmethod(tamper_document)
    tamper_release = staticmethod(tamper_release)
    tamper_recipient = staticmethod(tamper_recipient)
    tamper_hash = staticmethod(tamper_hash)
    tamper_signature = staticmethod(tamper_signature)
    replay_event = staticmethod(replay_event)
    duplicate_event = staticmethod(duplicate_event)
    swap_evidence = staticmethod(swap_evidence)
    remove_evidence = staticmethod(remove_evidence)
    cross_bind_evidence = staticmethod(cross_bind_evidence)
    corrupt_payload = staticmethod(corrupt_payload)

