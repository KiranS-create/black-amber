"""
AegisTrace Device Identity & Hardware Attestation Models.

Defines the production-grade DevicePrincipal, attestation states, platform
security module classifications, hardware assurance tiers, and attestation evidence.

CRITICAL ARCHITECTURAL INVARIANTS:
1. A device is NEVER trusted merely because an ID, hostname, MAC address,
   or browser fingerprint was reported.
2. The system strictly separates:
   - AUTHENTICATED USER (Identity / IdP)
   - RECIPIENT PRINCIPAL (Cryptographic release recipient)
   - DEVICE IDENTITY (Cryptographic device key reference)
   - ATTESTED DEVICE (Hardware-verified via TPM/SE/StrongBox)
   - UNATTESTED DEVICE (Software or unverified device)
   - COMPROMISED / SUSPICIOUS DEVICE (Takeover, impossible travel, tampered)
   - UNKNOWN DEVICE (Unregistered)
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field


class DeviceStatus(str, Enum):
    """Lifecycle administrative status of an enrolled device."""
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    REVOKED = "REVOKED"
    UNKNOWN = "UNKNOWN"


class AttestationState(str, Enum):
    """
    Forensically verified attestation state of a device.
    Never promotes UNATTESTED to ATTESTED without genuine hardware evidence.
    """
    DEVICE_ATTESTED = "DEVICE_ATTESTED"          # Cryptographically verified hardware-backed key (TPM/SE/StrongBox)
    DEVICE_UNATTESTED = "DEVICE_UNATTESTED"      # Valid cryptographic key, but lacking hardware root-of-trust
    DEVICE_KEY_MATCH = "DEVICE_KEY_MATCH"        # Challenge-response validated against registered device key
    DEVICE_KEY_MISMATCH = "DEVICE_KEY_MISMATCH"  # Challenge signature does not match registered device key
    ATTESTATION_EXPIRED = "ATTESTATION_EXPIRED"  # Attestation certificate or statement expired
    ATTESTATION_INVALID = "ATTESTATION_INVALID"  # Malformed attestation evidence or failed signature
    DEVICE_REVOKED = "DEVICE_REVOKED"            # Device explicitly revoked by security administrator
    DEVICE_UNKNOWN = "DEVICE_UNKNOWN"            # Unregistered device presenting claims
    PLATFORM_UNSUPPORTED = "PLATFORM_UNSUPPORTED" # Requested platform attestation not supported on runtime


class PlatformType(str, Enum):
    """Platform security architecture classification."""
    TPM_2_0 = "TPM_2_0"                           # Trusted Platform Module 2.0 (Windows / Linux)
    APPLE_SECURE_ENCLAVE = "APPLE_SECURE_ENCLAVE" # Apple T2 / A-Series / M-Series Secure Enclave (App Attest)
    ANDROID_STRONGBOX = "ANDROID_STRONGBOX"       # Android Keymaster / StrongBox Hardware Security Module
    WEBAUTHN_FIDO2 = "WEBAUTHN_FIDO2"             # FIDO2 / WebAuthn Hardware Security Key (e.g. YubiKey)
    SOFTWARE_LOCAL = "SOFTWARE_LOCAL"             # Local software keypair (non-hardware)


class HardwareClass(str, Enum):
    """Hardware assurance and isolation level."""
    DEDICATED_HARDWARE_HSM = "DEDICATED_HARDWARE_HSM"             # Discrete crypto chip (TPM 2.0, YubiKey)
    ISOLATED_SECURITY_PROCESSOR = "ISOLATED_SECURITY_PROCESSOR"   # Dedicated co-processor (Apple SE, StrongBox)
    TRUSTED_EXECUTION_ENVIRONMENT = "TRUSTED_EXECUTION_ENVIRONMENT" # ARM TrustZone, Intel SGX, AMD SEV
    GENERIC_OS_SECURE_STORAGE = "GENERIC_OS_SECURE_STORAGE"       # OS-level encrypted keystore (CNG, Keychain)
    SOFTWARE_FALLBACK = "SOFTWARE_FALLBACK"                       # Pure software memory / disk storage


class AttestationProviderType(str, Enum):
    """Attestation provider implementation identifier."""
    TPM_WINDOWS = "TPM_WINDOWS"
    APPLE_APP_ATTEST = "APPLE_APP_ATTEST"
    ANDROID_KEY_ATTESTATION = "ANDROID_KEY_ATTESTATION"
    FIDO2_WEBAUTHN = "FIDO2_WEBAUTHN"
    LOCAL_SOFTWARE = "LOCAL_SOFTWARE"


class AirGappedAttestationCapability(str, Enum):
    """Operational capability in air-gapped / offline deployments."""
    AIR_GAPPED_ATTESTATION_CAPABLE = "AIR_GAPPED_ATTESTATION_CAPABLE" # Verifiable fully offline using preloaded roots
    AIR_GAPPED_ATTESTATION_LIMITED = "AIR_GAPPED_ATTESTATION_LIMITED" # Requires cached intermediates; no live OCSP
    UNATTESTED = "UNATTESTED"                                         # No hardware attestation claimed


class DevicePrincipal(BaseModel):
    """
    Cryptographic Device Security Principal in AegisTrace.
    Binds an opaque, immutable device identifier to an organization, hardware platform,
    enrolled cryptographic key, and verified attestation state.

    INVARIANT: Does not use mutable hostnames, MAC addresses, or IP addresses as identity.
    """
    device_id: str = Field(..., description="Stable opaque unique device identifier (e.g. dev_9c2a8f1b)")
    organization_id: str = Field(..., description="Multi-tenant isolation identifier (e.g. org_defense_contractor)")
    device_key_id: str = Field(..., description="Fingerprint (SHA-256) of enrolled device public key")
    public_key_pem: str = Field(..., description="Device public key in PEM format")
    public_key_algorithm: str = Field("P-256", description="Cryptographic algorithm: P-256, RSA-2048, or ML-DSA-65")
    platform: PlatformType = Field(PlatformType.SOFTWARE_LOCAL, description="Underlying security module platform")
    platform_version: str = Field("1.0", description="OS / Firmware version string")
    hardware_class: HardwareClass = Field(HardwareClass.SOFTWARE_FALLBACK, description="Assurance tier")
    attestation_state: AttestationState = Field(AttestationState.DEVICE_UNATTESTED, description="Current attestation state")
    attestation_provider: Optional[str] = Field(None, description="Provider used for last successful attestation")
    attestation_timestamp: Optional[str] = Field(None, description="ISO-8601 UTC timestamp of last verified attestation")
    first_seen: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    last_seen: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    key_epoch: int = Field(1, description="Current cryptographic key epoch")
    status: DeviceStatus = Field(DeviceStatus.ACTIVE, description="Administrative lifecycle status")
    registered_to_recipient_id: Optional[str] = Field(None, description="Primary RecipientPrincipal bound to device")
    revocation_reason: Optional[str] = None
    revoked_at: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Platform metadata (non-security-critical)")


class AttestationEvidence(BaseModel):
    """
    Structured attestation evidence package presented by a client device
    in response to an attestation challenge.
    """
    evidence_id: str = Field(..., description="Unique evidence tracking identifier")
    device_id: str = Field(..., description="Target DevicePrincipal.device_id")
    provider_type: AttestationProviderType
    challenge_nonce: str = Field(..., description="Fresh nonce provided by verifier")
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    evidence_payload: Dict[str, Any] = Field(default_factory=dict, description="Platform-specific evidence data")
    platform_claims: Dict[str, Any] = Field(default_factory=dict, description="Claims: secure_boot, pcr, tcb, etc.")
    raw_evidence_bytes_b64: Optional[str] = Field(None, description="Optional raw binary quote or token")
    is_air_gapped_compatible: bool = Field(True, description="Whether evidence can be verified without internet")


class DeviceAttestationResult(BaseModel):
    """
    Deterministic evaluation result produced by an attestation verifier.
    """
    is_valid: bool = False
    attestation_state: AttestationState
    device_id: str
    hardware_class: HardwareClass
    platform_type: PlatformType
    verified_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    nonce_matched: bool = False
    signature_valid: bool = False
    trust_anchor_verified: bool = False
    failure_reason: Optional[str] = None
    air_gap_capability: AirGappedAttestationCapability = AirGappedAttestationCapability.AIR_GAPPED_ATTESTATION_CAPABLE
    details: Dict[str, Any] = Field(default_factory=dict)
