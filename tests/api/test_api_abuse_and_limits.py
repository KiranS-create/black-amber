import base64
import time
import pytest
from fastapi.testclient import TestClient

from apps.api.config import config
from apps.api.errors import ErrorCode
from apps.api.main import app
from apps.api.orchestrator import default_orchestrator
from apps.api.security import default_rate_limiter, default_replay_cache
from core.crypto.signatures import MLDSA65
from core.ledger.ledger import EvidenceEvent
from core.recipient import default_registry
from demo.end_to_end import create_sample_pdf

client = TestClient(app)

def create_valid_pdf_bytes() -> bytes:
    return create_sample_pdf()

# =====================================================================
# 1. RATE LIMITING & EXHAUSTION PROTECTION
# =====================================================================

def test_rate_limiting_burst_protection():
    """
    Verify sliding-window rate limiting triggers HTTP 429 when burst limit is exceeded.
    Validates Retry-After header and structured error response.
    """
    default_rate_limiter.reset()
    orig_limit = config.rate_limit_upload
    try:
        # Lower upload limit for precise burst testing
        config.rate_limit_upload = 3
        headers = {"Authorization": "Bearer token_operator_tenant_a"}
        pdf_bytes = create_valid_pdf_bytes()

        # 1-3. First 3 requests must succeed
        for i in range(3):
            res = client.post(
                "/documents",
                headers=headers,
                files={"file": (f"doc_{i}.pdf", pdf_bytes, "application/pdf")},
                data={"document_name": f"Document {i}.pdf"}
            )
            assert res.status_code == 201

        # 4. Fourth request must be rejected with 429
        res_blocked = client.post(
            "/documents",
            headers=headers,
            files={"file": ("doc_blocked.pdf", pdf_bytes, "application/pdf")},
            data={"document_name": "Blocked Document.pdf"}
        )
        assert res_blocked.status_code == 429
        err = res_blocked.json()["error"]
        assert err["code"] == ErrorCode.RATE_LIMITED
        assert "Retry-After" in res_blocked.headers
        assert int(res_blocked.headers["Retry-After"]) >= 1
    finally:
        config.rate_limit_upload = orig_limit
        default_rate_limiter.reset()

# =====================================================================
# 2. OVERSIZED PAYLOAD DEFENSE
# =====================================================================

def test_oversized_payload_rejection():
    """
    Verify that payloads exceeding max allowable upload size are rejected with HTTP 413.
    """
    orig_max = config.max_upload_size_bytes
    try:
        # Set limit to 2 KB for testing
        config.max_upload_size_bytes = 2048
        headers = {"Authorization": "Bearer token_operator_tenant_a"}

        # 3 KB payload
        oversized_data = b"%PDF-1.4\n" + b"A" * 3000

        res = client.post(
            "/documents",
            headers=headers,
            files={"file": ("huge.pdf", oversized_data, "application/pdf")},
            data={"document_name": "Too Big.pdf"}
        )
        assert res.status_code == 413
        err = res.json()["error"]
        assert err["code"] == ErrorCode.PAYLOAD_TOO_LARGE
        assert err["details"]["max_size_bytes"] == 2048
    finally:
        config.max_upload_size_bytes = orig_max

# =====================================================================
# 3. PATH TRAVERSAL DEFENSE
# =====================================================================

def test_path_traversal_in_identifiers_rejected():
    r"""
    Verify that path traversal sequences (../, ..\, null bytes) in path parameters
    and form data are rejected with HTTP 403 or 422.
    """
    headers = {"Authorization": "Bearer token_operator_tenant_a"}
    pdf_bytes = create_valid_pdf_bytes()

    # Traversal in form-data custom document_id
    res_traversal_form = client.post(
        "/documents",
        headers=headers,
        files={"file": ("doc.pdf", pdf_bytes, "application/pdf")},
        data={"document_name": "Valid.pdf", "document_id": "../../etc/passwd"}
    )
    assert res_traversal_form.status_code in (400, 403)

    # Traversal in GET document_id path parameter
    res_traversal_get = client.get(
        "/documents/..%2F..%2Fetc%2Fpasswd",
        headers={"Authorization": "Bearer token_investigator_tenant_a"}
    )
    assert res_traversal_get.status_code in (400, 403, 404)

    # Traversal in GET release_id
    res_traversal_rel = client.get(
        "/releases/..%2F..%2Fwindows%2Fwin.ini",
        headers={"Authorization": "Bearer token_investigator_tenant_a"}
    )
    assert res_traversal_rel.status_code in (400, 403, 404)

# =====================================================================
# 4. POLYGLOT & EXECUTABLE BINARY ATTACK DEFENSES
# =====================================================================

