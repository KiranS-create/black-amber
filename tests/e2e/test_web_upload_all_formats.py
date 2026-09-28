"""
Comprehensive End-to-End Test Suite for Multi-Format Document Upload, Ingestion,
Download, Release Creation, Leak Analysis, and Security Enforcement.

Validates Tier 1 formats (PDF, DOCX, PPTX, XLSX, PNG, JPEG),
Tier 2 formats (TXT, CSV, RTF, ODT), container formats (ZIP, JSON),
and verifies strict rejection of malicious or dangerous payloads (PE, ELF, Scripts).
"""

import base64
import hashlib
import io
import zipfile
import pytest
from fastapi.testclient import TestClient

from apps.api.main import app
from apps.api.config import config
from tests.formats.fixtures import (
    create_minimal_pdf_bytes,
    create_minimal_docx_bytes,
    create_minimal_pptx_bytes,
    create_minimal_xlsx_bytes,
    create_minimal_png_bytes,
    create_minimal_jpeg_bytes,
    create_minimal_txt_bytes,
    create_minimal_csv_bytes,
    create_minimal_rtf_bytes,
    create_minimal_odt_bytes,
)

client = TestClient(app)
AUTH_HEADERS = {"Authorization": "Bearer token_operator_tenant_a"}


def create_minimal_zip_bytes() -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("evidence_metadata.txt", "AegisTrace Sealed Evidence Package")
        zf.writestr("manifest.json", '{"version": "1.0", "status": "VERIFIED"}')
    return buf.getvalue()


def create_minimal_json_bytes() -> bytes:
    return b'{"aegistrace_package": "AUDIT-001", "classification": "TOP_SECRET", "valid": true}'


SUPPORTED_TEST_CASES = [
    ("spec.pdf", "application/pdf", create_minimal_pdf_bytes),
    ("memo.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", create_minimal_docx_bytes),
    ("slides.pptx", "application/vnd.openxmlformats-officedocument.presentationml.presentation", create_minimal_pptx_bytes),
    ("finance.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", create_minimal_xlsx_bytes),
    ("evidence.png", "image/png", create_minimal_png_bytes),
    ("forensic.jpg", "image/jpeg", create_minimal_jpeg_bytes),
    ("intel.txt", "text/plain", create_minimal_txt_bytes),
    ("records.csv", "text/csv", create_minimal_csv_bytes),
    ("report.rtf", "application/rtf", create_minimal_rtf_bytes),
    ("dispatch.odt", "application/vnd.oasis.opendocument.text", create_minimal_odt_bytes),
    ("package.zip", "application/zip", create_minimal_zip_bytes),
    ("manifest.json", "application/json", create_minimal_json_bytes),
]


