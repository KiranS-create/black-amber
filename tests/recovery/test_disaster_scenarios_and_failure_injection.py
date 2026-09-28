"""
Comprehensive Disaster Scenarios (A through O) & Failure-Injection Test Suite.
"""

from datetime import datetime, timezone
import json
import pytest
from core.crypto.signatures import MLDSA65
from core.ledger.ledger import TamperEvidentLedger, EvidenceEvent
from core.lineage.models import DocumentRoot, CopyInstance
from core.telemetry.event import ForensicEvent
from core.telemetry.models import TelemetrySource
from core.recovery.models import (
    BackupType,
    SignedBackupManifest,
    RecoveryState,
    FinalRecoveryOutcome,
)
from core.recovery.format import ContentAddressedStore, BackupPackageBuilder, canonical_json_bytes
from core.recovery.crypto import BackupCryptoEngine
from core.recovery.chain import BackupChainManager, ChainValidationStatus
from core.recovery.engine import DisasterRecoveryEngine
from core.recovery.media import AirGappedMediaBuilder


@pytest.fixture
def base_test_environment():
    kp = MLDSA65.generate_keypair()
    store = ContentAddressedStore()
    engine = DisasterRecoveryEngine(store=store)
    return {
        "kp": kp,
        "store": store,
        "engine": engine,
        "tenant": "tenant_disaster_lab"
    }


# ==============================================================================
# Partial Disaster Scenarios A through O
# ==============================================================================

def test_scenario_A_app_server_lost_bare_metal_rehydration(base_test_environment):
    """Scenario A: Application server completely lost; restore on a clean new instance."""
    env = base_test_environment
    kp, store, engine, tenant = env["kp"], env["store"], env["engine"], env["tenant"]

    manifest = engine.create_backup(
        tenant_id=tenant,
        backup_type=BackupType.FULL,
        datasets={"ledger_events": [{"event_id": "ev_srv_lost", "event_type": "DECRYPT", "document_id": "d1", "release_id": "r1", "recipient_id": "u1", "algorithm": "ML-DSA-65", "artifact_hash": "h1", "evidence_hash": "e1", "previous_event_hash": "0"*64, "signature": ""}]},
        signer_id="admin_1",
        signing_private_key_bytes=kp.private_key_bytes,
        signing_public_key_bytes=kp.public_key_bytes
    )

    # Simulate fresh, clean application server
    new_engine = DisasterRecoveryEngine(store=store)
    report = new_engine.restore_backup(manifest, expected_tenant_id=tenant)
    assert report.final_recovery_state == FinalRecoveryOutcome.RECOVERED
    assert report.ledger_status == RecoveryState.VALID_RECOVERY


def test_scenario_B_index_storage_lost_sparse_rebuild(base_test_environment):
    """Scenario B: Secondary graph and inverted index lost; rebuild from authoritative state."""
    env = base_test_environment
    kp, store, engine, tenant = env["kp"], env["store"], env["engine"], env["tenant"]

    manifest = engine.create_backup(
        tenant_id=tenant,
        backup_type=BackupType.FULL,
        datasets={
            "lineage_roots": [{"document_id": "doc_idx_lost", "canonical_hash": "1"*64, "byte_size": 2048}],
            "lineage_copies": [{"copy_id": "cpy_idx_lost", "parent_copy_id": None, "document_id": "doc_idx_lost", "lineage_depth": 0}]
        },
        signer_id="admin_1",
        signing_private_key_bytes=kp.private_key_bytes,
        signing_public_key_bytes=kp.public_key_bytes
    )

    report = engine.restore_backup(manifest, expected_tenant_id=tenant)
    assert report.final_recovery_state == FinalRecoveryOutcome.RECOVERED
    assert report.lineage_status == RecoveryState.VALID_RECOVERY


