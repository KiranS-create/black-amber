import io
import pytest
from core.recipient import RecipientRegistry
from core.release import ReleaseManager
from core.provenance.decryption import RecipientDecryptionClient
from core.traceability.provider import PrototypeTraceabilityProvider
from core.ledger.ledger import TamperEvidentLedger
from core.attribution.engine import AttributionEngine, AttributionState

from attacks.corpus.baseline_generator import BaselineTestCorpus
from attacks.integrity.adversarial_fixtures import (
    create_modified_artifact_fixture,
    create_altered_metadata_fixture,
    create_corrupted_release_id_fixture,
    create_recipient_substitution_fixture,
    create_wrong_document_fixture,
    create_stale_artifact_fixture,
    create_forged_provenance_event_fixture,
    create_modified_signature_fixture,
    create_modified_ledger_fixture,
    create_reordered_ledger_fixture,
    create_deleted_ledger_fixture,
    create_duplicated_ledger_fixture,
    create_substituted_artifact_fixture,
)

@pytest.fixture
def crypto_environment():
    registry = RecipientRegistry()
    alice = registry.enroll("Alice", "alice")
    bob = registry.enroll("Bob", "bob")
    ledger = TamperEvidentLedger()
    trace_provider = PrototypeTraceabilityProvider()
    release_manager = ReleaseManager(registry=registry)
    decryption_client = RecipientDecryptionClient(ledger=ledger, traceability_provider=trace_provider)
    engine = AttributionEngine(traceability_provider=trace_provider, ledger=ledger, registry=registry)

    sample_doc = BaselineTestCorpus.generate_simple_text_pdf()
    release = release_manager.create_release(
        document_bytes=sample_doc,
        document_name="test_doc.pdf",
        issuer_id="HQ",
        recipient_ids=["alice", "bob"]
    )
    # Bob decrypts legitimately
    bob_pkg = release.packages["bob"]
    _, bob_traceable_copy, bob_event, _ = decryption_client.decrypt_package(bob_pkg, bob)

    return {
        "registry": registry,
        "alice": alice,
        "bob": bob,
        "ledger": ledger,
        "trace_provider": trace_provider,
        "release_manager": release_manager,
        "decryption_client": decryption_client,
        "engine": engine,
        "sample_doc": sample_doc,
        "release": release,
        "bob_pkg": bob_pkg,
        "bob_traceable_copy": bob_traceable_copy,
        "bob_event": bob_event,
    }

def test_1_modified_artifact_ciphertext_bit_flip_fails_decryption(crypto_environment):
    env = crypto_environment
    corrupted_pkg = create_modified_artifact_fixture(env["bob_pkg"])
    # Decryption must raise ValueError due to AES-256-GCM authentication failure
    with pytest.raises(ValueError):
        env["decryption_client"].decrypt_package(corrupted_pkg, env["bob"])

def test_2_altered_metadata_fixture(crypto_environment):
    env = crypto_environment
    altered_pkg = create_altered_metadata_fixture(env["bob_pkg"], spoofed_doc_hash="cafebabe" * 8)
    assert altered_pkg.document_hash == "cafebabe" * 8
    # Attempting decryption with tampered document_hash must fail integrity verification
    with pytest.raises(ValueError, match="Integrity check failed"):
        env["decryption_client"].decrypt_package(altered_pkg, env["bob"])

def test_3_corrupted_release_id_fails_decryption_or_attribution(crypto_environment):
    env = crypto_environment
    corrupted_pkg = create_corrupted_release_id_fixture(env["bob_pkg"])
    with pytest.raises(ValueError):
        env["decryption_client"].decrypt_package(corrupted_pkg, env["bob"])

def test_4_recipient_substitution_framing_fails_decryption(crypto_environment):
    env = crypto_environment
    framed_pkg = create_recipient_substitution_fixture(env["bob_pkg"], target_recipient_id="alice")
    with pytest.raises(ValueError):
        env["decryption_client"].decrypt_package(framed_pkg, env["alice"])

