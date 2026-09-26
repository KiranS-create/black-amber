import os
import shutil
import tempfile
import pytest
from typing import Generator
from core.traceability.keystore import TraceabilityKeystore, MissingSecretError, TraceabilitySecurityError
from core.traceability.tardos import SymmetricTardosEngine, AccusationStatus
from core.traceability.provider import (
    PrototypeTraceabilityProvider,
    TardosTraceabilityProvider,
    TraceabilityMarker,
)

@pytest.fixture
def clean_env() -> Generator[None, None, None]:
    """Fixture to ensure a pristine environment without secret leaks between tests."""
    temp_dir = tempfile.mkdtemp(prefix="sih_keystore_test_")
    old_env = dict(os.environ)
    
    # Isolate keystore path
    os.environ["SIH26237_KEYSTORE_PATH"] = os.path.join(temp_dir, "traceability_master.key")
    if "SIH26237_TRACEABILITY_MASTER_SECRET" in os.environ:
        del os.environ["SIH26237_TRACEABILITY_MASTER_SECRET"]
    if "SIH26237_ENV" in os.environ:
        del os.environ["SIH26237_ENV"]
        
    yield
    
    # Cleanup
    os.environ.clear()
    os.environ.update(old_env)
    try:
        shutil.rmtree(temp_dir)
    except Exception:
        pass

def test_no_hardcoded_secrets_in_source():
    """Verify that hardcoded secrets are completely absent from class attributes."""
    assert not hasattr(PrototypeTraceabilityProvider, "DEFAULT_SECRET_KEY")
    assert not hasattr(TardosTraceabilityProvider, "DEFAULT_SECRET_KEY")
    assert not hasattr(SymmetricTardosEngine, "DEFAULT_MASTER_KEY")

def test_production_mode_fail_closed(clean_env):
    """Verify that production mode raises MissingSecretError when no secret is configured."""
    os.environ["SIH26237_ENV"] = "production"
    
    # Must fail closed when resolving secret without env var or explicit secret
    with pytest.raises(MissingSecretError) as exc_info:
        TraceabilityKeystore.resolve_secret(explicit_secret=None)
    assert "Traceability master secret is required in production mode" in str(exc_info.value)
    
    # Initializing provider without explicit secret in production must fail closed
    with pytest.raises(MissingSecretError):
        PrototypeTraceabilityProvider()
        
    with pytest.raises(MissingSecretError):
        TardosTraceabilityProvider()

def test_production_mode_accepts_env_secret(clean_env):
    """Verify that production mode accepts secret when provided via environment variable."""
    os.environ["SIH26237_ENV"] = "production"
    test_secret = b"PROD_ENTERPRISE_INJECTED_MASTER_KEY_32BYTES!!"
    os.environ["SIH26237_TRACEABILITY_MASTER_SECRET"] = test_secret.decode("utf-8")
    
    resolved = TraceabilityKeystore.resolve_secret()
    assert resolved == test_secret
    
    provider = TardosTraceabilityProvider()
    assert provider.provider_secret == test_secret
    assert provider.key_id == TraceabilityKeystore.compute_key_id(test_secret)

def test_development_mode_auto_generation_and_persistence(clean_env):
    """Verify development mode generates and persists a cryptographically secure key."""
    keystore_path = os.environ["SIH26237_KEYSTORE_PATH"]
    assert not os.path.exists(keystore_path)
    
    # First call: auto-generates key
    secret_1 = TraceabilityKeystore.resolve_secret()
    assert len(secret_1) == 32
    assert os.path.exists(keystore_path)
    
    # Second call: reuses persisted key
    secret_2 = TraceabilityKeystore.resolve_secret()
    assert secret_1 == secret_2

def test_custody_hierarchy_precedence(clean_env):
    """Verify exact precedence: Explicit > Env Var > Keystore File."""
    keystore_path = os.environ["SIH26237_KEYSTORE_PATH"]
    keystore_secret = b"KEYSTORE_FILE_SECRET_32BYTES_VAL"
    os.makedirs(os.path.dirname(keystore_path), exist_ok=True)
    with open(keystore_path, "wb") as f:
        f.write(keystore_secret)
        
    env_secret = b"ENV_VARIABLE_SECRET_32BYTES_VAL!"
    os.environ["SIH26237_TRACEABILITY_MASTER_SECRET"] = env_secret.decode("utf-8")
    
    explicit_secret = b"EXPLICIT_CALL_SECRET_32BYTES_VAL"
    
    # 1. With all 3 present, explicit secret wins
    assert TraceabilityKeystore.resolve_secret(explicit_secret) == explicit_secret
    
    # 2. With explicit None, env var wins over keystore file
    assert TraceabilityKeystore.resolve_secret() == env_secret
    
    # 3. With env var cleared, keystore file wins
    del os.environ["SIH26237_TRACEABILITY_MASTER_SECRET"]
    assert TraceabilityKeystore.resolve_secret() == keystore_secret

