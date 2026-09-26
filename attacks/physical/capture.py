import os
import hashlib
from typing import Optional, Dict, Any, Union
from pydantic import BaseModel, Field

from attacks.base import (
    BaseAttack,
    AttackFamily,
    ExecutionMode,
    ArtifactType,
    AttackInput,
    AttackOutput,
    AttackResult,
    DegradationMetrics,
)

class PhysicalCaptureMetadata(BaseModel):
    printer_model: str = "Unknown Laser Printer"
    paper_type: str = "Standard 80gsm A4"
    camera_device: str = "iPhone 15 Pro / Pixel 8"
    lighting_condition: str = "Ambient Office LED"
    capture_distance_cm: float = 35.0
    capture_angle_deg: float = 15.0
    notes: Optional[str] = None

class PhysicalArtifactCaptureImporter(BaseAttack):
    """
    Physical Artifact Ingestion Service (Level 1).
    Ingests authentic real-world documents printed and captured via smartphone camera or flatbed scanner.
    Records comprehensive physical provenance telemetry and labels outputs as PHYSICAL.
    """
    ATTACK_NAME = "physical_capture_import"
    ATTACK_FAMILY = AttackFamily.PRINT_CAMERA
    MODE = ExecutionMode.PHYSICAL
    TOOL = "PhysicalCaptureIngestionPipeline"
    TOOL_VERSION = "1.0.0"

    def import_physical_capture(
        self,
        captured_artifact_bytes: bytes,
        original_artifact_bytes: Optional[bytes] = None,
        telemetry: Optional[PhysicalCaptureMetadata] = None,
        parameters: Optional[Dict[str, Any]] = None
    ) -> AttackResult:
        """
        Record and ingest a real-world physical capture.
        """
        meta = telemetry or PhysicalCaptureMetadata()
        combined_params = meta.model_dump()
        if parameters:
            combined_params.update(parameters)

        orig_bytes = original_artifact_bytes or captured_artifact_bytes
        orig_hash = self.compute_sha256(orig_bytes)
        cap_hash = self.compute_sha256(captured_artifact_bytes)

        attack_id = f"atk_phys_{cap_hash[:8]}_{os.urandom(3).hex()}"

        return AttackResult(
            attack_id=attack_id,
            attack_family=self.ATTACK_FAMILY,
            attack_name=self.ATTACK_NAME,
            version=self.VERSION,
            input_hash=orig_hash,
            output_hash=cap_hash,
            input_type=self._infer_artifact_type(orig_bytes).value,
            output_type=self._infer_artifact_type(captured_artifact_bytes).value,
            parameters=combined_params,
            seed=None,
            tool=self.TOOL,
            tool_version=self.TOOL_VERSION,
            physical_or_simulated="PHYSICAL",
            expected_effect="Physical print and optical camera re-acquisition",
            observed_effect=(
                f"Ingested physical capture ({len(captured_artifact_bytes)} bytes) from "
                f"device '{meta.camera_device}' printed on '{meta.printer_model}'"
            ),
            success=True,
            execution_time_ms=0.0,
            notes=meta.notes,
            metrics=DegradationMetrics(
                file_size_ratio=round(len(captured_artifact_bytes) / max(len(orig_bytes), 1), 4),
                additional=combined_params
            )
        )

    def _execute_transform(self, artifact_bytes: bytes, parameters: Dict[str, Any], seed: Optional[int]) -> AttackOutput:
        # Standard fallback if called via base apply()
        return AttackOutput(
            artifact_bytes=artifact_bytes,
            artifact_type=self._infer_artifact_type(artifact_bytes),
            metadata={"physical_or_simulated": "PHYSICAL"}
        )
