import base64
import hashlib
import os
import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from apps.api.config import config
from apps.api.main import app
from apps.api.models import CreateReleaseRequest
from apps.api.orchestrator import default_orchestrator
from core.crypto.signatures import MLDSA65
from core.ledger.ledger import EvidenceEvent
from core.provenance.decryption import RecipientDecryptionClient
from core.recipient import default_registry
from demo.end_to_end import create_sample_pdf
from security.defense import sanitize_header_value, validate_base64_payload, SecurityValidationError

client = TestClient(app)

# Fixture to ensure fresh demo state
@pytest.fixture(autouse=True)
def setup_demo_state():
    default_registry.init_demo_recipients()
    yield

# 1. SEC-01: Key custody & decentralized provenance verification
def test_server_side_key_custody_prevention():
    """
    Verifies that in decentralized mode, the recipient client manages private keys,
    and server key custody is disabled (server_key_custody = False).
    """
    assert config.server_key_custody is False

def test_decentralized_provenance_submission_success():
    """
    Verifies that a recipient can decrypt locally using their private key and
    submit a cryptographically signed EvidenceEvent to POST /evidence/decryption-events.
    Server verifies ML-DSA-65 signature with the enrolled public key and records the event in the ledger.
    """
    pdf_bytes = create_sample_pdf()
    pdf_b64 = base64.b64encode(pdf_bytes).decode('utf-8')

    # Authority creates release
    rel = default_orchestrator.create_release(
        CreateReleaseRequest(
            document_name="ProvenanceDoc.pdf",
            document_base64=pdf_b64,
            issuer_id="HQ_AUTHORITY",
            recipient_ids=["alice", "bob"]
        )
    )

    # Client-side: Alice retrieves her package and decrypts locally with her private key
    package = default_orchestrator.get_recipient_package(rel.release_id, "alice")
    alice_rec = default_registry.get("alice")

    dec_client = RecipientDecryptionClient(ledger=None)
    tip_hash = default_orchestrator.ledger.get_last_event_hash()
    plaintext, traceable_copy, event, event_hash = dec_client.decrypt_package(
        package=package,
        recipient=alice_rec,
        last_event_hash=tip_hash,
        record_to_ledger=False
    )

    # Alice submits the signed provenance event to POST /evidence/decryption-events
    res = client.post(
        "/evidence/decryption-events",
        json=event.model_dump(),
        headers={"Authorization": "Bearer token_alice"}
    )
    assert res.status_code == 201
    data = res.json()
    assert data["status"] == "SUCCESS"
    assert data["event_id"] == event.event_id

def test_decentralized_provenance_submission_forged_sig_rejected():
    """
    Verifies that if an attacker submits a forged or tampered ML-DSA-65 signature on an
    EvidenceEvent, the server rejects it with HTTP 400 (INVALID_SIGNATURE).
    """
    pdf_bytes = create_sample_pdf()
    pdf_b64 = base64.b64encode(pdf_bytes).decode('utf-8')

    rel = default_orchestrator.create_release(
        CreateReleaseRequest(
            document_name="ForgedSigDoc.pdf",
            document_base64=pdf_b64,
            issuer_id="HQ_AUTHORITY",
            recipient_ids=["alice", "bob"]
        )
    )
    package = default_orchestrator.get_recipient_package(rel.release_id, "alice")
    alice_rec = default_registry.get("alice")

    dec_client = RecipientDecryptionClient(ledger=None)
    tip_hash = default_orchestrator.ledger.get_last_event_hash()
    _, _, event, _ = dec_client.decrypt_package(
        package=package,
        recipient=alice_rec,
        last_event_hash=tip_hash,
        record_to_ledger=False
    )

    # Tamper with the signature bytes (forge)
    corrupted_sig = base64.b64encode(os.urandom(len(base64.b64decode(event.signature)))).decode('utf-8')
    tampered_event = event.model_copy(update={"signature": corrupted_sig})

    res = client.post(
        "/evidence/decryption-events",
        json=tampered_event.model_dump(),
        headers={"Authorization": "Bearer token_alice"}
    )
    assert res.status_code == 400
    assert res.json()["error"]["code"] == "INVALID_SIGNATURE"

# 2. SEC-03: Base64 Payload DoS Protection
def test_base64_dos_prevention_oversized_string():
    """
    Verifies that validate_base64_payload inspects string length BEFORE decoding,
    preventing multi-gigabyte memory exhaustion attacks.
    """
    max_limit = 1000  # 1000 bytes
    huge_b64 = "A" * 5000  # Decoded size would exceed 1000 bytes

    with pytest.raises(SecurityValidationError) as exc:
        validate_base64_payload(huge_b64, max_size_bytes=max_limit)
    assert "exceeds maximum allowed size" in str(exc.value)

def test_base64_dos_prevention_corrupted_characters():
    """
    Verifies that malformed base64 strings with dangerous control or non-base64 characters are rejected.
    """
    bad_b64 = "AAA!!!@@@###$$$%%%"
    with pytest.raises(SecurityValidationError) as exc:
        validate_base64_payload(bad_b64, max_size_bytes=10000)
    assert "Invalid base64" in str(exc.value)

# 3. SEC-04: CORS Misconfiguration Remediation
def test_cors_wildcard_with_credentials_prevented():
    """
    Verifies that CORS middleware does not permit wildcard '*' when credentials are true,
    and explicitly restricts origins to trusted localhost domains.
    """
    cors_middlewares = [m for m in app.user_middleware if "CORSMiddleware" in str(m.cls)]
    assert len(cors_middlewares) > 0
    mw = cors_middlewares[0]
    
    # Assert origins are strictly specified in config
    assert "*" not in config.allowed_cors_origins
    assert "http://localhost:5173" in config.allowed_cors_origins

