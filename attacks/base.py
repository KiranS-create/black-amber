import os
import time
import hashlib
from enum import Enum
from typing import Optional, Dict, Any, Union, List
from pydantic import BaseModel, Field

class AttackFamily(str, Enum):
    DIGITAL_IMAGE = "DIGITAL_IMAGE"
    DIGITAL_DOCUMENT = "DIGITAL_DOCUMENT"
    PRINT_CAMERA = "PRINT_CAMERA"
    COLLUSION = "COLLUSION"
    INTEGRITY = "INTEGRITY"

class ExecutionMode(str, Enum):
    PHYSICAL = "PHYSICAL"
    SIMULATED = "SIMULATED"

class ArtifactType(str, Enum):
    IMAGE_PNG = "IMAGE_PNG"
    IMAGE_JPEG = "IMAGE_JPEG"
    DOCUMENT_PDF = "DOCUMENT_PDF"
    FINGERPRINT_VECTOR = "FINGERPRINT_VECTOR"
    CRYPTO_PACKAGE = "CRYPTO_PACKAGE"
    LEDGER_EVENT = "LEDGER_EVENT"
    RAW_BYTES = "RAW_BYTES"

class DegradationMetrics(BaseModel):
    psnr: Optional[float] = None
    ssim: Optional[float] = None
    mae: Optional[float] = None
    file_size_ratio: Optional[float] = None
    symbol_survival_rate: Optional[float] = None
    bit_error_rate: Optional[float] = None
    hamming_distance: Optional[int] = None
    normalized_correlation: Optional[float] = None
    additional: Dict[str, Any] = Field(default_factory=dict)

class AttackInput(BaseModel):
    artifact_bytes: bytes
    artifact_type: ArtifactType
    parameters: Dict[str, Any] = Field(default_factory=dict)
    seed: Optional[int] = None
    source_file_path: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class AttackOutput(BaseModel):
    artifact_bytes: bytes
    artifact_type: ArtifactType
    metadata: Dict[str, Any] = Field(default_factory=dict)

class AttackResult(BaseModel):
    attack_id: str
    attack_family: AttackFamily
    attack_name: str
    version: str = "1.0.0"
    input_hash: str
    output_hash: str
    input_type: str
    output_type: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    seed: Optional[int] = None
    tool: str
    tool_version: Optional[str] = None
    physical_or_simulated: str  # "PHYSICAL" or "SIMULATED"
    expected_effect: str
    observed_effect: str
    success: bool
    execution_time_ms: float = 0.0
    notes: Optional[str] = None
    metrics: Optional[DegradationMetrics] = None