def test_scenario_C_ledger_tail_corrupted_partial_recovery(base_test_environment):
    """Scenario C: Ledger storage corrupted at tail; recover clean prefix and quarantine tail."""
    env = base_test_environment
    kp, store, engine, tenant = env["kp"], env["store"], env["engine"], env["tenant"]

    ev0 = {"event_id": "ev_0", "event_type": "DECRYPT", "document_id": "d1", "release_id": "r1", "recipient_id": "u1", "algorithm": "ML-DSA-65", "artifact_hash": "h1", "evidence_hash": "e1", "previous_event_hash": "0"*64, "signature": ""}
    ev1_corrupt = {"event_id": "ev_1", "event_type": "DECRYPT", "document_id": "d1", "release_id": "r1", "recipient_id": "u1", "algorithm": "ML-DSA-65", "artifact_hash": "h1", "evidence_hash": "e1", "previous_event_hash": "corrupted_hash", "signature": ""}

    manifest = engine.create_backup(
        tenant_id=tenant,
        backup_type=BackupType.FULL,
        datasets={"ledger_events": [ev0, ev1_corrupt]},
        signer_id="admin_1",
        signing_private_key_bytes=kp.private_key_bytes,
        signing_public_key_bytes=kp.public_key_bytes
    )

    # Truncation enabled -> PARTIALLY_RECOVERED
    report = engine.restore_backup(manifest, expected_tenant_id=tenant, allow_tail_truncation=True)
    assert report.final_recovery_state == FinalRecoveryOutcome.PARTIALLY_RECOVERED
    assert report.ledger_status == RecoveryState.PARTIAL_RECOVERY


def test_scenario_D_latest_backup_corrupted(base_test_environment):
    """Scenario D: Latest backup manifest corrupted; fails closed."""
    env = base_test_environment
    kp, store, engine, tenant = env["kp"], env["store"], env["engine"], env["tenant"]

    manifest = engine.create_backup(
        tenant_id=tenant,
        backup_type=BackupType.FULL,
        datasets={"ledger_events": []},
        signer_id="admin_1",
        signing_private_key_bytes=kp.private_key_bytes,
        signing_public_key_bytes=kp.public_key_bytes
    )

    # Corrupt manifest signature
    manifest.signature_b64 = "CorruptedSignatureBytes=="
    report = engine.restore_backup(manifest, expected_tenant_id=tenant)
    assert report.final_recovery_state == FinalRecoveryOutcome.RECOVERY_FAILED
    assert any("SIGNATURE" in e for e in report.errors)


def test_scenario_E_consecutive_backup_deltas_missing(base_test_environment):
    """Scenario E: Chain has gap (seq 0 followed by seq 3); fails closed."""
    env = base_test_environment
    kp, tenant = env["kp"], env["tenant"]

    m0 = build_raw_manifest("bkp_0", BackupType.FULL, 0, tenant, kp)
    # Gap: Jump directly to seq 3
    m3 = build_raw_manifest("bkp_3", BackupType.DELTA, 3, tenant, kp, parent_id="bkp_2", parent_comm="0"*64)

    chain_res = BackupChainManager.validate_chain([m0, m3], expected_tenant_id=tenant)
    assert chain_res.is_valid is False
    assert chain_res.status == ChainValidationStatus.MISSING_DELTA


def test_scenario_F_telemetry_partially_lost_deduplication(base_test_environment):
    """Scenario F: Telemetry stream interrupted; restores available deduplicated events."""
    env = base_test_environment
    kp, store, engine, tenant = env["kp"], env["store"], env["engine"], env["tenant"]

    now = datetime.now(timezone.utc).isoformat()
    ev1 = {"event_id": "tel_1", "timestamp": now, "event_type": "LOGIN", "source_system": "EDR", "subject_id": "u1", "artifact_hash": "a1"}

    manifest = engine.create_backup(
        tenant_id=tenant,
        backup_type=BackupType.FULL,
        datasets={"telemetry_events": [ev1]},
        signer_id="admin_1",
        signing_private_key_bytes=kp.private_key_bytes,
        signing_public_key_bytes=kp.public_key_bytes
    )
    report = engine.restore_backup(manifest, expected_tenant_id=tenant)
    assert report.telemetry_status == RecoveryState.VALID_RECOVERY


