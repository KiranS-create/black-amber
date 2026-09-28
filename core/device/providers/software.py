"""
AegisTrace Local Software Device Provider.

Handles standard devices lacking hardware-rooted security modules (TPM, SE, StrongBox).
CRITICAL HONESTY INVARIANT:
Even when the cryptographic signature over the challenge nonce verifies perfectly,
the provider strictly returns:
  attestation_state = DEVICE_UNATTESTED
  hardware_class = SOFTWARE_FALLBACK
Under no circumstances does it promote software key storage to DEVICE_ATTESTED.
"""

import base64
from typing import Dict, Any, Optional
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
from core.device.attestation import DeviceAttestationProvider
from core.device.providers.base import verify_device_signature


class LocalSoftwareDeviceProvider(DeviceAttestationProvider):
    """
    Provider for local OS software key storage (e.g. software P-256 or ML-DSA-65).
    Provides cryptographic identity verification but strictly UNATTESTED assurance.
    """

    @property
    def provider_type(self) -> AttestationProviderType:
        return AttestationProviderType.LOCAL_SOFTWARE

    @property
    def supported_platform(self) -> PlatformType:
        return PlatformType.SOFTWARE_LOCAL

    @property
    def hardware_class(self) -> HardwareClass:
        return HardwareClass.SOFTWARE_FALLBACK

    @property
    def air_gap_capability(self) -> AirGappedAttestationCapability:
        return AirGappedAttestationCapability.UNATTESTED

    def verify_attestation(
        self,
        evidence: AttestationEvidence,
        device: DevicePrincipal,
        expected_nonce_hex: str,
    ) -> DeviceAttestationResult:
        now_iso = datetime.now(timezone.utc).isoformat()
        payload = evidence.evidence_payload

        sig_b64 = payload.get("signature_b64")
        pub_pem = payload.get("public_key_pem") or device.public_key_pem
        alg = device.public_key_algorithm

        if not sig_b64:
            return DeviceAttestationResult(
                is_valid=False,
                attestation_state=AttestationState.ATTESTATION_INVALID,
                device_id=device.device_id,
                hardware_class=self.hardware_class,
                platform_type=self.supported_platform,
                verified_at=now_iso,
                failure_reason="MISSING_SOFTWARE_CHALLENGE_SIGNATURE",
            )

        # 1. Nonce match
        if evidence.challenge_nonce != expected_nonce_hex:
            return DeviceAttestationResult(
                is_valid=False,
                attestation_state=AttestationState.ATTESTATION_INVALID,
                device_id=device.device_id,
                hardware_class=self.hardware_class,
                platform_type=self.supported_platform,
                verified_at=now_iso,
                nonce_matched=False,
                failure_reason="NONCE_MISMATCH: Challenge nonce does not match expected verifier nonce",
            )

        # 2. Signature verification
        try:
            sig_bytes = base64.b64decode(sig_b64)
            msg_bytes = expected_nonce_hex.encode("utf-8")
        except Exception:
            return DeviceAttestationResult(
                is_valid=False,
                attestation_state=AttestationState.ATTESTATION_INVALID,
                device_id=device.device_id,
                hardware_class=self.hardware_class,
                platform_type=self.supported_platform,
                verified_at=now_iso,
                failure_reason="MALFORMED_BASE64_SIGNATURE",
            )

        sig_valid = verify_device_signature(pub_pem, alg, msg_bytes, sig_bytes)
        if not sig_valid:
            return DeviceAttestationResult(
                is_valid=False,
                attestation_state=AttestationState.DEVICE_KEY_MISMATCH,
                device_id=device.device_id,
                hardware_class=self.hardware_class,
                platform_type=self.supported_platform,
                verified_at=now_iso,
                nonce_matched=True,
                signature_valid=False,
                failure_reason="DEVICE_KEY_MISMATCH: Signature does not match registered public key",
            )

        # 3. Cryptographically valid, but STRICTLY UNATTESTED
        return DeviceAttestationResult(
            is_valid=True,
            attestation_state=AttestationState.DEVICE_UNATTESTED,
            device_id=device.device_id,
            hardware_class=self.hardware_class,
            platform_type=self.supported_platform,
            verified_at=now_iso,
            nonce_matched=True,
            signature_valid=True,
            trust_anchor_verified=False,  # No hardware trust anchor
            air_gap_capability=self.air_gap_capability,
            details={
                "software_provider": "local_os_crypto",
                "assurance_note": "Cryptographic key verified; hardware root of trust absent (UNATTESTED).",
            },
        )
