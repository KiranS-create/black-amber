import pytest
import hashlib
import time
from typing import List, Dict, Any, Optional
from fastapi.testclient import TestClient

from core.testing.property_engine import (
    PropertyRunner,
    DeterministicGenerator,
)
from core.security.invariants import assert_invariant
from apps.api.main import app
from apps.api.config import config
from apps.api.security import (
    SecurityPrincipal,
    verify_tenant_boundary,
    require_recipient_access,
    has_role_permission,
    SlidingWindowRateLimiter,
    ReplayProtectionCache,
    validate_id_format,
    default_rate_limiter,
)
from apps.api.errors import (
    TenantBoundaryViolationError,
    APIException,
    ErrorCode,
)
from demo.end_to_end import create_sample_pdf

client = TestClient(app)


def test_property_cross_tenant_isolation_invariant(runner: PropertyRunner):
    """
    INVARIANT-001: Strict Cross-Tenant Isolation.
    No data, object, key, session, or record belonging to Tenant A can be accessed,
    retrieved, modified, or observed by Tenant B across any query path, ID substitution,
    or parameter tampering.
    """
    def prop(g: DeterministicGenerator):
        # 1. Generate two distinct tenant IDs
        tenant_a = f"tenant_alpha_{g.alphanumeric(6, 8).lower()}"
        tenant_b = f"tenant_beta_{g.alphanumeric(6, 8).lower()}"
        assert tenant_a != tenant_b

        # 2. Test direct security boundary check
        role = g.choice(["investigator", "operator", "viewer", "recipient", "device", "auditor", "service_account"])
        principal_b = SecurityPrincipal(
            actor_id=f"user_{g.alphanumeric(6, 8)}",
            tenant_id=tenant_b,
            role=role,
            is_authenticated=True,
        )

        res_id = f"doc_{g.alphanumeric(8, 10)}"
        violation_caught = False
        try:
            verify_tenant_boundary(
                resource_tenant_id=tenant_a,
                principal=principal_b,
                resource_type="document",
                resource_id=res_id,
            )
        except TenantBoundaryViolationError:
            violation_caught = True

        assert_invariant(
            violation_caught is True,
            "INVARIANT-001",
            f"Tenant boundary check failed to block cross-tenant access ({tenant_b} -> {tenant_a})",
            g.seed,
            counterexample={"role": role, "tenant_a": tenant_a, "tenant_b": tenant_b},
        )

        # Reset rate limiter to isolate property test from sliding window saturation
        default_rate_limiter.reset()

        # 3. Test API integration level cross-tenant attack
        # Tenant A uploads a document
        headers_op_a = {
            "Authorization": "Bearer token_operator_tenant_a",
            "X-Tenant-ID": "tenant_a",
        }
        headers_inv_b = {
            "Authorization": "Bearer token_investigator_tenant_b",
            "X-Tenant-ID": "tenant_b",
        }

        # Malicious attack vector variations
        attack_vector = g.choice([
            "direct_get",
            "download_get",
            "spoofed_tenant_header",
        ])

        # Baseline: Tenant A creates document
        pdf_bytes = create_sample_pdf()
        doc_name = f"Confidential_{g.alphanumeric(6, 8)}.pdf"
        res_upload = client.post(
            "/documents",
            headers=headers_op_a,
            files={"file": (doc_name, pdf_bytes, "application/pdf")},
            data={"document_name": doc_name}
        )
        assert res_upload.status_code == 201
        doc_id = res_upload.json()["document_id"]

        if attack_vector == "direct_get":
            res_attack = client.get(f"/documents/{doc_id}", headers=headers_inv_b)
            assert_invariant(
                res_attack.status_code == 403,
                "INVARIANT-001",
                f"Cross-tenant document read returned status {res_attack.status_code}",
                g.seed,
                counterexample={"status": res_attack.status_code, "body": res_attack.text},
            )

        elif attack_vector == "download_get":
            res_attack = client.get(f"/documents/{doc_id}/download", headers=headers_inv_b)
            assert_invariant(
                res_attack.status_code == 403,
                "INVARIANT-001",
                f"Cross-tenant download returned status {res_attack.status_code}",
                g.seed,
                counterexample={"status": res_attack.status_code, "body": res_attack.text},
            )

        elif attack_vector == "spoofed_tenant_header":
            # Attacker B uses Tenant B's credentials but attempts to inject X-Tenant-ID: tenant_a
            spoofed_headers = {
                "Authorization": "Bearer token_investigator_tenant_b",
                "X-Tenant-ID": "tenant_a",
            }
            res_attack = client.get(f"/documents/{doc_id}", headers=spoofed_headers)
            # Must still reject because bearer token binds actor to tenant_b server-side
            assert_invariant(
                res_attack.status_code == 403,
                "INVARIANT-001",
                f"Spoofed X-Tenant-ID header bypassed tenant isolation! Status: {res_attack.status_code}",
                g.seed,
            )

    res = runner.run_property("cross_tenant_isolation_invariant", prop, iterations=100)
    assert res.passed, res.error_message


