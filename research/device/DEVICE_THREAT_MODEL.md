# AegisTrace Device Threat Model & Adversarial Analysis

## 1. Adversary Capabilities & Threat Landscape

The AegisTrace threat model assumes an active, capable adversary operating within or adjacent to the protected document distribution perimeter. Specific adversary capabilities include:

1. **Malicious Endpoints**: Endpoints running untrusted OS kernels, emulators, or hypervisors with full memory inspection capabilities.
2. **Network Egress Attackers**: Adversaries capturing session tokens, challenge-response traffic, or encrypted release packages in transit.
3. **Insider Threats**: Legitimate enterprise employees attempting to exfiltrate documents or frame colleagues using shared physical hardware.
4. **Hardware Tampering**: Attempts to clone hardware keys, modify PCR values, or bypass secure boot.

---

## 2. Attack Vectors & Mitigations

### Attack 1: Quote & Assertion Tampering
- **Threat**: The attacker intercepts an attestation challenge and returns a modified TPM quote or WebAuthn payload claiming secure boot or clean PCR values.
- **AegisTrace Defense**: Every quote/assertion is signed by a hardware root key (TPM AIK, Apple Secure Enclave, Android StrongBox, or FIDO2 authenticator). Any bit-level modification invalidates the cryptographic signature, returning `ATTESTATION_INVALID`.

### Attack 2: Challenge Nonce Replay & Pre-computation
- **Threat**: The adversary records a valid attestation quote from a legitimate boot sequence and replays it during subsequent session requests.
- **AegisTrace Defense**: Every attestation challenge generates a fresh 256-bit random nonce (`os.urandom(32)`). The challenge manager tracks nonces in memory, enforcing single-use consumption (`NONCE_REUSED_REPLAY_ATTACK`) and a strict 120-second time-to-live (`CHALLENGE_EXPIRED`).

### Attack 3: Multi-Tenant Cross-Boundary Injection
- **Threat**: A contractor operating in Organization A captures a valid challenge nonce and attempts to enroll their device or claim sessions in Organization B.
- **AegisTrace Defense**: Challenges are bound to `(device_id, organization_id)`. Verification validates that the presenting organization matches the issuing organization; cross-tenant injection fails with `ORGANIZATION_MISMATCH`.

### Attack 4: Rogue Key Injection & Substitution
- **Threat**: An attacker enrolls a legitimate device identifier `dev_target` but supplies their own rogue public key, attempting to decrypt releases intended for `dev_target`.
- **AegisTrace Defense**: Registration requires an initial attestation quote that cryptographically binds to the public key fingerprint (`dkey_...`). Attempting to register an already-enrolled device ID fails closed (`ValueError: already enrolled`).

### Attack 5: Session Token Theft & Cross-Device Relay
- **Threat**: Malware extracts an active session token from Device A (e.g., via memory dump) and replays it on Device B to download or export protected documents.
- **AegisTrace Defense**: Sessions are cryptographically bound to `device_id`. When Device B presents a token issued to Device A, the session manager evaluates `presenting_device_id != session.device_id` and rejects access with `DEVICE_SESSION_MISMATCH`.

### Attack 6: Shared Kiosk / Multi-User Ambiguity
- **Threat**: Multiple analysts (Alice, Bob) share a single secure workstation. An attacker claims that Alice leaked a document because her registered workstation was used.
- **AegisTrace Defense**: AegisTrace decouples **Recipient Authorization** from **Device Trust**:
  - Decryption receipts require the recipient's post-quantum ML-DSA-65 signature.
  - The workstation's attestation corroborates platform integrity, but does **not** identify the human operator.
  - Both signals must align during forensic evidence fusion.

### Attack 7: Software Emulation of Hardware Roots
- **Threat**: An adversary runs a virtualized software TPM emulator (e.g., swtpm) and claims hardware-grade assurance.
- **AegisTrace Defense**: AegisTrace enforces the **Strict Honesty Invariant**: software providers strictly report `DEVICE_UNATTESTED` and `SOFTWARE_FALLBACK`. In `HIGH_ASSURANCE` environments, unattested software devices are blocked from decrypting or viewing releases.

---

## 3. Forensic Non-Repudiation Boundaries

AegisTrace embeds a mandatory, non-negotiable legal and forensic boundary statement in every device observation:

> **FORENSIC BOUNDARY**: Hardware attestation verifies device platform integrity and cryptographic key possession. It does NOT prove personal human operation.

This explicit distinction guarantees that forensic analysts and court adjudicators cannot conflate device physical presence with personal criminal culpability without corroborating identity evidence.
