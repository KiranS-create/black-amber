"""
Unit tests for AegisTrace Hardware Attestation Providers.

Verifies:
- TPM 2.0 provider: quotes, AIK signatures, PCR digests, secure boot claims
- Apple Secure Enclave provider: App Attest, clientDataHash, P-256 signatures
- Android StrongBox provider: KeyStore attestation, TEE/StrongBox levels, challenge binding
- WebAuthn FIDO2 provider: clientDataJSON, authenticatorData flags (UP/UV), signatures
- Local Software provider HONESTY INVARIANT: strictly reports DEVICE_UNATTESTED
  and SOFTWARE_FALLBACK even when cryptographic signatures are fully valid.
"""

import base64
import hashlib
import json
import pytest
from Crypto.PublicKey import ECC
from Crypto.Signature import DSS
from Crypto.Hash import SHA256

from core.device.models import (
    DevicePrincipal,
    AttestationEvidence,
    AttestationState,
    PlatformType,
    HardwareClass,
    AttestationProviderType,
)
from core.device.providers.tpm import TPMAttestationProvider
from core.device.providers.apple import AppleSecureEnclaveProvider
from core.device.providers.android import AndroidStrongBoxProvider
from core.device.providers.webauthn import WebAuthnDeviceProvider
from core.device.providers.software import LocalSoftwareDeviceProvider


def create_ecc_keypair():
    key = ECC.generate(curve="P-256")
    pub_pem = key.public_key().export_key(format="PEM")
    return key, pub_pem


# ---------------------------------------------------------------------------
# 1. TPM 2.0 PROVIDER TESTS
# ---------------------------------------------------------------------------

def test_tpm_attestation_success():
    provider = TPMAttestationProvider()
    aik_key, aik_pem = create_ecc_keypair()
    device_key, device_pem = create_ecc_keypair()
    device_key_id = f"dkey_{hashlib.sha256(device_pem.encode()).hexdigest()[:16]}"

    dev = DevicePrincipal(
        device_id="dev_win_tpm",
        organization_id="org_defense",
        device_key_id=device_key_id,
        public_key_pem=device_pem,
        public_key_algorithm="P-256",
        platform=PlatformType.TPM_2_0,
        hardware_class=HardwareClass.DEDICATED_HARDWARE_HSM,
    )

    nonce_hex = hashlib.sha256(b"fresh_nonce_1").hexdigest()
    # Mock TPM quote bytes
    quote_bytes = f"TPM2_QUOTE:extraData={nonce_hex}".encode()
    h = SHA256.new(quote_bytes)
    sig = DSS.new(aik_key, 'fips-186-3').sign(h)

    evidence = AttestationEvidence(
        evidence_id="ev_tpm_1",
        device_id="dev_win_tpm",
        provider_type=AttestationProviderType.TPM_WINDOWS,
        challenge_nonce=nonce_hex,
        evidence_payload={
            "quote_bytes_b64": base64.b64encode(quote_bytes).decode('ascii'),
            "signature_b64": base64.b64encode(sig).decode('ascii'),
            "aik_public_key_pem": aik_pem,
            "aik_algorithm": "P-256",
            "extra_data_nonce": nonce_hex,
            "attested_key_id": device_key_id,
        },
        platform_claims={
            "secure_boot_enabled": True,
            "pcr_digest": "a" * 64,
        }
    )

    res = provider.verify_attestation(evidence, dev, expected_nonce_hex=nonce_hex)
    assert res.is_valid is True
    assert res.attestation_state == AttestationState.DEVICE_ATTESTED
    assert res.hardware_class == HardwareClass.DEDICATED_HARDWARE_HSM
    assert res.nonce_matched is True
    assert res.signature_valid is True
    assert res.trust_anchor_verified is True
    assert res.details["secure_boot_enabled"] is True


