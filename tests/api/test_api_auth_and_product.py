"""
Unit and integration tests for Authentication, Demo Isolation, Readiness, and Package Verification.
"""

import pytest
from fastapi.testclient import TestClient

from apps.api.config import config
from apps.api.main import app

client = TestClient(app)


def _get_err_msg(res):
    body = res.json()
    if "error" in body and "message" in body["error"]:
        return body["error"]["message"]
    return body.get("detail", "")


def test_auth_status():
    """Verify /auth/status reports public authentication capabilities."""
    res = client.get("/auth/status")
    assert res.status_code == 200
    data = res.json()
    assert "demo_auth_enabled" in data
    assert "version" in data
    assert data["registration_enabled"] is False


def test_login_demo_rejected_when_disabled():
    """admin/admin must be strictly rejected with 401 when DEMO_AUTH_ENABLED=false."""
    orig_state = config.demo_auth_enabled
    try:
        config.demo_auth_enabled = False
        res = client.post("/auth/login", json={
            "username": "admin",
            "password": "admin"
        })
        assert res.status_code == 401
        assert "Invalid credentials" in _get_err_msg(res)
    finally:
        config.demo_auth_enabled = orig_state


def test_login_demo_accepted_when_enabled():
    """admin/admin must be accepted and mapped to demo_tenant when DEMO_AUTH_ENABLED=true."""
    orig_state = config.demo_auth_enabled
    try:
        config.demo_auth_enabled = True
        res = client.post("/auth/login", json={
            "username": "admin",
            "password": "admin"
        })
        assert res.status_code == 200
        data = res.json()
        assert data["token"] == "token_demo_admin"
        assert data["tenant_id"] == "demo_tenant"
        assert data["actor_id"] == "demo_admin"
        assert data["is_demo"] is True
    finally:
        config.demo_auth_enabled = orig_state


def test_login_standard_token():
    """Standard token login resolves proper principal and tenant."""
    res = client.post("/auth/login", json={
        "username": "admin_a",
        "password": "token_admin_tenant_a"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["token"] == "token_admin_tenant_a"
    assert data["tenant_id"] == "tenant_a"
    assert data["role"] == "administrator"
    assert data["is_demo"] is False


def test_login_invalid_credentials_rejected():
    """Invalid credentials must return 401."""
    res = client.post("/auth/login", json={
        "username": "nonexistent_user",
        "password": "wrong_password_1234"
    })
    assert res.status_code == 401
    assert "Invalid credentials" in _get_err_msg(res)


def test_registration_unavailable():
    """Self-registration is rejected with 403 Forbidden in sovereign deployments."""
    res = client.post("/auth/register", json={
        "name": "Jane Examiner",
        "email": "jane@defense.gov",
        "organization": "Naval Intelligence",
        "password": "StrongPassword123!"
    })
    assert res.status_code == 403
    assert _get_err_msg(res) == "Registration unavailable in this deployment."


def test_readiness_check():
    """Readiness probe verifies real dependencies (DB, storage, crypto, orchestrator)."""
    res = client.get("/ready")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "READY"
    assert data["dependencies"]["database"] == "OK"
    assert data["dependencies"]["storage"] == "OK"
    assert data["dependencies"]["orchestrator"] == "OK"
    assert "cryptography" in data["dependencies"]


def test_verify_evidence_package_invalid_archive():
    """Corrupted package returns error without crashing."""
    corrupt_zip = b"PK\x03\x04not_a_valid_zip_archive_payload"
    res = client.post(
        "/evidence/verify-package",
        content=corrupt_zip,
        headers={"Content-Type": "application/octet-stream"}
    )
    assert res.status_code in (400, 415, 422, 500)