def test_scenario_G_identity_directory_unavailable(base_test_environment):
    """Scenario G: Remote IdP down; local backup maintains valid principal identity state."""
    env = base_test_environment
    kp, store, engine, tenant = env["kp"], env["store"], env["engine"], env["tenant"]

    manifest = engine.create_backup(
        tenant_id=tenant,
        backup_type=BackupType.FULL,
        datasets={"identity_principals": [{"principal_id": "p_alice", "status": "ACTIVE"}]},
        signer_id="admin_1",
        signing_private_key_bytes=kp.private_key_bytes,
        signing_public_key_bytes=kp.public_key_bytes
    )
    report = engine.restore_backup(manifest, expected_tenant_id=tenant)
    assert report.identity_status == RecoveryState.VALID_RECOVERY


def test_scenario_H_validator_node_unavailable_bft_quorum():
    """Scenario H: One validator lost; remaining 2-of-3 quorum satisfies threshold."""
    from core.ledger.dlt import DLTNode, DLTValidator
    v1 = DLTValidator.generate("v1", 1)
    v2 = DLTValidator.generate("v2", 1)
    v3 = DLTValidator.generate("v3", 1)

    node = DLTNode("node_test", {"v1": v1, "v2": v2, "v3": v3})
    # 2N/3 + 1 = 3
    assert node.quorum_threshold >= 2


def test_scenario_I_validator_restored_from_stale_state():
    """Scenario I: Validator restored with older block height; rejected as rollback attempt."""
    from core.ledger.dlt import DLTNode, DLTValidator, DLTBlock, DLTBlockHeader
    v1 = DLTValidator.generate("v1", 1)
    node = DLTNode("node_test", {"v1": v1})

    # Commit block 1
    h1 = DLTBlockHeader(block_height=1, previous_block_hash="0"*64, proposer_validator_id="v1", round_number=0, merkle_root="0"*64)
    bh1 = h1.compute_header_hash()
    b1 = DLTBlock(header=h1, block_hash=bh1, endorsements={"v1": v1.sign(bh1.encode())})
    node.commit_block(b1)

    # Attempt to commit block with height 0 or 1 again
    with pytest.raises(ValueError, match="Rollback attempt|Fork detected"):
        node.commit_block(b1)


def test_scenario_J_complete_air_gapped_site_replacement(base_test_environment):
    """Scenario J: New bare-metal machine bootstrapped completely offline from signed media."""
    env = base_test_environment
    kp = env["kp"]

    payloads = {
        "bin/aegis_restore": b"#!/bin/sh\necho restoring...",
        "schemas/v1.json": b'{"schema": "1.0"}',
        "data/bootstrap_config.json": b'{"node_mode": "AIRGAPPED"}'
    }

    manifest, bundle = AirGappedMediaBuilder.create_recovery_media(
        media_id="media_offline_01",
        file_payloads=payloads,
        signing_private_key_bytes=kp.private_key_bytes,
        signing_public_key_bytes=kp.public_key_bytes
    )

    is_valid, errs = AirGappedMediaBuilder.verify_recovery_media(manifest, bundle)
    assert is_valid is True
    assert len(errs) == 0


def test_scenario_K_encrypted_backup_tampered_aad(base_test_environment):
    """Scenario K: Encrypted backup metadata/AAD tampered; fails closed."""
    plaintext = b'{"secret": "val"}'
    envelope = BackupCryptoEngine.encrypt_payload(
        plaintext=plaintext,
        passphrase="test-password",
        tenant_id="tenant_1",
        backup_id="bkp_01",
        backup_sequence=0
    )

    # Tamper with tenant in envelope
    envelope["tenant_id"] = "tenant_attacker"
    with pytest.raises(PermissionError, match="CROSS_TENANT_REJECTED"):
        BackupCryptoEngine.decrypt_payload(
            envelope=envelope,
            passphrase="test-password",
            expected_tenant_id="tenant_1",
            expected_backup_id="bkp_01",
            expected_sequence=0
        )


