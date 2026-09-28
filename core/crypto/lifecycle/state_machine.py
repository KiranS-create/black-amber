"""
AegisTrace Key Lifecycle State Machine.

Enforces valid lifecycle transitions, guards against illegal state reversals,
and guarantees fail-closed security for revoked and compromised keys.
"""

from datetime import datetime, timezone
from typing import Dict, Set, Tuple, Optional
from core.crypto.lifecycle.models import KeyState, KeyRecord


class KeyLifecycleTransitionError(ValueError):
    """Raised when an invalid or forbidden lifecycle transition is attempted."""
    pass


class KeyStateMachine:
    """
    State machine enforcing the formal 9-state key lifecycle.
    """
    # Allowed transitions: current_state -> Set[target_state]
    ALLOWED_TRANSITIONS: Dict[KeyState, Set[KeyState]] = {
        KeyState.GENERATED: {
            KeyState.PENDING_ACTIVATION,
            KeyState.ACTIVE,
            KeyState.REVOKED,
            KeyState.COMPROMISED,
        },
        KeyState.PENDING_ACTIVATION: {
            KeyState.ACTIVE,
            KeyState.REVOKED,
            KeyState.COMPROMISED,
        },
        KeyState.ACTIVE: {
            KeyState.ROTATING,
            KeyState.SUSPENDED,
            KeyState.REVOKED,
            KeyState.COMPROMISED,
            KeyState.RETIRED,
        },
        KeyState.SUSPENDED: {
            KeyState.ACTIVE,
            KeyState.REVOKED,
            KeyState.COMPROMISED,
        },
        KeyState.ROTATING: {
            KeyState.ACTIVE,
            KeyState.REVOKED,
            KeyState.COMPROMISED,
            KeyState.RETIRED,
        },
        KeyState.REVOKED: {
            KeyState.COMPROMISED,
            KeyState.RETIRED,
        },
        KeyState.COMPROMISED: {
            KeyState.RETIRED,
        },
        KeyState.RETIRED: {
            KeyState.REVOKED,
            KeyState.COMPROMISED,
        },
        KeyState.UNKNOWN: set(),
    }

    @classmethod
    def can_transition(cls, from_state: KeyState, to_state: KeyState) -> bool:
        """Evaluates whether transition from_state -> to_state is permissible."""
        if from_state == to_state:
            return True  # Idempotent no-op
        return to_state in cls.ALLOWED_TRANSITIONS.get(from_state, set())

    @classmethod
    def transition(
        cls,
        record: KeyRecord,
        target_state: KeyState,
        reason: str = "",
        timestamp: Optional[str] = None
    ) -> KeyRecord:
        """
        Executes a formal state transition on a KeyRecord.
        Updates appropriate timestamps and validates invariants.
        Raises KeyLifecycleTransitionError if transition is forbidden.
        """
        current_state = record.status
        now_iso = timestamp or datetime.now(timezone.utc).isoformat()

        if current_state == target_state:
            return record  # Idempotent

        if not cls.can_transition(current_state, target_state):
            raise KeyLifecycleTransitionError(
                f"ILLEGAL_KEY_TRANSITION: Cannot transition key '{record.key_id}' "
                f"from {current_state.value} to {target_state.value}. (Reason: {reason})"
            )

        # Apply state updates and timestamp boundaries
        record.status = target_state

        if target_state == KeyState.ACTIVE and not record.activation_timestamp:
            record.activation_timestamp = now_iso
        elif target_state == KeyState.ROTATING:
            record.rotation_timestamp = now_iso
        elif target_state in (KeyState.REVOKED, KeyState.COMPROMISED):
            if not record.revocation_timestamp:
                record.revocation_timestamp = now_iso
            if target_state == KeyState.COMPROMISED:
                record.compromise_details = reason or "Key reported compromised."

        return record
