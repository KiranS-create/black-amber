import pytest
from core.recipient import RecipientRegistry
from core.release import ReleaseManager
from core.provenance.decryption import RecipientDecryptionClient
from core.traceability.provider import PrototypeTraceabilityProvider, TardosTraceabilityProvider
from core.ledger.ledger import TamperEvidentLedger
from core.attribution.engine import AttributionEngine, AttributionState
from core.attribution.evidence import (
    EvidenceBundle,
    EvidenceObservation,
    EvidenceFamily,
    EvidenceSource,
    EvidenceConfidenceLevel,
    TargetBinding,
)
from core.traceability.collusion import (
    majority_collusion,
    interleaving_collusion,
    random_symbol_collusion,
    minimax_collusion,
)
from core.traceability.tardos import SymmetricTardosEngine, AccusationStatus
from attacks.corpus.baseline_generator import BaselineTestCorpus

@pytest.fixture
def framing_5party_env():
    registry = RecipientRegistry()
    alice = registry.enroll("Alice", "alice")
    bob = registry.enroll("Bob", "bob")
    charlie = registry.enroll("Charlie", "charlie")
    dave = registry.enroll("Dave", "dave")
    eve = registry.enroll("Eve", "eve")

    ledger = TamperEvidentLedger()
    trace_provider = PrototypeTraceabilityProvider()
    tardos_provider = TardosTraceabilityProvider(coalition_size=3, recipient_count_hint=5)
    release_manager = ReleaseManager(registry=registry)
    decryption_client = RecipientDecryptionClient(ledger=ledger, traceability_provider=trace_provider)
    engine = AttributionEngine(traceability_provider=trace_provider, ledger=ledger, registry=registry)

    sample_doc = BaselineTestCorpus.generate_simple_text_pdf()
    release = release_manager.create_release(
        document_bytes=sample_doc,
        document_name="framing_lab_doc.pdf",
        issuer_id="HQ",
        recipient_ids=["alice", "bob", "charlie", "dave", "eve"]
    )

    # Alice and Bob decrypt
    _, alice_copy, alice_event, _ = decryption_client.decrypt_package(release.packages["alice"], alice)
    _, bob_copy, bob_event, _ = decryption_client.decrypt_package(release.packages["bob"], bob)
    _, charlie_copy, charlie_event, _ = decryption_client.decrypt_package(release.packages["charlie"], charlie)

    return {
        "registry": registry,
        "alice": alice,
        "bob": bob,
        "charlie": charlie,
        "dave": dave,
        "eve": eve,
        "alice_copy": alice_copy,
        "bob_copy": bob_copy,
        "charlie_copy": charlie_copy,
        "alice_event": alice_event,
        "bob_event": bob_event,
        "charlie_event": charlie_event,
        "ledger": ledger,
        "release": release,
        "engine": engine,
        "trace_provider": trace_provider,
        "tardos_provider": tardos_provider,
    }

def test_scenario_A_alice_bob_collusion(framing_5party_env):
    env = framing_5party_env
    m = 1500
    c = 2
    recipients = ["alice", "bob", "charlie", "dave", "eve"]
    seed = b"scenario-A-seed"

    biases = SymmetricTardosEngine.generate_biases(m, c, seed=seed)
    codebook = SymmetricTardosEngine.generate_codebook(recipients, biases, seed=seed)

    forged = majority_collusion([codebook["alice"], codebook["bob"]])
    threshold = SymmetricTardosEngine.compute_threshold(m, len(recipients), 1e-4)

    scores = SymmetricTardosEngine.score_all(forged, codebook, biases)
    res = SymmetricTardosEngine.accuse(scores, threshold, 1e-4)

    # Must attribute Alice and/or Bob
    assert any(col in res.accused_recipients for col in ["alice", "bob"])
    # Innocent Charlie, Dave, Eve must NEVER be accused
    for inn in ["charlie", "dave", "eve"]:
        assert inn not in res.accused_recipients
        assert scores[inn] < threshold

def test_scenario_B_alice_bob_charlie_collusion(framing_5party_env):
    env = framing_5party_env
    m = 2500
    c = 3
    recipients = ["alice", "bob", "charlie", "dave", "eve"]
    seed = b"scenario-B-seed"

    biases = SymmetricTardosEngine.generate_biases(m, c, seed=seed)
    codebook = SymmetricTardosEngine.generate_codebook(recipients, biases, seed=seed)

    forged = interleaving_collusion([codebook["alice"], codebook["bob"], codebook["charlie"]], seed=42)
    threshold = SymmetricTardosEngine.compute_threshold(m, len(recipients), 1e-4)

    scores = SymmetricTardosEngine.score_all(forged, codebook, biases)
    res = SymmetricTardosEngine.accuse(scores, threshold, 1e-4)

    assert any(col in res.accused_recipients for col in ["alice", "bob", "charlie"])
    assert "dave" not in res.accused_recipients
    assert "eve" not in res.accused_recipients

