"""
AegisTrace Cryptographic Key Lifecycle, Rotation & Recovery Subsystem.

Public interface for key lifecycle states, management, historical resolution,
authenticated backup/recovery, and subsystem adapters.
"""

from core.crypto.lifecycle.models import (
    KeyState,
    KeyType,
    KeyCustodyClass,
    KeyRecoveryClassification,
    KeyRecord,
    generate_key_id,
)
from core.crypto.lifecycle.state_machine import (
    KeyStateMachine,
    KeyLifecycleTransitionError,
)
from core.crypto.lifecycle.audit import (
    KeyAuditEvent,
    KeyLifecycleAuditLogger,
    default_key_audit_logger,
)
from core.crypto.lifecycle.manager import (
    KeyLifecycleManager,
    KeyCustodyError,
    default_key_lifecycle_manager,
)
from core.crypto.lifecycle.resolver import (
    HistoricalResolutionStatus,
    HistoricalResolutionResult,
    HistoricalKeyResolver,
    default_historical_resolver,
)
from core.crypto.lifecycle.backup import (
    KeyBackupEngine,
    KeyBackupSecurityError,
    KeyBackupIntegrityError,
)
from core.crypto.lifecycle.adapters import (
    RecipientKeyLifecycleAdapter,
    DeviceKeyLifecycleAdapter,
    TraceabilityEpochAdapter,
    WatermarkEpochAdapter,
    ValidatorKeyLifecycleAdapter,
    SessionRotationPolicy,
    SessionLifecycleCoordinator,
)

__all__ = [
    "KeyState",
    "KeyType",
    "KeyCustodyClass",
    "KeyRecoveryClassification",
    "KeyRecord",
    "generate_key_id",
    "KeyStateMachine",
    "KeyLifecycleTransitionError",
    "KeyAuditEvent",
    "KeyLifecycleAuditLogger",
    "default_key_audit_logger",
    "KeyLifecycleManager",
    "KeyCustodyError",
    "default_key_lifecycle_manager",
    "HistoricalResolutionStatus",
    "HistoricalResolutionResult",
    "HistoricalKeyResolver",
    "default_historical_resolver",
    "KeyBackupEngine",
    "KeyBackupSecurityError",
    "KeyBackupIntegrityError",
    "RecipientKeyLifecycleAdapter",
    "DeviceKeyLifecycleAdapter",
    "TraceabilityEpochAdapter",
    "WatermarkEpochAdapter",
    "ValidatorKeyLifecycleAdapter",
    "SessionRotationPolicy",
    "SessionLifecycleCoordinator",
]
