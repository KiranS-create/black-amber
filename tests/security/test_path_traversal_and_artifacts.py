import pytest
import os
import base64
from pathlib import Path
from fastapi.testclient import TestClient

from apps.api.config import config
from apps.api.security import sanitize_path, sniff_mime_type, validate_uploaded_payload
from apps.api.errors import APIException
from security.defense import validate_base64_payload, sanitize_header_value, safe_mime_check, SecurityValidationError
from attacks.base import BaseAttack

def test_path_traversal_dot_dot_slash(client: TestClient):
    """Test that relative path traversal payloads are rejected across endpoints."""
    traversal_payloads = [
        "../../../etc/passwd",
        "..\\..\\..\\windows\\win.ini",
        "....//....//etc//shadow",
        "%2e%2e%2f%2e%2e%2fetc%2fpasswd",
        "doc/../../secret.txt",
    ]
    base_dir = config.artifacts_dir
    for payload in traversal_payloads:
        # 1. Direct sanitize_path check
        try:
            resolved = sanitize_path(payload, base_dir)
            # If it resolves, it MUST stay inside base_dir
            assert str(resolved.resolve()).startswith(str(base_dir.resolve()))
        except APIException as e:
            assert e.status_code == 403 or "traversal" in e.message.lower()

        # 2. HTTP endpoint path traversal check
        res = client.get(f"/documents/{payload}/download")
        assert res.status_code in (400, 403, 404)

def test_path_traversal_null_byte_injection():
    """Ensure null byte injection does not bypass filename sanitization."""
    base_dir = config.artifacts_dir
    malicious = "harmless.pdf\x00../../etc/shadow"
    resolved = sanitize_path(malicious, base_dir)
    assert "\x00" not in str(resolved)
    assert str(resolved.resolve()).startswith(str(base_dir.resolve()))

def test_oversized_payload_rejection(client: TestClient):
    """Ensure oversized multipart uploads are rejected with HTTP 413."""
    orig_max = config.max_upload_size_bytes
    try:
        config.max_upload_size_bytes = 1024  # 1 KB limit for testing
        large_payload = b"%PDF-1.4\n" + b"A" * 2048
        res = client.post(
            "/documents",
            files={"file": ("large.pdf", large_payload, "application/pdf")},
            data={"document_name": "Large Doc"}
        )
        assert res.status_code == 413
        data = res.json()
        assert data["error"]["code"] == "PAYLOAD_TOO_LARGE"
    finally:
        config.max_upload_size_bytes = orig_max

def test_inline_base64_payload_size_sanitizer():
    """Ensure defense layer rejects oversized inline base64 before decoding."""
    # Create base64 that exceeds 100 bytes limit
    large_b64 = base64.b64encode(b"X" * 200).decode('utf-8')
    with pytest.raises(SecurityValidationError, match="exceeds maximum allowed size"):
        validate_base64_payload(large_b64, max_size_bytes=100)

def test_malformed_base64_payload_rejected():
    """Ensure invalid characters or corrupt base64 strings are rejected safely."""
    invalid_b64_strings = [
        "not_base64_at_all!@#$",
        "======",
        "A" * 3,  # Invalid padding length
        "abcde====",
    ]
    for b64 in invalid_b64_strings:
        with pytest.raises(SecurityValidationError):
            validate_base64_payload(b64, max_size_bytes=1000)

def test_mime_spoofing_pe_executable_rejected():
    """Reject Windows PE executable header even if declared as application/pdf."""
    pe_header = b"MZ\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00\xff\xff\x00\x00"
    is_valid, detected = safe_mime_check(pe_header, allowed_mimes=["application/pdf"])
    assert is_valid is False
    assert detected == "application/x-dosexec"

def test_mime_spoofing_elf_binary_rejected():
    """Reject ELF binary header even if declared as image/png."""
    elf_header = b"\x7fELF\x02\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    is_valid, detected = safe_mime_check(elf_header, allowed_mimes=["image/png"])
    assert is_valid is False
    assert detected == "application/x-executable"

def test_malformed_pdf_parser_resilience():
    """Ensure severely malformed PDFs fail gracefully without crashing or hanging."""
    from attacks.digital.document_attacks import PdfRewriteAttack
    attack = PdfRewriteAttack()
    corrupt_pdf = b"%PDF-1.7\n%corrupted_xref\nxref\n0 1\n0000000000 65535 f\ntrailer\n<< /Size 1 >>\nstartxref\n99999\n%%EOF"
    res = attack.apply(corrupt_pdf)
    assert res.success is False
    assert "FAILED" in res.observed_effect

def test_malformed_image_resilience():
    """Ensure truncated image headers fail gracefully without unhandled exceptions."""
    from core.watermark.pipeline import ensure_cv2_image
    truncated_jpeg = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00"
    img = ensure_cv2_image(truncated_jpeg)
    # Pipeline handles gracefully by synthesizing fallback canvas
    assert img is not None
    assert img.shape[2] == 3

def test_header_injection_crlf_sanitization():
    """Ensure filenames containing CRLF characters cannot split HTTP headers."""
    malicious_filename = "report.pdf\r\nSet-Cookie: session=attacker_token\r\nX-Injected: true"
    sanitized = sanitize_header_value(malicious_filename)
    assert "\r" not in sanitized
    assert "\n" not in sanitized
    assert "Set-Cookie" in sanitized or "_" in sanitized

def test_artifact_hash_mismatch_detection():
    """Ensure data plane storage detects artifact modification after hashing."""
    from apps.api.storage import FilesystemArtifactStorage
    from apps.api.models import ArtifactType
    from apps.api.errors import ArtifactHashMismatchError

    storage = FilesystemArtifactStorage()
    content = b"ORIGINAL_VALID_CONTENT"
    wrong_hash = "0" * 64

    with pytest.raises(ArtifactHashMismatchError):
        storage.store_artifact(
            data=content,
            artifact_type=ArtifactType.ORIGINAL_DOCUMENT,
            expected_hash=wrong_hash
        )
