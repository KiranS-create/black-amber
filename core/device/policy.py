"""
AegisTrace Trust Policy Engine.

Enforces configurable, risk-based access policies governing operations
(decryption, viewing, export, forwarding) based on device attestation state,
hardware assurance class, and lifecycle status.
"""

from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from core.device.models import (
    DevicePrincipal,
    DeviceStatus,
    AttestationState,
    HardwareClass,
)


class OperationAssuranceLevel(str, Enum):
    """Assurance requirement level for an operation."""
    HIGH_ASSURANCE = "HIGH_ASSURANCE"     # Requires genuine hardware attestation (TPM/SE/StrongBox)
    STANDARD = "STANDARD"                 # Normal enterprise operations; permits UNATTESTED with audit
    RESTRICTED = "RESTRICTED"             # Strict monitoring; blocks untrusted or flagged devices


class OperationType(str, Enum):
    """Categorized forensic actions in AegisTrace."""
    DECRYPT_RELEASE = "DECRYPT_RELEASE"
    VIEWER_SESSION_OPEN = "VIEWER_SESSION_OPEN"
    EXPORT_DOCUMENT = "EXPORT_DOCUMENT"
    FORWARD_COPY = "FORWARD_COPY"
    PRINT_DOCUMENT = "PRINT_DOCUMENT"


class PolicyDecision(BaseModel):
    """Outcome of a policy evaluation."""
    is_allowed: bool
    operation: str
    required_assurance: OperationAssuranceLevel
    device_id: str
    device_attestation_state: AttestationState
    reason: str
    audit_flags: List[str] = Field(default_factory=list)


class TrustPolicyEngine:
    """
    Evaluates whether an operation is permissible under the active security policy.
    Configurable for different defense / enterprise profiles.
    """

    def __init__(self, default_policy_level: OperationAssuranceLevel = OperationAssuranceLevel.STANDARD):
        self.default_policy_level = default_policy_level

    def evaluate(
        self,
        device: DevicePrincipal,
        operation: OperationType,
        required_assurance: Optional[OperationAssuranceLevel] = None,
    ) -> PolicyDecision:
        assurance = required_assurance or self.default_policy_level
        audit_flags: List[str] = []

        # 1. Base Administrative Status Check (Hard Block)
        if device.status == DeviceStatus.REVOKED:
            return PolicyDecision(
                is_allowed=False,
                operation=operation.value,
                required_assurance=assurance,
                device_id=device.device_id,
                device_attestation_state=device.attestation_state,
                reason=f"OPERATION_DENIED: Device '{device.device_id}' is permanently REVOKED.",
                audit_flags=["DEVICE_REVOKED"],
            )

        if device.status == DeviceStatus.SUSPENDED:
            return PolicyDecision(
                is_allowed=False,
                operation=operation.value,
                required_assurance=assurance,
                device_id=device.device_id,
                device_attestation_state=device.attestation_state,
                reason=f"OPERATION_DENIED: Device '{device.device_id}' is temporarily SUSPENDED.",
                audit_flags=["DEVICE_SUSPENDED"],
            )

        # 2. Compromised or Invalid State Check
        if device.attestation_state in (AttestationState.ATTESTATION_INVALID, AttestationState.DEVICE_KEY_MISMATCH):
            return PolicyDecision(
                is_allowed=False,
                operation=operation.value,
                required_assurance=assurance,
                device_id=device.device_id,
                device_attestation_state=device.attestation_state,
                reason=f"OPERATION_DENIED: Device attestation is corrupted or invalid ({device.attestation_state.value}).",
                audit_flags=["ATTESTATION_CORRUPTED"],
            )

        # 3. High-Assurance Operation Requirements
        if assurance == OperationAssuranceLevel.HIGH_ASSURANCE:
            # High assurance strictly requires hardware attestation
            if device.attestation_state != AttestationState.DEVICE_ATTESTED:
                return PolicyDecision(
                    is_allowed=False,
                    operation=operation.value,
                    required_assurance=assurance,
                    device_id=device.device_id,
                    device_attestation_state=device.attestation_state,
                    reason="OPERATION_DENIED: High-assurance (HIGH_ASSURANCE) operations strictly require hardware-attested devices (DEVICE_ATTESTED).",
                    audit_flags=["UNATTESTED_DEVICE_BLOCKED_FOR_HIGH_ASSURANCE"],
                )

            # Check hardware class isolation
            if device.hardware_class == HardwareClass.SOFTWARE_FALLBACK:
                return PolicyDecision(
                    is_allowed=False,
                    operation=operation.value,
                    required_assurance=assurance,
                    device_id=device.device_id,
                    device_attestation_state=device.attestation_state,
                    reason="OPERATION_DENIED: Software-backed storage cannot satisfy high-assurance requirement.",
                    audit_flags=["INSUFFICIENT_HARDWARE_CLASS"],
                )

            audit_flags.append("HIGH_ASSURANCE_HARDWARE_VERIFIED")
            return PolicyDecision(
                is_allowed=True,
                operation=operation.value,
                required_assurance=assurance,
                device_id=device.device_id,
                device_attestation_state=device.attestation_state,
                reason="Permitted: Device is cryptographically attested with verified hardware root of trust.",
                audit_flags=audit_flags,
            )

        # 4. Standard Operation Requirements
        elif assurance == OperationAssuranceLevel.STANDARD:
            if device.attestation_state == AttestationState.DEVICE_UNATTESTED:
                audit_flags.append("DEVICE_UNATTESTED_STANDARD_OPERATION_LOGGED")
            elif device.attestation_state == AttestationState.DEVICE_ATTESTED:
                audit_flags.append("DEVICE_ATTESTED")

            return PolicyDecision(
                is_allowed=True,
                operation=operation.value,
                required_assurance=assurance,
                device_id=device.device_id,
                device_attestation_state=device.attestation_state,
                reason="Permitted: Standard enterprise operation allowed.",
                audit_flags=audit_flags,
            )

        # 5. Restricted Policy
        else:
            if device.attestation_state != AttestationState.DEVICE_ATTESTED:
                return PolicyDecision(
                    is_allowed=False,
                    operation=operation.value,
                    required_assurance=assurance,
                    device_id=device.device_id,
                    device_attestation_state=device.attestation_state,
                    reason="OPERATION_DENIED: Restricted environment requires proven hardware attestation.",
                    audit_flags=["RESTRICTED_POLICY_REJECTION"],
                )

            return PolicyDecision(
                is_allowed=True,
                operation=operation.value,
                required_assurance=assurance,
                device_id=device.device_id,
                device_attestation_state=device.attestation_state,
                reason="Permitted under restricted monitoring.",
                audit_flags=["RESTRICTED_MONITORED_ALLOWED"],
            )
