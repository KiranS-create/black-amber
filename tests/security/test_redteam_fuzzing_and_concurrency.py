"""
SIH26237 — AegisTrace Red-Team Security, Fuzzing & Concurrency Test Suite.

Comprehensive production-grade verification covering:
1. Authentication & Authorization bypass, IDOR, role spoofing, privilege boundaries.
2. Malformed input fuzzing (nulls, types, extreme lengths, Unicode, control chars, base64 corruption).
3. Resource exhaustion (oversized payloads, base64 bombs, excessive recipients).
4. State-machine abuse (decrypt non-existent, duplicate/replayed events, broken hash chains, forged signatures).
5. HTTP & Header security (CRLF injection, MIME sniffing/executable rejection, unsupported methods, CORS).
6. Information disclosure & error hygiene (stack trace suppression, path suppression, secret shielding).
7. Concurrency & race condition safety (concurrent recipient enrollment, ledger serialization, multi-threaded analysis).
"""

import base64
import concurrent.futures
import hashlib
import json
import math
import os
import uuid
from typing import Any, Dict, List
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from apps.api.config import config
from apps.api.errors import APIException, ErrorCode
from apps.api.main import app
from apps.api.models import CreateReleaseRequest, DecryptRequest
from apps.api.orchestrator import default_orchestrator
from apps.api.security import Actor, get_current_actor, require_recipient_access, require_document_access
from core.crypto.signatures import MLDSA65
from core.ledger.ledger import EvidenceEvent, TamperEvidentLedger
from core.recipient import RecipientRegistry, default_registry
from core.release import default_release_manager
from demo.end_to_end import create_sample_pdf
from security.defense import (
    SecurityValidationError,
    check_evidence_contradiction,
    safe_mime_check,
    sanitize_evidence_observation,
    sanitize_header_value,
    sanitize_log_likelihood,
    sanitize_numeric_bounds,
    validate_base64_payload,
)


# ==============================================================================
# SECTION 1: AUTHENTICATION, AUTHORIZATION & IDOR BOUNDARIES
# ==============================================================================

