import pytest
from core.traceability.tardos import (
    SymmetricTardosEngine,
    AccusationStatus,
)
from core.traceability.collusion import (
    verify_marking_assumption,
    majority_collusion,
    interleaving_collusion,
    random_symbol_collusion,
    all_zeros_collusion,
    all_ones_collusion,
    minimax_collusion,
    apply_noise_and_erasure,
)

def test_marking_assumption_validator():
    """Verify that verify_marking_assumption correctly detects violations of the Marking Assumption."""
    c1 = [1, 0, 1, 1, 0]
    c2 = [1, 1, 1, 0, 0]
    # Indices where c1 and c2 agree (undetectable):
    # j=0: both 1
    # j=2: both 1
    # j=4: both 0
    # Indices where they differ (detectable):
    # j=1 (0 vs 1), j=3 (1 vs 0)

    # Valid forged copy adhering to Marking Assumption:
    valid_forged = [1, 1, 1, 1, 0]
    res_valid = verify_marking_assumption([c1, c2], valid_forged)
    assert res_valid["is_valid"] is True
    assert res_valid["violation_count"] == 0
    assert res_valid["undetectable_positions"] == 3
    assert res_valid["detectable_positions"] == 2

    # Invalid forged copy modifying an undetectable position (j=0 changed to 0):
    invalid_forged = [0, 1, 1, 1, 0]
    res_invalid = verify_marking_assumption([c1, c2], invalid_forged)
    assert res_invalid["is_valid"] is False
    assert res_invalid["violation_count"] == 1
    assert res_invalid["violation_indices"] == [0]


def test_collusion_c2_attacks_matrix():
    """
    Test coalition of size c=2 (Alice and Bob) among 10 recipients across multiple attacks:
    - Majority voting
    - Interleaving
    - Random symbol
    - Minimax
    Verify that in every case, at least one of the true colluders is accused,
    and NO innocent recipient is falsely accused.
    """
    m = 1200
    c = 2
    epsilon_1 = 1e-4
    seed = b"c2-collusion-matrix-seed"

    recipients = [f"user_{i}" for i in range(10)]
    recipients[0] = "alice"
    recipients[1] = "bob"
    colluders = ["alice", "bob"]
    innocents = [rec for rec in recipients if rec not in colluders]

    biases = SymmetricTardosEngine.generate_biases(m, c, seed=seed)
    codebook = SymmetricTardosEngine.generate_codebook(recipients, biases, seed=seed)

    colluder_cws = [codebook[col] for col in colluders]
    threshold = SymmetricTardosEngine.compute_threshold(m, len(recipients), epsilon_1=epsilon_1)

    attacks = {
        "majority": majority_collusion(colluder_cws),
        "interleaving": interleaving_collusion(colluder_cws, seed=42),
        "random_symbol": random_symbol_collusion(colluder_cws, seed=42),
        "minimax": minimax_collusion(colluder_cws, biases),
        "all_zeros": all_zeros_collusion(colluder_cws),
        "all_ones": all_ones_collusion(colluder_cws),
    }

    for attack_name, forged_codeword in attacks.items():
        # Verify forged codeword satisfies the Marking Assumption
        ma_check = verify_marking_assumption(colluder_cws, forged_codeword)
        assert ma_check["is_valid"] is True, f"Attack {attack_name} violated marking assumption"

        scores = SymmetricTardosEngine.score_all(forged_codeword, codebook, biases)
        result = SymmetricTardosEngine.accuse(scores, threshold, epsilon_1=epsilon_1)

        assert result.status in (AccusationStatus.ATTRIBUTED, AccusationStatus.COLLUSION_DETECTED), (
            f"Attack {attack_name} failed to attribute: status={result.status}, max_score={result.max_score}, threshold={threshold}"
        )

        # At least one colluder must be in accused_recipients
        accused_colluders = [col for col in colluders if col in result.accused_recipients]
        assert len(accused_colluders) >= 1, f"Attack {attack_name} did not accuse any colluder: {result.accused_recipients}"

        # No innocent recipient may be falsely accused
        for inn in innocents:
            assert inn not in result.accused_recipients, f"Innocent user {inn} falsely accused in {attack_name}!"
            assert scores[inn] < threshold, f"Innocent user {inn} score {scores[inn]} exceeded threshold {threshold}"


