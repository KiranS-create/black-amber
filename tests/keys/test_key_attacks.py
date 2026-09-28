"""
Adversarial Security Audit and Attack Vectors for AegisTrace Key Lifecycle.
Tests 16 distinct attack scenarios:
1. Revoked key reuse for new actions.
2. Compromised key reuse for new actions.
3. Post-revocation timestamp forgery (event after T_revocation).
4. Time-travel paradox (event timestamp preceding key creation).
5. Cross-tenant key injection and query leakage.
6. Forged key metadata and digest tampering.
7. Modified epoch injection / epoch replay.
8. State rollback attack (REVOKED -> ACTIVE, RETIRED -> ACTIVE).
9. Duplicate active key injection on same entity.
10. Stale rotation race condition.
11. Corrupted backup envelope injection.
12. Unauthorized key activation bypass.
13. Custody class downgrade enforcement (DEVELOPMENT_ONLY in non-dev environment).
14. Identity hijacking (attempting to rotate another entity's key).
15. Key suspension enforcement (cannot use SUSPENDED key).
16. Unregistered key ID resolution attempt.
"""

import pytest
import os
import base64
from datetime import datetime, timezone, timedelta

from core.crypto.lifecycle.models import (
    KeyType,
    KeyCustodyClass,
    KeyRecoveryClassification,
    KeyState,
    KeyRecord
)
from core.crypto.lifecycle.manager import KeyLifecycleManager
from core.crypto.lifecycle.resolver import HistoricalKeyResolver, HistoricalResolutionStatus
from core.crypto.lifecycle.state_machine import KeyStateMachine, KeyLifecycleTransitionError
from core.crypto.lifecycle.backup import (
    KeyBackupEngine,
    KeyBackupSecurityError,
    KeyBackupIntegrityError
)


def test_attack_01_revoked_key_reuse():
    mgr = KeyLifecycleManager()
    rec = mgr.register_key(
        owner="rec_attacker_01",
        key_type=KeyType.RECIPIENT_PRIVATE_KEY,
        algorithm="ML-DSA-65",
        purpose="Test",
        activate_immediately=True
    )
    # Revoke
    mgr.revoke_key(rec.key_id, reason="Revocation triggered")

    # Manager must not return this as active key
    active = mgr.get_active_key("rec_attacker_01", KeyType.RECIPIENT_PRIVATE_KEY, algorithm="ML-DSA-65")
    assert active is None

    # Rotating an already revoked key must fail (no active key found)
    with pytest.raises(ValueError, match="No active key found"):
        mgr.rotate_key("rec_attacker_01", KeyType.RECIPIENT_PRIVATE_KEY, algorithm="ML-DSA-65", new_algorithm="ML-DSA-65")


def test_attack_02_compromised_key_reuse():
    mgr = KeyLifecycleManager()
    rec = mgr.register_key(
        owner="rec_attacker_02",
        key_type=KeyType.RECIPIENT_PRIVATE_KEY,
        algorithm="ML-DSA-65",
        purpose="Test",
        activate_immediately=True
    )
    mgr.report_compromise(rec.key_id, reason="Private key leaked on darknet")

    assert mgr.get_active_key("rec_attacker_02", KeyType.RECIPIENT_PRIVATE_KEY, algorithm="ML-DSA-65") is None

    # Cannot transition COMPROMISED -> ACTIVE
    assert not KeyStateMachine.can_transition(KeyState.COMPROMISED, KeyState.ACTIVE)
    comp_rec = mgr.get_key(rec.key_id)
    with pytest.raises(KeyLifecycleTransitionError):
        KeyStateMachine.transition(comp_rec, KeyState.ACTIVE)


