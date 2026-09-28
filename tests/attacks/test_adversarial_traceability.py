import pytest
import math
from core.traceability.tardos import (
    SymmetricTardosEngine,
    AccusationStatus,
)
from core.traceability.collusion import (
    majority_collusion,
    interleaving_collusion,
    random_symbol_collusion,
    minimax_collusion,
    all_zeros_collusion,
    all_ones_collusion,
    apply_noise_and_erasure,
)

@pytest.fixture
def tardos_scenario():
    m = 1200
    c = 2
    epsilon_1 = 1e-4
    seed = b"traceability-adversarial-seed-2026"
    recipients = ["alice", "bob", "charlie", "dave", "eve"]

    biases = SymmetricTardosEngine.generate_biases(m, c, seed=seed)
    codebook = SymmetricTardosEngine.generate_codebook(recipients, biases, seed=seed)
    threshold = SymmetricTardosEngine.compute_threshold(m, len(recipients), epsilon_1=epsilon_1)

    return {
        "m": m,
        "c": c,
        "epsilon_1": epsilon_1,
        "seed": seed,
        "recipients": recipients,
        "biases": biases,
        "codebook": codebook,
        "threshold": threshold,
    }

def test_codeword_truncation_fail_closed(tardos_scenario):
    env = tardos_scenario
    bob_codeword = env["codebook"]["bob"]

    # Truncate to only 20% of symbols (e.g. 240 symbols instead of 1200)
    truncated = bob_codeword[:240] + [-1] * (env["m"] - 240)

    scores = SymmetricTardosEngine.score_all(truncated, env["codebook"], env["biases"])
    result = SymmetricTardosEngine.accuse(
        scores, env["threshold"], epsilon_1=env["epsilon_1"], observed_length=env["m"], erasure_count=960
    )

    # With 80% erasures, score should drop below threshold Z and abstain fail-closed
    assert result.status in (AccusationStatus.INSUFFICIENT_EVIDENCE, AccusationStatus.NO_SIGNAL)
    assert len(result.accused_recipients) == 0
    # Innocent recipients must never exceed threshold
    for inn in ["alice", "charlie", "dave", "eve"]:
        assert scores[inn] < env["threshold"]

def test_symbol_flipping_adversarial_corruption(tardos_scenario):
    env = tardos_scenario
    bob_codeword = env["codebook"]["bob"]

    # Flip 30% of bits
    noisy = apply_noise_and_erasure(bob_codeword, error_rate=0.30, erasure_rate=0.0, seed=777)
    scores = SymmetricTardosEngine.score_all(noisy, env["codebook"], env["biases"])
    result = SymmetricTardosEngine.accuse(scores, env["threshold"], epsilon_1=env["epsilon_1"])

    # Even with heavy noise, Bob may still be identified or system abstains, but innocents never falsely accused
    for inn in ["alice", "charlie", "dave", "eve"]:
        assert inn not in result.accused_recipients
        assert scores[inn] < env["threshold"]

def test_low_information_all_erasures(tardos_scenario):
    env = tardos_scenario
    all_erasures = [-1] * env["m"]

    scores = SymmetricTardosEngine.score_all(all_erasures, env["codebook"], env["biases"])
    result = SymmetricTardosEngine.accuse(scores, env["threshold"], epsilon_1=env["epsilon_1"])

    assert result.status == AccusationStatus.NO_SIGNAL
    assert len(result.accused_recipients) == 0
    assert result.max_score == 0.0

def test_stale_key_epoch_mismatched_seed(tardos_scenario):
    env = tardos_scenario
    bob_codeword = env["codebook"]["bob"]

    # Verifier uses stale epoch seed (different release/seed)
    stale_seed = b"stale-epoch-2025-invalid-key"
    stale_biases = SymmetricTardosEngine.generate_biases(env["m"], env["c"], seed=stale_seed)
    stale_codebook = SymmetricTardosEngine.generate_codebook(env["recipients"], stale_biases, seed=stale_seed)

    scores = SymmetricTardosEngine.score_all(bob_codeword, stale_codebook, stale_biases)
    result = SymmetricTardosEngine.accuse(scores, env["threshold"], epsilon_1=env["epsilon_1"])

    # Must abstain fail-closed: zero correlation against mismatched seed
    assert result.status in (AccusationStatus.NO_SIGNAL, AccusationStatus.INSUFFICIENT_EVIDENCE)
    assert len(result.accused_recipients) == 0

def test_wrong_recipient_scope(tardos_scenario):
    env = tardos_scenario
    # Collusion between Alice and Bob
    cw_alice = env["codebook"]["alice"]
    cw_bob = env["codebook"]["bob"]
    forged = majority_collusion([cw_alice, cw_bob])

    # Investigator only tests against unrelated recipients
    foreign_recipients = ["frank", "grace", "heidi"]
    foreign_codebook = SymmetricTardosEngine.generate_codebook(foreign_recipients, env["biases"], seed=env["seed"])

    scores = SymmetricTardosEngine.score_all(forged, foreign_codebook, env["biases"])
    result = SymmetricTardosEngine.accuse(scores, env["threshold"], epsilon_1=env["epsilon_1"])

    # Foreign innocent recipients must not be accused
    assert len(result.accused_recipients) == 0
    assert result.status in (AccusationStatus.NO_SIGNAL, AccusationStatus.INSUFFICIENT_EVIDENCE)
