"""
AegisTrace Device Evidence Model & Forensic Fusion Adapter.

Bridges device identity and hardware attestation verification into the core
EvidenceBundle and EvidenceFusionEngine.

CRITICAL FORENSIC INVARIANTS:
1. Valid device attestation proves hardware trust and device key possession;
   it does NOT prove human culpability.
2. Unattested devices provide neutral LLR (0.0), acknowledging device presence
   without falsely claiming hardware security.
3. Revoked or mismatched devices emit negative LLR (-5.0) to flag compromised state.
"""

from typing import Optional, Dict, Any

from core.attribution.evidence import (
    EvidenceBundle,
    EvidenceFamily,
    DependencyType,
    DeviceAttestationObservation,
    TargetBinding,
)
from core.device.models import (
    DevicePrincipal,
    AttestationState,
    HardwareClass,
    DeviceStatus,
)


class DeviceEvidenceAdapter:
    """
    Constructs calibrated DeviceAttestationObservation records and binds them into an EvidenceBundle.
    """

    @staticmethod
    def device_to_observation(
        device: DevicePrincipal,
        target_binding: Optional[TargetBinding] = None,
        source_id: Optional[str] = None,
    ) -> DeviceAttestationObservation:
        """
        Produce a calibrated forensic DeviceAttestationObservation from a DevicePrincipal.
        """
        # Determine LLR based on attestation state and administrative status
        if device.status == DeviceStatus.REVOKED or device.attestation_state == AttestationState.DEVICE_REVOKED:
            llr = -5.0
            reliability = 0.95
        elif device.attestation_state in (AttestationState.DEVICE_KEY_MISMATCH, AttestationState.ATTESTATION_INVALID):
            llr = -5.0
            reliability = 0.90
        elif device.attestation_state == AttestationState.DEVICE_ATTESTED:
            # Hardware verified
            llr = 3.5
            reliability = 0.95
        elif device.attestation_state == AttestationState.DEVICE_UNATTESTED:
            # Neutral observation: key exists, but no hardware root of trust
            llr = 0.0
            reliability = 0.65
        else:
            llr = 0.0
            reliability = 0.50

        is_hw_attested = (device.attestation_state == AttestationState.DEVICE_ATTESTED)
        is_revoked = (device.status == DeviceStatus.REVOKED)

        boundary_stmt = (
            "FORENSIC BOUNDARY: Hardware attestation verifies device platform integrity and "
            "cryptographic key possession. It does NOT prove personal human operation."
        )

        scores = {}
        if device.registered_to_recipient_id:
            # Device evidence provides corroborating score towards its registered recipient
            scores[device.registered_to_recipient_id] = llr

        obs = DeviceAttestationObservation(
            source_id=source_id or f"dev-att-{device.device_id}",
            family=EvidenceFamily.DEVICE_ATTESTATION,
            dependency_type=DependencyType.INDEPENDENT,
            title="Hardware Device Attestation Evidence",
            is_valid=(device.status != DeviceStatus.REVOKED and device.attestation_state != AttestationState.DEVICE_KEY_MISMATCH),
            log_likelihood_ratio=llr,
            candidate_scores=scores,
            primary_candidate=device.registered_to_recipient_id,
            reliability_prior=reliability,
            effective_reliability=reliability,
            target_binding=target_binding or TargetBinding(),
            device_id=device.device_id,
            device_key_id=device.device_key_id,
            attestation_state=device.attestation_state.value,
            hardware_class=device.hardware_class.value,
            platform_type=device.platform.value,
            organization_id=device.organization_id,
            is_hardware_attested=is_hw_attested,
            is_device_revoked=is_revoked,
            boundary_statement=boundary_stmt,
            details={
                "platform_version": device.platform_version,
                "attestation_provider": device.attestation_provider,
                "attestation_timestamp": device.attestation_timestamp,
                "key_epoch": device.key_epoch,
                "status": device.status.value,
            },
        )
        return obs

    @classmethod
    def attach_to_bundle(
        cls,
        bundle: EvidenceBundle,
        device: DevicePrincipal,
        source_id: Optional[str] = None,
    ) -> DeviceAttestationObservation:
        """
        Attaches the device attestation observation to an existing EvidenceBundle.
        """
        obs = cls.device_to_observation(device, target_binding=bundle.target_binding, source_id=source_id)
        bundle.add_observation(obs)
        return obs
