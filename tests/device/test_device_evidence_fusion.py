"""
Unit tests for AegisTrace Device Evidence Model & Forensic Fusion Integration.

Verifies:
- DeviceEvidenceAdapter produces calibrated log-likelihood ratio (LLR) scores:
  * ATTESTED hardware: positive corroboration (+3.5)
  * UNATTESTED software: neutral score (0.0)
  * REVOKED or MISMATCHED: heavy negative penalty (-5.0)
- Explicit forensic boundary statement enforcement
- Integration with EvidenceBundle and EvidenceFusionEngine
- Independent corroborating channel without double-counting
"""

import hashlib
import pytest
from Crypto.PublicKey import ECC

from core.attribution.evidence import (
    EvidenceBundle,
    EvidenceFamily,
    DependencyType,
    DeviceAttestationObservation,
    ProvenanceObservation,
)
from core.attribution.fusion import EvidenceFusionEngine
from core.device.models import (
    DevicePrincipal,
    AttestationState,
    DeviceStatus,
    PlatformType,
    HardwareClass,
)
from core.device.evidence import DeviceEvidenceAdapter


def create_device(
    device_id: str,
    attestation_state: AttestationState,
    hardware_class: HardwareClass,
    status: DeviceStatus = DeviceStatus.ACTIVE,
    recipient_id: str = "rec_alice",
) -> DevicePrincipal:
    key = ECC.generate(curve="P-256")
    pem = key.public_key().export_key(format="PEM")
    key_id = f"dkey_{hashlib.sha256(pem.encode()).hexdigest()[:16]}"

    return DevicePrincipal(
        device_id=device_id,
        organization_id="org_defense",
        device_key_id=key_id,
        public_key_pem=pem,
        platform=PlatformType.TPM_2_0 if attestation_state == AttestationState.DEVICE_ATTESTED else PlatformType.SOFTWARE_LOCAL,
        hardware_class=hardware_class,
        attestation_state=attestation_state,
        status=status,
        registered_to_recipient_id=recipient_id,
    )


def test_device_evidence_adapter_attested():
    dev = create_device(
        device_id="dev_hardware_tpm",
        attestation_state=AttestationState.DEVICE_ATTESTED,
        hardware_class=HardwareClass.DEDICATED_HARDWARE_HSM,
        recipient_id="rec_alice",
    )

    obs = DeviceEvidenceAdapter.device_to_observation(dev)

    assert obs.family == EvidenceFamily.DEVICE_ATTESTATION
    assert obs.dependency_type == DependencyType.INDEPENDENT
    assert obs.is_valid is True
    assert obs.log_likelihood_ratio == 3.5
    assert obs.primary_candidate == "rec_alice"
    assert obs.candidate_scores["rec_alice"] == 3.5
    assert obs.is_hardware_attested is True
    assert obs.is_device_revoked is False
    assert "FORENSIC BOUNDARY" in obs.boundary_statement


def test_device_evidence_adapter_unattested_neutral():
    """
    CRITICAL FORENSIC INVARIANT:
    Unattested software devices must have a neutral LLR (0.0).
    They must never falsely inflate confidence.
    """
    dev = create_device(
        device_id="dev_software_laptop",
        attestation_state=AttestationState.DEVICE_UNATTESTED,
        hardware_class=HardwareClass.SOFTWARE_FALLBACK,
        recipient_id="rec_bob",
    )

    obs = DeviceEvidenceAdapter.device_to_observation(dev)

    assert obs.family == EvidenceFamily.DEVICE_ATTESTATION
    assert obs.is_valid is True
    assert obs.log_likelihood_ratio == 0.0
    assert obs.is_hardware_attested is False
    assert obs.candidate_scores["rec_bob"] == 0.0


def test_device_evidence_adapter_revoked_penalty():
    dev = create_device(
        device_id="dev_compromised",
        attestation_state=AttestationState.DEVICE_REVOKED,
        hardware_class=HardwareClass.DEDICATED_HARDWARE_HSM,
        status=DeviceStatus.REVOKED,
        recipient_id="rec_charlie",
    )

    obs = DeviceEvidenceAdapter.device_to_observation(dev)

    assert obs.family == EvidenceFamily.DEVICE_ATTESTATION
    assert obs.is_valid is False
    assert obs.log_likelihood_ratio == -5.0
    assert obs.is_device_revoked is True
    assert obs.candidate_scores["rec_charlie"] == -5.0


def test_device_evidence_adapter_key_mismatch_penalty():
    dev = create_device(
        device_id="dev_tampered",
        attestation_state=AttestationState.DEVICE_KEY_MISMATCH,
        hardware_class=HardwareClass.DEDICATED_HARDWARE_HSM,
        recipient_id="rec_dave",
    )

    obs = DeviceEvidenceAdapter.device_to_observation(dev)

    assert obs.family == EvidenceFamily.DEVICE_ATTESTATION
    assert obs.is_valid is False
    assert obs.log_likelihood_ratio == -5.0


def test_device_evidence_in_evidence_bundle():
    bundle = EvidenceBundle(bundle_id="bundle_case_001")
    dev = create_device(
        device_id="dev_surface_tpm",
        attestation_state=AttestationState.DEVICE_ATTESTED,
        hardware_class=HardwareClass.DEDICATED_HARDWARE_HSM,
        recipient_id="rec_alice",
    )

    obs = DeviceEvidenceAdapter.device_to_observation(dev)
    bundle.add_observation(obs)

    att_obs_list = bundle.get_by_family(EvidenceFamily.DEVICE_ATTESTATION)
    assert len(att_obs_list) == 1
    assert att_obs_list[0].device_id == "dev_surface_tpm"
    assert "rec_alice" in bundle.get_candidate_ids()


def test_device_evidence_fusion_engine_corroboration():
    """
    Verifies that the EvidenceFusionEngine correctly ingests and processes
    DeviceAttestationObservation alongside other evidence.
    """
    bundle = EvidenceBundle(bundle_id="bundle_multimodal_002")

    # 1. Provenance Observation (ML-DSA signature)
    prov_obs = ProvenanceObservation(
        source_id="prov_sig_01",
        dependency_type=DependencyType.INDEPENDENT,
        title="ML-DSA Provenance Signature",
        is_valid=True,
        log_likelihood_ratio=4.0,
        primary_candidate="rec_alice",
        candidate_scores={"rec_alice": 4.0},
        recipient_id="rec_alice",
        is_signature_valid=True,
    )
    bundle.add_observation(prov_obs)

    # 2. Hardware Device Attestation Observation
    dev = create_device(
        device_id="dev_hardware_laptop",
        attestation_state=AttestationState.DEVICE_ATTESTED,
        hardware_class=HardwareClass.DEDICATED_HARDWARE_HSM,
        recipient_id="rec_alice",
    )
    dev_obs = DeviceEvidenceAdapter.device_to_observation(dev)
    bundle.add_observation(dev_obs)

    engine = EvidenceFusionEngine()
    result = engine.fuse(bundle)

    # Fusion successfully identifies Alice with corroborating device evidence
    assert result.top_candidate_id == "rec_alice"
    assert result.fused_score > 2.0
    assert "dev-att-dev_hardware_laptop" in result.supporting_sources
