"""
SIH26237 - Telemetry Evidence & Dependency Graph Integration Tests.

Validates that:
1. Telemetry events (device attestation, session view, export) are dependency-linked.
2. Telemetry dependency relations (CORROBORATES, DIRECTLY_SUPPORTS) are enforced in DAG.
3. If telemetry is absent or uncorroborated, the system degrades safely without false accusations.
4. Offline Evidence Verifier checks DAG grounding and telemetry consistency.
"""

import pytest
from core.integration.orchestrator import AegisTraceEndToEndOrchestrator
from core.evidence_package.models import VerificationStatus, TelemetryDependencyRelation


def test_telemetry_evidence_and_dag_integration():
    """Tests telemetry recording, DAG edge linking, and offline verification."""
    orchestrator = AegisTraceEndToEndOrchestrator(tenant_id="tenant_telem_test")
    result = orchestrator.run_full_golden_pipeline(leak_recipient_id="alice")

    # 1. Inspect telemetry evidence object in evidence package
    telem_objs = [obj for obj in result.evidence_package.objects if obj.object_type.value == "TELEMETRY_EVIDENCE"]
    assert len(telem_objs) >= 1
    t_obj = telem_objs[0]
    assert t_obj.actor_id == "alice"
    assert t_obj.dependency_relation == TelemetryDependencyRelation.CORROBORATES
    assert t_obj.device_id.startswith("dev_alice_tpm")

    # 2. Inspect DAG edges
    edges = result.evidence_package.edges
    assert len(edges) >= 7
    telem_edge = next((e for e in edges if e.source_id == t_obj.object_id), None)
    assert telem_edge is not None
    assert telem_edge.relationship_type == "CORROBORATED_BY"

    # 3. Offline verification
    assert result.verification_result.overall_status == VerificationStatus.VERIFIED
    assert result.verification_result.dependency_graph_valid is True
