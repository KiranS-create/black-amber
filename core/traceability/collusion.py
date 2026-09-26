import random
from typing import List, Dict, Any, Optional, Tuple

def verify_marking_assumption(
    colluder_codewords: List[List[int]],
    forged_codeword: List[int]
) -> Dict[str, Any]:
    """
    Verify whether a forged codeword adheres to the Marking Assumption.
    
    The Marking Assumption dictates:
    For any position j, if all colluders k in C possess the identical symbol
    X_{k,j} = b in {0, 1}, the colluders cannot detect the position as a mark
    and are forced to emit y_j = b (or leave it unchanged).
    
    Returns a dictionary detailing:
    - is_valid: True if no undetectable marks were altered
    - violation_count: Number of undetectable marks altered
    - violation_indices: Specific indices where violation occurred
    - detectable_positions: Positions where colluders differed
    - undetectable_positions: Positions where all colluders held the same symbol
    """
    if not colluder_codewords:
        raise ValueError("Colluder codewords list cannot be empty")
    
    m = len(forged_codeword)
    c = len(colluder_codewords)
    for idx, cw in enumerate(colluder_codewords):
        if len(cw) != m:
            raise ValueError(f"Colluder {idx} codeword length ({len(cw)}) != forged length ({m})")

    violation_indices: List[int] = []
    detectable_count = 0
    undetectable_count = 0

    for j in range(m):
        symbols_at_j = {colluder_codewords[k][j] for k in range(c)}
        if len(symbols_at_j) == 1:
            # Undetectable position: all colluders agree
            common_symbol = symbols_at_j.pop()
            undetectable_count += 1
            if forged_codeword[j] != -1 and forged_codeword[j] != common_symbol:
                violation_indices.append(j)
        else:
            detectable_count += 1

    return {
        "is_valid": len(violation_indices) == 0,
        "violation_count": len(violation_indices),
        "violation_indices": violation_indices,
        "detectable_positions": detectable_count,
        "undetectable_positions": undetectable_count,
        "detectable_ratio": float(detectable_count) / float(m) if m > 0 else 0.0
    }


def majority_collusion(colluder_codewords: List[List[int]]) -> List[int]:
    """
    Majority Voting Collusion Attack.
    At each index j, the colluders output the symbol held by the majority of the coalition.
    Ties broken in favor of symbol 1.
    """
    if not colluder_codewords:
        raise ValueError("Colluder codewords list cannot be empty")
    m = len(colluder_codewords[0])
    c = len(colluder_codewords)

    forged: List[int] = []
    for j in range(m):
        ones = sum(colluder_codewords[k][j] for k in range(c))
        zeros = c - ones
        forged.append(1 if ones >= zeros else 0)
    return forged


def interleaving_collusion(
    colluder_codewords: List[List[int]],
    seed: Optional[int] = None
) -> List[int]:
    """
    Interleaving / Cut-and-Paste Collusion Attack.
    For each index j, the coalition selects a random colluder k in C uniformly at random
    and emits that colluder's symbol X_{k,j}.
    """
    if not colluder_codewords:
        raise ValueError("Colluder codewords list cannot be empty")
    m = len(colluder_codewords[0])
    c = len(colluder_codewords)

    rng = random.Random(seed)
    forged: List[int] = []
    for j in range(m):
        chosen_k = rng.randrange(c)
        forged.append(colluder_codewords[chosen_k][j])
    return forged


def random_symbol_collusion(
    colluder_codewords: List[List[int]],
    seed: Optional[int] = None
) -> List[int]:
    """
    Coin-Flip / Random Symbol Selection Collusion Attack.
    - If all colluders agree on symbol b, output b (Marking Assumption).
    - If colluders disagree, flip an unbiased coin: output Bernoulli(0.5).
    """
    if not colluder_codewords:
        raise ValueError("Colluder codewords list cannot be empty")
    m = len(colluder_codewords[0])
    c = len(colluder_codewords)

    rng = random.Random(seed)
    forged: List[int] = []
    for j in range(m):
        symbols = {colluder_codewords[k][j] for k in range(c)}
        if len(symbols) == 1:
            forged.append(symbols.pop())
        else:
            forged.append(rng.choice([0, 1]))
    return forged


