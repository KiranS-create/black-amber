import pytest
from core.recipient import RecipientRegistry
from core.release import ReleaseManager
from core.traceability.provider import PrototypeTraceabilityProvider
from core.ledger.ledger import TamperEvidentLedger
from core.attribution.engine import AttributionEngine, AttributionState
from attacks.corpus.negative_corpus import NegativeCorpusGenerator, NegativeCorpusSample
from attacks.corpus.baseline_generator import BaselineTestCorpus

@pytest.fixture
def negative_corpus_env():
    registry = RecipientRegistry()
    registry.enroll("Alice", "alice")
    registry.enroll("Bob", "bob")
    registry.enroll("Charlie", "charlie")

    ledger = TamperEvidentLedger()
    trace_provider = PrototypeTraceabilityProvider()
    release_manager = ReleaseManager(registry=registry)
    engine = AttributionEngine(traceability_provider=trace_provider, ledger=ledger, registry=registry)

    sample_doc = BaselineTestCorpus.generate_simple_text_pdf()
    release = release_manager.create_release(
        document_bytes=sample_doc,
        document_name="target_classified_doc.pdf",
        issuer_id="HQ",
        recipient_ids=["alice", "bob", "charlie"]
    )

    return {
        "engine": engine,
        "release": release,
    }

def test_full_100_sample_negative_corpus_evaluation(negative_corpus_env):
    """
    CRITICAL STATISTICAL TEST:
    Evaluates 100 negative samples across 10 distinct categories against AegisTrace.
    Must produce ZERO false positives (False Positive Rate = 0.00%).
    """
    env = negative_corpus_env
    samples = NegativeCorpusGenerator.generate_full_negative_corpus(count_per_category=10)
    assert len(samples) == 100

    false_positives = 0
    abstentions = 0
    state_breakdown = {}

    for sample in samples:
        res = env["engine"].analyze_leak(sample.artifact_bytes, expected_release_id=env["release"].release_id)
        
        state_breakdown[res.state.value] = state_breakdown.get(res.state.value, 0) + 1

        if res.state == AttributionState.ATTRIBUTED:
            false_positives += 1
        
        if res.should_abstain:
            abstentions += 1

    # Assertions
    assert false_positives == 0, f"Critical security failure: {false_positives} false positives in negative corpus!"
    assert abstentions == 100, f"Expected 100 abstentions, got {abstentions}"
    
    # Verify that all 100 samples map to fail-closed abstention states
    total_abstained_states = (
        state_breakdown.get("NO_SIGNAL", 0) +
        state_breakdown.get("INSUFFICIENT_EVIDENCE", 0) +
        state_breakdown.get("CONFLICT", 0)
    )
    assert total_abstained_states == 100
    assert state_breakdown.get("NO_SIGNAL", 0) >= 50

def test_negative_corpus_clean_unwatermarked_pdfs(negative_corpus_env):
    env = negative_corpus_env
    for i in range(1, 6):
        clean_pdf = NegativeCorpusGenerator.generate_clean_unwatermarked_pdf(i)
        res = env["engine"].analyze_leak(clean_pdf, expected_release_id=env["release"].release_id)
        assert res.state == AttributionState.NO_SIGNAL
        assert res.should_abstain is True
        assert res.candidate is None

def test_negative_corpus_counterfeit_forgeries_rejected(negative_corpus_env):
    env = negative_corpus_env
    for i in range(1, 6):
        counterfeit = NegativeCorpusGenerator.generate_counterfeit_marker_pdf(i)
        res = env["engine"].analyze_leak(counterfeit, expected_release_id=env["release"].release_id)
        # Counterfeit HMAC token fails validation -> INSUFFICIENT_EVIDENCE
        assert res.state == AttributionState.INSUFFICIENT_EVIDENCE
        assert res.should_abstain is True
        assert res.candidate is None
