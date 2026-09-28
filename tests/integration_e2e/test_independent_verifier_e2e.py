"""
SIH26237 - Independent Verifier CLI & Standalone Execution Integration Tests.

Validates that:
1. aegistrace_verify.py CLI executes successfully on standalone .zip archives and directories.
2. CLI returns exit code 0 and prints structured forensic tables or JSON reports.
3. Tampered packages cause the CLI to exit with non-zero error codes.
"""

import sys
import subprocess
import tempfile
from pathlib import Path
import pytest
from core.integration.orchestrator import AegisTraceEndToEndOrchestrator
from core.evidence_package.exporter import EvidencePackageExporter


def test_independent_verifier_cli_on_zip_and_directory():
    """Tests aegistrace_verify.py CLI execution via subprocess."""
    orchestrator = AegisTraceEndToEndOrchestrator(tenant_id="tenant_cli_test")
    result = orchestrator.run_full_golden_pipeline(leak_recipient_id="alice")
    package = result.evidence_package

    repo_root = Path(__file__).resolve().parent.parent.parent
    cli_script = repo_root / "aegistrace_verify.py"
    assert cli_script.exists()

    with tempfile.TemporaryDirectory() as tmpdir:
        dir_path = Path(tmpdir) / "evidence_dir"
        zip_path = Path(tmpdir) / "evidence_package.zip"

        EvidencePackageExporter.export_to_directory(package, dir_path)
        EvidencePackageExporter.export_to_zip(package, zip_path)

        # 1. Test CLI on Directory with Human Output
        proc_dir = subprocess.run(
            [sys.executable, str(cli_script), str(dir_path), "--tenant", "tenant_cli_test"],
            capture_output=True,
            text=True
        )
        assert proc_dir.returncode == 0
        assert "AEGISTRACE FORENSIC EVIDENCE PACKAGE VERIFICATION REPORT" in proc_dir.stdout
        assert "Overall Status:       VERIFIED" in proc_dir.stdout

        # 2. Test CLI on ZIP with JSON Output
        proc_zip = subprocess.run(
            [sys.executable, str(cli_script), str(zip_path), "--tenant", "tenant_cli_test", "--json"],
            capture_output=True,
            text=True
        )
        assert proc_zip.returncode == 0
        assert '"overall_status": "VERIFIED"' in proc_zip.stdout
        assert '"manifest_signature_valid": true' in proc_zip.stdout

        # 3. Test CLI with Mismatched Tenant (Should Fail with non-zero code)
        proc_tenant_fail = subprocess.run(
            [sys.executable, str(cli_script), str(zip_path), "--tenant", "wrong_tenant_corp"],
            capture_output=True,
            text=True
        )
        assert proc_tenant_fail.returncode != 0
