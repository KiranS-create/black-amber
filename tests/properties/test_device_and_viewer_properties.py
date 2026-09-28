"""
tests/properties/test_device_and_viewer_properties.py

Property-based testing and state fuzzing for Controlled Viewer and Device Attestation:
- Session expiration fail-closed enforcement
- In-memory controlled rendering and dynamic session watermark overlay
- Hardware attestation honesty invariants (never fakes TPM/Enclave in software)
- Controlled export lineage depth monotonicity and child fingerprint binding
"""

import copy
import hashlib
from datetime import datetime, timezone, timedelta
import pytest
from core.lineage.models import (
    PlatformType,
    DeviceAttestationStatus,
    ExportFormat,
)
from core.lineage.storage import LineageStorage
from core.lineage.service import LineageService
from core.lineage.viewer import ControlledViewer
from core.lineage.device import (
    LocalSoftwareDeviceProvider,
    SimulatedHardwareEnclaveProvider,
)
from core.testing.property_engine import PropertyRunner, DeterministicGenerator
from core.security.invariants import assert_invariant


def test_property_viewer_session_expiration_fail_closed(runner: PropertyRunner):
    """
    Property: An AccessSession that has passed its expires_at boundary strictly
    fails closed upon any attempt to render_view or controlled_export.
    """
    def prop(g: DeterministicGenerator):
        storage = LineageStorage()
        service = LineageService(storage)
        viewer = ControlledViewer(service)

        doc_id = g.generate_document_id()
        doc_bytes = b"%PDF-1.4\n" + g.bytes_data(256)
        service.create_document_root(doc_bytes, document_id=doc_id)
        viewer.register_master_document(doc_id, doc_bytes)

        copy_inst = service.issue_initial_copy(doc_id, "rec-alice")

        is_expired = g.boolean(0.5)

        if is_expired:
            # Expired session (-60 seconds)
            session = viewer.open_session(copy_inst.copy_id, identity_id="rec-alice", expires_in_seconds=-60)
            
            # Attempt to render_view must raise PermissionError
            with pytest.raises(PermissionError, match="expired"):
                viewer.render_view(session.session_id)

            # Attempt to controlled_export must raise PermissionError
            with pytest.raises(PermissionError, match="expired"):
                viewer.controlled_export(session.session_id, ExportFormat.PDF, actor_principal_id="rec-alice")

        else:
            # Active session (+3600 seconds)
            session = viewer.open_session(copy_inst.copy_id, identity_id="rec-alice", expires_in_seconds=3600)
            
            # Rendering succeeds
            render_res = viewer.render_view(session.session_id)
            assert render_res["status"] == "RENDERED_CONTROLLED"
            assert render_res["overlay"]["session_id"] == session.session_id
            assert render_res["overlay"]["session_fingerprint"].startswith("sf_")

    res = runner.run_property("viewer_session_expiration", prop, iterations=100)
    assert res.passed, res.error_message


def test_property_device_provider_attestation_honesty_invariant(runner: PropertyRunner):
    """
    Property: LocalSoftwareDeviceProvider strictly reports DEVICE_UNATTESTED
    and SOFTWARE_LOCAL, never falsely asserting hardware TPM / Enclave backing.
    """
    software_provider = LocalSoftwareDeviceProvider()
    hardware_provider = SimulatedHardwareEnclaveProvider(PlatformType.TPM)

    def prop(g: DeterministicGenerator):
        # 1. Enroll software device
        dev_soft = software_provider.enroll_device()
        assert dev_soft.attestation_status == DeviceAttestationStatus.DEVICE_UNATTESTED
        assert dev_soft.platform_type == PlatformType.SOFTWARE_LOCAL

        challenge = g.bytes_data(32)
        status_soft, sig_soft = software_provider.attest_device(dev_soft.device_id, challenge)
        assert status_soft == DeviceAttestationStatus.DEVICE_UNATTESTED
        assert len(sig_soft) == 3293  # Valid ML-DSA-65 signature

        # 2. Hardware simulation provider
        dev_hw = hardware_provider.enroll_device()
        assert dev_hw.attestation_status == DeviceAttestationStatus.DEVICE_ATTESTED
        assert dev_hw.platform_type == PlatformType.TPM

        status_hw, sig_hw = hardware_provider.attest_device(dev_hw.device_id, challenge)
        assert status_hw == DeviceAttestationStatus.DEVICE_ATTESTED

    res = runner.run_property("device_attestation_honesty", prop, iterations=100)
    assert res.passed, res.error_message


def test_property_controlled_export_lineage_monotonicity(runner: PropertyRunner):
    """
    Property: Every sequential controlled_export operation increments lineage_depth
    monotonically by 1 and embeds a unique child copy fingerprint.
    """
    def prop(g: DeterministicGenerator):
        storage = LineageStorage()
        service = LineageService(storage)
        viewer = ControlledViewer(service)

        doc_id = g.generate_document_id()
        doc_bytes = b"%PDF-1.4\n" + g.bytes_data(512)
        service.create_document_root(doc_bytes, document_id=doc_id)
        viewer.register_master_document(doc_id, doc_bytes)

        num_exports = g.integer(2, 6)
        curr_copy = service.issue_initial_copy(doc_id, "rec-root-user")
        assert curr_copy.lineage_depth == 0

        for depth in range(1, num_exports + 1):
            session = viewer.open_session(curr_copy.copy_id, identity_id=f"user_{depth}")
            fmt = g.choice([ExportFormat.PDF, ExportFormat.IMAGE, ExportFormat.PRINT, ExportFormat.SCREEN])

            exported_bytes, child_copy, exp_event, edge = viewer.controlled_export(
                session_id=session.session_id,
                export_format=fmt,
                actor_principal_id=f"user_{depth}",
            )

            # Invariant 1: Lineage depth increases monotonically
            assert child_copy.lineage_depth == depth
            assert child_copy.parent_copy_id == curr_copy.copy_id

            # Invariant 2: Export receipt binds child copy and parent copy
            assert exp_event.parent_copy_id == curr_copy.copy_id
            assert exp_event.child_copy_id == child_copy.copy_id
            assert exp_event.source_session_id == session.session_id

            # Invariant 3: Exported bytes contain embedded child fingerprint
            assert child_copy.embedded_fingerprint_reference.encode('utf-8') in exported_bytes

            curr_copy = child_copy

    res = runner.run_property("controlled_export_lineage_monotonicity", prop, iterations=50)
    assert res.passed, res.error_message
