import os
import time
import pytest
from core.traceability.keystore import (
    TraceabilityKeystore,
    MissingSecretError,
    KeyEpochUnavailableError,
    KeyEpochMismatchError,
)
from core.traceability.provider import (
    PrototypeTraceabilityProvider,
    TardosTraceabilityProvider,
    TraceabilityMarker,
)
from core.traceability.tardos import SymmetricTardosEngine, AccusationStatus
from core.traceability.collusion import majority_collusion

@pytest.fixture(autouse=True)
def isolated_keystore():
    """Ensure registry and environment isolation before and after every test."""
    TraceabilityKeystore.clear_registry()
    old_env = dict(os.environ)
    yield
    TraceabilityKeystore.clear_registry()
    os.environ.clear()
    os.environ.update(old_env)

# ==============================================================================
# 1. TWO-EPOCH CORE VERIFICATION
# ==============================================================================

def test_two_epoch_rotation_lifecycle():
    """
    Verify complete two-epoch lifecycle:
    - Epoch 1 (K1) creates valid markers with key_id_1.
    - System rotates to Epoch 2 (K2) creating valid markers with key_id_2.
    - Active K2 provider fails closed on Epoch 1 marker if K1 is not registered.
    - Active K2 provider successfully verifies Epoch 1 marker once K1 is registered as historical.
    - Cross-epoch key application fails closed.
    """
    secret_k1 = b"EPOCH_1_MASTER_KEY_2026_Q1_32BYTE!"
    secret_k2 = b"EPOCH_2_MASTER_KEY_2026_Q2_32BYTE!"
    
    key_id_1 = TraceabilityKeystore.compute_key_id(secret_k1)
    key_id_2 = TraceabilityKeystore.compute_key_id(secret_k2)
    assert key_id_1 != key_id_2
    
    # 1. Epoch 1 deployment
    provider_epoch1 = TardosTraceabilityProvider(provider_secret=secret_k1)
    assert provider_epoch1.key_id == key_id_1
    
    doc_bytes_1 = b"%PDF-1.7 Confidential Document Epoch 1\n%%EOF"
    marker_1 = provider_epoch1.issue_marker(
        document_id="DOC-EPOCH-001",
        release_id="REL-2026-Q1",
        recipient_id="alice",
        document_hash="1" * 64
    )
    assert marker_1.metadata["key_id"] == key_id_1
    assert marker_1.metadata["protocol_version"] == "v1.0"
    
    marked_doc_1 = provider_epoch1.embed_marker(doc_bytes_1, marker_1)
    
    # Validates with provider 1
    evidence_1 = provider_epoch1.get_evidence(marked_doc_1, expected_document_hash="1" * 64)
    assert evidence_1.is_valid is True
    assert evidence_1.verification_details["key_epoch_status"] == "ACTIVE"
    
    # 2. Rotate to Epoch 2
    provider_epoch2 = TardosTraceabilityProvider(provider_secret=secret_k2)
    assert provider_epoch2.key_id == key_id_2
    
    doc_bytes_2 = b"%PDF-1.7 Confidential Document Epoch 2\n%%EOF"
    marker_2 = provider_epoch2.issue_marker(
        document_id="DOC-EPOCH-002",
        release_id="REL-2026-Q2",
        recipient_id="bob",
        document_hash="2" * 64
    )
    assert marker_2.metadata["key_id"] == key_id_2
    marked_doc_2 = provider_epoch2.embed_marker(doc_bytes_2, marker_2)
    
    # Validates with provider 2
    evidence_2 = provider_epoch2.get_evidence(marked_doc_2, expected_document_hash="2" * 64)
    assert evidence_2.is_valid is True
    assert evidence_2.verification_details["key_epoch_status"] == "ACTIVE"
    
    # 3. Provider 2 analyzes Doc 1 BEFORE K1 is registered (fail-closed)
    evidence_1_unregistered = provider_epoch2.get_evidence(marked_doc_1, expected_document_hash="1" * 64)
    assert evidence_1_unregistered.is_valid is False
    assert evidence_1_unregistered.confidence == 0.0
    assert evidence_1_unregistered.verification_details["key_epoch_status"] == "KEY_EPOCH_UNAVAILABLE"
    
    # 4. Register K1 in historical keystore registry
    TraceabilityKeystore.register_key(secret_k1)
    
    # 5. Provider 2 analyzes Doc 1 AFTER K1 is registered (historical success)
    evidence_1_historical = provider_epoch2.get_evidence(marked_doc_1, expected_document_hash="1" * 64)
    assert evidence_1_historical.is_valid is True
    assert evidence_1_historical.confidence > 0.99
    assert evidence_1_historical.recipient_id == "alice"
    assert evidence_1_historical.verification_details["key_epoch_status"] == "HISTORICAL"
    assert evidence_1_historical.verification_details["key_id"] == key_id_1

