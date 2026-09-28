# AegisTrace Hardware Attestation Model

## 1. Overview & Threat Context

In high-consequence defense, intelligence, and regulated enterprise environments, software running on an endpoint cannot be assumed trustworthy if the endpoint itself lacks a verified hardware root of trust. Operating system kernels, virtualization layers, and dynamic linkers can be subverted by rootkits or malicious hypervisors.

AegisTrace implements a hardware-attested trust model supporting:
1. **TPM 2.0 (Windows / Linux)**
2. **Apple Secure Enclave (macOS / iOS App Attest)**
3. **Android Keymaster / StrongBox**
4. **WebAuthn / FIDO2 Hardware Security Keys**
5. **Local Software Fallback (Strictly UNATTESTED)**

---

## 2. Platform Attestation Providers

### 2.1 TPM 2.0 (Windows & Linux)
- **Standard**: Trusted Computing Group (TCG) TPM 2.0 Architecture.
- **Hardware Class**: `DEDICATED_HARDWARE_HSM`.
- **Root of Trust**: Manufacturer Endorsement Key (EK) and Attestation Identity Key (AIK).
- **Verification Flow**:
  1. Verifier issues 256-bit fresh challenge nonce $N$.
  2. Client TPM quotes Platform Configuration Registers (PCRs) with $N$ embedded in `extraData`.
  3. AIK signs quote structure (`TPM2B_ATTEST`).
  4. Verifier cryptographically verifies AIK signature, validates $N$, verifies PCR digests, and validates the device key binding.

### 2.2 Apple Secure Enclave & App Attest (macOS / iOS)
- **Standard**: Apple App Attest / DeviceCheck API.
- **Hardware Class**: `ISOLATED_SECURITY_PROCESSOR`.
- **Root of Trust**: Apple Silicon / T2 co-processor burned-in cryptographic keys.
- **Verification Flow**:
  1. Verifier issues fresh challenge nonce $N$.
  2. App Attest generates an assertion over `clientDataHash = SHA256(N)`.
  3. Secure Enclave signs `authenticatorData || SHA256(N)` using hardware-bound P-256 key.
  4. Verifier validates signature, counter freshness, and challenge nonce match.

### 2.3 Android Keymaster / StrongBox
- **Standard**: Android Hardware Key Attestation.
- **Hardware Class**: `ISOLATED_SECURITY_PROCESSOR` (StrongBox) or `TRUSTED_EXECUTION_ENVIRONMENT` (TEE).
- **Root of Trust**: Google Hardware Attestation Root CA.
- **Verification Flow**:
  1. Client requests key generation with `attestationChallenge = N`.
  2. Keystore produces X.509 certificate chain where leaf cert contains ASN.1 `KeyDescription` extension.
  3. Verifier parses extension, verifies $N$, confirms `securityLevel == StrongBox`, and verifies `verifiedBootState == Verified`.

### 2.4 FIDO2 / WebAuthn Hardware Security Keys
- **Standard**: FIDO Alliance WebAuthn Level 2 / CTAP2.
- **Hardware Class**: `DEDICATED_HARDWARE_HSM`.
- **Root of Trust**: FIDO Alliance Metadata Service (MDS) certified hardware tokens (e.g. YubiKey 5).
- **Verification Flow**:
  1. Verifier issues WebAuthn challenge $N$.
  2. Authenticator executes user presence (UP) and user verification (UV) checks.
  3. Client returns `clientDataJSON` and `authenticatorData`.
  4. Verifier confirms $N \in clientDataJSON$, checks UP/UV bits, and verifies credential signature.

---

## 3. The Strict Honesty Invariant

```
+-------------------------------------------------------------------------+
|                       STRICT HONESTY INVARIANT                          |
|                                                                         |
| A software-generated key, regardless of how cleanly its cryptographic   |
| signature over the challenge nonce verifies, MUST NEVER be promoted to  |
|                         DEVICE_ATTESTED.                                |
|                                                                         |
| The verifier strictly assigns:                                          |
|   attestation_state = DEVICE_UNATTESTED                                 |
|   hardware_class    = SOFTWARE_FALLBACK                                 |
|   trust_anchor      = UNVERIFIED / ABSENT                               |
+-------------------------------------------------------------------------+
```

This prevents software emulators, development VMs, or attackers running on compromised consumer OSes from masquerading as hardware-secured endpoints.

---

## 4. Challenge-Response Engine

To prevent replay, relay, and reflection attacks, challenges strictly enforce:

1. **Entropy**: 256 bits of cryptographically secure random bytes (`os.urandom(32)`).
2. **Single-Use Enforcement**: Nonces are tracked in memory and consumed upon first validation. Any subsequent submission returns `NONCE_REUSED_REPLAY_ATTACK`.
3. **Time-Bounded Validity**: Default TTL of 120 seconds. Expired nonces return `CHALLENGE_EXPIRED`.
4. **Context Binding**: Nonces are cryptographically bound to `(device_id, organization_id)`. Presenting a nonce generated for Device A from Device B returns `DEVICE_ID_MISMATCH`.

---

## 5. Air-Gapped & Offline Verification Architecture

AegisTrace operates 100% offline in air-gapped environments without live cloud or internet connectivity.

| Provider | Air-Gapped Verification Strategy | Network Requirement |
| :--- | :--- | :--- |
| **TPM 2.0** | Preloaded TCG OEM Endorsement Roots (Intel, AMD, Infineon, STMicro). | **Zero** (100% local). |
| **Apple Secure Enclave** | Preloaded Apple Root CA certificate chain. | **Zero** for assertion validation. |
| **Android StrongBox** | Preloaded Google Hardware Attestation Root CA certificates. | **Zero** (100% local). |
| **WebAuthn FIDO2** | Preloaded FIDO Alliance Metadata Service root blob. | **Zero** (100% local). |
| **Local Software** | Verified locally using registered device public key. | **Zero** (100% local). |
