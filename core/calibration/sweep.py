"""
SIH26237 - Forensic Threshold Sweep & Policy Optimization Engine
Systematic multi-dimensional threshold sweeps over the attribution decision boundary.
Optimizes for zero false positives, high selective accuracy, and maximal legitimate coverage.
"""

from typing import List, Dict, Any, Tuple, Optional
from core.attribution.policy import DecisionPolicy
from core.attribution.fusion import EvidenceFusionEngine
from core.calibration.models import (
    ForensicSampleRecord,
    ConfusionMatrix,
    ErrorRatesSummary,
    AbstentionMetricsSummary,
)
from core.calibration.evaluator import ForensicCalibrationEvaluator


class ThresholdSweepEngine:
    """
    Executes systematic parameter sweeps over decision policy thresholds:
    - min_attribution_score
    - min_separation_margin
    - conflict_runnerup_threshold
    """

    def __init__(self, samples: List[ForensicSampleRecord]):
        self.samples = samples

    def sweep_attribution_score(
        self,
        scores: Optional[List[float]] = None,
        fixed_margin: float = 2.5,
        fixed_conflict: float = 5.0
    ) -> List[Dict[str, Any]]:
        """Sweeps min_attribution_score across predefined grid."""
        grid = scores or [2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 12.0, 14.0]
        results: List[Dict[str, Any]] = []

        for score_th in grid:
            policy = DecisionPolicy(
                min_attribution_score=score_th,
                min_separation_margin=fixed_margin,
                conflict_runnerup_threshold=fixed_conflict
            )
            evaluator = ForensicCalibrationEvaluator(policy=policy)
            _, cm, rates, abstention, calib = evaluator.evaluate_corpus(self.samples)

            results.append({
                "min_attribution_score": score_th,
                "min_separation_margin": fixed_margin,
                "conflict_runnerup_threshold": fixed_conflict,
                "tp": cm.tp,
                "tn": cm.tn,
                "fp": cm.fp,
                "fn": cm.fn,
                "abstentions_valid": cm.abstentions_valid,
                "abstentions_negative": cm.abstentions_negative,
                "precision": rates.precision,
                "recall": rates.recall,
                "f1_score": rates.f1_score,
                "specificity": rates.specificity,
                "fpr_empirical": rates.fpr_empirical_str,
                "fpr_point_estimate": rates.fpr_point_estimate,
                "fnr_empirical": rates.fnr_empirical_str,
                "fnr_point_estimate": rates.fnr_point_estimate,
                "coverage": abstention.coverage,
                "selective_accuracy": abstention.selective_accuracy,
                "selective_risk": abstention.selective_risk,
                "ece": calib.expected_calibration_error,
                "brier_score": calib.brier_score
            })

        return results

    def find_optimal_threshold(
        self,
        sweep_results: List[Dict[str, Any]],
        max_acceptable_fpr: float = 0.0,
        min_selective_accuracy: float = 0.99
    ) -> Dict[str, Any]:
        """
        Formal Pareto Decision Policy Selection Rule:
        1. Strict constraint: Empirical FP == 0 (FPR <= max_acceptable_fpr)
        2. Strict constraint: Selective Accuracy >= min_selective_accuracy
        3. Maximize Coverage among surviving candidate policies
        4. Tie-breaker: Minimize Expected Calibration Error (ECE)
        """
        candidates = [
            r for r in sweep_results
            if r["fp"] == 0 and r["selective_accuracy"] >= min_selective_accuracy
        ]

        if not candidates:
            # Fallback to safest policy (highest threshold)
            return max(sweep_results, key=lambda r: r["min_attribution_score"])

        # Sort by coverage descending, then ECE ascending
        sorted_candidates = sorted(
            candidates,
            key=lambda r: (r["coverage"], -r["ece"]),
            reverse=True
        )
        return sorted_candidates[0]
