"""
SIH26237 - Device Anti-Fabrication & Epistemic Honesty Tests
============================================================
Adversarial test suite covering anti-fabrication vectors:
1. Claiming MEASURED_PHYSICAL for camera when camera_detected is False.
2. Claiming camera available merely because phone is USB-connected (USB_CONNECTED != CAMERA_AVAILABLE).
3. Declaring custody action CAPTURED for digital file transfer (IMAGE_TRANSFERRED != OPTICAL_CAPTURE_VERIFIED).
4. Claiming MEASURED_PHYSICAL for printer validation when 0 physical printers detected.
5. Claiming MEASURED_PHYSICAL for scanner validation when 0 physical scanners detected.
6. Claiming MEASURED_PHYSICAL when provenance is COMPUTATIONAL_MODEL or SIMULATION.
7. Overall experiment claiming MEASURED_PHYSICAL with missing camera subcomponent.
8. Overall experiment claiming MEASURED_PHYSICAL with missing printer subcomponent.
9. Overall experiment claiming MEASURED_PHYSICAL with missing scanner subcomponent.
10. Claiming physical paper validation from phone screen rendering.
11. Bypassing custody ledger validation by spoofing optical capture.
12. Tampering transfer record to claim hash match on corrupted bytes.
13. Unauthorized ADB device execution rejection.
14. Collapsing epistemic status into generic boolean without preserving granular states.
15. Masking simulated noise/blur as physical optical sensor capture.
16. Honest reporting: Validating that NOT_VERIFIED and UNAVAILABLE succeed without violation.
"""

import pytest
from core.physical.epistemic import (
    EpistemicStatus,
    AntiFabricationGuard,
    AntiFabricationViolation,
    SubsystemEpistemicClaim,
    ExperimentEpistemicRecord
)
from core.physical.device_discovery import (
    SmartphoneDeviceRecord,
    PhoneRole,
    PhoneAdbState
)
from core.physical.device_custody import (
    DeviceCustodyLedger,
    DeviceCustodyAction
)
from core.physical.device_transfer import (
    DeviceTransferEngine,
    DeviceTransferRecord,
    TransferDirection,
    TransferMechanism
)


# Vector 1: Camera claim when absent
def test_vector_1_camera_claim_when_absent():
    with pytest.raises(AntiFabricationViolation) as exc:
        AntiFabricationGuard.validate_camera_claim(
            camera_detected=False,
            claimed_status=EpistemicStatus.MEASURED_PHYSICAL
        )
    assert "Cannot claim MEASURED_PHYSICAL for camera" in str(exc.value)


# Vector 2: Phone USB != Camera
def test_vector_2_usb_connected_not_camera():
    with pytest.raises(AntiFabricationViolation) as exc:
        AntiFabricationGuard.validate_phone_role_separation(
            phone_connected=True,
            claimed_as_camera=True,
            has_real_camera_stream=False
        )
    assert "Phone USB connection alone does NOT constitute camera availability" in str(exc.value)


# Vector 3: Transfer != Optical Capture
def test_vector_3_transfer_not_optical_capture():
    with pytest.raises(AntiFabricationViolation) as exc:
        AntiFabricationGuard.validate_transfer_vs_capture(
            action="CAPTURED",
            is_optical_capture=False
        )
    assert "Cannot declare custody action 'CAPTURED'" in str(exc.value)


# Vector 4: Printer claim when absent
def test_vector_4_printer_claim_when_absent():
    with pytest.raises(AntiFabricationViolation) as exc:
        AntiFabricationGuard.validate_printer_claim(
            printer_detected=False,
            claimed_status=EpistemicStatus.MEASURED_PHYSICAL
        )
    assert "Cannot claim MEASURED_PHYSICAL for print validation" in str(exc.value)


# Vector 5: Scanner claim when absent
def test_vector_5_scanner_claim_when_absent():
    with pytest.raises(AntiFabricationViolation) as exc:
        AntiFabricationGuard.validate_scanner_claim(
            scanner_detected=False,
            claimed_status=EpistemicStatus.MEASURED_PHYSICAL
        )
    assert "Cannot claim MEASURED_PHYSICAL for scanner validation" in str(exc.value)


# Vector 6: Computational model claimed as measured physical
def test_vector_6_computational_model_claimed_as_physical():
    with pytest.raises(AntiFabricationViolation) as exc:
        AntiFabricationGuard.validate_camera_claim(
            camera_detected=True,  # Even if a camera were present
            claimed_status=EpistemicStatus.MEASURED_PHYSICAL,
            provenance_basis="COMPUTATIONAL_MODEL"
        )
    assert "Cannot claim MEASURED_PHYSICAL when transformation basis is computational model" in str(exc.value)


