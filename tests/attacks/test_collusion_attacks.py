import json
import pytest
from attacks.collusion.primitives import (
    AveragingCollusion,
    InterleavingCollusion,
    MajorityVotingCollusion,
    MinorityVotingCollusion,
    RandomSymbolSelectionCollusion,
    ErasureCollusion,
    SymbolSubstitutionCollusion,
    CodewordMixingCollusion,
    GenericCollusionAttack,
)

@pytest.fixture
def mock_coalition_binary():
    # 3 colluders with 8 symbols each
    return [
        [1, 1, 0, 0, 1, 0, 1, 0],
        [1, 0, 0, 1, 1, 0, 0, 1],
        [1, 1, 0, 1, 0, 0, 1, 1],
    ]

def test_averaging_collusion(mock_coalition_binary):
    # Position 0: all 1 -> avg 1.0 -> 1
    # Position 2: all 0 -> avg 0.0 -> 0
    # Position 1: [1, 0, 1] -> avg 2/3 (0.667) -> rounds to 1
    res = AveragingCollusion.collude(mock_coalition_binary, round_to_int=True)
    assert len(res) == 8
    assert res[0] == 1
    assert res[2] == 0
    assert res[1] == 1

def test_majority_voting_collusion(mock_coalition_binary):
    res = MajorityVotingCollusion.collude(mock_coalition_binary, seed=42)
    assert len(res) == 8
    # Position 0: [1, 1, 1] -> 1
    assert res[0] == 1
    # Position 1: [1, 0, 1] -> 1
    assert res[1] == 1
    # Position 2: [0, 0, 0] -> 0
    assert res[2] == 0

def test_minority_voting_collusion(mock_coalition_binary):
    res = MinorityVotingCollusion.collude(mock_coalition_binary, seed=42)
    assert len(res) == 8
    # Position 1: [1, 0, 1] -> minority is 0
    assert res[1] == 0

def test_interleaving_collusion(mock_coalition_binary):
    # Block size 2: takes 2 from c0, 2 from c1, 2 from c2, 2 from c0
    res = InterleavingCollusion.collude(mock_coalition_binary, block_size=2)
    assert len(res) == 8
    assert res[0:2] == mock_coalition_binary[0][0:2]
    assert res[2:4] == mock_coalition_binary[1][2:4]
    assert res[4:6] == mock_coalition_binary[2][4:6]
    assert res[6:8] == mock_coalition_binary[0][6:8]

def test_random_symbol_selection_is_seeded(mock_coalition_binary):
    res1 = RandomSymbolSelectionCollusion.collude(mock_coalition_binary, seed=777)
    res2 = RandomSymbolSelectionCollusion.collude(mock_coalition_binary, seed=777)
    assert res1 == res2
    # Verify symbols all come from valid colluders at each position
    for j in range(8):
        valid = {c[j] for c in mock_coalition_binary}
        assert res1[j] in valid

def test_erasure_collusion_marking_assumption(mock_coalition_binary):
    # Where all match -> symbol preserved. Where they differ -> -1
    res = ErasureCollusion.collude(mock_coalition_binary, erasure_value=-1)
    assert res[0] == 1  # [1, 1, 1] match
    assert res[2] == 0  # [0, 0, 0] match
    assert res[5] == 0  # [0, 0, 0] match
    assert res[1] == -1 # [1, 0, 1] differ
    assert res[3] == -1 # [0, 1, 1] differ

def test_symbol_substitution_collusion():
    base = [0] * 100
    res = SymbolSubstitutionCollusion.collude(base, substitution_rate=0.2, alphabet=(0, 1), seed=42)
    assert len(res) == 100
    flipped_count = sum(1 for x in res if x == 1)
    assert 10 <= flipped_count <= 30  # roughly 20%

def test_codeword_mixing_collusion(mock_coalition_binary):
    res = CodewordMixingCollusion.collude(mock_coalition_binary, mix_ratio=0.5, seed=42)
    assert len(res) == 8

def test_generic_collusion_attack_pipeline(mock_coalition_binary):
    attack = GenericCollusionAttack()
    payload = json.dumps({"coalition": mock_coalition_binary, "strategy": "majority"}).encode('utf-8')
    res = attack.apply(payload, seed=42)
    assert res.success is True
    assert res.output_type == "FINGERPRINT_VECTOR"
    data = json.loads(attack._execute_transform(payload, {}, 42).artifact_bytes.decode('utf-8'))
    assert data["strategy"] == "majority"
    assert data["code_length"] == 8

def test_coalition_validation_errors():
    with pytest.raises(ValueError, match="at least one codeword"):
        MajorityVotingCollusion.collude([])

    with pytest.raises(ValueError, match="expected 4"):
        MajorityVotingCollusion.collude([[1, 0, 1, 0], [1, 0]])