def test_collusion_c3_majority_attack():
    """
    Test coalition of size c=3 (Alice, Bob, Charlie) among 15 recipients under majority voting.
    """
    m = 2500
    c = 3
    epsilon_1 = 1e-4
    seed = b"c3-collusion-seed"

    recipients = [f"recipient_{i}" for i in range(15)]
    colluders = [recipients[0], recipients[1], recipients[2]]
    innocents = recipients[3:]

    biases = SymmetricTardosEngine.generate_biases(m, c, seed=seed)
    codebook = SymmetricTardosEngine.generate_codebook(recipients, biases, seed=seed)

    colluder_cws = [codebook[col] for col in colluders]
    forged = majority_collusion(colluder_cws)

    threshold = SymmetricTardosEngine.compute_threshold(m, len(recipients), epsilon_1=epsilon_1)
    scores = SymmetricTardosEngine.score_all(forged, codebook, biases)
    result = SymmetricTardosEngine.accuse(scores, threshold, epsilon_1=epsilon_1)

    assert result.status in (AccusationStatus.ATTRIBUTED, AccusationStatus.COLLUSION_DETECTED)
    assert any(col in result.accused_recipients for col in colluders)
    assert not any(inn in result.accused_recipients for inn in innocents)


def test_collusion_with_noisy_and_erasure_channel():
    """
    Verify attribution resilience when colluders apply an interleaving attack
    followed by 5% bit errors and 15% carrier erasures.
    """
    m = 1500
    c = 2
    epsilon_1 = 1e-4
    seed = b"noisy-collusion-seed"

    recipients = ["alice", "bob", "charlie", "dave", "eve"]
    colluders = ["alice", "bob"]
    innocents = ["charlie", "dave", "eve"]

    biases = SymmetricTardosEngine.generate_biases(m, c, seed=seed)
    codebook = SymmetricTardosEngine.generate_codebook(recipients, biases, seed=seed)

    colluder_cws = [codebook[col] for col in colluders]
    forged = interleaving_collusion(colluder_cws, seed=99)

    # Corrupt with 5% noise and 15% erasures
    noisy_forged = apply_noise_and_erasure(forged, error_rate=0.05, erasure_rate=0.15, seed=123)

    threshold = SymmetricTardosEngine.compute_threshold(m, len(recipients), epsilon_1=epsilon_1)
    scores = SymmetricTardosEngine.score_all(noisy_forged, codebook, biases)
    result = SymmetricTardosEngine.accuse(
        scores, threshold, epsilon_1=epsilon_1, observed_length=m, erasure_count=noisy_forged.count(-1)
    )

    assert result.status in (AccusationStatus.ATTRIBUTED, AccusationStatus.COLLUSION_DETECTED)
    assert any(col in result.accused_recipients for col in colluders)
    assert not any(inn in result.accused_recipients for inn in innocents)
    assert result.erasure_count > 0


def test_massive_erasure_fail_closed_abstention():
    """
    Verify that if the carrier is obliterated (e.g. 85% erasures),
    the system abstains (INSUFFICIENT_EVIDENCE / NO_SIGNAL) rather than falsely accusing an innocent user.
    """
    m = 1000
    c = 2
    epsilon_1 = 1e-4
    seed = b"massive-erasure-seed"

    recipients = ["alice", "bob", "charlie", "dave"]
    colluders = ["alice", "bob"]

    biases = SymmetricTardosEngine.generate_biases(m, c, seed=seed)
    codebook = SymmetricTardosEngine.generate_codebook(recipients, biases, seed=seed)

    colluder_cws = [codebook[col] for col in colluders]
    forged = majority_collusion(colluder_cws)

    # 85% erasures
    ruined_forged = apply_noise_and_erasure(forged, error_rate=0.05, erasure_rate=0.85, seed=456)

    threshold = SymmetricTardosEngine.compute_threshold(m, len(recipients), epsilon_1=epsilon_1)
    scores = SymmetricTardosEngine.score_all(ruined_forged, codebook, biases)
    result = SymmetricTardosEngine.accuse(
        scores, threshold, epsilon_1=epsilon_1, observed_length=m, erasure_count=ruined_forged.count(-1)
    )

    # Must abstain fail-closed: NO_SIGNAL or INSUFFICIENT_EVIDENCE, with zero false accusations
    assert result.status in (AccusationStatus.NO_SIGNAL, AccusationStatus.INSUFFICIENT_EVIDENCE)
    assert len(result.accused_recipients) == 0
