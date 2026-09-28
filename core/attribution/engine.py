from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import base64

from core.attribution.evidence import (
    AttributionState,
    EvidenceFamily,
    EvidenceConfidenceLevel,
    EvidenceSource,
    TargetBinding,
    EvidenceObservation,
    WatermarkObservation,
    TraceabilityObservation,
    ProvenanceObservation,
    LedgerObservation,
    IntegrityObservation,
    AttackContextObservation,
    EvidenceBundle,
)
from core.attribution.dependency import EvidenceDependencyGraph
from core.attribution.reliability import AttackAwareReliabilityCalibrator
from core.attribution.policy import DecisionPolicy
from core.attribution.fusion import (
    EvidenceFusionEngine,
    FusedAttributionResult,
    CandidateEvaluation,
)

from core.traceability.provider import (
    TraceabilityProvider,
    PrototypeTraceabilityProvider,
    TraceabilityEvidence
)
from core.ledger.ledger import TamperEvidentLedger, default_ledger, EvidenceEvent
from core.recipient import RecipientRegistry, default_registry
from core.crypto.signatures import MLDSA65
from core.identity.models import ResolvedIdentitySummary
from core.identity.resolver import IdentityResolver, default_identity_resolver
from core.lineage.models import ForensicAttributionLevel, ForensicBoundaryState

class EvidenceItem(BaseModel):
    source: EvidenceSource
    title: str
    is_valid: bool
    confidence: float
    details: Dict[str, Any] = Field(default_factory=dict)

class Candidate(BaseModel):
    recipient_id: str
    name: str = "Unknown (Resolution Pending)"
    confidence: float
    verified_events: List[str] = Field(default_factory=list)
    identity_id: Optional[str] = None
    identity_summary: Optional[ResolvedIdentitySummary] = None
    resolution_status: str = "RESOLVED"  # RESOLVED, CACHED, PENDING, NOT_FOUND
    identity_status: Optional[str] = "ACTIVE"

class AttributionResult(BaseModel):
    state: AttributionState
    candidate: Optional[Candidate] = None
    confidence: float = 0.0  # 0.0 to 1.0
    confidence_level: str = "NONE"  # "HIGH", "MEDIUM", "LOW", "NONE"
    evidence_items: List[EvidenceItem] = Field(default_factory=list)
    summary: str
    should_abstain: bool = True
    fused_details: Optional[Dict[str, Any]] = None

    # Lineage forensic fields
    forensic_attribution_level: Optional[ForensicAttributionLevel] = None
    forensic_boundary_state: Optional[ForensicBoundaryState] = None
    last_known_holder: Optional[str] = None
    lineage_proof: Optional[Dict[str, Any]] = None

