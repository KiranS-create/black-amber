import os
import json
import time
from typing import List, Dict, Any, Optional, Callable, Tuple
import numpy as np
from pydantic import BaseModel, Field

from attacks.base import BaseAttack, AttackResult
from attacks.measurement.metrics import EvaluationOutcome, TraceabilityMetricsEvaluator

class BenchmarkTiming(BaseModel):
    attack_name: str
    samples: int
    mean_ms: float
    median_ms: float
    p95_ms: float
    input_size_bytes: int
    output_size_bytes: int

class ParameterSweepEntry(BaseModel):
    parameter_value: Any
    attack_result: AttackResult
    survival_rate: Optional[float] = None
    attribution_state: Optional[str] = None
    outcome: Optional[EvaluationOutcome] = None

class RobustnessEvaluator:
    """
    Orchestrates parameter sweeps, performance benchmarks, and structured matrix evaluations.
    Saves machine-readable evidence artifacts to artifacts/attacks/.
    """
    def __init__(self, artifacts_dir: str = "artifacts/attacks"):
        self.artifacts_dir = os.path.abspath(artifacts_dir)
        os.makedirs(self.artifacts_dir, exist_ok=True)

    def run_parameter_sweep(
        self,
        attack: BaseAttack,
        input_bytes: bytes,
        param_name: str,
        param_values: List[Any],
        fixed_params: Optional[Dict[str, Any]] = None,
        seed: Optional[int] = 42,
        eval_fn: Optional[Callable[[bytes], Tuple[str, bool, float]]] = None
    ) -> List[ParameterSweepEntry]:
        """
        Execute an attack across a configured range of parameter values.
        Optionally evaluates attribution survival via eval_fn(attacked_bytes) -> (state, is_culprit, survival_rate).
        """
        entries: List[ParameterSweepEntry] = []
        fixed = fixed_params or {}

        for val in param_values:
            current_params = dict(fixed)
            current_params[param_name] = val

            res = attack.apply(input_bytes, parameters=current_params, seed=seed)

            survival = None
            attr_state = None
            outcome = None

            if eval_fn and res.success:
                try:
                    # eval_fn returns (state, is_culprit, survival_rate)
                    attr_state, is_culprit, survival = eval_fn(res.output_hash.encode('utf-8'))
                    outcome, _ = TraceabilityMetricsEvaluator.classify_outcome(
                        survival_rate=survival,
                        attribution_status=attr_state,
                        attributed_to_culprit=is_culprit
                    )
                except Exception:
                    outcome = EvaluationOutcome.FAIL

            entry = ParameterSweepEntry(
                parameter_value=val,
                attack_result=res,
                survival_rate=survival,
                attribution_state=attr_state,
                outcome=outcome
            )
            entries.append(entry)

            # Persist individual result JSON
            self.save_result(res)

        return entries

    def benchmark_attack(
        self,
        attack: BaseAttack,
        input_bytes: bytes,
        parameters: Optional[Dict[str, Any]] = None,
        iterations: int = 15,
        seed: int = 42
    ) -> BenchmarkTiming:
        """
        Measure actual execution timings for an attack over multiple iterations.
        Computes mean, median, P95, input size, and output size.
        """
        durations = []
        out_size = 0
        params = parameters or {}

        # Warmup
        _ = attack.apply(input_bytes, parameters=params, seed=seed)

        for i in range(iterations):
            start = time.perf_counter()
            res = attack.apply(input_bytes, parameters=params, seed=seed + i)
            elapsed_ms = (time.perf_counter() - start) * 1000.0
            durations.append(elapsed_ms)
            out_size = len(res.output_hash)

        durations_arr = np.array(durations)
        return BenchmarkTiming(
            attack_name=attack.ATTACK_NAME,
            samples=iterations,
            mean_ms=round(float(np.mean(durations_arr)), 3),
            median_ms=round(float(np.median(durations_arr)), 3),
            p95_ms=round(float(np.percentile(durations_arr, 95)), 3),
            input_size_bytes=len(input_bytes),
            output_size_bytes=out_size
        )

    def save_result(self, result: AttackResult) -> str:
        """Save machine-readable AttackResult to artifacts/attacks/<attack_id>.json."""
        filepath = os.path.join(self.artifacts_dir, f"{result.attack_id}.json")
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(result.model_dump(), f, indent=2)
        return filepath
