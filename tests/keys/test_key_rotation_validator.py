"""
Tests for DLT Validator Key Lifecycle, Rotation, and Historical Consensus Invariance.
Verifies that:
1. Validator enrollment and active quorum tracking.
2. Blocks signed by validator key K1 remain historically verifiable after K1 -> K2 rotation.
3. New blocks after rotation reject signatures from retired K1.
4. Revoked validators are excluded from active consensus quorum.
"""

import base64
import pytest
from datetime import datetime, timezone, timedelta

from core.crypto.lifecycle.models import KeyState, KeyType
from core.crypto.lifecycle.manager import KeyLifecycleManager
from core.crypto.lifecycle.resolver import HistoricalKeyResolver, HistoricalResolutionStatus
from core.crypto.lifecycle.adapters import ValidatorKeyLifecycleAdapter
from core.crypto.signatures import MLDSA65
from core.ledger.dlt import (
    DLTValidator,
    DLTBlock,
    DLTBlockHeader,
    build_merkle_tree
)


def test_validator_rotation_and_historical_block_invariance():
    mgr = KeyLifecycleManager()
    resolver = HistoricalKeyResolver(mgr)
    adapter = ValidatorKeyLifecycleAdapter(mgr)

    # 1. Create three independent validators with genuine ML-DSA-65 keypairs
    val1_kp1 = MLDSA65.generate_keypair()
    val2_kp = MLDSA65.generate_keypair()
    val3_kp = MLDSA65.generate_keypair()

    val1_pub1_b64 = base64.b64encode(val1_kp1.public_key_bytes).decode("utf-8")
    val2_pub_b64 = base64.b64encode(val2_kp.public_key_bytes).decode("utf-8")
    val3_pub_b64 = base64.b64encode(val3_kp.public_key_bytes).decode("utf-8")

    rec_v1_k1 = adapter.enroll_validator("node_val_1", val1_pub1_b64)
    rec_v2 = adapter.enroll_validator("node_val_2", val2_pub_b64)
    rec_v3 = adapter.enroll_validator("node_val_3", val3_pub_b64)

    assert adapter.is_validator_active("node_val_1")
    assert adapter.is_validator_active("node_val_2")
    assert adapter.is_validator_active("node_val_3")

    # 2. Propose Block 1 at t1, signed by val1 with kp1
    t1_dt = datetime.fromisoformat(rec_v1_k1.creation_timestamp.replace("Z", "+00:00")) + timedelta(seconds=1)
    t1_str = t1_dt.isoformat()

    header1 = DLTBlockHeader(
        block_height=1,
        previous_block_hash="0" * 64,
        proposer_validator_id="node_val_1",
        round_number=0,
        timestamp=t1_str,
        merkle_root=build_merkle_tree([])[0],
        state_root="0" * 64
    )
    block1_hash = header1.compute_header_hash()
    block1_msg = f"AEGIS-BLOCK-CONFIRM:{block1_hash}".encode("utf-8")

    sig1_v1 = base64.b64encode(MLDSA65.sign(val1_kp1.private_key_bytes, block1_msg)).decode("utf-8")
    sig1_v2 = base64.b64encode(MLDSA65.sign(val2_kp.private_key_bytes, block1_msg)).decode("utf-8")

    block1 = DLTBlock(
        header=header1,
        block_hash=block1_hash,
        transactions=[],
        proposer_signature_b64=sig1_v1,
        quorum_signatures={
            "node_val_1": sig1_v1,
            "node_val_2": sig1_v2
        }
    )

    # Verify Block 1 at t1
    val_map_t1 = {
        "node_val_1": DLTValidator(validator_id="node_val_1", public_key_b64=val1_pub1_b64),
        "node_val_2": DLTValidator(validator_id="node_val_2", public_key_b64=val2_pub_b64),
        "node_val_3": DLTValidator(validator_id="node_val_3", public_key_b64=val3_pub_b64)
    }
    valid, errors = block1.verify_block_integrity(val_map_t1, quorum_threshold=2)
    assert valid, f"Block 1 failed: {errors}"

    # 3. Rotate Validator 1: K1 -> K2
    val1_kp2 = MLDSA65.generate_keypair()
    val1_pub2_b64 = base64.b64encode(val1_kp2.public_key_bytes).decode("utf-8")

    retired_v1, new_v1 = adapter.rotate_validator_key("node_val_1", val1_pub2_b64, reason="Routine DLT key rotation")
    assert retired_v1.status == KeyState.RETIRED
    assert new_v1.status == KeyState.ACTIVE
    assert new_v1.key_id != retired_v1.key_id

    # 4. Invariant: Block 1 historical resolution
    # Resolving validator 1 at t1 returns HISTORICALLY_VALID
    res_k1_at_t1 = resolver.resolve_historical_key(
        owner="node_val_1",
        key_type=KeyType.LEDGER_VALIDATOR_KEY,
        event_timestamp=t1_str,
        key_id=retired_v1.key_id
    )
    assert res_k1_at_t1.is_valid
    assert res_k1_at_t1.status == HistoricalResolutionStatus.HISTORICALLY_VALID
    assert res_k1_at_t1.public_material_b64 == val1_pub1_b64

    # 5. Propose Block 2 at t2: Val 1 MUST use new keypair 2
    t2_dt = t1_dt + timedelta(minutes=5)
    t2_str = t2_dt.isoformat()

    header2 = DLTBlockHeader(
        block_height=2,
        previous_block_hash=block1_hash,
        proposer_validator_id="node_val_1",
        round_number=0,
        timestamp=t2_str,
        merkle_root=build_merkle_tree([])[0],
        state_root="0" * 64
    )
    block2_hash = header2.compute_header_hash()
    block2_msg = f"AEGIS-BLOCK-CONFIRM:{block2_hash}".encode("utf-8")

    # If Val 1 attempts to propose Block 2 using RETIRED keypair 1, active validators reject it
    stale_sig2_v1 = base64.b64encode(MLDSA65.sign(val1_kp1.private_key_bytes, block2_msg)).decode("utf-8")
    sig2_v2 = base64.b64encode(MLDSA65.sign(val2_kp.private_key_bytes, block2_msg)).decode("utf-8")

    val_map_t2_active = {
        "node_val_1": DLTValidator(validator_id="node_val_1", public_key_b64=val1_pub2_b64),
        "node_val_2": DLTValidator(validator_id="node_val_2", public_key_b64=val2_pub_b64),
        "node_val_3": DLTValidator(validator_id="node_val_3", public_key_b64=val3_pub_b64)
    }

    stale_block2 = DLTBlock(
        header=header2,
        block_hash=block2_hash,
        transactions=[],
        proposer_signature_b64=stale_sig2_v1,
        quorum_signatures={"node_val_1": stale_sig2_v1, "node_val_2": sig2_v2}
    )
    stale_valid, stale_errors = stale_block2.verify_block_integrity(val_map_t2_active, quorum_threshold=2)
    assert not stale_valid
    assert any("Invalid proposer signature" in e for e in stale_errors)

    # Using valid keypair 2 succeeds
    valid_sig2_v1 = base64.b64encode(MLDSA65.sign(val1_kp2.private_key_bytes, block2_msg)).decode("utf-8")
    valid_block2 = DLTBlock(
        header=header2,
        block_hash=block2_hash,
        transactions=[],
        proposer_signature_b64=valid_sig2_v1,
        quorum_signatures={"node_val_1": valid_sig2_v1, "node_val_2": sig2_v2}
    )
    valid2, errs2 = valid_block2.verify_block_integrity(val_map_t2_active, quorum_threshold=2)
    assert valid2, f"Block 2 failed: {errs2}"


