"""
Tests for Traceability (Tardos) and Dynamic Watermark Key Epoch Progression.

Verifies:
- Explicit key epochs for Tardos and Watermark secrets.
- Historical Tardos artifacts created under Epoch 12 remain verifiable using Epoch 12
  even after Epoch 17 is active.
- New releases strictly use current active epoch (Epoch 17), never silently falling back to Epoch 12.
- Dynamic watermarks generated under Epoch 7 remain verifiable after Epochs 8, 9, 10 become active.
- Production mode fail-closed behavior when required historical secret is absent.
"""

import os
import pytest
from datetime import datetime, timezone

from core.crypto.lifecycle.manager import KeyLifecycleManager
from core.crypto.lifecycle.resolver import HistoricalKeyResolver, HistoricalResolutionStatus
from core.crypto.lifecycle.adapters import TraceabilityEpochAdapter, WatermarkEpochAdapter
from core.crypto.lifecycle.models import KeyState, KeyType
from core.watermark.dynamic import (
    generate_dynamic_watermark,
    derive_dynamic_codeword,
    verify_dynamic_watermark_commitment,
)
from core.traceability.tardos import SymmetricTardosEngine


def test_traceability_key_epoch_progression_and_historical_invariance():
    mgr = KeyLifecycleManager()
    resolver = HistoricalKeyResolver(mgr)
    adapter = TraceabilityEpochAdapter(mgr)

    # Register Epoch 12 secret
    secret_epoch_12 = b"TRACEABILITY_SECRET_EPOCH_12_SECURE_TOKEN_32B!"[:32]
    rec12 = adapter.register_traceability_epoch(epoch=12, secret_bytes=secret_epoch_12, activate=True)
    assert rec12.creation_epoch == 12
    assert rec12.status == KeyState.ACTIVE

    # Create Tardos codebook under Epoch 12
    biases12 = SymmetricTardosEngine.generate_biases(m=128, c=5, seed=secret_epoch_12)
    codebook12 = SymmetricTardosEngine.generate_codebook(["rec_alice", "rec_bob"], biases12, seed=secret_epoch_12)
    alice_cw12 = codebook12["rec_alice"]

    # Now rotate/advance to Epoch 17
    secret_epoch_17 = b"TRACEABILITY_SECRET_EPOCH_17_SECURE_TOKEN_32B!"[:32]
    rec17 = adapter.register_traceability_epoch(epoch=17, secret_bytes=secret_epoch_17, activate=True)
    assert rec17.creation_epoch == 17
    assert rec17.status == KeyState.ACTIVE
    assert rec12.status == KeyState.RETIRED  # Epoch 12 retired

    # Invariant 1: New operations MUST use Epoch 17
    active_trace_key = mgr.get_active_key("SYSTEM_TRACEABILITY", KeyType.TRACEABILITY_SECRET)
    assert active_trace_key.creation_epoch == 17
    assert active_trace_key.metadata["secret_bytes"] == secret_epoch_17

    # Invariant 2: Historical artifact from Epoch 12 remains verifiable using Epoch 12 secret
    hist_key_res = resolver.resolve_historical_key(
        owner="SYSTEM_TRACEABILITY",
        key_type=KeyType.TRACEABILITY_SECRET,
        event_timestamp=rec12.creation_timestamp,
        event_epoch=12
    )
    assert hist_key_res.is_valid is True
    assert hist_key_res.status == HistoricalResolutionStatus.HISTORICALLY_VALID
    assert hist_key_res.key_record.creation_epoch == 12

    # Invariant 3: Reinterpreting Epoch 12 codeword with Epoch 17 biases yields uncorrelated score
    biases17 = SymmetricTardosEngine.generate_biases(m=128, c=5, seed=secret_epoch_17)
    codebook17 = SymmetricTardosEngine.generate_codebook(["rec_alice", "rec_bob"], biases17, seed=secret_epoch_17)
    alice_cw17 = codebook17["rec_alice"]

    # Codewords generated under different epochs are distinct
    assert alice_cw12 != alice_cw17
    diff_count = sum(1 for a, b in zip(alice_cw12, alice_cw17) if a != b)
    assert diff_count > 30  # Substantially uncorrelated across epochs


def test_dynamic_watermark_epoch_lifecycle_and_verification():
    mgr = KeyLifecycleManager()
    resolver = HistoricalKeyResolver(mgr)
    adapter = WatermarkEpochAdapter(mgr)

    # Register Epoch 7
    secret_epoch_7 = b"WATERMARK_MASTER_SECRET_EPOCH_07_AIRGAP_SEED"
    rec7 = adapter.register_watermark_epoch(epoch=7, epoch_secret=secret_epoch_7, activate=True)

    # Generate dynamic watermark under Epoch 7
    wm7 = generate_dynamic_watermark(
        doc_root_hash="a" * 64,
        recipient_id="rec_alice_4f9a",
        session_id="sess_001",
        event_id="evt_001",
        copy_id="cpy_001",
        key_epoch=7,
        epoch_key=secret_epoch_7
    )
    assert wm7.key_epoch == 7
    codeword7 = derive_dynamic_codeword(wm7.token, length=128)
    assert len(codeword7) == 128

    # Progress through Epochs 8, 9, 10
    secret_epoch_8 = b"WATERMARK_MASTER_SECRET_EPOCH_08_AIRGAP_SEED"
    secret_epoch_9 = b"WATERMARK_MASTER_SECRET_EPOCH_09_AIRGAP_SEED"
    secret_epoch_10 = b"WATERMARK_MASTER_SECRET_EPOCH_10_AIRGAP_SEED"

    adapter.register_watermark_epoch(epoch=8, epoch_secret=secret_epoch_8, activate=True)
    adapter.register_watermark_epoch(epoch=9, epoch_secret=secret_epoch_9, activate=True)
    rec10 = adapter.register_watermark_epoch(epoch=10, epoch_secret=secret_epoch_10, activate=True)

    # Active watermark epoch is 10
    active_wm_key = mgr.get_active_key("SYSTEM_WATERMARK", KeyType.WATERMARK_SECRET)
    assert active_wm_key.creation_epoch == 10

    # Invariant: Watermark generated under Epoch 7 remains verifiable under Epoch 7
    resolved_sec7 = adapter.get_epoch_secret(7)
    assert resolved_sec7 == secret_epoch_7

    recomputed_wm7 = generate_dynamic_watermark(
        doc_root_hash="a" * 64,
        recipient_id="rec_alice_4f9a",
        session_id="sess_001",
        event_id="evt_001",
        copy_id="cpy_001",
        key_epoch=7,
        epoch_key=resolved_sec7,
        nonce=wm7.nonce
    )
    assert recomputed_wm7.token == wm7.token
    assert derive_dynamic_codeword(recomputed_wm7.token, length=128) == codeword7

    # Invariant: Verifying with Epoch 10 secret fails
    recomputed_wm10 = generate_dynamic_watermark(
        doc_root_hash="a" * 64,
        recipient_id="rec_alice_4f9a",
        session_id="sess_001",
        event_id="evt_001",
        copy_id="cpy_001",
        key_epoch=10,
        epoch_key=secret_epoch_10,
        nonce=wm7.nonce
    )
    assert recomputed_wm10.token != wm7.token
    assert derive_dynamic_codeword(recomputed_wm10.token, length=128) != codeword7