# ==============================================================================
# 2. HISTORICAL FORENSIC COLLUSION ANALYSIS
# ==============================================================================

def test_historical_collusion_leak_analysis():
    """
    Verify historical traitor-tracing analysis across key epochs:
    - A leak occurred under Epoch 1 (K1).
    - An investigator in Epoch 2 (K2) investigates the leak specifying key_id_1.
    - If K1 is available in registry -> successfully attributes the colluders.
    - If K1 is unavailable in registry -> fails closed with NO_SIGNAL and explicit diagnostic.
    """
    secret_k1 = b"HISTORICAL_FORENSIC_KEY_EPOCH_1!"
    secret_k2 = b"ACTIVE_PRODUCTION_KEY_EPOCH_2_!!"
    key_id_1 = TraceabilityKeystore.compute_key_id(secret_k1)
    
    # Generate leaked symbols under Epoch 1
    m = 1024
    c = 2
    N = 10
    recipients = [f"agent_{i:02d}" for i in range(N)]
    colluders = ["agent_02", "agent_05"]
    
    provider_1 = TardosTraceabilityProvider(
        coalition_size=c,
        false_accusation_epsilon=1e-4,
        provider_secret=secret_k1
    )
    
    release_seed_1 = provider_1._derive_release_seed("DOC-TOPSECRET", "REL-001", secret_k1)
    biases_1 = SymmetricTardosEngine.generate_biases(m, c, release_seed_1)
    codebook_1 = SymmetricTardosEngine.generate_codebook(recipients, biases_1, release_seed_1)
    
    colluder_codewords = [codebook_1[k] for k in colluders]
    leaked_symbols = majority_collusion(colluder_codewords)
    
    # Active provider in Epoch 2
    provider_2 = TardosTraceabilityProvider(provider_secret=secret_k2)
    
    # Attempt 1: Analyze with key_id_1 when K1 is NOT registered -> FAIL CLOSED
    res_unavail = provider_2.analyze_collusion_leak(
        observed_symbols=leaked_symbols,
        all_recipient_ids=recipients,
        document_id="DOC-TOPSECRET",
        release_id="REL-001",
        key_id=key_id_1
    )
    assert res_unavail.status == AccusationStatus.NO_SIGNAL
    assert "unavailable" in res_unavail.details["reason"].lower()
    assert len(res_unavail.accused_recipients) == 0
    
    # Attempt 2: Register K1 into historical registry and re-analyze -> SUCCESS
    TraceabilityKeystore.register_key(secret_k1)
    
    res_success = provider_2.analyze_collusion_leak(
        observed_symbols=leaked_symbols,
        all_recipient_ids=recipients,
        document_id="DOC-TOPSECRET",
        release_id="REL-001",
        key_id=key_id_1
    )
    assert res_success.status in (AccusationStatus.ATTRIBUTED, AccusationStatus.COLLUSION_DETECTED)
    assert len(res_success.accused_recipients) > 0
    # Accused must be among the actual colluders
    for accused in res_success.accused_recipients:
        assert accused in colluders

# ==============================================================================
# 3. WRONG-EPOCH AND TAMPERING ATTACKS (10 VARIANTS)
# ==============================================================================