def test_validator_revocation_excludes_from_quorum():
    mgr = KeyLifecycleManager()
    adapter = ValidatorKeyLifecycleAdapter(mgr)

    v1_kp = MLDSA65.generate_keypair()
    v2_kp = MLDSA65.generate_keypair()
    v3_kp = MLDSA65.generate_keypair()

    rec_v1 = adapter.enroll_validator("v1", base64.b64encode(v1_kp.public_key_bytes).decode("utf-8"))
    rec_v2 = adapter.enroll_validator("v2", base64.b64encode(v2_kp.public_key_bytes).decode("utf-8"))
    rec_v3 = adapter.enroll_validator("v3", base64.b64encode(v3_kp.public_key_bytes).decode("utf-8"))

    # Revoke V3
    mgr.revoke_key(rec_v3.key_id, reason="Validator node compromise suspected")
    assert not adapter.is_validator_active("v3")

    # Construct active validator set (only V1 and V2)
    active_val_map = {}
    for vid, kp in [("v1", v1_kp), ("v2", v2_kp), ("v3", v3_kp)]:
        if adapter.is_validator_active(vid):
            active_val_map[vid] = DLTValidator(
                validator_id=vid,
                public_key_b64=base64.b64encode(kp.public_key_bytes).decode("utf-8")
            )

    assert "v3" not in active_val_map
    assert len(active_val_map) == 2

    # A block relying on V3's vote fails quorum if quorum threshold is 2 and only V1 + V3 voted
    header = DLTBlockHeader(
        block_height=3,
        previous_block_hash="0" * 64,
        proposer_validator_id="v1",
        round_number=0,
        merkle_root=build_merkle_tree([])[0],
        state_root="0" * 64
    )
    b_hash = header.compute_header_hash()
    msg = f"AEGIS-BLOCK-CONFIRM:{b_hash}".encode("utf-8")

    sig_v1 = base64.b64encode(MLDSA65.sign(v1_kp.private_key_bytes, msg)).decode("utf-8")
    sig_v3 = base64.b64encode(MLDSA65.sign(v3_kp.private_key_bytes, msg)).decode("utf-8")

    block = DLTBlock(
        header=header,
        block_hash=b_hash,
        transactions=[],
        proposer_signature_b64=sig_v1,
        quorum_signatures={"v1": sig_v1, "v3": sig_v3}
    )
    valid, errors = block.verify_block_integrity(active_val_map, quorum_threshold=2)
    assert not valid
    assert any("unauthorized validator 'v3'" in e for e in errors)
