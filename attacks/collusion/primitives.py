import json
import random
from typing import List, Sequence, Optional, Dict, Any, Union
import numpy as np

from attacks.base import (
    BaseAttack,
    AttackFamily,
    ExecutionMode,
    ArtifactType,
    AttackOutput,
    DegradationMetrics,
)

class BaseCollusionPrimitive:
    """Base class for generic collusion primitives operating on symbol sequences."""
    PRIMITIVE_NAME: str = "base_collusion"

    @classmethod
    def validate_coalition(cls, coalition_symbols: Sequence[Sequence[Any]]) -> None:
        if not coalition_symbols:
            raise ValueError("Coalition must contain at least one codeword.")
        code_len = len(coalition_symbols[0])
        if code_len == 0:
            raise ValueError("Codewords must not be empty.")
        for i, cw in enumerate(coalition_symbols):
            if len(cw) != code_len:
                raise ValueError(f"Codeword at index {i} has length {len(cw)}, expected {code_len}.")


class AveragingCollusion(BaseCollusionPrimitive):
    """Averages symbols across colluders (rounded to nearest integer or float)."""
    PRIMITIVE_NAME = "averaging"

    @classmethod
    def collude(
        cls,
        coalition_symbols: Sequence[Sequence[Union[int, float]]],
        round_to_int: bool = True
    ) -> List[Union[int, float]]:
        cls.validate_coalition(coalition_symbols)
        arr = np.array(coalition_symbols, dtype=np.float64)
        avg = np.mean(arr, axis=0)
        if round_to_int:
            return [int(round(x)) for x in avg]
        return [float(x) for x in avg]


class InterleavingCollusion(BaseCollusionPrimitive):
    """
    Interleaves segments/blocks of symbols from colluders in round-robin or randomized order.
    """
    PRIMITIVE_NAME = "interleaving"

    @classmethod
    def collude(
        cls,
        coalition_symbols: Sequence[Sequence[Any]],
        block_size: int = 1,
        seed: Optional[int] = None
    ) -> List[Any]:
        cls.validate_coalition(coalition_symbols)
        num_colluders = len(coalition_symbols)
        code_len = len(coalition_symbols[0])
        result = []

        rng = random.Random(seed if seed is not None else 42)
        pos = 0
        colluder_idx = 0
        while pos < code_len:
            end = min(pos + block_size, code_len)
            c_idx = colluder_idx % num_colluders
            result.extend(coalition_symbols[c_idx][pos:end])
            pos = end
            colluder_idx += 1

        return result


class MajorityVotingCollusion(BaseCollusionPrimitive):
    """Selects the most common symbol among colluders at each position."""
    PRIMITIVE_NAME = "majority_voting"

    @classmethod
    def collude(
        cls,
        coalition_symbols: Sequence[Sequence[Any]],
        tie_breaker: str = "random",
        seed: Optional[int] = None
    ) -> List[Any]:
        cls.validate_coalition(coalition_symbols)
        num_colluders = len(coalition_symbols)
        code_len = len(coalition_symbols[0])
        rng = random.Random(seed if seed is not None else 42)
        result = []

        for j in range(code_len):
            col_symbols = [coalition_symbols[i][j] for i in range(num_colluders)]
            counts: Dict[Any, int] = {}
            for sym in col_symbols:
                counts[sym] = counts.get(sym, 0) + 1

            max_count = max(counts.values())
            candidates = [sym for sym, count in counts.items() if count == max_count]

            if len(candidates) == 1:
                result.append(candidates[0])
            else:
                if tie_breaker == "first":
                    result.append(candidates[0])
                else:
                    result.append(rng.choice(candidates))

        return result


class MinorityVotingCollusion(BaseCollusionPrimitive):
    """Adversarial stress-test: selects the least common symbol at each position."""
    PRIMITIVE_NAME = "minority_voting"

    @classmethod
    def collude(
        cls,
        coalition_symbols: Sequence[Sequence[Any]],
        seed: Optional[int] = None
    ) -> List[Any]:
        cls.validate_coalition(coalition_symbols)
        num_colluders = len(coalition_symbols)
        code_len = len(coalition_symbols[0])
        rng = random.Random(seed if seed is not None else 42)
        result = []

        for j in range(code_len):
            col_symbols = [coalition_symbols[i][j] for i in range(num_colluders)]
            counts: Dict[Any, int] = {}
            for sym in col_symbols:
                counts[sym] = counts.get(sym, 0) + 1

            min_count = min(counts.values())
            candidates = [sym for sym, count in counts.items() if count == min_count]
            result.append(rng.choice(candidates))

        return result


class RandomSymbolSelectionCollusion(BaseCollusionPrimitive):
    """Uniformly at random picks a symbol from among the colluders at each position."""
    PRIMITIVE_NAME = "random_selection"

    @classmethod
    def collude(
        cls,
        coalition_symbols: Sequence[Sequence[Any]],
        seed: Optional[int] = None
    ) -> List[Any]:
        cls.validate_coalition(coalition_symbols)
        num_colluders = len(coalition_symbols)
        code_len = len(coalition_symbols[0])
        rng = random.Random(seed if seed is not None else 42)
        result = []

        for j in range(code_len):
            chosen_c = rng.randint(0, num_colluders - 1)
            result.append(coalition_symbols[chosen_c][j])

        return result


