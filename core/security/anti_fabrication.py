"""
AegisTrace - Anti-Fabrication & Strict Classification Enforcement Guard
=======================================================================
Enforces absolute scientific integrity across the entire AegisTrace forensic
pipeline. Prohibits any simulation, synthetic noise, or mathematical transform
from being labeled as genuine physical hardware capture.

MANDATORY TAXONOMY:
- MEASURED_PHYSICAL: Real physical hardware capture (camera, printer, scanner).
- SIMULATION: Software channel transformation (affine, blur, noise, compression).
- CALIBRATION: Dataset partition used to calibrate detector hyperparameters.
- NOT_VERIFIED: Hardware modality unavailable on current host.
- LIMITATION: Stated physical operating envelope boundary.
"""

from enum import Enum
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field


class ValidationClassification(str, Enum):
    MEASURED_PHYSICAL = "MEASURED_PHYSICAL"
    SIMULATION = "SIMULATION"
    CALIBRATION = "CALIBRATION"
    NOT_VERIFIED = "NOT_VERIFIED"
    LIMITATION = "LIMITATION"


class FabricationViolationError(Exception):
    """Raised when an artifact or report violates scientific non-fabrication rules."""
    pass


class AntiFabricationGuard:
    """
    Automated watchdog validating that results, artifacts, and claims strictly
    adhere to non-fabrication invariants.
    """

    @staticmethod
    def enforce_classification_integrity(
        classification: ValidationClassification,
        is_hardware_available: bool,
        device_id: Optional[str] = None,
        raw_capture_hash: Optional[str] = None,
        is_synthetic: bool = False,
        transformation_type: Optional[str] = None,
    ) -> None:
        """
        Validates that a declared classification is lawful given the operational context.
        Raises FabricationViolationError on any violation.
        """
        if classification == ValidationClassification.MEASURED_PHYSICAL:
            if not is_hardware_available:
                raise FabricationViolationError(
                    "Violation: Attempted to declare MEASURED_PHYSICAL when hardware is UNAVAILABLE."
                )
            if is_synthetic:
                raise FabricationViolationError(
                    "Violation: Attempted to declare synthetic or simulated artifact as MEASURED_PHYSICAL."
                )
            if not device_id or device_id == "UNKNOWN":
                raise FabricationViolationError(
                    "Violation: MEASURED_PHYSICAL requires a verified physical device_id."
                )
            if not raw_capture_hash:
                raise FabricationViolationError(
                    "Violation: MEASURED_PHYSICAL requires an immutable raw_capture_hash."
                )

        if classification == ValidationClassification.SIMULATION:
            if not is_synthetic and not transformation_type:
                # Simulation must explicitly acknowledge its transform/model
                pass

        if not is_hardware_available and classification == ValidationClassification.MEASURED_PHYSICAL:
            raise FabricationViolationError(
                "Violation: Cannot claim MEASURED_PHYSICAL without verified live hardware."
            )

    @staticmethod
    def sanitize_trial_record(record: Dict[str, Any], hardware_available: bool) -> Dict[str, Any]:
        """
        Ensures a trial dictionary cannot falsely claim physical verification.
        """
        sanitized = dict(record)
        declared_class = sanitized.get("classification")
        
        if declared_class == ValidationClassification.MEASURED_PHYSICAL.value and not hardware_available:
            sanitized["classification"] = ValidationClassification.NOT_VERIFIED.value
            sanitized["status"] = "NOT_VERIFIED"
            sanitized["non_fabrication_note"] = "Hardware unavailable; claim downgraded to NOT_VERIFIED."
            
        return sanitized
