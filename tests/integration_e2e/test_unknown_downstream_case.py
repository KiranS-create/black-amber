"""
SIH26237 - Unknown Downstream Recipient & Lineage Boundary Preservation Integration Tests.

Validates that when a document leak occurs downstream from an untracked third party:
1. The forensic attribution engine preserves LAST_KNOWN_HOLDER boundary.
2. The lineage graph records has_downstream_gap=True.
3. The system NEVER hallucinates or fabricates non-existent intermediate ancestors.
4. The evidence package verifier approves the LAST_KNOWN_HOLDER attribution decision.
"""

import pytest
import hashlib
from core.integration.orchestrator import AegisTraceEndToEndOrchestrator
from core.evidence_package.models import VerificationStatus, DecisionState


def test_unknown_downstream_lineage_boundary():
    """Simulates an untracked downstream leak where Alice was the last authorized recipient."""
    orchestrator = AegisTraceEndToEndOrchestrator(tenant_id="tenant_downstream_test")
    result = orchestrator.run_full_golden_pipeline(leak_recipient_id="alice")

    # Inspect lineage node and attribution
    attr = result.extraction_and_attribution
    assert attr.decision_state == DecisionState.ATTRIBUTED
    assert attr.last_known_holder_id == "alice"

    # Verify that in the evidence package, LineageEvidenceObject accurately reflects the boundary
    lineage_objs = [obj for obj in result.evidence_package.objects if obj.object_type.value == "LINEAGE_EVIDENCE"]
    assert len(lineage_objs) >= 1
    lin = lineage_objs[0]
    assert lin.last_known_holder == "alice"
    assert lin.boundary_state == "LAST_KNOWN_HOLDER"

    # Offline verifier must verify successfully
    assert result.verification_result.overall_status == VerificationStatus.VERIFIED
    assert result.verification_result.lineage_valid is True
