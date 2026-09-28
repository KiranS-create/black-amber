"""
SIH26237 - Test Device & Hardware Discovery
===========================================
Verifies discovery of physical smartphones, displays, network interfaces,
and strict non-fabrication of absent cameras/printers/scanners.
"""

import pytest
from core.physical.device_discovery import (
    DeviceHardwareDiscoveryEngine,
    UnifiedHardwareInventory,
    PhoneRole,
    PhoneAdbState
)
from core.physical.epistemic import EpistemicStatus


def test_device_discovery_execution():
    """Verify hardware discovery executes across all modalities without crashing."""
    inv = DeviceHardwareDiscoveryEngine.discover_all()
    assert isinstance(inv, UnifiedHardwareInventory)
    assert inv.inventory_id.startswith("HWINV-")
    assert inv.host_name != ""
    assert isinstance(inv.phones, list)
    assert isinstance(inv.displays, list)
    assert isinstance(inv.network_interfaces, list)


def test_device_discovery_non_fabrication_cameras():
    """Verify camera status is UNAVAILABLE or NOT_VERIFIED when 0 cameras detected."""
    inv = DeviceHardwareDiscoveryEngine.discover_all()
    if not inv.cameras or all(not c.is_available for c in inv.cameras):
        assert inv.camera_status in [EpistemicStatus.UNAVAILABLE, EpistemicStatus.NOT_VERIFIED]


def test_device_discovery_non_fabrication_printers():
    """Verify printer status is UNAVAILABLE when only virtual print queues exist."""
    inv = DeviceHardwareDiscoveryEngine.discover_all()
    assert inv.printer_status in [EpistemicStatus.UNAVAILABLE, EpistemicStatus.NOT_VERIFIED]
    for p in inv.printers:
        assert not any(v in p.name.lower() for v in ["onenote", "xps", "pdf", "fax"])


def test_smartphone_role_assignment():
    """Verify Phone A and Phone B role assignments when smartphones are detected."""
    inv = DeviceHardwareDiscoveryEngine.discover_all()
    if len(inv.phones) >= 1:
        assert inv.phone_a is not None
        assert inv.phone_a.role == PhoneRole.PHONE_A_RECIPIENT
        # Crucial invariant: phone USB connection does NOT mean camera is available!
        assert inv.phone_a.camera_capability == EpistemicStatus.NOT_VERIFIED
    if len(inv.phones) >= 2:
        assert inv.phone_b is not None
        assert inv.phone_b.role == PhoneRole.PHONE_B_INDEPENDENT
        assert inv.phone_b.camera_capability == EpistemicStatus.NOT_VERIFIED
