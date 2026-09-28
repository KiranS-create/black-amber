"""
tests/deployment/test_supply_chain_attacks.py

Comprehensive Supply-Chain and Air-Gap Attack Vector Test Suite for AegisTrace.
Verifies defense-grade security controls against 15 distinct supply-chain attack vectors:
  1. Compromised dependency wheel hash mismatch rejection.
  2. Typosquatting / unpinned dependency detection in inventory resolver.
  3. Silent substitution of ML-KEM-768 with mock provider (fails closed).
  4. Silent substitution of ML-DSA-65 with dummy provider (fails closed).
  5. Insecure fallback bypass prevention in production mode.
  6. Source file tampering detected by artifact integrity manifest.
  7. Missing security-sensitive file detected by integrity manifest.
  8. Backdoor injected file detected by integrity manifest.
  9. Tampered manifest root digest rejected by signature verification.
  10. Corrupted ML-DSA-65 signature bytes rejected.
  11. Tampered wheel in offline wheelhouse detected.
  12. Outbound network egress blocked in airgap mode.
  13. External DNS resolution blocked in airgap mode.
  14. Secret and credential scanner detects committed private keys.
  15. Version downgrade attack prevented by upgrade controller.
"""

import os
import json
import socket
import tempfile
from pathlib import Path
import pytest

from core.crypto.kem import MLKEM768, DevFallbackKEMProvider, get_default_kem_provider
from core.crypto.signatures import MLDSA65, DevFallbackDSAProvider, get_default_dsa_provider
from core.crypto.provider_verification import (
    CryptoProviderVerifier,
    CryptoProviderStatus,
    CryptoSupplyChainError,
)
from core.deployment.inventory import DependencyInventoryResolver, DependencyType
from core.deployment.manifest import ArtifactManifestManager
from core.deployment.signer import ReleaseManifestSigner, DEFAULT_SIGNER_ID
from core.deployment.offline_bundle import OfflineBundleManager
from core.security.airgap import enforce_airgap, AirgapViolationError, NetworkEgressGuard
from core.deployment.secret_scanner import SecretScanner
from core.deployment.versioning import SemVer
from core.deployment.upgrade import UpgradeSafetyController, UpgradeSecurityError


# --- Test 1: Compromised dependency wheel hash mismatch rejection ---
def test_attack_compromised_dependency_wheel_hash_mismatch(tmp_path):
    mgr = OfflineBundleManager()
    wheel_file = tmp_path / "fastapi-0.115.6-py3-none-any.whl"
    wheel_file.write_bytes(b"MALICIOUS_COMPROMISED_BYTECODE_INJECTION")

    res = mgr.verify_wheelhouse(tmp_path)
    assert res["status"] in ("CORRUPTED", "INCOMPLETE")
    assert res["corrupted_count"] >= 1
    assert any(c["filename"] == "fastapi-0.115.6-py3-none-any.whl" for c in res["corrupted"])


# --- Test 2: Typosquatting / unpinned dependency detection in inventory resolver ---
def test_attack_unpinned_or_typosquatting_detection():
    resolver = DependencyInventoryResolver()
    report = resolver.resolve_inventory()
    # Check that crypto-sensitive packages are strictly identified and version-pinned
    crypto_pkgs = [p for p in report["packages"] if p["is_crypto_sensitive"]]
    assert len(crypto_pkgs) >= 4
    for cp in crypto_pkgs:
        assert cp["name"] in report["summary"]["crypto_sensitive_packages"]
        assert cp["pinned_version"] is not None


# --- Test 3: Silent substitution of ML-KEM-768 with mock provider (fails closed) ---
def test_attack_ml_kem_mock_substitution_fails_closed(monkeypatch):
    monkeypatch.setattr(MLKEM768, "get_provider", lambda: DevFallbackKEMProvider())
    res = CryptoProviderVerifier.verify_ml_kem_768()
    assert res["status"] == CryptoProviderStatus.CRYPTO_PROVIDER_INVALID.value
    assert "Mock lattice fallback detected" in res["error"]

    with pytest.raises(CryptoSupplyChainError):
        CryptoProviderVerifier.verify_all_providers(fail_closed=True)


