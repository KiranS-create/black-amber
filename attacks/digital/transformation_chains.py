import io
import time
from typing import List, Dict, Any, Optional, Tuple
from pydantic import BaseModel, Field

from attacks.base import (
    BaseAttack,
    AttackFamily,
    ArtifactType,
    AttackResult,
    DegradationMetrics,
)
from attacks.digital.document_attacks import (
    PdfRewriteAttack,
    PdfRasterizationAttack,
    PdfMetadataModificationAttack,
    PdfPageReorderingAttack,
    PdfPageExtractionAttack,
    PdfMergeAttack,
    PdfCompressionChangesAttack,
)
from attacks.digital.image_attacks import (
    ResizeAttack,
    JpegRecompressionAttack,
    CropAttack,
    ScreenshotSimulationAttack,
    SaltAndPepperNoiseAttack,
    GaussianNoiseAttack,
    GaussianBlurAttack,
)

class ChainStep(BaseModel):
    step_number: int
    attack_name: str
    input_hash: str
    output_hash: str
    input_size_bytes: int
    output_size_bytes: int
    execution_time_ms: float
    success: bool
    notes: Optional[str] = None

class ChainResult(BaseModel):
    chain_name: str
    total_steps: int
    initial_hash: str
    final_hash: str
    initial_size_bytes: int
    final_size_bytes: int
    total_duration_ms: float
    steps: List[ChainStep] = Field(default_factory=list)
    final_artifact_bytes: bytes = Field(default=b"", repr=False)
    success: bool = True

class TransformationChain:
    """
    Executes a multi-stage sequential attack pipeline against an artifact,
    capturing intermediate outputs, degradation metrics, and telemetry.
    """

    def __init__(self, chain_name: str, attacks: List[Tuple[BaseAttack, Dict[str, Any]]]):
        self.chain_name = chain_name
        self.attacks = attacks

    def execute(self, initial_bytes: bytes, seed: Optional[int] = 42) -> ChainResult:
        start_time = time.perf_counter()
        current_bytes = initial_bytes
        initial_hash = BaseAttack.compute_sha256(initial_bytes)
        steps: List[ChainStep] = []

        for idx, (attack_inst, params) in enumerate(self.attacks):
            step_start = time.perf_counter()
            in_hash = BaseAttack.compute_sha256(current_bytes)
            in_size = len(current_bytes)

            res: AttackResult = attack_inst.apply(current_bytes, parameters=params, seed=seed)
            step_dur = (time.perf_counter() - step_start) * 1000.0

            if not res.success:
                steps.append(ChainStep(
                    step_number=idx + 1,
                    attack_name=attack_inst.ATTACK_NAME,
                    input_hash=in_hash,
                    output_hash=in_hash,
                    input_size_bytes=in_size,
                    output_size_bytes=in_size,
                    execution_time_ms=round(step_dur, 3),
                    success=False,
                    notes=res.observed_effect
                ))
                break

            # Decode output bytes from AttackOutput / execute_transform
            output_obj = attack_inst._execute_transform(current_bytes, params, seed)
            current_bytes = output_obj.artifact_bytes
            out_hash = BaseAttack.compute_sha256(current_bytes)
            out_size = len(current_bytes)

            steps.append(ChainStep(
                step_number=idx + 1,
                attack_name=attack_inst.ATTACK_NAME,
                input_hash=in_hash,
                output_hash=out_hash,
                input_size_bytes=in_size,
                output_size_bytes=out_size,
                execution_time_ms=round(step_dur, 3),
                success=True,
                notes=res.observed_effect
            ))

        total_dur = (time.perf_counter() - start_time) * 1000.0
        final_hash = BaseAttack.compute_sha256(current_bytes)

        return ChainResult(
            chain_name=self.chain_name,
            total_steps=len(steps),
            initial_hash=initial_hash,
            final_hash=final_hash,
            initial_size_bytes=len(initial_bytes),
            final_size_bytes=len(current_bytes),
            total_duration_ms=round(total_dur, 3),
            steps=steps,
            final_artifact_bytes=current_bytes,
            success=all(s.success for s in steps)
        )

# Pre-built standard adversarial transformation chains:

def create_chain_document_raster_jpeg_crop() -> TransformationChain:
    """
    Chain 1: PDF Rewrite -> Rasterization -> Resize (80%) -> JPEG Recompression (Q=75) -> Crop (10%)
    Simulates a digital leak pipeline: user re-saves PDF, rasterizes it, resizes it,
    compresses to JPEG, and crops out header/footer.
    """
    return TransformationChain(
        chain_name="chain_pdf_raster_jpeg_crop",
        attacks=[
            (PdfRewriteAttack(), {}),
            (PdfRasterizationAttack(), {"dpi": 150}),
            (PdfCompressionChangesAttack(), {"compress_streams": True}),
            (PdfMetadataModificationAttack(), {"title": "CLEANSED DOCUMENT"}),
        ]
    )

def create_chain_image_screenshot_noise_compression() -> TransformationChain:
    """
    Chain 2: Screenshot simulation -> Gaussian Blur -> Salt & Pepper Noise -> JPEG Recompression (Q=50) -> Crop
    Simulates an image leak captured from screen, slightly blurred, noisy, and heavily compressed.
    """
    return TransformationChain(
        chain_name="chain_image_screenshot_noise_compression",
        attacks=[
            (ScreenshotSimulationAttack(), {"device_scale": 0.9, "display_gamma": 1.1, "add_border": False}),
            (GaussianBlurAttack(), {"kernel_size": 3, "sigma": 1.0}),
            (SaltAndPepperNoiseAttack(), {"amount": 0.01, "salt_ratio": 0.5}),
            (JpegRecompressionAttack(), {"quality": 50}),
            (CropAttack(), {"crop_fraction": 0.05, "anchor": "center"}),
        ]
    )

def create_chain_multipage_reorder_extract_merge() -> TransformationChain:
    """
    Chain 3: Multi-page Reordering -> Page Extraction -> Prepend Decoy Cover -> Re-serialize
    """
    return TransformationChain(
        chain_name="chain_multipage_reorder_extract_merge",
        attacks=[
            (PdfPageReorderingAttack(), {"mode": "reverse"}),
            (PdfPageExtractionAttack(), {"page_index": 0}),
            (PdfMergeAttack(), {"position": "prepend"}),
            (PdfRewriteAttack(), {}),
        ]
    )
