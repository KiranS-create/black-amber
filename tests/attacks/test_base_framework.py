import os
import pytest
from attacks.base import (
    BaseAttack,
    AttackFamily,
    ExecutionMode,
    ArtifactType,
    AttackInput,
    AttackResult,
)
from attacks.digital.image_attacks import JpegRecompressionAttack

def test_attack_result_schema_and_types():
    attack = JpegRecompressionAttack()
    dummy_png = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR" + b"\x00" * 20
    # Malformed decode should return structured failure result, not uncaught crash
    result = attack.apply(dummy_png)
    assert isinstance(result, AttackResult)
    assert result.attack_name == "jpeg_recompression"
    assert result.attack_family == AttackFamily.DIGITAL_IMAGE
    assert result.physical_or_simulated == "SIMULATED"
    assert len(result.input_hash) == 64
    assert result.success is False
    assert "FAILED" in result.observed_effect

def test_path_sanitization_defense():
    # Valid relative path should resolve
    resolved = BaseAttack.sanitize_path("artifacts/attacks", allowed_root="artifacts")
    assert "artifacts" in resolved

    # Directory traversal attack must raise ValueError
    with pytest.raises(ValueError, match="Path traversal detected"):
        BaseAttack.sanitize_path("../../Windows/System32", allowed_root=os.path.abspath("artifacts"))

def test_empty_artifact_payload_fails_gracefully():
    attack = JpegRecompressionAttack()
    result = attack.apply(b"")
    assert result.success is False
    assert "empty" in result.observed_effect.lower()

def test_attack_input_object_support():
    attack = JpegRecompressionAttack()
    # Create valid minimal 1x1 image
    from PIL import Image
    import io
    img = Image.new("RGB", (10, 10), color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    png_bytes = buf.getvalue()

    attack_input = AttackInput(
        artifact_bytes=png_bytes,
        artifact_type=ArtifactType.IMAGE_PNG,
        parameters={"quality": 80},
        seed=123
    )
    result = attack.apply(attack_input)
    assert result.success is True
    assert result.parameters["quality"] == 80
    assert result.seed == 123
    assert result.execution_time_ms > 0
