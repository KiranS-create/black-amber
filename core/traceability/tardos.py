import math
import hmac
import hashlib
from enum import Enum
from typing import Dict, Any, List, Optional, Tuple
from pydantic import BaseModel, Field

class AccusationStatus(str, Enum):
    ATTRIBUTED = "ATTRIBUTED"
    NO_SIGNAL = "NO_SIGNAL"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    COLLUSION_DETECTED = "COLLUSION_DETECTED"

class TardosAccusationResult(BaseModel):
    status: AccusationStatus
    accused_recipients: List[str] = Field(default_factory=list)
    scores: Dict[str, float] = Field(default_factory=dict)
    threshold: float
    max_score: float
    margin: float  # max_score - threshold
    mean_score: float
    score_std_dev: float
    false_accusation_bound: float
    observed_length: int
    erasure_count: int = 0
    erasure_rate: float = 0.0
    details: Dict[str, Any] = Field(default_factory=dict)

from core.traceability.keystore import TraceabilityKeystore

class SymmetricTardosEngine:
    """
    Symmetric Tardos Fingerprinting & Traitor-Tracing Engine.
    
    Theoretical References:
    - G\u00e1bor Tardos, "Optimal Probabilistic Fingerprint Codes", STOC 2003 / J. ACM 2008.
    - Boris \u0160kori\u0107, Stefan Katzenbeisser, and Mehmet U. Celik, "Symmetric Tardos 
      Fingerprinting Codes for Arbitrary Alphabet Sizes", Designs, Codes and Cryptography 2008.
    - O. Blayer and T. Tassa, "Improved Versions of Tardos' Fingerprinting Code", 
      Designs, Codes and Cryptography 2008.
    
    Guarantees:
    - Under the Marking Assumption:
      1. False-positive accusation bounded by epsilon_1 via Chernoff/Bernstein bound:
         P(S_innocent >= Z) <= epsilon_1
      2. Zero expectation for innocent recipients: E[S_innocent] = 0 across any collusion strategy.
      3. Positive expected score for guilty colluders: sum_{k in C} E[S_k] >= (2 / pi) * m.
      4. Fail-closed abstention when evidence does not cross the cryptographic threshold Z.
    """

    @classmethod
    def compute_cutoff(cls, c: int) -> float:
        """Cutoff parameter t = 1 / (300 * c) for distribution bounding."""
        if c <= 0:
            raise ValueError(f"Coalition size c must be positive, got {c}")
        return 1.0 / (300.0 * float(c))

    @classmethod
    def generate_biases(
        cls,
        m: int,
        c: int,
        seed: Optional[bytes] = None
    ) -> List[float]:
        """
        Generate m secret bias parameters p_j in [t, 1-t] sampled from the continuous
        arcsin probability density function:
            f(p) = 1 / (2 * arcsin(1 - 2t)) * 1 / sqrt(p * (1 - p))
        
        Using transformation:
            p_j = sin^2( t' + r_j * (pi / 2 - 2 * t') )
            where t' = arcsin(sqrt(t)), r_j ~ Uniform[0, 1]
        """
        if m <= 0:
            raise ValueError(f"Code length m must be positive, got {m}")
        if c <= 0:
            raise ValueError(f"Coalition size c must be positive, got {c}")

        key = TraceabilityKeystore.resolve_secret(seed)
        t = cls.compute_cutoff(c)
        t_prime = math.asin(math.sqrt(t))
        span = (math.pi / 2.0) - (2.0 * t_prime)

        biases: List[float] = []
        for j in range(m):
            # Deterministic PRNG from HMAC-SHA256 for verifiability
            msg = f"bias:{j}:{c}".encode('utf-8')
            digest = hmac.new(key, msg, hashlib.sha256).digest()
            val_int = int.from_bytes(digest[:8], byteorder="big", signed=False)
            r_j = val_int / float(0xFFFFFFFFFFFFFFFF)

            # Continuous arcsin transform
            theta = t_prime + r_j * span
            p_j = math.sin(theta) ** 2

            # Clamp tightly within [t, 1 - t] to prevent division by zero in scoring
            p_j = max(t, min(1.0 - t, p_j))
            biases.append(p_j)

        return biases

    @classmethod
    def generate_codebook(
        cls,
        recipient_ids: List[str],
        biases: List[float],
        seed: Optional[bytes] = None
    ) -> Dict[str, List[int]]:
        """
        Generate recipient-specific binary codewords X_{i,j} in {0, 1}^m.
        For each recipient i and position j:
            P(X_{i,j} = 1) = p_j
            P(X_{i,j} = 0) = 1 - p_j
        
        Deterministic: derived from HMAC(seed, "code:{recipient_id}:{j}").
        """
        key = TraceabilityKeystore.resolve_secret(seed)
        codebook: Dict[str, List[int]] = {}

        for recipient_id in recipient_ids:
            codeword: List[int] = []
            for j, p_j in enumerate(biases):
                msg = f"code:{recipient_id}:{j}".encode('utf-8')
                digest = hmac.new(key, msg, hashlib.sha256).digest()
                val_int = int.from_bytes(digest[:8], byteorder="big", signed=False)
                u_ij = val_int / float(0xFFFFFFFFFFFFFFFF)

                bit = 1 if u_ij < p_j else 0
                codeword.append(bit)
            codebook[recipient_id] = codeword

        return codebook

    @classmethod
    def score_symbol(cls, y_j: int, x_ij: int, p_j: float) -> float:
        """
        Symmetric Tardos score function (Škorić et al. 2008):
            U(1, 1, p) = +sqrt((1 - p) / p)
            U(1, 0, p) = -sqrt(p / (1 - p))
            U(0, 1, p) = -sqrt((1 - p) / p)
            U(0, 0, p) = +sqrt(p / (1 - p))
        
        Erasure handling:
            If y_j = -1 (erasure / missing / carrier corrupted), returns 0.0.
        """
        if y_j == -1:
            return 0.0

        p = max(1e-12, min(1.0 - 1e-12, p_j))
        pos_term = math.sqrt((1.0 - p) / p)
        neg_term = math.sqrt(p / (1.0 - p))

        if y_j == 1:
            return pos_term if x_ij == 1 else -neg_term
        elif y_j == 0:
            return -pos_term if x_ij == 1 else neg_term
        else:
            # Unrecognized symbol treated as erasure (abstain on position)
            return 0.0

    @classmethod
    def score_all(
        cls,
        observed_symbols: List[int],
        codebook: Dict[str, List[int]],
        biases: List[float]
    ) -> Dict[str, float]:
        """
        Compute total accumulated score S_i = sum_{j=1}^m U(y_j, X_{i,j}, p_j)
        for every recipient in the codebook.
        """
        m = len(biases)
        if len(observed_symbols) != m:
            raise ValueError(
                f"Observed symbols length ({len(observed_symbols)}) must match bias length ({m})"
            )

        scores: Dict[str, float] = {}
        for recipient_id, codeword in codebook.items():
            if len(codeword) != m:
                raise ValueError(
                    f"Codeword length for {recipient_id} ({len(codeword)}) must match bias length ({m})"
                )
            
            s_i = 0.0
            for j in range(m):
                s_i += cls.score_symbol(observed_symbols[j], codeword[j], biases[j])
            scores[recipient_id] = s_i

        return scores

    @classmethod
    def compute_threshold(
        cls,
        m: int,
        recipient_count: int,
        epsilon_1: float
    ) -> float:
        """
        Compute Chernoff/Bernstein accusation threshold Z:
            Z = sqrt(2 * m * ln(N / epsilon_1))
        Guarantees that for any innocent recipient i, P(S_i >= Z) <= epsilon_1 / N,
        so by union bound P(exists innocent i with S_i >= Z) <= epsilon_1.
        """
        if m <= 0 or recipient_count <= 0 or epsilon_1 <= 0.0 or epsilon_1 >= 1.0:
            raise ValueError("Invalid parameters for threshold computation")
        
        log_term = math.log(float(recipient_count) / float(epsilon_1))
        return math.sqrt(2.0 * float(m) * log_term)

    @classmethod
    def accuse(
        cls,
        scores: Dict[str, float],
        threshold: float,
        epsilon_1: float = 1e-4,
        observed_length: int = 0,
        erasure_count: int = 0
    ) -> TardosAccusationResult:
        """
        Perform statistical accusation against threshold Z.
        
        Fail-Closed Rules:
        1. If one or more recipients score >= threshold Z:
           Status = ATTRIBUTED (or COLLUSION_DETECTED if multiple colluders cross threshold)
        2. If max score <= 0.0 or no signal is distinguishable from noise:
           Status = NO_SIGNAL
        3. If 0.0 < max score < threshold Z:
           Status = INSUFFICIENT_EVIDENCE (fail-closed: do NOT guess, abstain)
        """
        if not scores:
            return TardosAccusationResult(
                status=AccusationStatus.NO_SIGNAL,
                accused_recipients=[],
                scores={},
                threshold=threshold,
                max_score=0.0,
                margin=-threshold,
                mean_score=0.0,
                score_std_dev=0.0,
                false_accusation_bound=epsilon_1,
                observed_length=observed_length,
                erasure_count=erasure_count,
                details={"reason": "Empty score dictionary"}
            )

        score_values = list(scores.values())
        n = len(score_values)
        mean_score = sum(score_values) / float(n)
        variance = sum((x - mean_score) ** 2 for x in score_values) / float(n) if n > 1 else 0.0
        std_dev = math.sqrt(variance)

        sorted_recipients = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
        top_recipient, max_score = sorted_recipients[0]
        margin = max_score - threshold

        erasure_rate = (float(erasure_count) / float(observed_length)) if observed_length > 0 else 0.0

        # Identify all recipients who cross threshold Z
        crossing_recipients = [rec for rec, sc in sorted_recipients if sc >= threshold]

        if crossing_recipients:
            status = (
                AccusationStatus.COLLUSION_DETECTED 
                if len(crossing_recipients) > 1 
                else AccusationStatus.ATTRIBUTED
            )
            return TardosAccusationResult(
                status=status,
                accused_recipients=crossing_recipients,
                scores=scores,
                threshold=threshold,
                max_score=max_score,
                margin=margin,
                mean_score=mean_score,
                score_std_dev=std_dev,
                false_accusation_bound=epsilon_1,
                observed_length=observed_length,
                erasure_count=erasure_count,
                erasure_rate=erasure_rate,
                details={
                    "top_candidate": top_recipient,
                    "confidence_z_score": (max_score - mean_score) / (std_dev if std_dev > 1e-9 else 1.0),
                    "threshold_crossed": True,
                    "collusion_members_count": len(crossing_recipients)
                }
            )

        if max_score <= 0.0:
            return TardosAccusationResult(
                status=AccusationStatus.NO_SIGNAL,
                accused_recipients=[],
                scores=scores,
                threshold=threshold,
                max_score=max_score,
                margin=margin,
                mean_score=mean_score,
                score_std_dev=std_dev,
                false_accusation_bound=epsilon_1,
                observed_length=observed_length,
                erasure_count=erasure_count,
                erasure_rate=erasure_rate,
                details={
                    "reason": "Maximum recipient score is non-positive; signal absent or mismatched codebook",
                    "threshold_crossed": False
                }
            )

        # Fail-closed abstention: Positive score detected but does not reach threshold Z
        return TardosAccusationResult(
            status=AccusationStatus.INSUFFICIENT_EVIDENCE,
            accused_recipients=[],
            scores=scores,
            threshold=threshold,
            max_score=max_score,
            margin=margin,
            mean_score=mean_score,
            score_std_dev=std_dev,
            false_accusation_bound=epsilon_1,
            observed_length=observed_length,
            erasure_count=erasure_count,
            erasure_rate=erasure_rate,
            details={
                "reason": f"Weak signal detected (max_score {max_score:.2f} < threshold {threshold:.2f}). Abstaining to prevent false accusation.",
                "threshold_crossed": False,
                "top_candidate_unaccused": top_recipient
            }
        )
