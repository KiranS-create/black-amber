import math
from enum import Enum
from typing import List, Optional, Dict, Any, Set
from pydantic import BaseModel, Field

class AttributionState(str, Enum):
    """
    Fail-closed attribution decision states.
    Abstention is mandatory whenever evidence is weak, corrupted, or conflicting.
    """
    ATTRIBUTED = "ATTRIBUTED"
    NO_SIGNAL = "NO_SIGNAL"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    CONFLICT = "CONFLICT"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"

class EvidenceFamily(str, Enum):
    """Distinct families of forensic evidence."""
    TARDOS_FINGERPRINT = "TARDOS_FINGERPRINT"
    WATERMARK_PAYLOAD = "WATERMARK_PAYLOAD"
    PROVENANCE_SIGNATURE = "PROVENANCE_SIGNATURE"
    AUDIT_LEDGER = "AUDIT_LEDGER"
    CRYPTOGRAPHIC_INTEGRITY = "CRYPTOGRAPHIC_INTEGRITY"
    DOCUMENT_STRUCTURE = "DOCUMENT_STRUCTURE"
    ATTACK_CONTEXT = "ATTACK_CONTEXT"

class DependencyType(str, Enum):
    """
    Inter-signal dependency classification to prevent double-counting.
    - INDEPENDENT: Completely separate measurement channels (additive log-LR).
    - PARTIALLY_DEPENDENT: Shared extraction/carrier (correlation discounted).
    - DERIVED: Higher-order statistic computed from child signal (bounded by max evidentiary contribution).
    """
    INDEPENDENT = "INDEPENDENT"
    PARTIALLY_DEPENDENT = "PARTIALLY_DEPENDENT"
    DERIVED = "DERIVED"