def test_tpm_attestation_nonce_mismatch():
    provider = TPMAttestationProvider()
    aik_key, aik_pem = create_ecc_keypair()
    _, dev_pem = create_ecc_keypair()
    dev_key_id = f"dkey_{hashlib.sha256(dev_pem.encode()).hexdigest()[:16]}"

    dev = DevicePrincipal(
        device_id="dev_win_tpm",
        organization_id="org_defense",
        device_key_id=dev_key_id,
        public_key_pem=dev_pem,
        platform=PlatformType.TPM_2_0,
    )

    expected_nonce = hashlib.sha256(b"verifier_nonce").hexdigest()
    wrong_nonce = hashlib.sha256(b"stale_nonce").hexdigest()

    quote_bytes = f"TPM2_QUOTE:extraData={wrong_nonce}".encode()
    h = SHA256.new(quote_bytes)
    sig = DSS.new(aik_key, 'fips-186-3').sign(h)

    evidence = AttestationEvidence(
        evidence_id="ev_tpm_replay",
        device_id="dev_win_tpm",
        provider_type=AttestationProviderType.TPM_WINDOWS,
        challenge_nonce=wrong_nonce,
        evidence_payload={
            "quote_bytes_b64": base64.b64encode(quote_bytes).decode('ascii'),
            "signature_b64": base64.b64encode(sig).decode('ascii'),
            "aik_public_key_pem": aik_pem,
            "extra_data_nonce": wrong_nonce,
        }
    )

    res = provider.verify_attestation(evidence, dev, expected_nonce_hex=expected_nonce)
    assert res.is_valid is False
    assert res.attestation_state == AttestationState.ATTESTATION_INVALID
    assert "NONCE_MISMATCH" in (res.failure_reason or "")


def test_tpm_attestation_key_mismatch():
    provider = TPMAttestationProvider()
    aik_key, aik_pem = create_ecc_keypair()
    _, dev_pem = create_ecc_keypair()
    dev_key_id = f"dkey_{hashlib.sha256(dev_pem.encode()).hexdigest()[:16]}"

    dev = DevicePrincipal(
        device_id="dev_win_tpm",
        organization_id="org_defense",
        device_key_id=dev_key_id,
        public_key_pem=dev_pem,
        platform=PlatformType.TPM_2_0,
    )

    nonce_hex = hashlib.sha256(b"nonce_valid").hexdigest()
    quote_bytes = f"TPM2_QUOTE:extraData={nonce_hex}".encode()
    h = SHA256.new(quote_bytes)
    sig = DSS.new(aik_key, 'fips-186-3').sign(h)

    # Attested key id does not match registered device key id
    evidence = AttestationEvidence(
        evidence_id="ev_tpm_mismatch",
        device_id="dev_win_tpm",
        provider_type=AttestationProviderType.TPM_WINDOWS,
        challenge_nonce=nonce_hex,
        evidence_payload={
            "quote_bytes_b64": base64.b64encode(quote_bytes).decode('ascii'),
            "signature_b64": base64.b64encode(sig).decode('ascii'),
            "aik_public_key_pem": aik_pem,
            "extra_data_nonce": nonce_hex,
            "attested_key_id": "dkey_rogue_different_key",
        }
    )

    res = provider.verify_attestation(evidence, dev, expected_nonce_hex=nonce_hex)
    assert res.is_valid is False
    assert res.attestation_state == AttestationState.DEVICE_KEY_MISMATCH


# ---------------------------------------------------------------------------
# 2. APPLE SECURE ENCLAVE TESTS
# ---------------------------------------------------------------------------

def test_apple_secure_enclave_success():
    provider = AppleSecureEnclaveProvider()
    se_key, se_pem = create_ecc_keypair()
    dev_key_id = f"dkey_{hashlib.sha256(se_pem.encode()).hexdigest()[:16]}"

    dev = DevicePrincipal(
        device_id="dev_mac_m3",
        organization_id="org_aerospace",
        device_key_id=dev_key_id,
        public_key_pem=se_pem,
        platform=PlatformType.APPLE_SECURE_ENCLAVE,
        hardware_class=HardwareClass.ISOLATED_SECURITY_PROCESSOR,
    )

    nonce_hex = hashlib.sha256(b"apple_nonce").hexdigest()
    client_data_hash = hashlib.sha256(nonce_hex.encode()).hexdigest()
    auth_data = b"APPLE_APP_ATTEST_AUTH_DATA_FLAGS_RPID_COUNTER"
    to_sign = auth_data + hashlib.sha256(nonce_hex.encode()).digest()
    sig = DSS.new(se_key, 'fips-186-3').sign(SHA256.new(to_sign))

    evidence = AttestationEvidence(
        evidence_id="ev_apple_1",
        device_id="dev_mac_m3",
        provider_type=AttestationProviderType.APPLE_APP_ATTEST,
        challenge_nonce=nonce_hex,
        evidence_payload={
            "authenticator_data_b64": base64.b64encode(auth_data).decode('ascii'),
            "signature_b64": base64.b64encode(sig).decode('ascii'),
            "attestation_cert_pem": se_pem,
            "client_data_hash": client_data_hash,
        }
    )

    res = provider.verify_attestation(evidence, dev, expected_nonce_hex=nonce_hex)
    assert res.is_valid is True
    assert res.attestation_state == AttestationState.DEVICE_ATTESTED
    assert res.hardware_class == HardwareClass.ISOLATED_SECURITY_PROCESSOR
    assert res.nonce_matched is True
    assert res.signature_valid is True


