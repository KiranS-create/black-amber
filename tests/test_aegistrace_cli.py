"""
Unit & integration tests for unified aegistrace.py CLI.
"""

import sys
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def test_cli_info():
    """Verify aegistrace info command."""
    res = subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "aegistrace.py"), "info"],
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT)
    )
    assert res.returncode == 0
    assert "ML-KEM-768" in res.stdout
    assert "ML-DSA-65" in res.stdout
    assert "AES-256-GCM" in res.stdout


def test_cli_selftest_json():
    """Verify aegistrace selftest --json command."""
    res = subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "aegistrace.py"), "selftest", "--json"],
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT)
    )
    assert res.returncode == 0
    assert "overall_status" in res.stdout
    assert "checks" in res.stdout


def test_cli_demo():
    """Verify aegistrace demo command runs end-to-end without errors."""
    res = subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "aegistrace.py"), "demo"],
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT)
    )
    assert res.returncode == 0
    assert "GOLDEN INVESTIGATION OUTCOME SUMMARY" in res.stdout
    assert "12-Pillar Verification: VERIFIED" in res.stdout


def test_cli_benchmark_api():
    """Verify aegistrace benchmark --suite api command."""
    res = subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "aegistrace.py"), "benchmark", "--suite", "api"],
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT)
    )
    assert res.returncode == 0
    assert "API Security & Zero-Trust Middleware Benchmark" in res.stdout


def test_cli_verify_missing():
    """Verify aegistrace verify with missing path fails gracefully."""
    res = subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "aegistrace.py"), "verify", "non_existent_package_path"],
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT)
    )
    assert res.returncode == 2
    assert "not found" in res.stderr


def test_cli_formats_list():
    """Verify aegistrace formats list displays all registered formats."""
    res = subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "aegistrace.py"), "formats", "list"],
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT)
    )
    assert res.returncode == 0
    assert "AEGISTRACE MULTI-FORMAT FORENSIC REGISTRY" in res.stdout
    assert "PDF" in res.stdout
    assert "DOCX" in res.stdout
    assert "PPTX" in res.stdout
    assert "XLSX" in res.stdout
    assert "PNG" in res.stdout
    assert "JPEG" in res.stdout


def test_cli_formats_inspect_json():
    """Verify aegistrace formats inspect --json inspects an artifact."""
    res = subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "aegistrace.py"), "formats", "inspect", "README.md", "--json"],
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT)
    )
    assert res.returncode == 0
    assert "original_sha256" in res.stdout
    assert "detected_format" in res.stdout
    assert "security_passed" in res.stdout


def test_cli_device_status():
    """Verify aegistrace device status outputs discovery report."""
    res = subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "aegistrace.py"), "device", "status"],
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT)
    )
    assert res.returncode == 0
    assert "DEVICE-IN-THE-LOOP DISCOVERY" in res.stdout
    assert "Active Displays" in res.stdout
    assert "Smartphones Detected" in res.stdout


def test_cli_device_status_json():
    """Verify aegistrace device status --json outputs structured json."""
    res = subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "aegistrace.py"), "device", "status", "--json"],
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT)
    )
    assert res.returncode == 0
    assert '"inventory_id"' in res.stdout
    assert '"cameras"' in res.stdout
    assert '"displays"' in res.stdout


def test_cli_physical_status():
    """Verify aegistrace physical status outputs epistemic state table."""
    res = subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "aegistrace.py"), "physical", "status"],
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT)
    )
    assert res.returncode == 0
    assert "PHYSICAL HARDWARE EPISTEMIC STATUS" in res.stdout
    assert "CAMERA" in res.stdout
    assert "PRINTER" in res.stdout
    assert "SCANNER" in res.stdout
    assert "NOT_VERIFIED" in res.stdout or "UNAVAILABLE" in res.stdout


def test_cli_physical_status_json():
    """Verify aegistrace physical status --json outputs structured json."""
    res = subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "aegistrace.py"), "physical", "status", "--json"],
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT)
    )
    assert res.returncode == 0
    assert '"camera"' in res.stdout
    assert '"printer"' in res.stdout
    assert '"overall"' in res.stdout


def test_cli_physical_validate():
    """Verify aegistrace physical validate runs epistemic guards."""
    res = subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "aegistrace.py"), "physical", "validate"],
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT)
    )
    assert res.returncode == 0
    assert "AUDITING PHYSICAL EPISTEMIC INTEGRITY" in res.stdout
    assert "Camera Absence Invariant Guard" in res.stdout
    assert "HYBRID_VALIDATION" in res.stdout


def test_cli_physical_validate_json():
    """Verify aegistrace physical validate --json outputs structured verdict."""
    res = subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "aegistrace.py"), "physical", "validate", "--json"],
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT)
    )
    assert res.returncode == 0
    assert '"status": "PASS"' in res.stdout
    assert '"epistemic_integrity": "VERIFIED_FAIL_CLOSED"' in res.stdout

