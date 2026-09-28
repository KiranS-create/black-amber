"""
SIH26237 - Controlled Viewer, Device Binding, Telemetry & Physical Forensics Tests
Validates the secure boundary enforcement, hardware attestation honesty,
EDR/CASB telemetry correlation (Level 4 -> Level 5), and physical capture analysis.
"""

import pytest
import os
import hashlib
from datetime import datetime, timezone

from core.crypto.signatures import MLDSA65
from core.lineage.models import (
    ExportFormat,
    DeviceAttestationStatus,
    PlatformType,
    ForensicAttributionLevel,
    ForensicBoundaryState,
)
from core.lineage.storage import LineageStorage
from core.lineage.service import LineageService
from core.lineage.viewer import ControlledViewer
from core.lineage.device import (
    LocalSoftwareDeviceProvider,
    SimulatedHardwareEnclaveProvider,
)
from core.lineage.telemetry import (
    MockTelemetryProvider,
    TelemetryEvent,
    TelemetryEventType,
)
from core.lineage.physical_forensics import (
    PhysicalForensicsAdapter,
    PhysicalDeviceProfile,
    PhysicalDeviceMatchStatus,
)


def test_controlled_viewer_encryption_and_session_rendering():
    storage = LineageStorage()
    service = LineageService(storage)
    viewer = ControlledViewer(service)

    doc_bytes = b"%PDF-1.7 Top Secret Aegis Document Buffer"
    root = service.create_document_root(doc_bytes)
    copy = service.issue_initial_copy(root.document_id, "rec_alice")

    # Encrypt master document at rest
    ciphertext = viewer.register_master_document(root.document_id, doc_bytes)
    assert ciphertext != doc_bytes
    assert len(ciphertext) > len(doc_bytes)

    # Open authenticated session
    session = viewer.open_session(copy.copy_id, identity_id="id_alice_corp")
    assert session.is_active is True

    # Render inside session
    render_result = viewer.render_view(session.session_id)
    assert render_result["status"] == "RENDERED_CONTROLLED"
    assert render_result["byte_count"] == len(doc_bytes)
    assert render_result["overlay"]["session_id"] == session.session_id
    assert render_result["overlay"]["session_fingerprint"].startswith("sf_")

    # Inactive session rejects rendering
    session.is_active = False
    with pytest.raises(PermissionError):
        viewer.render_view(session.session_id)


def test_controlled_viewer_export_boundary_refingerprinting():
    storage = LineageStorage()
    service = LineageService(storage)
    viewer = ControlledViewer(service)

    doc_bytes = b"Sensitive Financial Spreadsheet Data"
    root = service.create_document_root(doc_bytes)
    copy = service.issue_initial_copy(root.document_id, "rec_bob")
    viewer.register_master_document(root.document_id, doc_bytes)

    session = viewer.open_session(copy.copy_id, identity_id="id_bob")

    kp = MLDSA65.generate_keypair()
    exported_bytes, child_copy, exp_event, edge = viewer.controlled_export(
        session_id=session.session_id,
        export_format=ExportFormat.PDF,
        actor_principal_id="rec_bob",
        signer_keypair=(kp.private_key_bytes, kp.public_key_bytes),
        device_id="dev_bob_laptop"
    )

    # Exported bytes contains child fingerprint token
    assert child_copy.embedded_fingerprint_reference.encode('utf-8') in exported_bytes
    assert child_copy.lineage_depth == 1
    assert child_copy.parent_copy_id == copy.copy_id

    # Lineage verifies child copy is depth 1 derivative
    proof = service.get_lineage(child_copy.copy_id)
    assert proof.is_valid is True
    assert proof.highest_attribution_level == ForensicAttributionLevel.LEVEL_4_LINEAGE_IDENTIFIED


def test_device_binding_honesty_invariant():
    # Local software provider MUST NEVER fake attestation
    soft_provider = LocalSoftwareDeviceProvider()
    device = soft_provider.enroll_device()

    assert device.attestation_status == DeviceAttestationStatus.DEVICE_UNATTESTED
    assert device.platform_type == PlatformType.SOFTWARE_LOCAL

    challenge = b"random_challenge_nonce_123"
    status, sig = soft_provider.attest_device(device.device_id, challenge)
    assert status == DeviceAttestationStatus.DEVICE_UNATTESTED

    # Hardware enclave simulation explicitly documents its simulated nature
    enclave_provider = SimulatedHardwareEnclaveProvider(PlatformType.TPM)
    hw_device = enclave_provider.enroll_device()
    assert hw_device.attestation_status == DeviceAttestationStatus.DEVICE_ATTESTED
    assert hw_device.platform_type == PlatformType.TPM

    hw_status, hw_sig = enclave_provider.attest_device(hw_device.device_id, challenge)
    assert hw_status == DeviceAttestationStatus.DEVICE_ATTESTED