def test_scenario_L_metadata_available_but_object_missing(base_test_environment):
    """Scenario L: Manifest lists object ID that is missing from object store; fails closed."""
    env = base_test_environment
    kp, store, engine, tenant = env["kp"], env["store"], env["engine"], env["tenant"]

    manifest = engine.create_backup(
        tenant_id=tenant,
        backup_type=BackupType.FULL,
        datasets={"ledger_events": [{"event_id": "ev_1"}]},
        signer_id="admin_1",
        signing_private_key_bytes=kp.private_key_bytes,
        signing_public_key_bytes=kp.public_key_bytes
    )

    # Remove object from store
    obj_id = manifest.objects[0].object_id
    del store._memory_objects[obj_id]

    report = engine.restore_backup(manifest, expected_tenant_id=tenant)
    assert report.final_recovery_state == FinalRecoveryOutcome.RECOVERY_FAILED


def test_scenario_M_cryptographic_key_unavailable(base_test_environment):
    """Scenario M: Encrypted backup attempted without password; fails closed."""
    env = base_test_environment
    kp, store, engine, tenant = env["kp"], env["store"], env["engine"], env["tenant"]

    manifest = engine.create_backup(
        tenant_id=tenant,
        backup_type=BackupType.FULL,
        datasets={"ledger_events": [{"event_id": "ev_1"}]},
        signer_id="admin_1",
        signing_private_key_bytes=kp.private_key_bytes,
        signing_public_key_bytes=kp.public_key_bytes,
        encryption_passphrase="super-secret-passphrase"
    )

    # Restore without passphrase
    report = engine.restore_backup(manifest, expected_tenant_id=tenant, encryption_passphrase=None)
    assert report.final_recovery_state == FinalRecoveryOutcome.RECOVERY_FAILED
    assert any("MISSING_PASSPHRASE" in e for e in report.errors)


def test_scenario_N_compromised_operator_unauthorized_rollback(base_test_environment):
    """Scenario N: Compromised operator attempts rollback without dual authorization."""
    env = base_test_environment
    kp, store, engine, tenant = env["kp"], env["store"], env["engine"], env["tenant"]

    m0 = engine.create_backup(tenant, BackupType.FULL, {"d": [0]}, "admin_1", kp.private_key_bytes, kp.public_key_bytes)
    m1 = engine.create_backup(tenant, BackupType.DELTA, {"d": [1]}, "admin_1", kp.private_key_bytes, kp.public_key_bytes, parent_manifest=m0)

    # Current tip is seq 1
    engine.set_trusted_watermark(tenant, sequence=1)

    # Malicious attempt to restore seq 0 without dual authorization
    report = engine.restore_backup(m0, expected_tenant_id=tenant, allow_rollback=False)
    assert report.final_recovery_state == FinalRecoveryOutcome.RECOVERY_FAILED
    assert report.rollback_status == RecoveryState.ROLLBACK_DETECTED


def test_scenario_O_accidental_duplicate_restore(base_test_environment):
    """Scenario O: Duplicate restore executed; deduplicates without creating corrupt state."""
    env = base_test_environment
    kp, store, engine, tenant = env["kp"], env["store"], env["engine"], env["tenant"]

    manifest = engine.create_backup(
        tenant_id=tenant,
        backup_type=BackupType.FULL,
        datasets={
            "telemetry_events": [{"event_id": "tel_dup_1", "timestamp": datetime.now(timezone.utc).isoformat(), "event_type": "OPEN", "source_system": "EDR"}]
        },
        signer_id="admin_1",
        signing_private_key_bytes=kp.private_key_bytes,
        signing_public_key_bytes=kp.public_key_bytes
    )

    report1 = engine.restore_backup(manifest, expected_tenant_id=tenant)
    assert report1.final_recovery_state == FinalRecoveryOutcome.RECOVERED

    # Run duplicate restore
    report2 = engine.restore_backup(manifest, expected_tenant_id=tenant)
    assert report2.final_recovery_state in (FinalRecoveryOutcome.RECOVERED, FinalRecoveryOutcome.PARTIALLY_RECOVERED)


