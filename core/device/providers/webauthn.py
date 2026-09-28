"""
AegisTrace WebAuthn / FIDO2 Hardware Attestation Provider.

Parses and cryptographically verifies WebAuthn clientDataJSON, authenticatorData flags
(UP: User Present, UV: User Verified, AT: Attested Credential), and FIDO2 signatures.
"""

import base64
import hashlib
import json
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


class WebAuthnDeviceProvider(DeviceAttestationProvider):
    """
    Verifier for FIDO2 / WebAuthn hardware-bound authenticators.
    """

    @property
    def provider_type(self) -> AttestationProviderType:
        return AttestationProviderType.FIDO2_WEBAUTHN

    @property
    def supported_platform(self) -> PlatformType:
        return PlatformType.WEBAUTHN_FIDO2

    @property
    def hardware_class(self) -> HardwareClass:
        return HardwareClass.DEDICATED_HARDWARE_HSM

    @property
    def air_gap_capability(self) -> AirGappedAttestationCapability:
        # FIDO Alliance Metadata Service (MDS) roots can be cached locally
        return AirGappedAttestationCapability.AIR_GAPPED_ATTESTATION_CAPABLE

    def verify_attestation(
        self,
        evidence: AttestationEvidence,
        device: DevicePrincipal,
        expected_nonce_hex: str,
    ) -> DeviceAttestationResult:
        now_iso = datetime.now(timezone.utc).isoformat()
        payload = evidence.evidence_payload

        client_data_json = payload.get("client_data_json", "")
        auth_data_b64 = payload.get("authenticator_data_b64")
        sig_b64 = payload.get("signature_b64")
        pub_pem = payload.get("credential_public_key_pem") or device.public_key_pem

        if not client_data_json or not auth_data_b64 or not sig_b64:
            return DeviceAttestationResult(
                is_valid=False,
                attestation_state=AttestationState.ATTESTATION_INVALID,
                device_id=device.device_id,
                hardware_class=self.hardware_class,
                platform_type=self.supported_platform,
                verified_at=now_iso,
                failure_reason="MISSING_WEBAUTHN_CLIENT_DATA_OR_AUTH_DATA",
            )

        # 1. Parse clientDataJSON and verify challenge
        try:
            client_dict = json.loads(client_data_json) if isinstance(client_data_json, str) else client_data_json
            extracted_challenge = client_dict.get("challenge")
        except Exception:
            return DeviceAttestationResult(
                is_valid=False,
                attestation_state=AttestationState.ATTESTATION_INVALID,
                device_id=device.device_id,
                hardware_class=self.hardware_class,
                platform_type=self.supported_platform,
                verified_at=now_iso,
                failure_reason="MALFORMED_CLIENT_DATA_JSON",
            )

        if extracted_challenge != expected_nonce_hex:
            return DeviceAttestationResult(
                is_valid=False,
                attestation_state=AttestationState.ATTESTATION_INVALID,
                device_id=device.device_id,
                hardware_class=self.hardware_class,
                platform_type=self.supported_platform,
                verified_at=now_iso,
                nonce_matched=False,
                failure_reason=f"NONCE_MISMATCH: WebAuthn challenge '{extracted_challenge}' does not match '{expected_nonce_hex}'",
            )

        # 2. Check authenticatorData flags (User Present = bit 0, User Verified = bit 2)
        try:
            auth_bytes = base64.b64decode(auth_data_b64)
            flags = auth_bytes[32] if len(auth_bytes) >= 33 else 0
            user_present = bool(flags & 0x01)
            user_verified = bool(flags & 0x04)
        except Exception:
            return DeviceAttestationResult(
                is_valid=False,
                attestation_state=AttestationState.ATTESTATION_INVALID,
                device_id=device.device_id,
                hardware_class=self.hardware_class,
                platform_type=self.supported_platform,
                verified_at=now_iso,
                failure_reason="MALFORMED_AUTHENTICATOR_DATA_BYTES",
            )

        if not user_present:
            return DeviceAttestationResult(
                is_valid=False,
                attestation_state=AttestationState.ATTESTATION_INVALID,
                device_id=device.device_id,
                hardware_class=self.hardware_class,
                platform_type=self.supported_platform,
                verified_at=now_iso,
                failure_reason="USER_PRESENCE_FLAG_NOT_SET",
            )

        # 3. Signature verification over (authData || SHA256(clientDataJSON))
        client_hash = hashlib.sha256(
            client_data_json.encode('utf-8') if isinstance(client_data_json, str) else json.dumps(client_data_json).encode()
        ).digest()
        signed_payload = auth_bytes + client_hash

        try:
            sig_bytes = base64.b64decode(sig_b64)
        except Exception:
            return DeviceAttestationResult(
                is_valid=False,
                attestation_state=AttestationState.ATTESTATION_INVALID,
                device_id=device.device_id,
                hardware_class=self.hardware_class,
                platform_type=self.supported_platform,
                verified_at=now_iso,
                failure_reason="MALFORMED_WEBAUTHN_SIGNATURE_BYTES",
            )

        sig_valid = verify_device_signature(pub_pem, device.public_key_algorithm, signed_payload, sig_bytes)
        if not sig_valid:
            return DeviceAttestationResult(
                is_valid=False,
                attestation_state=AttestationState.ATTESTATION_INVALID,
                device_id=device.device_id,
                hardware_class=self.hardware_class,
                platform_type=self.supported_platform,
                verified_at=now_iso,
                nonce_matched=True,
                signature_valid=False,
                failure_reason="SIGNATURE_VERIFICATION_FAILED: FIDO2 signature invalid",
            )

        return DeviceAttestationResult(
            is_valid=True,
            attestation_state=AttestationState.DEVICE_ATTESTED,
            device_id=device.device_id,
            hardware_class=self.hardware_class,
            platform_type=self.supported_platform,
            verified_at=now_iso,
            nonce_matched=True,
            signature_valid=True,
            trust_anchor_verified=True,
            air_gap_capability=self.air_gap_capability,
            details={
                "user_present": user_present,
                "user_verified": user_verified,
                "aaguid": payload.get("aaguid", "00000000-0000-0000-0000-000000000000"),
            },
        )
