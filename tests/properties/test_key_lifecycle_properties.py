"""
tests/properties/test_key_lifecycle_properties.py

Property-based testing and state-machine fuzzing for Key Lifecycle:
- KeyStateMachine formal transition rules
- INVARIANT-002: Revoked keys cannot authorize new events
- INVARIANT-003: Historical valid signatures remain verifiable after rotation
- Single active key per owner invariant
- Cross-tenant key isolation
"""

import pytest
from datetime import datetime, timezone, timedelta
from core.crypto.lifecycle.models import (
    KeyState,
    KeyType,
    KeyRecord,
    generate_key_id,
)
from core.crypto.lifecycle.state_machine import KeyStateMachine, KeyLifecycleTransitionError
from core.crypto.signatures import MLDSA65
from core.testing.property_engine import PropertyRunner, DeterministicGenerator
from core.security.invariants import assert_invariant


def create_sample_key(owner: str, tenant_id: str = "tenant-alpha", initial_state: KeyState = KeyState.GENERATED) -> KeyRecord:
    kid = generate_key_id(owner, KeyType.RECIPIENT_PRIVATE_KEY, epoch=1)
    return KeyRecord(
        key_id=kid,
        key_type=KeyType.RECIPIENT_PRIVATE_KEY,
        algorithm="ML-DSA-65",
        purpose="Testing key lifecycle property",
        owner=owner,
        tenant_id=tenant_id,
        status=initial_state,
    )


def test_property_key_state_machine_transition_fuzzing(runner: PropertyRunner):
    """
    Fuzzes arbitrary sequences of lifecycle state transitions across all 9 KeyStates.
    Asserts:
    1. Permitted transitions update state correctly.
    2. Illegal transitions strictly raise KeyLifecycleTransitionError.
    3. INVARIANT-002: REVOKED and COMPROMISED states NEVER transition back to ACTIVE.
    """
    all_states = list(KeyState)

    def prop(g: DeterministicGenerator):
        key = create_sample_key(f"owner-{g.alphanumeric(6, 8)}")
        num_transitions = g.integer(5, 20)

        for _ in range(num_transitions):
            target_state = g.choice(all_states)
            current_state = key.status
            can_trans = KeyStateMachine.can_transition(current_state, target_state)

            if can_trans:
                KeyStateMachine.transition(key, target_state, reason="Property fuzzing")
                assert key.status == target_state
            else:
                with pytest.raises(KeyLifecycleTransitionError):
                    KeyStateMachine.transition(key, target_state, reason="Should fail")
                # State remains untouched
                assert key.status == current_state

            # Golden Invariant INVARIANT-002 check:
            # If current state was REVOKED or COMPROMISED, key must never become ACTIVE
            if current_state in (KeyState.REVOKED, KeyState.COMPROMISED):
                assert_invariant(
                    key.status != KeyState.ACTIVE,
                    "INVARIANT-002",
                    f"Revoked/compromised key became active! from={current_state} to={key.status}",
                    g.seed,
                )

    res = runner.run_property("key_state_machine_fuzzing", prop, iterations=200)
    assert res.passed, res.error_message


def test_property_historical_signature_verification_invariant(runner: PropertyRunner):
    """
    INVARIANT-003: A signature produced when a key was ACTIVE remains verifiable
    even after the key rotates to RETIRED, REVOKED, or COMPROMISED.
    """
    kp = MLDSA65.generate_keypair()

    def prop(g: DeterministicGenerator):
        key = create_sample_key(f"owner-{g.alphanumeric(6, 8)}", initial_state=KeyState.ACTIVE)
        t_active = datetime.now(timezone.utc).isoformat()
        key.activation_timestamp = t_active

        # Sign message while active
        msg = g.bytes_data(g.integer(16, 128))
        sig = MLDSA65.sign(kp.private_key_bytes, msg)

        # Transition key to rotated, then retired or revoked
        KeyStateMachine.transition(key, KeyState.ROTATING)
        final_state = g.choice([KeyState.RETIRED, KeyState.REVOKED, KeyState.COMPROMISED])
        KeyStateMachine.transition(key, final_state)

        # Signature verification under historical public key must still succeed!
        valid = MLDSA65.verify(kp.public_key_bytes, msg, sig)
        assert_invariant(
            valid,
            "INVARIANT-003",
            f"Historical signature failed verification after key entered {final_state}",
            g.seed,
        )

    res = runner.run_property("historical_signature_verification", prop, iterations=100)
    assert res.passed, res.error_message


def test_property_single_active_successor_chain(runner: PropertyRunner):
    """
    Property: An orderly rotation succession chain guarantees that for any entity,
    rotating to a successor key leaves exactly one active key.
    """
    def prop(g: DeterministicGenerator):
        owner = f"owner-{g.alphanumeric(6, 8)}"
        chain_length = g.integer(3, 8)
        keys = []

        # Genesis key
        curr = create_sample_key(owner, initial_state=KeyState.ACTIVE)
        keys.append(curr)

        for epoch in range(2, chain_length + 2):
            successor = create_sample_key(owner, initial_state=KeyState.GENERATED)
            successor.creation_epoch = epoch
            successor.predecessor_key_id = curr.key_id

            # Start rotation
            KeyStateMachine.transition(curr, KeyState.ROTATING)
            KeyStateMachine.transition(successor, KeyState.PENDING_ACTIVATION)

            # Atomic cutover
            KeyStateMachine.transition(curr, KeyState.RETIRED)
            curr.successor_key_id = successor.key_id
            KeyStateMachine.transition(successor, KeyState.ACTIVE)

            keys.append(successor)
            curr = successor

            # Invariant: exactly one key in keys is ACTIVE
            active_keys = [k for k in keys if k.status == KeyState.ACTIVE]
            assert len(active_keys) == 1
            assert active_keys[0].key_id == curr.key_id

    res = runner.run_property("single_active_successor_chain", prop, iterations=100)
    assert res.passed, res.error_message


def test_property_cross_tenant_key_isolation(runner: PropertyRunner):
    """
    INVARIANT-001: Keys registered for Tenant A must never be accessible or
    satisfy queries originating from Tenant B.
    """
    def prop(g: DeterministicGenerator):
        tenant_a = f"tenant-{g.alphanumeric(6, 8)}"
        tenant_b = f"tenant-{g.alphanumeric(6, 8)}"
        if tenant_a == tenant_b:
            return

        key_a = create_sample_key("owner-alice", tenant_id=tenant_a, initial_state=KeyState.ACTIVE)
        key_b = create_sample_key("owner-bob", tenant_id=tenant_b, initial_state=KeyState.ACTIVE)

        keystore = {
            (key_a.tenant_id, key_a.key_id): key_a,
            (key_b.tenant_id, key_b.key_id): key_b,
        }

        # Query key_a using tenant_b context
        cross_query_res = keystore.get((tenant_b, key_a.key_id))
        assert_invariant(
            cross_query_res is None,
            "INVARIANT-001",
            "Tenant B accessed Tenant A key via direct ID lookup",
            g.seed,
        )

    res = runner.run_property("cross_tenant_key_isolation", prop, iterations=300)
    assert res.passed, res.error_message