def test_deterministic_codebook_reconstruction(clean_env):
    """Verify that identical configured secrets produce bit-for-bit identical codebooks."""
    secret = b"STABLE_DEMO_SECRET_KEY_FOR_TARDOS_32B"
    recipients = ["dept_alpha", "dept_beta", "dept_gamma"]
    
    biases_run1 = SymmetricTardosEngine.generate_biases(m=64, c=3, seed=secret)
    codebook_run1 = SymmetricTardosEngine.generate_codebook(recipients, biases_run1, seed=secret)
    
    biases_run2 = SymmetricTardosEngine.generate_biases(m=64, c=3, seed=secret)
    codebook_run2 = SymmetricTardosEngine.generate_codebook(recipients, biases_run2, seed=secret)
    
    assert biases_run1 == biases_run2
    for r in recipients:
        assert codebook_run1[r] == codebook_run2[r]

def test_codebook_isolation_between_different_secrets(clean_env):
    """Verify that distinct secrets produce distinct bias distributions and codewords."""
    secret_a = b"SECRET_TENANT_A_ENTERPRISE_KEY_32"
    secret_b = b"SECRET_TENANT_B_ENTERPRISE_KEY_32"
    recipients = ["user_1", "user_2"]
    
    biases_a = SymmetricTardosEngine.generate_biases(m=64, c=3, seed=secret_a)
    biases_b = SymmetricTardosEngine.generate_biases(m=64, c=3, seed=secret_b)
    assert biases_a != biases_b
    
    codebook_a = SymmetricTardosEngine.generate_codebook(recipients, biases_a, seed=secret_a)
    codebook_b = SymmetricTardosEngine.generate_codebook(recipients, biases_b, seed=secret_b)
    for r in recipients:
        assert codebook_a[r] != codebook_b[r]

def test_key_id_derivation_and_rotation_tagging(clean_env):
    """Verify key_id format and tracking in marker metadata."""
    secret_epoch_1 = b"SECRET_EPOCH_1_KEYS_FOR_Q1_2026"
    secret_epoch_2 = b"SECRET_EPOCH_2_KEYS_FOR_Q2_2026"
    
    key_id_1 = TraceabilityKeystore.compute_key_id(secret_epoch_1)
    key_id_2 = TraceabilityKeystore.compute_key_id(secret_epoch_2)
    
    assert key_id_1.startswith("tkey_")
    assert key_id_2.startswith("tkey_")
    assert key_id_1 != key_id_2
    assert len(key_id_1) == 13  # "tkey_" + 8 hex chars
    
    # Provider marker tagging
    provider_1 = TardosTraceabilityProvider(provider_secret=secret_epoch_1)
    marker_1 = provider_1.issue_marker(
        document_id="DOC-SECRET-001",
        release_id="REL-001",
        recipient_id="alice",
        document_hash="a" * 64
    )
    assert marker_1.metadata["key_id"] == key_id_1
    
    # Verify marker with provider_1
    assert provider_1.verify_marker(marker_1) is True
    
    # Marker verified with rotated provider_2 should fail unless correct key is used
    provider_2 = TardosTraceabilityProvider(provider_secret=secret_epoch_2)
    assert provider_2.verify_marker(marker_1) is False
    assert provider_2.verify_marker(marker_1, secret_key=secret_epoch_1) is True

def test_secret_non_exposure_in_strings_and_logs(clean_env):
    """Verify secret bytes are never exposed in string descriptors or custody status."""
    secret = b"SUPER_SENSITIVE_TOP_SECRET_BYTES"
    status_str = TraceabilityKeystore.get_custody_status(secret)
    
    # Must NOT contain raw secret string
    assert "SUPER_SENSITIVE" not in status_str
    assert "TOP_SECRET" not in status_str
    
    # Must contain safe key_id
    key_id = TraceabilityKeystore.compute_key_id(secret)
    assert key_id in status_str

def test_end_to_end_provider_with_managed_keystore(clean_env):
    """Verify complete end-to-end lifecycle using keystore management."""
    secret = b"E2E_KEYSTORE_VERIFIED_SECRET_32B"
    provider = TardosTraceabilityProvider(
        coalition_size=3,
        false_accusation_epsilon=1e-4,
        provider_secret=secret
    )
    
    doc_bytes = b"%PDF-1.7 Sample Forensic Confidential Brief\n%%EOF"
    marker = provider.issue_marker(
        document_id="DOC-999",
        release_id="REL-999",
        recipient_id="bob",
        document_hash="b" * 64
    )
    
    marked_doc = provider.embed_marker(doc_bytes, marker)
    assert len(marked_doc) > len(doc_bytes)
    
    evidence = provider.get_evidence(marked_doc, expected_document_hash="b" * 64)
    assert evidence.marker_found is True
    assert evidence.is_valid is True
    assert evidence.confidence > 0.99
    assert evidence.recipient_id == "bob"
    assert evidence.verification_details["key_id"] == provider.key_id
