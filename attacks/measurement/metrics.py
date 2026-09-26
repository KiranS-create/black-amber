import math
from enum import Enum
from typing import Sequence, Union, Optional, Dict, Any, Tuple
import numpy as np
import cv2

class EvaluationOutcome(str, Enum):
    PASS = "PASS"
    DEGRADE = "DEGRADE"
    FAIL = "FAIL"
    ABSTAIN = "ABSTAIN"

class TraceabilityMetricsEvaluator:
    """
    Evaluates raw traceability signal survival, symbol fidelity, and error rates.
    Strictly separated from visual image quality metrics and attribution outcomes.
    """
    @staticmethod
    def symbol_survival_rate(original: Sequence[Any], observed: Sequence[Any]) -> float:
        """Fraction of symbols surviving identical in observed vector."""
        if not original or not observed:
            return 0.0
        n = min(len(original), len(observed))
        if n == 0:
            return 0.0
        matches = sum(1 for i in range(n) if original[i] == observed[i])
        return round(float(matches / len(original)), 4)

    @staticmethod
    def bit_error_rate(original: Sequence[Any], observed: Sequence[Any]) -> float:
        """Fraction of mismatched symbols (BER)."""
        return round(1.0 - TraceabilityMetricsEvaluator.symbol_survival_rate(original, observed), 4)

    @staticmethod
    def hamming_distance(original: Sequence[Any], observed: Sequence[Any]) -> int:
        """Absolute count of differing positions between equal-length vectors."""
        n = min(len(original), len(observed))
        diffs = sum(1 for i in range(n) if original[i] != observed[i])
        diffs += abs(len(original) - len(observed))
        return int(diffs)

    @staticmethod
    def erasure_rate(observed: Sequence[Any], erasure_value: Any = -1) -> float:
        """Fraction of observed positions marked as erasures."""
        if not observed:
            return 0.0
        erasures = sum(1 for sym in observed if sym == erasure_value)
        return round(float(erasures / len(observed)), 4)

    @staticmethod
    def normalized_cross_correlation(
        original: Sequence[Union[int, float]],
        observed: Sequence[Union[int, float]]
    ) -> float:
        """Normalized Pearson correlation between numeric signal vectors."""
        if not original or not observed:
            return 0.0
        n = min(len(original), len(observed))
        a = np.array(original[:n], dtype=np.float64)
        b = np.array(observed[:n], dtype=np.float64)
        
        # Replace non-finite / erasure values with zero for correlation
        b = np.nan_to_num(b, nan=0.0)

        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)

        if norm_a == 0 or norm_b == 0:
            return 0.0

        dot = np.dot(a, b)
        corr = float(dot / (norm_a * norm_b))
        return round(corr, 4)

    @staticmethod
    def classify_outcome(
        survival_rate: float,
        attribution_status: str,
        attributed_to_culprit: bool,
        pass_threshold: float = 0.90,
        abstain_threshold: float = 0.70
    ) -> Tuple[EvaluationOutcome, str]:
        """
        Map quantitative evidence and attribution decision into a definitive outcome:
        - PASS: High signal survival (>= pass_threshold) and correctly attributed.
        - DEGRADE: Moderate signal survival (abstain_threshold <= survival < pass_threshold).
        - ABSTAIN: Low signal (< abstain_threshold) or destroyed marker, and engine abstains.
        - FAIL: Accused wrong innocent party (false accusation), or failed to abstain when expected.
        """
        # If wrong innocent party was attributed, critical security FAIL
        if attribution_status == "ATTRIBUTED" and not attributed_to_culprit:
            return EvaluationOutcome.FAIL, "False accusation: Innocent party wrongly attributed."

        if survival_rate >= pass_threshold:
            if attribution_status == "ATTRIBUTED" and attributed_to_culprit:
                return EvaluationOutcome.PASS, f"Full traceability signal survived (survival: {survival_rate:.2f})."
            else:
                return EvaluationOutcome.DEGRADE, f"High survival ({survival_rate:.2f}) but attribution degraded."

        elif survival_rate >= abstain_threshold:
            return EvaluationOutcome.DEGRADE, f"Degraded signal survival ({survival_rate:.2f})."

        else:
            if attribution_status in ("NO_SIGNAL", "INSUFFICIENT_EVIDENCE", "ABSTAIN"):
                return EvaluationOutcome.ABSTAIN, f"Signal destroyed ({survival_rate:.2f}); system correctly abstained."
            elif attribution_status == "ATTRIBUTED":
                return EvaluationOutcome.FAIL, "System attributed despite insufficient/destroyed signal."
            else:
                return EvaluationOutcome.ABSTAIN, "Safe fail-closed abstention."
