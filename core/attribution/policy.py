from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from core.attribution.evidence import AttributionState, EvidenceConfidenceLevel

class DecisionPolicy(BaseModel):
    """
    Forensic Decision Policy enforcing fail-closed attribution thresholds.
    
    Principles:
    1. NEVER FORCE AN ATTRIBUTION: Weak or ambiguous signals MUST result in
       NO_SIGNAL or INSUFFICIENT_EVIDENCE.
    2. CANDIDATE SEPARATION: If two candidates have close scores (Delta < min_separation_margin),
       the engine must abstain.
    3. CONFLICT RECOGNITION: If distinct independent channels point to different recipients,
       the state is CONFLICT.
       
    STATISTICAL AUDIT NOTICE:
    Threshold parameters (min_attribution_score, min_separation_margin, conflict_runnerup_threshold)
    are HEURISTIC POLICY PARAMETERS tuned for risk aversion rather than closed-form statistical distributions.
    The false alarm bound (max_false_alarm_bound) is a STATISTICAL BOUND derived from Tardos Chernoff/Bernstein inequalities.
    """

    # [HEURISTIC POLICY PARAMETER] Minimum fused log-likelihood score required for ATTRIBUTED (default 6.0 => ~403:1 LLR)
    min_attribution_score: float = 6.0

    # [HEURISTIC POLICY PARAMETER] Minimum margin Delta = S_(1) - S_(2) required over runner-up candidate
    min_separation_margin: float = 2.5

    # [HEURISTIC POLICY PARAMETER] Threshold for HIGH confidence rating
    high_confidence_score: float = 12.0

    # [HEURISTIC POLICY PARAMETER] Threshold for MEDIUM confidence rating
    medium_confidence_score: float = 6.0

    # [POLICY RULE] Whether a valid cryptographic signature is strictly mandatory for ATTRIBUTED
    strict_provenance_required: bool = False

    # [STATISTICAL BOUND] Maximum acceptable theoretical false accusation bound (Tardos epsilon_1)
    max_false_alarm_bound: float = 1e-3

    # [HEURISTIC POLICY PARAMETER] If top runner-up candidate also exceeds this threshold and margin is breached -> CONFLICT
    conflict_runnerup_threshold: float = 5.0

    def evaluate_confidence_level(self, score: float) -> EvidenceConfidenceLevel:
        """Map fused log-likelihood score to standardized confidence tier."""
        if score >= self.high_confidence_score:
            return EvidenceConfidenceLevel.HIGH
        elif score >= self.medium_confidence_score:
            return EvidenceConfidenceLevel.MEDIUM
        elif score > 0.0:
            return EvidenceConfidenceLevel.LOW
        else:
            return EvidenceConfidenceLevel.NONE

    def compute_probability(self, score: float) -> float:
        """
        Nominal Bayesian posterior probability P(Guilty | Evidence) assuming uniform prior odds:
        P = 1 / (1 + exp(-score))
        
        NOTE: This formula assumes calibrated log-likelihood ratios and uniform prior odds across
        all registered recipients. Under uncalibrated heuristic scores or non-uniform priors,
        this metric represents a ordinal confidence score rather than a true frequentist probability.
        """
        import math
        if math.isnan(score) or math.isinf(score):
            return 0.0
        if score <= -20.0:
            return 0.0
        if score >= 20.0:
            return 1.0
        return float(1.0 / (1.0 + math.exp(-score)))
