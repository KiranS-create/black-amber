"""
SIH26237 - Physical Laboratory Validation & Hardware-Grounded Forensics
Package initialization exporting hardware discovery, run manifests, physical trial engines,
experiments, negative corpora, separation matrices, visual metrics, custody, and evidence bridges.
"""

from core.physical.discovery import (
    DeviceModality,
    DeviceStatus,
    PhysicalDeviceRecord,
    HardwareInventory,
    HardwareDiscoveryEngine,
)
from core.physical.manifest import (
    LaboratoryRunManifest,
    RunManifestFactory,
)
from core.physical.golden_source import (
    GoldenSourceSpecification,
    GoldenPhysicalSourceBuilder,
)
from core.physical.trial_engine import (
    PhysicalTrialSessionRecord,
    PhysicalTrialEngine,
)
from core.physical.experiments import (
    PhysicalTrialResult,
    PhysicalExperimentRunner,
)
from core.physical.negative_corpus import (
    PhysicalNegativeResult,
    PhysicalNegativeCorpusBuilder,
)
from core.physical.separation import (
    PairwiseSeparationEntry,
    PhysicalSeparationMatrixSummary,
    PhysicalSeparationMatrixAnalyzer,
)
from core.physical.visual import (
    PhysicalVisualEquivalenceMetrics,
    PhysicalVisualEquivalenceAnalyzer,
)
from core.physical.custody import (
    CustodyTransitionEvent,
    PhysicalChainOfCustodyLedger,
    PhysicalChainOfCustodyTracker,
)
from core.physical.evidence_bridge import (
    PhysicalEvidenceBridge,
)
from core.physical.failure_boundaries import (
    FailureBoundaryTestPoint,
    PhysicalOperatingEnvelope,
    PhysicalFailureBoundaryAnalyzer,
)
from core.physical.metrics import (
    PhysicalValidationConfusionMatrix,
    PhysicalUncertaintySummary,
    PhysicalMetricsCalculator,
)

__all__ = [
    "DeviceModality",
    "DeviceStatus",
    "PhysicalDeviceRecord",
    "HardwareInventory",
    "HardwareDiscoveryEngine",
    "LaboratoryRunManifest",
    "RunManifestFactory",
    "GoldenSourceSpecification",
    "GoldenPhysicalSourceBuilder",
    "PhysicalTrialSessionRecord",
    "PhysicalTrialEngine",
    "PhysicalTrialResult",
    "PhysicalExperimentRunner",
    "PhysicalNegativeResult",
    "PhysicalNegativeCorpusBuilder",
    "PairwiseSeparationEntry",
    "PhysicalSeparationMatrixSummary",
    "PhysicalSeparationMatrixAnalyzer",
    "PhysicalVisualEquivalenceMetrics",
    "PhysicalVisualEquivalenceAnalyzer",
    "CustodyTransitionEvent",
    "PhysicalChainOfCustodyLedger",
    "PhysicalChainOfCustodyTracker",
    "PhysicalEvidenceBridge",
    "FailureBoundaryTestPoint",
    "PhysicalOperatingEnvelope",
    "PhysicalFailureBoundaryAnalyzer",
    "PhysicalValidationConfusionMatrix",
    "PhysicalUncertaintySummary",
    "PhysicalMetricsCalculator",
]
