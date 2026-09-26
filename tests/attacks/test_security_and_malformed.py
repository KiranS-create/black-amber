import pytest
from attacks.base import BaseAttack
from attacks.digital.image_attacks import JpegRecompressionAttack, RotationAttack, CropAttack
from attacks.digital.document_attacks import PdfRewriteAttack
from attacks.collusion.primitives import GenericCollusionAttack

def test_corrupt_pdf_fails_gracefully():
    attack = PdfRewriteAttack()
    corrupt_pdf = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\nCORRUPTED_GIBBERISH_DATA"
    res = attack.apply(corrupt_pdf)
    assert res.success is False
    assert "FAILED" in res.observed_effect

def test_corrupt_image_fails_gracefully():
    attack = JpegRecompressionAttack()
    corrupt_image = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00CORRUPT_BYTES"
    res = attack.apply(corrupt_image)
    assert res.success is False
    assert "FAILED" in res.observed_effect

def test_empty_artifact_fails_gracefully():
    attack = RotationAttack()
    res = attack.apply(b"")
    assert res.success is False
    assert "empty" in res.observed_effect.lower()

def test_path_traversal_sanitization():
    with pytest.raises(ValueError, match="Path traversal detected"):
        BaseAttack.sanitize_path("../../../etc/shadow", allowed_root="C:\\Projects\\SIH26237\\artifacts")

def test_malformed_json_collusion_attack_fails_gracefully():
    attack = GenericCollusionAttack()
    res = attack.apply(b"{ invalid json string: not a valid dictionary ")
    assert res.success is False
    assert "FAILED" in res.observed_effect

def test_collusion_empty_coalition_fails_gracefully():
    attack = GenericCollusionAttack()
    res = attack.apply(b'{"coalition": []}')
    assert res.success is False
    assert "FAILED" in res.observed_effect

def test_extreme_parameter_values():
    attack = CropAttack()
    # Crop fraction 1.0 would crop out entire image; should handle safely
    dummy_img = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR" + b"\x00" * 20
    res = attack.apply(dummy_img, parameters={"crop_fraction": 1.0})
    # Handled without unhandled crash
    assert res.success is False or res.output_hash != ""
