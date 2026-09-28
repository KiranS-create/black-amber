"""
Adversarial security and invariant verification tests for AegisTrace Device Subsystem.

Tests adversarial attack scenarios:
1. Nonce tampering in attestation evidence
2. Challenge nonce replay and stale token presentation
3. Multi-tenant cross-boundary nonce injection
4. Public key substitution and rogue key claiming
5. Cloned device ID spoofing
6. Uncorroborated human boundary (device != human)
7. Shared kiosk / multi-user session isolation
8. Software key claiming hardware security (spoof prevention)
"""

import base64
import hashlib
import pytest
from Crypto.PublicKey import ECC
from Crypto.Signature import DSS
from Crypto.Hash import SHA256

from core.crypto.signatures import MLDSA65
from core.device.models import (
    DevicePrincipal,
    AttestationEvidence,
    AttestationState,
    DeviceStatus,
    PlatformType,
    HardwareClass,
    AttestationProviderType,
)
from core.device.enrollment import DeviceEnrollmentService
from core.device.challenge import ChallengeManager
from core.device.policy import (
    TrustPolicyEngine,
    OperationType,
    OperationAssuranceLevel,
)
from core.device.session import (
    DeviceSessionManager,
    BoundDeviceSession,
)


def create_ecc_keypair():
    key = ECC.generate(curve="P-256")
    pub_pem = key.public_key().export_key(format="PEM")
    return key, pub_pem


# ---------------------------------------------------------------------------
# ATTACK 1: NONCE TAMPERING IN ATTESTATION EVIDENCE
# ---------------------------------------------------------------------------

def test_attack_tampered_challenge_nonce():
    svc = DeviceEnrollmentService()
    ch_mgr = svc.challenge_manager
    aik_key, aik_pem = create_ecc_keypair()
    _, dev_pem = create_ecc_keypair()
    dev_key_id = f"dkey_{hashlib.sha256(dev_pem.encode()).hexdigest()[:16]}"

    dev = svc.register_device(
        device_id="dev_victim_01",
        organization_id="org_defense",
        public_key_pem=dev_pem,
        platform=PlatformType.TPM_2_0,
    )

    legit_ch = ch_mgr.create_challenge("dev_victim_01", "org_defense")

    # Attacker tampers with the nonce in the quote
    tampered_nonce = legit_ch.nonce_hex[:-4] + "dead"
    quote_bytes = f"TPM2_QUOTE:extraData={tampered_nonce}".encode()
    h = SHA256.new(quote_bytes)
    sig = DSS.new(aik_key, 'fips-186-3').sign(h)

    evidence = AttestationEvidence(
        evidence_id="ev_tampered",
        device_id="dev_victim_01",
        provider_type=AttestationProviderType.TPM_WINDOWS,
        challenge_nonce=tampered_nonce,
        evidence_payload={
            "quote_bytes_b64": base64.b64encode(quote_bytes).decode('ascii'),
            "signature_b64": base64.b64encode(sig).decode('ascii'),
            "aik_public_key_pem": aik_pem,
            "extra_data_nonce": tampered_nonce,
            "attested_key_id": dev_key_id,
        }
    )

    # Verification against expected legit_ch.nonce_hex fails
    res = svc.verifier.verify(evidence, dev, expected_nonce_hex=legit_ch.nonce_hex)
    assert res.is_valid is False
    assert res.attestation_state == AttestationState.ATTESTATION_INVALID
    assert res.nonce_matched is False


# ---------------------------------------------------------------------------
# ATTACK 2: STALE / REPLAYED CHALLENGE NONCE
# ---------------------------------------------------------------------------

def test_attack_stale_nonce_replay():
    ch_mgr = ChallengeManager()
    ch = ch_mgr.create_challenge("dev_victim_02", "org_defense")

    # First legitimate consumption
    valid1, _ = ch_mgr.validate_nonce(ch.nonce_hex, "dev_victim_02", "org_defense", consume=True)
    assert valid1 is True

    # Attacker replays consumed nonce
    valid2, reason2 = ch_mgr.validate_nonce(ch.nonce_hex, "dev_victim_02", "org_defense", consume=True)
    assert valid2 is False
    assert reason2 == "NONCE_REUSED_REPLAY_ATTACK"