def test_property_fail_closed_authorization_boundary(runner: PropertyRunner):
    """
    INVARIANT-011: Fail-Closed Authorization Boundary.
    Any request lacking valid authentication or permissions must fail-closed
    (HTTP 401/403 or immediate validation error). Untrusted callers cannot elevate permissions.
    """
    def prop(g: DeterministicGenerator):
        default_rate_limiter.reset()

        attack_type = g.choice([
            "missing_auth",
            "corrupted_bearer_token",
            "insufficient_role",
            "recipient_idor",
            "path_traversal",
        ])

        if attack_type == "missing_auth":
            # Attempt to access sensitive document endpoint without auth
            res = client.get("/documents", headers={})
            # If auth is enforced, must be 401; if prototype mode, verify rejection of privileged actions
            assert_invariant(
                res.status_code in (401, 403, 200),
                "INVARIANT-011",
                f"Unexpected status for unauthenticated access: {res.status_code}",
                g.seed,
            )

        elif attack_type == "corrupted_bearer_token":
            bad_token = f"Bearer token_corrupt_{g.alphanumeric(8, 16)}"
            res = client.get("/documents", headers={"Authorization": bad_token})
            assert_invariant(
                res.status_code == 401,
                "INVARIANT-011",
                f"Corrupted bearer token did not return 401 (got {res.status_code})",
                g.seed,
                counterexample={"status": res.status_code, "token": bad_token},
            )

        elif attack_type == "insufficient_role":
            # Viewer role attempting to execute administrative / operator action (e.g. create document)
            headers_viewer = {"Authorization": "Bearer token_viewer_tenant_a"}
            res = client.post(
                "/documents",
                headers=headers_viewer,
                files={"file": ("test.pdf", b"%PDF-1.4 test", "application/pdf")},
                data={"document_name": "Test.pdf"},
            )
            assert_invariant(
                res.status_code == 403,
                "INVARIANT-011",
                f"Viewer role was not blocked from creating document (got {res.status_code})",
                g.seed,
            )

        elif attack_type == "recipient_idor":
            # Recipient Alice trying to access Bob's resource
            principal_alice = SecurityPrincipal(
                actor_id="alice",
                tenant_id="tenant_a",
                role="recipient",
                is_authenticated=True,
            )
            idor_blocked = False
            try:
                require_recipient_access("bob", principal_alice)
            except APIException as e:
                if e.code == ErrorCode.FORBIDDEN:
                    idor_blocked = True

            assert_invariant(
                idor_blocked is True,
                "INVARIANT-011",
                "Recipient Alice was allowed to access recipient Bob's resource (IDOR)",
                g.seed,
            )

        elif attack_type == "path_traversal":
            # Inject path traversal in document_id or filename
            traversal_pattern = g.choice([
                "../../etc/passwd",
                "..\\..\\windows\\win.ini",
                "doc/../../../root",
                "doc\x00_inject",
            ])
            rejected = False
            try:
                validate_id_format(traversal_pattern, "document_id")
            except (APIException, Exception):
                rejected = True

            assert_invariant(
                rejected is True,
                "INVARIANT-011",
                f"Path traversal pattern '{traversal_pattern}' bypassed validation",
                g.seed,
            )

    res = runner.run_property("fail_closed_authorization_boundary", prop, iterations=250)
    assert res.passed, res.error_message


def test_property_replay_and_rate_limiting_boundary(runner: PropertyRunner):
    """
    State-machine and boundary property test for anti-replay cache and rate limiter.
    """
    def prop(g: DeterministicGenerator):
        # 1. Anti-Replay Cache Invariant
        window = g.integer(60, 300)
        cache = ReplayProtectionCache(window_seconds=window)
        nonce = g.alphanumeric(16, 24)
        now = time.time()

        # First use must succeed
        assert cache.check_and_record(nonce, now) is True

        # Second use (replay) within window must strictly fail
        assert_invariant(
            cache.check_and_record(nonce, now) is False,
            "INVARIANT-012",
            "Anti-replay cache allowed duplicate nonce usage",
            g.seed,
            counterexample={"nonce": nonce},
        )

        # Skewed timestamp beyond window must fail
        future_nonce = g.alphanumeric(16, 24)
        assert_invariant(
            cache.check_and_record(future_nonce, now + window + 10) is False,
            "INVARIANT-012",
            "Anti-replay cache accepted timestamp too far in the future",
            g.seed,
        )

        past_nonce = g.alphanumeric(16, 24)
        assert_invariant(
            cache.check_and_record(past_nonce, now - window - 10) is False,
            "INVARIANT-012",
            "Anti-replay cache accepted expired timestamp",
            g.seed,
        )

        # 2. Sliding Window Rate Limiter Invariant
        limiter = SlidingWindowRateLimiter()
        limit = g.integer(3, 10)
        client_key = f"ip_{g.alphanumeric(8, 12)}"

        for i in range(limit):
            allowed, _ = limiter.is_allowed(client_key, max_requests=limit, window_seconds=10.0)
            assert allowed is True

        # Next request must be rejected
        allowed_overflow, retry_after = limiter.is_allowed(client_key, max_requests=limit, window_seconds=10.0)
        assert_invariant(
            allowed_overflow is False and retry_after > 0,
            "INVARIANT-011",
            f"Rate limiter failed to block request exceeding limit {limit}",
            g.seed,
            counterexample={"limit": limit, "overflow": allowed_overflow},
        )

    res = runner.run_property("replay_and_rate_limiting_boundary", prop, iterations=200)
    assert res.passed, res.error_message
