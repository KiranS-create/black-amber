import pytest
from scripts.deployment.health_check import run_health_check
from scripts.deployment.build_info import collect_build_info

def test_deployment_health_passes():
    report = run_health_check()
    assert report["status"] == "PASS"
    assert report["checks"]["python_runtime"]["status"] == "PASS"
    assert report["checks"]["crypto_primitives"]["status"] == "PASS"
    assert report["checks"]["storage_writable"]["status"] == "PASS"
    assert report["checks"]["api_endpoints"]["status"] == "PASS"

def test_build_info_collection():
    info = collect_build_info()
    assert info["version"] == "1.0.0"
    assert info["offline_ready"] is True
    assert "fastapi" in info["dependency_snapshot"]
    assert "pydantic" in info["dependency_snapshot"]