def test_attack_03_post_revocation_event_rejected():
    mgr = KeyLifecycleManager()
    resolver = HistoricalKeyResolver(mgr)

    rec = mgr.register_key(
        owner="rec_attacker_03",
        key_type=KeyType.RECIPIENT_PRIVATE_KEY,
        algorithm="ML-DSA-65",
        purpose="Test",
        activate_immediately=True
    )
    mgr.revoke_key(rec.key_id, reason="Explicit revocation")

    # Event timestamp after T_revocation
    rev_rec = mgr.get_key(rec.key_id)
    rev_dt = datetime.fromisoformat(rev_rec.revocation_timestamp.replace("Z", "+00:00"))
    post_rev_time = (rev_dt + timedelta(hours=1)).isoformat()

    res = resolver.resolve_historical_key(
        owner="rec_attacker_03",
        key_type=KeyType.RECIPIENT_PRIVATE_KEY,
        event_timestamp=post_rev_time,
        key_id=rec.key_id
    )
    assert not res.is_valid
    assert res.status == HistoricalResolutionStatus.POST_REVOCATION_REJECTED


def test_attack_04_time_travel_paradox():
    mgr = KeyLifecycleManager()
    resolver = HistoricalKeyResolver(mgr)

    rec = mgr.register_key(
        owner="rec_attacker_04",
        key_type=KeyType.RECIPIENT_PRIVATE_KEY,
        algorithm="ML-DSA-65",
        purpose="Test",
        activate_immediately=True
    )
    # Event timestamp BEFORE key creation
    created_dt = datetime.fromisoformat(rec.creation_timestamp.replace("Z", "+00:00"))
    pre_creation_time = (created_dt - timedelta(days=1)).isoformat()

    res = resolver.resolve_historical_key(
        owner="rec_attacker_04",
        key_type=KeyType.RECIPIENT_PRIVATE_KEY,
        event_timestamp=pre_creation_time,
        key_id=rec.key_id
    )
    assert not res.is_valid
    assert res.status == HistoricalResolutionStatus.KEY_NOT_YET_CREATED


def test_attack_05_cross_tenant_key_leakage():
    mgr = KeyLifecycleManager()
    resolver = HistoricalKeyResolver(mgr)

    rec_a = mgr.register_key(
        owner="tenant_a_user",
        key_type=KeyType.RECIPIENT_PUBLIC_KEY,
        algorithm="ML-DSA-65",
        purpose="Tenant A Key",
        tenant_id="TENANT_ALPHA",
        activate_immediately=True
    )

    # Tenant B queries key registered in Tenant A
    key_in_b = mgr.get_key(rec_a.key_id, tenant_id="TENANT_BETA")
    assert key_in_b is None

    # Resolver query across tenant fails closed
    t_now = datetime.now(timezone.utc).isoformat()
    res = resolver.resolve_historical_key(
        owner="tenant_a_user",
        key_type=KeyType.RECIPIENT_PUBLIC_KEY,
        event_timestamp=t_now,
        key_id=rec_a.key_id,
        tenant_id="TENANT_BETA"
    )
    assert not res.is_valid
    assert res.status == HistoricalResolutionStatus.KEY_UNAVAILABLE


def test_attack_06_forged_metadata_digest_tampering():
    mgr = KeyLifecycleManager()
    k = mgr.register_key(
        owner="rec_victim",
        key_type=KeyType.RECIPIENT_PRIVATE_KEY,
        algorithm="ML-DSA-65",
        purpose="Signing",
        custody_class=KeyCustodyClass.SECURE_KEYSTORE,
        recovery_class=KeyRecoveryClassification.RECOVERABLE,
        activate_immediately=True
    )
    pkg = KeyBackupEngine.create_backup_package(k, b"PRIVATE_KEY_BYTES", "Pass123!")

    # Attacker alters metadata owner without recalculating digest
    pkg["metadata"]["owner"] = "rec_attacker"
    with pytest.raises(KeyBackupIntegrityError, match="BACKUP_METADATA_TAMPERED"):
        KeyBackupEngine.restore_backup_package(pkg, "Pass123!")


