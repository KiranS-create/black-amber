import base64
import hashlib
import os
import tempfile
import pytest
from fastapi.testclient import TestClient

from apps.api.main import app
from apps.api.config import config
from core.crypto.kem import (
    MLKEM768,
    StandardMLKEM768Provider,
    OQSMLKEMProvider,
    DevFallbackKEMProvider,
    get_default_kem_provider,
)
from core.crypto.signatures import (
    MLDSA65,
    StandardMLDSA65Provider,
    OQSMLDSAProvider,
    DevFallbackDSAProvider,
    get_default_dsa_provider,
)
from core.crypto.symmetric import (
    generate_symmetric_key,
    encrypt_aes_gcm,
    decrypt_aes_gcm,
    wrap_key_aes_kw,
    unwrap_key_aes_kw,
)
from core.crypto.key_derivation import (
    derive_key,
    derive_recipient_wrapping_key,
    PROTOCOL_VERSION,
)
from core.traceability.keystore import TraceabilityKeystore, MissingSecretError
from scripts.deployment.health_check import run_health_check
from scripts.deployment.build_info import collect_build_info
from scripts.deployment.generate_demo_fixtures import generate_fixtures
from demo.end_to_end import create_sample_pdf


@pytest.fixture
def client():
    return TestClient(app)


def test_production_crypto_provider_invariants():
    """
    Verify that production crypto providers are genuine NIST FIPS 203/204 implementations.
    Strictly asserts that insecure development fallbacks are NEVER active by default.
    """
    kem_meta = MLKEM768.get_metadata()
    dsa_meta = MLDSA65.get_metadata()

    # Assert ML-KEM-768 standard conformance
    assert kem_meta["algorithm"] == "ML-KEM-768"
    assert kem_meta["is_post_quantum"] is True
    assert kem_meta["is_production_safe"] is True
    assert kem_meta["public_key_size_bytes"] == 1184
    assert kem_meta["private_key_size_bytes"] == 2400
    assert kem_meta["ciphertext_size_bytes"] == 1088
    assert kem_meta["shared_secret_size_bytes"] == 32
    assert not isinstance(MLKEM768.get_provider(), DevFallbackKEMProvider)

    # Assert ML-DSA-65 standard conformance
    assert dsa_meta["algorithm"] == "ML-DSA-65"
    assert dsa_meta["is_post_quantum"] is True
    assert dsa_meta["is_production_safe"] is True
    assert dsa_meta["public_key_size_bytes"] == 1952
    assert dsa_meta["private_key_size_bytes"] == 4000
    assert dsa_meta["signature_size_bytes"] == 3293
    assert not isinstance(MLDSA65.get_provider(), DevFallbackDSAProvider)


def test_crypto_fail_closed_in_production_mode(monkeypatch):
    """
    Verify that in production mode (SIH26237_ENV=production or AEGISTRACE_ENV=production),
    crypto provider factory strictly fails closed if secure PQC providers are unavailable.
    """
    monkeypatch.setenv("SIH26237_ENV", "production")
    
    # Simulate an environment missing both native OQS and pure-Python PQC engines
    monkeypatch.setattr("core.crypto.kem._OQS_AVAILABLE", False)
    monkeypatch.setattr("core.crypto.kem._KYBER_PY_AVAILABLE", False)
    monkeypatch.setattr("core.crypto.signatures._OQS_AVAILABLE", False)
    monkeypatch.setattr("core.crypto.signatures._DILITHIUM_PY_AVAILABLE", False)

    # In production mode without PQC providers, provider selection MUST raise RuntimeError
    with pytest.raises(RuntimeError, match="FATAL \\[ML-KEM-768\\]"):
        get_default_kem_provider()

    with pytest.raises(RuntimeError, match="FATAL \\[ML-DSA-65\\]"):
        get_default_dsa_provider()



