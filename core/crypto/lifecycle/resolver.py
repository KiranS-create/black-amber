"""
AegisTrace Historical Key Resolver.

Enables chronological resolution of historical cryptographic keys without requiring
the current active key. Enforces T_revocation timestamp boundaries, epoch matching,
and compromise annotations.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

from core.crypto.lifecycle.models import KeyRecord, KeyState, KeyType
from core.crypto.lifecycle.manager import KeyLifecycleManager, default_key_lifecycle_manager


class HistoricalResolutionStatus(str, Enum):
    HISTORICALLY_VALID = "HISTORICALLY_VALID"
    COMPROMISED_KEY_HISTORICAL_VERIFIED = "COMPROMISED_KEY_HISTORICAL_VERIFIED"
    POST_REVOCATION_REJECTED = "POST_REVOCATION_REJECTED"
    POST_COMPROMISE_REJECTED = "POST_COMPROMISE_REJECTED"
    KEY_NOT_YET_CREATED = "KEY_NOT_YET_CREATED"
    KEY_UNAVAILABLE = "KEY_UNAVAILABLE"
    TENANT_MISMATCH = "TENANT_MISMATCH"
    EPOCH_MISMATCH = "EPOCH_MISMATCH"


class HistoricalResolutionResult(BaseModel):
    """Result of historical key resolution for a forensic event."""
    is_valid: bool
    status: HistoricalResolutionStatus
    key_record: Optional[KeyRecord] = None
    is_compromised: bool = False
    annotation: Optional[str] = None
    resolved_epoch: Optional[int] = None
    public_material_b64: Optional[str] = None


class HistoricalKeyResolver:
    """
    Resolves historical verification keys based on event timestamp and key epoch.
    Guarantees:
    1. Historical events remain verifiable after key rotation.
    2. Events created before T_revocation remain historically verifiable.
    3. Events created after T_revocation are rejected.
    4. Compromised keys flag historical events with COMPROMISED_KEY_HISTORICAL_VERIFIED.
    5. Cross-tenant queries fail closed.
    """
    def __init__(self, manager: Optional[KeyLifecycleManager] = None):
        self.manager = manager or default_key_lifecycle_manager

    def resolve_historical_key(
        self,
        owner: str,
        key_type: KeyType,
        event_timestamp: str,
        event_epoch: Optional[int] = None,
        key_id: Optional[str] = None,
        algorithm: Optional[str] = None,
        tenant_id: str = "default_tenant"
    ) -> HistoricalResolutionResult:
        """
        Resolves the appropriate historical key for an event.
        Evaluates:
        - Timestamp chronological consistency
        - Epoch matching
        - T_revocation boundary
        - Compromise status
        """
        # Parse event timestamp
        try:
            event_dt = datetime.fromisoformat(event_timestamp.replace("Z", "+00:00"))
        except Exception:
            return HistoricalResolutionResult(
                is_valid=False,
                status=HistoricalResolutionStatus.KEY_UNAVAILABLE,
                annotation=f"Malformed event timestamp '{event_timestamp}'"
            )

        candidate: Optional[KeyRecord] = None

        # 1. Lookup by key_id if provided
        if key_id:
            record = self.manager.get_key(key_id, tenant_id=tenant_id)
            if not record:
                return HistoricalResolutionResult(
                    is_valid=False,
                    status=HistoricalResolutionStatus.KEY_UNAVAILABLE,
                    annotation=f"Key '{key_id}' not found in tenant '{tenant_id}'"
                )
            if record.owner != owner or record.key_type != key_type:
                return HistoricalResolutionResult(
                    is_valid=False,
                    status=HistoricalResolutionStatus.TENANT_MISMATCH,
                    annotation=f"Key '{key_id}' owner/type mismatch"
                )
            candidate = record
        else:
            # 2. Lookup by (owner, key_type, epoch)
            keys = self.manager.get_keys_for_owner(owner, key_type, algorithm=algorithm, tenant_id=tenant_id)
            if not keys:
                return HistoricalResolutionResult(
                    is_valid=False,
                    status=HistoricalResolutionStatus.KEY_UNAVAILABLE,
                    annotation=f"No keys registered for owner '{owner}' type '{key_type.value}' in tenant '{tenant_id}'"
                )

            if event_epoch is not None:
                matches = [k for k in keys if k.creation_epoch == event_epoch]
                if matches:
                    candidate = matches[0]
                else:
                    return HistoricalResolutionResult(
                        is_valid=False,
                        status=HistoricalResolutionStatus.EPOCH_MISMATCH,
                        annotation=f"No key found for epoch {event_epoch}"
                    )
            else:
                # If no epoch specified, find the key that was active at event_timestamp
                for k in keys:
                    created_dt = datetime.fromisoformat(k.creation_timestamp.replace("Z", "+00:00"))
                    if created_dt <= event_dt:
                        if k.revocation_timestamp:
                            rev_dt = datetime.fromisoformat(k.revocation_timestamp.replace("Z", "+00:00"))
                            if event_dt < rev_dt:
                                candidate = k
                                break
                        else:
                            candidate = k

                if not candidate:
                    candidate = keys[0]

        # Evaluate candidate against event_dt
        created_dt = datetime.fromisoformat(candidate.creation_timestamp.replace("Z", "+00:00"))
        if event_dt < created_dt:
            return HistoricalResolutionResult(
                is_valid=False,
                status=HistoricalResolutionStatus.KEY_NOT_YET_CREATED,
                key_record=candidate,
                annotation=f"Event timestamp {event_timestamp} precedes key creation {candidate.creation_timestamp}"
            )

        # Check T_revocation boundary
        if candidate.revocation_timestamp:
            rev_dt = datetime.fromisoformat(candidate.revocation_timestamp.replace("Z", "+00:00"))
            if event_dt >= rev_dt:
                # Event happened AFTER revocation!
                if candidate.status == KeyState.COMPROMISED:
                    return HistoricalResolutionResult(
                        is_valid=False,
                        status=HistoricalResolutionStatus.POST_COMPROMISE_REJECTED,
                        key_record=candidate,
                        is_compromised=True,
                        annotation=f"Event timestamp {event_timestamp} occurs after key compromise at {candidate.revocation_timestamp}"
                    )
                return HistoricalResolutionResult(
                    is_valid=False,
                    status=HistoricalResolutionStatus.POST_REVOCATION_REJECTED,
                    key_record=candidate,
                    annotation=f"Event timestamp {event_timestamp} occurs after key revocation at {candidate.revocation_timestamp}"
                )

        # If event happened BEFORE revocation or key is active
        if candidate.status == KeyState.COMPROMISED:
            # Compromised key, but event occurred before T_compromise
            return HistoricalResolutionResult(
                is_valid=True,
                status=HistoricalResolutionStatus.COMPROMISED_KEY_HISTORICAL_VERIFIED,
                key_record=candidate,
                is_compromised=True,
                resolved_epoch=candidate.creation_epoch,
                public_material_b64=candidate.public_material_b64,
                annotation=f"Historically valid before compromise (T_compromise: {candidate.revocation_timestamp})"
            )

        return HistoricalResolutionResult(
            is_valid=True,
            status=HistoricalResolutionStatus.HISTORICALLY_VALID,
            key_record=candidate,
            is_compromised=False,
            resolved_epoch=candidate.creation_epoch,
            public_material_b64=candidate.public_material_b64,
            annotation="Historically valid key reference"
        )


default_historical_resolver = HistoricalKeyResolver()