class BaseAttack:
    """
    Abstract Base Class for all Adversarial Transformations in SIH26237.
    Enforces standardized execution, input/output hashing, telemetry recording,
    path sanitization, and fail-closed security error handling.
    """
    ATTACK_NAME: str = "base_attack"
    ATTACK_FAMILY: AttackFamily = AttackFamily.DIGITAL_IMAGE
    VERSION: str = "1.0.0"
    TOOL: str = "SIH26237_AttackLab"
    TOOL_VERSION: Optional[str] = "1.0.0"
    MODE: ExecutionMode = ExecutionMode.SIMULATED
    DEFAULT_PARAMETERS: Dict[str, Any] = {}

    def __init__(self):
        pass

    @classmethod
    def sanitize_path(cls, path: str, allowed_root: Optional[str] = None) -> str:
        """
        Sanitize and normalize paths to prevent path traversal attacks.
        """
        normalized = os.path.abspath(os.path.normpath(path))
        if allowed_root:
            allowed = os.path.abspath(os.path.normpath(allowed_root))
            if not normalized.startswith(allowed):
                raise ValueError(f"Path traversal detected: '{path}' outside allowed root '{allowed_root}'")
        return normalized

    @classmethod
    def compute_sha256(cls, data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()

    def apply(
        self,
        input_artifact: Union[bytes, AttackInput],
        parameters: Optional[Dict[str, Any]] = None,
        seed: Optional[int] = None
    ) -> AttackResult:
        """
        Execute the attack deterministically on the input artifact.
        Handles both raw bytes and AttackInput objects.
        """
        start_time = time.perf_counter()

        # Normalize input
        if isinstance(input_artifact, bytes):
            input_bytes = input_artifact
            in_type = self._infer_artifact_type(input_bytes)
            attack_input = AttackInput(
                artifact_bytes=input_bytes,
                artifact_type=in_type,
                parameters=parameters or {},
                seed=seed
            )
        elif isinstance(input_artifact, AttackInput):
            attack_input = input_artifact
            merged_params = dict(attack_input.parameters)
            if parameters:
                merged_params.update(parameters)
            attack_input.parameters = merged_params
            if seed is not None:
                attack_input.seed = seed
        else:
            raise TypeError(f"Expected bytes or AttackInput, got {type(input_artifact).__name__}")

        # Merge with default parameters
        effective_params = dict(self.DEFAULT_PARAMETERS)
        effective_params.update(attack_input.parameters)

        input_hash = self.compute_sha256(attack_input.artifact_bytes)
        attack_id = f"atk_{self.ATTACK_FAMILY.value.lower()}_{self.ATTACK_NAME}_{input_hash[:8]}_{int(time.time()*1000)%1000000}"

        try:
            # Validate input size / malformed check
            if len(attack_input.artifact_bytes) == 0:
                raise ValueError("Input artifact payload is empty (0 bytes).")

            # Execute transform
            output = self._execute_transform(attack_input.artifact_bytes, effective_params, attack_input.seed)
            output_hash = self.compute_sha256(output.artifact_bytes)
            duration_ms = (time.perf_counter() - start_time) * 1000.0

            # Compute degradation metrics where applicable
            metrics = self._compute_metrics(attack_input.artifact_bytes, output.artifact_bytes, effective_params)

            return AttackResult(
                attack_id=attack_id,
                attack_family=self.ATTACK_FAMILY,
                attack_name=self.ATTACK_NAME,
                version=self.VERSION,
                input_hash=input_hash,
                output_hash=output_hash,
                input_type=attack_input.artifact_type.value,
                output_type=output.artifact_type.value,
                parameters=effective_params,
                seed=attack_input.seed,
                tool=self.TOOL,
                tool_version=self.TOOL_VERSION,
                physical_or_simulated=self.MODE.value,
                expected_effect=self._get_expected_effect(effective_params),
                observed_effect=self._get_observed_effect(attack_input.artifact_bytes, output.artifact_bytes, metrics),
                success=True,
                execution_time_ms=round(duration_ms, 3),
                notes=output.metadata.get("notes"),
                metrics=metrics
            )

        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            return AttackResult(
                attack_id=attack_id,
                attack_family=self.ATTACK_FAMILY,
                attack_name=self.ATTACK_NAME,
                version=self.VERSION,
                input_hash=input_hash,
                output_hash=input_hash,
                input_type=attack_input.artifact_type.value,
                output_type=attack_input.artifact_type.value,
                parameters=effective_params,
                seed=attack_input.seed,
                tool=self.TOOL,
                tool_version=self.TOOL_VERSION,
                physical_or_simulated=self.MODE.value,
                expected_effect=self._get_expected_effect(effective_params),
                observed_effect=f"FAILED: {type(e).__name__}: {str(e)}",
                success=False,
                execution_time_ms=round(duration_ms, 3),
                notes="Attack execution encountered an unhandled exception or malformed payload."
            )

    def _execute_transform(
        self,
        artifact_bytes: bytes,
        parameters: Dict[str, Any],
        seed: Optional[int]
    ) -> AttackOutput:
        """To be overridden by subclasses."""
        raise NotImplementedError

    def _infer_artifact_type(self, data: bytes) -> ArtifactType:
        if data.startswith(b"%PDF"):
            return ArtifactType.DOCUMENT_PDF
        elif data.startswith(b"\x89PNG\r\n\x1a\n"):
            return ArtifactType.IMAGE_PNG
        elif data.startswith(b"\xff\xd8\xff"):
            return ArtifactType.IMAGE_JPEG
        return ArtifactType.RAW_BYTES

    def _get_expected_effect(self, parameters: Dict[str, Any]) -> str:
        return f"Apply {self.ATTACK_NAME} with parameters {parameters}"

    def _get_observed_effect(
        self,
        orig_bytes: bytes,
        mod_bytes: bytes,
        metrics: Optional[DegradationMetrics]
    ) -> str:
        ratio = len(mod_bytes) / max(len(orig_bytes), 1)
        return f"Artifact transformed. Length changed from {len(orig_bytes)} to {len(mod_bytes)} bytes (ratio: {ratio:.2f})."

    def _compute_metrics(
        self,
        orig_bytes: bytes,
        mod_bytes: bytes,
        parameters: Dict[str, Any]
    ) -> Optional[DegradationMetrics]:
        ratio = len(mod_bytes) / max(len(orig_bytes), 1)
        return DegradationMetrics(file_size_ratio=round(ratio, 4))