def test_attack_07_epoch_mismatch():
    mgr = KeyLifecycleManager()
    resolver = HistoricalKeyResolver(mgr)

    rec = mgr.register_key(
        owner="SYSTEM_TRACEABILITY",
        key_type=KeyType.TRACEABILITY_SECRET,
        algorithm="TARDOS-SYMMETRIC",
        purpose="Collusion Traceability",
        epoch=5,
        activate_immediately=True
    )

    t_now = datetime.now(timezone.utc).isoformat()
    # Query specifying mismatched epoch 8
    res = resolver.resolve_historical_key(
        owner="SYSTEM_TRACEABILITY",
        key_type=KeyType.TRACEABILITY_SECRET,
        event_timestamp=t_now,
        event_epoch=8
    )
    assert not res.is_valid
    assert res.status == HistoricalResolutionStatus.EPOCH_MISMATCH


def test_attack_08_state_rollback_attack():
    mgr = KeyLifecycleManager()
    rec = mgr.register_key(
        owner="rec_rollback",
        key_type=KeyType.RECIPIENT_PRIVATE_KEY,
        algorithm="ML-DSA-65",
        purpose="Test",
        activate_immediately=True
    )
    mgr.revoke_key(rec.key_id, reason="Revoked")

    # Attacker calls state machine transition to force REVOKED -> ACTIVE
    assert not KeyStateMachine.can_transition(KeyState.REVOKED, KeyState.ACTIVE)
    assert not KeyStateMachine.can_transition(KeyState.RETIRED, KeyState.ACTIVE)

    rev_rec = mgr.get_key(rec.key_id)
    with pytest.raises(KeyLifecycleTransitionError):
        KeyStateMachine.transition(rev_rec, KeyState.ACTIVE)


def test_attack_09_duplicate_active_key_injection():
    mgr = KeyLifecycleManager()
    # Register first active key
    k1 = mgr.register_key(
        owner="rec_dup",
        key_type=KeyType.RECIPIENT_PRIVATE_KEY,
        algorithm="ML-DSA-65",
        purpose="Key 1",
        activate_immediately=True
    )
    assert k1.status == KeyState.ACTIVE

    # Registering second key with activate_immediately=True must atomically retire the first or raise
    k2 = mgr.register_key(
        owner="rec_dup",
        key_type=KeyType.RECIPIENT_PRIVATE_KEY,
        algorithm="ML-DSA-65",
        purpose="Key 2",
        activate_immediately=True
    )

    # Invariant: exactly ONE active key for (owner, type, algorithm)
    active_keys = [
        k for k in mgr.get_keys_for_owner("rec_dup", KeyType.RECIPIENT_PRIVATE_KEY, algorithm="ML-DSA-65")
        if k.status == KeyState.ACTIVE
    ]
    assert len(active_keys) == 1
    assert active_keys[0].key_id == k2.key_id
    assert mgr.get_key(k1.key_id).status == KeyState.RETIRED


def test_attack_10_stale_rotation_request():
    mgr = KeyLifecycleManager()
    k1 = mgr.register_key(
        owner="rec_stale",
        key_type=KeyType.RECIPIENT_PRIVATE_KEY,
        algorithm="ML-DSA-65",
        purpose="Key 1",
        activate_immediately=True
    )
    # First rotation
    mgr.rotate_key("rec_stale", KeyType.RECIPIENT_PRIVATE_KEY, algorithm="ML-DSA-65", new_algorithm="ML-DSA-65")

    # If an attacker specifies predecessor_key_id as already-retired k1 while k2 is active,
    # the manager enforces single active predecessor
    active = mgr.get_active_key("rec_stale", KeyType.RECIPIENT_PRIVATE_KEY, algorithm="ML-DSA-65")
    assert active.predecessor_key_id == k1.key_id


def test_attack_11_corrupted_backup_envelope():
    mgr = KeyLifecycleManager()
    k = mgr.register_key(
        owner="rec_corrupt",
        key_type=KeyType.RECIPIENT_PRIVATE_KEY,
        algorithm="ML-DSA-65",
        purpose="Test",
        custody_class=KeyCustodyClass.SECURE_KEYSTORE,
        recovery_class=KeyRecoveryClassification.RECOVERABLE,
        activate_immediately=True
    )
    pkg = KeyBackupEngine.create_backup_package(k, b"PRIV", "pass")
    pkg["tag_b64"] = base64.b64encode(b"0" * 16).decode("utf-8")  # Invalid tag

    with pytest.raises(KeyBackupIntegrityError):
        KeyBackupEngine.restore_backup_package(pkg, "pass")


