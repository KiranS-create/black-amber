"""
SIH26237 - Test Epistemic Segregation and Scientific Honesty Invariants
"""

import pytest
from core.physical.discovery import HardwareDiscoveryEngine, DeviceModality
from core.physical.manifest import RunManifestFactory
from core.physical.metrics import PhysicalMetricsCalculator
from core.physical.negative_corpus import PhysicalNegativeCorpusBuilder


def test_epistemic_tag_honesty():
    """Verify that when physical devices are absent, epistemic tags are never fabricated as hardware-grounded."""
    inventory = HardwareDiscoveryEngine.discover_all()
    cams = inventory.get_devices_by_modality(DeviceModality.CAMERA)
    printers = inventory.get_devices_by_modality(DeviceModality.PRINTER)
    if len(cams) == 0 or len(printers) == 0:
        assert inventory.epistemic_classification == "NOT_VERIFIED"
        assert inventory.is_physical_lab_ready is False

    manifest = RunManifestFactory.create_manifest(inventory=inventory)
    assert manifest.epistemic_classification in ["NOT_VERIFIED", "GENUINE_HARDWARE_GROUNDED"]


def test_metrics_clopper_pearson_confidence_intervals():
    """Verify exact Clopper-Pearson 95% confidence intervals are computed for physical error rates."""
    neg_results = PhysicalNegativeCorpusBuilder().evaluate_negative_corpus()
    summary = PhysicalMetricsCalculator.compute_summary(
        positive_results=[],
        negative_results=neg_results
    )

    assert summary.fp == 0
    assert summary.fpr_ci_clopper_pearson.lower_bound_95 == 0.0
    assert summary.fpr_ci_clopper_pearson.upper_bound_95 <= 0.10  # Exact upper bound for 0/40 is ~0.088
