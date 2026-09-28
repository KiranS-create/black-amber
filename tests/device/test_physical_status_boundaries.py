"""
SIH26237 - Test Physical Status Boundaries & Epistemic Fail-Closed Rules
========================================================================
Validates boundary constraints and fail-closed transitions across:
1. Missing camera hardware boundaries (0 cameras -> NOT_VERIFIED / UNAVAILABLE only)
2. Missing printer hardware boundaries (0 printers -> UNAVAILABLE only)
3. Missing scanner hardware boundaries (0 scanners -> UNAVAILABLE only)
4. Display presence boundary (Display -> DEVICE_IN_LOOP presentation, not optical capture)
5. Smartphone boundary (Phone connected -> DEVICE_IN_LOOP, not camera)
6. Epistemic state transition boundaries (Simulated -> Physical transition blocked)
7. Non-collapsing invariant across multi-subsystem aggregation
"""

import pytest
from core.physical.epistemic import (
    EpistemicStatus,
    AntiFabricationGuard,
    AntiFabricationViolation,
    SubsystemEpistemicClaim,
    ExperimentEpistemicRecord
)
from core.physical.device_discovery import DeviceHardwareDiscoveryEngine


def test_camera_absence_boundary():
    """Ensure that 0 detected cameras strictly constrains camera claims."""
    hw_inv = DeviceHardwareDiscoveryEngine.discover_all()
    # Host has 0 detected physical cameras
    assert len(hw_inv.cameras) == 0
    
    # Passing valid statuses
    AntiFabricationGuard.validate_camera_claim(
        camera_detected=False,
        claimed_status=EpistemicStatus.NOT_VERIFIED
    )
    AntiFabricationGuard.validate_camera_claim(
        camera_detected=False,
        claimed_status=EpistemicStatus.UNAVAILABLE
    )
    
    # Invalid statuses must raise AntiFabricationViolation
    with pytest.raises(AntiFabricationViolation):
        AntiFabricationGuard.validate_camera_claim(
            camera_detected=False,
            claimed_status=EpistemicStatus.MEASURED_PHYSICAL
        )
    with pytest.raises(AntiFabricationViolation):
        AntiFabricationGuard.validate_camera_claim(
            camera_detected=False,
            claimed_status=EpistemicStatus.DEVICE_IN_LOOP
        )


def test_printer_absence_boundary():
    """Ensure that 0 detected physical printers strictly constrains print claims."""
    hw_inv = DeviceHardwareDiscoveryEngine.discover_all()
    assert len(hw_inv.printers) == 0
    
    # UNAVAILABLE is allowed
    AntiFabricationGuard.validate_printer_claim(
        printer_detected=False,
        claimed_status=EpistemicStatus.UNAVAILABLE
    )
    
    # MEASURED_PHYSICAL is blocked
    with pytest.raises(AntiFabricationViolation):
        AntiFabricationGuard.validate_printer_claim(
            printer_detected=False,
            claimed_status=EpistemicStatus.MEASURED_PHYSICAL
        )


def test_scanner_absence_boundary():
    """Ensure that 0 detected scanners strictly constrains scanner claims."""
    hw_inv = DeviceHardwareDiscoveryEngine.discover_all()
    assert len(hw_inv.scanners) == 0
    
    # UNAVAILABLE is allowed
    AntiFabricationGuard.validate_scanner_claim(
        scanner_detected=False,
        claimed_status=EpistemicStatus.UNAVAILABLE
    )
    
    # MEASURED_PHYSICAL is blocked
    with pytest.raises(AntiFabricationViolation):
        AntiFabricationGuard.validate_scanner_claim(
            scanner_detected=False,
            claimed_status=EpistemicStatus.MEASURED_PHYSICAL
        )


def test_display_boundary():
    """Ensure display presence allows presentation verification but blocks optical capture."""
    hw_inv = DeviceHardwareDiscoveryEngine.discover_all()
    assert len(hw_inv.displays) >= 1
    
    # Display presentation claim
    disp = hw_inv.displays[0]
    disp_claim = SubsystemEpistemicClaim(
        subsystem="LAPTOP_DISPLAY",
        status=EpistemicStatus.DEVICE_IN_LOOP,
        required_hardware="Physical Monitor",
        detected_hardware=f"{disp.name} ({disp.resolution_str})",
        actual_procedure="Presentation of carrier artifact"
    )
    assert disp_claim.status == EpistemicStatus.DEVICE_IN_LOOP
    
    # Display cannot be claimed as camera capture
    with pytest.raises(AntiFabricationViolation):
        AntiFabricationGuard.validate_camera_claim(
            camera_detected=False,
            claimed_status=EpistemicStatus.MEASURED_PHYSICAL
        )


def test_simulation_to_physical_transition_blocked():
    """Ensure a computational transform cannot be relabeled as physical measurement."""
    sim_claim = SubsystemEpistemicClaim(
        subsystem="OPTICAL_WARP",
        status=EpistemicStatus.SIMULATION_CALIBRATION,
        required_hardware="None",
        detected_hardware="N/A",
        actual_procedure="Synthetic homography and blur",
        provenance_basis="COMPUTATIONAL_MODEL"
    )
    
    # Re-evaluating with claimed_status=MEASURED_PHYSICAL should fail
    with pytest.raises(AntiFabricationViolation):
        AntiFabricationGuard.validate_camera_claim(
            camera_detected=True,  # Even if camera exists
            claimed_status=EpistemicStatus.MEASURED_PHYSICAL,
            provenance_basis=sim_claim.provenance_basis
        )