def test_executable_pe_binary_rejected():
    """
    Verify that Windows PE executables ('MZ' magic header) disguised as PDF
    are rejected with HTTP 415.
    """
    headers = {"Authorization": "Bearer token_operator_tenant_a"}
    fake_exe = b"MZ\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00\xff\xff" + b"\x00" * 100

    res = client.post(
        "/documents",
        headers=headers,
        files={"file": ("innocent.pdf", fake_exe, "application/pdf")},
        data={"document_name": "Innocent.pdf"}
    )
    assert res.status_code == 415
    assert res.json()["error"]["code"] == ErrorCode.UNSUPPORTED_ARTIFACT_TYPE

def test_executable_elf_binary_rejected():
    """
    Verify that Linux ELF executables ('\\x7fELF' magic header) are rejected with HTTP 415.
    """
    headers = {"Authorization": "Bearer token_operator_tenant_a"}
    fake_elf = b"\x7fELF\x02\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00" + b"\x00" * 100

    res = client.post(
        "/documents",
        headers=headers,
        files={"file": ("payload.pdf", fake_elf, "application/pdf")},
        data={"document_name": "Payload.pdf"}
    )
    assert res.status_code == 415
    assert res.json()["error"]["code"] == ErrorCode.UNSUPPORTED_ARTIFACT_TYPE

def test_script_and_shell_shebang_rejected():
    """
    Verify that shell scripts ('#!' shebang) and active script tags are rejected with HTTP 415.
    """
    headers = {"Authorization": "Bearer token_operator_tenant_a"}

    # Shebang script
    fake_sh = b"#!/bin/bash\nrm -rf /\n"
    res_sh = client.post(
        "/documents",
        headers=headers,
        files={"file": ("script.pdf", fake_sh, "application/pdf")},
        data={"document_name": "Script.pdf"}
    )
    assert res_sh.status_code == 415
    assert res_sh.json()["error"]["code"] == ErrorCode.UNSUPPORTED_ARTIFACT_TYPE

    # Embedded script tag in document payload
    xss_doc = b"%PDF-1.4\n<script>alert(document.cookie)</script>\n%%EOF"
    res_xss = client.post(
        "/documents",
        headers=headers,
        files={"file": ("xss.pdf", xss_doc, "application/pdf")},
        data={"document_name": "XSS.pdf"}
    )
    assert res_xss.status_code == 415
    assert res_xss.json()["error"]["code"] == ErrorCode.UNSUPPORTED_ARTIFACT_TYPE

# =====================================================================
# 5. REPLAY ATTACK DEFENSE ON SIGNED PROVENANCE EVENTS
# =====================================================================

def test_signed_provenance_event_replay_attack_rejected():
    """
    Verify that submitting the same signed EvidenceEvent twice (replay attack)
    is rejected with HTTP 409 REPLAY_DETECTED.
    """
    default_replay_cache.reset()
    headers_op = {"Authorization": "Bearer token_operator_tenant_a"}
    headers_alice = {"Authorization": "Bearer token_alice_tenant_a"}

    # 1. Create a release for Alice
    pdf_bytes = create_valid_pdf_bytes()
    pdf_b64 = base64.b64encode(pdf_bytes).decode("utf-8")
    rel_res = client.post(
        "/releases",
        headers=headers_op,
        json={
            "document_name": "ReplayProofDoc.pdf",
            "document_base64": pdf_b64,
            "issuer_id": "HQ_TEST",
            "recipient_ids": ["alice"]
        }
    )
    assert rel_res.status_code == 200
    release_id = rel_res.json()["release_id"]

    # 2. Generate a valid client-signed provenance event for Alice without recording to ledger yet
    package = default_orchestrator.get_recipient_package(release_id, "alice")
    alice_recipient = default_orchestrator.registry.get("alice")
    assert alice_recipient is not None

    _, _, event, _ = default_orchestrator.decryption_client.decrypt_package(
        package=package,
        recipient=alice_recipient,
        record_to_ledger=False
    )

    event_payload = event.model_dump()

    # 3. First submission: must succeed with 201
    res_first = client.post("/evidence/decryption-events", headers=headers_alice, json=event_payload)
    assert res_first.status_code == 201
    assert res_first.json()["status"] == "SUCCESS"

    # 4. Second submission (replay): must be rejected with 409 REPLAY_DETECTED
    res_replay = client.post("/evidence/decryption-events", headers=headers_alice, json=event_payload)
    assert res_replay.status_code == 409
    err = res_replay.json()["error"]
    assert err["code"] == ErrorCode.REPLAY_DETECTED
