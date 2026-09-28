"""
SIH26237 - Forensic Calibration Data Models & Evaluation Schemas
Formalizes decision outcomes, evaluation populations, split manifests,
error rates with statistical confidence bounds, and abstention-aware metrics.
"""

from enum import Enum
from typing import Dict, List, Optional, Any, Tuple, Union
from datetime import datetime, timezone
from pydantic import BaseModel, Field

from core.attribution.evidence import AttributionState, EvidenceConfidenceLevel, EvidenceBundle


class PopulationCategory(str, Enum):
    """
    Evaluation populations representing distinct real-world and adversarial operating conditions.
    """
    POSITIVE_CORRECT = "A_POSITIVE_CORRECT"
    NEGATIVE_CLEAN = "B_NEGATIVE_CLEAN"
    WRONG_RECIPIENT = "C_WRONG_RECIPIENT"
    WRONG_DOCUMENT = "D_WRONG_DOCUMENT"
    TAMPERED_ARTIFACT = "E_TAMPERED_ARTIFACT"
    REPLAYED_EVIDENCE = "F_REPLAYED_EVIDENCE"
    CONFLICTING_EVIDENCE = "G_CONFLICTING_EVIDENCE"
    INSUFFICIENT_EVIDENCE = "H_INSUFFICIENT_EVIDENCE"
    UNKNOWN_DOWNSTREAM = "I_UNKNOWN_DOWNSTREAM"
    ACCOUNT_DEVICE_MISMATCH = "J_ACCOUNT_DEVICE_MISMATCH"
    TELEMETRY_GAP = "K_TELEMETRY_GAP"
    OUT_OF_ENVELOPE = "L_OUT_OF_ENVELOPE"


class DatasetSplit(str, Enum):
    """
    Strictly non-overlapping dataset partitions.
    Thresholds calibrated on CALIBRATION/VALIDATION are NEVER derived from HELD_OUT_TEST.
    """
    CALIBRATION = "CALIBRATION"
    VALIDATION = "VALIDATION"
    HELD_OUT_TEST = "HELD_OUT_TEST"


class ForensicGroundTruth(BaseModel):
    """
    Ground truth specification for a single calibration or test artifact.
    Honesty invariant: Unknown downstream leaks NEVER synthesize a fabricated suspect.
    """
    sample_id: str
    split: DatasetSplit
    population: PopulationCategory
    true_recipient_id: Optional[str] = None
    is_attributable: bool
    expected_state: AttributionState
    document_id: str
    release_id: str
    content_hash: str
    is_adversarial: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ForensicSampleRecord(BaseModel):
    """
    Executable evaluation sample with bound ground truth and evidence payload.
    """
    sample_id: str
    ground_truth: ForensicGroundTruth
    evidence_bundle: Optional[EvidenceBundle] = None
    carrier_bytes_hash: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ConfidenceInterval(BaseModel):
    """Statistical binomial confidence interval [lower, upper]."""
    point_estimate: float
    lower_bound_95: float
    upper_bound_95: float
    method: str  # "wilson_score" or "clopper_pearson_exact"
    sample_size: int
    success_count: int

    def to_display_string(self) -> str:
        return f"{self.point_estimate:.4f} (95% CI [{self.lower_bound_95:.4f}, {self.upper_bound_95:.4f}], n={self.sample_size})"


class ConfusionMatrix(BaseModel):
    """Forensic classification confusion matrix with abstentions."""
    tp: int = 0  # True positive (Attributed to correct recipient)
    tn: int = 0  # True negative (Correctly abstained / rejected on negative/invalid)
    fp: int = 0  # False positive (Attributed to incorrect recipient or attributed on clean negative)
    fn: int = 0  # False negative (Failed to attribute legitimate positive)
    abstentions_valid: int = 0    # Legitimate abstentions on ambiguous/insufficient samples
    abstentions_negative: int = 0 # Correct abstentions on negative corpus
    total_evaluated: int = 0


class ErrorRatesSummary(BaseModel):
    """Comprehensive empirical error rates with rigorous confidence bounds."""
    precision: float
    recall: float
    f1_score: float
    specificity: float
    fpr_empirical_str: str  # e.g. "0 / 1000"
    fpr_point_estimate: float
    fnr_empirical_str: str  # e.g. "12 / 1000"
    fnr_point_estimate: float
    fpr_ci_wilson: ConfidenceInterval
    fpr_ci_clopper_pearson: ConfidenceInterval
    fnr_ci_wilson: ConfidenceInterval
    fnr_ci_clopper_pearson: ConfidenceInterval
    precision_ci_wilson: ConfidenceInterval
    recall_ci_wilson: ConfidenceInterval


class RiskCoveragePoint(BaseModel):
    """Point on the empirical Risk-Coverage tradeoff curve."""
    threshold: float
    coverage: float               # Fraction of population attributed
    abstention_rate: float        # Fraction of population abstained (1 - coverage)
    selective_accuracy: float     # Accuracy among attributed cases
    selective_risk: float         # Error rate among attributed cases (1 - selective_accuracy)
    conditional_fp_count: int
    conditional_tp_count: int
    total_decided: int


class AbstentionMetricsSummary(BaseModel):
    """Metrics accounting for fail-closed abstention capabilities."""
    total_samples: int
    attributed_count: int
    abstained_count: int
    coverage: float
    abstention_rate: float
    selective_accuracy: float
    selective_risk: float
    risk_coverage_curve: List[RiskCoveragePoint] = Field(default_factory=list)


class ReliabilityDiagramBin(BaseModel):
    """Bin for confidence calibration assessment."""
    bin_index: int
    bin_lower: float
    bin_upper: float
    bin_center: float
    sample_count: int
    mean_confidence: float
    empirical_accuracy: float
    calibration_gap: float  # |mean_confidence - empirical_accuracy|


class ConfidenceCalibrationMetrics(BaseModel):
    """Statistical calibration metrics for attribution likelihood scores."""
    expected_calibration_error: float  # ECE (weighted average gap)
    maximum_calibration_error: float   # MCE (worst bin gap)
    brier_score: float                 # Mean squared error of probabilities
    brier_skill_score: float           # Skill relative to base rate
    reliability_bins: List[ReliabilityDiagramBin] = Field(default_factory=list)
    raw_score_median: float
    calibrated_probability_median: float


class RecipientSeparationSummary(BaseModel):
    """Pairwise separation and collision statistics across recipient candidate scales."""
    candidate_pool_size: int
    codeword_length_bits: int
    pairwise_comparisons: int
    min_hamming_distance: int
    mean_hamming_distance: float
    max_cross_correlation: float
    observed_collisions: int
    empirical_collision_rate_str: str  # "0 / N"
    theoretical_collision_bound: float
    label: str = "OBSERVED_ON_SYNTHETIC_CODEWORDS"


class VisualEquivalenceDistribution(BaseModel):
    """Empirical distribution of visual fidelity across document renders."""
    sample_count: int
    ssim_median: float
    ssim_p95: float
    ssim_p99: float
    ssim_min: float
    ssim_max: float
    psnr_median_db: float
    psnr_p95_db: float
    psnr_p99_db: float
    psnr_min_db: float
    psnr_max_db: float
    max_pixel_delta_median: float
    max_pixel_delta_p99: float
    max_pixel_delta_worst: float
    text_equality_pass_rate: float
    hardware_status: str = "NOT_VERIFIED"  # Explicit hardware boundary flag
