import pytest
import base64
from core.recipient import RecipientRegistry
from core.release import ReleaseManager
from core.provenance.decryption import RecipientDecryptionClient
from core.traceability.provider import PrototypeTraceabilityProvider
from core.ledger.ledger import TamperEvidentLedger, EvidenceEvent
from core.attribution.engine import AttributionEngine, AttributionState
from core.crypto.signatures import MLDSA65
from attacks.corpus.baseline_generator import BaselineTestCorpus
from attacks.integrity.adversarial_fixtures import (
    create_altered_metadata_fixture,
    create_modified_signature_fixture,
    create_modified_ledger_fixture,
)

@pytest.fixture
def metadata_env():
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
        document_name="meta_test.pdf",
        issuer_id="HQ",
        recipient_ids=["alice", "bob"]
    )
    bob_pkg = release.packages["bob"]
    _, bob_copy, bob_event, _ = decryption_client.decrypt_package(bob_pkg, bob)

    return {
        "registry": registry,
        "bob": bob,
        "bob_copy": bob_copy,
        "bob_event": bob_event,
        "bob_pkg": bob_pkg,
        "release": release,
        "engine": engine,
        "ledger": ledger,
        "trace_provider": trace_provider,
    }

def test_metadata_document_id_tampering_invalidates_marker(metadata_env):
    env = metadata_env
    marker = env["trace_provider"].extract_marker(env["bob_copy"])
    tampered_marker = marker.model_copy(deep=True)
    tampered_marker.document_id = "doc_spoofed_uuid_9999"

    marked_doc = env["trace_provider"].embed_marker(BaselineTestCorpus.generate_simple_text_pdf(), tampered_marker)
    res = env["engine"].analyze_leak(marked_doc, expected_release_id=env["release"].release_id)

    # HMAC token validation fails closed
    assert res.state == AttributionState.INSUFFICIENT_EVIDENCE
    assert res.should_abstain is True
    assert res.candidate is None

def test_metadata_release_id_tampering_triggers_conflict(metadata_env):
    env = metadata_env
    marker = env["trace_provider"].extract_marker(env["bob_copy"])
    tampered_marker = marker.model_copy(deep=True)
    tampered_marker.release_id = "rel_different_scope_777"
    # Even if signature token was freshly computed for the tampered release:
    fresh_token = env["trace_provider"]._compute_token(
        tampered_marker.document_id,
        "rel_different_scope_777",
        tampered_marker.recipient_id,
        tampered_marker.document_hash
    )
    tampered_marker.signature_token = fresh_token

    marked_doc = env["trace_provider"].embed_marker(BaselineTestCorpus.generate_simple_text_pdf(), tampered_marker)
    res = env["engine"].analyze_leak(marked_doc, expected_release_id=env["release"].release_id)

    # Expected release ID does not match marker's release_id
    assert res.state == AttributionState.CONFLICT
    assert res.should_abstain is True

def test_metadata_artifact_hash_tampering_in_ledger(metadata_env):
    env = metadata_env
    # Mutate artifact_hash in ledger event
    tampered_ledger = create_modified_ledger_fixture(env["ledger"], event_index=0)
    isolated_engine = AttributionEngine(
        traceability_provider=env["trace_provider"],
        ledger=tampered_ledger,
        registry=env["registry"]
    )
    res = isolated_engine.analyze_leak(env["bob_copy"], expected_release_id=env["release"].release_id)

    # Ledger integrity chain breaks
    assert res.state == AttributionState.INSUFFICIENT_EVIDENCE
    assert res.should_abstain is True

def test_metadata_timestamp_tampering_breaks_pqc_signature(metadata_env):
    env = metadata_env
    event = env["bob_event"].model_copy(deep=True)
    # Alter timestamp by 1 second
    event.timestamp = "2026-09-26T12:00:01Z"

    sign_payload = (
        f"DECRYPTION_PROVENANCE:{event.event_id}:{event.document_id}:"
        f"{event.release_id}:{event.recipient_id}:{event.artifact_hash}:"
        f"{event.previous_event_hash}:{event.timestamp}"
    ).encode('utf-8')

    sig_bytes = base64.b64decode(event.signature)
    pub_bytes = env["bob"].dsa_keypair.public_key_bytes

    # Signature verification must fail
    assert MLDSA65.verify(pub_bytes, sign_payload, sig_bytes) is False

def test_metadata_signature_bitflip_fails_pqc_verification(metadata_env):
    env = metadata_env
    tampered_event = create_modified_signature_fixture(env["bob_event"])
    test_ledger = TamperEvidentLedger()
    test_ledger.events = [tampered_event]

    isolated_engine = AttributionEngine(
        traceability_provider=env["trace_provider"],
        ledger=test_ledger,
        registry=env["registry"]
    )
    res = isolated_engine.analyze_leak(env["bob_copy"], expected_release_id=env["release"].release_id)

    assert res.state == AttributionState.INSUFFICIENT_EVIDENCE
    assert res.should_abstain is True