class ErasureCollusion(BaseCollusionPrimitive):
    """
    If colluders disagree on a symbol, sets it to an erasure marker (-1).
    Under the Marking Assumption, matching symbols are preserved.
    """
    PRIMITIVE_NAME = "erasure"

    @classmethod
    def collude(
        cls,
        coalition_symbols: Sequence[Sequence[Any]],
        erasure_value: Any = -1
    ) -> List[Any]:
        cls.validate_coalition(coalition_symbols)
        num_colluders = len(coalition_symbols)
        code_len = len(coalition_symbols[0])
        result = []

        for j in range(code_len):
            first = coalition_symbols[0][j]
            all_match = all(coalition_symbols[i][j] == first for i in range(1, num_colluders))
            if all_match:
                result.append(first)
            else:
                result.append(erasure_value)

        return result


class SymbolSubstitutionCollusion(BaseCollusionPrimitive):
    """
    Flips or substitutes symbols at a specified error rate p, introducing random noise.
    """
    PRIMITIVE_NAME = "symbol_substitution"

    @classmethod
    def collude(
        cls,
        base_symbols: Sequence[Any],
        substitution_rate: float = 0.1,
        alphabet: Sequence[Any] = (0, 1),
        seed: Optional[int] = None
    ) -> List[Any]:
        rng = random.Random(seed if seed is not None else 42)
        result = list(base_symbols)
        for j in range(len(result)):
            if rng.random() < substitution_rate:
                # Pick alternative symbol from alphabet
                choices = [sym for sym in alphabet if sym != result[j]]
                if choices:
                    result[j] = rng.choice(choices)
                else:
                    result[j] = rng.choice(alphabet)
        return result


class CodewordMixingCollusion(BaseCollusionPrimitive):
    """
    Partial collusion: A primary subset colludes on a fraction of positions,
    while remaining symbols are fixed from a reference colluder.
    """
    PRIMITIVE_NAME = "codeword_mixing"

    @classmethod
    def collude(
        cls,
        coalition_symbols: Sequence[Sequence[Any]],
        mix_ratio: float = 0.5,
        primary_colluder_idx: int = 0,
        seed: Optional[int] = None
    ) -> List[Any]:
        cls.validate_coalition(coalition_symbols)
        code_len = len(coalition_symbols[0])
        rng = random.Random(seed if seed is not None else 42)

        # Baseline is primary colluder
        result = list(coalition_symbols[primary_colluder_idx])
        num_mix = int(code_len * mix_ratio)
        mix_indices = rng.sample(range(code_len), num_mix)

        num_colluders = len(coalition_symbols)
        for idx in mix_indices:
            other_c = rng.randint(0, num_colluders - 1)
            result[idx] = coalition_symbols[other_c][idx]

        return result


# BaseAttack Wrapper for generic pipeline integration
class GenericCollusionAttack(BaseAttack):
    """
    BaseAttack wrapper allowing collusion attacks to be orchestrated in the
    standardized SIH26237 attack pipeline.
    Expects input_artifact to be a JSON string of a dictionary:
    {
       "coalition": [[0, 1, ...], [1, 1, ...], ...],
       "strategy": "majority" | "averaging" | "random" | "erasure" | "interleaving"
    }
    """
    ATTACK_NAME = "generic_collusion"
    ATTACK_FAMILY = AttackFamily.COLLUSION
    TOOL = "GenericCollusionEngine"
    TOOL_VERSION = "1.0.0"

    def _execute_transform(
        self,
        artifact_bytes: bytes,
        parameters: Dict[str, Any],
        seed: Optional[int]
    ) -> AttackOutput:
        try:
            data = json.loads(artifact_bytes.decode('utf-8'))
        except Exception:
            raise ValueError("Collusion attack input must be valid JSON encoding a symbol coalition.")

        coalition = data.get("coalition", [])
        strategy = parameters.get("strategy") or data.get("strategy", "majority")

        if not coalition:
            raise ValueError("No coalition symbols provided in payload.")

        if strategy == "majority":
            forged = MajorityVotingCollusion.collude(coalition, seed=seed)
        elif strategy == "averaging":
            forged = AveragingCollusion.collude(coalition)
        elif strategy == "random":
            forged = RandomSymbolSelectionCollusion.collude(coalition, seed=seed)
        elif strategy == "erasure":
            forged = ErasureCollusion.collude(coalition)
        elif strategy == "interleaving":
            block_size = int(parameters.get("block_size", 1))
            forged = InterleavingCollusion.collude(coalition, block_size=block_size, seed=seed)
        elif strategy == "minority":
            forged = MinorityVotingCollusion.collude(coalition, seed=seed)
        elif strategy == "substitution":
            rate = float(parameters.get("substitution_rate", 0.1))
            forged = SymbolSubstitutionCollusion.collude(coalition[0], substitution_rate=rate, seed=seed)
        elif strategy == "mixing":
            ratio = float(parameters.get("mix_ratio", 0.5))
            forged = CodewordMixingCollusion.collude(coalition, mix_ratio=ratio, seed=seed)
        else:
            raise ValueError(f"Unknown collusion strategy: {strategy}")

        out_data = {
            "strategy": strategy,
            "coalition_size": len(coalition),
            "code_length": len(forged),
            "forged_symbols": forged
        }
        out_bytes = json.dumps(out_data).encode('utf-8')
        return AttackOutput(
            artifact_bytes=out_bytes,
            artifact_type=ArtifactType.FINGERPRINT_VECTOR,
            metadata={"strategy": strategy, "coalition_size": len(coalition)}
        )
