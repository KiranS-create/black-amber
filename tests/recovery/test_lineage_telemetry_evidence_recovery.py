"""
Unit & Integration Tests for AegisTrace Lineage, Telemetry, and Evidence Package Recovery.
"""

from datetime import datetime, timezone
import pytest
from core.lineage.models import DocumentRoot, CopyInstance, AccessSession
from core.lineage.storage import LineageStorage
from core.telemetry.event import ForensicEvent
from core.telemetry.models import TelemetrySource, CanonicalEventType
from core.attribution.evidence import EvidenceBundle, EvidenceObservation, EvidenceFamily, TargetBinding
from core.recovery.models import RecoveryState
from core.recovery.lineage_recovery import LineageRecoveryEngine
from core.recovery.telemetry_recovery import TelemetryRecoveryEngine
from core.recovery.evidence_recovery import EvidencePackageRecoveryEngine


def test_lineage_recovery_intact_tree():
    root = DocumentRoot(document_id="doc_root_1", canonical_hash="a"*64, byte_size=1024)
    c0 = CopyInstance(copy_id="cpy_0", parent_copy_id=None, document_id="doc_root_1", lineage_depth=0)
    c1 = CopyInstance(copy_id="cpy_1", parent_copy_id="cpy_0", document_id="doc_root_1", lineage_depth=1)
    c2 = CopyInstance(copy_id="cpy_2", parent_copy_id="cpy_1", document_id="doc_root_1", lineage_depth=2)

    res, storage = LineageRecoveryEngine.recover_lineage(
        roots=[root],
        copies=[c0, c1, c2],
        expected_tenant_id="default_tenant"
    )
    assert res.state == RecoveryState.VALID_RECOVERY
    assert res.copies_recovered == 3
    assert res.missing_parents_count == 0
    assert storage.get_document_root("doc_root_1") is not None
    assert storage.get_copy("cpy_2") is not None


def test_lineage_recovery_detects_cycle():
    root = DocumentRoot(document_id="doc_root_1", canonical_hash="a"*64, byte_size=1024)
    # Cycle: cpy_A -> cpy_B -> cpy_A
    cA = CopyInstance(copy_id="cpy_A", parent_copy_id="cpy_B", document_id="doc_root_1")
    cB = CopyInstance(copy_id="cpy_B", parent_copy_id="cpy_A", document_id="doc_root_1")

    res, _ = LineageRecoveryEngine.recover_lineage(
        roots=[root],
        copies=[cA, cB],
        expected_tenant_id="default_tenant"
    )
    assert res.state == RecoveryState.CORRUPTED_RECOVERY
    assert any("CYCLE_DETECTED" in e for e in res.errors)


def test_lineage_recovery_preserves_missing_parent_boundary():
    root = DocumentRoot(document_id="doc_root_1", canonical_hash="a"*64, byte_size=1024)
    # cpy_downstream references unknown parent cpy_unseen
    c = CopyInstance(copy_id="cpy_downstream", parent_copy_id="cpy_unseen", document_id="doc_root_1")

    res, storage = LineageRecoveryEngine.recover_lineage(
        roots=[root],
        copies=[c],
        expected_tenant_id="default_tenant"
    )
    # Missing parent is preserved as legitimate forensic boundary (PARTIAL_RECOVERY), not failure
    assert res.state == RecoveryState.PARTIAL_RECOVERY
    assert res.missing_parents_count == 1
    assert any("MISSING_PARENT" in w for w in res.warnings)


def test_lineage_cross_tenant_parent_rejected():
    root = DocumentRoot(document_id="doc_root_1", canonical_hash="a"*64, byte_size=1024)
    cP = CopyInstance(copy_id="cpy_parent", parent_copy_id=None, document_id="doc_root_1", metadata={"tenant_id": "tenant_1"})
    cC = CopyInstance(copy_id="cpy_child", parent_copy_id="cpy_parent", document_id="doc_root_1", metadata={"tenant_id": "tenant_2"})

    # Recovering into tenant_1 must flag cross-tenant conflict
    res, _ = LineageRecoveryEngine.recover_lineage(
        roots=[root],
        copies=[cP, cC],
        expected_tenant_id="tenant_1"
    )
    assert res.state == RecoveryState.CORRUPTED_RECOVERY
    assert any("CROSS_TENANT" in e for e in res.errors)


def test_telemetry_recovery_and_deduplication():
    now = datetime.now(timezone.utc)
    ev1 = ForensicEvent(
        event_id="tel_001",
        timestamp=now,
        event_type="DOCUMENT_OPENED",
        source_system=TelemetrySource.EDR,
        subject_id="alice",
        artifact_hash="art_1"
    )
    ev2 = ForensicEvent(
        event_id="tel_002",
        timestamp=now,
        event_type="DOCUMENT_PRINTED",
        source_system=TelemetrySource.PRINT,
        subject_id="alice",
        artifact_hash="art_1"
    )

    # Ingest ev1 and ev2
    res1, recovered = TelemetryRecoveryEngine.recover_telemetry([ev1, ev2])
    assert res1.state == RecoveryState.VALID_RECOVERY
    assert res1.events_recovered == 2
    assert res1.duplicates_detected == 0

    # Ingest again with ev1 duplicate
    existing_fps = {ev.compute_event_fingerprint() for ev in recovered}
    ev3 = ForensicEvent(
        event_id="tel_003",
        timestamp=now,
        event_type="DOCUMENT_SAVED",
        source_system=TelemetrySource.DLP,
        subject_id="bob",
        artifact_hash="art_2"
    )
    res2, recovered2 = TelemetryRecoveryEngine.recover_telemetry(
        [ev1, ev3],
        existing_event_fingerprints=existing_fps
    )
    assert res2.state == RecoveryState.PARTIAL_RECOVERY
    assert res2.events_recovered == 1  # only ev3 recovered
    assert res2.duplicates_detected == 1  # ev1 detected as duplicate


def test_evidence_package_recovery_and_target_binding():
    bundle = EvidenceBundle(
        bundle_id="bnd_101",
        target_binding=TargetBinding(document_id="doc_xyz", release_id="rel_xyz"),
        observations=[
            EvidenceObservation(source_id="obs_1", family=EvidenceFamily.WATERMARK_PAYLOAD),
            EvidenceObservation(source_id="obs_2", family=EvidenceFamily.AUDIT_LEDGER),
        ]
    )

    # 1. Matching target binding recovers cleanly
    res, rec_bundles = EvidencePackageRecoveryEngine.recover_evidence_bundles(
        candidate_bundles=[bundle],
        expected_document_id="doc_xyz",
        expected_release_id="rel_xyz"
    )
    assert res.state == RecoveryState.VALID_RECOVERY
    assert res.bundles_recovered == 1
    assert res.observations_verified == 2

    # 2. Mismatched target binding fails closed
    res_mismatch, _ = EvidencePackageRecoveryEngine.recover_evidence_bundles(
        candidate_bundles=[bundle],
        expected_document_id="doc_DIFFERENT"
    )
    assert res_mismatch.state == RecoveryState.CORRUPTED_RECOVERY
    assert res_mismatch.target_binding_mismatches == 1