# --- Test 4: Silent substitution of ML-DSA-65 with dummy provider (fails closed) ---
def test_attack_ml_dsa_dummy_substitution_fails_closed(monkeypatch):
    monkeypatch.setattr(MLDSA65, "get_provider", lambda: DevFallbackDSAProvider())
    res = CryptoProviderVerifier.verify_ml_dsa_65()
    assert res["status"] == CryptoProviderStatus.CRYPTO_PROVIDER_INVALID.value
    assert "Mock signature fallback detected" in res["error"]

    with pytest.raises(CryptoSupplyChainError):
        CryptoProviderVerifier.verify_all_providers(fail_closed=True)


# --- Test 5: Insecure fallback bypass prevention in production mode ---
def test_attack_insecure_fallback_bypass_in_production(monkeypatch):
    monkeypatch.setenv("SIH26237_ENV", "production")
    monkeypatch.setattr("core.crypto.kem._OQS_AVAILABLE", False)
    monkeypatch.setattr("core.crypto.kem._KYBER_PY_AVAILABLE", False)

    with pytest.raises(RuntimeError, match="FATAL \\[ML-KEM-768\\]"):
        get_default_kem_provider()


# --- Test 6: Source file tampering detected by artifact integrity manifest ---
def test_attack_source_file_tampering_detected(tmp_path):
    mgr = ArtifactManifestManager(repo_root=tmp_path)
    fake_core = tmp_path / "core"
    fake_core.mkdir(parents=True)
    fake_file = fake_core / "security.py"
    fake_file.write_text("VALID_SOURCE_CODE = True\n", encoding="utf-8")

    manifest = mgr.generate_manifest(output_path=tmp_path / "manifest.json")
    assert manifest["file_count"] == 1

    # Tamper with file
    fake_file.write_text("BACKDOOR_INJECTED = True\n", encoding="utf-8")

    ver = mgr.verify_manifest(manifest_path=tmp_path / "manifest.json")
    assert ver["status"] == "INVALID"
    assert ver["modified_count"] == 1
    assert ver["modified"][0]["path"] == "core/security.py"


# --- Test 7: Missing security-sensitive file detected by integrity manifest ---
def test_attack_missing_file_detected(tmp_path):
    mgr = ArtifactManifestManager(repo_root=tmp_path)
    fake_core = tmp_path / "core"
    fake_core.mkdir(parents=True)
    fake_file = fake_core / "crypto.py"
    fake_file.write_text("CRYPTO_CODE = True\n", encoding="utf-8")

    manifest = mgr.generate_manifest(output_path=tmp_path / "manifest.json")
    assert manifest["file_count"] == 1

    # Delete file
    fake_file.unlink()

    ver = mgr.verify_manifest(manifest_path=tmp_path / "manifest.json")
    assert ver["status"] == "INVALID"
    assert ver["missing_count"] == 1
    assert "core/crypto.py" in ver["missing"]


# --- Test 8: Backdoor injected file detected by integrity manifest ---
def test_attack_backdoor_extra_file_detected(tmp_path):
    mgr = ArtifactManifestManager(repo_root=tmp_path)
    fake_core = tmp_path / "core"
    fake_core.mkdir(parents=True)
    fake_file = fake_core / "approved.py"
    fake_file.write_text("APPROVED = True\n", encoding="utf-8")

    manifest = mgr.generate_manifest(output_path=tmp_path / "manifest.json")
    assert manifest["file_count"] == 1

    # Inject unauthorized file
    injected = fake_core / "backdoor_exfiltrate.py"
    injected.write_text("import socket; # backdoor\n", encoding="utf-8")

    ver = mgr.verify_manifest(manifest_path=tmp_path / "manifest.json", check_unexpected=True)
    assert ver["status"] == "INVALID"
    assert ver["unexpected_count"] == 1
    assert "core/backdoor_exfiltrate.py" in ver["unexpected"]


# --- Test 9: Tampered manifest root digest rejected by signature verification ---
def test_attack_tampered_manifest_digest_rejected(tmp_path):
    manifest_p = tmp_path / "release_manifest.json"
    sig_p = tmp_path / "release_manifest.sig.json"

    manifest_data = {
        "format_version": "1.0.0",
        "release_id": "v1.0.0",
        "manifest_root_digest": "aaaa" * 16,
        "files": [],
    }
    manifest_p.write_text(json.dumps(manifest_data), encoding="utf-8")

    signer = ReleaseManifestSigner(repo_root=tmp_path)
    signer.sign_manifest(manifest_path=manifest_p, output_sig_path=sig_p)

    # Tamper with manifest root digest
    manifest_data["manifest_root_digest"] = "bbbb" * 16
    manifest_p.write_text(json.dumps(manifest_data), encoding="utf-8")

    res = signer.verify_manifest_signature(manifest_path=manifest_p, sig_path=sig_p)
    assert res["valid"] is False
    assert "digest mismatch" in res["error"]


