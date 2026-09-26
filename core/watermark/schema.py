"""
SIH26237 - Physical Watermark Experiment Result Schema & Ingestion Models
Defines machine-readable data structures for physical and simulated watermark validation.
"""

from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field


class PhysicalExperimentRecord(BaseModel):
    """
    Standardized experimental record schema for every physical or simulated test.
    Never stores private cryptographic keys.
    """
    test_id: str
    physical_or_simulated: Literal["PHYSICAL", "SIMULATED"]
    printer: str = "N/A"
    printer_type: str = "N/A"                    # e.g., "Laser", "Inkjet", "Simulation"
    paper: str = "N/A"                           # e.g., "80gsm standard copy paper", "Synthetic"
    camera: str = "N/A"                          # e.g., "Smartphone Rear", "Simulation"
    camera_model_if_known: Optional[str] = None  # e.g., "iPhone 15 Pro", "Samsung S23"
    lighting: str = "Normal indoor"              # e.g., "Normal indoor", "Uneven shadow", "Low light"
    distance: str = "~30cm"                      # e.g., "30cm", "45cm"
    angle: str = "0 deg"                         # e.g., "0 deg", "15 deg tilt", "30 deg skew"
    document_id: str
    release_id: str
    artifact_hash: str                           # SHA-256 of original digital watermarked document
    capture_hash: str                            # SHA-256 of physical camera image file
    image_resolution: str                        # e.g., "1920x1080", "800x1000"
    sync_status: str                             # "OK", "FAILED", "NO_MARK"
    marker_count: int = 0                        # Number of ArUco fiducials detected (0 to 4)
    reprojection_error: float = 0.0              # Mean reprojection error in pixels
    pre_ecc_ber: float = 0.0                     # Raw bit error rate [0.0, 1.0]
    post_ecc_ber: float = 0.0                    # Post-ECC bit error rate [0.0, 1.0]
    ecc_corrected: int = 0                       # Number of byte errata corrected by Reed-Solomon
    watermark_status: str                        # "RECOVERED", "PARTIAL", "NO_SIGNAL", "INVALID"
    recovered_bits: Optional[int] = None         # Total bits recovered
    expected_bits: Optional[int] = None          # Ground truth bit count
    tardos_state: str                            # "ATTRIBUTED", "NO_SIGNAL", "INSUFFICIENT_EVIDENCE", etc.
    candidate: Optional[str] = None              # Accused recipient ID or None
    abstention: bool = False                     # True if system abstained (fail-closed)
    sync_latency_ms: float = 0.0
    demod_latency_ms: float = 0.0
    ecc_latency_ms: float = 0.0
    total_latency_ms: float = 0.0
    notes: str = ""
    telemetry: Dict[str, Any] = Field(default_factory=dict)


class PhysicalValidationReport(BaseModel):
    """Container for batch physical and simulated validation runs."""
    validation_type: Literal["PHYSICAL", "SIMULATED", "COMBINED"]
    execution_timestamp: str
    environment_hardware_available: bool = False
    physical_test_count: int = 0
    simulated_test_count: int = 0
    calibration_set_count: int = 0
    evaluation_set_count: int = 0
    negative_corpus_count: int = 0
    records: List[PhysicalExperimentRecord] = Field(default_factory=list)
    summary_metrics: Dict[str, Any] = Field(default_factory=dict)