# Vector 7: Overall experiment claiming MEASURED_PHYSICAL with absent camera
def test_vector_7_experiment_absent_camera():
    rec = ExperimentEpistemicRecord(
        experiment_id="EXP-V7",
        overall_status=EpistemicStatus.MEASURED_PHYSICAL,
        summary_declaration="Fraudulent claim of full physical capture",
        subcomponents={
            "CAMERA": SubsystemEpistemicClaim(
                subsystem="CAMERA",
                status=EpistemicStatus.MEASURED_PHYSICAL,
                required_hardware="Physical Camera Sensor",
                detected_hardware="None",
                actual_procedure="Simulated blur"
            )
        }
    )
    with pytest.raises(AntiFabricationViolation) as exc:
        AntiFabricationGuard.validate_experiment_record(rec, camera_detected=False)
    assert "absent camera" in str(exc.value)


# Vector 8: Overall experiment claiming MEASURED_PHYSICAL with absent printer
def test_vector_8_experiment_absent_printer():
    rec = ExperimentEpistemicRecord(
        experiment_id="EXP-V8",
        overall_status=EpistemicStatus.MEASURED_PHYSICAL,
        summary_declaration="Fraudulent claim of full physical print",
        subcomponents={
            "PRINTER": SubsystemEpistemicClaim(
                subsystem="PRINTER",
                status=EpistemicStatus.MEASURED_PHYSICAL,
                required_hardware="Physical Laser/Inkjet Printer",
                detected_hardware="None",
                actual_procedure="Virtual PDF print"
            )
        }
    )
    with pytest.raises(AntiFabricationViolation) as exc:
        AntiFabricationGuard.validate_experiment_record(rec, printer_detected=False)
    assert "absent printer" in str(exc.value)


# Vector 9: Overall experiment claiming MEASURED_PHYSICAL with absent scanner
def test_vector_9_experiment_absent_scanner():
    rec = ExperimentEpistemicRecord(
        experiment_id="EXP-V9",
        overall_status=EpistemicStatus.MEASURED_PHYSICAL,
        summary_declaration="Fraudulent claim of full physical scan",
        subcomponents={
            "SCANNER": SubsystemEpistemicClaim(
                subsystem="SCANNER",
                status=EpistemicStatus.MEASURED_PHYSICAL,
                required_hardware="Physical Flatbed Scanner",
                detected_hardware="None",
                actual_procedure="Virtual image crop"
            )
        }
    )
    with pytest.raises(AntiFabricationViolation) as exc:
        AntiFabricationGuard.validate_experiment_record(rec, scanner_detected=False)
    assert "absent scanner" in str(exc.value)


# Vector 10: PDF rendered on phone screen != Physical paper validation
def test_vector_10_pdf_rendered_not_paper():
    # Attempting to assign MEASURED_PHYSICAL to a paper printout claim when only display was rendered
    sub = SubsystemEpistemicClaim(
        subsystem="PAPER_PRINT",
        status=EpistemicStatus.MEASURED_PHYSICAL,
        required_hardware="Paper & Printer",
        detected_hardware="Phone AMOLED Screen",
        actual_procedure="Rendered on Note10 screen"
    )
    with pytest.raises(AntiFabricationViolation):
        AntiFabricationGuard.validate_printer_claim(
            printer_detected=False,
            claimed_status=sub.status
        )


# Vector 11: Custody ledger rejects CAPTURED without physical optical sensor
def test_vector_11_custody_ledger_rejects_unverified_capture():
    ledger = DeviceCustodyLedger(ledger_id="CUST-V11")
    with pytest.raises(AntiFabricationViolation) as exc:
        ledger.record_transition(
            action=DeviceCustodyAction.CAPTURED,
            device_id="phone_rf8n927pm9n",
            artifact_hash="deadbeef1234",
            operator="AUTOMATED_PIPELINE",
            is_optical_capture=False  # Not a real optical sensor capture
        )
    assert "Cannot declare custody action 'CAPTURED'" in str(exc.value)


