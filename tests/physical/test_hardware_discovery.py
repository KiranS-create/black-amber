"""
SIH26237 - Test Hardware Discovery Engine & Epistemic Status
"""

import pytest
from core.physical.discovery import HardwareDiscoveryEngine, HardwareInventory, DeviceStatus, DeviceModality


def test_hardware_discovery_probes_cleanly():
    """Verify hardware discovery executes across all modalities without crashing."""
    inventory = HardwareDiscoveryEngine.discover_all()
    assert isinstance(inventory, HardwareInventory)
    assert isinstance(inventory.devices, list)
    assert inventory.epistemic_classification in [
        "NOT_VERIFIED",
        "PHYSICAL"
    ]


def test_epistemic_honesty_when_hardware_unavailable():
    """When no genuine cameras or printers exist, verification status must be NOT_VERIFIED."""
    inventory = HardwareDiscoveryEngine.discover_all()
    cams = inventory.get_devices_by_modality(DeviceModality.CAMERA)
    printers = inventory.get_devices_by_modality(DeviceModality.PRINTER)
    if len(cams) == 0:
        assert inventory.camera_status == DeviceStatus.UNAVAILABLE
        assert inventory.epistemic_classification == "NOT_VERIFIED"


def test_camera_probe_returns_list():
    """Test camera probe directly returns list of devices."""
    cameras = HardwareDiscoveryEngine.probe_cameras(max_indices=2)
    assert isinstance(cameras, list)


def test_printer_probe_filters_software_drivers():
    """Test printer probe filters out virtual/software print queues."""
    printers = HardwareDiscoveryEngine.probe_printers()
    assert isinstance(printers, list)
    for p in printers:
        assert p.modality == DeviceModality.PRINTER
        # Ensure virtual drivers aren't in model/driver
        assert not any(v in p.model.lower() for v in ["onenote", "xps", "pdf", "fax"])
