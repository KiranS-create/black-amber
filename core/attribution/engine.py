from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

from core.traceability.provider import (
    TraceabilityProvider,
    PrototypeTraceabilityProvider,
    TraceabilityEvidence
)
from core.ledger.ledger import TamperEvidentLedger, default_ledger, EvidenceEvent
from core.recipient import RecipientRegistry, default_registry
from core.crypto.signatures import MLDSA65
import base64

class AttributionState(str, Enum):
    ATTRIBUTED = "ATTRIBUTED"
    CONFLICT = "CONFLICT"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    NO_SIGNAL = "NO_SIGNAL"

class EvidenceSource(str, Enum):
    TRACEABILITY_MARKER = "TRACEABILITY_MARKER"
    AUDIT_LEDGER = "AUDIT_LEDGER"
    DOCUMENT_INTEGRITY = "DOCUMENT_INTEGRITY"
    RECIPIENT_SIGNATURE = "RECIPIENT_SIGNATURE"

class EvidenceItem(BaseModel):
    source: EvidenceSource
    title: str
    is_valid: bool
    confidence: float
    details: Dict[str, Any] = Field(default_factory=dict)

class Candidate(BaseModel):
    recipient_id: str
    name: str
    confidence: float
    verified_events: List[str] = Field(default_factory=list)

class AttributionResult(BaseModel):
    state: AttributionState
    candidate: Optional[Candidate] = None
    confidence: float = 0.0  # 0.0 to 1.0
    confidence_level: str = "NONE"  # "HIGH", "MEDIUM", "LOW", "NONE"
    evidence_items: List[EvidenceItem] = Field(default_factory=list)
    summary: str
    should_abstain: bool = True