def all_zeros_collusion(colluder_codewords: List[List[int]]) -> List[int]:
    """
    Extreme Zero-Biased Collusion Attack.
    - If all colluders hold 1, forced to output 1 (Marking Assumption).
    - In all other positions (including disagreements), output 0.
    """
    if not colluder_codewords:
        raise ValueError("Colluder codewords list cannot be empty")
    m = len(colluder_codewords[0])
    c = len(colluder_codewords)

    forged: List[int] = []
    for j in range(m):
        symbols = {colluder_codewords[k][j] for k in range(c)}
        if symbols == {1}:
            forged.append(1)
        else:
            forged.append(0)
    return forged


def all_ones_collusion(colluder_codewords: List[List[int]]) -> List[int]:
    """
    Extreme One-Biased Collusion Attack.
    - If all colluders hold 0, forced to output 0 (Marking Assumption).
    - In all other positions (including disagreements), output 1.
    """
    if not colluder_codewords:
        raise ValueError("Colluder codewords list cannot be empty")
    m = len(colluder_codewords[0])
    c = len(colluder_codewords)

    forged: List[int] = []
    for j in range(m):
        symbols = {colluder_codewords[k][j] for k in range(c)}
        if symbols == {0}:
            forged.append(0)
        else:
            forged.append(1)
    return forged


def minimax_collusion(
    colluder_codewords: List[List[int]],
    biases: List[float]
) -> List[int]:
    """
    Minimax Worst-Case Strategy against Symmetric Tardos scoring.
    Where colluders disagree, they select y_j in {0, 1} that minimizes
    the maximum score contribution among the coalition members at that index:
        y_j = argmin_{y in {0, 1}} max_{k in C} U(y, X_{k,j}, p_j)
    """
    from core.traceability.tardos import SymmetricTardosEngine

    if not colluder_codewords:
        raise ValueError("Colluder codewords list cannot be empty")
    m = len(colluder_codewords[0])
    c = len(colluder_codewords)
    if len(biases) != m:
        raise ValueError(f"Biases length ({len(biases)}) != codeword length ({m})")

    forged: List[int] = []
    for j in range(m):
        symbols = {colluder_codewords[k][j] for k in range(c)}
        if len(symbols) == 1:
            forged.append(symbols.pop())
            continue

        p_j = biases[j]
        # Evaluate y = 0 vs y = 1
        max_score_if_0 = max(
            SymmetricTardosEngine.score_symbol(0, colluder_codewords[k][j], p_j)
            for k in range(c)
        )
        max_score_if_1 = max(
            SymmetricTardosEngine.score_symbol(1, colluder_codewords[k][j], p_j)
            for k in range(c)
        )

        if max_score_if_0 < max_score_if_1:
            forged.append(0)
        elif max_score_if_1 < max_score_if_0:
            forged.append(1)
        else:
            forged.append(0)

    return forged


def apply_noise_and_erasure(
    codeword: List[int],
    error_rate: float = 0.0,
    erasure_rate: float = 0.0,
    seed: Optional[int] = None
) -> List[int]:
    """
    Apply channel distortions to a codeword:
    - Erasures: with probability `erasure_rate`, symbol is replaced by -1 (erasure).
    - Bit errors: with probability `error_rate`, bit is flipped (0 <-> 1).
    """
    if error_rate < 0.0 or error_rate > 1.0:
        raise ValueError(f"Error rate must be in [0, 1], got {error_rate}")
    if erasure_rate < 0.0 or erasure_rate > 1.0:
        raise ValueError(f"Erasure rate must be in [0, 1], got {erasure_rate}")
    if error_rate + erasure_rate > 1.0:
        raise ValueError("Sum of error_rate and erasure_rate cannot exceed 1.0")

    rng = random.Random(seed)
    distorted: List[int] = []

    for bit in codeword:
        r = rng.random()
        if r < erasure_rate:
            distorted.append(-1)  # Erasure
        elif r < (erasure_rate + error_rate):
            # Bit flip
            distorted.append(1 - bit if bit in (0, 1) else bit)
        else:
            distorted.append(bit)

    return distorted