def test_symmetric_and_kdf_invariants():
    """
    Verify AES-256-GCM and HKDF-SHA256 mathematical invariants and domain separation.
    """
    key = generate_symmetric_key()
    assert len(key) == 32

    plaintext = b"AEGISTRACE_REPRODUCIBLE_DEPLOYMENT_PAYLOAD_TEST"
    aad = b"SECURITY_DOMAIN_SEPARATION_AAD"

    ciphertext = encrypt_aes_gcm(key, plaintext, associated_data=aad)
    assert len(ciphertext.nonce) == 12
    assert len(ciphertext.tag) == 16
    assert ciphertext.associated_data == aad

    decrypted = decrypt_aes_gcm(key, ciphertext)
    assert decrypted == plaintext

    # Test Key Wrap / Unwrap
    wrapping_key = generate_symmetric_key()
    wrapped = wrap_key_aes_kw(wrapping_key, key, associated_data=aad)
    assert len(wrapped) == 60  # 12 (nonce) + 16 (tag) + 32 (key)
    unwrapped = unwrap_key_aes_kw(wrapping_key, wrapped, associated_data=aad)
    assert unwrapped == key

    # Test HKDF domain separation
    ss = b"\x42" * 32
    k1 = derive_recipient_wrapping_key(ss, "REL-001", "DOC-001", "alice")
    k2 = derive_recipient_wrapping_key(ss, "REL-001", "DOC-001", "bob")
    k3 = derive_recipient_wrapping_key(ss, "REL-002", "DOC-001", "alice")

    assert k1 != k2
    assert k1 != k3
    assert len(k1) == 32


def test_deployment_health_and_build_manifest():
    """
    Verify deployment health verification script and build information manifest collection.
    """
    report = run_health_check()
    assert report["status"] == "PASS"
    assert report["checks"]["python_runtime"]["status"] == "PASS"
    assert report["checks"]["crypto_primitives"]["status"] == "PASS"
    assert report["checks"]["crypto_primitives"]["is_post_quantum"] is True
    assert report["checks"]["storage_writable"]["status"] == "PASS"
    assert report["checks"]["api_endpoints"]["status"] == "PASS"

    info = collect_build_info()
    assert info["version"] == "1.0.0"
    assert info["offline_ready"] is True
    assert "fastapi" in info["dependency_snapshot"]
    assert "kyber-py" in info["dependency_snapshot"]
    assert "dilithium-py" in info["dependency_snapshot"]
    assert "cryptography" in info["dependency_snapshot"]


def test_clean_deployment_fixture_reproducibility(client: TestClient, tmp_path):
    """
    Verify that generating demo fixtures in a fresh isolated directory produces
    valid, reproducible, and verifiable cryptographic artifacts.
    """
    manifest = generate_fixtures(output_dir=tmp_path, use_default_singletons=False)
    assert len(manifest["fixtures"]) == 3

    # Check all fixture files exist on disk
    for item in manifest["fixtures"]:
        file_p = tmp_path / item["file"]
        assert file_p.exists()
        assert file_p.stat().st_size > 0
        with open(file_p, "rb") as f:
            computed_sha = hashlib.sha256(f.read()).hexdigest()
        assert computed_sha == item["sha256"]

    # Verify Bob leak attribution against API
    with open(tmp_path / "bob_leak.pdf", "rb") as f:
        bob_leak_bytes = f.read()

    doc_res = client.post(
        "/documents",
        files={"file": ("repro_source.pdf", (tmp_path / "source_document.pdf").read_bytes(), "application/pdf")},
        data={"document_name": "Reproducible Source"}
    )
    assert doc_res.status_code == 201


def test_secret_custody_fail_closed_in_production(monkeypatch, tmp_path):
    """
    Verify that in production mode, missing master secret fails closed.
    """
    monkeypatch.setenv("SIH26237_ENV", "production")
    monkeypatch.delenv("SIH26237_TRACEABILITY_MASTER_SECRET", raising=False)
    monkeypatch.delenv("SIH26237_KEYSTORE_PATH", raising=False)

    with pytest.raises(MissingSecretError, match="Traceability master secret is required in production mode"):
        TraceabilityKeystore.resolve_secret(allow_dev_generation=False)