class TestWebUploadMultiFormat:
    """Tests full lifecycle upload for all supported formats across the web API."""

    @pytest.mark.parametrize("filename,expected_mime,generator", SUPPORTED_TEST_CASES)
    def test_document_upload_and_download_all_formats(self, filename: str, expected_mime: str, generator):
        """Verify each supported format can be uploaded to /documents, retrieved, and downloaded."""
        payload_bytes = generator()
        orig_sha = hashlib.sha256(payload_bytes).hexdigest()

        # 1. Upload via multipart form
        res = client.post(
            "/documents",
            headers=AUTH_HEADERS,
            files={"file": (filename, payload_bytes, expected_mime)},
            data={"document_name": f"Test {filename}"}
        )
        assert res.status_code == 201, f"Failed uploading {filename}: {res.text}"
        data = res.json()
        doc_id = data["document_id"]
        assert data["original_document_hash"] == orig_sha
        assert data["size_bytes"] == len(payload_bytes)
        assert data["document_name"] == f"Test {filename}"

        # 2. Get document metadata
        get_res = client.get(f"/documents/{doc_id}", headers=AUTH_HEADERS)
        assert get_res.status_code == 200
        assert get_res.json()["document_id"] == doc_id

        # 3. Download document and verify byte-for-byte integrity
        down_res = client.get(f"/documents/{doc_id}/download", headers=AUTH_HEADERS)
        assert down_res.status_code == 200
        assert hashlib.sha256(down_res.content).hexdigest() == orig_sha

    @pytest.mark.parametrize("filename,expected_mime,generator", SUPPORTED_TEST_CASES)
    def test_leak_upload_all_formats(self, filename: str, expected_mime: str, generator):
        """Verify each supported format can be ingested into /leaks and listed."""
        payload_bytes = generator()
        orig_sha = hashlib.sha256(payload_bytes).hexdigest()

        # Ingest leak
        res = client.post(
            "/leaks",
            headers=AUTH_HEADERS,
            files={"file": (filename, payload_bytes, expected_mime)}
        )
        assert res.status_code == 201, f"Failed leak upload for {filename}: {res.text}"
        leak_data = res.json()
        leak_id = leak_data["leak_id"]
        assert leak_data["leak_artifact_hash"] == orig_sha

        # Verify listed in GET /leaks
        list_res = client.get("/leaks", headers=AUTH_HEADERS)
        assert list_res.status_code == 200
        leaks = list_res.json()
        assert any(l["leak_id"] == leak_id for l in leaks)

        # Download leak artifact
        down_res = client.get(f"/leaks/{leak_id}/download", headers=AUTH_HEADERS)
        assert down_res.status_code == 200
        assert hashlib.sha256(down_res.content).hexdigest() == orig_sha

    def test_create_release_from_uploaded_document(self):
        """Verify a document uploaded in DOCX format can be used to create a release."""
        docx_bytes = create_minimal_docx_bytes("Classified Release", "Intel Body")
        res = client.post(
            "/documents",
            headers=AUTH_HEADERS,
            files={"file": ("mission.docx", docx_bytes, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
            data={"document_name": "Mission Spec"}
        )
        assert res.status_code == 201
        doc_id = res.json()["document_id"]

        # Fetch recipients
        rec_res = client.get("/recipients", headers=AUTH_HEADERS)
        recipients = [r["recipient_id"] for r in rec_res.json()[:2]]

        # Create release referencing document_id
        rel_res = client.post(
            "/releases",
            headers=AUTH_HEADERS,
            json={
                "document_id": doc_id,
                "recipient_ids": recipients,
                "tardos_enabled": False
            }
        )
        assert rel_res.status_code == 200, f"Release failed: {rel_res.text}"
        rel_data = rel_res.json()
        assert rel_data["document_id"] == doc_id
        assert len(rel_data["packages"]) == len(recipients)

    def test_create_release_inline_base64_multi_format(self):
        """Verify inline document_base64 creation supports formats other than PDF."""
        png_bytes = create_minimal_png_bytes(200, 200)
        png_b64 = base64.b64encode(png_bytes).decode("utf-8")

        rec_res = client.get("/recipients", headers=AUTH_HEADERS)
        recipients = [r["recipient_id"] for r in rec_res.json()[:2]]

        rel_res = client.post(
            "/releases",
            headers=AUTH_HEADERS,
            json={
                "document_name": "Satellite_Image.png",
                "document_base64": png_b64,
                "recipient_ids": recipients,
                "tardos_enabled": False
            }
        )
        assert rel_res.status_code == 200, f"Inline PNG release failed: {rel_res.text}"
        rel_data = rel_res.json()
        assert "Satellite_Image.png" in rel_data["document_name"]


class TestSecurityRejections:
    """Verifies that malicious, disguised, or dangerous files are strictly rejected."""

    def test_reject_pe_executable(self):
        """Reject Windows PE executable (.exe) with MZ header."""
        pe_payload = b"MZ\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00\xff\xff\x00\x00" + b"\x00" * 100
        res = client.post(
            "/documents",
            headers=AUTH_HEADERS,
            files={"file": ("payload.exe", pe_payload, "application/octet-stream")}
        )
        assert res.status_code in [400, 415]
        assert "rejected" in res.text.lower() or "not allowed" in res.text.lower() or "unsupported" in res.text.lower()

    def test_reject_elf_executable(self):
        """Reject Linux ELF binary with \\x7fELF magic."""
        elf_payload = b"\x7fELF\x02\x01\x01\x00" + b"\x00" * 100
        res = client.post(
            "/documents",
            headers=AUTH_HEADERS,
            files={"file": ("malware.elf", elf_payload, "application/x-executable")}
        )
        assert res.status_code in [400, 415]

    def test_reject_script_html_content(self):
        """Reject active script or HTML disguised as document."""
        html_payload = b"<!DOCTYPE html><html><body><script>alert('xss')</script></body></html>"
        res = client.post(
            "/documents",
            headers=AUTH_HEADERS,
            files={"file": ("dangerous.html", html_payload, "text/html")}
        )
        assert res.status_code in [400, 415]