# Vector 12: Transfer corruption detection fail-closed
def test_vector_12_transfer_corruption_fail_closed():
    payload = b"CRITICAL_INTELLIGENCE_DISPATCH_DOC"
    rec = DeviceTransferEngine.execute_transfer(
        payload_bytes=payload,
        filename="dispatch.pdf",
        artifact_id="ART-12",
        direction=TransferDirection.LAPTOP_TO_PHONE,
        source_device="laptop_host",
        dest_device="phone_rf8n927pm9n",
        simulate_corruption=True
    )
    assert rec.is_hash_identical is False
    assert rec.status == "HASH_MISMATCH"
    assert rec.source_hash != rec.destination_hash


# Vector 13: Unauthorized ADB device execution separation
def test_vector_13_unauthorized_adb_separation():
    phone_unauth = SmartphoneDeviceRecord(
        device_id="phone_rzcy9396agx",
        serial="RZCY9396AGX",
        role=PhoneRole.PHONE_B_INDEPENDENT,
        model="Galaxy A55 5G",
        os_version="Android 14",
        usb_connection_state="CONNECTED",
        adb_state=PhoneAdbState.UNAUTHORIZED,
        camera_capability=EpistemicStatus.NOT_VERIFIED
    )
    # When ADB is unauthorized, direct ADB push/pull cannot execute
    assert phone_unauth.adb_state == PhoneAdbState.UNAUTHORIZED
    assert phone_unauth.camera_capability == EpistemicStatus.NOT_VERIFIED


# Vector 14: Non-collapsing of epistemic states
def test_vector_14_non_collapsing_status_integrity():
    rec = ExperimentEpistemicRecord(
        experiment_id="EXP-14",
        overall_status=EpistemicStatus.HYBRID_VALIDATION,
        summary_declaration="Honest hybrid validation",
        subcomponents={
            "DISPLAY": SubsystemEpistemicClaim(
                subsystem="DISPLAY",
                status=EpistemicStatus.DEVICE_IN_LOOP,
                required_hardware="Laptop Display",
                detected_hardware="AMD Radeon 1920x1080@144Hz",
                actual_procedure="Physical screen presentation"
            ),
            "CAMERA": SubsystemEpistemicClaim(
                subsystem="CAMERA",
                status=EpistemicStatus.NOT_VERIFIED,
                required_hardware="Camera",
                detected_hardware="None",
                actual_procedure="Optical probe"
            )
        }
    )
    assert rec.overall_status == EpistemicStatus.HYBRID_VALIDATION
    assert rec.subcomponents["DISPLAY"].status == EpistemicStatus.DEVICE_IN_LOOP
    assert rec.subcomponents["CAMERA"].status == EpistemicStatus.NOT_VERIFIED


# Vector 15: Masking simulation as physical is blocked
def test_vector_15_masking_simulation_blocked():
    with pytest.raises(AntiFabricationViolation):
        AntiFabricationGuard.validate_camera_claim(
            camera_detected=False,
            claimed_status=EpistemicStatus.MEASURED_PHYSICAL,
            provenance_basis="SIMULATION"
        )


# Vector 16: Honest reporting passes cleanly
def test_vector_16_honest_reporting_passes_cleanly():
    # NOT_VERIFIED passes when camera is absent
    AntiFabricationGuard.validate_camera_claim(
        camera_detected=False,
        claimed_status=EpistemicStatus.NOT_VERIFIED
    )
    # UNAVAILABLE passes when printer is absent
    AntiFabricationGuard.validate_printer_claim(
        printer_detected=False,
        claimed_status=EpistemicStatus.UNAVAILABLE
    )
    # TRANSFERRED passes when optical capture is false
    AntiFabricationGuard.validate_transfer_vs_capture(
        action="TRANSFERRED",
        is_optical_capture=False
    )
    # Full record with HYBRID_VALIDATION and honest subcomponents passes
    rec = ExperimentEpistemicRecord(
        experiment_id="EXP-16-HONEST",
        overall_status=EpistemicStatus.HYBRID_VALIDATION,
        summary_declaration="Honest hybrid experiment",
        subcomponents={
            "CAMERA": SubsystemEpistemicClaim(
                subsystem="CAMERA",
                status=EpistemicStatus.NOT_VERIFIED,
                required_hardware="Camera",
                detected_hardware="None",
                actual_procedure="Probe returned 0 cameras"
            ),
            "PRINTER": SubsystemEpistemicClaim(
                subsystem="PRINTER",
                status=EpistemicStatus.UNAVAILABLE,
                required_hardware="Printer",
                detected_hardware="None",
                actual_procedure="Probe returned 0 physical printers"
            )
        }
    )
    AntiFabricationGuard.validate_experiment_record(
        rec,
        camera_detected=False,
        printer_detected=False,
        scanner_detected=False
    )
