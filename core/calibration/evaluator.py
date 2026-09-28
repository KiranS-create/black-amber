"""
SIH26237 - Forensic Calibration Evaluator
Executes multi-channel fusion evaluations across partitioned corpora,
maps decisions to ground truth, and computes empirical validation metrics.
"""

from typing import List, Dict, Any, Optional, Tuple
import numpy as np

from core.attribution.fusion import EvidenceFusionEngine, FusedAttributionResult
from core.attribution.policy import DecisionPolicy
from core.calibration.models import (
    DatasetSplit,
    PopulationCategory,
    ForensicSampleRecord,
    ConfusionMatrix,
    ErrorRatesSummary,
    AbstentionMetricsSummary,
    ConfidenceCalibrationMetrics,
)
from core.calibration.metrics import ForensicMetricsCalculator


class ForensicCalibrationEvaluator:
    """
    Coordinates batch forensic evaluation across sample corpora using
    EvidenceFusionEngine and DecisionPolicy.
    """

    def __init__(
        self,
        fusion_engine: Optional[EvidenceFusionEngine] = None,
        policy: Optional[DecisionPolicy] = None
    ):
        self.fusion_engine = fusion_engine or EvidenceFusionEngine(policy=policy)
        self.policy = policy or self.fusion_engine.policy

    def evaluate_sample(self, sample: ForensicSampleRecord) -> Dict[str, Any]:
        """Evaluates a single sample record and compares output with ground truth."""
        bundle = sample.evidence_bundle
        gt = sample.ground_truth

        fused_res: FusedAttributionResult = self.fusion_engine.fuse(bundle)

        pred_state = fused_res.state.value if hasattr(fused_res.state, "value") else str(fused_res.state)
        pred_rec = fused_res.top_candidate_id
        fused_score = fused_res.fused_score
        conf = fused_res.confidence

        # Evaluation accuracy
        is_pos = gt.is_attributable
        true_rec = gt.true_recipient_id

        is_correct_decision = False
        if is_pos:
            is_correct_decision = (pred_state == "ATTRIBUTED" and pred_rec == true_rec)
        else:
            is_correct_decision = (pred_state != "ATTRIBUTED")

        return {
            "sample_id": sample.sample_id,
            "split": gt.split.value,
            "population": gt.population.value,
            "document_id": gt.document_id,
            "release_id": gt.release_id,
            "is_attributable": is_pos,
            "true_recipient_id": true_rec,
            "predicted_state": pred_state,
            "predicted_recipient_id": pred_rec,
            "fused_score": round(fused_score, 4),
            "confidence": round(conf, 4),
            "confidence_level": fused_res.confidence_level.value if hasattr(fused_res.confidence_level, "value") else str(fused_res.confidence_level),
            "is_correct": is_correct_decision,
            "should_abstain": fused_res.should_abstain,
            "separation_margin": round(fused_res.separation_margin, 4)
        }

    def evaluate_corpus(
        self,
        samples: List[ForensicSampleRecord]
    ) -> Tuple[List[Dict[str, Any]], ConfusionMatrix, ErrorRatesSummary, AbstentionMetricsSummary, ConfidenceCalibrationMetrics]:
        """
        Evaluates a list of samples and computes complete statistical summaries.
        """
        results: List[Dict[str, Any]] = []
        for s in samples:
            results.append(self.evaluate_sample(s))

        # 1. Confusion Matrix & Error Rates
        cm = ForensicMetricsCalculator.compute_confusion_matrix(results)
        rates = ForensicMetricsCalculator.compute_error_rates(cm)

        # 2. Abstention Metrics
        abstention = ForensicMetricsCalculator.compute_abstention_metrics(results)

        # 3. Calibration ECE & Brier Score
        # Binary target: 1 if correctly attributed positive, 0 otherwise
        probs = [r["confidence"] for r in results]
        labels = [
            1 if (r["is_attributable"] and r["predicted_state"] == "ATTRIBUTED" and r["predicted_recipient_id"] == r["true_recipient_id"])
            else 0
            for r in results
        ]
        calib = ForensicMetricsCalculator.compute_calibration_metrics(probs, labels)

        return results, cm, rates, abstention, calib
