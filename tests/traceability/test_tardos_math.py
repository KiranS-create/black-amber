import pytest
import math
from core.traceability.tardos import (
    SymmetricTardosEngine,
    AccusationStatus,
    TardosAccusationResult,
)

def test_bias_generation_bounds():
    """Verify that all generated biases lie strictly in [t, 1-t]."""
    m = 500
    c = 3
    t = SymmetricTardosEngine.compute_cutoff(c)
    assert t == pytest.approx(1.0 / 900.0)

    biases = SymmetricTardosEngine.generate_biases(m, c, seed=b"test-seed-1")
    assert len(biases) == m

    for p in biases:
        assert p >= t
        assert p <= 1.0 - t

    # Due to symmetry of arcsin distribution around 0.5, sample mean should be ~0.5
    mean_p = sum(biases) / float(m)
    assert mean_p == pytest.approx(0.5, abs=0.08)


def test_bias_generation_reproducibility():
    """Verify that bias generation is deterministic for the same seed."""
    b1 = SymmetricTardosEngine.generate_biases(100, 2, seed=b"repro-seed")
    b2 = SymmetricTardosEngine.generate_biases(100, 2, seed=b"repro-seed")
    b3 = SymmetricTardosEngine.generate_biases(100, 2, seed=b"different-seed")

    assert b1 == b2
    assert b1 != b3


def test_codebook_reproducibility_and_properties():
    """Verify codebook generation determinism and distinctness."""
    m = 200
    biases = SymmetricTardosEngine.generate_biases(m, 2, seed=b"seed-cb")
    recipients = ["alice", "bob", "charlie"]

    cb1 = SymmetricTardosEngine.generate_codebook(recipients, biases, seed=b"seed-cb")
    cb2 = SymmetricTardosEngine.generate_codebook(recipients, biases, seed=b"seed-cb")

    assert cb1 == cb2
    assert set(cb1.keys()) == set(recipients)

    # Alice and Bob must receive distinct codewords
    assert cb1["alice"] != cb1["bob"]
    assert len(cb1["alice"]) == m

    # Check symbols are in {0, 1}
    for bit in cb1["alice"]:
        assert bit in (0, 1)


def test_symmetric_scoring_values():
    """Verify the 4 exact branches of the Symmetric Tardos scoring function and erasure handling."""
    p = 0.25
    pos_term = math.sqrt(0.75 / 0.25)  # sqrt(3) ~= 1.732
    neg_term = math.sqrt(0.25 / 0.75)  # sqrt(1/3) ~= 0.577

    # y = 1 cases
    assert SymmetricTardosEngine.score_symbol(1, 1, p) == pytest.approx(pos_term)
    assert SymmetricTardosEngine.score_symbol(1, 0, p) == pytest.approx(-neg_term)

    # y = 0 cases
    assert SymmetricTardosEngine.score_symbol(0, 1, p) == pytest.approx(-pos_term)
    assert SymmetricTardosEngine.score_symbol(0, 0, p) == pytest.approx(neg_term)

    # Erasure (y = -1) or invalid symbol
    assert SymmetricTardosEngine.score_symbol(-1, 1, p) == 0.0
    assert SymmetricTardosEngine.score_symbol(-1, 0, p) == 0.0
    assert SymmetricTardosEngine.score_symbol(99, 1, p) == 0.0


def test_zero_expectation_for_innocent_recipients():
    """
    Empirically test Škorić et al.'s Zero Expectation Theorem:
    For any innocent recipient i, regardless of the leak pattern y_j,
    E[U(y_j, X_{i,j}, p_j)] = 0.
    """
    m = 1000
    c = 2
    seed = b"zero-expectation-test"
    biases = SymmetricTardosEngine.generate_biases(m, c, seed=seed)

    # Arbitrary leak vector y (e.g. alternating bits)
    leak_y = [j % 2 for j in range(m)]

    # Generate 50 independent innocent recipients
    innocent_recipients = [f"innocent_{k}" for k in range(50)]
    codebook = SymmetricTardosEngine.generate_codebook(innocent_recipients, biases, seed=seed)

    scores = SymmetricTardosEngine.score_all(leak_y, codebook, biases)
    score_values = list(scores.values())

    mean_innocent_score = sum(score_values) / len(score_values)
    # The mean across 50 independent innocent users must be close to 0
    # Standard deviation of sum of m terms is O(sqrt(m)) ~= 31.6; standard error of mean ~= 31.6/sqrt(50) ~= 4.5
    assert abs(mean_innocent_score) < 10.0


def test_positive_expectation_for_guilty_colluder():
    """
    Verify that an unauthorized leak of an unaltered recipient copy yields a strongly positive score
    crossing the threshold Z.
    """
    m = 600
    c = 2
    seed = b"guilty-test-seed"
    biases = SymmetricTardosEngine.generate_biases(m, c, seed=seed)

    recipients = ["alice", "bob", "charlie", "dave"]
    codebook = SymmetricTardosEngine.generate_codebook(recipients, biases, seed=seed)

    # Bob's copy leaks unaltered
    leak_bob = codebook["bob"]

    scores = SymmetricTardosEngine.score_all(leak_bob, codebook, biases)
    threshold = SymmetricTardosEngine.compute_threshold(m, len(recipients), epsilon_1=1e-4)

    result = SymmetricTardosEngine.accuse(scores, threshold, epsilon_1=1e-4)

    assert result.status == AccusationStatus.ATTRIBUTED
    assert "bob" in result.accused_recipients
    assert result.max_score > threshold
    assert result.margin > 0.0

    # Innocent users must not cross threshold
    for rec in ["alice", "charlie", "dave"]:
        assert scores[rec] < threshold


def test_codebook_mismatch_yields_no_signal():
    """
    Verify that decoding a leak against a mismatched seed / wrong document codebook
    yields no false accusations and abstains fail-closed.
    """
    m = 500
    c = 2
    doc_a_seed = b"doc-A-seed-secret"
    doc_b_seed = b"doc-B-seed-secret"

    biases_a = SymmetricTardosEngine.generate_biases(m, c, seed=doc_a_seed)
    codebook_a = SymmetricTardosEngine.generate_codebook(["bob"], biases_a, seed=doc_a_seed)

    biases_b = SymmetricTardosEngine.generate_biases(m, c, seed=doc_b_seed)
    codebook_b = SymmetricTardosEngine.generate_codebook(["alice", "bob", "charlie"], biases_b, seed=doc_b_seed)

    # Bob leaks from Doc A, but verifier tests against Doc B's codebook
    scores = SymmetricTardosEngine.score_all(codebook_a["bob"], codebook_b, biases_b)
    threshold = SymmetricTardosEngine.compute_threshold(m, len(codebook_b), epsilon_1=1e-4)

    result = SymmetricTardosEngine.accuse(scores, threshold, epsilon_1=1e-4)

    # All recipients must be innocent relative to Doc B codebook
    assert result.status in (AccusationStatus.NO_SIGNAL, AccusationStatus.INSUFFICIENT_EVIDENCE)
    assert len(result.accused_recipients) == 0
    assert result.margin < 0.0