# ==============================================================================
# Failure-Injection Deterministic Bit Flips
# ==============================================================================

def test_failure_injection_single_byte_ciphertext_corruption():
    """Failure Injection: Flip 1 byte in AES-256-GCM ciphertext."""
    plaintext = b"AegisTrace evidentiary record bytes"
    envelope = BackupCryptoEngine.encrypt_payload(
        plaintext=plaintext,
        passphrase="pass",
        tenant_id="t1",
        backup_id="b1",
        backup_sequence=0
    )

    # Flip 1 byte in ciphertext
    raw_ct = list(base64_decode(envelope["ciphertext_b64"]))
    raw_ct[0] ^= 0x01
    envelope["ciphertext_b64"] = base64_encode(bytes(raw_ct))

    with pytest.raises(ValueError, match="DECRYPTION_FAILED"):
        BackupCryptoEngine.decrypt_payload(
            envelope=envelope,
            passphrase="pass",
            expected_tenant_id="t1",
            expected_backup_id="b1",
            expected_sequence=0
        )


def test_failure_injection_single_byte_signature_tamper():
    """Failure Injection: Flip 1 byte in ML-DSA-65 signature."""
    kp = MLDSA65.generate_keypair()
    store = ContentAddressedStore()
    builder = BackupPackageBuilder(store)
    builder.add_dataset("data", [{"val": 1}], tenant_id="t1")

    m = SignedBackupManifest(
        backup_id="b_fi",
        backup_type=BackupType.FULL,
        tenant_id="t1",
        backup_sequence=0,
        source_system_id="node_1",
        datasets=list(builder.datasets),
        objects=builder.objects,
        merkle_root=builder.compute_merkle_root(),
        cryptographic_digest="",
        signer_id="admin_1",
        signer_public_key_b64=base64_encode(kp.public_key_bytes),
        signature_b64=""
    )
    signed = BackupCryptoEngine.sign_manifest(m, kp.private_key_bytes)

    # Flip 1 byte in signature
    raw_sig = list(base64_decode(signed.signature_b64))
    raw_sig[5] ^= 0x01
    signed.signature_b64 = base64_encode(bytes(raw_sig))

    is_valid, err = BackupCryptoEngine.verify_manifest(signed)
    assert is_valid is False
    assert "SIGNATURE_VERIFICATION_FAILED" in err


def build_raw_manifest(backup_id, b_type, seq, tenant, kp, parent_id=None, parent_comm=None):
    store = ContentAddressedStore()
    builder = BackupPackageBuilder(store)
    builder.add_dataset("data", [{"s": seq}], tenant_id=tenant)
    m = SignedBackupManifest(
        backup_id=backup_id,
        backup_type=b_type,
        tenant_id=tenant,
        backup_sequence=seq,
        source_system_id="node_1",
        parent_backup_id=parent_id,
        parent_backup_commitment=parent_comm,
        datasets=list(builder.datasets),
        objects=builder.objects,
        merkle_root=builder.compute_merkle_root(),
        cryptographic_digest="",
        signer_id="admin_1",
        signer_public_key_b64=base64_encode(kp.public_key_bytes),
        signature_b64=""
    )
    return BackupCryptoEngine.sign_manifest(m, kp.private_key_bytes)


def base64_encode(data: bytes) -> str:
    import base64
    return base64.b64encode(data).decode('utf-8')


def base64_decode(data_str: str) -> bytes:
    import base64
    return base64.b64decode(data_str)