# ---------------------------------------------------------------------------
# ATTACK 3: MULTI-TENANT CROSS-BOUNDARY NONCE INJECTION
# ---------------------------------------------------------------------------

def test_attack_cross_tenant_nonce_injection():
    ch_mgr = ChallengeManager()
    # Nonce issued for Department of Energy (org_energy)
    ch_energy = ch_mgr.create_challenge("dev_shared_model", "org_energy")

    # Attacker attempts to validate it against Department of Defense (org_defense)
    valid, reason = ch_mgr.validate_nonce(
        ch_energy.nonce_hex,
        device_id="dev_shared_model",
        organization_id="org_defense",
    )
    assert valid is False
    assert reason == "ORGANIZATION_MISMATCH"


# ---------------------------------------------------------------------------
# ATTACK 4: PUBLIC KEY SUBSTITUTION / ROGUE KEY CLAIMING
# ---------------------------------------------------------------------------

def test_attack_key_substitution_detection():
    svc = DeviceEnrollmentService()
    _, legitimate_pem = create_ecc_keypair()
    _, rogue_pem = create_ecc_keypair()
    aik_key, aik_pem = create_ecc_keypair()

    dev = svc.register_device(
        device_id="dev_target",
        organization_id="org_defense",
        public_key_pem=legitimate_pem,
        platform=PlatformType.TPM_2_0,
    )

    legit_key_id = dev.device_key_id
    rogue_key_id = f"dkey_{hashlib.sha256(rogue_pem.encode()).hexdigest()[:16]}"
    nonce = hashlib.sha256(b"n").hexdigest()

    # Attacker generates quote that binds to rogue_key_id instead of registered legit_key_id
    quote_bytes = f"TPM2_QUOTE:extraData={nonce}".encode()
    sig = DSS.new(aik_key, 'fips-186-3').sign(SHA256.new(quote_bytes))

    evidence = AttestationEvidence(
        evidence_id="ev_subst",
        device_id="dev_target",
        provider_type=AttestationProviderType.TPM_WINDOWS,
        challenge_nonce=nonce,
        evidence_payload={
            "quote_bytes_b64": base64.b64encode(quote_bytes).decode('ascii'),
            "signature_b64": base64.b64encode(sig).decode('ascii'),
            "aik_public_key_pem": aik_pem,
            "extra_data_nonce": nonce,
            "attested_key_id": rogue_key_id,
        }
    )

    res = svc.verifier.verify(evidence, dev, expected_nonce_hex=nonce)
    assert res.is_valid is False
    assert res.attestation_state == AttestationState.DEVICE_KEY_MISMATCH


# ---------------------------------------------------------------------------
# ATTACK 5: CLONED DEVICE ID SPOOFING
# ---------------------------------------------------------------------------

def test_attack_cloned_device_id_rejection():
    svc = DeviceEnrollmentService()
    _, pem1 = create_ecc_keypair()
    _, pem2 = create_ecc_keypair()

    svc.register_device("dev_cloned", "org_ops", pem1)

    # Rogue attempt to overwrite or duplicate existing device_id
    with pytest.raises(ValueError, match="already enrolled"):
        svc.register_device("dev_cloned", "org_ops", pem2)


# ---------------------------------------------------------------------------
# INVARIANT 6: UNCORROBORATED HUMAN BOUNDARY (DEVICE != HUMAN)
# ---------------------------------------------------------------------------