# ---------------------------------------------------------------------------
# 3. ANDROID STRONGBOX TESTS
# ---------------------------------------------------------------------------

def test_android_strongbox_success():
    provider = AndroidStrongBoxProvider()
    sb_key, sb_pem = create_ecc_keypair()
    dev_key_id = f"dkey_{hashlib.sha256(sb_pem.encode()).hexdigest()[:16]}"

    dev = DevicePrincipal(
        device_id="dev_pixel_9",
        organization_id="org_mobile_field",
        device_key_id=dev_key_id,
        public_key_pem=sb_pem,
        platform=PlatformType.ANDROID_STRONGBOX,
        hardware_class=HardwareClass.ISOLATED_SECURITY_PROCESSOR,
    )

    nonce_hex = hashlib.sha256(b"android_nonce").hexdigest()
    msg = nonce_hex.encode('utf-8')
    sig = DSS.new(sb_key, 'fips-186-3').sign(SHA256.new(msg))

    evidence = AttestationEvidence(
        evidence_id="ev_android_1",
        device_id="dev_pixel_9",
        provider_type=AttestationProviderType.ANDROID_KEY_ATTESTATION,
        challenge_nonce=nonce_hex,
        evidence_payload={
            "attestation_challenge": nonce_hex,
            "signature_b64": base64.b64encode(sig).decode('ascii'),
            "leaf_cert_pem": sb_pem,
            "attestation_security_level": "StrongBox",
        },
        platform_claims={
            "verified_boot_state": "Verified",
        }
    )

    res = provider.verify_attestation(evidence, dev, expected_nonce_hex=nonce_hex)
    assert res.is_valid is True
    assert res.attestation_state == AttestationState.DEVICE_ATTESTED
    assert res.hardware_class == HardwareClass.ISOLATED_SECURITY_PROCESSOR
    assert res.details["verified_boot_state"] == "Verified"


# ---------------------------------------------------------------------------
# 4. WEBAUTHN FIDO2 TESTS
# ---------------------------------------------------------------------------

def test_webauthn_fido2_success():
    provider = WebAuthnDeviceProvider()
    fido_key, fido_pem = create_ecc_keypair()
    dev_key_id = f"dkey_{hashlib.sha256(fido_pem.encode()).hexdigest()[:16]}"

    dev = DevicePrincipal(
        device_id="dev_yubikey_5",
        organization_id="org_finance",
        device_key_id=dev_key_id,
        public_key_pem=fido_pem,
        platform=PlatformType.WEBAUTHN_FIDO2,
        hardware_class=HardwareClass.DEDICATED_HARDWARE_HSM,
    )

    nonce_hex = hashlib.sha256(b"webauthn_nonce").hexdigest()
    client_data = json.dumps({"type": "webauthn.get", "challenge": nonce_hex, "origin": "https://aegistrace.local"})
    # authenticatorData: 32 bytes rpIdHash + 1 byte flags (0x05 = UP + UV) + 4 bytes signCount
    auth_data = b"0" * 32 + bytes([0x05]) + bytes([0, 0, 0, 1])
    to_sign = auth_data + hashlib.sha256(client_data.encode()).digest()
    sig = DSS.new(fido_key, 'fips-186-3').sign(SHA256.new(to_sign))

    evidence = AttestationEvidence(
        evidence_id="ev_fido_1",
        device_id="dev_yubikey_5",
        provider_type=AttestationProviderType.FIDO2_WEBAUTHN,
        challenge_nonce=nonce_hex,
        evidence_payload={
            "client_data_json": client_data,
            "authenticator_data_b64": base64.b64encode(auth_data).decode('ascii'),
            "signature_b64": base64.b64encode(sig).decode('ascii'),
            "credential_public_key_pem": fido_pem,
        }
    )

    res = provider.verify_attestation(evidence, dev, expected_nonce_hex=nonce_hex)
    assert res.is_valid is True
    assert res.attestation_state == AttestationState.DEVICE_ATTESTED
    assert res.hardware_class == HardwareClass.DEDICATED_HARDWARE_HSM
    assert res.details["user_present"] is True
    assert res.details["user_verified"] is True


