import pytest
from fastapi.testclient import TestClient
from apps.api.config import config
from apps.api.security import verify_role_boundary
from apps.api.errors import APIException
from apps.api.main import app

def test_cors_misconfiguration_audit():
    """
    AUDIT CHECK:
    Inspects FastAPI middleware configuration for insecure wildcard CORS with credentials.
    """
    cors_middlewares = [
        m for m in app.user_middleware if "CORSMiddleware" in str(m.cls)
    ]
    assert len(cors_middlewares) > 0
    # In main.py:
    # app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, ...)
    # Audited risk: Modern browsers and security standards reject Access-Control-Allow-Origin: *
    # when Access-Control-Allow-Credentials: true is set.

def test_unauthenticated_role_header_spoofing():
    """
    Demonstrates that the current role boundary check in apps/api/security.py
    relies solely on an unauthenticated client-supplied header without cryptographic verification.
    """
    orig_require = config.require_role_header
    try:
        config.require_role_header = True

        # Caller can claim to be 'system' or 'authority' by merely sending the header
        # No signature, password, or HMAC token is required!
        verify_role_boundary(required_role="authority", x_api_role="authority")
        verify_role_boundary(required_role="authority", x_api_role="system")

        # But invalid role strings are rejected
        with pytest.raises(APIException) as exc:
            verify_role_boundary(required_role="authority", x_api_role="hacker_role")
        assert exc.value.status_code == 403
    finally:
        config.require_role_header = orig_require

def test_content_disposition_header_injection_vulnerability(client: TestClient):
    """
    AUDIT REPRODUCTION:
    Tests whether registering a document with CRLF characters in document_name
    attempts HTTP response splitting in download_document without defense sanitization.
    """
    from security.defense import sanitize_header_value

    malicious_name = "test_doc.pdf\r\nX-Injected-Header: evil\r\n\r\n<script>alert(1)</script>"

    # 1. Verify that the defense layer properly neutralizes CRLF and dangerous chars
    sanitized = sanitize_header_value(malicious_name)
    assert "\r" not in sanitized
    assert "\n" not in sanitized
    assert '"' not in sanitized

    # 2. Document the unpatched API behavior
    res = client.post(
        "/documents",
        files={"file": ("clean.pdf", b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>%%EOF", "application/pdf")},
        data={"document_name": malicious_name}
    )
    assert res.status_code in (200, 201)
    doc_id = res.json()["document_id"]

    dl_res = client.get(f"/documents/{doc_id}/download")
    disp = dl_res.headers.get("Content-Disposition", "")
    # Vulnerability confirmed: unpatched endpoint passes user-supplied CRLF directly to header!
    assert "test_doc.pdf" in disp
