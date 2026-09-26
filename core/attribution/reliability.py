import math
from typing import Optional, Dict, Any, List
from core.attribution.evidence import (
    EvidenceFamily,
    EvidenceObservation,
    WatermarkObservation,
    TraceabilityObservation,
    ProvenanceObservation,
    LedgerObservation,
    AttackContextObservation,
    EvidenceBundle
)

class AttackAwareReliabilityCalibrator:
    """
    Attack-Aware Channel Reliability Calibrator.
    
    NOTE ON STATISTICAL VALIDITY:
    Channel reliability modifiers (rho_i) are HEURISTIC POLICY SCALING FUNCTIONS
    grounded in observed distortion behavior (BER, SSIM, crop, physical capture).
    They represent policy-defined sensitivity discounts rather than closed-form
    Bayesian posterior probabilities.
    """

    # HEURISTIC POLICY PARAMETER: Prior baseline channel weights in [0, 1]
    DEFAULT_FAMILY_PRIORS: Dict[EvidenceFamily, float] = {
        EvidenceFamily.PROVENANCE_SIGNATURE: 1.0,
        EvidenceFamily.AUDIT_LEDGER: 1.0,
        EvidenceFamily.CRYPTOGRAPHIC_INTEGRITY: 0.98,
        EvidenceFamily.TARDOS_FINGERPRINT: 0.95,
        EvidenceFamily.WATERMARK_PAYLOAD: 0.90,
        EvidenceFamily.DOCUMENT_STRUCTURE: 0.80,
        EvidenceFamily.ATTACK_CONTEXT: 0.85,
    }

    # HEURISTIC POLICY PARAMETER: Physical capture degradation scaling
    PHYSICAL_CAPTURE_DISCOUNT: float = 0.85

    def __init__(self, family_priors: Optional[Dict[EvidenceFamily, float]] = None):
        self.priors = dict(self.DEFAULT_FAMILY_PRIORS)
        if family_priors:
            self.priors.update(family_priors)

    def calibrate_bundle(self, bundle: EvidenceBundle) -> None:
        """
        In-place calibration of all observations within an evidence bundle.
        Modifies `effective_reliability` on each observation.
        """
        attack = bundle.attack_context

        for obs in bundle.observations:
            obs.effective_reliability = self.compute_reliability(obs, attack)

    def _sanitize_val(self, val: float, default: float = 0.0) -> float:
        """Sanitize numerical input against NaN, Inf, and out-of-bound values."""
        if val is None or math.isnan(val) or math.isinf(val):
            return default
        return float(val)

    def compute_reliability(
        self,
        obs: EvidenceObservation,
        attack: Optional[AttackContextObservation] = None
    ) -> float:
        """
        Compute effective reliability modifier rho_i in [0, 1] for a single observation.
        Safeguarded against NaN, Inf, negative, or invalid metrics.
        """
        if not obs.is_valid:
            return 0.0

        prior_val = self._sanitize_val(obs.reliability_prior, 1.0)
        family_prior = self._sanitize_val(self.priors.get(obs.family, 0.90), 0.90)
        base = max(0.0, min(1.0, prior_val * family_prior))

        # Specialized calibration per observation type
        if isinstance(obs, WatermarkObservation):
            base = self._calibrate_watermark(obs, base, attack)
        elif isinstance(obs, TraceabilityObservation):
            base = self._calibrate_traceability(obs, base, attack)
        elif isinstance(obs, ProvenanceObservation):
            base = self._calibrate_provenance(obs, base)
        elif isinstance(obs, LedgerObservation):
            base = self._calibrate_ledger(obs, base)

        # Global attack context impact
        if attack:
            # Physical capture discount for analog-sensitive channels
            if attack.execution_mode == "PHYSICAL":
                if obs.family in (EvidenceFamily.WATERMARK_PAYLOAD, EvidenceFamily.DOCUMENT_STRUCTURE):
                    base *= self.PHYSICAL_CAPTURE_DISCOUNT

            # Crop degradation
            if attack.crop_ratio is not None:
                crop = self._sanitize_val(attack.crop_ratio, 1.0)
                crop_clamped = max(0.0, min(1.0, crop))
                if obs.family == EvidenceFamily.WATERMARK_PAYLOAD:
                    base *= max(0.05, crop_clamped)

            # SSIM / Noise degradation
            if attack.ssim is not None:
                ssim = self._sanitize_val(attack.ssim, 1.0)
                if ssim < 0.7:
                    base *= max(0.1, max(0.0, min(1.0, ssim)))

        # Bound strictly in [0.0, 1.0] and check finite
        final_val = self._sanitize_val(base, 0.0)
        return max(0.0, min(1.0, final_val))

    def _calibrate_watermark(
        self,
        obs: WatermarkObservation,
        base: float,
        attack: Optional[AttackContextObservation]
    ) -> float:
        ber = self._sanitize_val(obs.bit_error_rate, 0.0)
        ber_clamped = max(0.0, min(1.0, ber))
        ber_factor = max(0.0, 1.0 - 2.0 * ber_clamped)
        base *= ber_factor

        sym_count = max(0, int(self._sanitize_val(obs.symbol_count, 0)))
        sym_extracted = max(0, int(self._sanitize_val(obs.symbols_extracted, 0)))

        if sym_count > 0 and sym_extracted < sym_count:
            extraction_ratio = sym_extracted / float(sym_count)
            base *= max(0.05, min(1.0, extraction_ratio))

        return base

    def _calibrate_traceability(
        self,
        obs: TraceabilityObservation,
        base: float,
        attack: Optional[AttackContextObservation]
    ) -> float:
        erasure = self._sanitize_val(obs.erasure_rate, 0.0)
        if erasure > 0.0:
            erasure_factor = max(0.0, 1.0 - min(1.0, erasure))
            base *= erasure_factor

        margin = self._sanitize_val(obs.margin_over_threshold, 0.0)
        if margin <= 0:
            return 0.0
        elif margin < 5.0:
            base *= (margin / 5.0)

        return base

    def _calibrate_provenance(self, obs: ProvenanceObservation, base: float) -> float:
        if not obs.signature_valid:
            return 0.0
        return base

    def _calibrate_ledger(self, obs: LedgerObservation, base: float) -> float:
        if not obs.chain_valid:
            return 0.0
        return base
