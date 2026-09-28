"""
SIH26237 - Test Laboratory Run Manifest & Cryptographic Attestation
"""

import pytest
import json
from core.physical.manifest import LaboratoryRunManifest, RunManifestFactory
from core.physical.discovery import HardwareDiscoveryEngine


def test_manifest_creation_and_integrity():
    """Verify laboratory manifest builds with canonical hash and verifies cleanly."""
    inventory = HardwareDiscoveryEngine.discover_all()
    manifest = RunManifestFactory.create_manifest(
        inventory=inventory,
        operator="TEST_OPERATOR",
        random_seed=12345
    )
    assert manifest.run_id.startswith("run_phys_")
    assert manifest.operator == "TEST_OPERATOR"
    assert manifest.random_seed == 12345
    assert len(manifest.manifest_hash) == 64
    assert manifest.verify_integrity() is True


def test_manifest_detects_tampering():
    """Verify tampering with manifest attributes invalidates integrity check."""
    inventory = HardwareDiscoveryEngine.discover_all()
    manifest = RunManifestFactory.create_manifest(
        inventory=inventory,
        operator="TEST_OPERATOR"
    )
    assert manifest.verify_integrity() is True

    # Tamper with operator
    manifest.operator = "MALICIOUS_OPERATOR"
    assert manifest.verify_integrity() is False


def test_manifest_serialization_roundtrip():
    """Verify manifest dictionary serialization and deserialization."""
    inventory = HardwareDiscoveryEngine.discover_all()
    manifest = RunManifestFactory.create_manifest(
        inventory=inventory,
        operator="TEST_OPERATOR"
    )
    data = manifest.model_dump()
    assert isinstance(data, dict)
    assert data["manifest_hash"] == manifest.manifest_hash
    rebuilt = LaboratoryRunManifest(**data)
    assert rebuilt.verify_integrity() is True