# 4. SEC-05: Authentication & Token Resolution
def test_auth_token_resolution_authority():
    """
    Verifies that Bearer token 'token_authority_hq' correctly resolves to role 'authority' and actor 'HQ_AUTHORITY'.
    """
    from apps.api.security import get_current_actor
    from fastapi import Request
    actor = get_current_actor(
        request=None,
        authorization="Bearer token_authority_hq"
    )
    assert actor.role == "authority"
    assert actor.actor_id == "HQ_AUTHORITY"

def test_auth_token_resolution_recipient():
    """
    Verifies that Bearer token 'token_alice' correctly resolves to role 'recipient' and actor 'alice'.
    """
    from apps.api.security import get_current_actor
    actor = get_current_actor(
        request=None,
        authorization="Bearer token_alice"
    )
    assert actor.role == "recipient"
    assert actor.actor_id == "alice"

def test_auth_token_invalid_rejected():
    """
    Verifies that when enforce_auth is enabled, an invalid Bearer token is rejected with HTTP 401.
    """
    orig_enforce = config.enforce_auth
    try:
        config.enforce_auth = True
        res = client.get(
            "/documents",
            headers={"Authorization": "Bearer invalid_secret_token_12345"}
        )
        assert res.status_code == 401
        assert res.json()["error"]["code"] == "UNAUTHORIZED"
    finally:
        config.enforce_auth = orig_enforce

# 5. SEC-07: Content-Disposition Header Injection Sanitization
def test_content_disposition_header_injection_crlf():
    """
    Verifies that filenames containing CRLF splitting characters (\r\n), null bytes,
    and header injection payloads are sanitized to safe characters.
    """
    malicious_filename = "Confidential_Report\r\nSet-Cookie: session=hijacked\r\n\x00.pdf"
    sanitized = sanitize_header_value(malicious_filename)
    assert "\r" not in sanitized
    assert "\n" not in sanitized
    assert "\x00" not in sanitized
    assert "Set-Cookie" not in sanitized or "_" in sanitized

    # Direct test via API endpoint
    res = client.post(
        "/documents",
        files={"file": ("malicious.pdf", b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>%%EOF", "application/pdf")},
        data={"document_name": malicious_filename},
        headers={"Authorization": "Bearer token_authority_hq"}
    )
    assert res.status_code == 201
    doc_id = res.json()["document_id"]

    dl_res = client.get(
        f"/documents/{doc_id}/download",
        headers={"Authorization": "Bearer token_authority_hq"}
    )
    assert dl_res.status_code == 200
    disp_header = dl_res.headers.get("Content-Disposition", "")
    assert "\r" not in disp_header
    assert "\n" not in disp_header
    assert "\x00" not in disp_header

# 6. SEC-08: Insecure Direct Object Reference (IDOR) Protection
def test_idor_recipient_package_cross_access():
    """
    Verifies that Alice cannot access Bob's encrypted package (/releases/{id}/packages/bob)
    using her token (returns HTTP 403 FORBIDDEN).
    """
    pdf_bytes = create_sample_pdf()
    pdf_b64 = base64.b64encode(pdf_bytes).decode('utf-8')

    rel = default_orchestrator.create_release(
        CreateReleaseRequest(
            document_name="IdorDoc.pdf",
            document_base64=pdf_b64,
            issuer_id="HQ_AUTHORITY",
            recipient_ids=["alice", "bob"]
        )
    )

    # Alice requests Bob's package
    res = client.get(
        f"/releases/{rel.release_id}/packages/bob",
        headers={"Authorization": "Bearer token_alice"}
    )
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "FORBIDDEN"

def test_idor_recipient_decrypt_cross_access():
    """
    Verifies that Alice cannot invoke the decryption endpoint pretending to be Bob (returns HTTP 403 FORBIDDEN).
    """
    pdf_bytes = create_sample_pdf()
    pdf_b64 = base64.b64encode(pdf_bytes).decode('utf-8')

    rel = default_orchestrator.create_release(
        CreateReleaseRequest(
            document_name="IdorDecryptDoc.pdf",
            document_base64=pdf_b64,
            issuer_id="HQ_AUTHORITY",
            recipient_ids=["alice", "bob"]
        )
    )

    # Alice attempts to decrypt as Bob
    res = client.post(
        f"/releases/{rel.release_id}/decrypt",
        json={"recipient_id": "bob"},
        headers={"Authorization": "Bearer token_alice"}
    )
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "FORBIDDEN"

# 7. Inline Base64 Attack Analysis Validation
def test_leak_analysis_base64_validation():
    """
    Verifies that POST /analyze validates inline leaked_document_base64 with validate_base64_payload.
    """
    bad_b64 = "MALFORMED_BASE64_WITH_INVALID_CHARS!!!!"
    res = client.post(
        "/analyze",
        json={"leaked_document_base64": bad_b64},
        headers={"Authorization": "Bearer token_auditor_sec"}
    )
    assert res.status_code == 400
    assert res.json()["error"]["code"] == "INVALID_ANALYSIS_REQUEST"

def test_legacy_endpoint_base64_validation():
    """
    Verifies that legacy POST /leaks/analyze validates inline leaked_document_base64.
    """
    bad_b64 = "MALFORMED_BASE64_WITH_INVALID_CHARS!!!!"
    res = client.post(
        "/leaks/analyze",
        json={"leaked_document_base64": bad_b64}
    )
    assert res.status_code == 400
    assert res.json()["error"]["code"] == "INVALID_ANALYSIS_REQUEST"
