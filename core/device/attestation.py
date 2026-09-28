"""
AegisTrace Device Attestation Provider Abstraction & Registry.

Defines the pluggable DeviceAttestationProvider interface and central verifier.
NO FAKE ATTESTATION INVARIANT:
Never returns DEVICE_ATTESTED without genuine, validated cryptographic evidence
rooted in hardware (TPM 2.0 quote, Apple Secure Enclave, Android StrongBox, or FIDO2).
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timezone

from core.device.models import (
    DevicePrincipal,
    AttestationEvidence,
    DeviceAttestationResult,
    AttestationState,
    PlatformType,
    HardwareClass,
    AttestationProviderType,
    AirGappedAttestationCapability,
)


class DeviceAttestationProvider(ABC):
    """
    Abstract interface for platform-specific hardware attestation verifiers.
    """

    @property
    @abstractmethod
    def provider_type(self) -> AttestationProviderType:
        """Provider identifier."""
        pass

    @property
    @abstractmethod
    def supported_platform(self) -> PlatformType:
        """Supported platform security module."""
        pass

    @property
    @abstractmethod
    def hardware_class(self) -> HardwareClass:
        """Hardware assurance tier provided by this platform."""
        pass

    @property
    @abstractmethod
    def air_gap_capability(self) -> AirGappedAttestationCapability:
        """Air-gap verification capability."""
        pass

    @abstractmethod
    def verify_attestation(
        self,
        evidence: AttestationEvidence,
        device: DevicePrincipal,
        expected_nonce_hex: str,
    ) -> DeviceAttestationResult:
        """
        Verify the presented attestation evidence against the device principal and challenge nonce.
        """
        pass


class AttestationVerifier:
    """
    Central dispatcher and verifier routing attestation evidence
    to the appropriate platform provider.
    """

    def __init__(self):
        self._providers: Dict[AttestationProviderType, DeviceAttestationProvider] = {}

    def register_provider(self, provider: DeviceAttestationProvider) -> None:
        self._providers[provider.provider_type] = provider

    def get_provider(self, provider_type: AttestationProviderType) -> Optional[DeviceAttestationProvider]:
        return self._providers.get(provider_type)

    def verify(
        self,
        evidence: AttestationEvidence,
        device: DevicePrincipal,
        expected_nonce_hex: str,
    ) -> DeviceAttestationResult:
        """
        Dispatch attestation verification to the registered platform provider.
        """
        provider = self._providers.get(evidence.provider_type)
        if not provider:
            return DeviceAttestationResult(
                is_valid=False,
                attestation_state=AttestationState.PLATFORM_UNSUPPORTED,
                device_id=device.device_id,
                hardware_class=HardwareClass.SOFTWARE_FALLBACK,
                platform_type=device.platform,
                verified_at=datetime.now(timezone.utc).isoformat(),
                failure_reason=f"No provider registered for attestation type '{evidence.provider_type.value}'",
            )

        return provider.verify_attestation(evidence, device, expected_nonce_hex)