def test_scenario_F_targeted_framing_of_innocent_dave(framing_5party_env):
    """
    Alice and Bob collude and deliberately attempt to construct symbols to frame Dave.
    Under the Marking Assumption, where Alice and Bob agree, they cannot guess Dave's bit.
    """
    env = framing_5party_env
    m = 1500
    c = 2
    recipients = ["alice", "bob", "charlie", "dave", "eve"]
    seed = b"scenario-F-framing-seed"

    biases = SymmetricTardosEngine.generate_biases(m, c, seed=seed)
    codebook = SymmetricTardosEngine.generate_codebook(recipients, biases, seed=seed)

    # Alice and Bob try minimax attack against the scoring function
    forged = minimax_collusion([codebook["alice"], codebook["bob"]], biases)
    threshold = SymmetricTardosEngine.compute_threshold(m, len(recipients), 1e-4)

    scores = SymmetricTardosEngine.score_all(forged, codebook, biases)
    res = SymmetricTardosEngine.accuse(scores, threshold, 1e-4)

    # Dave's expected score is 0.0 because Dave is innocent and not in the coalition
    assert scores["dave"] < threshold
    assert "dave" not in res.accused_recipients

def test_scenario_G_watermark_from_alice_provenance_from_bob(framing_5party_env):
    """
    Adversary splices Alice's extracted watermark with Bob's signed provenance event.
    Target binding and dependency graph must flag a direct conflict.
    """
    env = framing_5party_env

    bundle = EvidenceBundle(
        bundle_id="bnd_spliced_alice_bob",
        target_binding=TargetBinding(
            document_id=env["release"].document_id,
            release_id=env["release"].release_id,
        ),
        observations=[
            EvidenceObservation(
                source_id="obs_wmk_alice",
                family=EvidenceFamily.WATERMARK_PAYLOAD,
                target_binding=TargetBinding(
                    document_id=env["release"].document_id,
                    release_id=env["release"].release_id,
                    recipient_id="alice",
                    artifact_hash="hash_alice_123"
                ),
                primary_candidate="alice",
                log_likelihood_ratio=4.0
            ),
            EvidenceObservation(
                source_id="obs_prov_bob",
                family=EvidenceFamily.PROVENANCE_SIGNATURE,
                target_binding=TargetBinding(
                    document_id=env["release"].document_id,
                    release_id=env["release"].release_id,
                    recipient_id="bob",
                    artifact_hash="hash_bob_456"
                ),
                primary_candidate="bob",
                log_likelihood_ratio=4.0
            )
        ]
    )

    fused = env["engine"].analyze_evidence_bundle(bundle)
    assert fused.state in (AttributionState.CONFLICT, AttributionState.INSUFFICIENT_EVIDENCE)
    assert fused.should_abstain is True

def test_scenario_H_traceability_alice_metadata_bob(framing_5party_env):
    """
    Adversary modifies Alice's marker metadata to point to Bob's release.
    """
    env = framing_5party_env
    marker_alice = env["trace_provider"].extract_marker(env["alice_copy"])
    tampered_marker = marker_alice.model_copy(deep=True)
    tampered_marker.recipient_id = "bob"  # Tampered recipient ID

    marked_doc = env["trace_provider"].embed_marker(BaselineTestCorpus.generate_simple_text_pdf(), tampered_marker)
    res = env["engine"].analyze_leak(marked_doc, expected_release_id=env["release"].release_id)

    # HMAC signature token verification fails because token covers original recipient "alice"
    assert res.state == AttributionState.INSUFFICIENT_EVIDENCE
    assert res.should_abstain is True
    assert res.candidate is None

def test_scenario_I_forged_recipient_identifier_fails_closed(framing_5party_env):
    env = framing_5party_env
    # Create marker with completely non-existent recipient
    marker_ghost = env["trace_provider"].issue_marker(
        document_id=env["release"].document_id,
        release_id=env["release"].release_id,
        recipient_id="mallory_unknown",
        document_hash="hash_doc_123"
    )
    doc_ghost = env["trace_provider"].embed_marker(BaselineTestCorpus.generate_simple_text_pdf(), marker_ghost)
    res = env["engine"].analyze_leak(doc_ghost, expected_release_id=env["release"].release_id)

    assert res.state == AttributionState.INSUFFICIENT_EVIDENCE
    assert res.should_abstain is True
    assert res.candidate is None

def test_scenario_J_stolen_artifact_with_unrelated_ledger(framing_5party_env):
    env = framing_5party_env
    # Bob's artifact presented with empty or unrelated ledger
    empty_ledger = TamperEvidentLedger()
    isolated_engine = AttributionEngine(
        traceability_provider=env["trace_provider"],
        ledger=empty_ledger,
        registry=env["registry"]
    )
    res = isolated_engine.analyze_leak(env["bob_copy"], expected_release_id=env["release"].release_id)

    # Without matching signed decryption provenance event in ledger, attribution must abstain fail-closed
    assert res.state == AttributionState.INSUFFICIENT_EVIDENCE
    assert res.should_abstain is True
    assert res.candidate is None