def test_wrong_epoch_attack_matrix():
    """
    Test 10 adversarial wrong-epoch and metadata tampering attack scenarios:
    1. old artifact + new secret
    2. new artifact + old secret
    3. old key_id + new secret
    4. new key_id + old secret
    5. swapped key_id metadata
    6. deleted key_id
    7. malformed key_id
    8. key_id from another document
    9. key_id from another release
    10. replay of an old valid artifact against a new release
    """
    k1 = b"KEY_EPOCH_1_SECRET_TEST_32BYTES!"
    k2 = b"KEY_EPOCH_2_SECRET_TEST_32BYTES!"
    p1 = TardosTraceabilityProvider(provider_secret=k1)
    p2 = TardosTraceabilityProvider(provider_secret=k2)
    
    raw_doc = b"%PDF-1.7 Secret Intelligence Brief\n%%EOF"
    marker_1 = p1.issue_marker("DOC-X", "REL-1", "alice", "x" * 64)
    marker_2 = p2.issue_marker("DOC-Y", "REL-2", "bob", "y" * 64)
    
    # 1. Old artifact verified with explicit new secret K2 -> FAIL
    assert p1.verify_marker(marker_1, secret_key=k2) is False
    
    # 2. New artifact verified with explicit old secret K1 -> FAIL
    assert p2.verify_marker(marker_2, secret_key=k1) is False
    
    # 3. Old key_id in marker verified with new secret K2 -> FAIL CLOSED
    assert p2.verify_marker(marker_1, secret_key=k2) is False
    
    # 4. New key_id in marker verified with old secret K1 -> FAIL CLOSED
    assert p1.verify_marker(marker_2, secret_key=k1) is False
    
    # 5. Swapped key_id metadata (marker 1 with key_id_2) -> FAIL CLOSED
    tampered_marker_5 = marker_1.model_copy(deep=True)
    tampered_marker_5.metadata["key_id"] = p2.key_id
    assert p2.verify_marker(tampered_marker_5) is False
    assert p1.verify_marker(tampered_marker_5) is False
    
    # 6. Deleted key_id (stripped metadata) with wrong key -> FAIL CLOSED
    tampered_marker_6 = marker_1.model_copy(deep=True)
    del tampered_marker_6.metadata["key_id"]
    assert p2.verify_marker(tampered_marker_6) is False
    
    # 7. Malformed key_id -> FAIL CLOSED
    tampered_marker_7 = marker_1.model_copy(deep=True)
    tampered_marker_7.metadata["key_id"] = "MALFORMED_GARBAGE_KEY_ID_$%^&*("
    assert p1.verify_marker(tampered_marker_7) is False
    assert p2.verify_marker(tampered_marker_7) is False
    
    # 8. Token with key_id from another document -> FAIL CLOSED
    assert p1.verify_marker(marker_1, expected_document_hash="wrong_hash" * 4) is False
    
    # 9. Marker with mismatched release_id -> FAIL CLOSED
    tampered_marker_9 = marker_1.model_copy(deep=True)
    tampered_marker_9.release_id = "REL-DIFFERENT"
    assert p1.verify_marker(tampered_marker_9) is False
    
    # 10. Replay old valid artifact against new release check
    doc_1_bytes = p1.embed_marker(raw_doc, marker_1)
    ev_replay = p2.get_evidence(doc_1_bytes, expected_document_hash="y" * 64)
    assert ev_replay.is_valid is False

# ==============================================================================
# 4. 4D CROSS-DOCUMENT / RELEASE / RECIPIENT / EPOCH ISOLATION MATRIX
# ==============================================================================

