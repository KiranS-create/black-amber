"""
SIH26237 - Epistemic Status Model & Anti-Fabrication Framework
===============================================================
Establishes the formal mathematical and scientific honesty rules for
hardware-grounded, device-in-the-loop, and hybrid physical validation.

SCIENTIFIC INTEGRITY INVARIANTS:
1. Every experiment and subcomponent must be assigned exactly ONE primary epistemic state:
   - MEASURED_PHYSICAL: A genuine physical hardware process actually occurred.
   - DEVICE_IN_LOOP: A real physical device participated, but the complete physical
     optical/print/scan chain was not physically reproduced.
   - HYBRID_VALIDATION: Real device/network/file/display behavior combined with explicitly
     labeled simulation steps.
   - SIMULATION_CALIBRATION: The transformation or experiment was generated computationally
     rather than physically measured.
   - NOT_VERIFIED: The capability was not actually demonstrated.
   - UNAVAILABLE: Required hardware or interface is absent from the host environment.
2. Contradictory claims fail closed:
   - camera_used == True when camera_detected == False -> AntiFabricationViolation
   - physical_capture == True when no capture artifact exists -> AntiFabricationViolation
   - printer_test == PASSED when printer_detected == 0 -> AntiFabricationViolation
   - scanner_test == PASSED when scanner_detected == 0 -> AntiFabricationViolation
   - status == MEASURED_PHYSICAL when provenance says SIMULATION -> AntiFabricationViolation
3. Non-inferential boundaries:
   - USB_CONNECTED != CAMERA_AVAILABLE
   - IMAGE_TRANSFERRED != OPTICAL_CAPTURE_VERIFIED
   - PDF_RENDERED_ON_PHONE != PDF_PHYSICALLY_VALIDATED
"""

from enum import Enum
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from pydantic import BaseModel, Field


class EpistemicStatus(str, Enum):
    """
    Formal epistemic classification of an experimental measurement or capability claim.
    Never collapse these into a single generic 'physical validation' score.
    """
    MEASURED_PHYSICAL = "MEASURED_PHYSICAL"
    DEVICE_IN_LOOP = "DEVICE_IN_LOOP"
    HYBRID_VALIDATION = "HYBRID_VALIDATION"
    SIMULATION_CALIBRATION = "SIMULATION_CALIBRATION"
    NOT_VERIFIED = "NOT_VERIFIED"
    UNAVAILABLE = "UNAVAILABLE"