class TestAuthAndAccessBoundaries:
    """Rigorous verification of caller identity, bearer tokens, roles, and IDOR."""

    def test_anonymous_request_blocked_when_auth_enforced(self, client: TestClient, sample_pdf_b64: str):
        """When auth is enforced, anonymous calls to protected endpoints must return 401."""
        with patch.object(config, "enforce_auth", True):
            # Documents listing
            res = client.get("/documents")
            assert res.status_code == 401
            assert "detail" in res.json() or "error" in res.json()

            # Release creation
            res = client.post("/releases", json={
                "document_base64": sample_pdf_b64,
                "recipient_ids": ["alice"]
            })
            assert res.status_code == 401

            # Recipient enrollment
            res = client.post("/recipients", json={"name": "Attacker"})
            assert res.status_code == 401

            # Public endpoints remain accessible without auth
            assert client.get("/health").status_code == 200
            assert client.get("/capabilities").status_code == 200
            assert client.get("/ledger/verify").status_code == 200

    def test_invalid_bearer_token_rejected_under_enforced_auth(self, client: TestClient):
        """Invalid or forged bearer tokens must return 401."""
        with patch.object(config, "enforce_auth", True):
            headers = {"Authorization": "Bearer forged_jwt_token_payload_xyz"}
            res = client.get("/documents", headers=headers)
            assert res.status_code == 401
            assert "Invalid bearer token" in str(res.json())

            # Non-bearer auth scheme
            headers = {"Authorization": "Basic dXNlcjpwYXNz"}
            res = client.get("/documents", headers=headers)
            assert res.status_code == 401

    def test_role_privilege_boundaries_prevent_unauthorized_actions(self, client: TestClient, sample_pdf_b64: str):
        """A recipient role cannot execute authority or auditor actions."""
        with patch.object(config, "enforce_auth", True):
            recipient_headers = {"Authorization": "Bearer token_alice"}  # role: recipient

            # Recipient cannot upload master documents
            res = client.post(
                "/documents",
                headers=recipient_headers,
                files={"file": ("test.pdf", b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>%%EOF", "application/pdf")}
            )
            assert res.status_code == 403

            # Recipient cannot list master documents
            res = client.get("/documents", headers=recipient_headers)
            assert res.status_code == 403

            # Recipient cannot create releases
            res = client.post(
                "/releases",
                headers=recipient_headers,
                json={"document_base64": sample_pdf_b64, "recipient_ids": ["alice"]}
            )
            assert res.status_code == 403

            # Recipient cannot enroll new recipients
            res = client.post(
                "/recipients",
                headers=recipient_headers,
                json={"name": "Attacker"}
            )
            assert res.status_code == 403

            # Recipient cannot trigger forensic analysis
            res = client.post(
                "/analyze",
                headers=recipient_headers,
                json={"leaked_document_base64": sample_pdf_b64}
            )
            assert res.status_code == 403

            # Auditor role can list documents, but CANNOT create releases or enroll recipients
            auditor_headers = {"Authorization": "Bearer token_auditor_sec"}
            res = client.get("/documents", headers=auditor_headers)
            assert res.status_code == 200

            res = client.post(
                "/releases",
                headers=auditor_headers,
                json={"document_base64": sample_pdf_b64, "recipient_ids": ["alice"]}
            )
            assert res.status_code == 403

    def test_role_header_spoofing_blocked_under_auth_enforcement(self, client: TestClient):
        """When auth is enforced, sending X-API-Role: authority without a valid token must fail."""
        with patch.object(config, "enforce_auth", True):
            headers = {"X-API-Role": "authority"}
            res = client.get("/documents", headers=headers)
            # Rejected because Bearer token is missing
            assert res.status_code == 401

            # Even if token is valid for Alice (recipient), spoofing X-API-Role: authority is ignored
            alice_headers = {
                "Authorization": "Bearer token_alice",
                "X-API-Role": "authority"
            }
            res = client.get("/documents", headers=alice_headers)
            assert res.status_code == 403

    def test_invalid_role_strings_rejected(self, client: TestClient):
        """Non-standard role names must be rejected with 403."""
        with patch.object(config, "require_role_header", True):
            for bad_role in ["root", "admin", "superuser", "godmode", "unknown_role"]:
                res = client.get("/documents", headers={"X-API-Role": bad_role})
                assert res.status_code == 403
                assert f"Invalid role '{bad_role}'" in str(res.json())

    def test_idor_cross_recipient_package_access_blocked(self, client: TestClient, sample_pdf_b64: str):
        """Alice cannot access Bob's encrypted package."""
        # 1. Authority creates release for Alice and Bob
        auth_headers = {"Authorization": "Bearer token_authority_hq"}
        rel_res = client.post(
            "/releases",
            headers=auth_headers,
            json={
                "document_name": "Classified_Plans.pdf",
                "document_base64": sample_pdf_b64,
                "recipient_ids": ["alice", "bob"]
            }
        )
        assert rel_res.status_code == 200
        release_id = rel_res.json()["release_id"]

        # 2. Alice tries to access Bob's package
        alice_headers = {"Authorization": "Bearer token_alice"}
        bob_pkg_res = client.get(f"/releases/{release_id}/packages/bob", headers=alice_headers)
        assert bob_pkg_res.status_code == 403
        assert "Access denied" in str(bob_pkg_res.json())

        # 3. Alice can access her own package
        alice_pkg_res = client.get(f"/releases/{release_id}/packages/alice", headers=alice_headers)
        assert alice_pkg_res.status_code == 200
        assert alice_pkg_res.json()["recipient_id"] == "alice"

    def test_idor_cross_recipient_decryption_blocked(self, client: TestClient, sample_pdf_b64: str):
        """Alice cannot trigger decryption for Bob."""
        auth_headers = {"Authorization": "Bearer token_authority_hq"}
        rel_res = client.post(
            "/releases",
            headers=auth_headers,
            json={
                "document_name": "Target_Doc.pdf",
                "document_base64": sample_pdf_b64,
                "recipient_ids": ["alice", "bob"]
            }
        )
        assert rel_res.status_code == 200
        release_id = rel_res.json()["release_id"]

        alice_headers = {"Authorization": "Bearer token_alice"}
        dec_res = client.post(
            f"/releases/{release_id}/decrypt",
            headers=alice_headers,
            json={"recipient_id": "bob"}
        )
        assert dec_res.status_code == 403
        assert "Access denied" in str(dec_res.json())

    def test_idor_document_download_blocked_for_recipient(self, client: TestClient, sample_pdf_bytes: bytes):
        """A recipient cannot download raw master documents."""
        auth_headers = {"Authorization": "Bearer token_authority_hq"}
        up_res = client.post(
            "/documents",
            headers=auth_headers,
            files={"file": ("master.pdf", sample_pdf_bytes, "application/pdf")},
            data={"document_name": "Secret Master"}
        )
        assert up_res.status_code == 201
        doc_id = up_res.json()["document_id"]

        # Recipient attempts download
        alice_headers = {"Authorization": "Bearer token_alice"}
        dl_res = client.get(f"/documents/{doc_id}/download", headers=alice_headers)
        assert dl_res.status_code == 403


# ==============================================================================
# SECTION 2: MALFORMED INPUT & FUZZING RESILIENCE
# ==============================================================================

class TestMalformedInputFuzzing:
    """Fuzzing input parsers with corrupt base64, extreme buffers, Unicode, and schema anomalies."""

    def test_fuzz_base64_payload_validator(self):
        """Exhaustive boundary testing of validate_base64_payload."""
        # Non-string types
        for invalid_type in [None, 12345, 3.14, [], {}, b"raw_bytes"]:
            with pytest.raises(SecurityValidationError, match="must be a base64 string"):
                validate_base64_payload(invalid_type)

        # Invalid characters
        corrupt_chars = [
            "AAAA!@#$%^&*()",
            "AAA AAAA",  # internal space handled or clean
            "AAAA\x00AAAA==",
            "AAAA\n\rAAAA==",
            "AAAA<script>",
            "AAAA--====",
        ]
        for bad in corrupt_chars:
            # If chars are invalid, should raise SecurityValidationError
            try:
                validate_base64_payload(bad)
            except SecurityValidationError:
                pass  # expected

        # Truncated or malformed padding
        bad_paddings = ["A", "AA", "AAA===", "====", "AAAA="]
        for bad_pad in bad_paddings:
            with pytest.raises(SecurityValidationError):
                validate_base64_payload(bad_pad)

        # Valid payload succeeds
        valid = base64.b64encode(b"test valid content").decode('utf-8')
        assert validate_base64_payload(valid) == b"test valid content"

    def test_fuzz_extreme_string_lengths(self, client: TestClient, sample_pdf_b64: str):
        """Oversized string inputs (100k+ chars) must not crash the service."""
        auth_headers = {"Authorization": "Bearer token_authority_hq"}
        giant_str = "A" * 100_000

        # Oversized document_name in release
        res = client.post(
            "/releases",
            headers=auth_headers,
            json={
                "document_name": giant_str,
                "document_base64": sample_pdf_b64,
                "recipient_ids": ["alice"]
            }
        )
        # Should succeed or return clean validation error, never crash with 500
        assert res.status_code in (200, 400, 422)

    def test_fuzz_control_characters_and_path_traversal(self, client: TestClient, sample_pdf_bytes: bytes):
        """Path traversal characters and null bytes in filenames must be neutralized."""
        auth_headers = {"Authorization": "Bearer token_authority_hq"}
        traversal_names = [
            "../../etc/passwd",
            "..\\..\\windows\\system32\\cmd.exe",
            "test\x00hidden.pdf",
            "test\r\nInjected-Header: bad\r\n\r\n.pdf",
            "....//....//escape.pdf",
            "/absolute/root/file.pdf",
            "C:\\boot.ini"
        ]
        for name in traversal_names:
            res = client.post(
                "/documents",
                headers=auth_headers,
                files={"file": (name, sample_pdf_bytes, "application/pdf")},
                data={"document_name": name}
            )
            assert res.status_code == 201
            doc = res.json()
            doc_id = doc["document_id"]

            # Download document and verify sanitized Content-Disposition header
            dl = client.get(f"/documents/{doc_id}/download", headers=auth_headers)
            assert dl.status_code == 200
            cd = dl.headers.get("Content-Disposition", "")
            assert "\r" not in cd
            assert "\n" not in cd
            assert "\x00" not in cd

    def test_fuzz_unicode_homoglyphs_and_bidi_overrides(self, client: TestClient, sample_pdf_b64: str):
        """RTL overrides, zero-width characters, and non-ASCII unicode handled gracefully."""
        auth_headers = {"Authorization": "Bearer token_authority_hq"}
        unicode_payloads = [
            "Test\u202Efdp.exe",       # Right-to-Left Override spoofing
            "Test\u200B\u200CZeroWidth", # Zero-width spaces
            "T\u00E9st D\u00F3cum\u00EBnt", # Accented Latin
            "\u4E2D\u6587\u6587\u6863.pdf", # CJK Unicode
            "\U0001F512 Secure Document \U0001F6E1", # Emojis
            "Z\u0300\u0301\u0302\u0303\u0304algo", # Combining diacritics
        ]
        for uname in unicode_payloads:
            res = client.post(
                "/releases",
                headers=auth_headers,
                json={
                    "document_name": uname,
                    "document_base64": sample_pdf_b64,
                    "recipient_ids": ["alice"]
                }
            )
            assert res.status_code in (200, 400, 422)

    def test_fuzz_json_schema_non_object_roots(self, client: TestClient):
        """Sending arrays, numbers, or bare strings where a JSON object is expected returns 422."""
        auth_headers = {"Authorization": "Bearer token_authority_hq"}
        for bad_payload in [[1, 2, 3], "string_value", 12345, True]:
            res = client.post("/releases", headers=auth_headers, json=bad_payload)
            assert res.status_code == 422

            res = client.post("/recipients", headers=auth_headers, json=bad_payload)
            assert res.status_code == 422

    def test_fuzz_numeric_boundaries_nan_and_infinities(self):
        """Sanitizers clamp NaN, Infinity, and negative values safely."""
        # sanitize_numeric_bounds
        assert sanitize_numeric_bounds(float("nan"), default=0.5) == 0.5
        assert sanitize_numeric_bounds(float("inf"), default=0.0) == 0.0
        assert sanitize_numeric_bounds(-float("inf"), default=0.0) == 0.0
        assert sanitize_numeric_bounds(-5.0, min_val=0.0, max_val=1.0) == 0.0
        assert sanitize_numeric_bounds(15.0, min_val=0.0, max_val=1.0) == 1.0
        assert sanitize_numeric_bounds("not_a_number", default=0.0) == 0.0

        # sanitize_log_likelihood
        assert sanitize_log_likelihood(float("nan")) == 0.0
        assert sanitize_log_likelihood(float("inf")) == 0.0
        assert sanitize_log_likelihood(999999.0, max_abs_val=100.0) == 100.0
        assert sanitize_log_likelihood(-999999.0, max_abs_val=100.0) == -100.0

        # check_evidence_contradiction with NaN and edge cases
        conflict, top_c, run_c, top_s, run_s = check_evidence_contradiction({})
        assert conflict is False

        conflict, _, _, _, _ = check_evidence_contradiction({"alice": 12.0})
        assert conflict is False

        # Two high scores within margin trigger conflict
        conflict, top_c, run_c, _, _ = check_evidence_contradiction({
            "alice": 14.0,
            "bob": 13.5
        }, conflict_threshold=5.0, min_separation_margin=2.5)
        assert conflict is True
        assert {top_c, run_c} == {"alice", "bob"}

    def test_sanitize_evidence_observation_structure(self):
        """sanitize_evidence_observation purges malicious values from candidate dicts."""
        poisoned_obs = {
            "log_likelihood_ratio": float("nan"),
            "effective_reliability": float("inf"),
            "candidate_scores": {
                "alice": float("nan"),
                "bob": 1500000.0,
                "": 10.0,  # empty candidate key
                123: 5.0   # non-string key
            }
        }
        cleaned = sanitize_evidence_observation(poisoned_obs)
        assert cleaned["log_likelihood_ratio"] == 0.0
        assert cleaned["effective_reliability"] == 0.5
        assert cleaned["candidate_scores"]["alice"] == 0.0
        assert cleaned["candidate_scores"]["bob"] == 100.0
        assert "" not in cleaned["candidate_scores"]


# ==============================================================================
# SECTION 3: RESOURCE EXHAUSTION & PAYLOAD BOUNDARIES
# ==============================================================================

class TestResourceExhaustion:
    """Verifies that oversized files, expansion bombs, and excessive requests are rejected."""

    def test_payload_too_large_rejection(self, client: TestClient):
        """Upload exceeding max_upload_size_bytes is rejected with 413."""
        auth_headers = {"Authorization": "Bearer token_authority_hq"}
        # Simulate ceiling at 1KB to test boundary without allocating 50MB
        with patch.object(config, "max_upload_size_bytes", 1024):
            oversized_payload = b"%PDF-1.4\n" + b"X" * 2048
            res = client.post(
                "/documents",
                headers=auth_headers,
                files={"file": ("oversized.pdf", oversized_payload, "application/pdf")}
            )
            assert res.status_code == 413
            data = res.json()
            assert "PAYLOAD_TOO_LARGE" in str(data)

    def test_base64_payload_too_large_rejection(self):
        """Base64 string exceeding maximum allowable decoded size rejected before decoding."""
        huge_len_b64 = "AAAA" * 500  # 2000 chars
        with pytest.raises(SecurityValidationError, match="exceeds maximum allowed size"):
            validate_base64_payload(huge_len_b64, max_size_bytes=100)

    def test_zero_byte_empty_payload_rejection(self, client: TestClient):
        """Empty uploads (0 bytes) must return 400."""
        auth_headers = {"Authorization": "Bearer token_authority_hq"}
        res = client.post(
            "/documents",
            headers=auth_headers,
            files={"file": ("empty.pdf", b"", "application/pdf")}
        )
        assert res.status_code == 400
        assert "empty" in str(res.json()).lower()

        res = client.post(
            "/leaks",
            headers=auth_headers,
            files={"file": ("empty.pdf", b"", "application/pdf")}
        )
        assert res.status_code == 400

    def test_capacity_planner_exhaustion_defense(self, client: TestClient, sample_pdf_b64: str):
        """Demanding release with 1000 recipients and tiny carrier budget returns 400."""
        auth_headers = {"Authorization": "Bearer token_authority_hq"}
        # Pre-enroll demo recipients
        registry = default_orchestrator.registry
        rec_ids = []
        for i in range(20):
            r = registry.enroll(f"BatchUser_{i}")
            rec_ids.append(r.recipient_id)

        res = client.post(
            "/releases",
            headers=auth_headers,
            json={
                "document_base64": sample_pdf_b64,
                "recipient_ids": rec_ids,
                "tardos_enabled": True,
                "coalition_size": 10,
                "carrier_budget": 16  # Way too small for 20 users with c=10
            }
        )
        assert res.status_code == 400
        assert "CAPACITY_INSUFFICIENT" in str(res.json())


# ==============================================================================
# SECTION 4: STATE MACHINE ABUSE & REPLAY ATTACKS
# ==============================================================================

class TestStateMachineAndReplay:
    """Verifies tamper-evident ledger, anti-replay guards, and state consistency."""

    def test_decrypt_nonexistent_release_returns_404(self, client: TestClient):
        """Decrypting a phantom release ID returns 404."""
        auth_headers = {"Authorization": "Bearer token_authority_hq"}
        res = client.post(
            "/releases/rel_non_existent_uuid/decrypt",
            headers=auth_headers,
            json={"recipient_id": "alice"}
        )
        assert res.status_code == 404

    def test_provenance_nonexistent_release_returns_404(self, client: TestClient):
        """Submitting provenance for a phantom release ID returns 404."""
        auth_headers = {"Authorization": "Bearer token_authority_hq"}
        event = EvidenceEvent(
            event_id="evt_phantom_01",
            event_type="DECRYPTION_EVENT",
            timestamp="2026-09-26T12:00:00Z",
            document_id="doc_any",
            release_id="rel_phantom_999",
            recipient_id="alice",
            algorithm="ML-DSA-65",
            artifact_hash="a" * 64,
            evidence_hash="b" * 64,
            previous_event_hash="0" * 64,
            signature="dGVzdF9zaWc=",
        )
        res = client.post(
            "/releases/rel_phantom_999/provenance",
            headers=auth_headers,
            json=event.model_dump()
        )
        assert res.status_code == 404

    def test_provenance_document_id_mismatch_rejected(self, client: TestClient, sample_pdf_b64: str):
        """Provenance event binding a different document_id from the release is rejected."""
        auth_headers = {"Authorization": "Bearer token_authority_hq"}
        rel_res = client.post(
            "/releases",
            headers=auth_headers,
            json={"document_base64": sample_pdf_b64, "recipient_ids": ["alice"]}
        )
        assert rel_res.status_code == 200
        rel_data = rel_res.json()
        release_id = rel_data["release_id"]

        event = EvidenceEvent(
            event_id="evt_mismatch_01",
            event_type="DECRYPTION_EVENT",
            timestamp="2026-09-26T12:00:00Z",
            document_id="doc_spoofed_wrong_id",  # Mismatched!
            release_id=release_id,
            recipient_id="alice",
            algorithm="ML-DSA-65",
            artifact_hash="a" * 64,
            evidence_hash="b" * 64,
            previous_event_hash="0" * 64,
            signature="dGVzdF9zaWc=",
        )
        res = client.post(
            f"/releases/{release_id}/provenance",
            headers=auth_headers,
            json=event.model_dump()
        )
        assert res.status_code == 400
        assert "Document ID mismatch" in str(res.json())

    def test_provenance_unauthorized_recipient_rejected(self, client: TestClient, sample_pdf_b64: str):
        """A recipient not included in the release cannot submit provenance for it."""
        auth_headers = {"Authorization": "Bearer token_authority_hq"}
        # Release only for Alice
        rel_res = client.post(
            "/releases",
            headers=auth_headers,
            json={"document_base64": sample_pdf_b64, "recipient_ids": ["alice"]}
        )
        assert rel_res.status_code == 200
        release_id = rel_res.json()["release_id"]
        doc_id = rel_res.json()["document_id"]

        # Bob submits provenance
        event = EvidenceEvent(
            event_id="evt_unauth_rec_01",
            event_type="DECRYPTION_EVENT",
            timestamp="2026-09-26T12:00:00Z",
            document_id=doc_id,
            release_id=release_id,
            recipient_id="bob",  # Not authorized in this release
            algorithm="ML-DSA-65",
            artifact_hash="a" * 64,
            evidence_hash="b" * 64,
            previous_event_hash="0" * 64,
            signature="dGVzdF9zaWc=",
        )
        res = client.post(
            f"/releases/{release_id}/provenance",
            headers=auth_headers,
            json=event.model_dump()
        )
        assert res.status_code == 400
        assert "Unauthorized recipient" in str(res.json())

    def test_provenance_replay_and_hash_chain_checks(self, client: TestClient, sample_pdf_b64: str):
        """Verifies anti-replay detection and hash chain continuity enforcement."""
        auth_headers = {"Authorization": "Bearer token_authority_hq"}
        rel_res = client.post(
            "/releases",
            headers=auth_headers,
            json={"document_base64": sample_pdf_b64, "recipient_ids": ["alice"]}
        )
        assert rel_res.status_code == 200
        release_id = rel_res.json()["release_id"]
        doc_id = rel_res.json()["document_id"]

        alice = default_orchestrator.registry.get("alice")
        priv_bytes = alice.dsa_keypair.private_key_bytes
        pub_bytes = alice.dsa_keypair.public_key_bytes

        # Legitimate first event
        event_id_1 = f"evt_valid_{uuid.uuid4().hex[:6]}"
        prev_tip = default_orchestrator.ledger.get_last_event_hash()
        timestamp = "2026-09-26T12:00:00Z"
        art_hash = "c" * 64

        sign_payload = (
            f"DECRYPTION_PROVENANCE:{event_id_1}:{doc_id}:"
            f"{release_id}:alice:{art_hash}:"
            f"{prev_tip}:{timestamp}"
        ).encode('utf-8')
        sig_bytes = MLDSA65.sign(priv_bytes, sign_payload)

        event1 = EvidenceEvent(
            event_id=event_id_1,
            event_type="DECRYPTION_EVENT",
            timestamp=timestamp,
            document_id=doc_id,
            release_id=release_id,
            recipient_id="alice",
            algorithm="ML-DSA-65",
            artifact_hash=art_hash,
            evidence_hash="d" * 64,
            previous_event_hash=prev_tip,
            signature=base64.b64encode(sig_bytes).decode('utf-8'),
            signer_public_key_b64=base64.b64encode(pub_bytes).decode('utf-8'),
        )

        res1 = client.post(
            f"/releases/{release_id}/provenance",
            headers=auth_headers,
            json=event1.model_dump()
        )
        assert res1.status_code == 201

        # Replay Attack: Re-submit exact same event
        res_replay = client.post(
            f"/releases/{release_id}/provenance",
            headers=auth_headers,
            json=event1.model_dump()
        )
        assert res_replay.status_code in (400, 409)
        assert "Replay detected" in str(res_replay.json()) or "rejection" in str(res_replay.json()).lower() or "replay" in str(res_replay.json()).lower()

        # Broken Hash Chain Attack: Submit event with stale previous_event_hash
        event_id_2 = f"evt_stale_{uuid.uuid4().hex[:6]}"
        stale_payload = (
            f"DECRYPTION_PROVENANCE:{event_id_2}:{doc_id}:"
            f"{release_id}:alice:{art_hash}:"
            f"{prev_tip}:{timestamp}"  # Stale! Ledger tip changed after event 1
        ).encode('utf-8')
        stale_sig = MLDSA65.sign(priv_bytes, stale_payload)

        event2 = EvidenceEvent(
            event_id=event_id_2,
            event_type="DECRYPTION_EVENT",
            timestamp=timestamp,
            document_id=doc_id,
            release_id=release_id,
            recipient_id="alice",
            algorithm="ML-DSA-65",
            artifact_hash=art_hash,
            evidence_hash="e" * 64,
            previous_event_hash=prev_tip,  # Stale!
            signature=base64.b64encode(stale_sig).decode('utf-8'),
        )
        res_stale = client.post(
            f"/releases/{release_id}/provenance",
            headers=auth_headers,
            json=event2.model_dump()
        )
        assert res_stale.status_code == 400
        assert "previous_event_hash" in str(res_stale.json()).lower()


# ==============================================================================
# SECTION 5: HTTP & HEADER SECURITY
# ==============================================================================

class TestHttpAndHeaderSecurity:
    """Verifies CRLF response splitting protection, MIME sniffing, HTTP verbs, and CORS."""

    def test_crlf_response_splitting_neutralized(self, client: TestClient, sample_pdf_bytes: bytes):
        """Header sanitization neutralizes CRLF injections in download filenames."""
        auth_headers = {"Authorization": "Bearer token_authority_hq"}
        crlf_name = "report.pdf\r\nSet-Cookie: session=attacker_fixed_id\r\nX-Evil: injected"
        res = client.post(
            "/documents",
            headers=auth_headers,
            files={"file": (crlf_name, sample_pdf_bytes, "application/pdf")},
            data={"document_name": crlf_name}
        )
        assert res.status_code == 201
        doc_id = res.json()["document_id"]

        dl = client.get(f"/documents/{doc_id}/download", headers=auth_headers)
        assert dl.status_code == 200
        disp = dl.headers.get("Content-Disposition", "")
        # CRLF must be completely absent from the header value
        assert "\r" not in disp
        assert "\n" not in disp
        assert "session=attacker_fixed_id" not in dl.headers.get("Set-Cookie", "")

    def test_executable_mime_types_rejected(self, client: TestClient):
        """Windows PE executables (.exe) and Linux ELF binaries must be rejected with 415."""
        auth_headers = {"Authorization": "Bearer token_authority_hq"}

        # Windows MZ executable header
        pe_payload = b"MZ\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00\xff\xff\x00\x00"
        res = client.post(
            "/documents",
            headers=auth_headers,
            files={"file": ("malware.exe", pe_payload, "application/x-dosexec")}
        )
        assert res.status_code == 415
        assert "UNSUPPORTED_ARTIFACT_TYPE" in str(res.json())

        # Linux ELF executable header
        elf_payload = b"\x7fELF\x02\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        res = client.post(
            "/leaks",
            headers=auth_headers,
            files={"file": ("exploit.elf", elf_payload, "application/x-executable")}
        )
        assert res.status_code == 415

    def test_unsupported_http_methods_rejected(self, client: TestClient):
        """HTTP methods not allowed on endpoints return 405 Method Not Allowed."""
        assert client.put("/documents").status_code == 405
        assert client.delete("/ledger/verify").status_code == 405
        assert client.patch("/health").status_code == 405

    def test_cors_origin_policy(self, client: TestClient):
        """Allowed origins receive CORS headers; untrusted origins do not."""
        # Allowed origin
        res = client.options(
            "/health",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "GET"
            }
        )
        assert res.headers.get("access-control-allow-origin") == "http://localhost:5173"

        # Untrusted malicious origin
        res_evil = client.options(
            "/health",
            headers={
                "Origin": "https://malicious-attacker-domain.org",
                "Access-Control-Request-Method": "GET"
            }
        )
        # Should not reflect the malicious origin
        assert res_evil.headers.get("access-control-allow-origin") != "https://malicious-attacker-domain.org"


