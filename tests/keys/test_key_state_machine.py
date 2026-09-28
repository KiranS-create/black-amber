"""
Tests for AegisTrace Key Lifecycle State Machine.

Verifies:
- Formal 9-state lifecycle transitions.
- Disallowed transitions fail closed.
- Idempotent transitions.
- Timestamp updates on state entry.
"""

import pytest
from core.crypto.lifecycle.models import (
    KeyRecord,
    KeyState,
    KeyType,
    KeyCustodyClass,
    KeyRecoveryClassification,
    generate_key_id,
)
from core.crypto.lifecycle.state_machine import KeyStateMachine, KeyLifecycleTransitionError


def create_sample_key_record(initial_state: KeyState = KeyState.GENERATED) -> KeyRecord:
    kid = generate_key_id("test_owner", KeyType.RECIPIENT_PRIVATE_KEY, 1)
    return KeyRecord(
        key_id=kid,
        key_type=KeyType.RECIPIENT_PRIVATE_KEY,
        algorithm="ML-DSA-65",
        purpose="Test Signing Key",
        owner="test_owner",
        tenant_id="default_tenant",
        creation_epoch=1,
        status=initial_state,
        storage_class=KeyCustodyClass.LOCAL_PROTECTED_STORE,
        recovery_class=KeyRecoveryClassification.RECOVERABLE
    )


def test_state_machine_valid_full_lifecycle():
    """GENERATED -> PENDING_ACTIVATION -> ACTIVE -> ROTATING -> RETIRED."""
    rec = create_sample_key_record(KeyState.GENERATED)
    assert rec.status == KeyState.GENERATED

    KeyStateMachine.transition(rec, KeyState.PENDING_ACTIVATION, reason="Enrolled")
    assert rec.status == KeyState.PENDING_ACTIVATION

    KeyStateMachine.transition(rec, KeyState.ACTIVE, reason="Activated")
    assert rec.status == KeyState.ACTIVE
    assert rec.activation_timestamp is not None

    KeyStateMachine.transition(rec, KeyState.ROTATING, reason="Rotation begun")
    assert rec.status == KeyState.ROTATING
    assert rec.rotation_timestamp is not None

    KeyStateMachine.transition(rec, KeyState.RETIRED, reason="Rotated to successor")
    assert rec.status == KeyState.RETIRED


def test_state_machine_suspension_and_reactivation():
    """ACTIVE -> SUSPENDED -> ACTIVE."""
    rec = create_sample_key_record(KeyState.ACTIVE)
    KeyStateMachine.transition(rec, KeyState.SUSPENDED, reason="Under investigation")
    assert rec.status == KeyState.SUSPENDED

    KeyStateMachine.transition(rec, KeyState.ACTIVE, reason="Cleared investigation")
    assert rec.status == KeyState.ACTIVE


def test_state_machine_revocation_irreversibility():
    """Revoked keys can never transition back to ACTIVE."""
    rec = create_sample_key_record(KeyState.ACTIVE)
    KeyStateMachine.transition(rec, KeyState.REVOKED, reason="Certificate expired")
    assert rec.status == KeyState.REVOKED
    assert rec.revocation_timestamp is not None

    with pytest.raises(KeyLifecycleTransitionError, match="ILLEGAL_KEY_TRANSITION"):
        KeyStateMachine.transition(rec, KeyState.ACTIVE, reason="Attempted unauthorized reactivation")


def test_state_machine_compromise_irreversibility():
    """Compromised keys can never transition back to ACTIVE or REVOKED."""
    rec = create_sample_key_record(KeyState.ACTIVE)
    KeyStateMachine.transition(rec, KeyState.COMPROMISED, reason="Key leak detected")
    assert rec.status == KeyState.COMPROMISED
    assert rec.revocation_timestamp is not None
    assert "leak detected" in rec.compromise_details

    with pytest.raises(KeyLifecycleTransitionError, match="ILLEGAL_KEY_TRANSITION"):
        KeyStateMachine.transition(rec, KeyState.ACTIVE, reason="Attempted reactivation")

    with pytest.raises(KeyLifecycleTransitionError, match="ILLEGAL_KEY_TRANSITION"):
        KeyStateMachine.transition(rec, KeyState.REVOKED, reason="Attempted downgrade to regular revocation")


def test_state_machine_revoked_to_compromised_upgrade():
    """A previously revoked key can be upgraded to COMPROMISED if post-revocation compromise is discovered."""
    rec = create_sample_key_record(KeyState.ACTIVE)
    KeyStateMachine.transition(rec, KeyState.REVOKED, reason="Normal rotation")
    assert rec.status == KeyState.REVOKED

    KeyStateMachine.transition(rec, KeyState.COMPROMISED, reason="Discovered historical theft of revoked key")
    assert rec.status == KeyState.COMPROMISED
    assert "Discovered historical theft" in rec.compromise_details


def test_state_machine_idempotent_transition():
    """Transitioning to the same state is an idempotent no-op."""
    rec = create_sample_key_record(KeyState.ACTIVE)
    KeyStateMachine.transition(rec, KeyState.ACTIVE, reason="No-op")
    assert rec.status == KeyState.ACTIVE