def test_invariant_device_does_not_prove_human_consent():
    """
    CRITICAL FORENSIC INVARIANT:
    A valid device attestation only proves the device platform was genuine.
    It DOES NOT prove that the human recipient authorized the operation
    without the recipient's post-quantum ML-DSA signature.
    """
    session_mgr = DeviceSessionManager()
    _, pem = create_ecc_keypair()
    dev = DevicePrincipal(
        device_id="dev_secure_workstation",
        organization_id="org_hq",
        device_key_id="dkey_test",
        public_key_pem=pem,
        platform=PlatformType.TPM_2_0,
        hardware_class=HardwareClass.DEDICATED_HARDWARE_HSM,
        attestation_state=AttestationState.DEVICE_ATTESTED,
    )

    doc_hash = hashlib.sha256(b"classified_mission_plan").hexdigest()
    session = session_mgr.create_bound_session(
        session_id="ses_human_test",
        recipient_id="rec_general_smith",
        device=dev,
        document_root_hash=doc_hash,
    )

    # An unauthorized party attempts to claim decryption without Smith's ML-DSA signature
    # Notice: device is genuinely attested, but recipient signature is empty or unverified
    receipt = session_mgr.create_decryption_receipt(
        session=session,
        device=dev,
        recipient_signature_bytes=b"",  # Empty signature
        document_id="doc_mission",
    )

    # Forensic invariant: Receipt records recipient_signature_b64 as empty
    assert receipt.recipient_signature_b64 == ""
    assert receipt.device_attestation_state == AttestationState.DEVICE_ATTESTED
    # The platform trust DOES NOT substitute for the missing human authorization
    assert receipt.device_id == dev.device_id
    assert receipt.recipient_id == "rec_general_smith"


# ---------------------------------------------------------------------------
# INVARIANT 7: SHARED KIOSK / MULTI-USER SESSION ISOLATION
# ---------------------------------------------------------------------------

def test_invariant_shared_kiosk_multi_user_isolation():
    """
    A single physical terminal (dev_kiosk) may be used by multiple recipients (Alice, Bob).
    Their sessions MUST have distinct fingerprints and cryptographic isolation.
    """
    session_mgr = DeviceSessionManager()
    _, pem = create_ecc_keypair()
    kiosk = DevicePrincipal(
        device_id="dev_kiosk_secure",
        organization_id="org_embassy",
        device_key_id="dkey_kiosk",
        public_key_pem=pem,
        platform=PlatformType.TPM_2_0,
        hardware_class=HardwareClass.DEDICATED_HARDWARE_HSM,
        attestation_state=AttestationState.DEVICE_ATTESTED,
    )

    doc_hash = hashlib.sha256(b"embassy_cables").hexdigest()

    session_alice = session_mgr.create_bound_session(
        session_id="ses_kiosk_alice",
        recipient_id="rec_alice",
        device=kiosk,
        document_root_hash=doc_hash,
    )

    session_bob = session_mgr.create_bound_session(
        session_id="ses_kiosk_bob",
        recipient_id="rec_bob",
        device=kiosk,
        document_root_hash=doc_hash,
    )

    # Same device, but different recipients and different session nonces
    assert session_alice.device_id == session_bob.device_id
    assert session_alice.recipient_id != session_bob.recipient_id
    assert session_alice.compute_session_fingerprint() != session_bob.compute_session_fingerprint()


# ---------------------------------------------------------------------------
# INVARIANT 8: SOFTWARE CANNOT SPOOF HARDWARE ATTESTATION
# ---------------------------------------------------------------------------

def test_invariant_software_cannot_spoof_hardware():
    """
    An attacker claiming TPM_WINDOWS provider type with a software key lacking
    genuine AIK quote format is rejected.
    """
    svc = DeviceEnrollmentService()
    soft_key, soft_pem = create_ecc_keypair()
    nonce = hashlib.sha256(b"nonce").hexdigest()

    dev = svc.register_device(
        device_id="dev_fake_tpm",
        organization_id="org_lab",
        public_key_pem=soft_pem,
        platform=PlatformType.SOFTWARE_LOCAL,
    )

    # Attacker crafts bogus evidence pretending to be TPM
    evidence = AttestationEvidence(
        evidence_id="ev_spoof",
        device_id="dev_fake_tpm",
        provider_type=AttestationProviderType.TPM_WINDOWS,
        challenge_nonce=nonce,
        evidence_payload={
            # Missing real quote and AIK
            "extra_data_nonce": nonce,
        }
    )

    res = svc.verifier.verify(evidence, dev, expected_nonce_hex=nonce)
    assert res.is_valid is False
    assert res.attestation_state == AttestationState.ATTESTATION_INVALID
    assert res.trust_anchor_verified is False
