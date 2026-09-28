"""
SIH26237 - Physical Validation Uncertainty & Statistical Error Metrics
Computes empirical error rates, coverage, and exact Clopper-Pearson / Wilson Score
confidence intervals across partitioned physical validation corpora.
"""

from typing import List, Dict, Any, Tuple, Optional
import math
from pydantic import BaseModel, Field

from core.calibration.uncertainty import compute_wilson_score_interval, compute_clopper_pearson_interval
from core.calibration.models import ConfidenceInterval
from core.physical.experiments import PhysicalTrialResult
from core.physical.negative_corpus import PhysicalNegativeResult


class PhysicalValidationConfusionMatrix(BaseModel):
    tp: int = 0
    tn: int = 0
    fp: int = 0
    fn: int = 0
    total_evaluated: int = 0


class PhysicalUncertaintySummary(BaseModel):
    """Statistical error rate summary with exact confidence intervals."""
    total_samples: int
    positive_samples_tested: int
    negative_samples_tested: int
    tp: int
    tn: int
    fp: int
    fn: int
    precision: float
    recall: float
    specificity: float
    fpr_empirical_str: str  # "0 / N"
    fpr_point_estimate: float
    fpr_ci_wilson: ConfidenceInterval
    fpr_ci_clopper_pearson: ConfidenceInterval
    fnr_empirical_str: str  # "0 / N"
    fnr_point_estimate: float
    fnr_ci_wilson: ConfidenceInterval
    fnr_ci_clopper_pearson: ConfidenceInterval
    epistemic_classification: str = "NOT_VERIFIED"


class PhysicalMetricsCalculator:
    """
    Computes statistical error rates and confidence intervals for physical laboratory benchmarks.
    """

    @classmethod
    def calculate_metrics(
        cls,
        trial_results: List[PhysicalTrialResult],
        negative_results: List[PhysicalNegativeResult]
    ) -> PhysicalUncertaintySummary:
        """Alias for compute_summary."""
        return cls.compute_summary(positive_results=trial_results, negative_results=negative_results)

    @classmethod
    def compute_summary(
        cls,
        positive_results: List[PhysicalTrialResult],
        negative_results: List[PhysicalNegativeResult]
    ) -> PhysicalUncertaintySummary:

        tp = sum(1 for r in positive_results if r.is_correct_attribution)
        fn = sum(1 for r in positive_results if not r.is_correct_attribution)
        pos_total = len(positive_results)

        fp = sum(1 for r in negative_results if r.false_positive_attribution)
        tn = sum(1 for r in negative_results if not r.false_positive_attribution)
        neg_total = len(negative_results)

        total = pos_total + neg_total

        prec = float(tp) / float(tp + fp) if (tp + fp) > 0 else 1.0
        rec = float(tp) / float(tp + fn) if (tp + fn) > 0 else 0.0
        spec = float(tn) / float(tn + fp) if (tn + fp) > 0 else 1.0

        fpr_pt = float(fp) / float(neg_total) if neg_total > 0 else 0.0
        fnr_pt = float(fn) / float(pos_total) if pos_total > 0 else 0.0

        fpr_wilson = compute_wilson_score_interval(fp, neg_total)
        fpr_cp = compute_clopper_pearson_interval(fp, neg_total)

        fnr_wilson = compute_wilson_score_interval(fn, pos_total)
        fnr_cp = compute_clopper_pearson_interval(fn, pos_total)

        return PhysicalUncertaintySummary(
            total_samples=total,
            positive_samples_tested=pos_total,
            negative_samples_tested=neg_total,
            tp=tp,
            tn=tn,
            fp=fp,
            fn=fn,
            precision=round(prec, 4),
            recall=round(rec, 4),
            specificity=round(spec, 4),
            fpr_empirical_str=f"{fp} / {neg_total}",
            fpr_point_estimate=round(fpr_pt, 6),
            fpr_ci_wilson=fpr_wilson,
            fpr_ci_clopper_pearson=fpr_cp,
            fnr_empirical_str=f"{fn} / {pos_total}",
            fnr_point_estimate=round(fnr_pt, 6),
            fnr_ci_wilson=fnr_wilson,
            fnr_ci_clopper_pearson=fnr_cp,
            epistemic_classification="NOT_VERIFIED"
        )
