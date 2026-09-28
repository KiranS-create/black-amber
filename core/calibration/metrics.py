"""
SIH26237 - Forensic Metrics & Calibration Calculations
Implements:
- Standard Confusion Matrix & Classification Metrics
- Binomial Uncertainty & Error Bounds
- Abstention-Aware Coverage & Selective Accuracy
- Expected Calibration Error (ECE), MCE, and Brier Score
"""

import math
from typing import List, Dict, Any, Tuple, Optional
import numpy as np

from core.calibration.models import (
    ConfusionMatrix,
    ErrorRatesSummary,
    AbstentionMetricsSummary,
    RiskCoveragePoint,
    ConfidenceCalibrationMetrics,
    ReliabilityDiagramBin,
)
from core.calibration.uncertainty import (
    compute_wilson_score_interval,
    compute_clopper_pearson_interval,
)


class ForensicMetricsCalculator:
    """
    Computes rigorous forensic evaluation metrics, abstention curves,
    and statistical calibration metrics.
    """

    @staticmethod
    def compute_confusion_matrix(
        decisions: List[Dict[str, Any]],
    ) -> ConfusionMatrix:
        """
        Computes TP, TN, FP, FN and Abstentions from evaluated samples.
        Each sample dict contains:
        - `is_attributable`: bool (Ground truth positive)
        - `true_recipient_id`: Optional[str]
        - `predicted_state`: AttributionState
        - `predicted_recipient_id`: Optional[str]
        """
        tp = 0
        tn = 0
        fp = 0
        fn = 0
        abs_val = 0
        abs_neg = 0

        for d in decisions:
            is_pos = d["is_attributable"]
            true_rec = d.get("true_recipient_id")
            pred_state = d["predicted_state"]
            pred_rec = d.get("predicted_recipient_id")

            # Final decision classification
            is_attributed = (pred_state == "ATTRIBUTED")

            if is_pos:
                if is_attributed:
                    if pred_rec == true_rec:
                        tp += 1
                    else:
                        # Attributed to the WRONG recipient -> Fatal False Positive
                        fp += 1
                else:
                    # Legitimate positive abstained or unrecovered
                    fn += 1
                    abs_val += 1
            else:
                # Ground truth negative or non-attributable
                if is_attributed:
                    # Attributed on a negative/tampered/foreign carrier -> Fatal False Positive
                    fp += 1
                else:
                    # Correctly abstained / rejected
                    tn += 1
                    abs_neg += 1

        total = len(decisions)
        return ConfusionMatrix(
            tp=tp,
            tn=tn,
            fp=fp,
            fn=fn,
            abstentions_valid=abs_val,
            abstentions_negative=abs_neg,
            total_evaluated=total
        )

    @staticmethod
    def compute_error_rates(cm: ConfusionMatrix) -> ErrorRatesSummary:
        """Computes point estimates and 95% confidence intervals for all error metrics."""
        total_pos = cm.tp + cm.fn
        total_neg = cm.tn + cm.fp
        total_pred_pos = cm.tp + cm.fp

        # Precision = TP / (TP + FP)
        precision = float(cm.tp) / float(total_pred_pos) if total_pred_pos > 0 else 1.0
        prec_ci = compute_wilson_score_interval(cm.tp, total_pred_pos)

        # Recall (Sensitivity) = TP / (TP + FN)
        recall = float(cm.tp) / float(total_pos) if total_pos > 0 else 0.0
        rec_ci = compute_wilson_score_interval(cm.tp, total_pos)

        # Specificity = TN / (TN + FP)
        specificity = float(cm.tn) / float(total_neg) if total_neg > 0 else 1.0

        # F1 Score
        f1 = 2.0 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

        # False Positive Rate (FPR) = FP / (FP + TN)
        fpr_pt = float(cm.fp) / float(total_neg) if total_neg > 0 else 0.0
        fpr_ci_w = compute_wilson_score_interval(cm.fp, total_neg)
        fpr_ci_cp = compute_clopper_pearson_interval(cm.fp, total_neg)

        # False Negative Rate (FNR) = FN / (FN + TP)
        fnr_pt = float(cm.fn) / float(total_pos) if total_pos > 0 else 0.0
        fnr_ci_w = compute_wilson_score_interval(cm.fn, total_pos)
        fnr_ci_cp = compute_clopper_pearson_interval(cm.fn, total_pos)

        return ErrorRatesSummary(
            precision=round(precision, 4),
            recall=round(recall, 4),
            f1_score=round(f1, 4),
            specificity=round(specificity, 4),
            fpr_empirical_str=f"{cm.fp} / {total_neg}",
            fpr_point_estimate=round(fpr_pt, 6),
            fnr_empirical_str=f"{cm.fn} / {total_pos}",
            fnr_point_estimate=round(fnr_pt, 6),
            fpr_ci_wilson=fpr_ci_w,
            fpr_ci_clopper_pearson=fpr_ci_cp,
            fnr_ci_wilson=fnr_ci_w,
            fnr_ci_clopper_pearson=fnr_ci_cp,
            precision_ci_wilson=prec_ci,
            recall_ci_wilson=rec_ci
        )

    @staticmethod
    def compute_abstention_metrics(
        evaluated_samples: List[Dict[str, Any]],
        thresholds: Optional[List[float]] = None
    ) -> AbstentionMetricsSummary:
        """
        Computes coverage, selective accuracy, and risk-coverage curve across score thresholds.
        """
        total = len(evaluated_samples)
        if total == 0:
            return AbstentionMetricsSummary(
                total_samples=0,
                attributed_count=0,
                abstained_count=0,
                coverage=0.0,
                abstention_rate=1.0,
                selective_accuracy=1.0,
                selective_risk=0.0
            )

        attributed = [s for s in evaluated_samples if s.get("predicted_state") == "ATTRIBUTED"]
        attr_count = len(attributed)
        abs_count = total - attr_count

        coverage = float(attr_count) / float(total)
        abstention_rate = float(abs_count) / float(total)

        # Selective accuracy: Accuracy among cases where the system chose to attribute
        correct_attributed = sum(
            1 for s in attributed
            if s.get("is_attributable") and s.get("predicted_recipient_id") == s.get("true_recipient_id")
        )
        selective_accuracy = float(correct_attributed) / float(attr_count) if attr_count > 0 else 1.0
        selective_risk = 1.0 - selective_accuracy

        # Risk-Coverage Curve across threshold sweep
        pts: List[RiskCoveragePoint] = []
        sweep_threshs = thresholds or [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 10.0, 12.0, 15.0]

        for th in sweep_threshs:
            decided = [s for s in evaluated_samples if s.get("fused_score", 0.0) >= th]
            n_dec = len(decided)
            cov_t = float(n_dec) / float(total)
            abs_t = 1.0 - cov_t

            tp_t = sum(1 for s in decided if s.get("is_attributable") and s.get("predicted_recipient_id") == s.get("true_recipient_id"))
            fp_t = sum(1 for s in decided if (not s.get("is_attributable")) or (s.get("predicted_recipient_id") != s.get("true_recipient_id")))

            sel_acc_t = float(tp_t) / float(n_dec) if n_dec > 0 else 1.0
            sel_risk_t = 1.0 - sel_acc_t

            pts.append(RiskCoveragePoint(
                threshold=th,
                coverage=round(cov_t, 4),
                abstention_rate=round(abs_t, 4),
                selective_accuracy=round(sel_acc_t, 4),
                selective_risk=round(sel_risk_t, 4),
                conditional_fp_count=fp_t,
                conditional_tp_count=tp_t,
                total_decided=n_dec
            ))

        return AbstentionMetricsSummary(
            total_samples=total,
            attributed_count=attr_count,
            abstained_count=abs_count,
            coverage=round(coverage, 4),
            abstention_rate=round(abstention_rate, 4),
            selective_accuracy=round(selective_accuracy, 4),
            selective_risk=round(selective_risk, 4),
            risk_coverage_curve=pts
        )

    @staticmethod
    def compute_calibration_metrics(
        predicted_probabilities: List[float],
        ground_truth_binary: List[int],
        num_bins: int = 10
    ) -> ConfidenceCalibrationMetrics:
        """
        Computes ECE, MCE, Brier Score, and reliability diagram bins.
        - predicted_probabilities in [0.0, 1.0]
        - ground_truth_binary in {0, 1}
        """
        if not predicted_probabilities or len(predicted_probabilities) != len(ground_truth_binary):
            return ConfidenceCalibrationMetrics(
                expected_calibration_error=0.0,
                maximum_calibration_error=0.0,
                brier_score=0.0,
                brier_skill_score=0.0,
                raw_score_median=0.0,
                calibrated_probability_median=0.0
            )

        probs = np.array(predicted_probabilities, dtype=np.float64)
        labels = np.array(ground_truth_binary, dtype=np.float64)
        n = len(probs)

        # 1. Brier Score: (1/n) * sum((p_i - y_i)^2)
        brier = float(np.mean((probs - labels) ** 2))

        # Base rate Brier score
        base_rate = float(np.mean(labels))
        brier_ref = float(base_rate * (1.0 - base_rate))
        brier_skill = float(1.0 - (brier / brier_ref)) if brier_ref > 0 else 1.0

        # 2. Binning for ECE and MCE
        bins = np.linspace(0.0, 1.0, num_bins + 1)
        ece = 0.0
        mce = 0.0
        reliability_bins: List[ReliabilityDiagramBin] = []

        for b in range(num_bins):
            low = bins[b]
            high = bins[b + 1]
            if b == num_bins - 1:
                mask = (probs >= low) & (probs <= high)
            else:
                mask = (probs >= low) & (probs < high)

            count = int(np.sum(mask))
            if count > 0:
                bin_conf = float(np.mean(probs[mask]))
                bin_acc = float(np.mean(labels[mask]))
                gap = abs(bin_conf - bin_acc)

                ece += (float(count) / float(n)) * gap
                mce = max(mce, gap)

                reliability_bins.append(ReliabilityDiagramBin(
                    bin_index=b,
                    bin_lower=round(float(low), 2),
                    bin_upper=round(float(high), 2),
                    bin_center=round(float(low + high) / 2.0, 2),
                    sample_count=count,
                    mean_confidence=round(bin_conf, 4),
                    empirical_accuracy=round(bin_acc, 4),
                    calibration_gap=round(gap, 4)
                ))
            else:
                reliability_bins.append(ReliabilityDiagramBin(
                    bin_index=b,
                    bin_lower=round(float(low), 2),
                    bin_upper=round(float(high), 2),
                    bin_center=round(float(low + high) / 2.0, 2),
                    sample_count=0,
                    mean_confidence=round(float(low + high) / 2.0, 4),
                    empirical_accuracy=0.0,
                    calibration_gap=0.0
                ))

        return ConfidenceCalibrationMetrics(
            expected_calibration_error=round(float(ece), 4),
            maximum_calibration_error=round(float(mce), 4),
            brier_score=round(float(brier), 4),
            brier_skill_score=round(float(brier_skill), 4),
            reliability_bins=reliability_bins,
            raw_score_median=round(float(np.median(probs)), 4),
            calibrated_probability_median=round(float(np.median(probs)), 4)
        )
