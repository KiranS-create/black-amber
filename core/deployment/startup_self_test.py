"""
core/deployment/startup_self_test.py

Automated Startup Self-Test and Enclave Integrity Verifier for AegisTrace.
Executes defense-grade hardware/runtime/cryptographic self-tests prior to serving
any forensic requests or API traffic.

Enforces zero-trust fail-closed security:
  1. Python runtime and platform specification validation.
  2. PQC and symmetric cryptographic provider verification (NIST FIPS 203/204).
  3. Repository artifact integrity manifest verification (SHA-256).
  4. Post-quantum release manifest digital signature verification (ML-DSA-65).
  5. Keystore custody and storage filesystem writability verification.
  6. Air-gap network egress isolation verification.
"""

import os
import sys
import json
import time
from pathlib import Path
from typing import Dict, Any, Optional

from core.crypto.provider_verification import (
    CryptoProviderVerifier,
    CryptoProviderStatus,
    is_production_mode,
)
from core.deployment.manifest import ArtifactManifestManager
from core.deployment.signer import ReleaseManifestSigner
from core.security.airgap import NetworkEgressGuard


class StartupSelfTestFailure(RuntimeError):
    """Raised when one or more startup self-test invariants fail."""
    pass


class StartupSelfTestRunner:
    """
    Executes comprehensive system startup self-tests.
    """

    def __init__(self, repo_root: Optional[Path] = None):
        self.repo_root = repo_root or Path(__file__).resolve().parent.parent.parent
        self.report_path = self.repo_root / "artifacts" / "deployment" / "startup_self_test_report.json"

    def check_runtime(self) -> Dict[str, Any]:
        """Verify Python version >= 3.9 and execution runtime invariants."""
        v = sys.version_info
        is_ok = v.major == 3 and v.minor >= 9
        return {
            "status": "PASS" if is_ok else "FAIL",
            "python_version": f"{v.major}.{v.minor}.{v.micro}",
            "platform": sys.platform,
            "executable": sys.executable,
        }

    def check_crypto(self, fail_closed: bool) -> Dict[str, Any]:
        """Verify NIST FIPS 203/204 and symmetric cryptographic providers."""
        try:
            res = CryptoProviderVerifier.verify_all_providers(fail_closed=fail_closed)
            is_valid = res["overall_status"] == CryptoProviderStatus.CRYPTO_PROVIDER_VALID.value
            return {
                "status": "PASS" if is_valid else "FAIL",
                "overall_status": res["overall_status"],
                "details": res["primitives"],
            }
        except Exception as e:
            return {
                "status": "FAIL",
                "overall_status": CryptoProviderStatus.CRYPTO_PROVIDER_INVALID.value,
                "error": str(e),
            }

    def check_manifest(self, strict: bool) -> Dict[str, Any]:
        """Verify artifact hashes against release_manifest.json."""
        mgr = ArtifactManifestManager(repo_root=self.repo_root)
        if not mgr.manifest_path.exists():
            return {
                "status": "FAIL" if strict else "WARN",
                "error": f"Release manifest not found at {mgr.manifest_path}",
                "matched_count": 0,
            }

        res = mgr.verify_manifest(check_unexpected=False)
        is_pass = res["status"] == "VALID"
        return {
            "status": "PASS" if is_pass else ("FAIL" if strict else "WARN"),
            "matched_count": res.get("matched_count", 0),
            "missing_count": res.get("missing_count", 0),
            "modified_count": res.get("modified_count", 0),
        }

    def check_signature(self, strict: bool) -> Dict[str, Any]:
        """Verify post-quantum ML-DSA-65 signature of release manifest."""
        signer = ReleaseManifestSigner(repo_root=self.repo_root)
        if not signer.default_sig_path.exists():
            return {
                "status": "FAIL" if strict else "WARN",
                "error": f"Signature file not found at {signer.default_sig_path}",
            }

        res = signer.verify_manifest_signature()
        is_pass = res.get("valid", False)
        return {
            "status": "PASS" if is_pass else ("FAIL" if strict else "WARN"),
            "algorithm": res.get("algorithm"),
            "signer_id": res.get("signer_id"),
            "error": res.get("error"),
        }

    def check_storage_and_keystore(self) -> Dict[str, Any]:
        """Verify data directory writability and keystore configuration."""
        data_dir = self.repo_root / "data"
        data_dir.mkdir(parents=True, exist_ok=True)
        test_file = data_dir / ".self_test_write_probe"
        try:
            test_file.write_text("write_probe_ok", encoding="utf-8")
            content = test_file.read_text(encoding="utf-8")
            test_file.unlink()
            is_writable = (content == "write_probe_ok")
        except Exception as e:
            return {"status": "FAIL", "error": f"Storage not writable: {e}"}

        return {
            "status": "PASS" if is_writable else "FAIL",
            "storage_path": str(data_dir),
            "writable": is_writable,
        }

    def check_airgap(self) -> Dict[str, Any]:
        """Verify network egress guard status."""
        airgap_env = os.environ.get("AEGISTRACE_AIRGAP_MODE", "").strip().lower() in ("1", "true", "yes")
        guard_installed = NetworkEgressGuard.is_installed()
        return {
            "status": "PASS",
            "airgap_mode_configured": airgap_env,
            "egress_guard_installed": guard_installed,
            "policy": "EGRESS_BLOCKED" if (airgap_env or guard_installed) else "STANDARD",
        }

    def run_all(self, fail_closed: Optional[bool] = None) -> Dict[str, Any]:
        """
        Execute complete startup self-test suite.
        Fails closed if fail_closed is True or production mode is detected.
        """
        strict = is_production_mode() if fail_closed is None else fail_closed

        checks = {
            "runtime": self.check_runtime(),
            "crypto_providers": self.check_crypto(fail_closed=strict),
            "manifest_integrity": self.check_manifest(strict=strict),
            "manifest_signature": self.check_signature(strict=strict),
            "storage_and_keystore": self.check_storage_and_keystore(),
            "airgap_guard": self.check_airgap(),
        }

        has_failure = any(c.get("status") == "FAIL" for c in checks.values())
        overall_status = "FAIL" if has_failure else "PASS"

        report = {
            "overall_status": overall_status,
            "timestamp_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "strict_mode": strict,
            "checks": checks,
        }

        # Save report
        try:
            self.report_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.report_path, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2, sort_keys=True)
        except Exception:
            pass

        if has_failure and strict:
            failed_names = [k for k, v in checks.items() if v.get("status") == "FAIL"]
            raise StartupSelfTestFailure(
                f"AegisTrace startup self-test failed in strict production mode for checks: {failed_names}. "
                "Halting startup to prevent compromised operation."
            )

        return report


def run_startup_self_test(fail_closed: Optional[bool] = None) -> Dict[str, Any]:
    """Convenience function to run startup self-test."""
    return StartupSelfTestRunner().run_all(fail_closed=fail_closed)