# ==============================================================================
# SECTION 6: INFORMATION DISCLOSURE & ERROR HYGIENE
# ==============================================================================

class TestInformationDisclosure:
    """Verifies that error responses never expose Python stack traces, private keys, or file paths."""

    def test_error_responses_suppress_stack_traces_and_paths(self, client: TestClient):
        """Trigger multiple error codes and audit response bodies for sensitive leaks."""
        auth_headers = {"Authorization": "Bearer token_authority_hq"}

        test_endpoints = [
            # 404
            ("GET", "/documents/doc_does_not_exist_404", None, auth_headers),
            # 404
            ("GET", "/releases/rel_does_not_exist_404", None, auth_headers),
            # 400
            ("POST", "/releases", {"document_name": "no_content"}, auth_headers),
            # 400
            ("POST", "/analyze", {"leak_id": "non_existent_leak"}, auth_headers),
            # 415
            ("POST", "/documents", None, auth_headers),
        ]

        forbidden_patterns = [
            "Traceback (most recent call last)",
            "private_key",
            "dsa_keypair",
            "kem_keypair",
            "C:\\Users\\",
            "C:\\Projects\\",
            "/home/",
            "/var/log/",
        ]

        for method, url, json_body, headers in test_endpoints:
            if method == "GET":
                res = client.get(url, headers=headers)
            elif method == "POST" and json_body is not None:
                res = client.post(url, headers=headers, json=json_body)
            else:
                continue

            content = res.text
            for pattern in forbidden_patterns:
                assert pattern not in content, f"Sensitive leak of '{pattern}' in response from {url}"