def test_4d_orthogonal_isolation_matrix():
    """
    Verify complete isolation across 4 orthogonal dimensions:
    - 2 Documents (DOC_A, DOC_B)
    - 2 Releases (REL_1, REL_2)
    - 2 Recipients (USER_X, USER_Y)
    - 2 Key Epochs (K1, K2)
    
    Total parameter combinations: 16
    Exactly 1 combination is valid for a given target marker.
    All other 15 invalid tuples MUST fail closed.
    """
    k1 = b"ORTHOGONAL_TEST_SECRET_EPOCH_1!!"
    k2 = b"ORTHOGONAL_TEST_SECRET_EPOCH_2!!"
    TraceabilityKeystore.register_key(k1)
    TraceabilityKeystore.register_key(k2)
    
    provider = TardosTraceabilityProvider(provider_secret=k1)
    
    target_doc = "DOC_ALPHA"
    target_rel = "REL_100"
    target_rec = "charlie"
    target_hash = "f" * 64
    
    marker = provider.issue_marker(
        document_id=target_doc,
        release_id=target_rel,
        recipient_id=target_rec,
        document_hash=target_hash,
        secret_key=k1
    )
    
    documents = [target_doc, "DOC_BETA"]
    releases = [target_rel, "REL_200"]
    recipients = [target_rec, "david"]
    keys = [("EPOCH_1", k1), ("EPOCH_2", k2)]
    
    valid_count = 0
    fail_count = 0
    
    for d in documents:
        for r in releases:
            for u in recipients:
                for k_name, k_val in keys:
                    # Construct trial marker
                    is_exact_match = (
                        d == target_doc and
                        r == target_rel and
                        u == target_rec and
                        k_val == k1
                    )
                    
                    trial_token = provider._compute_token(
                        d, r, u, target_hash,
                        marker.metadata["codeword_digest"],
                        secret_key=k_val
                    )
                    
                    if is_exact_match:
                        assert trial_token == marker.signature_token
                        valid_count += 1
                    else:
                        assert trial_token != marker.signature_token
                        fail_count += 1
                        
    assert valid_count == 1
    assert fail_count == 15

# ==============================================================================
# 5. KEY IDENTIFIER SECURITY AND PERFORMANCE
# ==============================================================================

def test_key_id_lookup_performance_and_scaling():
    """
    Benchmark O(1) key_id direct lookup across 100 registered historical epochs.
    Lookup must complete in under 0.1ms per query without iterating.
    """
    TraceabilityKeystore.clear_registry()
    num_epochs = 100
    registered_keys = {}
    
    for i in range(num_epochs):
        secret = f"SIMULATED_ENTERPRISE_KEY_EPOCH_{i:04d}_32B".encode('utf-8')
        kid = TraceabilityKeystore.register_key(secret)
        registered_keys[kid] = secret
        
    epochs_list = TraceabilityKeystore.list_known_epochs()
    assert len(epochs_list) >= num_epochs
    assert len(TraceabilityKeystore._registry) == num_epochs
    
    # Benchmark 1000 lookups
    registered_kids = list(registered_keys.keys())
    start_time = time.perf_counter()
    iterations = 1000
    for i in range(iterations):
        target_kid = registered_kids[i % num_epochs]
        # Direct lookup
        key = TraceabilityKeystore.get_key_by_id(target_kid)
        assert key is not None
    elapsed = time.perf_counter() - start_time
    
    avg_latency_ms = (elapsed / iterations) * 1000.0
    # Must be faster than 0.05ms (direct dictionary lookup is ~1 microsecond)
    assert avg_latency_ms < 0.05, f"Lookup latency too high: {avg_latency_ms:.4f} ms"

def test_legacy_prototype_backward_compatibility():
    """
    Verify backward compatibility with legacy prototype markers lacking key_id metadata.
    """
    secret = b"LEGACY_COMPATIBILITY_TEST_KEY_32B"
    provider = PrototypeTraceabilityProvider(provider_secret=secret)
    
    # Create legacy marker without key_id in metadata
    legacy_marker = TraceabilityMarker(
        document_id="DOC-LEGACY",
        release_id="REL-LEGACY",
        recipient_id="eve",
        document_hash="e" * 64,
        signature_token=provider._compute_token("DOC-LEGACY", "REL-LEGACY", "eve", "e" * 64),
        timestamp="2026-01-01T00:00:00Z",
        metadata={}  # Empty metadata
    )
    
    doc_bytes = b"%PDF-1.7 Legacy Prototype Doc\n%%EOF"
    marked_doc = provider.embed_marker(doc_bytes, legacy_marker)
    
    evidence = provider.get_evidence(marked_doc, expected_document_hash="e" * 64)
    assert evidence.is_valid is True
    assert evidence.verification_details["key_epoch_status"] == "LEGACY_PRE_EPOCH"
    assert evidence.confidence > 0.98
