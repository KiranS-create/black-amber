"""
AegisTrace Device Identity & Hardware Attestation Subsystem.

Production-grade hardware-rooted device identity, platform attestation,
cryptographic challenge-response, multi-tenant isolation, trust policy enforcement,
and forensic evidence fusion.
"""

from core.device.models import (
    DeviceStatus,
    AttestationState,
    PlatformType,
    HardwareClass,
    AttestationProviderType,
    AirGappedAttestationCapability,
    DevicePrincipal,
    AttestationEvidence,
    DeviceAttestationResult,
)

from core.device.challenge import (
    AttestationChallenge,
    ChallengeManager,
)

from core.device.attestation import (
    DeviceAttestationProvider,
    AttestationVerifier,
)

from core.device.providers import (
    verify_device_signature,
    TPMAttestationProvider,
    AppleSecureEnclaveProvider,
    AndroidStrongBoxProvider,
    WebAuthnDeviceProvider,
    LocalSoftwareDeviceProvider,
)

from core.device.enrollment import (
    DeviceEnrollmentService,
)

from core.device.policy import (
    OperationAssuranceLevel,
    OperationType,
    PolicyDecision,
    TrustPolicyEngine,
)

from core.device.session import (
    BoundDeviceSession,
    DecryptionDeviceBindingReceipt,
    DeviceSessionManager,
)

from core.device.evidence import (
    DeviceEvidenceAdapter,
)

from core.device.benchmarks import (
    DeviceBenchmarkMetrics,
    run_device_benchmarks,
)

__all__ = [
    "DeviceStatus",
    "AttestationState",
    "PlatformType",
    "HardwareClass",
    "AttestationProviderType",
    "AirGappedAttestationCapability",
    "DevicePrincipal",
    "AttestationEvidence",
    "DeviceAttestationResult",
    "AttestationChallenge",
    "ChallengeManager",
    "DeviceAttestationProvider",
    "AttestationVerifier",
    "verify_device_signature",
    "TPMAttestationProvider",
    "AppleSecureEnclaveProvider",
    "AndroidStrongBoxProvider",
    "WebAuthnDeviceProvider",
    "LocalSoftwareDeviceProvider",
    "DeviceEnrollmentService",
    "OperationAssuranceLevel",
    "OperationType",
    "PolicyDecision",
    "TrustPolicyEngine",
    "BoundDeviceSession",
    "DecryptionDeviceBindingReceipt",
    "DeviceSessionManager",
    "DeviceEvidenceAdapter",
    "DeviceBenchmarkMetrics",
    "run_device_benchmarks",
]