class AttributionEngine:
    """
    Fail-Closed Attribution Engine for SIH26237.
    Analyzes leaked document artifacts, extracts cryptographic markers,
    correlates with tamper-evident ledger events, and verifies signatures.
    """
    def __init__(
        self,
        traceability_provider: Optional[TraceabilityProvider] = None,
        ledger: Optional[TamperEvidentLedger] = None,
        registry: Optional[RecipientRegistry] = None
    ):
        self.traceability_provider = traceability_provider or PrototypeTraceabilityProvider()
        self.ledger = ledger or default_ledger
        self.registry = registry or default_registry

    def analyze_leak(
        self,
        leaked_document_bytes: bytes,
        expected_release_id: Optional[str] = None
    ) -> AttributionResult:
        evidence_items: List[EvidenceItem] = []

        # 1. Extract and verify traceability marker
        trace_evidence: TraceabilityEvidence = self.traceability_provider.get_evidence(leaked_document_bytes)
        
        if not trace_evidence.marker_found:
            evidence_items.append(EvidenceItem(
                source=EvidenceSource.TRACEABILITY_MARKER,
                title="Traceability Marker Detection",
                is_valid=False,
                confidence=0.0,
                details={"status": "No marker found in carrier artifact"}
            ))
            return AttributionResult(
                state=AttributionState.NO_SIGNAL,
                candidate=None,
                confidence=0.0,
                confidence_level="NONE",
                evidence_items=evidence_items,
                summary="Abstain: No cryptographic traceability marker detected.",
                should_abstain=True
            )

        if not trace_evidence.is_valid:
            evidence_items.append(EvidenceItem(
                source=EvidenceSource.TRACEABILITY_MARKER,
                title="Traceability Marker Verification",
                is_valid=False,
                confidence=0.0,
                details={
                    "status": "Marker corrupted or forged",
                    "details": trace_evidence.verification_details
                }
            ))
            return AttributionResult(
                state=AttributionState.INSUFFICIENT_EVIDENCE,
                candidate=None,
                confidence=0.0,
                confidence_level="NONE",
                evidence_items=evidence_items,
                summary="Abstain: Marker authentication failed (forged or modified marker).",
                should_abstain=True
            )

        evidence_items.append(EvidenceItem(
            source=EvidenceSource.TRACEABILITY_MARKER,
            title="Traceability Marker Verification",
            is_valid=True,
            confidence=trace_evidence.confidence,
            details={
                "document_id": trace_evidence.document_id,
                "release_id": trace_evidence.release_id,
                "recipient_id": trace_evidence.recipient_id,
                "document_hash": trace_evidence.document_hash
            }
        ))

        # Check expected release if specified
        if expected_release_id and trace_evidence.release_id != expected_release_id:
            evidence_items.append(EvidenceItem(
                source=EvidenceSource.DOCUMENT_INTEGRITY,
                title="Release Scope Verification",
                is_valid=False,
                confidence=0.0,
                details={"expected": expected_release_id, "found": trace_evidence.release_id}
            ))
            return AttributionResult(
                state=AttributionState.CONFLICT,
                candidate=None,
                confidence=0.0,
                confidence_level="NONE",
                evidence_items=evidence_items,
                summary="Abstain: Marker release_id does not match target release.",
                should_abstain=True
            )

        # 2. Check recipient registry
        recipient = self.registry.get(trace_evidence.recipient_id)
        if not recipient:
            evidence_items.append(EvidenceItem(
                source=EvidenceSource.TRACEABILITY_MARKER,
                title="Recipient Identity Lookup",
                is_valid=False,
                confidence=0.0,
                details={"recipient_id": trace_evidence.recipient_id, "status": "Unknown recipient"}
            ))
            return AttributionResult(
                state=AttributionState.INSUFFICIENT_EVIDENCE,
                candidate=None,
                confidence=0.0,
                confidence_level="NONE",
                evidence_items=evidence_items,
                summary="Abstain: Recipient ID referenced by marker is not in registry.",
                should_abstain=True
            )

        # 3. Verify ledger audit chain and signed decryption events
        is_chain_valid, chain_errors = self.ledger.verify_chain()
        if not is_chain_valid:
            evidence_items.append(EvidenceItem(
                source=EvidenceSource.AUDIT_LEDGER,
                title="Tamper-Evident Ledger Integrity",
                is_valid=False,
                confidence=0.0,
                details={"errors": chain_errors}
            ))
            return AttributionResult(
                state=AttributionState.INSUFFICIENT_EVIDENCE,
                candidate=None,
                confidence=0.0,
                confidence_level="NONE",
                evidence_items=evidence_items,
                summary="Abstain: Audit ledger integrity check failed (tampered ledger).",
                should_abstain=True
            )

        evidence_items.append(EvidenceItem(
            source=EvidenceSource.AUDIT_LEDGER,
            title="Tamper-Evident Ledger Integrity",
            is_valid=True,
            confidence=1.0,
            details={"events_count": len(self.ledger.events), "status": "Chain intact"}
        ))

        # 4. Find matching decryption event for this recipient and release
        recipient_events = [
            e for e in self.ledger.events
            if e.recipient_id == recipient.recipient_id
            and e.release_id == trace_evidence.release_id
            and e.event_type == "DECRYPTION_EVENT"
        ]

        if not recipient_events:
            evidence_items.append(EvidenceItem(
                source=EvidenceSource.AUDIT_LEDGER,
                title="Decryption Provenance Event Check",
                is_valid=False,
                confidence=0.0,
                details={"status": "No signed decryption record for recipient in ledger"}
            ))
            return AttributionResult(
                state=AttributionState.INSUFFICIENT_EVIDENCE,
                candidate=None,
                confidence=0.0,
                confidence_level="NONE",
                evidence_items=evidence_items,
                summary="Abstain: No valid decryption provenance event found in audit ledger.",
                should_abstain=True
            )

        # 5. Verify recipient digital signature on the decryption event
        matching_event = recipient_events[-1]
        signature_valid = False
        try:
            sign_payload = (
                f"DECRYPTION_PROVENANCE:{matching_event.event_id}:{matching_event.document_id}:"
                f"{matching_event.release_id}:{matching_event.recipient_id}:{matching_event.artifact_hash}:"
                f"{matching_event.previous_event_hash}:{matching_event.timestamp}"
            ).encode('utf-8')
            
            sig_bytes = base64.b64decode(matching_event.signature)
            pub_bytes = recipient.dsa_keypair.public_key_bytes
            signature_valid = MLDSA65.verify(pub_bytes, sign_payload, sig_bytes)
        except Exception:
            signature_valid = False

        if not signature_valid:
            evidence_items.append(EvidenceItem(
                source=EvidenceSource.RECIPIENT_SIGNATURE,
                title="Recipient Digital Signature Verification",
                is_valid=False,
                confidence=0.0,
                details={"event_id": matching_event.event_id, "status": "Invalid signature"}
            ))
            return AttributionResult(
                state=AttributionState.INSUFFICIENT_EVIDENCE,
                candidate=None,
                confidence=0.0,
                confidence_level="NONE",
                evidence_items=evidence_items,
                summary="Abstain: Recipient signature verification on decryption event failed.",
                should_abstain=True
            )

        evidence_items.append(EvidenceItem(
            source=EvidenceSource.RECIPIENT_SIGNATURE,
            title="Recipient Digital Signature Verification",
            is_valid=True,
            confidence=1.0,
            details={"algorithm": MLDSA65.ALGORITHM_NAME, "event_id": matching_event.event_id}
        ))

        # All checks passed cleanly with high confidence
        candidate = Candidate(
            recipient_id=recipient.recipient_id,
            name=recipient.name,
            confidence=0.99,
            verified_events=[matching_event.event_id]
        )

        return AttributionResult(
            state=AttributionState.ATTRIBUTED,
            candidate=candidate,
            confidence=0.99,
            confidence_level="HIGH",
            evidence_items=evidence_items,
            summary=f"Successfully attributed leak to recipient '{recipient.name}' ({recipient.recipient_id}).",
            should_abstain=False
        )

default_attribution_engine = AttributionEngine()
