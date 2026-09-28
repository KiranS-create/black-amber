"""
SIH26237 - Forensic Calibration, Empirical Error Analysis & Statistical Validation Package
"""

from core.calibration.models import (
    PopulationCategory,
    DatasetSplit,
    ForensicGroundTruth,
    ForensicSampleRecord,
    ConfidenceInterval,
    ConfusionMatrix,
    ErrorRatesSummary,
    RiskCoveragePoint,
    AbstentionMetricsSummary,
    ReliabilityDiagramBin,
    ConfidenceCalibrationMetrics,
    RecipientSeparationSummary,
    VisualEquivalenceDistribution,
)
from core.calibration.uncertainty import (
    compute_wilson_score_interval,
    compute_clopper_pearson_interval,
    compute_zero_numerator_rule_of_three,
)
from core.calibration.metrics import (
    ForensicMetricsCalculator,
)
from core.calibration.corpora import (
    ForensicCorporaBuilder,
)
from core.calibration.evaluator import (
    ForensicCalibrationEvaluator,
)
from core.calibration.sweep import (
    ThresholdSweepEngine,
)
from core.calibration.separation import (
    RecipientSeparationAnalyzer,
)
from core.calibration.visual import (
    VisualEquivalenceDistributionAnalyzer,
)
from core.calibration.adversarial_search import (
    AdversarialEvidenceSearcher,
)

__all__ = [
    # Models
    "PopulationCategory",
    "DatasetSplit",
    "ForensicGroundTruth",
    "ForensicSampleRecord",
    "ConfidenceInterval",
    "ConfusionMatrix",
    "ErrorRatesSummary",
    "RiskCoveragePoint",
    "AbstentionMetricsSummary",
    "ReliabilityDiagramBin",
    "ConfidenceCalibrationMetrics",
    "RecipientSeparationSummary",
    "VisualEquivalenceDistribution",
    # Uncertainty
    "compute_wilson_score_interval",
    "compute_clopper_pearson_interval",
    "compute_zero_numerator_rule_of_three",
    # Metrics & Evaluator
    "ForensicMetricsCalculator",
    "ForensicCorporaBuilder",
    "ForensicCalibrationEvaluator",
    "ThresholdSweepEngine",
    "RecipientSeparationAnalyzer",
    "VisualEquivalenceDistributionAnalyzer",
    "AdversarialEvidenceSearcher",
]
