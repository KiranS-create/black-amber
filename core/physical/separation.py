"""
SIH26237 - Cross-Recipient Physical Separation Matrix
Constructs pairwise separation metrics across distinct recipients (Alice, Bob, Charlie)
under physical/optical capture conditions.
Verifies that no cross-recipient misattribution or codeword collision occurs.
"""

from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from pydantic import BaseModel, Field

from core.physical.trial_engine import PhysicalTrialEngine, PhysicalTrialSessionRecord
from core.watermark.pipeline import CanonicalCanvasSpec, PrintCameraWatermarkDecoder


class PairwiseSeparationEntry(BaseModel):
    recipient_a: str
    recipient_b: str
    hamming_distance: int
    normalized_correlation: float
    bit_error_rate: float
    is_orthogonal: bool
    collision_detected: bool


class PhysicalSeparationMatrixSummary(BaseModel):
    """Pairwise separation matrix and collision summary across physical captures."""
    evaluated_recipients: List[str]
    codeword_length_bits: int = 128
    pairwise_entries: List[PairwiseSeparationEntry]
    mean_pairwise_hamming_distance: float
    min_pairwise_hamming_distance: int
    max_pairwise_correlation: float
    observed_cross_recipient_collisions: int
    empirical_collision_rate_str: str  # "0 / N"
    epistemic_classification: str = "NOT_VERIFIED"


CrossRecipientSeparationMatrix = PhysicalSeparationMatrixSummary


class PhysicalSeparationMatrixAnalyzer:
    """
    Evaluates physical cross-recipient orthogonality and separation properties.
    """

    @classmethod
    def analyze_cross_recipient_separation(
        cls,
        trial_engine: Optional[PhysicalTrialEngine] = None,
        canvas_spec: Optional[CanonicalCanvasSpec] = None
    ) -> PhysicalSeparationMatrixSummary:
        engine = trial_engine or PhysicalTrialEngine(canvas_spec=canvas_spec)
        engine.setup_standard_laboratory_recipients()

        recipients = ["rec_alice", "rec_bob", "rec_charlie"]
        sessions: Dict[str, PhysicalTrialSessionRecord] = {}

        # Generate trial session for each recipient
        for r_id in recipients:
            _, rec = engine.execute_decryption_and_render_artifact(r_id)
            sessions[r_id] = rec

        pairwise_entries: List[PairwiseSeparationEntry] = []
        hamming_sum = 0
        min_hamming = 128
        max_corr = -1.0
        collisions = 0
        comparisons_done = 0

        for i in range(len(recipients)):
            for j in range(i + 1, len(recipients)):
                r_a = recipients[i]
                r_b = recipients[j]
                cw_a = np.array(sessions[r_a].codeword_bits, dtype=np.int8)
                cw_b = np.array(sessions[r_b].codeword_bits, dtype=np.int8)

                m = len(cw_a)
                h_dist = int(np.sum(cw_a != cw_b))
                ber = float(h_dist) / float(m)
                corr = float(np.sum(cw_a == cw_b) - h_dist) / float(m)

                min_hamming = min(min_hamming, h_dist)
                hamming_sum += h_dist
                max_corr = max(max_corr, corr)
                is_coll = (h_dist == 0)
                if is_coll:
                    collisions += 1
                comparisons_done += 1

                pairwise_entries.append(PairwiseSeparationEntry(
                    recipient_a=r_a,
                    recipient_b=r_b,
                    hamming_distance=h_dist,
                    normalized_correlation=round(corr, 4),
                    bit_error_rate=round(ber, 4),
                    is_orthogonal=(h_dist >= 40),
                    collision_detected=is_coll
                ))

        mean_hamming = float(hamming_sum) / float(comparisons_done) if comparisons_done > 0 else 0.0

        return PhysicalSeparationMatrixSummary(
            evaluated_recipients=recipients,
            codeword_length_bits=128,
            pairwise_entries=pairwise_entries,
            mean_pairwise_hamming_distance=round(mean_hamming, 2),
            min_pairwise_hamming_distance=min_hamming,
            max_pairwise_correlation=round(max_corr, 4),
            observed_cross_recipient_collisions=collisions,
            empirical_collision_rate_str=f"{collisions} / {comparisons_done}",
            epistemic_classification="NOT_VERIFIED"
        )
