import hashlib
import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from scripts.deployment.generate_demo_fixtures import generate_fixtures
from apps.api.config import config

def test_demo_fixtures_integrity_and_execution(client: TestClient):
    fixtures_dir = config.data_dir / "demo_fixtures"
    manifest = generate_fixtures(fixtures_dir)

    assert (fixtures_dir / "source_document.pdf").exists()
    assert (fixtures_dir / "bob_leak.pdf").exists()
    assert (fixtures_dir / "tampered_leak.pdf").exists()
    assert (fixtures_dir / "clean_document.pdf").exists()
    assert (fixtures_dir / "manifest.json").exists()

    # Verify manifest hash matching
    for fixture in manifest["fixtures"]:
        file_path = fixtures_dir / fixture["file"]
        assert file_path.exists()
        with open(file_path, "rb") as f:
            actual_hash = hashlib.sha256(f.read()).hexdigest()
        assert actual_hash == fixture["sha256"]

    # Test Bob leak against live API
    with open(fixtures_dir / "bob_leak.pdf", "rb") as f:
        bob_bytes = f.read()

    leak_res = client.post(
        "/leaks",
        files={"file": ("bob_leak.pdf", bob_bytes, "application/pdf")}
    )
    assert leak_res.status_code == 201
    leak_id = leak_res.json()["leak_id"]

    anlz_res = client.post("/analyze", json={
        "leak_id": leak_id,
        "expected_release_id": manifest["release"]["release_id"],
        "async_execution": False
    })
    assert anlz_res.status_code == 200
    result = anlz_res.json()["result"]
    assert result["state"] == "ATTRIBUTED"
    assert result["candidate"]["recipient_id"] == "bob"
    assert result["should_abstain"] is False

    # Test clean document against live API
    with open(fixtures_dir / "clean_document.pdf", "rb") as f:
        clean_bytes = f.read()

    clean_leak_res = client.post(
        "/leaks",
        files={"file": ("clean_document.pdf", clean_bytes, "application/pdf")}
    )
    clean_id = clean_leak_res.json()["leak_id"]

    clean_anlz_res = client.post("/analyze", json={
        "leak_id": clean_id,
        "async_execution": False
    })
    assert clean_anlz_res.status_code == 200
    clean_result = clean_anlz_res.json()["result"]
    assert clean_result["state"] == "NO_SIGNAL"
    assert clean_result["should_abstain"] is True