class AttributionEngine:
    """
    Fail-Closed Attribution & Multi-Channel Evidence Fusion Engine for AegisTrace.
    
    Provides:
    1. Direct artifact analysis via `analyze_leak(leaked_document_bytes, ...)`
    2. Multi-channel evidence bundle fusion via `analyze_evidence_bundle(bundle, ...)`
    
    Guarantees:
    - Candidate recipient_id is derived autonomously from cryptographic evidence.
    - Operator cannot influence attribution by specifying a recipient name.
    - Human identity is an output of directory resolution, not an input to attribution.
    - Directory lookup outage produces resolution_status="PENDING" without losing cryptographic attribution.
    - Deprovisioned/revoked identities retain historical forensic auditability.
    """
    def __init__(
        self,
        traceability_provider: Optional[TraceabilityProvider] = None,
        ledger: Optional[TamperEvidentLedger] = None,
        registry: Optional[RecipientRegistry] = None,
        fusion_engine: Optional[EvidenceFusionEngine] = None,
        identity_resolver: Optional[IdentityResolver] = None
    ):
        self.traceability_provider = traceability_provider or PrototypeTraceabilityProvider()
        self.ledger = ledger or default_ledger
        self.registry = registry or default_registry
        self.fusion_engine = fusion_engine or EvidenceFusionEngine()
        self.identity_resolver = identity_resolver or default_identity_resolver

    def analyze_evidence_bundle(
        self,
        bundle: EvidenceBundle,
        policy: Optional[DecisionPolicy] = None
    ) -> FusedAttributionResult:
        """
        Execute multi-channel evidence fusion across heterogeneous observations.
        """
        engine = self.fusion_engine
        if policy:
            engine = EvidenceFusionEngine(
                dependency_graph=self.fusion_engine.dependency_graph,
                calibrator=self.fusion_engine.calibrator,
                policy=policy
            )
        fused = engine.fuse(bundle)
        if fused.top_candidate_id:
            cand = Candidate(
                recipient_id=fused.top_candidate_id,
                name=fused.top_candidate_id,
                confidence=fused.confidence,
            )
            if hasattr(self, "identity_resolver") and self.identity_resolver:
                try:
                    if hasattr(self.identity_resolver, "resolve_recipient_id"):
                        res = self.identity_resolver.resolve_recipient_id(fused.top_candidate_id)
                        cand.resolution_status = res.status
                        cand.identity_status = getattr(res, "account_status", "ACTIVE")
                        if res.display_name:
                            cand.name = res.display_name
                    elif hasattr(self.identity_resolver, "resolve_recipient"):
                        summary, status_code = self.identity_resolver.resolve_recipient(fused.top_candidate_id)
                        cand.resolution_status = status_code
                        if summary:
                            cand.identity_summary = summary
                            cand.identity_id = summary.identity_id
                            cand.name = summary.display_name
                            cand.identity_status = summary.status
                except Exception:
                    cand.resolution_status = "PENDING"
            fused.candidate = cand
        return fused

    def analyze_leak(
        self,
        leaked_document_bytes: bytes,
        expected_release_id: Optional[str] = None
    ) -> AttributionResult:
        """
        Analyze leaked document bytes, extract cryptographic markers,
        correlate with tamper-evident ledger events, verify signatures,
        and produce a fail-closed attribution result with post-attribution identity resolution.
        """
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

        # 4. Find matching decryption event for this recipient, release, and document
        if hasattr(self.ledger, "find_decryption_event"):
            matching_event = self.ledger.find_decryption_event(
                recipient_id=recipient.recipient_id,
                release_id=trace_evidence.release_id,
                document_id=trace_evidence.document_id
            )
            recipient_events = [matching_event] if matching_event else []
        else:
            recipient_events = [
                e for e in self.ledger.events
                if e.recipient_id == recipient.recipient_id
                and e.release_id == trace_evidence.release_id
                and (not trace_evidence.document_id or e.document_id == trace_evidence.document_id)
                and e.event_type == "DECRYPTION_EVENT"
            ]

        if not recipient_events:
            evidence_items.append(EvidenceItem(
                source=EvidenceSource.AUDIT_LEDGER,
                title="Decryption Provenance Event Check",
                is_valid=False,
                confidence=0.0,
                details={"status": "No signed decryption record for recipient in ledger matching release and document"}
            ))
            return AttributionResult(
                state=AttributionState.INSUFFICIENT_EVIDENCE,
                candidate=None,
                confidence=0.0,
                confidence_level="NONE",
                evidence_items=evidence_items,
                summary=f"Abstain: No signed decryption provenance event found in ledger for recipient '{recipient.recipient_id}'.",
                should_abstain=True
            )

        matching_event = recipient_events[0]
        evidence_items.append(EvidenceItem(
            source=EvidenceSource.AUDIT_LEDGER,
            title="Decryption Provenance Event Check",
            is_valid=True,
            confidence=1.0,
            details={
                "event_id": matching_event.event_id,
                "timestamp": matching_event.timestamp,
                "algorithm": matching_event.algorithm
            }
        ))

        # 5. Verify recipient digital signature on provenance event using ML-DSA-65
        signature_valid = False
        try:
            sig_bytes = base64.b64decode(matching_event.signature)
            canonical_payload = (
                f"DECRYPTION_PROVENANCE:{matching_event.event_id}:{matching_event.document_id}:"
                f"{matching_event.release_id}:{matching_event.recipient_id}:{matching_event.artifact_hash}:"
                f"{matching_event.previous_event_hash}:{matching_event.timestamp}"
            ).encode('utf-8')
            signature_valid = MLDSA65.verify(recipient.dsa_keypair.public_key_bytes, canonical_payload, sig_bytes)
            if not signature_valid:
                # Fallback to legacy evidence_hash signature
                msg_bytes = matching_event.evidence_hash.encode('utf-8')
                signature_valid = MLDSA65.verify(recipient.dsa_keypair.public_key_bytes, msg_bytes, sig_bytes)
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

        # 6. Verify original document hash binding between marker and ledger record
        expected_orig_hash = matching_event.metadata.get("original_document_hash")
        if expected_orig_hash and trace_evidence.document_hash and expected_orig_hash != trace_evidence.document_hash:
            evidence_items.append(EvidenceItem(
                source=EvidenceSource.DOCUMENT_INTEGRITY,
                title="Original Document Hash Verification",
                is_valid=False,
                confidence=0.0,
                details={
                    "event_original_hash": expected_orig_hash,
                    "marker_original_hash": trace_evidence.document_hash,
                    "status": "Document hash mismatch between marker and ledger record"
                }
            ))
            return AttributionResult(
                state=AttributionState.CONFLICT,
                candidate=None,
                confidence=0.0,
                confidence_level="NONE",
                evidence_items=evidence_items,
                summary="Abstain: Document hash in marker does not match ledger provenance record.",
                should_abstain=True
            )

        # 7. Post-Attribution Identity Resolution
        # Cryptographic candidate is already derived from evidence.
        # Now resolve human enterprise identity via IdentityResolver.
        identity_summary, resolution_status = self.identity_resolver.resolve_recipient(recipient.recipient_id)
        
        display_name = recipient.name
        identity_id = recipient.identity_id or None
        identity_status = recipient.status
        
        if identity_summary:
            if identity_summary.display_name and not identity_summary.display_name.startswith("Recipient ["):
                display_name = identity_summary.display_name
            elif not display_name:
                display_name = identity_summary.display_name
            identity_id = identity_summary.identity_id
            if recipient.status in ["REVOKED", "DEPROVISIONED"]:
                identity_status = recipient.status
            else:
                identity_status = identity_summary.status
        elif resolution_status == "PENDING":
            if not display_name:
                display_name = f"Recipient [{recipient.recipient_id}]"

        candidate = Candidate(
            recipient_id=recipient.recipient_id,
            name=display_name,
            confidence=0.99,
            verified_events=[matching_event.event_id],
            identity_id=identity_id,
            identity_summary=identity_summary,
            resolution_status=resolution_status,
            identity_status=identity_status
        )

        status_flags = []
        if identity_status and identity_status != "ACTIVE":
            status_flags.append(f"Historical Status: {identity_status}")
        if resolution_status == "PENDING":
            status_flags.append("Identity Resolution Pending Directory Availability")
        elif resolution_status == "CACHED":
            status_flags.append("Identity Resolved from Local Release Cache")

        flag_str = f" ({'; '.join(status_flags)})" if status_flags else ""

        return AttributionResult(
            state=AttributionState.ATTRIBUTED,
            candidate=candidate,
            confidence=0.99,
            confidence_level="HIGH",
            evidence_items=evidence_items,
            summary=f"Successfully attributed leak to recipient '{recipient.recipient_id}' -> Identity '{display_name}'{flag_str}.",
            should_abstain=False,
            forensic_attribution_level=ForensicAttributionLevel.LEVEL_2_ORIGINAL_RECIPIENT_IDENTIFIED,
            forensic_boundary_state=ForensicBoundaryState.ATTRIBUTED_TO_CONTROLLED_ACTOR,
            last_known_holder=recipient.recipient_id,
        )

    def analyze_dynamic_leak(
        self,
        leak_artifact: Any,
        expected_document_id: Optional[str] = None,
        expected_release_id: Optional[str] = None,
        reference_clean_image: Optional[Any] = None,
        dlt_ledger: Optional[Any] = None,
        lineage_storage: Optional[Any] = None,
        dynamic_wm_engine: Optional[Any] = None,
    ) -> AttributionResult:
        """
        Analyzes a dynamic decryption leak artifact using DynamicForensicExtractor,
        verifying the offline permissioned DLT commitment, recipient ML-DSA-65 signature,
        BFT quorum consensus, and resolves the recipient's enterprise identity.
        """
        from core.lineage.forensics import DynamicForensicExtractor, ForensicVerificationStatus

        extractor = DynamicForensicExtractor(
            dlt_ledger=dlt_ledger,
            lineage_storage=lineage_storage,
            wm_engine=dynamic_wm_engine,
        )

        res = extractor.analyze_leak(
            leak_artifact=leak_artifact,
            expected_doc_id=expected_document_id,
            expected_release_id=expected_release_id,
            reference_clean_image=reference_clean_image,
        )

        evidence_items: List[EvidenceItem] = []

        if res.status == ForensicVerificationStatus.ABSENT_OR_DESTROYED:
            evidence_items.append(EvidenceItem(
                source=EvidenceSource.TRACEABILITY_MARKER,
                title="Dynamic Watermark Recovery",
                is_valid=False,
                confidence=0.0,
                details=res.details,
            ))
            return AttributionResult(
                state=AttributionState.NO_SIGNAL,
                candidate=None,
                confidence=0.0,
                confidence_level="NONE",
                evidence_items=evidence_items,
                summary="Abstain: No dynamic watermark recovered from artifact.",
                should_abstain=True,
            )

        evidence_items.append(EvidenceItem(
            source=EvidenceSource.TRACEABILITY_MARKER,
            title="Dynamic Watermark Recovery",
            is_valid=res.watermark_recovered,
            confidence=0.95 if res.watermark_recovered else 0.0,
            details={"symbols_recovered": res.observed_symbols_count},
        ))

        evidence_items.append(EvidenceItem(
            source=EvidenceSource.AUDIT_LEDGER,
            title="Permissioned DLT Quorum & Signature",
            is_valid=bool(res.quorum_verified and res.recipient_signature_verified),
            confidence=1.0 if (res.quorum_verified and res.recipient_signature_verified) else 0.0,
            details=res.details,
        ))

        if res.status == ForensicVerificationStatus.INVALID_SIGNATURE:
            return AttributionResult(
                state=AttributionState.INSUFFICIENT_EVIDENCE,
                candidate=None,
                confidence=0.0,
                confidence_level="NONE",
                evidence_items=evidence_items,
                summary="Abstain: Recipient ML-DSA-65 signature on DLT receipt failed verification.",
                should_abstain=True,
            )

        if res.status == ForensicVerificationStatus.UNAUTHORIZED_LEDGER:
            return AttributionResult(
                state=AttributionState.CONFLICT,
                candidate=None,
                confidence=0.0,
                confidence_level="NONE",
                evidence_items=evidence_items,
                summary="Abstain: DLT receipt not authorized, missing quorum, or uncommitted.",
                should_abstain=True,
            )

        if res.status == ForensicVerificationStatus.SUSPECT_TRANSPLANT:
            return AttributionResult(
                state=AttributionState.CONFLICT,
                candidate=None,
                confidence=0.0,
                confidence_level="NONE",
                evidence_items=evidence_items,
                summary="Abstain: Watermark appears transplanted or cross-document bound.",
                should_abstain=True,
            )

        if res.status == ForensicVerificationStatus.PROVEN_AUTHENTIC:
            rec_id = res.attributed_recipient_id or "UNKNOWN"
            recipient = self.registry.get(rec_id)
            display_name = recipient.name if recipient else f"Recipient [{rec_id}]"
            identity_id = recipient.identity_id if recipient else None
            identity_status = recipient.status if recipient else "ACTIVE"

            summary, res_status = self.identity_resolver.resolve_recipient(rec_id)
            if summary:
                if summary.display_name and not summary.display_name.startswith("Recipient ["):
                    display_name = summary.display_name
                elif not display_name:
                    display_name = summary.display_name
                identity_id = summary.identity_id
                if recipient and recipient.status in ["REVOKED", "DEPROVISIONED"]:
                    identity_status = recipient.status
                else:
                    identity_status = summary.status

            candidate = Candidate(
                recipient_id=rec_id,
                name=display_name,
                confidence=0.99,
                verified_events=[res.decryption_event_id] if res.decryption_event_id else [],
                identity_id=identity_id,
                identity_summary=summary,
                resolution_status=res_status,
                identity_status=identity_status,
            )

            return AttributionResult(
                state=AttributionState.ATTRIBUTED,
                candidate=candidate,
                confidence=0.99,
                confidence_level="HIGH",
                evidence_items=evidence_items,
                summary=f"Successfully attributed dynamic leak to recipient '{rec_id}' -> Identity '{display_name}'. "
                        f"{res.honesty_declaration}",
                should_abstain=False,
                forensic_attribution_level=ForensicAttributionLevel.LEVEL_2_ORIGINAL_RECIPIENT_IDENTIFIED,
                forensic_boundary_state=ForensicBoundaryState.ATTRIBUTED_TO_CONTROLLED_ACTOR,
                last_known_holder=rec_id,
                lineage_proof={
                    "lineage_depth": res.lineage_depth,
                    "lineage_path": res.lineage_path,
                    "dlt_block_height": res.dlt_block_height,
                    "merkle_verified": res.merkle_verified,
                    "quorum_verified": res.quorum_verified,
                }
            )

        return AttributionResult(
            state=AttributionState.INSUFFICIENT_EVIDENCE,
            candidate=None,
            confidence=0.0,
            confidence_level="NONE",
            evidence_items=evidence_items,
            summary="Abstain: Inconclusive forensic evidence.",
            should_abstain=True,
        )

default_attribution_engine = AttributionEngine()