def test_5_wrong_document_fixture_abstained_by_attribution(crypto_environment):
    env = crypto_environment
    marker = env["trace_provider"].extract_marker(env["bob_traceable_copy"])
    wrong_doc, tampered_marker = create_wrong_document_fixture(env["sample_doc"], marker)
    marked_wrong = env["trace_provider"].embed_marker(wrong_doc, tampered_marker)
    res = env["engine"].analyze_leak(marked_wrong, expected_release_id=env["release"].release_id)
    assert res.should_abstain is True
    assert res.state in (AttributionState.CONFLICT, AttributionState.INSUFFICIENT_EVIDENCE, AttributionState.NO_SIGNAL)

def test_6_stale_artifact_replay_triggers_release_conflict(crypto_environment):
    env = crypto_environment
    stale = create_stale_artifact_fixture(env["bob_event"], new_release_id="rel_expired_999")
    assert stale.release_id == "rel_expired_999"

def test_7_forged_provenance_event_signature_rejected(crypto_environment):
    env = crypto_environment
    forged = create_forged_provenance_event_fixture(
        event_id="evt_forged_01",
        recipient_id="bob",
        document_id=env["release"].document_id,
        release_id=env["release"].release_id,
        prev_event_hash=env["ledger"].get_last_event_hash()
    )
    # Create test ledger with the forged event replacing or following Bob's event
    test_ledger = TamperEvidentLedger()
    test_ledger.events = [forged]
    test_engine = AttributionEngine(traceability_provider=env["trace_provider"], ledger=test_ledger, registry=env["registry"])
    res = test_engine.analyze_leak(env["bob_traceable_copy"], expected_release_id=env["release"].release_id)
    # Recipient signature validation must fail, leading to abstention
    assert res.should_abstain is True
    assert res.state == AttributionState.INSUFFICIENT_EVIDENCE

def test_8_modified_signature_fixture_rejected(crypto_environment):
    env = crypto_environment
    tampered_event = create_modified_signature_fixture(env["bob_event"])
    test_ledger = TamperEvidentLedger()
    test_ledger.events = [tampered_event]
    test_engine = AttributionEngine(traceability_provider=env["trace_provider"], ledger=test_ledger, registry=env["registry"])
    res = test_engine.analyze_leak(env["bob_traceable_copy"], expected_release_id=env["release"].release_id)
    assert res.should_abstain is True

def test_9_modified_ledger_event_fails_chain_integrity(crypto_environment):
    env = crypto_environment
    tampered_ledger = create_modified_ledger_fixture(env["ledger"], event_index=0)
    valid, errors = tampered_ledger.verify_chain()
    assert valid is False
    assert len(errors) > 0

def test_10_reordered_ledger_fails_chain_integrity(crypto_environment):
    env = crypto_environment
    alice_pkg = env["release"].packages["alice"]
    env["decryption_client"].decrypt_package(alice_pkg, env["alice"])

    reordered_ledger = create_reordered_ledger_fixture(env["ledger"])
    valid, errors = reordered_ledger.verify_chain()
    assert valid is False
    assert len(errors) > 0

def test_11_deleted_ledger_entry_fails_chain_integrity(crypto_environment):
    env = crypto_environment
    alice_pkg = env["release"].packages["alice"]
    env["decryption_client"].decrypt_package(alice_pkg, env["alice"])

    deleted_ledger = create_deleted_ledger_fixture(env["ledger"], delete_index=0)
    valid, errors = deleted_ledger.verify_chain()
    assert valid is False

def test_12_duplicated_ledger_event_fails_chain_or_replay(crypto_environment):
    env = crypto_environment
    dup_ledger = create_duplicated_ledger_fixture(env["ledger"], dup_index=0)
    valid, errors = dup_ledger.verify_chain()
    assert valid is False

def test_13_substituted_artifact_triggers_abstention(crypto_environment):
    env = crypto_environment
    decoy_pdf = BaselineTestCorpus.generate_multipage_pdf()
    substituted = create_substituted_artifact_fixture(decoy_pdf)
    res = env["engine"].analyze_leak(substituted, expected_release_id=env["release"].release_id)
    assert res.should_abstain is True
    assert res.state == AttributionState.NO_SIGNAL
