"""
AegisTrace Device Enrollment & Lifecycle Service.

Manages cryptographic enrollment, multi-tenant isolation, hardware attestation
binding, device key registration, and revocation state tracking.
"""

import os
import hashlib
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple

from core.device.models import (
    DevicePrincipal,
    DeviceStatus,
    AttestationState,
    PlatformType,
    HardwareClass,
    AttestationEvidence,
    DeviceAttestationResult,
    AttestationProviderType,
)
from core.device.attestation import AttestationVerifier
from core.device.challenge import ChallengeManager
from core.device.providers.tpm import TPMAttestationProvider
from core.device.providers.apple import AppleSecureEnclaveProvider
from core.device.providers.android import AndroidStrongBoxProvider
from core.device.providers.webauthn import WebAuthnDeviceProvider
from core.device.providers.software import LocalSoftwareDeviceProvider


class DeviceEnrollmentService:
    """
    Production device registration and lifecycle authority.
    Enforces multi-tenant isolation and strict attestation boundary validation.
    """

    def __init__(
        self,
        verifier: Optional[AttestationVerifier] = None,
        challenge_manager: Optional[ChallengeManager] = None,
    ):
        self.challenge_manager = challenge_manager or ChallengeManager()
        self.verifier = verifier or self._create_default_verifier()

        # In-memory storage: (organization_id, device_id) -> DevicePrincipal
        self._devices: Dict[Tuple[str, str], DevicePrincipal] = {}
        # Historical revocation audit log: list of dicts
        self._revocation_log: List[Dict[str, Any]] = []

    @staticmethod
    def _create_default_verifier() -> AttestationVerifier:
        v = AttestationVerifier()
        v.register_provider(TPMAttestationProvider())
        v.register_provider(AppleSecureEnclaveProvider())
        v.register_provider(AndroidStrongBoxProvider())
        v.register_provider(WebAuthnDeviceProvider())
        v.register_provider(LocalSoftwareDeviceProvider())
        return v

    def register_device(
        self,
        device_id: str,
        organization_id: str,
        public_key_pem: str,
        public_key_algorithm: str = "P-256",
        platform: PlatformType = PlatformType.SOFTWARE_LOCAL,
        platform_version: str = "1.0",
        registered_to_recipient_id: Optional[str] = None,
        attestation_evidence: Optional[AttestationEvidence] = None,
        expected_challenge_nonce: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> DevicePrincipal:
        """
        Register a new device principal with cryptographic key binding and attestation check.
        """
        lookup_key = (organization_id, device_id)
        if lookup_key in self._devices:
            existing = self._devices[lookup_key]
            if existing.status == DeviceStatus.REVOKED:
                raise PermissionError(f"Device '{device_id}' is permanently REVOKED and cannot be re-registered.")
            raise ValueError(f"Device '{device_id}' already enrolled in organization '{organization_id}'.")

        # Derive device_key_id from public key fingerprint
        device_key_id = f"dkey_{hashlib.sha256(public_key_pem.encode('utf-8')).hexdigest()[:16]}"
        now_iso = datetime.now(timezone.utc).isoformat()

        # Initial default state is UNATTESTED
        att_state = AttestationState.DEVICE_UNATTESTED
        hw_class = HardwareClass.SOFTWARE_FALLBACK
        att_provider_name = None
        att_timestamp = None

        # If attestation evidence is provided, verify it
        if attestation_evidence:
            if not expected_challenge_nonce:
                raise ValueError("Expected challenge nonce required to verify attestation evidence.")

            # Validate nonce through challenge manager
            nonce_valid, reason = self.challenge_manager.validate_nonce(
                nonce_hex=expected_challenge_nonce,
                device_id=device_id,
                organization_id=organization_id,
                consume=True,
            )
            if not nonce_valid:
                raise ValueError(f"Attestation enrollment rejected: {reason}")

            # Create transient principal to run verification against
            transient_principal = DevicePrincipal(
                device_id=device_id,
                organization_id=organization_id,
                device_key_id=device_key_id,
                public_key_pem=public_key_pem,
                public_key_algorithm=public_key_algorithm,
                platform=platform,
                platform_version=platform_version,
                hardware_class=hw_class,
                attestation_state=att_state,
                registered_to_recipient_id=registered_to_recipient_id,
            )

            res = self.verifier.verify(
                evidence=attestation_evidence,
                device=transient_principal,
                expected_nonce_hex=expected_challenge_nonce,
            )

            if not res.is_valid:
                raise ValueError(f"Attestation evidence verification failed: {res.failure_reason}")

            att_state = res.attestation_state
            hw_class = res.hardware_class
            att_provider_name = attestation_evidence.provider_type.value
            att_timestamp = res.verified_at

        principal = DevicePrincipal(
            device_id=device_id,
            organization_id=organization_id,
            device_key_id=device_key_id,
            public_key_pem=public_key_pem,
            public_key_algorithm=public_key_algorithm,
            platform=platform,
            platform_version=platform_version,
            hardware_class=hw_class,
            attestation_state=att_state,
            attestation_provider=att_provider_name,
            attestation_timestamp=att_timestamp,
            first_seen=now_iso,
            last_seen=now_iso,
            key_epoch=1,
            status=DeviceStatus.ACTIVE,
            registered_to_recipient_id=registered_to_recipient_id,
            metadata=metadata or {},
        )

        self._devices[lookup_key] = principal
        return principal

    def get_device(self, device_id: str, organization_id: str) -> Optional[DevicePrincipal]:
        """Fetch device principal enforcing multi-tenant isolation."""
        return self._devices.get((organization_id, device_id))

    def list_devices(
        self,
        organization_id: str,
        recipient_id: Optional[str] = None,
    ) -> List[DevicePrincipal]:
        """List devices in an organization, optionally filtered by recipient."""
        res = []
        for (org, dev), principal in self._devices.items():
            if org == organization_id:
                if recipient_id is None or principal.registered_to_recipient_id == recipient_id:
                    res.append(principal)
        return res

    def list_devices_for_organization(
        self,
        organization_id: str,
    ) -> List[DevicePrincipal]:
        """List all devices registered to an organization."""
        return self.list_devices(organization_id)

    def revoke_device(
        self,
        device_id: str,
        organization_id: str,
        reason: str,
        actor_id: str = "system",
    ) -> DevicePrincipal:
        """
        Permanently revoke a device.
        INVARIANT: Historical events remain verifiable, but all future operations are rejected.
        """
        lookup_key = (organization_id, device_id)
        if lookup_key not in self._devices:
            raise KeyError(f"Device '{device_id}' not found in organization '{organization_id}'.")

        principal = self._devices[lookup_key]
        now_iso = datetime.now(timezone.utc).isoformat()

        principal.status = DeviceStatus.REVOKED
        principal.attestation_state = AttestationState.DEVICE_REVOKED
        principal.revocation_reason = reason
        principal.revoked_at = now_iso

        self._revocation_log.append({
            "device_id": device_id,
            "organization_id": organization_id,
            "revoked_at": now_iso,
            "reason": reason,
            "revoked_by": actor_id,
            "key_epoch_at_revocation": principal.key_epoch,
        })

        return principal

    def get_revocation_log(self) -> List[Dict[str, Any]]:
        """Return audit log of device revocations."""
        return list(self._revocation_log)

    def rotate_device_key(
        self,
        device_id: str,
        organization_id: str,
        new_public_key_pem: str,
        actor_id: str = "system",
    ) -> DevicePrincipal:
        """
        Rotates a device's public key, advancing its key_epoch and updating device_key_id.
        """
        lookup_key = (organization_id, device_id)
        if lookup_key not in self._devices:
            raise KeyError(f"Device '{device_id}' not found in organization '{organization_id}'.")

        principal = self._devices[lookup_key]
        if principal.status == DeviceStatus.REVOKED:
            raise PermissionError(f"Cannot rotate key for permanently REVOKED device '{device_id}'.")

        now_iso = datetime.now(timezone.utc).isoformat()
        new_device_key_id = f"dkey_{hashlib.sha256(new_public_key_pem.encode('utf-8')).hexdigest()[:16]}"

        principal.public_key_pem = new_public_key_pem
        principal.device_key_id = new_device_key_id
        principal.key_epoch += 1
        principal.last_seen = now_iso

        return principal

    def suspend_device(
        self,
        device_id: str,
        organization_id: str,
        reason: str,
    ) -> DevicePrincipal:
        """Temporarily suspend a device."""
        lookup_key = (organization_id, device_id)
        if lookup_key not in self._devices:
            raise KeyError(f"Device '{device_id}' not found in organization '{organization_id}'.")

        principal = self._devices[lookup_key]
        if principal.status == DeviceStatus.REVOKED:
            raise PermissionError(f"Cannot suspend permanently REVOKED device '{device_id}'.")

        principal.status = DeviceStatus.SUSPENDED
        return principal

    def reactivate_device(
        self,
        device_id: str,
        organization_id: str,
    ) -> DevicePrincipal:
        """Reactivate a suspended device. Cannot reactivate a revoked device."""
        lookup_key = (organization_id, device_id)
        if lookup_key not in self._devices:
            raise KeyError(f"Device '{device_id}' not found in organization '{organization_id}'.")

        principal = self._devices[lookup_key]
        if principal.status == DeviceStatus.REVOKED:
            raise PermissionError(f"Cannot reactivate permanently REVOKED device '{device_id}'.")

        principal.status = DeviceStatus.ACTIVE
        return principal