def test_telemetry_corroboration_bridge_level4_to_level5():
    telemetry = MockTelemetryProvider()

    # Case 1: No corroborating telemetry exists
    corroborated, conf, events = telemetry.corroborate_leak(
        candidate_principal_id="rec_eve",
        leak_approx_timestamp=datetime.now(timezone.utc).isoformat()
    )
    assert corroborated is False
    assert conf == 0.0
    assert len(events) == 0

    # Case 2: EDR captures screenshot and removable media write for candidate Eve
    telemetry.record_event(TelemetryEvent(
        event_id="edr_evt_101",
        event_type=TelemetryEventType.SCREENSHOT_TAKEN,
        principal_id="rec_eve",
        identity_id="id_eve_contractor",
        device_id="dev_laptop_eve",
        source_process="SnippingTool.exe",
        confidence=0.98
    ))
    telemetry.record_event(TelemetryEvent(
        event_id="edr_evt_102",
        event_type=TelemetryEventType.REMOVABLE_MEDIA_WRITE,
        principal_id="rec_eve",
        identity_id="id_eve_contractor",
        device_id="dev_laptop_eve",
        source_process="explorer.exe",
        target_destination="E:\\leaked_file.pdf",
        confidence=0.95
    ))

    corroborated, conf, events = telemetry.corroborate_leak(
        candidate_principal_id="rec_eve",
        leak_approx_timestamp=datetime.now(timezone.utc).isoformat()
    )
    assert corroborated is True
    assert conf >= 0.95
    assert len(events) == 2


def test_physical_forensics_device_matching():
    adapter = PhysicalForensicsAdapter()

    # Case 1: No enrolled profiles
    sample_capture = b"CAMERA_IMAGE_CAPTURE_PIXELS_XYZ"
    res1 = adapter.analyze_capture(sample_capture)
    assert res1.status == PhysicalDeviceMatchStatus.NO_REFERENCE

    # Case 2: Enroll known camera profile
    target_sensor_hash = "sensor_canon_eos_r5_9812"
    adapter.register_profile(PhysicalDeviceProfile(
        device_id="dev_canon_camera_01",
        device_name="Canon EOS R5 Serial #9812",
        device_type="CAMERA",
        sensor_fingerprint_hash=target_sensor_hash
    ))

    # Exact sensor match
    res2 = adapter.analyze_capture(sample_capture, extracted_sensor_hash=target_sensor_hash)
    assert res2.status == PhysicalDeviceMatchStatus.DEVICE_MATCH
    assert res2.matched_device_id == "dev_canon_camera_01"
    assert res2.confidence >= 0.90

    # Unknown device sensor
    res3 = adapter.analyze_capture(sample_capture, extracted_sensor_hash="sensor_unknown_iphone_15")
    assert res3.status == PhysicalDeviceMatchStatus.UNKNOWN_DEVICE
    assert res3.confidence == 0.0


def test_controlled_viewer_passive_session_expiry_rejection():
    """
    Asserts SEC-LIN-003: ControlledViewer actively enforces expires_at timestamp
    without relying on external cron or manual is_active=False toggling.
    """
    storage = LineageStorage()
    service = LineageService(storage)
    viewer = ControlledViewer(service)

    doc_bytes = b"Time-sensitive Security Audit Report"
    root = service.create_document_root(doc_bytes)
    copy = service.issue_initial_copy(root.document_id, "rec_analyst")
    viewer.register_master_document(root.document_id, doc_bytes)

    # Open session with negative duration (already expired)
    expired_session = viewer.open_session(copy.copy_id, identity_id="id_analyst", expires_in_seconds=-60)
    assert expired_session.is_active is True  # newly created, but expires_at is in the past

    # Calling render_view must detect expiry, set is_active=False, and raise PermissionError
    with pytest.raises(PermissionError, match="has expired at"):
        viewer.render_view(expired_session.session_id)

    # Calling controlled_export must also reject
    with pytest.raises(PermissionError):
        viewer.controlled_export(expired_session.session_id, ExportFormat.PDF)