def test_attack_12_unauthorized_activation_bypass():
    mgr = KeyLifecycleManager()
    # Register in GENERATED (not activated)
    k = mgr.register_key(
        owner="rec_unauth",
        key_type=KeyType.RECIPIENT_PRIVATE_KEY,
        algorithm="ML-DSA-65",
        purpose="Test",
        activate_immediately=False
    )
    assert k.status == KeyState.GENERATED

    # Unactivated key cannot be returned as active
    assert mgr.get_active_key("rec_unauth", KeyType.RECIPIENT_PRIVATE_KEY, algorithm="ML-DSA-65") is None


def test_attack_13_custody_class_downgrade_rejection():
    # In production environment (AEGISTRACE_ENV != development), DEVELOPMENT_ONLY custody fails closed
    old_env = os.environ.get("AEGISTRACE_ENV")
    try:
        os.environ["AEGISTRACE_ENV"] = "production"
        mgr = KeyLifecycleManager()
        with pytest.raises(PermissionError, match="DEVELOPMENT_ONLY key custody is strictly prohibited in production"):
            mgr.register_key(
                owner="rec_prod_victim",
                key_type=KeyType.RECIPIENT_PRIVATE_KEY,
                algorithm="ML-DSA-65",
                purpose="Insecure test in prod",
                custody_class=KeyCustodyClass.DEVELOPMENT_ONLY,
                activate_immediately=True
            )
    finally:
        if old_env is not None:
            os.environ["AEGISTRACE_ENV"] = old_env
        else:
            os.environ.pop("AEGISTRACE_ENV", None)


def test_attack_14_identity_hijacking_during_rotation():
    mgr = KeyLifecycleManager()
    mgr.register_key(
        owner="rec_victim_alice",
        key_type=KeyType.RECIPIENT_PRIVATE_KEY,
        algorithm="ML-DSA-65",
        purpose="Alice Key",
        tenant_id="TENANT_ALPHA",
        activate_immediately=True
    )

    # Eve from TENANT_BETA attempts to rotate Alice's key
    with pytest.raises(ValueError, match="No active key found to rotate"):
        mgr.rotate_key(
            owner="rec_victim_alice",
            key_type=KeyType.RECIPIENT_PRIVATE_KEY,
            algorithm="ML-DSA-65",
            tenant_id="TENANT_BETA"
        )


def test_attack_15_key_suspension_enforcement():
    mgr = KeyLifecycleManager()
    k = mgr.register_key(
        owner="rec_suspend",
        key_type=KeyType.RECIPIENT_PRIVATE_KEY,
        algorithm="ML-DSA-65",
        purpose="Test",
        activate_immediately=True
    )
    mgr.suspend_key(k.key_id, reason="Pending investigation")

    # Suspended key is not active
    assert mgr.get_active_key("rec_suspend", KeyType.RECIPIENT_PRIVATE_KEY, algorithm="ML-DSA-65") is None

    # Unsuspending restores active status
    mgr.unsuspend_key(k.key_id, reason="Investigation cleared")
    active = mgr.get_active_key("rec_suspend", KeyType.RECIPIENT_PRIVATE_KEY, algorithm="ML-DSA-65")
    assert active is not None
    assert active.key_id == k.key_id


def test_attack_16_unregistered_key_id_resolution():
    mgr = KeyLifecycleManager()
    resolver = HistoricalKeyResolver(mgr)

    t_now = datetime.now(timezone.utc).isoformat()
    res = resolver.resolve_historical_key(
        owner="nonexistent",
        key_type=KeyType.RECIPIENT_PRIVATE_KEY,
        event_timestamp=t_now,
        key_id="kid_00000000000000000000000000000000"
    )
    assert not res.is_valid
    assert res.status == HistoricalResolutionStatus.KEY_UNAVAILABLE