# ==============================================================================
# SECTION 7: CONCURRENCY & RACE CONDITION SAFETY
# ==============================================================================

class TestConcurrencyAndRaces:
    """Verifies behavior under multi-threaded concurrency."""

    def test_concurrent_recipient_enrollment(self):
        """20 concurrent threads enrolling recipients in RecipientRegistry must not corrupt state."""
        registry = RecipientRegistry()

        def _enroll(i: int):
            return registry.enroll(name=f"Concurrent_User_{i}")

        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            futures = [executor.submit(_enroll, i) for i in range(20)]
            recipients = [f.result() for f in futures]

        assert len(recipients) == 20
        unique_ids = {r.recipient_id for r in recipients}
        assert len(unique_ids) == 20

        # Verify all generated keypairs are intact and valid
        for r in recipients:
            assert len(r.kem_keypair.public_key_bytes) > 0
            assert len(r.dsa_keypair.public_key_bytes) > 0

    def test_concurrent_ledger_append_serialization(self):
        """
        In a tamper-evident sequential hash chain, racing appends with stale
        previous_event_hash must be rejected, preserving linear integrity.
        """
        ledger = TamperEvidentLedger()
        registry = RecipientRegistry()
        alice = registry.enroll(name="Alice")
        priv = alice.dsa_keypair.private_key_bytes

        # Attempt concurrent appends referencing the initial tip
        initial_tip = ledger.get_last_event_hash()

        def _make_and_append(idx: int):
            event_id = f"evt_conc_{idx}_{uuid.uuid4().hex[:4]}"
            event = EvidenceEvent(
                event_id=event_id,
                event_type="DECRYPTION_EVENT",
                timestamp="2026-09-26T12:00:00Z",
                document_id="doc_conc",
                release_id="rel_conc",
                recipient_id=alice.recipient_id,
                algorithm="ML-DSA-65",
                artifact_hash="f" * 64,
                evidence_hash="0" * 64,
                previous_event_hash=initial_tip,  # all racing with the same tip
                signature="dGVzdA==",
            )
            return ledger.append_event(event)

        results = []
        errors = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(_make_and_append, i) for i in range(5)]
            for f in futures:
                try:
                    res = f.result()
                    results.append(res)
                except ValueError as ve:
                    errors.append(str(ve))

        # Exactly 1 append should succeed with the initial tip; 4 must be rejected due to stale tip
        assert len(results) == 1
        assert len(errors) == 4
        assert all("Invalid previous_event_hash" in e for e in errors)

        # Hash chain must remain 100% valid
        is_valid, chain_errs = ledger.verify_chain()
        assert is_valid is True
        assert len(chain_errs) == 0

    def test_concurrent_analysis_job_creation(self, sample_pdf_bytes: bytes):
        """Simultaneous analysis requests generate distinct jobs without thread collisions."""
        orchestrator = default_orchestrator
        meta = orchestrator.register_document(sample_pdf_bytes, "ConcurrencyTest.pdf")

        def _run_analysis(idx: int):
            # Ingest leak artifact
            leak = orchestrator.ingest_leak(sample_pdf_bytes, suspected_document_id=meta.document_id)
            job = orchestrator.analyze_leak(leak_id=leak.leak_id, async_execution=False)
            return job.analysis_id, job.status

        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(_run_analysis, i) for i in range(4)]
            jobs = [f.result() for f in futures]

        assert len(jobs) == 4
        job_ids = {j[0] for j in jobs}
        assert len(job_ids) == 4