class AntiFabricationViolation(Exception):
    """
    Raised when an experiment, claim, or report attempts to assert a physical or
    hardware capability that is contradicted by discovered hardware or provenance records.
    """
    def __init__(self, rule_violation: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(f"[ANTI_FABRICATION_VIOLATION] {rule_violation}")
        self.rule_violation = rule_violation
        self.details = details or {}


class SubsystemEpistemicClaim(BaseModel):
    """Granular epistemic assessment of a single validation subcomponent."""
    subsystem: str  # e.g. "DISPLAY", "PHONE_BROWSER", "FILE_TRANSFER", "NETWORK", "CAMERA", "PRINTER", "SCANNER"
    status: EpistemicStatus
    required_hardware: str
    detected_hardware: str
    actual_procedure: str
    evidence_artifact: Optional[str] = None
    provenance_basis: str = "GENUINE_HARDWARE"  # "GENUINE_HARDWARE", "DEVICE_SESSION", "COMPUTATIONAL_MODEL", "NONE"
    limitations: List[str] = Field(default_factory=list)


class ExperimentEpistemicRecord(BaseModel):
    """Overall epistemic classification and subcomponent breakdown for an experiment."""
    experiment_id: str
    overall_status: EpistemicStatus
    summary_declaration: str
    subcomponents: Dict[str, SubsystemEpistemicClaim] = Field(default_factory=dict)
    has_unsupported_claim: bool = False
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class AntiFabricationGuard:
    """
    Enforces non-fabrication invariants across hardware discovery, device-in-the-loop
    executions, and validation reports.
    """

    @classmethod
    def validate_camera_claim(
        cls,
        camera_detected: bool,
        claimed_status: EpistemicStatus,
        provenance_basis: str = "GENUINE_HARDWARE"
    ) -> None:
        """
        Validates that a camera capture claim is epistemically honest.
        """
        if not camera_detected:
            if claimed_status == EpistemicStatus.MEASURED_PHYSICAL:
                raise AntiFabricationViolation(
                    "Cannot claim MEASURED_PHYSICAL for camera capture when 0 physical cameras are detected.",
                    details={"camera_detected": False, "claimed_status": claimed_status.value}
                )
            if claimed_status not in [EpistemicStatus.NOT_VERIFIED, EpistemicStatus.UNAVAILABLE, EpistemicStatus.SIMULATION_CALIBRATION]:
                raise AntiFabricationViolation(
                    f"Invalid status '{claimed_status.value}' for camera when hardware is absent. Must be NOT_VERIFIED or UNAVAILABLE.",
                    details={"camera_detected": False, "claimed_status": claimed_status.value}
                )
        if provenance_basis in ["MODEL", "COMPUTATIONAL_MODEL", "SIMULATION"] and claimed_status == EpistemicStatus.MEASURED_PHYSICAL:
            raise AntiFabricationViolation(
                "Cannot claim MEASURED_PHYSICAL when transformation basis is computational model/simulation.",
                details={"provenance_basis": provenance_basis, "claimed_status": claimed_status.value}
            )

    @classmethod
    def validate_printer_claim(cls, printer_detected: bool, claimed_status: EpistemicStatus) -> None:
        """Validates printer capability claims."""
        if not printer_detected and claimed_status == EpistemicStatus.MEASURED_PHYSICAL:
            raise AntiFabricationViolation(
                "Cannot claim MEASURED_PHYSICAL for print validation when 0 physical printers are detected.",
                details={"printer_detected": False, "claimed_status": claimed_status.value}
            )

    @classmethod
    def validate_scanner_claim(cls, scanner_detected: bool, claimed_status: EpistemicStatus) -> None:
        """Validates scanner capability claims."""
        if not scanner_detected and claimed_status == EpistemicStatus.MEASURED_PHYSICAL:
            raise AntiFabricationViolation(
                "Cannot claim MEASURED_PHYSICAL for scanner validation when 0 physical scanners are detected.",
                details={"scanner_detected": False, "claimed_status": claimed_status.value}
            )

    @classmethod
    def validate_phone_role_separation(
        cls,
        phone_connected: bool,
        claimed_as_camera: bool,
        has_real_camera_stream: bool
    ) -> None:
        """
        Enforces: USB_CONNECTED != CAMERA_AVAILABLE.
        Connecting a phone via USB does not make it a camera.
        """
        if phone_connected and claimed_as_camera and not has_real_camera_stream:
            raise AntiFabricationViolation(
                "Phone USB connection alone does NOT constitute camera availability. Optical capture stream is absent.",
                details={"phone_connected": True, "claimed_as_camera": True, "has_real_camera_stream": False}
            )

    @classmethod
    def validate_transfer_vs_capture(
        cls,
        action: str,
        is_optical_capture: bool
    ) -> None:
        """
        Enforces: IMAGE_TRANSFERRED != OPTICAL_CAPTURE_VERIFIED.
        Transferring a file from phone to laptop is TRANSFERRED, not CAPTURED.
        """
        if action.upper() == "CAPTURED" and not is_optical_capture:
            raise AntiFabricationViolation(
                "Cannot declare custody action 'CAPTURED' for digital file transfer without physical optical sensor capture. Must use 'TRANSFERRED'.",
                details={"action": action, "is_optical_capture": is_optical_capture}
            )

    @classmethod
    def validate_experiment_record(
        cls,
        record: ExperimentEpistemicRecord,
        camera_detected: bool = False,
        printer_detected: bool = False,
        scanner_detected: bool = False
    ) -> None:
        """
        Performs holistic audit on an entire experiment epistemic record.
        """
        # Overall status cannot be MEASURED_PHYSICAL if any required physical step (camera/print/scan) is missing
        if record.overall_status == EpistemicStatus.MEASURED_PHYSICAL:
            if not camera_detected and "CAMERA" in record.subcomponents:
                cam = record.subcomponents["CAMERA"]
                if cam.status == EpistemicStatus.MEASURED_PHYSICAL:
                    raise AntiFabricationViolation("Overall experiment claimed MEASURED_PHYSICAL with absent camera.")
            if not printer_detected and "PRINTER" in record.subcomponents:
                pr = record.subcomponents["PRINTER"]
                if pr.status == EpistemicStatus.MEASURED_PHYSICAL:
                    raise AntiFabricationViolation("Overall experiment claimed MEASURED_PHYSICAL with absent printer.")
            if not scanner_detected and "SCANNER" in record.subcomponents:
                sc = record.subcomponents["SCANNER"]
                if sc.status == EpistemicStatus.MEASURED_PHYSICAL:
                    raise AntiFabricationViolation("Overall experiment claimed MEASURED_PHYSICAL with absent scanner.")

        # Check subcomponents individually
        for name, sub in record.subcomponents.items():
            if name.upper() == "CAMERA":
                cls.validate_camera_claim(camera_detected, sub.status, sub.provenance_basis)
            elif name.upper() == "PRINTER":
                cls.validate_printer_claim(printer_detected, sub.status)
            elif name.upper() == "SCANNER":
                cls.validate_scanner_claim(scanner_detected, sub.status)
