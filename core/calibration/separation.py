"""
SIH26237 - Recipient Separation & Scaled Candidate Pool Statistics
Analyzes pairwise Tardos / dynamic watermark codeword separation, Hamming distance distributions,
cross-correlation bounds, and collision frequencies across scaling candidate pools (10 to 10,000).
"""

import math
import hashlib
from typing import List, Dict, Any, Tuple, Optional
import numpy as np

from core.watermark.dynamic import derive_dynamic_codeword
from core.calibration.models import RecipientSeparationSummary


class RecipientSeparationAnalyzer:
    """
    Evaluates pairwise separation properties across recipient populations.
    Verifies that no two independent recipients produce dangerously close codewords.
    """

    @staticmethod
    def generate_candidate_codewords(
        pool_size: int,
        codeword_length: int = 128,
        salt_prefix: str = "AEGIS_SEPARATION_STUDY"
    ) -> List[List[int]]:
        """Generates deterministic pseudo-random codewords for N recipients."""
        codewords: List[List[int]] = []
        for i in range(pool_size):
            token_hex = hashlib.sha256(f"{salt_prefix}:{i:06d}".encode()).hexdigest()
            cw = derive_dynamic_codeword(token_hex, length=codeword_length)
            codewords.append(cw)
        return codewords

    @classmethod
    def analyze_separation(
        cls,
        candidate_pool_size: int = 100,
        codeword_length: int = 128,
        sample_comparisons: Optional[int] = None
    ) -> RecipientSeparationSummary:
        """
        Computes empirical pairwise Hamming distance and cross-correlation statistics.
        """
        codewords = cls.generate_candidate_codewords(candidate_pool_size, codeword_length)
        n = len(codewords)
        total_possible_pairs = n * (n - 1) // 2

        # Convert to numpy array for fast vector operations
        arr = np.array(codewords, dtype=np.int8)  # shape (n, m)

        min_hamming = codeword_length
        hamming_sum = 0
        max_cross_corr = -1.0
        collisions = 0
        comparisons_done = 0

        # Subsample if n is very large (> 2000) for performance
        if sample_comparisons and sample_comparisons < total_possible_pairs:
            rng = np.random.RandomState(42)
            for _ in range(sample_comparisons):
                i, j = rng.choice(n, size=2, replace=False)
                c1 = arr[i]
                c2 = arr[j]
                h_dist = int(np.sum(c1 != c2))
                # Normalized correlation in [-1, 1]: (matches - mismatches) / m
                corr = float(np.sum(c1 == c2) - h_dist) / float(codeword_length)

                min_hamming = min(min_hamming, h_dist)
                hamming_sum += h_dist
                max_cross_corr = max(max_cross_corr, corr)
                if h_dist == 0:
                    collisions += 1
                comparisons_done += 1
        else:
            for i in range(n):
                for j in range(i + 1, n):
                    c1 = arr[i]
                    c2 = arr[j]
                    h_dist = int(np.sum(c1 != c2))
                    corr = float(np.sum(c1 == c2) - h_dist) / float(codeword_length)

                    min_hamming = min(min_hamming, h_dist)
                    hamming_sum += h_dist
                    max_cross_corr = max(max_cross_corr, corr)
                    if h_dist == 0:
                        collisions += 1
                    comparisons_done += 1

        mean_hamming = float(hamming_sum) / float(comparisons_done) if comparisons_done > 0 else 0.0

        # Theoretical collision bound for independent m-bit Bernoulli(0.5) sequences:
        # P(collision) <= (N*(N-1)/2) * 2^(-m)
        theo_bound = (float(total_possible_pairs) * math.pow(2.0, -float(codeword_length)))

        return RecipientSeparationSummary(
            candidate_pool_size=candidate_pool_size,
            codeword_length_bits=codeword_length,
            pairwise_comparisons=comparisons_done,
            min_hamming_distance=min_hamming,
            mean_hamming_distance=round(mean_hamming, 2),
            max_cross_correlation=round(max_cross_corr, 4),
            observed_collisions=collisions,
            empirical_collision_rate_str=f"{collisions} / {comparisons_done}",
            theoretical_collision_bound=theo_bound,
            label="OBSERVED_ON_SYNTHETIC_CODEWORDS"
        )
