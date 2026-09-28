"""
AegisTrace Red-Team & Independent Reproduction Subsystem.

Provides automated tools for blind forensic evaluation, composed adversary attack simulation,
privileged operator resistance verification, and fail-closed code auditing.
"""

from core.red_team.blind_evaluator import (
    BlindForensicEvaluator,
    BlindEvaluationResult,
)
from core.red_team.composed_attacks import (
    ComposedAttackSimulator,
    ComposedAttackResult,
    ComposedAttackVerdict,
)
from core.red_team.privileged_operator import (
    PrivilegedOperatorAttackSimulator,
    PrivilegedAttackResult,
)
from core.red_team.audit_fail_closed import (
    FailClosedAuditor,
    FailClosedAuditReport,
    CodeAuditFinding,
)

__all__ = [
    "BlindForensicEvaluator",
    "BlindEvaluationResult",
    "ComposedAttackSimulator",
    "ComposedAttackResult",
    "ComposedAttackVerdict",
    "PrivilegedOperatorAttackSimulator",
    "PrivilegedAttackResult",
    "FailClosedAuditor",
    "FailClosedAuditReport",
    "CodeAuditFinding",
]
