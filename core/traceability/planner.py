import math
from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

class PlannerStatus(str, Enum):
    FEASIBLE = "FEASIBLE"
    CAPACITY_INSUFFICIENT = "CAPACITY_INSUFFICIENT"
    INVALID_PARAMETERS = "INVALID_PARAMETERS"

class CapacityPlanRequest(BaseModel):
    recipient_count: int = Field(gt=0, description="Total population of authorized recipients (N)")
    coalition_size: int = Field(gt=0, description="Target maximum collusion coalition size (c)")
    false_accusation_epsilon: float = Field(gt=0.0, lt=1.0, default=1e-4, description="Target false-positive accusation probability (epsilon_1)")
    available_carrier_budget: Optional[int] = Field(default=None, description="Available carrier symbols (m_available)")
    kappa_factor: float = Field(default=20.0, description="Multiplier kappa for code length: 100.0 (Tardos 2003) or 20.0 (Blayer-Tassa / Skoric 2008)")
    protocol_version: str = "SIH26237-v1.0"

class CapacityPlanResult(BaseModel):
    status: PlannerStatus
    is_feasible: bool
    recipient_count: int
    coalition_size: int
    false_accusation_epsilon: float
    required_code_length: int
    available_code_length: Optional[int] = None
    accusation_threshold: float
    cutoff_parameter_t: float
    code_length_parameter_kappa: float
    assumptions: List[str]
    reason: Optional[str] = None
    recommendations: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class TardosCapacityPlanner:
    """
    Capacity & Security Parameter Planner for Tardos Fingerprinting Codes.
    
    Mathematical Foundations:
    1. Code Length (Blayer-Tassa / Skoric et al. 2008):
       m >= ceil( kappa * c^2 * ln(N / epsilon_1) )
       - Original Tardos (2003): kappa = 100
       - Blayer & Tassa (2008) / Symmetric Skoric (2008): kappa in [15, 25], default 20.0
       - Information-theoretic asymptotic lower bound: kappa_min = pi^2 / 2 ~= 4.93
    2. Accusation Threshold Z:
       Z = sqrt( 2 * m * ln(N / epsilon_1) )
       guarantees false accusation probability P(S_innocent > Z) <= epsilon_1 via Chernoff/Bernstein bound.
    3. Cutoff parameter t:
       t = 1 / (300 * c) for distribution bounding.
    """

    @classmethod
    def plan(cls, request: CapacityPlanRequest) -> CapacityPlanResult:
        N = request.recipient_count
        c = request.coalition_size
        eps = request.false_accusation_epsilon
        kappa = request.kappa_factor
        m_avail = request.available_carrier_budget

        if N <= 0 or c <= 0 or eps <= 0.0 or eps >= 1.0:
            return CapacityPlanResult(
                status=PlannerStatus.INVALID_PARAMETERS,
                is_feasible=False,
                recipient_count=N,
                coalition_size=c,
                false_accusation_epsilon=eps,
                required_code_length=0,
                available_code_length=m_avail,
                accusation_threshold=0.0,
                cutoff_parameter_t=0.0,
                code_length_parameter_kappa=kappa,
                assumptions=["Invalid input domain"],
                reason="Parameters must satisfy N > 0, c > 0, 0 < epsilon < 1",
                recommendations=["Correct input bounds"]
            )

        # 1. Compute required code length m
        log_term = math.log(N / eps)
        m_req = int(math.ceil(kappa * (c ** 2) * log_term))

        # 2. Cutoff parameter t
        t_cutoff = 1.0 / (300.0 * c)

        # 3. Threshold Z
        # For symmetric Tardos, standard threshold based on Chernoff bound:
        # Z = sqrt(2 * m * ln(N / epsilon))
        threshold = math.sqrt(2.0 * m_req * log_term)

        assumptions = [
            f"Marking Assumption: Colluders can only select symbols present in their assigned copies",
            f"Code construction: Symmetric Tardos with continuous arcsin bias distribution",
            f"Symmetric scoring: E[S_innocent] = 0 for any collusion strategy",
            f"Chernoff-bound false accusation ceiling <= {eps:.1e}",
            f"Maximum modeled coalition size c = {c}"
        ]

        # 4. Capacity feasibility validation
        if m_avail is not None and m_avail < m_req:
            recs = [
                f"Increase carrier capacity from {m_avail} to at least {m_req} symbols",
                f"Reduce maximum supported coalition size (e.g. c={max(1, int(math.sqrt(m_avail / (kappa * log_term))))})",
                f"Relax false accusation tolerance epsilon (current: {eps:.1e})"
            ]
            return CapacityPlanResult(
                status=PlannerStatus.CAPACITY_INSUFFICIENT,
                is_feasible=False,
                recipient_count=N,
                coalition_size=c,
                false_accusation_epsilon=eps,
                required_code_length=m_req,
                available_code_length=m_avail,
                accusation_threshold=threshold,
                cutoff_parameter_t=t_cutoff,
                code_length_parameter_kappa=kappa,
                assumptions=assumptions,
                reason=f"Carrier budget ({m_avail} symbols) is insufficient for target security (requires {m_req} symbols)",
                recommendations=recs,
                metadata={
                    "deficit_symbols": m_req - m_avail,
                    "deficit_percentage": round(((m_req - m_avail) / m_req) * 100, 2)
                }
            )

        # Success: Capacity is feasible
        effective_m = m_avail if m_avail is not None else m_req
        effective_threshold = math.sqrt(2.0 * effective_m * log_term)

        return CapacityPlanResult(
            status=PlannerStatus.FEASIBLE,
            is_feasible=True,
            recipient_count=N,
            coalition_size=c,
            false_accusation_epsilon=eps,
            required_code_length=m_req,
            available_code_length=effective_m,
            accusation_threshold=effective_threshold,
            cutoff_parameter_t=t_cutoff,
            code_length_parameter_kappa=kappa,
            assumptions=assumptions,
            reason=None,
            recommendations=["Configuration satisfies theoretical security bounds; proceed with release generation."],
            metadata={
                "margin_symbols": (effective_m - m_req) if m_avail is not None else 0
            }
        )
