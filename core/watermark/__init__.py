"""
SIH26237 - Core Watermark Package
Provides physical and print-camera robust watermarking, geometric synchronization,
Reed-Solomon ECC, carrier modulation, and traceability integration adapters.
"""

from core.watermark.base import (
    WatermarkStatus,
    WatermarkPayload,
    WatermarkObservation,
    WatermarkEncoder,
    WatermarkDecoder,
)
from core.watermark.sync import (
    CanonicalCanvasSpec,
    GeometricSynchronizer,
)
from core.watermark.ecc import (
    WatermarkPayloadCodec,
    compute_doc_release_binding,
    DEFAULT_RS_PARITY_BYTES,
)
from core.watermark.carrier import (
    CarrierStrategy,
    CarrierConfig,
    CarrierModulator,
    compute_image_ssim,
)
from core.watermark.pipeline import (
    PrintCameraWatermarkEncoder,
    PrintCameraWatermarkDecoder,
)
from core.watermark.adapter import (
    WatermarkTraceabilityAdapter,
    PhysicalTraceabilityResult,
)
from core.watermark.schema import (
    PhysicalExperimentRecord,
    PhysicalValidationReport,
)
from core.watermark.dynamic import (
    DynamicWatermarkIdentity,
    derive_dynamic_codeword,
    generate_dynamic_watermark,
    verify_dynamic_watermark_commitment,
    DynamicWatermarkEngine,
    compute_visual_equivalence_metrics,
)

__all__ = [
    # Base
    "WatermarkStatus",
    "WatermarkPayload",
    "WatermarkObservation",
    "WatermarkEncoder",
    "WatermarkDecoder",
    # Synchronization
    "CanonicalCanvasSpec",
    "GeometricSynchronizer",
    # ECC
    "WatermarkPayloadCodec",
    "compute_doc_release_binding",
    "DEFAULT_RS_PARITY_BYTES",
    # Carrier
    "CarrierStrategy",
    "CarrierConfig",
    "CarrierModulator",
    "compute_image_ssim",
    # Pipeline
    "PrintCameraWatermarkEncoder",
    "PrintCameraWatermarkDecoder",
    # Adapter
    "WatermarkTraceabilityAdapter",
    "PhysicalTraceabilityResult",
    # Schema
    "PhysicalExperimentRecord",
    "PhysicalValidationReport",
    # Dynamic
    "DynamicWatermarkIdentity",
    "derive_dynamic_codeword",
    "generate_dynamic_watermark",
    "verify_dynamic_watermark_commitment",
    "DynamicWatermarkEngine",
    "compute_visual_equivalence_metrics",
]