# --- Test 10: Corrupted ML-DSA-65 signature bytes rejected ---
def test_attack_corrupted_signature_bytes_rejected(tmp_path):
    manifest_p = tmp_path / "release_manifest.json"
    sig_p = tmp_path / "release_manifest.sig.json"

    manifest_data = {
        "format_version": "1.0.0",
        "release_id": "v1.0.0",
        "manifest_root_digest": "cccc" * 16,
        "files": [],
    }
    manifest_p.write_text(json.dumps(manifest_data), encoding="utf-8")

    signer = ReleaseManifestSigner(repo_root=tmp_path)
    signer.sign_manifest(manifest_path=manifest_p, output_sig_path=sig_p)

    # Corrupt signature bytes in json
    with open(sig_p, "r", encoding="utf-8") as f:
        sig_doc = json.load(f)

    raw_sig = bytearray(bytes.fromhex(sig_doc["signature_hex"]))
    raw_sig[10] ^= 0xAA
    sig_doc["signature_hex"] = raw_sig.hex()

    with open(sig_p, "w", encoding="utf-8") as f:
        json.dump(sig_doc, f)

    res = signer.verify_manifest_signature(manifest_path=manifest_p, sig_path=sig_p)
    assert res["valid"] is False


# --- Test 11: Tampered wheel in offline wheelhouse detected ---
def test_attack_tampered_wheel_detected(tmp_path):
    wheelhouse = tmp_path / "wheelhouse"
    wheelhouse.mkdir()
    tampered_wheel = wheelhouse / "numpy-1.26.4-cp39-cp39-win_amd64.whl"
    tampered_wheel.write_bytes(b"INJECTED_TAMPERED_WHEEL_BYTES")

    mgr = OfflineBundleManager()
    res = mgr.verify_wheelhouse(wheelhouse)
    assert res["status"] in ("CORRUPTED", "INCOMPLETE")
    assert len(res["corrupted"]) >= 1


# --- Test 12: Outbound network egress blocked in airgap mode ---
def test_attack_network_egress_blocked_in_airgap():
    with enforce_airgap():
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        with pytest.raises(AirgapViolationError, match="Egress blocked in air-gap mode"):
            s.connect(("8.8.8.8", 53))


# --- Test 13: External DNS resolution blocked in airgap mode ---
def test_attack_dns_resolution_blocked_in_airgap():
    with enforce_airgap():
        with pytest.raises(AirgapViolationError, match="DNS/Resolution blocked in air-gap mode"):
            socket.getaddrinfo("attacker-c2.malicious-domain.com", 443)


# --- Test 14: Secret and credential scanner detects committed private keys ---
def test_attack_secret_scanner_detects_private_key(tmp_path):
    scanner = SecretScanner(repo_root=tmp_path)
    leak_file = tmp_path / "leaked_credentials.py"
    leak_file.write_text(
        '# Secret file\nPRIVATE_KEY = "-----BEGIN RSA PRIVATE KEY-----\\nMIIEowIBAAKCAQEA..."\n',
        encoding="utf-8",
    )

    findings = scanner.scan_file(leak_file)
    assert len(findings) >= 1
    assert findings[0]["rule"] in ("RSA_PRIVATE_KEY", "PRIVATE_KEY_PEM")
    assert findings[0]["severity"] == "CRITICAL"


# --- Test 15: Version downgrade attack prevented by upgrade controller ---
def test_attack_downgrade_prevention():
    controller = UpgradeSafetyController(current_version=SemVer(2, 0, 0))

    downgrade_package = {
        "target_version": "1.0.0",
        "payload_digest": "deadbeef" * 8,
        "signature_hex": "1234" * 16,
        "signer_id": "attacker",
    }

    with pytest.raises(UpgradeSecurityError, match="Downgrade attack prevented"):
        controller.validate_upgrade_package(downgrade_package)