# ---------------------------------------------------------------------------
# 5. LOCAL SOFTWARE PROVIDER HONESTY INVARIANT TESTS
# ---------------------------------------------------------------------------

def test_software_provider_strictly_unattested():
    """
    CRITICAL HONESTY INVARIANT:
    Software key signs challenge validly, but MUST NEVER be promoted to DEVICE_ATTESTED.
    """
    provider = LocalSoftwareDeviceProvider()
    soft_key, soft_pem = create_ecc_keypair()
    dev_key_id = f"dkey_{hashlib.sha256(soft_pem.encode()).hexdigest()[:16]}"

    dev = DevicePrincipal(
        device_id="dev_linux_vm",
        organization_id="org_lab",
        device_key_id=dev_key_id,
        public_key_pem=soft_pem,
        platform=PlatformType.SOFTWARE_LOCAL,
        hardware_class=HardwareClass.SOFTWARE_FALLBACK,
    )

    nonce_hex = hashlib.sha256(b"soft_nonce").hexdigest()
    msg = nonce_hex.encode('utf-8')
    sig = DSS.new(soft_key, 'fips-186-3').sign(SHA256.new(msg))

    evidence = AttestationEvidence(
        evidence_id="ev_soft_1",
        device_id="dev_linux_vm",
        provider_type=AttestationProviderType.LOCAL_SOFTWARE,
        challenge_nonce=nonce_hex,
        evidence_payload={
            "signature_b64": base64.b64encode(sig).decode('ascii'),
            "public_key_pem": soft_pem,
        }
    )

    res = provider.verify_attestation(evidence, dev, expected_nonce_hex=nonce_hex)

    # Cryptographic validity is True
    assert res.is_valid is True
    assert res.signature_valid is True
    assert res.nonce_matched is True

    # BUT hardware attestation state is strictly UNATTESTED
    assert res.attestation_state == AttestationState.DEVICE_UNATTESTED
    assert res.hardware_class == HardwareClass.SOFTWARE_FALLBACK
    assert res.trust_anchor_verified is False
    assert "UNATTESTED" in res.details["assurance_note"]


def test_software_provider_key_mismatch():
    provider = LocalSoftwareDeviceProvider()
    _, soft_pem = create_ecc_keypair()
    wrong_key, _ = create_ecc_keypair()
    dev_key_id = f"dkey_{hashlib.sha256(soft_pem.encode()).hexdigest()[:16]}"

    dev = DevicePrincipal(
        device_id="dev_linux_vm",
        organization_id="org_lab",
        device_key_id=dev_key_id,
        public_key_pem=soft_pem,
        platform=PlatformType.SOFTWARE_LOCAL,
    )

    nonce_hex = hashlib.sha256(b"soft_nonce").hexdigest()
    # Signed by wrong key
    msg = nonce_hex.encode('utf-8')
    sig = DSS.new(wrong_key, 'fips-186-3').sign(SHA256.new(msg))

    evidence = AttestationEvidence(
        evidence_id="ev_soft_mismatch",
        device_id="dev_linux_vm",
        provider_type=AttestationProviderType.LOCAL_SOFTWARE,
        challenge_nonce=nonce_hex,
        evidence_payload={
            "signature_b64": base64.b64encode(sig).decode('ascii'),
        }
    )

    res = provider.verify_attestation(evidence, dev, expected_nonce_hex=nonce_hex)
    assert res.is_valid is False
    assert res.attestation_state == AttestationState.DEVICE_KEY_MISMATCH