class EvidenceConfidenceLevel(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    NONE = "NONE"

class EvidenceSource(str, Enum):
    """Legacy and modern evidence source identifiers."""
    TRACEABILITY_MARKER = "TRACEABILITY_MARKER"
    AUDIT_LEDGER = "AUDIT_LEDGER"
    DOCUMENT_INTEGRITY = "DOCUMENT_INTEGRITY"
    RECIPIENT_SIGNATURE = "RECIPIENT_SIGNATURE"
    TARDOS_CODEWORD = "TARDOS_CODEWORD"
    WATERMARK_SPATIAL = "WATERMARK_SPATIAL"
    WATERMARK_FREQUENCY = "WATERMARK_FREQUENCY"
    METADATA_PROVENANCE = "METADATA_PROVENANCE"
    ATTACK_DETECTION = "ATTACK_DETECTION"

class TargetBinding(BaseModel):
    """Cryptographic binding tuple isolating document, release, and artifact."""
    document_id: Optional[str] = None
    release_id: Optional[str] = None
    artifact_hash: Optional[str] = None

    def matches(self, other: "TargetBinding") -> bool:
        """Check if bindings match where both are defined."""
        if self.document_id and other.document_id and self.document_id != other.document_id:
            return False
        if self.release_id and other.release_id and self.release_id != other.release_id:
            return False
        if self.artifact_hash and other.artifact_hash and self.artifact_hash != other.artifact_hash:
            return False
        return True

class EvidenceObservation(BaseModel):
    """
    Standardized observation from a single forensic detection or verification channel.
    """
    source_id: str
    family: EvidenceFamily
    dependency_type: DependencyType = DependencyType.INDEPENDENT
    parent_source_id: Optional[str] = None  # If DERIVED or PARTIALLY_DEPENDENT

    title: str = "Forensic Evidence Observation"
    is_valid: bool = True
    raw_signal: Optional[Dict[str, Any]] = None

    # Likelihood Ratio: P(E | H_guilty) / P(E | H_innocent)
    # log_lr = ln(LR). Positive indicates support for candidate; <= 0 indicates innocent or noise.
    log_likelihood_ratio: float = 0.0

    # Per-candidate log-LR mapping if multi-candidate evaluation is available
    candidate_scores: Dict[str, float] = Field(default_factory=dict)
    primary_candidate: Optional[str] = None

    # Base channel reliability prior in [0, 1]
    reliability_prior: float = 1.0

    # Effective reliability modifier after attack discounting in [0, 1]
    effective_reliability: float = 1.0

    # Target binding
    target_binding: TargetBinding = Field(default_factory=TargetBinding)

    details: Dict[str, Any] = Field(default_factory=dict)

    def get_candidate_llr(self, candidate_id: str) -> float:
        """Retrieve LLR for a specific candidate, defaulting to 0.0 if not scored."""
        if candidate_id in self.candidate_scores:
            return float(self.candidate_scores[candidate_id])
        if self.primary_candidate == candidate_id:
            return float(self.log_likelihood_ratio)
        return 0.0

    def compute_signal_fingerprint(self) -> str:
        """
        Compute deterministic fingerprint hash of the observation payload
        to prevent adversarial duplication attacks.
        """
        import hashlib, json
        payload = {
            "family": self.family.value,
            "primary_candidate": self.primary_candidate,
            "scores": {k: round(v, 4) for k, v in sorted(self.candidate_scores.items())},
            "log_lr": round(self.log_likelihood_ratio, 4),
            "target": {
                "doc": self.target_binding.document_id,
                "rel": self.target_binding.release_id,
                "hash": self.target_binding.artifact_hash
            }
        }
        encoded = json.dumps(payload, sort_keys=True).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()[:16]

class WatermarkObservation(EvidenceObservation):
    family: EvidenceFamily = Field(default=EvidenceFamily.WATERMARK_PAYLOAD)
    bit_error_rate: float = 0.0
    symbol_count: int = 0
    symbols_extracted: int = 0
    carrier_type: str = "SPATIAL_OR_FREQUENCY"

class TraceabilityObservation(EvidenceObservation):
    family: EvidenceFamily = Field(default=EvidenceFamily.TARDOS_FINGERPRINT)
    observed_length: int = 0
    erasure_rate: float = 0.0
    margin_over_threshold: float = 0.0
    theoretical_false_alarm_bound: float = 1.0
    accused_candidates: List[str] = Field(default_factory=list)

class ProvenanceObservation(EvidenceObservation):
    family: EvidenceFamily = Field(default=EvidenceFamily.PROVENANCE_SIGNATURE)
    algorithm: str = "ML-DSA-65"
    key_id: Optional[str] = None
    signature_valid: bool = False
    signer_recipient_id: Optional[str] = None

class LedgerObservation(EvidenceObservation):
    family: EvidenceFamily = Field(default=EvidenceFamily.AUDIT_LEDGER)
    chain_valid: bool = False
    matching_events_count: int = 0
    event_ids: List[str] = Field(default_factory=list)

class IntegrityObservation(EvidenceObservation):
    family: EvidenceFamily = Field(default=EvidenceFamily.CRYPTOGRAPHIC_INTEGRITY)
    hash_match: bool = False
    structure_intact: bool = True

class AttackContextObservation(EvidenceObservation):
    family: EvidenceFamily = Field(default=EvidenceFamily.ATTACK_CONTEXT)
    attack_family: Optional[str] = None
    attack_name: Optional[str] = None
    execution_mode: str = "SIMULATED"  # "PHYSICAL" or "SIMULATED"
    psnr: Optional[float] = None
    ssim: Optional[float] = None
    crop_ratio: Optional[float] = None
    noise_level: Optional[float] = None
    detected_collusion_size: Optional[int] = None

class EvidenceBundle(BaseModel):
    """
    Container of all gathered forensic evidence across all channels for a single inquiry.
    """
    bundle_id: str
    target_binding: TargetBinding = Field(default_factory=TargetBinding)
    observations: List[EvidenceObservation] = Field(default_factory=list)
    attack_context: Optional[AttackContextObservation] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def add_observation(self, observation: EvidenceObservation):
        self.observations.append(observation)

    def get_by_family(self, family: EvidenceFamily) -> List[EvidenceObservation]:
        return [o for o in self.observations if o.family == family]

    def get_candidate_ids(self) -> Set[str]:
        candidates = set()
        for o in self.observations:
            if o.primary_candidate:
                candidates.add(o.primary_candidate)
            for c in o.candidate_scores.keys():
                candidates.add(c)
        return candidates
